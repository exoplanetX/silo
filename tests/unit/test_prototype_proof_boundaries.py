"""Narrow independently requested M3 proof, lattice and limit regressions."""

import itertools
import runpy
from dataclasses import replace
from fractions import Fraction as F
from math import inf
from pathlib import Path
from time import perf_counter

import numpy as np
import pytest

from silo import SolveOptions, SolveResult, solve
from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.cuts.gmi import ExactGmi, derive_gmi
from silo.io import model_from_dict, model_to_mps, parse_mps
from silo.lp.general import solve_lp_data
from silo.lp.tableau_view import AffineCoordinate, GmiTableauRow, exact_tableau_rows
from silo.modeling.general import linear_data
from silo.utils.rational import ProofBudget, exact_solve

ROOT = Path(__file__).resolve().parents[2]
R = runpy.run_path(str(ROOT / "scripts/prototype/freeze_manifest.py"))


@pytest.mark.parametrize("location", ["bound", "rhs", "range", "coefficient"])
@pytest.mark.parametrize("input_format", ["python", "json", "mps"])
def test_unrepresentable_integer_never_silently_changes_model(location, input_format):
    value = 2**53 + 1
    p = R["model"](
        [R["variable"]("x", 0, 2, "integer")], [R["row"]("r", {"x": 1}, "=", 1)], {"x": 1}
    )
    if location == "bound":
        p["variables"][0].update(lower=value, upper=value)
        p["constraints"] = []
    elif location == "rhs":
        p["constraints"][0]["rhs"] = value
    elif location == "range":
        p["constraints"][0].update(lower=value, upper=value + 2)
    else:
        p["constraints"][0]["coefficients"]["x"] = value
    if input_format == "python":
        v = p["variables"][0]
        m = Model(
            variables=[Variable("x", Bounds(v["lower"], v["upper"]), "integer")],
            constraints=[
                Constraint(
                    "r",
                    row["coefficients"],
                    row["sense"],
                    row["rhs"],
                    row.get("lower"),
                    row.get("upper"),
                )
                for row in p["constraints"]
            ],
            objective=Objective({"x": 1}),
        )
    else:
        m = model_from_dict(p)
        if input_format == "mps":
            m = parse_mps(model_to_mps(m))
    result = solve(m)
    assert result.status == "numerical_failure"
    assert result.termination_reason == "input_conversion"


def test_exactly_representable_large_integer_is_accepted():
    m = model_from_dict(R["model"]([R["variable"]("x", 2**53, 2**53, "integer")], [], {}))
    assert solve(m).status == "optimal"


@pytest.mark.parametrize(
    "maximize,kind", [(False, "negative_infinity"), (True, "positive_infinity")]
)
def test_unresolved_infinity_survives_json(maximize, kind):
    p = R["boundary_input"](7)["model"]
    if maximize:
        p["sense"] = "maximize"
        p["objective"]["coefficients"]["y"] = 1
    result = solve(model_from_dict(p), SolveOptions(integer_ray_proof_limit=0))
    output = result.to_dict()
    assert output["dual_bound"] is None
    assert output["dual_bound_kind"] == kind
    assert output["relative_gap"] is output["absolute_gap"] is None


def test_conflicting_unbounded_child_does_not_publish_finite_gap(monkeypatch):
    import silo.lp.general as lp_module

    original, zero_calls = lp_module.solve_lp_data, 0

    def controlled(data, options, basis=None, deadline=inf):
        nonlocal zero_calls
        if data.lower[0] == data.upper[0] == 0:
            zero_calls += 1
            if zero_calls == 2:  # after the failed rounding heuristic, corrupt the child result
                return SolveResult("unbounded", "controlled_conflict")
        return original(data, options, basis, deadline)

    monkeypatch.setattr(lp_module, "solve_lp_data", controlled)
    p = R["model"](
        [R["variable"]("x", 0, 2, "integer")], [R["row"]("r", {"x": 1}, ">=", 0.3)], {"x": 10}
    )
    result = solve(model_from_dict(p), SolveOptions(presolve=False, cuts=False))
    assert result.status == "numerical_failure"
    assert result.primal_bound == 10
    assert result.dual_bound == -inf
    assert result.absolute_gap is result.relative_gap is None
    assert result.diagnostics["unbounded_state"] == "conflicting_unbounded_relaxation"


def test_published_unbounded_anchor_is_the_verified_anchor(monkeypatch):
    import silo.lp.general as lp_module

    original = lp_module.solve_lp_data

    def controlled(*args, **kwargs):
        result = original(*args, **kwargs)
        if result.status == "unbounded":
            result.primal_values["x"] = 1 - 2**-40
        return result

    monkeypatch.setattr(lp_module, "solve_lp_data", controlled)
    p = R["model"](
        [R["variable"]("x", 1, 1, "integer"), R["variable"]("y")], [], {"x": -1, "y": -1}
    )
    result = solve(model_from_dict(p))
    assert result.status == "unbounded"
    assert result.primal_values["x"] == F(result.witness["point"]["x"]) == 1
    assert result.objective_value == -1


def test_public_lp_can_keep_rational_anchor_without_publishing_rounded_float():
    p = R["model"](
        [R["variable"]("x"), R["variable"]("y")], [R["row"]("third", {"x": 3}, "=", 1)], {"y": -1}
    )
    result = solve(model_from_dict(p), SolveOptions(presolve=False))
    assert result.status == "unbounded"
    assert result.witness["point"]["x"] == "1/3"
    assert not result.has_primal_solution
    assert not result.primal_values


@pytest.mark.parametrize("reflection", [False, True])
@pytest.mark.parametrize("scaling", [False, True])
def test_gmi_shift_reflection_scaling_and_trace(reflection, scaling):
    variables = [
        R["variable"]("x", None if reflection else -2, 3, "integer"),
        R["variable"]("y", 0, 4),
    ]
    scale = 10000 if scaling else 1
    p = R["model"](
        variables,
        [
            R["row"](
                "r",
                {"x": (-2 if reflection else 2) * scale, "y": scale},
                ">=",
                (-5 if reflection else -1) * scale,
            )
        ],
        {"x": -1 if reflection else 1, "y": 1},
    )
    data = linear_data(model_from_dict(p))
    lp = solve_lp_data(
        replace(data, integer=np.zeros_like(data.integer)),
        SolveOptions(presolve=False, scaling=scaling),
    )
    norm, native, _ = lp._lp
    views = exact_tableau_rows(norm, native, data.integer)
    assert views
    cuts = [derive_gmi(view, 2) for view in views]
    assert any(cut is not None for cut in cuts)
    for cut in cuts:
        if cut is None:
            continue
        proof = cut.proof()
        assert proof["basis_keys"] and proof["effective_box"]
        assert proof["nonbasic_coordinates"]
        for x in range(-8 if reflection else -2, 4):
            lower_y = max(F(0), (-5 + 2 * x) if reflection else (-1 - 2 * x))
            for y in (lower_y, F(4)):
                if y >= lower_y and y <= 4:
                    assert cut.coefficients[0] * x + cut.coefficients[1] * y >= cut.lower


def test_slack_integer_tags_and_free_projection_rejection():
    p = R["model"](
        [
            R["variable"]("x", 0, 3, "integer"),
            R["variable"]("w", 0, 1, "integer"),
            R["variable"]("y", 0, 4),
        ],
        [R["row"]("r", {"x": 2, "w": -1, "y": 1}, ">=", 2)],
        {"x": 1, "w": -2, "y": 1},
    )
    data = linear_data(model_from_dict(p))
    lp = solve_lp_data(
        replace(data, integer=np.zeros_like(data.integer)), SolveOptions(presolve=False)
    )
    views = exact_tableau_rows(*lp._lp[:2], data.integer)
    coords = [v for view in views for v in view.coordinates if v is not None]
    assert any(v.key == ("slack", ("bound", "w", "upper")) and v.integer for v in coords)
    assert any(v.key == ("slack", ("row", "r", "lower")) and not v.integer for v in coords)
    free = GmiTableauRow(("int",), F(3, 2), (F(1, 2),), (None,), True, ())
    assert derive_gmi(free, 1) is None


def test_float_gmi_is_outward_over_asymmetric_box_and_refuses_missing_error_side():
    source = GmiTableauRow(("b",), F(3, 2), (), (), True, ())
    cut = ExactGmi((F(1, 3), F(-1, 3)), F(2, 7), (), F(1, 2), source)
    names, lower, upper = ("x", "y"), (-2, -7), (5, 3)
    candidate = cut.to_candidate(names, lower, upper, 4, 0)
    proof = cut.float_proof(candidate, names, lower, upper)
    assert F(proof["minimum_box_error"]) < 0
    floats = dict(candidate.coefficients)
    for x, y in itertools.product((-2, 5), (-7, 3)):
        relaxed = F(floats["x"]) * x + F(floats["y"]) * y - F(candidate.rhs)
        exact = cut.coefficients[0] * x + cut.coefficients[1] * y - cut.lower
        assert relaxed >= exact
    assert cut.to_candidate(names, lower, (inf, 3), 4, 0) is None
    assert cut.to_candidate(names, (-2, -inf), upper, 4, 0) is None


def test_exact_proof_budget_and_expired_deadline_cannot_generate_cuts():
    with pytest.raises(ValueError, match="budget"):
        exact_solve([[F(1)]], [F(1)], operation_limit=0)
    with pytest.raises(ValueError, match="budget"):
        exact_solve([[F(1)]], [F(1)], deadline=perf_counter() - 1)
    p = R["model"](
        [R["variable"]("x", 0, 3, "integer"), R["variable"]("y")],
        [R["row"]("r", {"x": 2, "y": 1}, ">=", 3)],
        {"x": 1, "y": 1},
    )
    result = solve(
        model_from_dict(p),
        SolveOptions(presolve=False, proof_operation_limit=0, node_limit=1, heuristics=False),
    )
    assert result.status == "limit"
    assert result.diagnostics["cuts_added"] == 0
    assert result.diagnostics["open_nodes"] == 2
    assert result.relative_gap is None


def test_gmi_shared_budget_reaches_projection_conversion_and_trace():
    coordinate = AffineCoordinate(("z",), F(0), (F(1),), True)
    row = GmiTableauRow(("b",), F(3, 2), (F(1, 2),), (coordinate,), True, ())
    assert derive_gmi(row, 1, budget=ProofBudget(9)) is None
    assert derive_gmi(row, 1, budget=ProofBudget(deadline=perf_counter() - 1)) is None
    shared = ProofBudget(200)
    exact = derive_gmi(row, 1, budget=shared)
    assert exact is not None and shared.remaining < 200
    assert exact.to_candidate(("x",), (0,), (2,), 0, 0, budget=ProofBudget(4)) is None
    candidate = exact.to_candidate(("x",), (0,), (2,), 0, 0, budget=shared)
    assert candidate is not None
    assert exact.proof(budget=ProofBudget(2)) is None
    assert exact.proof(budget=shared)["scope"] == "node_local"
    assert exact.float_proof(candidate, ("x",), (0,), (2,), budget=ProofBudget(3)) is None
    assert exact.float_proof(candidate, ("x",), (0,), (2,), budget=shared)
    assert 0 < shared.remaining < 180


def test_gmi_rejects_rational_growth_during_projection():
    coordinate = AffineCoordinate(("z",), F(0), (F(1 << 4096, 3),), True)
    row = GmiTableauRow(("b",), F(3, 2), (F(1, 2),), (coordinate,), True, ())
    assert derive_gmi(row, 1) is None


@pytest.mark.parametrize("entry", ["propagate", "mip"])
def test_final_redundancy_scan_obeys_deadline_and_retains_node(monkeypatch, entry):
    import silo.presolve.activity as activity

    calls, now = 0, perf_counter()

    def clock():
        nonlocal calls
        calls += 1
        return now if calls < 6 else now + 100

    monkeypatch.setattr(activity, "perf_counter", clock)
    model = model_from_dict(
        R["model"](
            [R["variable"]("x", 0, 2, "integer")],
            [R["row"]("r", {"x": 1}, "<=", 1)],
            {"x": -1},
        )
    )
    if entry == "propagate":
        result = activity.propagate(linear_data(model), integral=True, deadline=now + 10)
        assert result.timed_out and calls == 6
    else:
        result = solve(model, SolveOptions(time_limit=10))
        assert result.status == "limit" and result.termination_reason == "time_limit"
        assert result.diagnostics["lp_calls"] == 0
        assert result.diagnostics["open_nodes"] == 1
        assert result.dual_bound == -inf and result.relative_gap is None
