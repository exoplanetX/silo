"""Repeat the frozen seed-20261024 independent audit, without its old run ledger.

The 192 payloads, random draw order, two configurations, direct SciPy/HiGHS calls
and 48 pure-IP enumerations come from outputs/audit_20261024/independent_probe.py.
Before any solver import/call, generated JSON bytes must match the original SHA.
Its serialization profile is indent=2, CRLF, UTF-8, no final newline.

Default/--check-inputs validates inputs only. Explicit --run starts 384 native
calls (2 seconds each), 192 direct HiGHS references and 48 exhaustive oracles,
under the original 240-second wall guard. There are no retries or ledger edits.
Every run uses a new directory inside outputs/prototype_revision_20261024/.
"""

import argparse
import hashlib
import importlib
import itertools
import json
import math
import os
import platform
import subprocess
import sys
import tempfile
import traceback
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = ROOT / "outputs" / "prototype_revision_20261024"
SEED = 20261024
EXPECTED_MODELS_SHA256 = "4df0fbec29dc7afd7df66872d395bd5c52e7f31155c6c28e642050483383ddad"
AUDIT_COMMIT = "4ca4bab47f2eecb8b60d5e34e767b4dc239fd969"
AUDIT_DRIVER_SHA256 = "e90479eb7ee71b7494270f4719c569fbab0f96aa4e0988533892a9728ac59bc3"
CONFIGURATIONS = ("default", "reference_controls")
PER_CALL_SECONDS = 2
WALL_GUARD_SECONDS = 240


def _numpy():
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    return importlib.import_module("numpy")


def generate_models():
    """Preserve the original audit's isolated RNG and exact draw/order semantics."""
    np = _numpy()
    rng = np.random.default_rng(SEED)
    cases = []
    for kind in ("LP", "MILP"):
        for i in range(96):
            n = 4
            lo = rng.integers(-3, 1, n).astype(float)
            hi = lo + rng.integers(2, 6, n)
            anchor = np.array(
                [
                    rng.integers(int(lower), int(upper) + 1)
                    for lower, upper in zip(lo, hi, strict=True)
                ]
            )
            a = rng.integers(-4, 5, (6, n)).astype(float)
            value = a @ anchor
            rl = value - rng.integers(0, 5, 6)
            ru = value + rng.integers(0, 5, 6)
            rl[0] = -np.inf
            ru[1] = np.inf
            if i % 4 == 0:
                rl[2] = ru[2] = value[2]
            if i % 16 == 0:
                a[-1] = [1, 0, 0, 0]
                rl[-1], ru[-1] = hi[0] + 1, np.inf
            integer = np.zeros(n, dtype=int)
            if kind == "MILP":
                integer[: 4 if i < 48 else 2] = 1
            c = rng.integers(-5, 6, n).astype(float)
            constant = int(rng.integers(-10, 11))
            sign = 1 if i % 2 == 0 else -1
            cases.append(
                {
                    "name": f"audit_{kind}_{i:03}",
                    "sense": "minimize" if sign == 1 else "maximize",
                    "variables": [
                        {
                            "name": f"x{j}",
                            "lower": float(lo[j]),
                            "upper": float(hi[j]),
                            "type": "integer" if integer[j] else "continuous",
                        }
                        for j in range(n)
                    ],
                    "constraints": [
                        {
                            "name": f"r{k}",
                            "coefficients": {f"x{j}": float(a[k, j]) for j in range(n)},
                            "lower": float(rl[k]) if np.isfinite(rl[k]) else None,
                            "upper": float(ru[k]) if np.isfinite(ru[k]) else None,
                        }
                        for k in range(6)
                    ],
                    "objective": {
                        "constant": constant,
                        "coefficients": {f"x{j}": float(c[j]) for j in range(n)},
                    },
                }
            )
    return cases


def model_bytes(cases):
    """Portable reconstruction of the exact Windows audit file, not a new hash."""
    data = json.dumps(cases, indent=2, allow_nan=False).replace("\n", "\r\n").encode("utf-8")
    digest = hashlib.sha256(data).hexdigest()
    if digest != EXPECTED_MODELS_SHA256:
        raise AssertionError(f"Frozen audit input reconstruction mismatch: {digest}")
    if len(cases) != 192:
        raise AssertionError("Frozen audit must contain 192 models.")
    return data


def _arrays(payload, np):
    names = [v["name"] for v in payload["variables"]]
    return {
        "names": names,
        "lo": np.array([v["lower"] for v in payload["variables"]]),
        "hi": np.array([v["upper"] for v in payload["variables"]]),
        "integer": np.array([v["type"] != "continuous" for v in payload["variables"]], dtype=int),
        "a": np.array(
            [[row["coefficients"].get(name, 0) for name in names] for row in payload["constraints"]]
        ),
        "rl": np.array(
            [-np.inf if row["lower"] is None else row["lower"] for row in payload["constraints"]]
        ),
        "ru": np.array(
            [np.inf if row["upper"] is None else row["upper"] for row in payload["constraints"]]
        ),
        "c": np.array([payload["objective"]["coefficients"].get(name, 0) for name in names]),
        "constant": payload["objective"]["constant"],
        "sign": 1 if payload["sense"] == "minimize" else -1,
    }


def _reference(data, integer, optimize):
    """The original direct-HiGHS oracle, independent of SILO interfaces/helpers."""
    started = perf_counter()
    a, rl, ru = data["a"], data["rl"], data["ru"]
    if not integer:
        rows, rhs = [], []
        for k in range(6):
            if math.isfinite(ru[k]):
                rows.append(a[k])
                rhs.append(ru[k])
            if math.isfinite(rl[k]):
                rows.append(-a[k])
                rhs.append(-rl[k])
        result = optimize.linprog(
            data["sign"] * data["c"],
            A_ub=rows,
            b_ub=rhs,
            bounds=list(zip(data["lo"], data["hi"], strict=True)),
            method="highs",
        )
    else:
        result = optimize.milp(
            data["sign"] * data["c"],
            integrality=data["integer"],
            bounds=optimize.Bounds(data["lo"], data["hi"]),
            constraints=optimize.LinearConstraint(a, rl, ru),
            options={"time_limit": 2},
        )
    status = {0: "optimal", 2: "infeasible", 3: "unbounded"}.get(result.status, "other")
    objective = data["constant"] + data["sign"] * float(result.fun) if result.status == 0 else None
    return {
        "status": status,
        "objective": objective,
        "scipy_status": int(result.status),
        "message": str(result.message),
        "elapsed_seconds": perf_counter() - started,
        "point": None if result.x is None else list(map(float, result.x)),
    }


def _enumerate(data, np):
    """Original 4-integer oracle; these small integer-valued floats are exact."""
    started = perf_counter()
    feasible = []
    assignments = 0
    domains = (
        range(int(lower), int(upper) + 1)
        for lower, upper in zip(data["lo"], data["hi"], strict=True)
    )
    for point in itertools.product(*domains):
        assignments += 1
        x = np.array(point)
        activity = data["a"] @ x
        if np.all(activity >= data["rl"]) and np.all(activity <= data["ru"]):
            feasible.append(float(data["c"] @ x + data["constant"]))
    best = (min(feasible) if data["sign"] == 1 else max(feasible)) if feasible else None
    return {
        "status": "infeasible" if best is None else "optimal",
        "objective": best,
        "assignments": assignments,
        "feasible_assignments": len(feasible),
        "elapsed_seconds": perf_counter() - started,
    }


def _close(actual, expected, tolerance=1e-6):
    return (
        actual is not None
        and math.isfinite(float(actual))
        and abs(actual - expected) <= tolerance * (1 + abs(expected))
    )


def _check_native(data, reference, result, np):
    """Raw original-array checks; preserve the historical tolerances, add gap algebra."""
    problems = []
    if result.status != reference["status"]:
        problems.append("status_mismatch")
    objective = result.objective_value
    if objective is not None:
        if set(result.primal_values) != set(data["names"]):
            problems.append("raw_primal_missing_variable")
        elif not all(math.isfinite(value) for value in result.primal_values.values()):
            problems.append("raw_primal_nonfinite")
        else:
            x = np.array([result.primal_values[name] for name in data["names"]])
            activity = data["a"] @ x
            violation = max(
                np.max(data["lo"] - x),
                np.max(x - data["hi"]),
                np.max(data["rl"] - activity),
                np.max(activity - data["ru"]),
            )
            if violation > 1e-6:
                problems.append("raw_primal_violation")
            integer = x[data["integer"] != 0]
            if np.any(abs(integer - np.rint(integer)) > 1e-7):
                problems.append("raw_integer_violation")
            if (
                not math.isfinite(objective)
                or abs(data["c"] @ x + data["constant"] - objective) > 1e-6
            ):
                problems.append("raw_objective_mismatch")
        if not _close(result.primal_bound, objective):
            problems.append("wrong_primal_bound")
    elif result.primal_bound is not None:
        problems.append("primal_bound_without_solution")
    if result.has_primal_solution != (objective is not None):
        problems.append("primal_flag_mismatch")
    if result.status == "optimal" and reference["objective"] is not None:
        if not _close(objective, reference["objective"]):
            problems.append("wrong_optimum")
        if not _close(result.dual_bound, reference["objective"]):
            problems.append("wrong_bound")
    dual = result.dual_bound
    finite_dual = dual is not None and math.isfinite(dual)
    if finite_dual and reference["objective"] is not None:
        if data["sign"] * (dual - reference["objective"]) > 1e-6 * (
            1 + abs(reference["objective"])
        ):
            problems.append("dual_bound_excludes_true_optimum")
    if objective is not None and finite_dual:
        if data["sign"] * (dual - objective) > 1e-6 * (1 + abs(objective)):
            problems.append("primal_dual_bound_order")
        gap = abs(objective - dual)
        relative = gap / max(1, abs(objective), abs(dual))
        for value in (result.absolute_gap, result.relative_gap):
            if value is not None and (not math.isfinite(value) or value < 0):
                problems.append("invalid_gap_value")
        if not _close(result.absolute_gap, gap, 1e-7):
            problems.append("absolute_gap_inconsistent")
        if not _close(result.relative_gap, relative, 1e-7):
            problems.append("relative_gap_inconsistent")
        if result.status == "optimal" and gap > 1e-6 * (1 + abs(objective)):
            problems.append("optimal_gap_not_closed")
    elif result.absolute_gap is not None or result.relative_gap is not None:
        problems.append("gap_without_incumbent_and_finite_bound")
    return problems


def _write_json(path, value):
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8"
    )


def _append(stream, value):
    stream.write(json.dumps(value, sort_keys=True, allow_nan=False) + "\n")
    stream.flush()


def _guard(started):
    if perf_counter() - started > WALL_GUARD_SECONDS:
        raise RuntimeError("Audit wall guard exceeded")


def _source_tree_hash():
    digest = hashlib.sha256()
    for path in sorted((ROOT / "src").rglob("*.py")):
        digest.update(path.relative_to(ROOT).as_posix().encode() + b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _source_identity():
    return {
        "source_commit": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        "source_dirty_paths": subprocess.check_output(
            ["git", "status", "--short"], cwd=ROOT, text=True
        ).splitlines(),
        "driver_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "native_src_tree_sha256": _source_tree_hash(),
    }


def _run(cases, output, summary, started):
    np = _numpy()
    scipy = importlib.import_module("scipy")
    optimize = importlib.import_module("scipy.optimize")
    # The native implementation is the object under audit. Oracles/checkers above
    # use only raw input arrays; they never call production transforms or checkers.
    sys.path.insert(0, str(ROOT / "src"))
    silo = importlib.import_module("silo")
    io = importlib.import_module("silo.io")
    if not Path(silo.__file__).resolve().is_relative_to(ROOT / "src"):
        raise RuntimeError("Native audit must import the declared source checkout.")
    summary.update({"scipy": scipy.__version__, "native_module": silo.__file__})
    native_records = []
    with (
        (output / "probe_records.jsonl").open("x", encoding="utf-8") as records,
        (output / "probe_references.jsonl").open("x", encoding="utf-8") as references,
    ):
        for index, payload in enumerate(cases):
            _guard(started)
            data = _arrays(payload, np)
            summary["reference_calls"] += 1
            reference = _reference(data, index >= 96, optimize)
            enumeration = None
            if 96 <= index < 144:
                enumeration = _enumerate(data, np)
                summary["exact_integer_oracles"] += 1
            oracle_record = {
                "id": payload["name"],
                "reference": reference,
                "enumeration": enumeration,
            }
            _append(references, oracle_record)
            if reference["status"] not in ("optimal", "infeasible"):
                raise AssertionError(f"Direct HiGHS reference did not determine {payload['name']}")
            if enumeration is not None:
                if enumeration["status"] != reference["status"] or (
                    enumeration["objective"] is not None
                    and abs(enumeration["objective"] - reference["objective"]) >= 1e-7
                ):
                    raise AssertionError(f"Independent enumeration mismatch: {payload['name']}")
            for config in CONFIGURATIONS:
                _guard(started)
                options = (
                    silo.SolveOptions(time_limit=2)
                    if config == "default"
                    else silo.SolveOptions(
                        time_limit=2,
                        presolve=False,
                        scaling=False,
                        cuts=False,
                        heuristics=False,
                        node_strategy="dfs",
                    )
                )
                tick = perf_counter()
                record = {
                    "id": payload["name"],
                    "config": config,
                    "options": asdict(options),
                    "reference_status": reference["status"],
                    "reference_objective": reference["objective"],
                    "enumeration": None if enumeration is None else enumeration["objective"],
                }
                try:
                    model = io.model_from_dict(payload)
                    summary["native_calls"] += 1
                    result = silo.solve(model, options)
                    record.update(
                        {
                            "status": result.status,
                            "termination": result.termination_reason,
                            "objective": result.objective_value,
                            "problems": _check_native(data, reference, result, np),
                            "result": result.to_dict(),
                        }
                    )
                except Exception as exc:
                    record.update(
                        {
                            "problems": ["exception"],
                            "error": repr(exc),
                            "traceback": traceback.format_exc(),
                        }
                    )
                record["elapsed_seconds"] = perf_counter() - tick
                _append(records, record)
                native_records.append(record)
                summary["completed_configurations"] += 1
                if record["problems"]:
                    summary["failures"].append(
                        {"id": record["id"], "config": config, "problems": record["problems"]}
                    )
                summary["elapsed_seconds"] = perf_counter() - started
                _write_json(output / "probe_summary.json", summary)
    # Compatibility aggregate alongside the always-flushed per-call records.
    _write_json(output / "probe_records.json", native_records)
    if (summary["native_calls"], summary["reference_calls"], summary["exact_integer_oracles"]) != (
        384,
        192,
        48,
    ):
        raise AssertionError("The fixed matrix did not execute completely.")
    summary["status"] = "failed" if summary["failures"] else "passed"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--check-inputs", action="store_true", help="Check frozen inputs; call no solvers"
    )
    mode.add_argument(
        "--run", action="store_true", help="Explicitly run the fixed 384-native-call matrix"
    )
    parser.add_argument(
        "--output-dir", type=Path, help="A new directory below the revision output root"
    )
    args = parser.parse_args(argv)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)
    if args.output_dir is None:
        output = Path(tempfile.mkdtemp(prefix="independent-probe-", dir=OUTPUT_ROOT))
    else:
        output = args.output_dir.resolve()
        if output == OUTPUT_ROOT.resolve() or not output.is_relative_to(OUTPUT_ROOT.resolve()):
            parser.error(
                "All outputs must be in a new child of outputs/prototype_revision_20261024"
            )
        output.mkdir(parents=True, exist_ok=False)
    started = perf_counter()
    summary = {
        "status": "running",
        "mode": "matrix" if args.run else "inputs_only",
        "seed": SEED,
        "source_audit_commit": AUDIT_COMMIT,
        "source_audit_driver_sha256": AUDIT_DRIVER_SHA256,
        "expected_models_sha256": EXPECTED_MODELS_SHA256,
        "models": 0,
        "native_calls": 0,
        "reference_calls": 0,
        "exact_integer_oracles": 0,
        "expected_matrix_calls": {"native": 384, "direct_highs": 192, "pure_ip_enumeration": 48},
        "completed_configurations": 0,
        "failures": [],
        "output_directory": str(output),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "per_native_call_seconds": PER_CALL_SECONDS,
        "wall_guard_seconds": WALL_GUARD_SECONDS,
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "serialization": "json.dumps(indent=2), UTF-8, CRLF, no trailing newline",
        "external_algorithm_evidence": "direct scipy_highs (one algorithm evidence)",
        "ledger_written": False,
    }
    try:
        summary.update(_source_identity())
        cases = generate_models()
        frozen = model_bytes(cases)
        (output / "probe_models.json").write_bytes(frozen)
        summary.update(
            {
                "models": len(cases),
                "models_sha256": hashlib.sha256(frozen).hexdigest(),
                "numpy": _numpy().__version__,
            }
        )
        if args.run:
            _run(cases, output, summary, started)
        else:
            summary["status"] = "inputs_verified"
    except Exception as exc:
        summary["status"] = "failed"
        summary["fatal_error"] = repr(exc)
        summary["traceback"] = traceback.format_exc()
    finally:
        summary["elapsed_seconds"] = perf_counter() - started
        summary["finished_utc"] = datetime.now(timezone.utc).isoformat()
        summary["silo_imported"] = "silo" in sys.modules
        summary["scipy_imported"] = "scipy" in sys.modules
        summary["native_src_tree_sha256_after"] = _source_tree_hash()
        summary["source_changed_during_run"] = (
            summary.get("native_src_tree_sha256") != (summary["native_src_tree_sha256_after"])
        )
        if args.run and summary["source_changed_during_run"]:
            summary["status"] = "failed"
            summary["fatal_error"] = "Native source files changed during the matrix"
        _write_json(output / "probe_summary.json", summary)
    print(json.dumps(summary, sort_keys=True, allow_nan=False))
    return 0 if summary["status"] in ("passed", "inputs_verified") else 1


if __name__ == "__main__":
    raise SystemExit(main())
