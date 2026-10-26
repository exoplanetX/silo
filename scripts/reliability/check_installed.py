"""Standalone current-candidate installed smoke: exactly 24 public requests.

Run a copied file outside the checkout using the fresh environment's python -I.
No old candidate checker, fixture, profile hook or source import is used.
"""

import argparse
import importlib.metadata
import importlib.util
import json
import math
import platform
import subprocess
import sys
import sysconfig
import tempfile
from fractions import Fraction
from hashlib import sha256
from pathlib import Path


def digest(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--artifact", type=Path, required=True)
    parser.add_argument("--engine", choices=("dense", "sparse"), required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    assert sys.flags.isolated and sys.flags.ignore_environment
    source = args.source_root.resolve()
    assert not Path.cwd().resolve().is_relative_to(source)
    import silo
    from silo import SolveOptions, solve
    from silo.core.bounds import Bounds
    from silo.core.constraint import Constraint
    from silo.core.variable import Variable
    from silo.decomposition.general_master import covering_example
    from silo.io import (
        model_from_dict,
        model_to_dict,
        model_to_lp,
        model_to_mps,
        parse_lp,
        parse_mps,
    )
    from silo.lp.session import LPSession

    assert silo.__version__ == importlib.metadata.version("silo-solver") == "0.3.0a2"
    assert importlib.metadata.version("numpy") == "2.3.5"
    if args.engine == "sparse":
        assert importlib.metadata.version("scipy") == "1.16.3"
    else:
        assert importlib.util.find_spec("scipy") is None
    distribution = importlib.metadata.distribution("silo-solver")
    direct = json.loads(distribution.read_text("direct_url.json"))
    artifact_sha = digest(args.artifact)
    assert direct["archive_info"]["hashes"]["sha256"] == artifact_sha
    assert "dir_info" not in direct
    roots = {Path(sysconfig.get_path(n)).resolve() for n in ("purelib", "platlib")}
    options = SolveOptions(lp_engine=args.engine, time_limit=10, cuts=False, heuristics=False)
    payload = {"name": "installed_smoke", "variables": [
        {"name": "x", "lower": 0, "upper": 2}, {"name": "y", "lower": 0, "upper": 1.5}],
        "objective": {"coefficients": {"x": -1, "y": -2}, "constant": 3},
        "constraints": [{"name": "r", "coefficients": {"x": 1, "y": 1},
                         "sense": "<=", "rhs": 2}]}
    requests = []

    def accepted(name, result, expected):
        data = result.to_dict() if hasattr(result, "to_dict") else result
        assert data["status"] == "optimal", data
        value = data["objective_value"]
        assert value is not None and math.isfinite(value)
        assert abs(value - expected) <= 1e-7 * (1 + abs(value) + abs(expected))
        requests.append({"name": name, "status": data["status"], "objective": value,
                         "diagnostics": data.get("diagnostics", {})})

    accepted("LP", solve(model_from_dict(payload), options), -0.5)
    mip = {"sense": "maximize", "variables": [
        {"name": "a", "lower": 0, "upper": 3, "type": "integer"},
        {"name": "b", "lower": 0, "upper": 3, "type": "integer"}],
        "objective": {"coefficients": {"a": 1, "b": 1}, "constant": 0.25},
        "constraints": [{"name": "cap", "coefficients": {"a": 2, "b": 2},
                         "sense": "<=", "rhs": 5}]}
    accepted("MILP", solve(model_from_dict(mip), options), 2.25)
    work = Path(tempfile.mkdtemp(prefix="silo-smoke-", dir=Path.cwd()))
    model = model_from_dict(payload)
    texts = {"json": json.dumps(model_to_dict(model)), "mps": model_to_mps(model),
             "lp": model_to_lp(model)}
    for fmt in ("json", "mps", "lp"):
        reader = {"json": lambda t: model_from_dict(json.loads(t)),
                  "mps": parse_mps, "lp": parse_lp}
        accepted("roundtrip_" + fmt, solve(reader[fmt](texts[fmt]), options), -0.5)
        (work / ("input." + fmt)).write_text(texts[fmt], encoding="utf-8")
    for source_fmt, target_fmt in (("json", "mps"), ("mps", "lp"), ("lp", "json")):
        output = work / ("converted_from_" + source_fmt + "." + target_fmt)
        run = subprocess.run([sys.executable, "-I", "-m", "silo.cli.main", "convert",
                              str(work / ("input." + source_fmt)), "--output", str(output)],
                             capture_output=True, text=True, timeout=10, check=False)
        assert run.returncode == 0, run.stderr
        assert output.is_file()
        requests.append({"name": "convert_" + source_fmt + "_" + target_fmt, "exit_code": 0,
                         "output_sha": digest(output), "solver_calls": 0})
    for fmt in ("json", "mps", "lp"):
        run = subprocess.run([sys.executable, "-I", "-m", "silo.cli.main", "optimize",
                              str(work / ("input." + fmt)), "--lp-engine", args.engine],
                             capture_output=True, text=True, timeout=10, check=False)
        assert run.returncode == 0, run.stderr
        data = json.loads(run.stdout)
        assert data["schema_version"] == 2
        accepted("CLI_optimize_" + fmt, data, -0.5)
    for kind, expected in (("rhs", 1), ("bounds", -0.25), ("row", 1), ("column", -2)):
        session = LPSession(model_from_dict(payload), options)
        accepted(kind + "_initial", session.solve(), -0.5)
        if kind == "rhs":
            session.change_rhs("r", 1)
        elif kind == "bounds":
            session.change_bounds("x", 0, 0.25)
        elif kind == "row":
            session.append_row(Constraint("new", {"x": 1, "y": 1}, rhs=1))
        else:
            session.append_column(Variable("z", Bounds(0, 1)), {"r": 1}, -3)
        accepted(kind + "_warm", session.solve(), expected)
        accepted(kind + "_cold", solve(session.model, options), expected)
    cg = covering_example(options)
    assert cg.status == "optimal" and abs(cg.objective_value - 2.5) <= 1e-7
    witness = cg.witness
    assert witness["kind"] == "finite_pool_optimality"
    assert (Fraction(witness["primal_objective"]) ==
            Fraction(witness["dual_objective"]) == Fraction(5, 2))
    assert all(Fraction(v) >= 0 for v in witness["reduced_costs"].values())
    requests.append({"name": "finite_pool_CG", "status": cg.status,
                     "objective": cg.objective_value,
                     "witness": witness})
    assert len(requests) == 24
    loaded = {}
    for name, module in sorted(sys.modules.items()):
        if (name == "silo" or name.startswith("silo.")) and getattr(module, "__file__", None):
            path = Path(module.__file__).resolve()
            assert not path.is_relative_to(source)
            assert any(path.is_relative_to(root) for root in roots), (name, path)
            loaded[name] = {"path": str(path), "sha256": digest(path)}
    assert not any(n.split(".")[0] in ("highspy", "gurobipy", "pulp", "ortools")
                   for n in sys.modules)
    report = {"passed": True, "version": silo.__version__, "python": platform.python_version(),
              "platform": platform.platform(), "machine": platform.machine(),
              "engine": args.engine, "isolated": True, "cwd": str(Path.cwd()),
              "artifact": str(args.artifact), "artifact_sha256": artifact_sha,
              "direct_url": direct, "requests": requests, "public_requests": 24,
              "loaded_modules": loaded, "source_imports": 0,
              "numpy": importlib.metadata.version("numpy"),
              "scipy": importlib.metadata.version("scipy") if args.engine == "sparse" else None}
    with args.report.open("x", encoding="utf-8") as stream:
        json.dump(report, stream, indent=2, allow_nan=False)
    print(json.dumps({k: v for k, v in report.items() if k not in ("requests", "loaded_modules")}))


if __name__ == "__main__":
    main()
