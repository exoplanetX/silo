"""Source-independent validation of an installed SILO wheel or sdist.

Copy this standard-library-only driver outside the source checkout, then run its
installed environment's interpreter with ``-I``. The checker neither builds nor
installs packages; each wheel/sdist and Python version requires a fresh caller-
created environment. JSON output records actual execution and import provenance.
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
from hashlib import sha256
from pathlib import Path
from time import perf_counter


def _within(path, directory):
    return path.resolve().is_relative_to(directory.resolve())


def _provenance(source_root):
    if not sys.flags.isolated or not sys.flags.ignore_environment:
        raise RuntimeError("Run the installed interpreter with -I")
    if _within(Path.cwd(), source_root):
        raise RuntimeError("Installed checks must run outside the source checkout")
    roots = {Path(sysconfig.get_path(name)).resolve() for name in ("purelib", "platlib")}
    silo = importlib.import_module("silo")
    path = Path(silo.__file__).resolve()
    if _within(path, source_root) or not any(_within(path, root) for root in roots):
        raise RuntimeError(f"SILO was not imported from installed site-packages: {path}")
    distribution = importlib.metadata.distribution("silo-solver")
    if distribution.version != silo.__version__:
        raise RuntimeError("Installed distribution and runtime versions disagree")
    direct_url = distribution.read_text("direct_url.json")
    if "scipy" in sys.modules:
        raise RuntimeError("Native package import loaded the optional SciPy dependency")
    if importlib.util.find_spec("scipy") is not None:
        raise RuntimeError("Use a fresh NumPy-only environment with optional SciPy absent")
    return silo, {
        "module_file": str(path),
        "site_packages": sorted(map(str, roots)),
        "distribution": distribution.metadata["Name"],
        "version": distribution.version,
        "python": platform.python_version(),
        "platform": platform.platform(),
        "executable": sys.executable,
        "isolated": True,
        "scipy_installed": False,
        "installation_source": json.loads(direct_url) if direct_url is not None else None,
    }


def _lp_payload():
    return {
        "name": "installed_general_lp",
        "sense": "minimize",
        "variables": [
            {"name": "x", "lower": -2, "upper": 4},
            {"name": "y", "lower": None, "upper": None},
            {"name": "z", "lower": 3, "upper": 3},
            {"name": "u", "lower": None, "upper": 2},
        ],
        "constraints": [
            {
                "name": "range",
                "coefficients": {"x": 1, "y": 1},
                "lower": 1,
                "upper": 3,
                "sense": "<=",
                "rhs": 0,
            }
        ],
        "objective": {"coefficients": {"x": 1, "y": 2, "z": 5, "u": -1}, "constant": 7},
    }


def _milp_payload():
    return {
        "name": "installed_general_milp",
        "sense": "minimize",
        "variables": [
            {"name": "i", "lower": -2, "upper": 1, "type": "integer"},
            {"name": "b", "lower": 0, "upper": 1, "type": "binary"},
            {"name": "f", "lower": 0, "upper": 4},
        ],
        "constraints": [
            {"name": "demand", "coefficients": {"i": 1, "b": 1, "f": 1}, "sense": ">=", "rhs": 1.5},
            {"name": "link", "coefficients": {"f": 1, "b": -2}, "sense": "<=", "rhs": 1},
        ],
        "objective": {"coefficients": {"i": 2, "b": 3, "f": 0.5}, "constant": -2},
    }


def _result_dict(result):
    if isinstance(result, dict):
        return result
    if hasattr(result, "to_dict"):
        return result.to_dict()
    return {
        "status": result.status,
        "objective_value": getattr(result, "objective_value", getattr(result, "objective", None)),
    }


def _assert_optimal(data, expected):
    if data.get("status") != "optimal":
        raise AssertionError(f"Expected installed optimal result: {data}")
    value = data.get("objective_value", data.get("objective"))
    if (
        value is None
        or not math.isfinite(value)
        or abs(value - expected) > 1e-7 * (1 + abs(expected))
    ):
        raise AssertionError(f"Installed objective mismatch: expected {expected}, got {value}")
    return float(value)


def _assert_original_point(payload, data):
    point = data["primal_values"]
    names = {v["name"] for v in payload["variables"]}
    if set(point) != names or not all(math.isfinite(x) for x in point.values()):
        raise AssertionError("Installed result has an incomplete/nonfinite original point")
    for variable in payload["variables"]:
        value = point[variable["name"]]
        for bound, sign in ((variable.get("lower", 0), -1), (variable.get("upper"), 1)):
            if bound is not None and sign * (value - bound) > 1e-7 * (1 + abs(value) + abs(bound)):
                raise AssertionError("Installed primal violates an original variable bound")
        if variable.get("type", "continuous") != "continuous" and abs(value - round(value)) > 1e-7:
            raise AssertionError("Installed primal violates original integrality")
    for row in payload["constraints"]:
        terms = [a * point[n] for n, a in row["coefficients"].items()]
        activity = math.fsum(terms)
        if "lower" in row or "upper" in row:
            lower, upper = row.get("lower"), row.get("upper")
        else:
            sense, rhs = row.get("sense", "<="), row.get("rhs", 0)
            lower = rhs if sense in (">=", "=") else None
            upper = rhs if sense in ("<=", "=") else None
        for bound, sign in ((lower, -1), (upper, 1)):
            scale = 1 + (abs(bound) if bound is not None else 0) + math.fsum(abs(x) for x in terms)
            if bound is not None and sign * (activity - bound) > 1e-7 * scale:
                raise AssertionError("Installed primal violates an original row side")
    recomputed = math.fsum(
        [payload["objective"]["constant"]]
        + [a * point[n] for n, a in payload["objective"]["coefficients"].items()]
    )
    if abs(recomputed - data["objective_value"]) > 1e-7 * (1 + abs(recomputed)):
        raise AssertionError("Installed objective does not match the original primal point")
    for field in ("primal_bound", "dual_bound"):
        if data.get(field) is None or abs(data[field] - recomputed) > 1e-7 * (1 + abs(recomputed)):
            raise AssertionError(f"Installed optimal {field} is missing or inconsistent")
    if data.get("relative_gap") != 0 or data.get("absolute_gap") != 0:
        raise AssertionError("Installed optimal result must publish a zero gap")


def _api_checks(silo):
    io = importlib.import_module("silo.io")
    cases = [("lp_min", _lp_payload(), 18.0), ("milp_min", _milp_payload(), -1.75)]
    maximum = copy.deepcopy(cases[0][1])
    maximum["sense"] = "maximize"
    maximum["objective"]["constant"] *= -1
    maximum["objective"]["coefficients"] = {
        n: -c for n, c in maximum["objective"]["coefficients"].items()
    }
    cases.append(("lp_max", maximum, -18.0))
    records = []
    for identifier, payload, expected in cases:
        start = perf_counter()
        data = _result_dict(
            silo.solve(
                io.model_from_dict(payload),
                silo.SolveOptions(time_limit=20, node_limit=1000, lp_iteration_limit=10000),
            )
        )
        value = _assert_optimal(data, expected)
        _assert_original_point(payload, data)
        if not data.get("has_primal_solution"):
            raise AssertionError("Installed optimal result lost its primal-solution flag")
        records.append(
            {
                "id": identifier,
                "status": data["status"],
                "objective": value,
                "elapsed_seconds": perf_counter() - start,
            }
        )
    return cases, records


def _cli_checks(cases):
    io = importlib.import_module("silo.io")
    records = []
    with tempfile.TemporaryDirectory(prefix="silo-cli-", dir=Path.cwd()) as directory:
        for identifier, payload, expected in cases[:2]:
            model = io.model_from_dict(payload)
            for suffix, contents in (
                ("json", json.dumps(io.model_to_dict(model), allow_nan=False)),
                ("mps", io.model_to_mps(model)),
            ):
                path = Path(directory) / f"{identifier}.{suffix}"
                path.write_text(contents, encoding="utf-8")
                command = [
                    sys.executable,
                    "-I",
                    "-m",
                    "silo",
                    "optimize",
                    str(path),
                    "--time-limit",
                    "20",
                    "--node-limit",
                    "1000",
                ]
                start = perf_counter()
                process = subprocess.run(
                    command, text=True, capture_output=True, check=False, timeout=30, cwd=Path.cwd()
                )
                if process.returncode != 0:
                    raise AssertionError(
                        f"Installed CLI failed: {process.stdout}\n{process.stderr}"
                    )
                data = json.loads(process.stdout)
                if data.get("schema_version") != 2:
                    raise AssertionError("Installed CLI did not publish schema_version=2")
                value = _assert_optimal(data, expected)
                _assert_original_point(payload, data)
                records.append(
                    {
                        "id": f"{identifier}_{suffix}",
                        "status": data["status"],
                        "objective": value,
                        "elapsed_seconds": perf_counter() - start,
                    }
                )
    return records


def _research_checks():
    records = []
    for module_name, function_name, expected in (
        ("silo.decomposition.general_master", "covering_example", 2.5),
        ("silo.mip.research_example", "run_example", -8.5),
    ):
        start = perf_counter()
        function = getattr(importlib.import_module(module_name), function_name)
        result = _result_dict(function())
        value = _assert_optimal(result, expected)
        records.append(
            {
                "module": module_name,
                "function": function_name,
                "status": result["status"],
                "objective": value,
                "elapsed_seconds": perf_counter() - start,
            }
        )
    return records


def run_checks(source_root, artifact=None):
    start = perf_counter()
    source_root = source_root.resolve()
    silo, provenance = _provenance(source_root)
    cases, api = _api_checks(silo)
    cli, research = _cli_checks(cases), _research_checks()
    allowed = [Path(path) for path in provenance["site_packages"]]
    imported = {}
    for name, module in tuple(sys.modules.items()):
        if name == "silo" or name.startswith("silo."):
            path = getattr(module, "__file__", None)
            if path is not None:
                resolved = Path(path).resolve()
                if _within(resolved, source_root) or not any(_within(resolved, p) for p in allowed):
                    raise RuntimeError(f"A SILO module escaped installed site-packages: {name}")
                imported[name] = str(resolved)
    if "scipy" in sys.modules:
        raise RuntimeError("Native installed checks imported optional SciPy")
    report = {
        "status": "passed",
        "provenance": provenance,
        "api": api,
        "cli": cli,
        "research_examples": research,
        "imported_modules": imported,
        "optional_scipy_imported": False,
        "elapsed_seconds": perf_counter() - start,
        "platform_qualification": "this exact interpreter and platform only",
    }
    if artifact is not None:
        artifact = artifact.resolve()
        artifact_hash = sha256(artifact.read_bytes()).hexdigest()
        direct_url = provenance["installation_source"] or {}
        archive = direct_url.get("archive_info", {})
        installed_hash = archive.get("hashes", {}).get("sha256")
        if installed_hash is None and archive.get("hash", "").startswith("sha256="):
            installed_hash = archive["hash"].split("=", 1)[1]
        if installed_hash != artifact_hash:
            raise RuntimeError(
                "Artifact hash does not match the installed direct_url archive identity"
            )
        report["artifact"] = {
            "path": str(artifact),
            "sha256": artifact_hash,
            "installed_archive_hash_matched": True,
        }
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-root", required=True, type=Path)
    parser.add_argument("--artifact", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    start = perf_counter()
    try:
        report = run_checks(args.source_root, args.artifact)
    except (
        AssertionError,
        RuntimeError,
        ImportError,
        OSError,
        ValueError,
        subprocess.TimeoutExpired,
    ) as exc:
        report = {
            "status": "failed",
            "reason": str(exc),
            "python": platform.python_version(),
            "executable": sys.executable,
            "platform": platform.platform(),
            "elapsed_seconds": perf_counter() - start,
        }
    output = json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    print(output, end="")
    if args.report is not None:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output, encoding="utf-8")
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
