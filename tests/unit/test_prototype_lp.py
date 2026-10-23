"""M2 LP identity, dual reoptimization, QR and separate numerical tolerances."""

import json
import runpy
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest

from silo import SolveOptions, solve
from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.variable import Variable
from silo.io import model_from_dict
from silo.lp.session import LPSession
from silo.lp.verification import check_kkt, primal_check
from silo.modeling.general import linear_data

ROOT = Path(__file__).resolve().parents[2]
R = runpy.run_path(str(ROOT / "scripts/prototype/freeze_manifest.py"))
ORACLE = runpy.run_path(str(ROOT / "scripts/prototype/oracles.py"))
LP = [
    e
    for e in json.loads((ROOT / "tests/fixtures/prototype_manifest.json").read_text())["cases"]
    if e["suite"] == "lp_small"
]


@pytest.mark.parametrize("entry", LP, ids=lambda e: e["id"])
def test_frozen_small_lp(entry):
    payload = R["payload_for"](entry)
    assert R["digest"](payload) == entry["model_sha256"]
    truth = ORACLE["exact_small"](payload, entry["suite"], entry["family"])
    result = solve(model_from_dict(payload), SolveOptions(**entry["options"]))
    assert result.status == truth["status"], result
    if result.status == "optimal":
        assert result.optimality["valid"]
        assert result.objective_value == pytest.approx(float(truth["objective"]), abs=1e-7)
    else:
        assert result.witness["exact"]


def base():
    return model_from_dict(
        {
            "name": "warm",
            "sense": "minimize",
            "variables": [R["variable"]("x", 0, 2), R["variable"]("y", 0, 1.5)],
            "constraints": [R["row"]("r", {"x": 1, "y": 1}, "<=", 2)],
            "objective": {"coefficients": {"x": -1, "y": -2}, "constant": 3},
        }
    )


@pytest.mark.parametrize("change", ["rhs", "bounds", "row", "column"])
def test_four_warm_paths_match_cold_and_use_basis(change):
    options = SolveOptions(presolve=False, scaling=False)
    session = LPSession(base(), options)
    initial = session.solve()
    assert initial.status == "optimal"
    if change == "rhs":
        session.change_rhs("r", 1)
    elif change == "bounds":
        session.change_bounds("x", 0, 0.25)
    elif change == "row":
        session.append_row(Constraint("new", {"x": 1, "y": 1}, rhs=1))
    else:
        session.append_column(Variable("z", Bounds(0, 1)), {"r": 1}, -3)
    warm = session.solve()
    cold = solve(session.model, options)
    assert warm.status == cold.status == "optimal"
    assert warm.objective_value == pytest.approx(cold.objective_value)
    assert warm.diagnostics["warm_starts"] == 1
    assert warm.diagnostics["cold_starts"] == 0
    assert warm.diagnostics["factor_reuses"] > 0
    if change != "column":
        assert warm.diagnostics["dual_pivots"] > 0
        assert warm.diagnostics["warm_mode"] == "dual"
    else:
        assert warm.diagnostics["primal_pivots"] > 0
    assert initial.primal_values == {"x": pytest.approx(0.5), "y": pytest.approx(1.5)}


def test_bad_and_singular_snapshots_have_exactly_one_cold_fallback():
    options = SolveOptions(presolve=False, scaling=False)
    m = model_from_dict(
        R["model"](
            [R["variable"]("x"), R["variable"]("y")],
            [R["row"]("a", {"x": 1, "y": 1}, "<=", 2), R["row"]("b", {"x": 2, "y": 2}, "<=", 4)],
            {"x": -1},
        )
    )
    initial = solve(m, options)
    invalid = replace(initial.basis, basic_keys=(("variable", "x", 1), ("variable", "y", 1)))
    singular = solve(m, options, basis=invalid)
    assert singular.status == "optimal"
    assert singular.diagnostics["cold_starts"] == 1
    assert singular.diagnostics["refactorizations"] >= 1
    assert "Singular" in singular.diagnostics["fallback_reason"]
    stale = solve(m, options, basis=object())
    assert stale.status == "optimal"
    assert stale.diagnostics["cold_starts"] == 1
    assert stale.diagnostics["fallback_reason"]


def test_primal_dual_and_integer_tolerances_are_independent():
    m = model_from_dict(
        R["model"]([R["variable"]("x", 0, 2)], [R["row"]("lo", {"x": 1}, ">=", 1)], {"x": 1})
    )
    data = linear_data(m)
    point = np.array([0.99999])
    multipliers = (np.array([1.0]), np.zeros(1), np.zeros(1), np.zeros(1))
    assert not primal_check(data, point, 1e-9)
    assert not check_kkt(data, point, multipliers, primal_tolerance=1e-9, dual_tolerance=1e-3)[
        "valid"
    ]
    data.integer[:] = True
    assert not primal_check(data, point, 1e-3, integer=True, integrality_tolerance=1e-9)
    m = model_from_dict(
        R["model"](
            [R["variable"]("x", 0, 1, "integer")],
            [R["row"]("cap", {"x": 1}, "<=", 0.99999)],
            {"x": -1},
        )
    )
    result = solve(
        m,
        SolveOptions(
            presolve=False,
            primal_tolerance=1e-9,
            dual_tolerance=1e-9,
            integrality_tolerance=1e-3,
            cuts=False,
            heuristics=False,
        ),
    )
    assert result.status == "optimal"
    assert result.primal_values["x"] == 0
    assert result.objective_value == 0


def test_limits_scaling_and_original_exact_float_semantics():
    m = model_from_dict(R["small_lp"](7))
    on, off = solve(m), solve(m, SolveOptions(scaling=False, presolve=False))
    assert on.status == off.status == "optimal"
    assert on.objective_value == pytest.approx(off.objective_value)
    assert solve(m, SolveOptions(lp_iteration_limit=0)).termination_reason == "lp_iteration_limit"
    assert solve(m, SolveOptions(time_limit=0)).termination_reason == "time_limit"
    # Strict candidate checking uses the original binary coefficient, before sums.
    from silo.lp.verification import exact_ray

    m = model_from_dict(
        R["model"](
            [R["variable"]("x"), R["variable"]("z")],
            [R["row"]("binary", {"x": 10}, "=", 1)],
            {"z": -1},
        )
    )
    assert exact_ray(linear_data(m), [0.1, 0], [0, 1]) is not None  # reconstructs exact 1/10
    m = model_from_dict(
        R["model"](
            [R["variable"]("x"), R["variable"]("z")],
            [R["row"]("binary", {"x": 1}, "=", 0.1)],
            {"z": -1},
        )
    )
    assert exact_ray(linear_data(m), [0.1, 0], [0, 1]) is None  # 1/10 != actual binary RHS


def test_both_row_and_column_scaling_actually_change_coordinates():
    payload = R["model"](
        [R["variable"]("x"), R["variable"]("y")],
        [R["row"]("r", {"x": 1e-4, "y": 1e4}, "<=", 1e4)],
        {"x": -1, "y": -1},
    )
    model = model_from_dict(payload)
    on = solve(model, SolveOptions(presolve=False))
    off = solve(model, SolveOptions(presolve=False, scaling=False))
    assert on.status == off.status == "optimal"
    norm, _, _ = on._lp
    assert np.any(norm.row_scale != 1)
    assert np.any(norm.col_scale != 1)
    assert on.objective_value == pytest.approx(off.objective_value, rel=1e-7)
    assert on.primal_values["x"] == pytest.approx(1e8)
    assert on.optimality["valid"]


def test_session_row_edit_preserves_explicit_interval_semantics():
    m = model_from_dict(
        R["model"](
            [R["variable"]("x", 0, 5)], [R["row"]("r", {"x": 1}, lower=1, upper=3)], {"x": -1}
        )
    )
    session = LPSession(m)
    with pytest.raises(ValueError, match="change_row_bounds"):
        session.change_rhs("r", 4)
    assert session.model.constraints[0].row_bounds == (1, 3)
    session.change_row_bounds("r", None, None)
    assert session.model.constraints[0].row_bounds == (-float("inf"), float("inf"))
    assert session.solve().primal_values["x"] == pytest.approx(5)
