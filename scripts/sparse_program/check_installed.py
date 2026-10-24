"""Standalone standard-library driver for one fresh, source-external installation.

Copy this file outside the checkout and invoke the new environment's Python -I.
Optional numerical imports occur only inside the selected sparse checks. This
file builds/installs nothing and never adds a source directory to sys.path.
"""

import argparse
import copy
import importlib
import importlib.metadata
import importlib.util
import json
import math
import platform
import subprocess
import sys
import sysconfig
import tempfile
from fractions import Fraction as F
from hashlib import sha256
from pathlib import Path
from time import perf_counter

VERSION, NUMPY, SCIPY = "0.3.0a1", "2.3.5", "1.16.3"
COUNTS = {
    f"{kind}_{phase}": 0
    for kind in ("native_calls", "lp_calls", "kernel_calls", "cg_calls", "session_calls")
    for phase in ("started", "completed")
}
OPTIMIZER_ATTEMPTS = 0


def _within(path, root):
    return Path(path).resolve().is_relative_to(Path(root).resolve())


def _profile(frame, event, arg):
    if event not in ("call", "return"):
        return
    path, name = frame.f_code.co_filename.replace("\\", "/"), frame.f_code.co_name
    kind = None
    for suffix, function, label in (
        ("/silo/solver.py", "solve", "native_calls"),
        ("/silo/lp/general.py", "solve_lp_data", "lp_calls"),
        ("/silo/lp/kernel.py", "solve_canonical", "kernel_calls"),
        ("/silo/lp/sparse_kernel.py", "solve_canonical", "kernel_calls"),
        ("/silo/decomposition/general_master.py", "column_generation", "cg_calls"),
        ("/silo/lp/session.py", "solve", "session_calls"),
    ):
        if path.endswith(suffix) and name == function:
            kind = label
            break
    if kind:
        COUNTS[kind + ("_started" if event == "call" else "_completed")] += 1


def _provenance(args):
    if not sys.flags.isolated or not sys.flags.ignore_environment:
        raise RuntimeError("Installed interpreter requires -I")
    if _within(Path.cwd(), args.source_root) or _within(__file__, args.source_root):
        raise RuntimeError("Checker and cwd must both be outside the source checkout")
    if platform.system() != "Windows" or platform.python_version_tuple()[:2] != tuple(
        args.python_minor.split(".")
    ):
        raise RuntimeError("Actual interpreter/platform differs from requested Windows combination")
    roots = {Path(sysconfig.get_path(name)).resolve() for name in ("purelib", "platlib")}
    silo = importlib.import_module("silo")
    if "scipy" in sys.modules:
        raise RuntimeError("Importing SILO loaded SciPy before engine selection")
    path = Path(silo.__file__).resolve()
    if _within(path, args.source_root) or not any(_within(path, root) for root in roots):
        raise RuntimeError("SILO import escaped the new installed site-packages")
    distribution = importlib.metadata.distribution("silo-solver")
    if distribution.version != VERSION or silo.__version__ != VERSION:
        raise RuntimeError("Installed metadata/runtime is not candidate0.3.0a1")
    np = importlib.import_module("numpy")
    if np.__version__ != NUMPY or importlib.metadata.version("numpy") != NUMPY:
        raise RuntimeError("NumPy differs from the locked version2.3.5")
    available = importlib.util.find_spec("scipy") is not None
    if available != (args.mode == "sparse"):
        raise RuntimeError(
            "Environment optional SciPy presence differs from selected configuration"
        )
    if available and importlib.metadata.version("scipy") != SCIPY:
        raise RuntimeError("Sparse installation requires SciPy1.16.3")
    direct_raw = distribution.read_text("direct_url.json")
    direct = json.loads(direct_raw) if direct_raw else {}
    archive = direct.get("archive_info", {})
    installed_sha = archive.get("hashes", {}).get("sha256")
    if installed_sha is None and archive.get("hash", "").startswith("sha256="):
        installed_sha = archive["hash"].split("=", 1)[1]
    artifact_sha = sha256(args.artifact.read_bytes()).hexdigest()
    if installed_sha != artifact_sha:
        raise RuntimeError("Installed direct_url archive SHA differs from the issued artifact")
    return silo, {
        "module_file": str(path),
        "site_packages": sorted(map(str, roots)),
        "version": distribution.version,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "executable": sys.executable,
        "isolated": True,
        "numpy": np.__version__,
        "numpy_file": np.__file__,
        "scipy_installed": available,
        "scipy_version": importlib.metadata.version("scipy") if available else None,
        "silo_import_loaded_scipy": False,
        "installation_source": direct,
        "artifact_sha256": artifact_sha,
        "direct_url_artifact_sha_matched": True,
    }


def _configure(mode):
    if mode == "dense":
        return None
    optimize = importlib.import_module("scipy.optimize")

    def forbidden(*args, **kwargs):
        global OPTIMIZER_ATTEMPTS
        OPTIMIZER_ATTEMPTS += 1
        raise AssertionError("Native SILO attempted an external optimizer call")

    optimize.linprog = optimize.milp = forbidden
    sparse = importlib.import_module("scipy.sparse")
    linalg = importlib.import_module("scipy.sparse.linalg")
    np = importlib.import_module("numpy")
    matrix = sparse.csc_matrix([[2.0, 1], [0, 3]])
    factor = linalg.splu(matrix)
    rhs = np.array([1.0, 2])
    x, y = factor.solve(rhs), factor.solve(rhs, trans="T")
    if max(abs(matrix @ x - rhs)) > 1e-12 or max(abs(matrix.T @ y - rhs)) > 1e-12:
        raise AssertionError("Locked sparse forward/transpose linear solves failed")
    return {
        "forward_and_transpose_checked": True,
        "scipy": SCIPY,
        "optimizer_functions_blocked": ["scipy.optimize.linprog", "scipy.optimize.milp"],
    }


def _module_provenance(source_root, provenance):
    roots = list(map(Path, provenance["site_packages"]))
    imported = {}
    for name, module in tuple(sys.modules.items()):
        if name == "silo" or name.startswith("silo."):
            path = getattr(module, "__file__", None)
            if path:
                if _within(path, source_root) or not any(_within(path, root) for root in roots):
                    raise RuntimeError(f"Imported SILO module outside new site-packages: {name}")
                imported[name] = str(Path(path).resolve())
    if not imported:
        raise RuntimeError("No installed SILO modules verified")
    return imported


def _options(silo, mode, **kwargs):
    return silo.SolveOptions(lp_engine=mode, **kwargs)


def _lp():
    return {
        "name": "installed_lp",
        "sense": "minimize",
        "variables": [
            {"name": "x", "lower": -2, "upper": 4},
            {"name": "y", "lower": None, "upper": None},
            {"name": "z", "lower": 3, "upper": 3},
            {"name": "u", "lower": None, "upper": 2},
        ],
        "constraints": [
            {"name": "range", "coefficients": {"x": 1, "y": 1}, "lower": 1, "upper": 3}
        ],
        "objective": {"constant": 7, "coefficients": {"x": 1, "y": 2, "z": 5, "u": -1}},
    }


def _mip():
    return {
        "name": "installed_mip",
        "sense": "minimize",
        "variables": [
            {"name": "i", "lower": -2, "upper": 1, "type": "integer"},
            {"name": "b", "lower": 0, "upper": 1, "type": "binary"},
            {"name": "f", "lower": 0, "upper": 4},
        ],
        "constraints": [
            {"name": "demand", "coefficients": {"i": 1, "b": 1, "f": 1}, "sense": ">=", "rhs": 1.5},
            {"name": "link", "coefficients": {"f": 1, "b": -2}, "rhs": 1},
        ],
        "objective": {"constant": -2, "coefficients": {"i": 2, "b": 3, "f": 0.5}},
    }


def _bounds(row):
    if "lower" in row or "upper" in row:
        return row.get("lower"), row.get("upper")
    sense, rhs = row.get("sense", "<="), row.get("rhs", 0)
    return (rhs if sense in (">=", "=") else None, rhs if sense in ("<=", "=") else None)


def _optimal(data, expected):
    if data["status"] != "optimal" or not math.isfinite(data["objective_value"]):
        raise AssertionError(f"Installed required optimum failed: {data}")
    assert abs(data["objective_value"] - expected) <= 1e-7 * (1 + abs(expected))


def _point(payload, data):
    point = data["primal_values"]
    assert set(point) == {v["name"] for v in payload["variables"]}
    assert all(math.isfinite(v) for v in point.values())
    for variable in payload["variables"]:
        value = point[variable["name"]]
        for bound, side in ((variable.get("lower", 0), -1), (variable.get("upper"), 1)):
            if bound is not None:
                assert side * (value - bound) <= 1e-7 * (1 + abs(value) + abs(bound))
        if variable.get("type", "continuous") != "continuous":
            assert abs(value - round(value)) <= 1e-7
    for row in payload["constraints"]:
        terms = [a * point[name] for name, a in row["coefficients"].items()]
        value = math.fsum(terms)
        for bound, side in zip(_bounds(row), (-1, 1), strict=True):
            if bound is not None:
                assert side * (value - bound) <= 1e-7 * (
                    1 + abs(bound) + math.fsum(map(abs, terms))
                )
    objective = payload["objective"].get("constant", 0) + math.fsum(
        a * point[name] for name, a in payload["objective"]["coefficients"].items()
    )
    assert abs(data["objective_value"] - objective) <= 1e-7 * (1 + abs(objective))
    for label in ("primal_bound", "dual_bound"):
        assert data[label] is not None and abs(data[label] - objective) <= 1e-7 * (
            1 + abs(objective)
        )
    assert data["absolute_gap"] == data["relative_gap"] == 0


def _api(silo, mode):
    io = importlib.import_module("silo.io")
    maximum = copy.deepcopy(_lp())
    maximum["sense"] = "maximize"
    maximum["objective"]["constant"] = -7
    maximum["objective"]["coefficients"] = {
        n: -v for n, v in maximum["objective"]["coefficients"].items()
    }
    cases = [("lp_min", _lp(), 18.0), ("mip_min", _mip(), -1.75), ("lp_max", maximum, -18.0)]
    records = []
    for label, payload, objective in cases:
        result = silo.solve(io.model_from_dict(payload), _options(silo, mode, time_limit=20))
        data = result.to_dict()
        _optimal(data, objective)
        _point(payload, data)
        assert data["diagnostics"]["lp_engine"] == mode
        records.append({"id": label, "result": data})
    if mode == "dense":
        missing = silo.solve(io.model_from_dict(_lp()), _options(silo, "sparse"))
        assert (
            missing.status == "unsupported"
            and missing.termination_reason == "sparse_dependency_missing"
        )
        assert "scipy" not in sys.modules
        records.append({"id": "explicit_sparse_missing", "result": missing.to_dict()})
    return cases, records


def _pool_pair(model, pool, result):
    proof = result.witness
    assert proof["kind"] == "finite_pool_optimality"
    point, duals = [
        dict((n, F(v)) for n, v in proof[key].items()) for key in ("point", "row_duals")
    ]
    assert set(point) == {column.name for column in pool} and all(v >= 0 for v in point.values())
    primal = F(model.objective.constant) + sum((F(c.cost) * point[c.name] for c in pool), F(0))
    dual = F(model.objective.constant)
    for row in model.constraints:
        value = sum((F(c.row_coefficients.get(row.name, 0)) * point[c.name] for c in pool), F(0))
        lower, upper = row.row_bounds
        assert (not math.isfinite(lower) or value >= F(lower)) and (
            not math.isfinite(upper) or value <= F(upper)
        )
        pi = duals[row.name]
        bound = lower if pi >= 0 else upper
        if pi:
            assert math.isfinite(bound)
            dual += pi * F(bound)
    for column in pool:
        reduced = F(column.cost) - sum(
            (F(a) * duals[n] for n, a in column.row_coefficients.items()), F(0)
        )
        assert reduced >= 0 and F(proof["reduced_costs"][column.name]) == reduced
    assert primal == dual == F(proof["primal_objective"]) == F(proof["dual_objective"])
    return str(primal)


def _research(silo, mode):
    cg = importlib.import_module("silo.decomposition.general_master")
    io = importlib.import_module("silo.io")
    records = []
    covering = cg.covering_example(_options(silo, mode))
    assert covering.status == "optimal" and abs(covering.objective_value - 2.5) < 1e-7
    assert (
        F(covering.witness["primal_objective"]) == F(covering.witness["dual_objective"]) == F(5, 2)
    )
    records.append({"id": "public_covering_example", "result": covering.to_dict()})
    research = importlib.import_module("silo.mip.research_example").run_example()
    assert research["status"] == "optimal" and abs(research["objective"] + 8.5) < 1e-7
    records.append({"id": "public_policy_example_fixed_dense", "result": research})
    payload = {
        "variables": [],
        "constraints": [{"name": "third", "coefficients": {}, "sense": "=", "rhs": 1}],
        "objective": {"coefficients": {}},
    }
    model = io.model_from_dict(payload)
    pool = [cg.MasterColumn("a", 1, {"third": 3})]
    third = cg.column_generation(
        cg.GeneralRestrictedMaster(model, _options(silo, mode)), cg.FiniteColumnPricer(pool)
    )
    assert third.status == "optimal" and _pool_pair(model, pool, third) == "1/3"
    records.append({"id": "original_full_pool_third", "result": third.to_dict()})
    return records


def _sessions(silo, mode):
    io = importlib.import_module("silo.io")
    Session = importlib.import_module("silo.lp.session").LPSession
    Constraint = importlib.import_module("silo.core.constraint").Constraint
    Variable = importlib.import_module("silo.core.variable").Variable
    Bounds = importlib.import_module("silo.core.bounds").Bounds
    payload = {
        "variables": [{"name": "x", "upper": 2}, {"name": "y", "upper": 1.5}],
        "constraints": [{"name": "r", "coefficients": {"x": 1, "y": 1}, "rhs": 2}],
        "objective": {"constant": 3, "coefficients": {"x": -1, "y": -2}},
    }
    options = _options(silo, mode, presolve=False, scaling=False)
    records = []
    for kind, expected in (("rhs", 1), ("bounds", -0.25), ("row", 1), ("column", -2)):
        session = Session(io.model_from_dict(payload), options)
        initial = session.solve()
        _optimal(initial.to_dict(), -0.5)
        if kind == "rhs":
            session.change_rhs("r", 1)
        elif kind == "bounds":
            session.change_bounds("x", 0, 0.25)
        elif kind == "row":
            session.append_row(Constraint("new", {"x": 1, "y": 1}, rhs=1))
        else:
            session.append_column(Variable("z", Bounds(0, 1)), {"r": 1}, -3)
        warm, cold = session.solve(), silo.solve(session.model, options)
        for result in (warm, cold):
            _optimal(result.to_dict(), expected)
            _point(io.model_to_dict(session.model), result.to_dict())
        assert warm.diagnostics["warm_starts"] == 1
        records.append({"id": kind, "warm": warm.to_dict(), "cold": cold.to_dict()})
    return records


def _repairs(silo, mode):
    io = importlib.import_module("silo.io")
    cg = importlib.import_module("silo.decomposition.general_master")
    records = []
    options = _options(
        silo,
        mode,
        presolve=False,
        cuts=False,
        primal_tolerance=0.01,
        dual_tolerance=1e-12,
        objective_tolerance=1e-12,
    )
    for sense, sign in (("minimize", 1), ("maximize", -1)):
        payload = {
            "sense": sense,
            "variables": [{"name": n, "upper": 1, "type": "binary"} for n in ("x", "y")],
            "constraints": [{"name": "cover", "coefficients": {"x": 2, "y": 3}, "lower": 3}],
            "objective": {"coefficients": {"x": sign * 0.006, "y": sign * 0.01}},
        }
        result = silo.solve(io.model_from_dict(payload), options)
        assert result.status == "optimal" and result.primal_values == {"x": 0, "y": 1}
        assert abs(result.objective_value - sign * 0.01) < 1e-14
        records.append({"id": "F1_" + sense, "result": result.to_dict()})
    payload = {
        "variables": [],
        "constraints": [{"name": "cap", "coefficients": {}, "rhs": 1e12}],
        "objective": {"coefficients": {}},
    }
    model = io.model_from_dict(payload)
    pool = [cg.MasterColumn("x", -1e-8, {"cap": 1})]
    tiny = cg.column_generation(
        cg.GeneralRestrictedMaster(model, _options(silo, mode)), cg.FiniteColumnPricer(pool)
    )
    assert tiny.status == "optimal" and abs(tiny.objective_value + 10000) < 1e-8
    _pool_pair(model, pool, tiny)
    records.append({"id": "F2_bounded", "result": tiny.to_dict()})
    payload = {
        "variables": [{"name": "a"}, {"name": "b"}],
        "constraints": [
            {"name": "r1", "coefficients": {"a": 1, "b": 1}, "sense": "=", "rhs": 1},
            {"name": "r2", "coefficients": {"a": 1, "b": 2}, "sense": "=", "rhs": 2},
        ],
        "objective": {"coefficients": {"b": -1e7}},
    }
    pool = [
        cg.MasterColumn("a", 0, {"r1": 1, "r2": 1}),
        cg.MasterColumn("b", -1e7, {"r1": 1, "r2": 2}),
        cg.MasterColumn("c", -1, {"r1": -1, "r2": -1}),
    ]
    guarded = cg.column_generation(
        cg.GeneralRestrictedMaster(io.model_from_dict(payload), _options(silo, mode)),
        cg.FiniteColumnPricer(pool),
    )
    assert guarded.status in ("unbounded", "limit", "numerical_failure")
    assert guarded.dual_bound is None or guarded.dual_bound == -math.inf
    records.append({"id": "F2_unbounded", "result": guarded.to_dict()})
    text = (
        "NAME lattice\nROWS\n N obj\nCOLUMNS\n x obj 1\n"
        "BOUNDS\n LI bnd x 9007199254740993.0\n PL bnd x\nENDATA\n"
    )
    model = io.parse_mps(text)
    assert model.variables[0].bounds.lower == 9007199254740993
    result = silo.solve(model, _options(silo, mode))
    assert result.status == "numerical_failure" and result.termination_reason == "input_conversion"
    records.append({"id": "F3_integer", "result": result.to_dict()})
    for kind in ("L", "G", "E"):
        for sign in (-1, 1):
            rhs = "-1e-300" if kind == "G" or (kind == "E" and sign > 0) else "1e-300"
            width = ("-" if sign < 0 else "") + "0." + "9" * 100 + "e-300"
            text = (
                f"NAME tiny\nROWS\n N obj\n {kind} r\nCOLUMNS\n x obj 1 r 1\n"
                f"RHS\n rhs r {rhs}\nRANGES\n rng r {width}\nENDATA\n"
            )
            try:
                io.parse_mps(text)
            except ValueError as exc:
                assert "underflow" in str(exc).lower()
            else:
                raise AssertionError("F4 accepted a nonzero derived underflow")
    return {"records": records, "F4_derived_underflow_refusals": 6}


def _cli(args, cases):
    io = importlib.import_module("silo.io")
    records = []
    with tempfile.TemporaryDirectory(prefix="cli-", dir=Path.cwd()) as directory:
        for label, payload, expected in cases[:2]:
            for suffix in ("json", "mps"):
                path = Path(directory) / f"{label}.{suffix}"
                contents = (
                    json.dumps(payload)
                    if suffix == "json"
                    else io.model_to_mps(io.model_from_dict(payload))
                )
                path.write_text(contents, encoding="utf-8")
                request, report = (
                    path.with_suffix(".request.json"),
                    path.with_suffix(".report.json"),
                )
                product_argv = [
                    "optimize",
                    str(path),
                    "--lp-engine",
                    args.mode,
                    "--time-limit",
                    "20",
                    "--node-limit",
                    "1000",
                ]
                request.write_text(json.dumps(product_argv), encoding="utf-8")
                argv = [
                    sys.executable,
                    "-I",
                    str(Path(__file__).resolve()),
                    "--source-root",
                    str(args.source_root),
                    "--artifact",
                    str(args.artifact),
                    "--mode",
                    args.mode,
                    "--python-minor",
                    args.python_minor,
                    "--cli-request",
                    str(request),
                    "--report",
                    str(report),
                ]
                start = perf_counter()
                process = subprocess.run(
                    argv, text=True, capture_output=True, timeout=40, check=False
                )
                if process.returncode != 0:
                    raise AssertionError(
                        f"Installed CLI failed: {process.stdout}\n{process.stderr}"
                    )
                data = json.loads(process.stdout)
                assert data["schema_version"] == 2
                _optimal(data, expected)
                _point(payload, data)
                child = json.loads(report.read_text())
                assert child["status"] == "passed" and child["external_optimizer_attempts"] == 0
                records.append(
                    {
                        "id": f"{label}_{suffix}",
                        "argv": argv,
                        "product_argv": product_argv,
                        "returncode": process.returncode,
                        "stdout": process.stdout,
                        "stderr": process.stderr,
                        "elapsed_seconds": perf_counter() - start,
                        "child_report": child,
                    }
                )
    return records


def run(args):
    started = perf_counter()
    report = {"status": "failed", "mode": args.mode, "provenance": {}}
    sys.setprofile(_profile)
    try:
        silo, provenance = _provenance(args)
        report["provenance"] = provenance
        report["sparse_interface"] = _configure(args.mode)
        if args.cli_request:
            argv = json.loads(args.cli_request.read_text())
            code = importlib.import_module("silo.cli.main").main(argv)
            assert code == 0
            report["product_argv"] = argv
        else:
            cases, report["api"] = _api(silo, args.mode)
            report["research_examples"] = _research(silo, args.mode)
            report["session_edits"] = _sessions(silo, args.mode)
            report["repair_regressions"] = _repairs(silo, args.mode)
            report["cli"] = _cli(args, cases)
        report["imported_modules"] = _module_provenance(args.source_root, provenance)
        report["optional_scipy_imported"] = "scipy" in sys.modules
        assert args.mode != "dense" or "scipy" not in sys.modules
        assert OPTIMIZER_ATTEMPTS == 0
        report["status"] = "passed"
    except (
        AssertionError,
        RuntimeError,
        ImportError,
        OSError,
        ValueError,
        KeyError,
        subprocess.TimeoutExpired,
    ) as exc:
        report["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        sys.setprofile(None)
        report.update(
            elapsed_seconds=perf_counter() - started,
            counts=COUNTS,
            external_optimizer_attempts=OPTIMIZER_ATTEMPTS,
        )
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--mode", choices=("dense", "sparse"), required=True)
    parser.add_argument("--python-minor", choices=("3.11", "3.13"), required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--cli-request", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args(argv)
    report = run(args)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    output = json.dumps(report, allow_nan=False, indent=2)
    args.report.write_text(output, encoding="utf-8")
    if args.cli_request is None:
        print(output)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
