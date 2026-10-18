"""Original-space dual conventions, including Phase I and presolve recovery."""

import numpy as np
import pytest

from silo.cli.main import _solve_model
from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.lp.optimality import check_lp_optimality
from silo.lp.simplex.basis import Basis
from silo.lp.simplex.revised import (
    RevisedSimplexSolver,
    _remove_artificial_columns,
    _run_primal_revised_simplex,
)
from silo.lp.simplex.standard_form import build_standard_form
from silo.lp.simplex.tableau import TableauSimplexSolver
from silo.presolve import Presolver


def _one_variable(coefficient=1.0, sense=ConstraintSense.LE, rhs=3.0, cost=2.0):
    return Model(variables=[Variable("x")],
                 constraints=[Constraint("row", {"x": coefficient}, sense, rhs)],
                 objective=Objective({"x": cost}, OptimizationSense.MAXIMIZE, constant=7.0))


@pytest.mark.parametrize("backend", [TableauSimplexSolver, RevisedSimplexSolver])
@pytest.mark.parametrize("coefficient,sense,rhs,cost,dual", [
    (1, ConstraintSense.LE, 3, 2, 2),
    (1, ConstraintSense.GE, 3, -2, -2),
    (1, ConstraintSense.EQ, 3, 2, 2),
    (-1, ConstraintSense.LE, -3, -2, 2),
    (-1, ConstraintSense.GE, -3, 2, -2),
    (-1, ConstraintSense.EQ, -3, 2, -2),
])
def test_unique_original_dual_signs(backend, coefficient, sense, rhs, cost, dual):
    model = _one_variable(coefficient, sense, rhs, cost)
    solution = backend().solve(model)
    assert solution.status == SolverStatus.OPTIMAL
    assert solution.dual_values == {"row": pytest.approx(dual)}
    assert solution.objective_value == pytest.approx(cost * 3 + 7)
    assert solution.reduced_costs == {"x": pytest.approx(0)}
    assert check_lp_optimality(model, solution).passed


@pytest.mark.parametrize("backend", ["tableau", "revised"])
def test_presolve_restores_removed_rows_and_fixed_reduced_cost(backend):
    model = _one_variable()
    model.variables.append(Variable("fixed", Bounds(2, 2)))
    model.constraints[0].coefficients["fixed"] = 1
    model.constraints.append(Constraint("removed", {"fixed": 1}, ConstraintSense.EQ, 2))
    model.objective.coefficients["fixed"] = 5
    solution = _solve_model(model, backend, True)
    assert solution.dual_values == {"row": pytest.approx(2), "removed": 0}
    # rc_fixed = 5 - (1*2 + 1*0); fixed-variable bound absorbs this multiplier.
    assert solution.reduced_costs["fixed"] == pytest.approx(3)
    assert solution.objective_value == pytest.approx(19)
    assert check_lp_optimality(model, solution).passed


@pytest.mark.parametrize("backend", [TableauSimplexSolver, RevisedSimplexSolver])
def test_redundant_equality_cleanup_preserves_original_dual_equations(backend):
    model = _one_variable(sense=ConstraintSense.EQ)
    model.constraints.append(Constraint("duplicate", {"x": 2}, ConstraintSense.EQ, 6))
    model.constraints.append(Constraint("empty", {}, ConstraintSense.EQ, 0))
    solution = backend().solve(model)
    assert set(solution.dual_values) == {"row", "duplicate", "empty"}
    assert solution.dual_values["row"] + 2 * solution.dual_values["duplicate"] == pytest.approx(2)
    assert solution.objective_value == pytest.approx(13)
    assert check_lp_optimality(model, solution).passed


@pytest.mark.parametrize("backend", [TableauSimplexSolver, RevisedSimplexSolver])
def test_all_fixed_presolve_has_bound_contribution_and_zero_row_duals(backend):
    model = _one_variable()
    model.variables[0] = Variable("x", Bounds(3, 3))
    presolved = Presolver().run(model)
    solution = presolved.recover_solution(backend().solve(presolved.model))
    assert solution.dual_values == {"row": 0}
    assert solution.reduced_costs == {"x": 2}
    assert solution.objective_value == pytest.approx(13)
    assert check_lp_optimality(model, solution).passed


def test_existing_revised_cleanup_slot_source_limit_fails_without_dual_claim():
    # This is a supplied feasible Phase-I basis, not a claim that the current
    # deterministic entering rule can reach it. Preserve the known guard until
    # a separately scoped source-row cleanup fix is approved.
    model = Model(variables=[Variable("x"), Variable("z")], constraints=[
        Constraint("a", {"x": 1}, ConstraintSense.EQ, 1),
        Constraint("b", {"z": 1}, ConstraintSense.EQ, 2),
        Constraint("c", {"z": 1}, ConstraintSense.EQ, 2),
    ], objective=Objective({"x": 1, "z": 1}, OptimizationSense.MAXIMIZE))
    problem = build_standard_form(model)
    # Columns: x,z,artificial_a,artificial_b,artificial_c.
    basis = Basis(basic_columns=(3, 0, 1), nonbasic_columns=(2, 4))
    cleaned = _remove_artificial_columns(problem, basis)
    assert isinstance(cleaned, tuple)
    reduced, new_basis = cleaned
    result = _run_primal_revised_simplex(
        reduced, new_basis, np.asarray(reduced.objective_coefficients), 10, "Phase II",
    )
    assert result.status == SolverStatus.NUMERICAL_ISSUE
    assert result.state is None


@pytest.mark.parametrize("backend", ["tableau", "revised"])
def test_small_fixed_reduced_cost_retains_material_bound_contribution(backend):
    model = _one_variable(cost=2)
    model.variables.append(Variable("fixed", Bounds(1e9, 1e9)))
    model.objective.coefficients["fixed"] = 5e-10
    solution = _solve_model(model, backend, True)
    assert solution.reduced_costs["fixed"] == 5e-10
    reconstructed = model.objective.constant + sum(
        row.rhs * solution.dual_values[row.name] for row in model.constraints
    ) + solution.reduced_costs["fixed"] * 1e9
    assert reconstructed == pytest.approx(13.5)
    assert solution.objective_value == pytest.approx(reconstructed)
    assert check_lp_optimality(model, solution).passed


@pytest.mark.parametrize("backend", [TableauSimplexSolver, RevisedSimplexSolver])
@pytest.mark.parametrize("scale", [1e9, 1e10])
def test_small_row_dual_retains_material_rhs_contribution(backend, scale):
    model = _one_variable(coefficient=scale, rhs=scale, cost=1)
    solution = backend().solve(model)
    assert solution.objective_value == pytest.approx(8)
    assert solution.dual_values["row"] == pytest.approx(1 / scale, rel=1e-12, abs=0)
    assert check_lp_optimality(model, solution).passed
