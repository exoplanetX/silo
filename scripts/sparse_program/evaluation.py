"""Mechanical fixed-denominator checks; independent reviewers own technical GO."""

import json
import re
import subprocess
import zipfile
from fractions import Fraction
from hashlib import sha256
from math import isfinite
from pathlib import Path

from . import checker, ledger
from .runner import check_exit, check_inputs, manifest, oracle, read_payload


class EvidenceError(ValueError):
    """A missing or contradictory receipt is an unmet obligation."""


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def _path(value):
    path = Path(value)
    path = path if path.is_absolute() else ledger.ROOT / path
    require(path.resolve().is_relative_to(ledger.ROOT.resolve()), f"Evidence escaped repo: {value}")
    return path


def _read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _ref(path):
    path = _path(path)
    return {"path": path.relative_to(ledger.ROOT).as_posix(), "sha256": ledger.sha(path)}


def _bound(path, digest):
    path = _path(path)
    require(ledger.sha(path) == digest, f"Evidence hash mismatch: {path}")
    return path


def _metadata_mask(path, raw):
    masked, fields, section = [], set(), False
    for line in raw.splitlines(keepends=True):
        if path == "pyproject.toml":
            if line.lstrip().startswith(b"["):
                section = line.strip() == b"[project]"
            names = rb"(?:version|description)" if section else rb"(?!)"
        else:
            names = rb"__version__"
        pattern = (
            rb"^([ \t]*" + names + rb"[ \t]*=[ \t]*)(\"(?:[^\"\\]|\\.)*\"|'[^']*')"
            rb"([ \t]*(?:#.*)?)(\r?\n|$)"
        )
        match = re.match(pattern, line)
        if match:
            fields.add(match[1].split(b"=")[0].strip().decode())
            line = match[1] + b"<METADATA_LITERAL>" + match[3] + match[4]
        masked.append(line)
    require(fields, f"No supported single-line metadata literals in {path}")
    return b"".join(masked)


def source_match(recorded, current=None, bridge=None):
    """Strict solver bytes; only explicit, verified version/description bridges."""
    current = ledger.identity() if current is None else current
    old, new = recorded["source"], current["source"]
    require(recorded["source_sha256"] == ledger.digest(old), "Recorded source map digest mismatch")
    require(current["source_sha256"] == ledger.digest(new), "Current source map digest mismatch")
    require(set(old) == set(new), "Production module inventory changed")
    require(
        recorded.get("inputs", {}) == current.get("inputs", {}), "Frozen input identities changed"
    )
    if bridge is None:
        path = ledger.OUT / "metadata_source_bridge.json"
        bridge = _read(path) if path.exists() else {"changes": []}
    accepted = []
    for name in old:
        if old[name] == new[name]:
            continue
        require(
            name in ("pyproject.toml", "src/silo/__init__.py"), f"Algorithm source changed: {name}"
        )
        candidates = [
            c
            for c in bridge["changes"]
            if c["path"] == name
            and c["before_sha256"] == old[name]
            and c["after_sha256"] == new[name]
        ]
        require(len(candidates) == 1, f"Missing unique byte bridge for {name}")
        change = candidates[0]
        before = _bound(change["before_path"], old[name]).read_bytes()
        after = _bound(change["after_path"], new[name]).read_bytes()
        if change.get("allow_crlf_transport") is True:
            before, after = before.replace(b"\r\n", b"\n"), after.replace(b"\r\n", b"\n")
            require(b"\r" not in before + after, "Metadata bridge contains bare CR")
        require(
            _metadata_mask(name, before) == _metadata_mask(name, after),
            f"Bridge changes bytes outside allowed metadata: {name}",
        )
        accepted.append(change)
    return {
        "recorded_sha256": recorded["source_sha256"],
        "current_sha256": current["source_sha256"],
        "metadata_bridges": accepted,
    }


def _fixed_records(records, expected_ids):
    ids = [r["id"] for r in records]
    require(
        len(ids) == len(set(ids)) and set(ids) == set(expected_ids),
        "Fixed ID set/denominator mismatch",
    )
    require(all(r.get("pass") is True for r in records), "A retained case failed")


def _drivers_unchanged(recorded, names):
    current = ledger.identity()
    for name in names:
        key = "scripts/sparse_program/" + name + ".py"
        require(
            recorded["scripts"][key] == current["scripts"][key], f"Evidence driver changed: {key}"
        )


def _monitor(record, seconds, tree=False):
    monitor = record["monitor"]
    require(
        monitor["exit_code"] == 0 and monitor["guard_reason"] is None,
        "Child failed or watchdog killed it",
    )
    require(
        isfinite(monitor["elapsed_seconds"]) and 0 < monitor["elapsed_seconds"] <= seconds,
        "Per-case hard wall exceeded",
    )
    require(0 < monitor["peak_rss_bytes"] <= 1 << 30, "OS peak RSS missing/exceeded1GiB")
    if tree:
        require(
            monitor.get("process_scope") == "root_and_descendants",
            "Whole process tree RSS was not measured",
        )


def _entries(group):
    cases = manifest()["cases"]
    if group == "sp2-smoke":
        ids = {"NETLIB-" + s for s in ("AFIRO", "ADLITTLE", "SC50A", "SC50B")}
        ids.update(("CAP-FLOW-01", "CAP-TRANS-01"))
        return [e for e in cases if e["id"] in ids]
    return [e for e in cases if e["group"] in ({"mip", "cg"} if group == "mip-cg" else {group})]


def _record_files(record, entry, engine):
    require(
        record["input_sha256"] == entry["payload_sha256"], "Record input SHA differs from freeze"
    )
    read_payload(entry)
    result_path = _bound(record["result_path"], record["result_sha256"])
    require(result_path.name == entry["id"] + ".result.json", "Result path/ID mismatch")
    request_path = result_path.with_name(entry["id"] + ".request.json")
    request = _read(_bound(request_path, record["request_sha256"]))
    packet = _read(result_path)
    require(
        request["entry"] == entry and request["engine"] == engine,
        "Request differs from frozen entry/engine",
    )
    require(packet["id"] == entry["id"] and packet["engine"] == engine, "Packet identity mismatch")
    seconds = (
        120
        if entry["group"] in ("capacity", "netlib")
        else 60
        if entry["group"] in ("mip", "cg", "mechanism")
        else 10
    )
    require(request["seconds"] == seconds, "Request wall limit differs from fixed group")
    _monitor(record, seconds, tree=entry["group"] in ("capacity", "netlib"))
    options = dict(entry.get("options", {}))
    options["time_limit"] = min(options.get("time_limit", seconds), seconds)
    if engine == "sparse":
        options["lp_engine"] = "sparse"
    require(packet["options"] == options, "Actual options differ from frozen request")
    require(
        packet["native_root_calls_started"] == packet["native_root_calls_completed"] == 1,
        "Native root did not complete exactly once",
    )
    require(
        packet["native_lp_calls_started"] == packet["native_lp_calls_completed"],
        "Unfinished native LP call",
    )
    require(
        packet["result"]["status"] in entry["expected_statuses"],
        "Status outside frozen expectation",
    )
    check_exit(entry, packet)
    require(
        record.get("status") == packet["result"]["status"], "Summary/packet terminal status differs"
    )
    return packet


def _case_math(entry, packet):
    result = packet["result"]
    if entry["group"] == "cg":
        if result["status"] == "optimal":
            from .oracles import full_pool_payload, primal_dual_pair

            proof = result["witness"]
            require(proof["kind"] == "finite_pool_optimality", "CG lacks full-pool proof")
            primal_dual_pair(
                full_pool_payload({**entry, "payload": read_payload(entry)}),
                {
                    key: {name: Fraction(value) for name, value in proof[key].items()}
                    for key in ("point", "row_duals")
                },
            )
            checker.close(result["objective_value"], oracle(entry)["objective"])
        else:
            require(
                result.get("dual_bound") is None or result.get("dual_bound_is_infinite") is True,
                "Unproved CG returned finite full-pool bound",
            )
    else:
        checker.check(
            read_payload(entry),
            result,
            truth=oracle(entry),
            options=packet["options"],
            mip=entry["group"] == "mip",
        )
        if result["status"] in ("infeasible", "unbounded"):
            checker.certificate(read_payload(entry), result)


def latest(group):
    choices = []
    for path in (ledger.OUT / "groups").glob("*/summary.json"):
        value = _read(path)
        if value["group"] == group:
            choices.append((path, value))
    assert choices, f"Missing group {group}"
    return max(choices, key=lambda pair: pair[0].stat().st_mtime)


def group_check(group, expected):
    path, summary = latest(group)
    records = summary["records"]
    entries = {e["id"]: e for e in _entries(group)}
    require(len(entries) == expected, "Frozen group denominator differs from contract")
    _fixed_records(records, entries)
    require([r["id"] for r in records] == list(entries), "Frozen group order changed")
    require(
        summary["all_pass"] is True and summary["engine"] == "sparse",
        "Group did not pass on sparse engine",
    )
    source = source_match(summary["source"])
    _drivers_unchanged(
        summary["source"], ("cases", "netlib_data", "oracles", "runner", "checker", "resources")
    )
    for record in records:
        packet = _record_files(record, entries[record["id"]], "sparse")
        _case_math(entries[record["id"]], packet)
        if entries[record["id"]]["group"] not in ("cg", "mip"):
            result = packet["result"]
            actual = result["diagnostics"].get("lp_engine")
            require(
                actual == "sparse"
                or (
                    actual is None
                    and result["status"] not in ("optimal", "infeasible", "unbounded")
                ),
                "Native engine differs from request",
            )
    return {
        "path": str(path.relative_to(ledger.ROOT)),
        "sha256": ledger.sha(path),
        "cases": expected,
        "source": source,
        "evidence_refs": [_ref(path)],
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
    mechanisms, warm = mechanism_check(), warm_check()
    return {
        "mechanism": mechanisms,
        "warm": warm,
        "median_ratio": warm["median_ratio"],
        "nonregressing": warm["nonregressing"],
    }


def mechanism_check():
    outcome = group_check("mechanism", 8)
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
    outcome["mechanism_ratios"] = ratios
    return outcome


def _latest_folder(name):
    paths = list((ledger.OUT / name).glob("*/summary.json"))
    require(paths, f"Missing {name} summary")
    path = max(paths, key=lambda p: p.stat().st_mtime)
    return path, _read(path)


def _tree_bound(path, summary):
    claimed = summary["bound_files"]
    require(claimed, "Missing predeclared bound_files")
    bound = {_bound(name, digest).resolve() for name, digest in claimed.items()}
    actual = {p.resolve() for p in path.parent.rglob("*") if p.is_file() and p != path}
    require(bound == actual, "New-run file inventory differs from bound_files")


def warm_check():
    from .warm import aggregate

    path, summary = _latest_folder("warm")
    source_match(summary["source"])
    _drivers_unchanged(
        summary["source"], ("cases", "oracles", "runner", "checker", "resources", "warm")
    )
    _tree_bound(path, summary)
    chains = {chain["id"]: chain for chain in manifest()["trajectories"]}
    records = summary["records"]
    require(len(chains) == 8 and len(records) == 80, "Warm denominator is not8x2x5")
    expected = {
        (name, mode, repeat) for name in chains for mode in ("cold", "warm") for repeat in range(5)
    }
    require(
        {(r["id"], r["mode"], r["repetition"]) for r in records} == expected,
        "Warm fixed trajectory/mode/repetition set differs",
    )
    ordered = [
        (name, mode, repeat)
        for index, name in enumerate(chains)
        for repeat in range(5)
        for mode in (("cold", "warm") if (index + repeat) % 2 == 0 else ("warm", "cold"))
    ]
    require(
        [(r["id"], r["mode"], r["repetition"]) for r in records] == ordered,
        "Warm/cold alternating execution order changed",
    )
    recomputed, reuse = [], {name: 0 for name in chains}
    references = _read(ledger.ROOT / "tests/fixtures/sparse_program_oracles.json")
    for record in records:
        require(record["pass"] is True, "Failed warm repetition retained")
        _monitor(record, 60, tree=True)
        chain = chains[record["id"]]
        result_path = _bound(record["result_path"], record["result_sha256"])
        request_path = result_path.with_name(result_path.stem + ".request.json")
        request = _read(_bound(request_path, record["request_sha256"]))
        require(
            request == {"chain": chain, "mode": record["mode"], "repetition": record["repetition"]},
            "Warm request differs from freeze",
        )
        packet = _read(result_path)
        require(
            packet["id"] == chain["id"]
            and packet["mode"] == record["mode"]
            and packet["repetition"] == record["repetition"],
            "Warm packet identity mismatch",
        )
        require(
            packet["native_roots_started"] == packet["native_roots_completed"] == 21,
            "Warm initial/state call count differs",
        )
        require(
            packet["total_seconds_including_import_initial"] <= 60,
            "Initial-inclusive warm wall exceeded",
        )
        require(
            packet["segment_seconds"] > 0
            and packet["segment_seconds"] <= packet["total_seconds_including_import_initial"],
            "Invalid warm segment timing",
        )
        initial = packet["initial"]["result"]
        require(initial["status"] == "optimal", "Warm initial solve not optimal")
        initial_payload = _read(_bound(chain["initial_path"], chain["initial_sha256"]))
        checker.check(
            initial_payload,
            initial,
            truth=references["trajectories"][chain["id"]]["initial"]["truth"],
        )
        states = packet["states"]
        require(
            [s["id"] for s in states] == [s["id"] for s in chain["states"]],
            "Warm state sequence differs from freeze",
        )
        for state, frozen in zip(states, chain["states"], strict=True):
            require(
                state["payload_sha256"] == frozen["payload_sha256"], "Warm state input SHA differs"
            )
            require(state["result"]["status"] == "optimal", "Modified warm state not optimal")
            checker.check(
                read_payload(frozen),
                state["result"],
                truth=oracle(frozen, chain["id"]),
                options=chain["options"],
            )
            require(
                state["result"]["diagnostics"].get("lp_engine") == "sparse",
                "Warm used another engine",
            )
            if record["mode"] == "warm":
                reuse[chain["id"]] += state["result"]["diagnostics"].get("cross_solve_reuses", 0)
        require(
            sum(s["seconds"] for s in states) <= packet["segment_seconds"] * (1 + 1e-9),
            "Warm state times exceed measured segment",
        )
        recomputed.append(
            {
                **record,
                "segment_seconds": packet["segment_seconds"],
                "total_seconds": packet["total_seconds_including_import_initial"],
            }
        )
    measured = aggregate(recomputed)
    require(
        measured["performance_pass"] and summary["all_correct"] is True,
        "Warm correctness/performance gate unmet",
    )
    require(sum(reuse.values()) > 0, "No actual cross-solve factor reuse recorded")
    require(
        measured["trajectory_ratios"] == summary["trajectory_ratios"],
        "Published warm ratios differ from raw timings",
    )
    return {
        **measured,
        "cross_solve_reuses": reuse,
        "state_solves": 1600,
        "initial_solves": 80,
        "evidence_refs": [_ref(path)],
    }


def frozen_sp1_gate():
    gates = [
        e
        for e in ledger.history()
        if e["kind"] == "stage_gate" and e.get("stage") == "SP1" and e.get("decision") == "GO"
    ]
    require(len(gates) == 1, "Unique historical SP1 GO missing")
    gate = gates[0]
    review_path = _bound(gate["review_path"], gate["review_sha256"])
    review = _read(review_path)
    require(
        gate["production_unchanged"] is True
        and review["decision"] == "GO"
        and review["source_matches_issuance"] is True,
        "SP1 preimplementation freeze not established",
    )
    diff = subprocess.check_output(
        ["git", "diff", "a480985", gate["truth_commit"], "--", "src", "pyproject.toml"],
        cwd=ledger.ROOT,
    )
    require(not diff, "Product changed before truth freeze")
    from .delivery import equivalent_text

    frozen = {}
    paths = [
        "scripts/sparse_program/cases.py",
        "scripts/sparse_program/netlib_data.py",
        "tests/fixtures/sparse_program_manifest.json",
        "tests/fixtures/sparse_program_sources.json",
        "tests/fixtures/sparse_program_oracles.json",
    ]
    for name in paths:
        commit = gate["truth_commit"] if name.endswith("oracles.json") else gate["input_commit"]
        raw = subprocess.check_output(["git", "show", f"{commit}:{name}"], cwd=ledger.ROOT)
        frozen[name] = equivalent_text(raw, (ledger.ROOT / name).read_bytes())
    return {
        "historical_gate_sha256": gate["sha256"],
        "input_commit": gate["input_commit"],
        "truth_commit": gate["truth_commit"],
        "frozen_files": frozen,
        "sp1_rerun": False,
        "evidence_refs": [_ref(review_path)],
    }


def capacity_check():
    outcome = {
        name: group_check(name, count)
        for name, count in (("tiny", 48), ("pressure", 24), ("capacity", 12), ("netlib", 12))
    }
    _, summary = latest("capacity")
    entries = {e["id"]: e for e in _entries("capacity")}
    coupled = []
    for record in summary["records"]:
        entry = entries[record["id"]]
        packet = _read(_path(record["result_path"]))
        require(packet["result"]["status"] == "optimal", "Capacity required-success case failed")
        if entry["metadata"].get("require_coupled_pivots"):
            require(
                packet["options"]["presolve"] is False and packet["result"]["iterations"] >= 20,
                "Prelocked coupled capacity pivot mechanism unmet",
            )
            coupled.append(entry["id"])
    require(len(coupled) == 6, "Six prelocked capacity mechanisms missing")
    largest = entries["CAP-BLOCK-02"]["statistics"]
    require(
        (largest["variables"], largest["rows"], largest["matrix_nonzeros"]) == (2000, 5000, 100000),
        "Largest fixed target changed",
    )
    return {
        "groups": outcome,
        "coupled_ids": coupled,
        "evidence_refs": [ref for value in outcome.values() for ref in value["evidence_refs"]],
    }


def mip_cg_check():
    outcome = group_check("mip-cg", 16)
    _, summary = latest("mip-cg")
    entries = {e["id"]: e for e in _entries("mip-cg")}
    branches, cuts, phase1, phase2 = [], [], [], []
    for record in summary["records"]:
        entry = entries[record["id"]]
        packet = _read(_path(record["result_path"]))
        result, meta = packet["result"], entry["metadata"]
        if entry["group"] == "mip":
            stats = result["diagnostics"]
            require(
                stats["lp_engine_counts"]["sparse"] == stats["lp_calls"]
                and stats["lp_engine_counts"]["dense"] == 0,
                "MIP did not use sparse on every LP",
            )
            if meta["require_branch"]:
                require(stats["branches"] > 0, "Prelocked branching model did not branch")
                branches.append(entry["id"])
            if meta["require_gmi"]:
                require(stats["cuts_added"] > 0, "Prelocked local GMI model added no cut")
                require(
                    any(
                        event.get("scope") == "node_local"
                        and event.get("added")
                        and event.get("status") == "optimal"
                        and event.get("lp_engine") == "sparse"
                        and event["lp_diagnostics"].get("lp_engine") == "sparse"
                        and any(p.get("kind") == "gmi" for p in event.get("proofs", []))
                        for event in stats["cut_events"]
                    ),
                    "No actual local GMI plus sparse reoptimization",
                )
                cuts.append(entry["id"])
        else:
            trace = result["trace"]
            require(
                len(trace) == packet["native_lp_calls_completed"] and trace,
                "CG LP count/trace mismatch",
            )
            require(
                all(step["lp_diagnostics"].get("lp_engine") == "sparse" for step in trace),
                "CG used another engine",
            )
            if meta["require_phase1_added_column"]:
                require(
                    any(s["phase"] == "phase1" and s["added_columns"] for s in trace),
                    "CG Phase I added no real column",
                )
                phase1.append(entry["id"])
            if meta["require_phase2_cross_solve_reuse"]:
                require(
                    any(
                        s["phase"] == "phase2"
                        and s["lp_diagnostics"].get("cross_solve_reuses", 0) > 0
                        for s in trace
                    ),
                    "CG Phase II lacks actual cross-call reuse",
                )
                phase2.append(entry["id"])
            if entry["id"] == "CG-TINYRC":
                checker.close(result["objective_value"], -10000)
    require(
        len(branches) >= 4 and len(cuts) >= 2 and phase1 and phase2,
        "Fixed upper-layer mechanisms incomplete",
    )
    return {
        **outcome,
        "branched_ids": branches,
        "local_gmi_ids": cuts,
        "phase1_ids": phase1,
        "phase2_reuse_ids": phase2,
    }


def historical_check():
    path, summary = _latest_folder("historical")
    source_match(summary["source"])
    _drivers_unchanged(summary["source"], ("historical", "checker"))
    _tree_bound(path, summary)
    pins_path = ledger.OUT / "preserved_old_evidence.json"
    pins = _read(pins_path)
    require(pins, "Old evidence pin set is empty")
    for name, digest in pins.items():
        _bound(name, digest)
    old = _read(ledger.ROOT / "tests/fixtures/prototype_manifest.json")
    models_path = ledger.ROOT / "outputs/audit_20261024/probe_models.json"
    references_path = ledger.ROOT / "outputs/audit_20261024/probe_records.json"
    models, references = _read(models_path), _read(references_path)
    require(len(models) == len(references) == 192, "Old192-model audit inventory differs")
    original = {e["id"] for e in [*old["cases"], *old["boundaries"]]}
    diagnostics = {e["id"] for e in old["diagnostics"]}
    audit_ids = {
        p["name"] + "_" + config for p in models for config in ("default", "reference_controls")
    }
    require(
        len(original) == 288 and len(diagnostics) == 64 and len(audit_ids) == 384,
        "Historical fixed denominators differ",
    )
    _fixed_records(
        summary["records"], original | diagnostics | audit_ids | {"two_public_research_examples"}
    )
    require(
        summary["all_pass"] is True
        and summary["old_cases"] == 288
        and summary["old_audit_models"] == 192
        and summary["old_audit_configurations"] == 384
        and summary["saved_diagnostics"] == 64,
        "Historical matrix incomplete",
    )
    require(
        summary["saved_diagnostic_new_solves"] == 0
        and summary["new_reference_calls"] == 0
        and summary["old_ledger_written"] is False
        and summary["old_evidence_unchanged"] is True,
        "Historical recheck changed old evidence or re-solved saved diagnostics",
    )
    require(summary["audit_native_calls"] == 384, "Audit configuration calls incomplete")
    records = {r["id"]: r for r in summary["records"]}
    for entry in old["cases"]:
        record = records[entry["id"]]
        require(
            record["model_sha256"] == entry["model_sha256"], "Historical model identity changed"
        )
        require((path.parent / record["result_file"]).is_file(), "Historical result missing")
    for entry in old["boundaries"]:
        require(
            records[entry["id"]]["input_sha256"] == entry["input_sha256"],
            "Historical boundary identity changed",
        )
    for entry in old["diagnostics"]:
        record = records[entry["id"]]
        require(
            record["new_native_calls"] == 0 and record["native_calls"] == 0,
            "Saved diagnostic was re-solved",
        )
        original_path = (
            ledger.ROOT
            / "outputs/prototype/validation/diagnostics"
            / (entry["id"] + "_output.json")
        )
        require(
            record["source_sha256"] == ledger.sha(original_path), "Saved diagnostic source differs"
        )
    for name in audit_ids:
        require(
            records[name]["reference_source_sha256"] == ledger.sha(references_path),
            "Old audit reference changed",
        )
        require((path.parent / (name + ".json")).is_file(), "Old audit result missing")
    integration = records["two_public_research_examples"]
    require(integration["integration_examples"] == 2, "Historical public examples missing")
    for key, frozen_name in (("cg", "finite_cg"), ("mip", "mip_policy")):
        require(
            integration[key]["input_sha256"] == old["integrations"][frozen_name]["input_sha256"],
            "Historical integration identity changed",
        )
    return {
        "old_cases": 288,
        "audit_models": 192,
        "audit_configurations": 384,
        "saved_diagnostics": 64,
        "saved_new_solves": 0,
        "pinned_files": len(pins),
        "evidence_refs": [_ref(path), _ref(pins_path)],
    }


def quality_scope_files():
    paths = {ledger.ROOT / "pyproject.toml"}
    for directory in ("src", "tests", "examples", "scripts"):
        paths.update((ledger.ROOT / directory).rglob("*.py"))
    paths.update((ledger.ROOT / "tests/fixtures").rglob("*.json"))
    return {p.relative_to(ledger.ROOT).as_posix(): ledger.sha(p) for p in sorted(paths)}


def quality_check():
    events = ledger.history()
    successes = [
        e
        for e in events
        if e["kind"] == "command_finished"
        and e.get("group") == "quality"
        and e.get("exit_code") == 0
    ]
    require(successes, "No successful complete quality command")
    finished = successes[-1]
    argv = finished["argv"]
    require(
        len(argv) == 2
        and _path(argv[1]).resolve() == (ledger.ROOT / "scripts/check_quality.py").resolve(),
        "Receipt is not the complete quality entry point",
    )
    started = next(
        e for e in events if e["kind"] == "command_started" and e["run"] == finished["run"]
    )
    identity_path = _path(finished["run"]) / "identity.json"
    identity = _read(identity_path)
    require(ledger.digest(identity) == started["identity_sha256"], "Quality start identity changed")
    source_match(identity)
    _bound(finished["log"], finished["log_sha256"])
    previous = events[: events.index(started)]
    scopes = [e for e in previous if e["kind"] == "quality_scope_pinned"]
    require(scopes, "QUALITY_SCOPE_MISSING: no source/test/driver pin before quality")
    event = scopes[-1]
    scope_path = _bound(event["path"], event["file_sha256"])
    scope = _read(scope_path)
    require(
        event["source_commit"] == identity["commit"]
        and event["source_sha256"] == identity["source_sha256"],
        "Quality scope/event/source mismatch",
    )
    current_map = quality_scope_files()
    source_match(
        {"source": scope["files"], "source_sha256": ledger.digest(scope["files"])},
        {"source": current_map, "source_sha256": ledger.digest(current_map)},
    )
    return {
        "command_finished_sha256": finished["sha256"],
        "exit_code": 0,
        "evidence_refs": [_ref(scope_path), _ref(identity_path), _ref(finished["log"])],
    }


def delivery_check():
    from .delivery import KEYS, audit_artifact, equivalent_text

    path, summary = _latest_folder("delivery")
    require(
        summary["candidate"] == "0.3.0a1" and summary["all_pass"] is True,
        "Candidate delivery is incomplete",
    )
    source = summary["source"]
    snapshot = _path(source["snapshot"])
    files = source["files"]
    require(source["source_sha256"] == ledger.digest(files), "Delivery source map digest mismatch")
    current = ledger.identity()["source"]
    require(set(files) == set(current), "Delivery source module inventory differs")
    requests = "".join(f"{source['commit']}:{name}\n" for name in files).encode()
    committed = subprocess.check_output(
        ["git", "cat-file", "--batch"], input=requests, cwd=ledger.ROOT
    )
    offset = 0
    for name, digest in files.items():
        end = committed.find(b"\n", offset)
        fields = committed[offset:end].split()
        require(
            len(fields) == 3 and fields[1] == b"blob", "Delivery source is not a committed Git blob"
        )
        size = int(fields[2])
        raw = committed[end + 1 : end + 1 + size]
        require(
            len(raw) == size and sha256(raw).hexdigest() == digest,
            f"Snapshot differs from actual committed blob: {name}",
        )
        offset = end + size + 2
    require(offset == len(committed), "Committed batch stream length mismatch")
    transport = {}
    for name, digest in files.items():
        snapshot_file = _bound(snapshot / name, digest)
        transport[name] = equivalent_text(
            snapshot_file.read_bytes(), (ledger.ROOT / name).read_bytes()
        )
    archive_path = _bound(path.parent / "source.zip", source["archive_sha256"])
    with zipfile.ZipFile(archive_path) as archive:
        for name, digest in files.items():
            require(
                sha256(archive.read(name)).hexdigest() == digest,
                "Git archive member differs from committed snapshot",
            )
    checker_path = ledger.ROOT / "scripts/sparse_program/check_installed.py"
    require(
        ledger.sha(checker_path) == summary["checker_sha256"], "Installation checker source changed"
    )
    for kind in ("wheel", "sdist"):
        artifact = summary["artifacts"][kind]
        artifact_path = _bound(artifact["path"], artifact["sha256"])
        checked = audit_artifact(artifact_path, kind, snapshot, source["project"])
        require(checked == artifact, "Current artifact audit differs from recorded artifact")
    installations = summary["installations"]
    require(
        len(installations) == 8 and {r["key"] for r in installations} == KEYS,
        "Eight unique installation combinations missing",
    )
    environments = set()
    for record in installations:
        require(
            record["key"]
            == f"{record['python_requested']}-{record['mode']}-{record['artifact_kind']}",
            "Installation key disagrees with its actual combination",
        )
        require(
            record["pass"] is True and 1 <= len(record["attempts"]) <= 2,
            "Installation did not pass within retry cap",
        )
        require(
            record["artifact_sha256"] == summary["artifacts"][record["artifact_kind"]]["sha256"],
            "Installation artifact changed",
        )
        for attempt in record["attempts"]:
            environment = Path(attempt["fresh_environment"]).resolve()
            require(
                environment not in environments
                and not environment.is_relative_to(ledger.ROOT.resolve()),
                "Installation reused environment/source tree",
            )
            environments.add(environment)
            for command in attempt["commands"]:
                _bound(command["log"], command["log_sha256"])
            if attempt["number"] == 1 and len(record["attempts"]) == 2:
                require(
                    attempt.get("environmental_failure") is True,
                    "Non-environment installation retry",
                )
        report_path = _bound(record["check_report_path"], record["check_report_sha256"])
        report = _read(report_path)
        p = report["provenance"]
        require(
            report["status"] == "passed" and p["version"] == "0.3.0a1" and p["isolated"] is True,
            "Installed provenance not passed/isolated/candidate",
        )
        require(
            p["python"].startswith(record["python_requested"] + ".") and p["numpy"] == "2.3.5",
            "Installed interpreter/NumPy mismatch",
        )
        require(p["platform"].startswith("Windows"), "Required Windows platform was not verified")
        require(
            Path(p["executable"])
            .resolve()
            .is_relative_to(Path(record["attempts"][-1]["fresh_environment"]).resolve()),
            "Installed checker used another environment's interpreter",
        )
        sparse = record["mode"] == "sparse"
        require(
            p["scipy_installed"] is sparse and p["scipy_version"] == ("1.16.3" if sparse else None),
            "Installed SciPy configuration mismatch",
        )
        require(
            p["silo_import_loaded_scipy"] is False and report["external_optimizer_attempts"] == 0,
            "Installed lazy import/optimizer isolation failed",
        )
        require(
            p["artifact_sha256"] == record["artifact_sha256"]
            and p["direct_url_artifact_sha_matched"] is True,
            "Installed direct_url artifact identity failed",
        )
        require(
            report["mode"] == record["mode"] and report["optional_scipy_imported"] is sparse,
            "Installed selected engine configuration differs",
        )
        require(
            len(report["session_edits"]) == 4 and len(report["cli"]) == 4,
            "Installed edit/CLI contract incomplete",
        )
        require(
            report["repair_regressions"]["F4_derived_underflow_refusals"] == 6,
            "Installed F4 regressions incomplete",
        )
        require(
            {r["id"] for r in report["research_examples"]}
            == {
                "public_covering_example",
                "public_policy_example_fixed_dense",
                "original_full_pool_third",
            },
            "Installed research/full-pool checks missing",
        )
        roots = [Path(root).resolve() for root in p["site_packages"]]
        for module in report["imported_modules"].values():
            installed = Path(module).resolve()
            require(
                not installed.is_relative_to(ledger.ROOT.resolve())
                and any(installed.is_relative_to(root) for root in roots),
                "Installed module came from source checkout",
            )
        require(
            record["attempts"][-1]["commands"][-1]["returncode"] == 0,
            "Installed checker process failed",
        )
    return {
        "candidate": "0.3.0a1",
        "combinations": 8,
        "source_transport": transport,
        "evidence_refs": [_ref(path), *[_ref(a["path"]) for a in summary["artifacts"].values()]],
    }


def docs_budget_check():
    from .delivery import equivalent_text

    references = []
    for slug, code_paths in (
        ("L0012-reoptimizable-lp", ("src/silo/lp/session.py", "src/silo/lp/general.py")),
        (
            "L0015-sparse-basis-updates",
            ("src/silo/lp/sparse_factor.py", "src/silo/lp/sparse_kernel.py"),
        ),
    ):
        folder = ledger.ROOT / "learning/lessons" / slug
        lesson = folder / "README.md"
        text = lesson.read_text(encoding="utf-8")
        parts = text.split("---", 2)
        require(len(parts) == 3, f"Lesson metadata missing: {slug}")
        front = parts[1]
        require(
            re.search(r"^status:\s*checked\s*$", front, re.MULTILINE),
            f"Lesson remains draft/unverified: {slug}",
        )
        match = re.search(r"^verified_code:\s*([0-9a-f]{40})\s*$", front, re.MULTILINE)
        require(
            match is not None
            and re.search(r"^verified_on:\s*\d{4}-\d{2}-\d{2}\s*$", front, re.MULTILINE),
            "Lesson lacks actual verification metadata",
        )
        for name in code_paths:
            committed = subprocess.check_output(
                ["git", "show", f"{match[1]}:{name}"], cwd=ledger.ROOT
            )
            equivalent_text(committed, (ledger.ROOT / name).read_bytes())
        for name in ("README.md", "exercises.md", "solutions.md"):
            references.append(_ref(folder / name))
    for name in ("README.md", "docs/installation.md"):
        require(
            "0.3.0a1" in (ledger.ROOT / name).read_text(encoding="utf-8"),
            "Current entry still points at old candidate",
        )
        references.append(_ref(ledger.ROOT / name))
    references.extend(
        _ref(ledger.ROOT / name)
        for name in (
            "learning/CATALOG.md",
            "docs/sparse_matrix_contract.md",
            "docs/sparse_basis_session_contract.md",
            "docs/sparse_validation_contract.md",
            "tasks/reports/20261024-02-01_sparse-lp-program_report.md",
        )
    )
    return {
        "budget": ledger.totals(),
        "lessons_verified_against_actual_code": True,
        "evidence_refs": references,
    }


def _item(identifier, name, function):
    try:
        facts = function()
        return {
            "id": identifier,
            "name": name,
            "pass": True,
            "facts": facts,
            "evidence_refs": facts["evidence_refs"],
        }
    except (
        AssertionError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.CalledProcessError,
    ) as exc:
        return {
            "id": identifier,
            "name": name,
            "pass": False,
            "failure": f"{type(exc).__name__}: {exc}",
            "evidence_refs": [],
        }


def sp4():
    def historical_and_quality():
        historical, quality = historical_check(), quality_check()
        return {
            "historical": historical,
            "quality": quality,
            "evidence_refs": historical["evidence_refs"] + quality["evidence_refs"],
        }

    items = [
        _item(i, name, function)
        for i, name, function in (
            (1, "preimplementation_freeze", frozen_sp1_gate),
            (2, "end_to_end_sparse_lp", capacity_check),
            (3, "real_basis_updates", mechanism_check),
            (4, "four_edit_correctness_and_speed", warm_check),
            (5, "sparse_mip_and_cg", mip_cg_check),
            (6, "old_behavior_and_identity", historical_and_quality),
            (7, "candidate_and_eight_installs", delivery_check),
            (8, "learning_report_and_budget", docs_budget_check),
        )
    ]
    return {
        "items": items,
        "mechanical_checks_pass": all(item["pass"] for item in items),
        "unmet_ids": [item["id"] for item in items if not item["pass"]],
        "technical_review_required": True,
    }


IMPLEMENTERS = {
    "/root",
    "/root/sparse_matrix_proof",
    "/root/sparse_factor_kernel",
    "/root/sparse_sp1_inputs",
}


def validate_final_review(review, items, current=None):
    require(
        review["schema_version"] == 1
        and review["program"] == ledger.PROGRAM
        and review["decision"] == "GO",
        "Independent final technical GO missing",
    )
    reviewer = review["reviewer"]
    require(
        isinstance(reviewer["id"], str)
        and reviewer["id"]
        and reviewer["id"] not in IMPLEMENTERS
        and reviewer["independent"] is True
        and reviewer["read_only"] is True
        and reviewer["files_modified"] == []
        and reviewer["write_attempts"] == 0,
        "Final reviewer is not independent/read-only",
    )
    require(review["unresolved_required"] == [], "Independent review retains required obligations")
    source_match(review["source"], current)
    require(
        len(items) == 8
        and [item["id"] for item in items] == list(range(1, 9))
        and all(item["pass"] for item in items),
        "Mechanical eight-item gate incomplete",
    )
    criteria = review["criteria"]
    require(
        len(criteria) == 8 and {c["id"] for c in criteria} == set(range(1, 9)),
        "Independent review lacks eight unique criteria",
    )
    for criterion in criteria:
        require(criterion["decision"] == "GO", f"Review criterion{criterion['id']} is not GO")
        supplied = {(r["path"], r["sha256"]) for r in criterion["evidence"]}
        required = {(r["path"], r["sha256"]) for r in items[criterion["id"] - 1]["evidence_refs"]}
        require(
            required and required <= supplied,
            "Independent review evidence differs from mechanical item",
        )
        for ref in criterion["evidence"]:
            _bound(ref["path"], ref["sha256"])
    _bound(review["review_record"]["path"], review["review_record"]["sha256"])
    return {"reviewer": reviewer["id"], "criteria": 8, "decision": "GO"}


def final():
    checks = sp4()
    report = {"schema_version": 1, "source": ledger.identity(), **checks, "overall_complete": False}
    try:
        require(
            checks["mechanical_checks_pass"],
            "One or more of the eight mandatory items remain unmet",
        )
        path = ledger.OUT / "reviews/final_technical_go.json"
        review = _read(path)
        report["technical_review"] = validate_final_review(review, checks["items"])
        report["technical_review_ref"] = _ref(path)
        report["overall_complete"] = True
    except (AssertionError, OSError, ValueError, KeyError, TypeError) as exc:
        report["final_failure"] = f"{type(exc).__name__}: {exc}"
    folder = ledger.OUT / "evaluation"
    folder.mkdir(exist_ok=True)
    path = folder / f"final_{ledger.utc().replace(':', '-')}.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "overall_complete": report["overall_complete"],
                "unmet_ids": checks["unmet_ids"],
                "report": str(path),
            }
        )
    )
    return 0 if report["overall_complete"] else 1


def evaluate(stage):
    try:
        function = {"SP1": sp1, "SP2": sp2, "SP3": sp3, "SP4": sp4}[stage]
        checks = function()
        passed = checks["mechanical_checks_pass"] if stage == "SP4" else True
        value = {
            "stage": stage,
            "mechanical_checks_pass": passed,
            "checks": checks,
            "source": ledger.identity(),
            "technical_review_required": True,
        }
        code = 0 if passed else 1
    except (
        AssertionError,
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.CalledProcessError,
    ) as exc:
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
