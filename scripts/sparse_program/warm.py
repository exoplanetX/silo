"""Fixed paired reoptimization timing, including public edits and original checks."""

import json
import statistics
import sys
from math import inf
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from . import checker, ledger
from .resources import guarded
from .runner import manifest, oracle


def edit_session(session, edit):
    from silo.core.bounds import Bounds
    from silo.core.constraint import Constraint
    from silo.core.variable import Variable

    kind = edit["kind"]
    if kind == "rhs":
        session.change_rhs(edit["row"], edit["rhs"])
    elif kind == "bounds":
        session.change_bounds(edit["variable"], edit["lower"], edit["upper"])
    elif kind == "append_row":
        row = edit["row"]
        session.append_row(
            Constraint(
                row["name"],
                row["coefficients"],
                row.get("sense", "<="),
                row.get("rhs", 0),
                row.get("lower"),
                row.get("upper"),
            )
        )
    elif kind == "append_column":
        v = edit["variable"]
        session.append_column(
            Variable(
                v["name"],
                Bounds(
                    v.get("lower", 0) if v.get("lower", 0) is not None else -inf,
                    v.get("upper") if v.get("upper") is not None else inf,
                ),
            ),
            edit["coefficients"],
            edit["cost"],
        )
    else:
        raise ValueError(f"Unknown frozen edit {kind}")


def one(request_path, response_path):
    start = perf_counter()
    request = json.loads(Path(request_path).read_text())
    chain, mode = request["chain"], request["mode"]
    response = Path(response_path)

    def forbidden(*args, **kwargs):
        raise AssertionError("External optimizer called during native trajectory")

    import scipy.optimize

    scipy.optimize.linprog = scipy.optimize.milp = forbidden
    sys.path.insert(0, str(ledger.ROOT / "src"))
    from silo import SolveOptions, solve
    from silo.io import model_from_dict
    from silo.lp.session import LPSession

    options = SolveOptions(lp_engine="sparse", **chain["options"], time_limit=60)
    initial_path = ledger.ROOT / chain["initial_path"]
    assert ledger.sha(initial_path) == chain["initial_sha256"]
    payload = json.loads(initial_path.read_text())
    session = LPSession(model_from_dict(payload), options)
    references = json.loads(
        (ledger.ROOT / "tests/fixtures/sparse_program_oracles.json").read_text()
    )["trajectories"][chain["id"]]
    initial = references["initial"]
    assert initial["payload_sha256"] == chain["initial_sha256"]
    assert ledger.sha(ledger.ROOT / initial["witness_path"]) == initial["witness_sha256"]
    records = []

    def record_started(label):
        with response.with_suffix(".started.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"id": label, "mode": mode, "native_roots_started": 1}) + "\n")

    def call(label, truth):
        record_started(label)
        result = session.solve() if mode == "warm" else solve(session.model, options)
        raw = result.to_dict()
        checked = checker.check(payload, raw, truth=truth, options=vars(options))
        assert result.status == "optimal", (label, result.status, result.termination_reason)
        return raw, checked

    raw, checked = call(chain["id"] + "-initial", initial["truth"])
    initial_seconds = perf_counter() - start
    initial_record = {"result": raw, "raw_check": checked, "seconds": initial_seconds}
    segment = perf_counter()
    from .cases import apply_edit

    for state in chain["states"]:
        step = perf_counter()
        payload = apply_edit(payload, state["edit"])
        edit_session(session, state["edit"])
        # Both modes pay for the same input identity/original-space checks.
        from .cases import sha

        assert sha(payload) == state["payload_sha256"]
        truth = oracle(state, chain["id"])
        raw, checked = call(state["id"], truth)
        packet = {
            "id": state["id"],
            "payload_sha256": state["payload_sha256"],
            "seconds": perf_counter() - step,
            "result": raw,
            "raw_check": checked,
        }
        records.append(packet)
        with response.with_suffix(".states.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(packet, allow_nan=False) + "\n")
    segment_seconds = perf_counter() - segment
    packet = {
        "id": chain["id"],
        "mode": mode,
        "repetition": request["repetition"],
        "initial": initial_record,
        "states": records,
        "segment_seconds": segment_seconds,
        "total_seconds_including_import_initial": perf_counter() - start,
        "native_roots_started": 21,
        "native_roots_completed": 21,
    }
    response.write_text(json.dumps(packet, allow_nan=False), encoding="utf-8")
    return 0


def aggregate(records):
    assert len(records) == 80
    assert len({(r["id"], r["mode"], r["repetition"]) for r in records}) == 80
    ratios, totals = {}, {}
    for label in sorted({r["id"] for r in records}):
        paired, inclusive = [], []
        for repetition in range(5):
            pair = {
                r["mode"]: r for r in records if r["id"] == label and r["repetition"] == repetition
            }
            assert set(pair) == {"warm", "cold"}
            assert all(r["pass"] for r in pair.values())
            paired.append(pair["cold"]["segment_seconds"] / pair["warm"]["segment_seconds"])
            inclusive.append(pair["cold"]["total_seconds"] / pair["warm"]["total_seconds"])
        ratios[label], totals[label] = statistics.median(paired), statistics.median(inclusive)
    assert len(ratios) == 8
    median = statistics.median(ratios.values())
    nonregressing = sum(r >= 1 for r in ratios.values())
    return {
        "trajectory_ratios": ratios,
        "initial_inclusive_ratios": totals,
        "median_ratio": median,
        "nonregressing": nonregressing,
        "performance_pass": median >= 1.5 and nonregressing >= 6,
    }


def execute(args):
    assert any(
        e["kind"] == "stage_gate" and e.get("stage") == "SP2" and e.get("decision") == "GO"
        for e in ledger.history()
    )
    folder = ledger.OUT / "warm" / f"round{args.round}_{uuid4()}"
    folder.mkdir(parents=True)
    records = []
    for chain_index, chain in enumerate(manifest()["trajectories"]):
        for repetition in range(5):
            modes = ("cold", "warm") if (chain_index + repetition) % 2 == 0 else ("warm", "cold")
            for mode in modes:
                stem = f"{chain['id']}_{repetition}_{mode}"
                request, response = folder / (stem + ".request.json"), folder / (stem + ".json")
                request.write_text(
                    json.dumps({"chain": chain, "mode": mode, "repetition": repetition}),
                    encoding="utf-8",
                )
                monitor = guarded(
                    [
                        sys.executable,
                        str(ledger.ROOT / "scripts/sparse_program.py"),
                        "_warm-one",
                        "--request",
                        str(request),
                        "--response",
                        str(response),
                    ],
                    ledger.ROOT,
                    folder / (stem + ".log"),
                    60,
                )
                record = {
                    "id": chain["id"],
                    "repetition": repetition,
                    "mode": mode,
                    "monitor": monitor,
                    "result_path": str(response.relative_to(ledger.ROOT)),
                    "pass": False,
                }
                try:
                    assert monitor["exit_code"] == 0 and monitor["guard_reason"] is None
                    packet = json.loads(response.read_text())
                    assert len(packet["states"]) == 20
                    record.update(
                        segment_seconds=packet["segment_seconds"],
                        total_seconds=packet["total_seconds_including_import_initial"],
                        **{"pass": True},
                    )
                except (AssertionError, OSError, ValueError, KeyError) as exc:
                    record["failure"] = f"{type(exc).__name__}: {exc}"
                records.append(record)
                with (folder / "records.jsonl").open("a", encoding="utf-8") as stream:
                    stream.write(json.dumps(record) + "\n")
                print(
                    json.dumps({k: record[k] for k in ("id", "mode", "repetition", "pass")}),
                    flush=True,
                )
    summary = {
        "records": records,
        "source": ledger.identity(),
        "all_correct": all(r["pass"] for r in records),
    }
    if summary["all_correct"]:
        summary.update(aggregate(records))
    (folder / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0 if summary.get("performance_pass") else 1
