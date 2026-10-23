"""M1 model/IO/restore checks against raw rational truth, not standard form."""

import json
import runpy
import subprocess
import sys
from pathlib import Path

import pytest

from silo import SolveOptions, solve
from silo.core.constraint import Constraint
from silo.core.objective import Objective
from silo.io import model_from_dict, model_to_dict, model_to_mps, parse_mps

ROOT = Path(__file__).resolve().parents[2]
RECIPES = runpy.run_path(str(ROOT / "scripts/prototype/freeze_manifest.py"))
ORACLES = runpy.run_path(str(ROOT / "scripts/prototype/oracles.py"))


@pytest.mark.parametrize("suite", ["lp_small", "milp_small"])
@pytest.mark.parametrize("family", range(12))
def test_general_model_base(suite, family):
    payload = RECIPES["small_lp" if suite == "lp_small" else "small_milp"](family)
    truth = ORACLES["exact_small"](payload, suite, family)
    result = solve(model_from_dict(payload))
    assert result.status == truth["status"], result
    if result.status == "optimal":
        assert result.objective_value == pytest.approx(float(truth["objective"]), abs=1e-7)
        assert result.optimality.get("valid", result.optimality.get("integer_feasible"))
    else:
        assert result.witness is not None


@pytest.mark.parametrize("family", [1, 2, 3, 4, 7, 10, 11])
@pytest.mark.parametrize("presolve", [False, True])
def test_original_kkt_signs_and_complementarity(family, presolve):
    payload = RECIPES["small_lp"](family)
    result = solve(model_from_dict(payload), SolveOptions(presolve=presolve))
    assert result.status == "optimal"
    # This check reconstructs all equations directly from raw input records.
    point, sides = result.primal_values, result.side_multipliers
    sign = 1 if payload["sense"] == "minimize" else -1
    for v in payload["variables"]:
        name = v["name"]
        rc = payload["objective"]["coefficients"].get(name, 0) - sum(
            r["coefficients"].get(name, 0) * result.dual_values[r["name"]]
            for r in payload["constraints"]
        )
        zl, zu = sides["variable_lower"][name], sides["variable_upper"][name]
        assert sign * rc - zl + zu == pytest.approx(0, abs=1e-7)
        for bound, multiplier in ((v["lower"], zl), (v["upper"], zu)):
            assert multiplier >= -1e-7
            assert (
                multiplier if bound is None else multiplier * (point[name] - bound)
            ) == pytest.approx(0, abs=1e-7)
    for r in payload["constraints"]:
        lower, upper = ORACLES["row_sides"](r)
        value = sum(a * point[n] for n, a in r["coefficients"].items())
        for bound, key in ((lower, "row_lower"), (upper, "row_upper")):
            mu = sides[key][r["name"]]
            assert mu >= -1e-7
            assert (mu if bound is None else mu * (value - bound)) == pytest.approx(0, abs=1e-7)


def test_derived_fixed_dual_returns_to_source_row():
    result = solve(model_from_dict(RECIPES["small_lp"](3)))
    assert result.dual_values["fix"] == pytest.approx(1)
    assert result.reduced_costs["x"] == pytest.approx(0)
    assert result.side_multipliers["variable_lower"]["x"] == pytest.approx(0)
    assert result.side_multipliers["variable_upper"]["x"] == pytest.approx(0)
    assert result.diagnostics["bound_tightenings"] == 2


def test_python_json_mps_and_cli_agree(tmp_path):
    model = model_from_dict(RECIPES["small_lp"](10))
    assert solve(model).objective_value == pytest.approx(20)
    assert solve(parse_mps(model_to_mps(model))).objective_value == pytest.approx(20)
    for suffix, text in (("json", json.dumps(model_to_dict(model))), ("mps", model_to_mps(model))):
        path = tmp_path / f"model.{suffix}"
        path.write_text(text, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, "-m", "silo", "optimize", str(path)],
            text=True,
            capture_output=True,
            check=False,
        )
        assert proc.returncode == 0, proc.stderr + proc.stdout
        data = json.loads(proc.stdout)
        assert data["schema_version"] == 2
        assert data["objective_value"] == pytest.approx(20)
        assert data["has_primal_solution"]


def test_invalid_data_and_resource_limits_are_structured():
    model = model_from_dict(RECIPES["small_lp"](0))
    model.set_objective(Objective(coefficients={"x": float("nan")}))
    assert solve(model).status == "invalid_model"
    model = model_from_dict(RECIPES["small_lp"](0))
    assert solve(model, SolveOptions(max_dense_cells=1)).termination_reason == "resource_limit"
    with pytest.raises(ValueError):
        SolveOptions(time_limit=-1)
    with pytest.raises(ValueError):
        SolveOptions(lp_iteration_limit=1.5)
    assert Constraint("free", lower_bound=-float("inf"), upper_bound=float("inf")).row_bounds == (
        -float("inf"),
        float("inf"),
    )


def test_legacy_standard_form_explicitly_rejects_general_rows():
    from silo.lp.simplex.revised import RevisedSimplexSolver
    from silo.lp.simplex.tableau import TableauSimplexSolver

    model = model_from_dict(RECIPES["small_lp"](4))
    for solver in (RevisedSimplexSolver(), TableauSimplexSolver()):
        result = solver.solve(model)
        assert result.status.value == "error"
        assert "silo.solve" in result.message
