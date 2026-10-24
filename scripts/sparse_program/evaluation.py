"""Mechanical fixed-denominator checks; independent reviewers own technical GO."""

import json
import subprocess

from . import checker, ledger
from .runner import check_inputs, manifest, oracle, read_payload


def latest(group):
    choices = []
    for path in (ledger.OUT / "groups").glob("*/summary.json"):
        value = json.loads(path.read_text())
        if value["group"] == group:
            choices.append((path, value))
    assert choices, f"Missing group {group}"
    return max(choices, key=lambda pair: pair[0].stat().st_mtime)


def group_check(group, expected):
    path, summary = latest(group)
    records = summary["records"]
    assert len(records) == expected and len({r["id"] for r in records}) == expected
    assert summary["all_pass"], [r for r in records if not r["pass"]]
    assert summary["engine"] == "sparse"
    return {
        "path": str(path.relative_to(ledger.ROOT)),
        "sha256": ledger.sha(path),
        "cases": expected,
    }


def sp1():
    check_inputs()
    assert not subprocess.check_output(
        ["git", "diff", "a480985", "--", "src", "pyproject.toml"], cwd=ledger.ROOT
    ), "SP1 must precede production edits"
    frozen = manifest()
    references_path = ledger.ROOT / "tests/fixtures/sparse_program_oracles.json"
    references = json.loads(references_path.read_text())
    assert len(references["cases"]) == 120
    for entry in frozen["cases"]:
        oracle(entry)
    for chain in frozen["trajectories"]:
        ref = references["trajectories"][chain["id"]]
        assert ref["initial"]["payload_sha256"] == chain["initial_sha256"]
        assert (
            ledger.sha(ledger.ROOT / ref["initial"]["witness_path"])
            == ref["initial"]["witness_sha256"]
        )
        assert len(ref["states"]) == 20
        for state in chain["states"]:
            assert oracle(state, chain["id"])["status"] == "optimal"
    path, baseline = latest("overlap")
    assert baseline["engine"] == "dense" and len(baseline["records"]) == 8
    by_id = {e["id"]: e for e in frozen["cases"]}
    retained = []
    for record in baseline["records"]:
        entry = by_id[record["id"]]
        result_path = ledger.ROOT / record["result_path"]
        if result_path.exists():
            packet = json.loads(result_path.read_text())
            if packet["result"]["status"] == "optimal":
                checker.check(
                    read_payload(entry),
                    packet["result"],
                    truth=oracle(entry),
                    options=packet["options"],
                )
        retained.append(
            {
                "id": record["id"],
                "status": record.get("status"),
                "pass": record["pass"],
                "failure": record.get("failure"),
            }
        )
    return {
        "case_truths": 120,
        "warm_state_truths": 160,
        "warm_initial_truths": 8,
        "oracle_sha256": ledger.sha(references_path),
        "baseline_path": str(path.relative_to(ledger.ROOT)),
        "baseline_records": retained,
        "production_edits": False,
    }


def sp2():
    return {g: group_check(g, n) for g, n in (("tiny", 48), ("pressure", 24), ("sp2-smoke", 6))}


def sp3():
    outcome = {"mechanism": group_check("mechanism", 8)}
    _, mechanism = latest("mechanism")
    ratios = {}
    for record in mechanism["records"]:
        packet = json.loads((ledger.ROOT / record["result_path"]).read_text())
        counters = packet["result"]["diagnostics"]
        assert packet["result"]["iterations"] >= 50
        updates, replacements = counters["eta_updates"], counters["basis_replacements"]
        assert replacements >= 50 and updates / replacements >= 0.7
        ratios[record["id"]] = {
            "eta_updates": updates,
            "basis_replacements": replacements,
            "ratio": updates / replacements,
        }
    choices = sorted((ledger.OUT / "warm").glob("*/summary.json"), key=lambda p: p.stat().st_mtime)
    assert choices
    path = choices[-1]
    warm = json.loads(path.read_text())
    assert warm["all_correct"] and warm["performance_pass"] and len(warm["records"]) == 80
    outcome.update(
        mechanism_ratios=ratios,
        warm_path=str(path.relative_to(ledger.ROOT)),
        warm_sha256=ledger.sha(path),
        median_ratio=warm["median_ratio"],
        nonregressing=warm["nonregressing"],
    )
    return outcome


def evaluate(stage):
    try:
        function = {"SP1": sp1, "SP2": sp2, "SP3": sp3}[stage]
        checks = function()
        value = {
            "stage": stage,
            "mechanical_checks_pass": True,
            "checks": checks,
            "source": ledger.identity(),
            "technical_review_required": True,
        }
        code = 0
    except (AssertionError, OSError, ValueError, KeyError) as exc:
        value = {
            "stage": stage,
            "mechanical_checks_pass": False,
            "failure": f"{type(exc).__name__}: {exc}",
        }
        code = 1
    folder = ledger.OUT / "evaluation"
    folder.mkdir(exist_ok=True)
    path = folder / f"{stage}_{ledger.utc().replace(':', '-')}.json"
    path.write_text(json.dumps(value, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "stage": stage,
                "mechanical_checks_pass": code == 0,
                "path": str(path.relative_to(ledger.ROOT)),
            }
        )
    )
    return code
