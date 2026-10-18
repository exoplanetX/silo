from dataclasses import replace
from math import inf

import pytest

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.lp.optimality import check_lp_optimality


def _evidence():
    model = Model(
        variables=[Variable("x")],
        constraints=[Constraint("capacity", {"x": 1}, ConstraintSense.LE, 3)],
        objective=Objective({"x": 2}, OptimizationSense.MAXIMIZE, 7),
    )
    solution = Solution(SolverStatus.OPTIMAL, objective_value=13,
                        primal_values={"x": 3}, dual_values={"capacity": 2},
                        reduced_costs={"x": 0})
    return model, solution


def test_checker_accepts_hand_derived_evidence_without_backend():
    model, solution = _evidence()
    check = check_lp_optimality(model, solution)
    assert check.passed
    assert check.primal_objective == check.dual_objective == 13
    assert check.objective_gap == check.stationarity_violation == 0


@pytest.mark.parametrize("field,value", [
    ("objective_value", 14), ("primal_values", {"x": 4}),
    ("primal_values", {"x": 2}), ("primal_values", {"x": -1}),
    ("dual_values", {"capacity": -2}), ("dual_values", {"capacity": 1}),
    ("reduced_costs", {"x": -1}), ("dual_values", {}),
    ("dual_values", {"capacity": 2, "extra": 0}),
    ("primal_values", {}), ("reduced_costs", {}),
    ("objective_value", float("nan")), ("objective_value", inf),
    ("primal_values", {"x": float("nan")}), ("dual_values", {"capacity": inf}),
    ("reduced_costs", {"x": float("nan")}),
])
def test_checker_rejects_independently_corrupted_evidence(field, value):
    model, solution = _evidence()
    assert not check_lp_optimality(model, replace(solution, **{field: value})).passed


@pytest.mark.parametrize("status", [SolverStatus.INFEASIBLE, SolverStatus.UNBOUNDED,
                                   SolverStatus.ITERATION_LIMIT, SolverStatus.ERROR])
def test_checker_rejects_nonoptimal_status(status):
    model, solution = _evidence()
    assert not check_lp_optimality(model, replace(solution, status=status)).passed


@pytest.mark.parametrize("domain", ["minimize", "integer", "binary", "upper", "lower", "free"])
def test_checker_rejects_unsupported_domains(domain):
    model, solution = _evidence()
    if domain == "minimize":
        model.objective = Objective({"x": 2}, OptimizationSense.MINIMIZE)
    else:
        variable = {
            "integer": Variable("x", Bounds(0, 3), VariableType.INTEGER),
            "binary": Variable("x", Bounds(0, 1), VariableType.BINARY),
            "upper": Variable("x", Bounds(0, 3)),
            "lower": Variable("x", Bounds(1, inf)),
            "free": Variable("x", Bounds(-inf, inf)),
        }[domain]
        model.variables = [variable]
    assert not check_lp_optimality(model, solution).passed


@pytest.mark.parametrize("tolerance", [0, -1, inf, float("nan")])
def test_invalid_tolerance_is_explicit(tolerance):
    model, solution = _evidence()
    with pytest.raises(ValueError, match="tolerance"):
        check_lp_optimality(model, solution, tolerance)


def test_checker_accepts_alternative_dual_optima():
    model, solution = _evidence()
    model.constraints.append(Constraint("duplicate", {"x": 1}, ConstraintSense.LE, 3))
    for dual in ({"capacity": 2, "duplicate": 0}, {"capacity": 0, "duplicate": 2}):
        assert check_lp_optimality(model, replace(solution, dual_values=dual)).passed


@pytest.mark.parametrize("fixed_value,rc", [(2, 3), (2, -3), (-2, 3), (0, -3)])
def test_checker_includes_fixed_bound_contribution(fixed_value, rc):
    model = Model(variables=[Variable("f", Bounds(fixed_value, fixed_value))],
                  objective=Objective({"f": rc}, OptimizationSense.MAXIMIZE, 7))
    value = 7 + fixed_value * rc
    solution = Solution(SolverStatus.OPTIMAL, objective_value=value,
                        primal_values={"f": fixed_value}, reduced_costs={"f": rc})
    result = check_lp_optimality(model, solution)
    assert result.passed
    assert result.dual_objective == value


def test_checker_rejects_nonfinite_arithmetic_even_with_finite_inputs():
    model = Model(variables=[Variable("x"), Variable("z")],
                  constraints=[Constraint("r", {"x": 1e308, "z": -1e308},
                                          ConstraintSense.EQ, 0)],
                  objective=Objective({}, OptimizationSense.MAXIMIZE))
    solution = Solution(SolverStatus.OPTIMAL, objective_value=0,
                        primal_values={"x": 2, "z": 2}, dual_values={"r": 0},
                        reduced_costs={"x": 0, "z": 0})
    assert not check_lp_optimality(model, solution).passed


def test_checker_rejects_nonfinite_model_data():
    model, solution = _evidence()
    model.constraints[0].coefficients["x"] = float("nan")
    assert not check_lp_optimality(model, solution).passed


def test_checker_does_not_trust_reported_slacks_or_basis():
    model, solution = _evidence()
    solution = replace(solution, slack_values={"capacity": 100}, basis_status={"x": "wrong"})
    assert check_lp_optimality(model, solution).passed


def test_absolute_tolerance_is_applied_to_reported_objective():
    model, solution = _evidence()
    solution = replace(solution, objective_value=13 + 5e-8)
    assert check_lp_optimality(model, solution, 1e-7).passed
    assert not check_lp_optimality(model, solution, 1e-9).passed


def test_zero_gap_alone_does_not_validate_wrong_dual_signs():
    model, solution = _evidence()
    model.objective = Objective({}, OptimizationSense.MAXIMIZE)
    model.constraints[0] = replace(model.constraints[0], rhs=0)
    solution = replace(solution, objective_value=0, primal_values={"x": 0},
                       dual_values={"capacity": -1}, reduced_costs={"x": 1})
    check = check_lp_optimality(model, solution)
    assert check.objective_gap == check.complementarity_violation == 0
    assert check.dual_violation == 1
    assert not check.passed
