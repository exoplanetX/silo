"""Frozen group dispatch and actual native case receipts."""

import importlib
import json
import sys
from fractions import Fraction
from pathlib import Path
from time import perf_counter
from uuid import uuid4

from . import checker, ledger
from .resources import guarded


def manifest():
    return json.loads((ledger.ROOT / "tests/fixtures/sparse_program_manifest.json").read_text())


def read_payload(entry):
    path = ledger.ROOT / entry["payload_path"]
    assert ledger.sha(path) == entry["payload_sha256"]
    return json.loads(path.read_text())


def oracle(entry, chain=None):
    """Bind the independent reference and its raw witness to this frozen payload."""
    path = ledger.ROOT / "tests/fixtures/sparse_program_oracles.json"
    frozen = json.loads(path.read_text())
    assert frozen["manifest_sha256"] == ledger.sha(
        ledger.ROOT / "tests/fixtures/sparse_program_manifest.json"
    )
    if chain is None:
        record = frozen["cases"][entry["id"]]
    else:
        record = frozen["trajectories"][chain]["states"][entry["id"]]
    assert record["payload_sha256"] == entry["payload_sha256"]
    assert ledger.sha(ledger.ROOT / record["witness_path"]) == record["witness_sha256"]
    return record["truth"]


def check_exit(entry, packet):
    """Bind frozen resource categories to the unchanged public resource_limit."""
    result = packet["result"]
    expected = entry.get("metadata", {}).get("expected_reason")
    if expected is None:
        return None
    if expected not in ("sparse_nnz_limit", "factor_nnz_limit"):
        assert result["termination_reason"] == expected
        return {"expected_category": expected, "public_reason": result["termination_reason"]}
    assert (result["status"], result["termination_reason"]) == ("limit", "resource_limit")
    diagnostic = result["diagnostics"]
    message = diagnostic.get("resource_message", diagnostic.get("message", ""))
    name = "max_sparse_nnz" if expected == "sparse_nnz_limit" else "max_factor_nnz"
    assert packet["options"][name] == 0 and name in message
    calls = packet["native_lp_calls_completed"]
    if expected == "sparse_nnz_limit":
        assert (calls == 0 and entry["statistics"]["matrix_nonzeros"] > 0) or (
            calls == 1 and diagnostic.get("normalized_nnz", 0) > 0
        )
    else:
        assert calls == 1 and diagnostic["standard_nnz"] > 0
        assert diagnostic["base_factorizations"] == 0
    return {
        "expected_category": expected,
        "public_reason": "resource_limit",
        "resource_option": name,
        "resource_value": 0,
        "lp_calls": calls,
        "diagnostic_message": message,
    }


def check_inputs():
    from .cases import build_cases, build_trajectories, sha

    frozen = manifest()
    actual = {c["id"]: c for c in build_cases(True)}
    assert len(actual) == len(frozen["cases"]) == 120
    for entry in frozen["cases"]:
        assert sha(actual[entry["id"]]["payload"]) == entry["payload_sha256"]
        if "candidate_sha256" in entry:
            assert sha(actual[entry["id"]]["candidate"]) == entry["candidate_sha256"]
        read_payload(entry)
    assert len(build_trajectories()) == 8
    for chain in frozen["trajectories"]:
        assert len(chain["states"]) == 20
        assert ledger.sha(ledger.ROOT / chain["initial_path"]) == chain["initial_sha256"]
        for state in chain["states"]:
            read_payload(state)
    print(json.dumps({"input_check": "passed", "cases": 120, "states": 160, "native_calls": 0}))
    return 0


def native_one(request_path, response_path):
    request = json.loads(Path(request_path).read_text())
    entry = request["entry"]
    payload = read_payload(entry)
    response = Path(response_path)
    start = perf_counter()

    # Comparison optimizers are unavailable to the native path even when the
    # selected sparse engine legitimately imports scipy.sparse/linalg.
    def forbidden(*args, **kwargs):
        raise AssertionError("External optimizer called by native solver")

    try:
        import scipy.optimize

        scipy.optimize.linprog = scipy.optimize.milp = forbidden
    except ImportError:
        pass
    sys.path.insert(0, str(ledger.ROOT / "src"))
    from silo import SolveOptions, solve
    from silo.io import model_from_dict

    counts = {"lp_started": 0, "lp_completed": 0}
    general = importlib.import_module("silo.lp.general")
    original_lp = general.solve_lp_data

    def counted_lp(*args, **kwargs):
        counts["lp_started"] += 1
        number = counts["lp_started"]
        path = response.with_suffix(".lp_calls.jsonl")
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps({"number": number, "event": "started"}) + "\n")
        value = original_lp(*args, **kwargs)
        counts["lp_completed"] += 1
        with path.open("a", encoding="utf-8") as stream:
            stream.write(
                json.dumps(
                    {
                        "number": number,
                        "event": "completed",
                        "status": value.status,
                        "engine": value.diagnostics.get("lp_engine"),
                    }
                )
                + "\n"
            )
        return value

    general.solve_lp_data = counted_lp
    importlib.import_module("silo.solver").solve_lp_data = counted_lp
    importlib.import_module("silo.lp.session").solve_lp_data = counted_lp

    options = dict(entry.get("options", {}))
    options["time_limit"] = min(options.get("time_limit", request["seconds"]), request["seconds"])
    if request["engine"] == "sparse":
        options["lp_engine"] = "sparse"
    response.with_suffix(".started.json").write_text(
        json.dumps(
            {"id": entry["id"], "native_root_calls_started": 1, "engine": request["engine"]}
        ),
        encoding="utf-8",
    )
    if entry["group"] == "cg":
        from silo.decomposition.general_master import (
            FiniteColumnPricer,
            GeneralRestrictedMaster,
            MasterColumn,
            column_generation,
        )

        pool = [MasterColumn(c["name"], c["cost"], c["coefficients"]) for c in entry["pool"]]
        result = column_generation(
            GeneralRestrictedMaster(model_from_dict(payload), SolveOptions(**options)),
            FiniteColumnPricer(pool),
        )
    else:
        result = solve(model_from_dict(payload), SolveOptions(**options))
    packet = {
        "id": entry["id"],
        "engine": request["engine"],
        "options": options,
        "native_root_calls_started": 1,
        "native_root_calls_completed": 1,
        "native_lp_calls_started": counts["lp_started"],
        "native_lp_calls_completed": counts["lp_completed"],
        "native_seconds_including_import": perf_counter() - start,
        "result": result.to_dict(),
    }
    response.write_text(json.dumps(packet, allow_nan=False), encoding="utf-8")
    return 0


def execute_group(args):
    import subprocess

    frozen_paths = [
        "scripts/sparse_program/cases.py",
        "scripts/sparse_program/netlib_data.py",
        "tests/fixtures/sparse_program_manifest.json",
        "tests/fixtures/sparse_program_sources.json",
    ]
    subprocess.run(
        ["git", "ls-files", "--error-unmatch", *frozen_paths],
        cwd=ledger.ROOT,
        check=True,
        stdout=subprocess.DEVNULL,
    )
    assert not subprocess.check_output(
        ["git", "diff", "--name-only", "--", *frozen_paths], cwd=ledger.ROOT
    )
    if args.command != "baseline":
        assert any(
            e["kind"] == "stage_gate" and e.get("stage") == "SP1" and e.get("decision") == "GO"
            for e in ledger.history()
        ), "SP1 GO is required before product validation"
    source = ledger.identity()
    frozen = manifest()
    if args.command == "baseline":
        ids = {
            "NETLIB-" + s
            for s in ("AFIRO", "ADLITTLE", "BLEND", "SC50A", "SC50B", "SC105", "SC205", "SHARE2B")
        }
        entries = [c for c in frozen["cases"] if c["id"] in ids]
        assert len(entries) == 8
    elif args.group == "sp2-smoke":
        ids = {"NETLIB-" + s for s in ("AFIRO", "ADLITTLE", "SC50A", "SC50B")}
        ids.update(("CAP-FLOW-01", "CAP-TRANS-01"))
        entries = [c for c in frozen["cases"] if c["id"] in ids]
    else:
        groups = {"mip", "cg"} if args.group == "mip-cg" else {args.group}
        entries = [c for c in frozen["cases"] if c["group"] in groups]
    folder = ledger.OUT / "groups" / (str(uuid4()))
    folder.mkdir(parents=True)
    records = []
    for entry in entries:
        seconds = (
            120
            if entry["group"] in ("capacity", "netlib")
            else 60
            if entry["group"] in ("mip", "cg", "mechanism")
            else 10
        )
        request, output = (
            folder / (entry["id"] + ".request.json"),
            folder / (entry["id"] + ".result.json"),
        )
        request.write_text(
            json.dumps({"entry": entry, "engine": args.engine, "seconds": seconds}),
            encoding="utf-8",
        )
        monitor = guarded(
            [
                sys.executable,
                str(ledger.ROOT / "scripts/sparse_program.py"),
                "_native-one",
                "--request",
                str(request),
                "--response",
                str(output),
            ],
            ledger.ROOT,
            folder / (entry["id"] + ".console.log"),
            seconds,
        )
        record = {
            "id": entry["id"],
            "monitor": monitor,
            "result_path": str(output.relative_to(ledger.ROOT)),
            "input_sha256": entry["payload_sha256"],
            "pass": False,
            "request_sha256": ledger.sha(request),
        }
        if output.exists():
            record["result_sha256"] = ledger.sha(output)
        try:
            assert monitor["exit_code"] == 0 and monitor["guard_reason"] is None
            packet = json.loads(output.read_text())
            result = packet["result"]
            assert packet["native_lp_calls_started"] == packet["native_lp_calls_completed"]
            record["native_lp_calls"] = packet["native_lp_calls_completed"]
            assert result["status"] in entry["expected_statuses"]
            record["exit_check"] = check_exit(entry, packet)
            if entry["group"] != "cg":
                record["raw_check"] = checker.check(
                    read_payload(entry),
                    result,
                    truth=None if args.command == "baseline" else oracle(entry),
                    options=packet["options"],
                    mip=entry["group"] == "mip",
                )
                if result["status"] in ("infeasible", "unbounded"):
                    record["exact_witness_check"] = checker.certificate(read_payload(entry), result)
            else:
                from .oracles import full_pool_payload, primal_dual_pair

                if result["status"] == "optimal":
                    proof = result["witness"]
                    assert proof["kind"] == "finite_pool_optimality"
                    record["full_pool_exact_check"] = primal_dual_pair(
                        full_pool_payload({**entry, "payload": read_payload(entry)}),
                        {
                            k: {n: Fraction(v) for n, v in proof[k].items()}
                            for k in ("point", "row_duals")
                        },
                    )
                else:
                    assert result.get("dual_bound") is None or result.get("dual_bound_is_infinite")
            if args.engine == "sparse":
                metadata = entry.get("metadata", {})
                if entry["group"] == "cg":
                    trace = result["trace"]
                    assert len(trace) == packet["native_lp_calls_completed"]
                    assert all(
                        step["lp_diagnostics"].get("lp_engine") == "sparse" for step in trace
                    )
                    if metadata.get("require_phase1_added_column"):
                        assert any(
                            step["phase"] == "phase1" and step["added_columns"] for step in trace
                        )
                    if metadata.get("require_phase2_cross_solve_reuse"):
                        assert any(
                            step["phase"] == "phase2"
                            and step["lp_diagnostics"].get("cross_solve_reuses", 0) > 0
                            for step in trace
                        )
                    if result["status"] == "optimal":
                        checker.close(result["objective_value"], oracle(entry)["objective"])
                else:
                    counters = result["diagnostics"]
                    if entry["group"] == "mip":
                        assert counters["lp_engine_counts"]["sparse"] == counters["lp_calls"]
                        assert counters["lp_engine_counts"]["dense"] == 0
                        if metadata.get("require_branch"):
                            assert counters["branches"] > 0
                        if metadata.get("require_gmi"):
                            assert counters["cuts_added"] > 0
                            assert any(
                                event["lp_engine"] == "sparse" and event["status"] == "optimal"
                                for event in counters["cut_events"]
                            )
                    if metadata.get("minimum_pivots"):
                        assert result["iterations"] >= metadata["minimum_pivots"]
                    if metadata.get("stable_update_group"):
                        assert counters["eta_updates"] / counters["basis_replacements"] >= 0.7
            record["status"] = result["status"]
            record["pass"] = True
        except (AssertionError, ValueError, OSError, KeyError, TypeError) as exc:
            record["failure"] = f"{type(exc).__name__}: {exc}"
        records.append(record)
        with (folder / "records.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record) + "\n")
        print(json.dumps({"id": record["id"], "pass": record["pass"]}), flush=True)
    assert ledger.identity()["source"] == source["source"], "Source changed during fixed group"
    summary = {
        "command": args.command,
        "group": getattr(args, "group", "overlap"),
        "engine": args.engine,
        "records": records,
        "all_pass": all(r["pass"] for r in records),
        "source": source,
        "baseline_failures_retained": args.command == "baseline",
    }
    (folder / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    return 0 if summary["all_pass"] or args.command == "baseline" else 1


def dispatch(args):
    if args.command == "check-inputs":
        return check_inputs()
    if args.command in ("baseline", "run"):
        if getattr(args, "group", None) == "historical":
            from .historical import run

            return run()
        return execute_group(args)
    if args.command == "warm":
        from .warm import execute

        return execute(args)
    if args.command == "evaluate":
        from .evaluation import evaluate

        return evaluate(args.stage)
    if args.command == "install-checks":
        from .delivery import execute

        return execute(args)
    raise RuntimeError(f"Stage adapter is not yet implemented: {args.command}")
