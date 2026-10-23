"""Run the frozen M5 matrix; generated evidence stays under ignored outputs/.

Groups are separate so the 64 diagnostics are called only once, after core fixes.
Each scale solve runs in a fresh process with the frozen hard wall limit. The
persistent ledger caps full scale runs at three and diagnostics at 64 calls.
"""

import argparse
import copy
import json
import os
import platform
import subprocess
import sys
from collections import Counter
from dataclasses import replace
from fractions import Fraction as F
from pathlib import Path
from time import perf_counter
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
for thread_variable in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[thread_variable] = "1"

import evidence as ev  # noqa: E402
from validate_results import TOL, close, primal, validate  # noqa: E402

from silo import SolveOptions, solve  # noqa: E402
from silo.io import model_from_dict  # noqa: E402


def write_json(path, value):
    path.write_text(
        json.dumps(ev.json_ready(value), indent=2, allow_nan=False) + "\n", encoding="utf-8"
    )


def environment():
    import numpy

    return {
        "python": sys.version,
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "numpy": numpy.__version__,
        "threads": {
            name: os.environ[name]
            for name in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS")
        },
        "commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_hashes": {
            str(path.relative_to(ROOT)): ev.sha256(path.read_bytes())
            for path in sorted((ROOT / "src/silo").rglob("*.py"))
        },
        "runner_sha256": ev.sha256(Path(__file__).read_bytes()),
        "checker_sha256": ev.sha256(Path(__file__).with_name("validate_results.py").read_bytes()),
        "seed": 20261023,
    }


class Runner:
    def __init__(self, folder, ledger, evidence):
        self.folder, self.ledger, self.evidence = folder, ledger, evidence
        self.records, self.native_calls = [], 0
        self.entries = {entry["id"]: entry for entry in ev.load_manifest()["cases"]}

    def native(self, payload, options, basis=None):
        self.native_calls += 1
        return solve(model_from_dict(payload), SolveOptions(**options), basis=basis)

    def record(self, identifier, function):
        start = perf_counter()
        before = self.native_calls
        try:
            data = function()
            record = {"id": identifier, "pass": True, **data}
        except Exception as exc:
            record = {"id": identifier, "pass": False, "error": f"{type(exc).__name__}: {exc}"}
        record.update(wall_seconds=perf_counter() - start, native_calls=self.native_calls - before)
        self.records.append(record)
        with (self.folder / "records.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(ev.json_ready(record), allow_nan=False) + "\n")
        print(json.dumps({key: record[key] for key in ("id", "pass", "wall_seconds")}), flush=True)

    def case(self, entry):
        entry = {**self.entries[entry["id"]], **entry}
        payload = ev.raw_payload(entry)
        assert ev.digest(payload) == entry["model_sha256"]
        options = dict(entry["options"])
        scale = entry["suite"] in ("lp_scale", "milp_scale")
        if scale:
            limit = 20 if entry["suite"] == "lp_scale" else 60
            options.update(time_limit=limit, node_limit=100000)
            request, response = (
                self.folder / f"{entry['id']}_input.json",
                self.folder / f"{entry['id']}_output.json",
            )
            write_json(request, {"payload": payload, "options": options})
            self.native_calls += 1
            start = perf_counter()
            process = subprocess.run(
                [
                    sys.executable,
                    str(Path(__file__).resolve()),
                    "--solve-one",
                    str(request),
                    "--response",
                    str(response),
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
                timeout=limit,
            )
            assert process.returncode == 0, process.stderr
            output = json.loads(response.read_text(encoding="utf-8"))
            assert perf_counter() - start < limit, "Frozen hard wall exceeded"
        else:
            output = self.native(payload, options).to_dict()
            write_json(self.folder / f"{entry['id']}_output.json", output)
        check = validate(payload, output, entry["truth"])
        return {
            "suite": entry["suite"],
            "model_sha256": entry["model_sha256"],
            "variables": entry["variables"],
            "rows": entry["rows"],
            "options": options,
            "check": check,
            "result_file": f"{entry['id']}_output.json",
        }

    def boundary(self, boundary, reference):
        identifier, data = boundary["id"], boundary["input"]
        assert ev.digest(data) == boundary["input_sha256"]
        if data["format"] == "mps":
            path = self.folder / f"{identifier}.mps"
            path.write_text(data["text"], encoding="utf-8")
            process = subprocess.run(
                [sys.executable, "-m", "silo", "optimize", str(path)],
                capture_output=True,
                text=True,
                cwd=ROOT,
                check=False,
                env={**os.environ, "PYTHONPATH": str(ROOT / "src")},
            )
            assert process.returncode == (7 if identifier == "B22" else 6), process.stderr
            output = json.loads(process.stdout)
        else:
            payload = copy.deepcopy(data["model"])
            action, basis = data.get("action") or {}, None
            if action.get("type") in (
                "stale_basis",
                "singular_basis",
                "rhs",
                "append_row",
                "append_column",
            ):
                initial = self.native(payload, data["options"])
                assert initial.status == "optimal" and initial.basis is not None
                basis = initial.basis
                if action["type"] == "stale_basis":
                    basis = (999,)
                elif action["type"] == "singular_basis":
                    basis = replace(
                        basis, basic_keys=(basis.basic_keys[0],) * len(basis.basic_keys)
                    )
                else:
                    payload = ev.modified_boundary_payload(boundary)
            if action.get("type") == "nonfinite":
                model = model_from_dict(payload)
                model.objective.coefficients["x"] = float("nan")
                self.native_calls += 1
                output = solve(model, SolveOptions(**data["options"])).to_dict()
            else:
                output = self.native(payload, data["options"], basis).to_dict()
            assert output["status"] == reference["expected_status"], output["termination_reason"]
            if identifier in ("B07", "B08", "B09", "B10", "B11"):
                assert (
                    output["termination_reason"]
                    == reference["assertions"]["expected_termination_reason"]
                )
                if output["has_primal_solution"]:
                    point, _ = primal(payload, output["primal_values"])
                    close(
                        output["objective_value"], ev.objective(payload, point), "Limit incumbent"
                    )
                if identifier == "B07":
                    assert output["dual_bound_kind"] == "negative_infinity"
                    assert output["absolute_gap"] is output["relative_gap"] is None
                else:
                    optimum = reference["reference_objective"]
                    if output["dual_bound"] is not None:
                        assert F(output["dual_bound"]) <= optimum + TOL * (1 + abs(optimum))
                    if output["primal_bound"] is not None:
                        assert F(output["primal_bound"]) >= optimum - TOL * (1 + abs(optimum))
                    if identifier == "B11":
                        assert output["has_primal_solution"]
                        gap = abs(output["primal_bound"] - output["dual_bound"])
                        assert output["relative_gap"] == gap / max(
                            1, abs(output["primal_bound"]), abs(output["dual_bound"])
                        )
                        assert output["relative_gap"] <= 1
                    elif not output["has_primal_solution"]:
                        assert output["relative_gap"] is None
                if identifier == "B08":
                    assert output["nodes"] == 0
                if identifier == "B09":
                    assert output["diagnostics"]["lp_calls"] == 0
                if identifier == "B10":
                    assert output["iterations"] == 0
            elif output["status"] in ("optimal", "infeasible", "unbounded"):
                proof = reference["proof"]
                if "status" not in proof:  # independently proved empty integer interval
                    proof = {"status": "infeasible"}
                validate(payload, output, proof)
            else:
                assert not output["has_primal_solution"]
        assert output["status"] == reference["expected_status"]
        diagnostics, observed = output["diagnostics"], {}
        if identifier in ("B14", "B19"):
            assert diagnostics["cold_starts"] == 1 and diagnostics["fallback_reason"]
            observed["fallback_reason"] = diagnostics["fallback_reason"]
            if identifier == "B19":
                observed["design_note"] = (
                    "Frozen duplicate-basis rejection precedes QR; distinct singular QR "
                    "recovery is the recorded M2 test."
                )
        if identifier == "B15":
            assert diagnostics["warm_mode"] == "dual"
            observed.update(
                warm_mode=diagnostics["warm_mode"],
                dual_pivots=diagnostics["dual_pivots"],
                design_note=(
                    "This input enters dual simplex with zero pivots; "
                    "positive pivots are covered by the recorded M2 example."
                ),
            )
        if identifier == "B18":
            unscaled = self.native(payload, {**data["options"], "scaling": False}).to_dict()
            validate(payload, unscaled, reference["proof"])
            close(unscaled["objective_value"], F(output["objective_value"]), "Scaling invariance")
            observed["scaled_and_unscaled_checked"] = True
        if identifier == "B13":
            observed.update(
                fractional_point_removed=False,
                mechanism_triggered=False,
                design_note=(
                    "Frozen small_milp4 has an integral root. Original objective/feasible "
                    "slices checked here; actual mixed GMI 1.5->2 is separately "
                    "recorded from the predeclared M3 case."
                ),
            )
        if identifier == "B12":
            nodes = {n["node"]: n for n in diagnostics["node_log"]}
            for node in nodes.values():
                ancestry, current = set(), node
                while current is not None:
                    ancestry.add(current["node"])
                    current = nodes.get(current["parent"])
                assert set(node["local_cut_origins"]) <= ancestry
            assert all(
                event.get("scope", "node_local") == "node_local"
                for event in diagnostics["cut_events"]
            )
        write_json(self.folder / f"{identifier}_output.json", output)
        return {
            "input_sha256": boundary["input_sha256"],
            "status": output["status"],
            "observed": observed,
            "frozen_assertions": reference["assertions"],
            "result_file": f"{identifier}_output.json",
        }

    def diagnostic(self, record, cold):
        entry = self.entries[record["case_id"]]
        base = ev.diagnostic_payload(ev.raw_payload(entry), record["prepare_model"])
        payload = ev.diagnostic_payload(base, record["actions"])
        assert ev.digest(payload) == record["model_sha256"]
        basis = None
        if record["actions"][-1]["basis"] == "shared_cold":
            basis = cold[record["case_id"]].basis
            if record["variant"] == "invalid_basis_fallback":
                basis = (999,)
        self.ledger["diagnostic_calls"] += 1
        assert self.ledger["diagnostic_calls"] <= 64
        write_json(ROOT / "outputs/prototype/run_ledger.json", self.ledger)
        result = self.native(payload, record["options"], basis)
        if record["variant"] == "cold":
            cold[record["case_id"]] = result
        output = result.to_dict()
        write_json(self.folder / f"{record['id']}_output.json", output)
        check = validate(payload, output, record["reference_proof"])
        stats = result.diagnostics
        if record["case_id"].startswith("LP"):
            warm = record["expected"]["reuse_attempt_required"]
            if warm:
                assert stats.get("warm_starts", 0) + bool(stats.get("fallback_reason")) == 1
                if stats.get("fallback_reason"):
                    assert stats["cold_starts"] == 1
                else:
                    assert stats["warm_starts"] == 1 and stats["cold_starts"] == 0
            if record["variant"] == "invalid_basis_fallback":
                assert stats["fallback_reason"] and stats["cold_starts"] == 1
        else:
            assert stats["cuts_enabled"] == record["options"]["cuts"]
            assert stats["heuristics_enabled"] == record["options"]["heuristics"]
            if not record["options"]["cuts"]:
                assert stats["gmi_attempts"] == stats["cuts_added"] == 0
            if not record["options"]["heuristics"]:
                assert stats["heuristic_calls"] == 0
        write_json(self.folder / f"{record['id']}_output.json", output)
        return {
            "model_sha256": record["model_sha256"],
            "options": record["options"],
            "check": check,
            "actual_diagnostics": stats,
        }

    def integration(self):
        from silo.decomposition.general_master import covering_example
        from silo.mip.research_example import run_example

        cg, mip = covering_example().to_dict(), run_example()
        assert cg["status"] == mip["status"] == "optimal"
        close(cg["objective_value"], F(5, 2), "Full-pool CG optimum")
        close(mip["objective"], F(-17, 2), "Policy optimum")
        assert mip["policy_invocations"]["node_selector"] > 0
        frozen = ev.load_manifest()["integrations"]
        assert mip["input_sha256"] == frozen["mip_policy"]["input_sha256"]
        assert cg["input_sha256"] == frozen["finite_cg"]["input_sha256"]
        self.native_calls += len(cg["trace"]) + 1
        # These calls are the two integrations, never part of the64 diagnostics.
        return {"cg": cg, "mip": mip, "integration_examples": 2}

    def recorded_mechanisms(self):
        from silo.lp.session import LPSession

        recipes = ev.frozen_modules()[0]
        payload = recipes["model"](
            [recipes["variable"]("x", 0, 3, "integer"), recipes["variable"]("y", 0, 4)],
            [recipes["row"]("d", {"x": 2, "y": 1}, ">=", 3)],
            {"x": 1, "y": 1},
        )
        truth = ev.small_truth(payload, "milp_small")
        off = self.native(payload, {"presolve": False, "cuts": False, "heuristics": False})
        on = self.native(payload, {"presolve": False, "cuts": True, "heuristics": False})
        validate(payload, off.to_dict(), truth)
        validate(payload, on.to_dict(), truth)
        assert on.diagnostics["cuts_added"] > 0
        event = on.diagnostics["cut_events"][0]
        assert event["before"] == 1.5 and abs(event["after"] - 2) < 1e-7
        proof = event["proofs"][0]
        a, b = list(map(F, proof["original_coefficients"])), F(proof["original_lower"])
        assert a[0] * F(3, 2) < b
        for x in range(4):
            for y in (max(F(0), 3 - 2 * x), F(4)):
                if 2 * x + y >= 3:
                    assert a[0] * x + a[1] * y >= b
        warm_payload = recipes["model"](
            [recipes["variable"]("x", 0, 2), recipes["variable"]("y", 0, 1.5)],
            [recipes["row"]("r", {"x": 1, "y": 1}, "<=", 2)],
            {"x": -1, "y": -2},
            3,
        )
        session = LPSession(
            model_from_dict(warm_payload), SolveOptions(presolve=False, scaling=False)
        )
        initial = session.solve()
        session.change_rhs("r", 1)
        warm = session.solve()
        self.native_calls += 2
        assert initial.status == warm.status == "optimal"
        changed = ev.diagnostic_payload(warm_payload, [{"type": "rhs", "row": "r", "rhs": 1}])
        validate(changed, warm.to_dict(), ev.small_truth(changed, "lp_small"))
        assert warm.diagnostics["warm_mode"] == "dual" and warm.diagnostics["dual_pivots"] > 0
        return {
            "evidence_role": "Replay of already recorded M2/M3 mechanism cases; not B13/B15 inputs",
            "recorded_commit": "8a07e4b211795c60bf77bfabda1b90a0b2f3f04c",
            "gmi_source": "tests/unit/test_prototype_mip.py::mixed_model",
            "warm_source": "tests/unit/test_prototype_lp.py::base",
            "gmi_input_sha256": ev.digest(payload),
            "warm_input_sha256": ev.digest(warm_payload),
            "mixed_gmi_trace": event,
            "integer_slice_endpoints_verified": True,
            "positive_dual_pivot_trace": warm.to_dict(),
        }

    def external(self, entry):
        from silo.interfaces.highs import compare_with_highs

        entry = {**self.entries[entry["id"]], **entry}
        source = self.folder.parent / "core" / f"{entry['id']}_output.json"
        assert source.exists(), "Run core in the sibling core folder first."
        output = json.loads(source.read_text(encoding="utf-8"))
        comparison = compare_with_highs(
            model_from_dict(ev.raw_payload(entry)),
            SimpleNamespace(**output),
            SolveOptions(time_limit=20),
        )
        assert comparison["status_match"]
        if entry["expected_status"] == "optimal":
            assert comparison["optimal_comparison_passed"]
        return comparison


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--group", choices=("core", "diagnostics", "integrations", "external"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--solve-one", type=Path)
    parser.add_argument("--response", type=Path)
    args = parser.parse_args()
    if args.solve_one:
        request = json.loads(args.solve_one.read_text(encoding="utf-8"))
        output = solve(
            model_from_dict(request["payload"]), SolveOptions(**request["options"])
        ).to_dict()
        write_json(args.response, output)
        return 0
    if not args.group or not args.output:
        parser.error("--group and --output are required")
    folder = args.output.resolve()
    if not folder.is_relative_to((ROOT / "outputs").resolve()):
        parser.error("Generated evidence must stay under ignored outputs/")
    folder.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    ledger_path = ROOT / "outputs/prototype/run_ledger.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    ledger = (
        json.loads(ledger_path.read_text())
        if ledger_path.exists()
        else {"scale_runs": 0, "diagnostic_calls": 0}
    )
    evidence = ev.build_evidence()
    write_json(folder / "raw_evidence.json", evidence)
    write_json(folder / "environment.json", environment())
    runner = Runner(folder, ledger, evidence)
    if args.group == "core":
        for entry in evidence["cases"]:
            if entry["suite"].endswith("small"):
                runner.record(entry["id"], lambda e=entry: runner.case(e))
        for boundary, reference in zip(
            ev.load_manifest()["boundaries"], evidence["boundaries"], strict=True
        ):
            runner.record(boundary["id"], lambda b=boundary, r=reference: runner.boundary(b, r))
        ledger["scale_runs"] += 1
        assert ledger["scale_runs"] <= 3, "Scale run cap exhausted"
        write_json(ledger_path, ledger)
        for entry in evidence["cases"]:
            if entry["suite"].endswith("scale"):
                runner.record(entry["id"], lambda e=entry: runner.case(e))
    elif args.group == "diagnostics":
        assert ledger["diagnostic_calls"] == 0, "Diagnostic calls already issued; inspect ledger"
        cold = {}
        for record in evidence["diagnostics"]:
            runner.record(record["id"], lambda r=record: runner.diagnostic(r, cold))
    elif args.group == "integrations":
        runner.record("two_integrations", runner.integration)
        runner.record("recorded_M2_M3_mechanisms", runner.recorded_mechanisms)
    else:
        for entry in evidence["cases"]:
            if entry["suite"].endswith("small"):
                runner.record(entry["id"], lambda e=entry: runner.external(e))
    summary = {
        "group": args.group,
        "all_pass": all(r["pass"] for r in runner.records),
        "records": len(runner.records),
        "failed": [r for r in runner.records if not r["pass"]],
        "native_calls": runner.native_calls,
        "ledger": ledger,
        "verification_wall_seconds": perf_counter() - started,
        "passed_by_suite": dict(
            Counter(r.get("suite", args.group) for r in runner.records if r["pass"])
        ),
    }
    write_json(folder / "summary.json", summary)
    print(json.dumps(summary, indent=2), flush=True)
    return 0 if summary["all_pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
