from dataclasses import replace

import numpy as np
import pytest

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.lp.optimality import check_lp_optimality
from silo.lp.simplex import revised
from silo.lp.simplex.basis import Basis
from silo.lp.simplex.standard_form import build_standard_form

THREE_ROWS = (("a", "x", 1), ("b", "z", 2), ("c", "z", 2))
FOUR_ROWS = (("a", "x", 1), ("b", "x", 1), ("c", "z", 2), ("d", "z", 2))


def _equality_model(rows=THREE_ROWS, constant=0):
    return Model(
        variables=[Variable("x"), Variable("z")],
        constraints=[Constraint(name, {variable: 1}, ConstraintSense.EQ, rhs)
                     for name, variable, rhs in rows],
        objective=Objective({"x": 1, "z": 1}, OptimizationSense.MAXIMIZE, constant),
    )


def _basis(problem, basic):
    return Basis(basic, tuple(j for j in range(len(problem.columns)) if j not in basic))


def _phase_two_solution(model, problem, basis):
    result = revised._run_primal_revised_simplex(
        problem, basis, np.asarray(problem.objective_coefficients), 10, "Phase II",
    )
    assert result.status == SolverStatus.OPTIMAL, result.message
    assert result.state is not None
    solution = revised._optimal_solution(model, problem, result.basis, result.state)
    checked = check_lp_optimality(model, solution)
    assert checked.passed, checked
    return solution


@pytest.mark.parametrize("rows,basic,kept_rows,kept_basis", [
    (THREE_ROWS, (3, 0, 1), ("a", "c"), (0, 1)),
    (FOUR_ROWS, (3, 5, 0, 1), ("a", "c"), (0, 1)),
    (THREE_ROWS, (0, 1, 3), ("a", "c"), (0, 1)),
    ((THREE_ROWS[2], THREE_ROWS[0], THREE_ROWS[1]), (0, 4, 1), ("c", "a"), (0, 1)),
    (THREE_ROWS, (1, 3, 0), ("a", "c"), (1, 0)),
], ids=["one-residual", "two-residuals", "basis-slot-permutation",
        "row-permutation", "surviving-basis-permutation"])
def test_cleanup_keeps_source_rows_and_basis_slots_separate(rows, basic, kept_rows, kept_basis):
    model = _equality_model(rows, constant=7)
    problem = build_standard_form(model)
    basis = _basis(problem, basic)
    basis.validate(len(problem.columns), len(rows))
    # Establish that the supplied basis is nonsingular and Phase-I feasible.
    matrix = np.asarray(problem.matrix)
    values = np.linalg.solve(matrix[:, basic], problem.rhs)
    assert np.all(values >= 0)
    assert all(values[i] == 0 for i, j in enumerate(basic) if j in problem.artificial_columns)
    assert matrix[:, :2] @ [1, 2] == pytest.approx(problem.rhs)

    cleaned = revised._remove_artificial_columns(problem, basis)
    assert isinstance(cleaned, tuple), cleaned
    reduced, new_basis = cleaned
    assert reduced.row_names == kept_rows
    assert tuple(column.name for column in reduced.columns) == ("x", "z")
    assert reduced.artificial_columns == ()
    assert new_basis.basic_columns == kept_basis
    assert np.linalg.matrix_rank(np.asarray(reduced.matrix)[:, kept_basis]) == 2
    solution = _phase_two_solution(model, reduced, new_basis)
    assert solution.primal_values == {"x": 1, "z": 2}
    assert solution.objective_value == 10
    assert all(solution.dual_values[name] == 0 for name, _, _ in rows if name not in kept_rows)


def test_cleanup_renumbers_columns_independently_of_rows_and_basis_slots():
    model = _equality_model(constant=7)
    model.constraints.insert(1, Constraint("limit", {"x": 1}, ConstraintSense.LE, 4))
    problem = build_standard_form(model)
    assert tuple(column.name for column in problem.columns) == (
        "x", "z", "artificial_a", "slack_limit", "artificial_b", "artificial_c",
    )
    cleaned = revised._remove_artificial_columns(problem, _basis(problem, (4, 0, 3, 1)))
    assert isinstance(cleaned, tuple)
    reduced, basis = cleaned
    assert reduced.row_names == ("a", "limit", "c")
    assert tuple(column.name for column in reduced.columns) == ("x", "z", "slack_limit")
    assert basis.basic_columns == (0, 2, 1)
    solution = _phase_two_solution(model, reduced, basis)
    assert solution.objective_value == 10
    assert solution.slack_values["limit"] == 3
    assert solution.dual_values["b"] == solution.dual_values["limit"] == 0


def test_cleanup_with_no_residual_artificial_keeps_original_rows_and_basis_order():
    model = _equality_model((THREE_ROWS[0], THREE_ROWS[2]))
    problem = build_standard_form(model)
    cleaned = revised._remove_artificial_columns(problem, _basis(problem, (1, 0)))
    assert isinstance(cleaned, tuple)
    reduced, basis = cleaned
    assert reduced.row_names == ("a", "c")
    assert basis.basic_columns == (1, 0)
    assert _phase_two_solution(model, reduced, basis).objective_value == 3


@pytest.mark.parametrize("variables,rows,objective", [
    ([], [], {}),
    ([], [Constraint("empty", {}, ConstraintSense.EQ, 0)], {}),
    ([], [Constraint("a", {}, ConstraintSense.EQ, 0),
          Constraint("b", {}, ConstraintSense.EQ, 0)], {}),
    ([Variable("x")], [Constraint("a", {}, ConstraintSense.EQ, 0),
                       Constraint("b", {}, ConstraintSense.EQ, 0)], {"x": -1}),
    ([Variable("x")], [], {"x": -1}),
], ids=["empty-problem", "zero-variable", "all-rows-redundant",
        "zero-rows-after-cleanup", "no-artificial-columns"])
def test_cleanup_empty_boundaries_keep_objective_constant(variables, rows, objective):
    model = Model(variables=variables, constraints=rows,
                  objective=Objective(objective, OptimizationSense.MAXIMIZE, constant=7))
    problem = build_standard_form(model)
    # Reverse artificial basis order to exercise source/slot identity even for empty rows.
    basis = _basis(problem, tuple(reversed(problem.initial_basis.basic_columns)))
    cleaned = revised._remove_artificial_columns(problem, basis)
    assert isinstance(cleaned, tuple)
    reduced, new_basis = cleaned
    assert reduced.row_names == ()
    assert new_basis.basic_columns == ()
    assert reduced.objective_constant == 7
    solution = _phase_two_solution(model, reduced, new_basis)
    assert solution.objective_value == 7
    assert solution.dual_values == dict.fromkeys((row.name for row in rows), 0)


@pytest.mark.parametrize("source,match", [
    (None, "missing"), ("absent", "not found"), ("a", "ambiguous"),
])
def test_cleanup_rejects_bad_source_without_slot_fallback(source, match):
    problem = build_standard_form(_equality_model())
    columns = list(problem.columns)
    columns[3] = replace(columns[3], source_constraint=source)
    problem = replace(problem, columns=tuple(columns))
    result = revised._remove_artificial_columns(problem, _basis(problem, (3, 0, 1)))
    assert isinstance(result, Solution)
    assert result.status == SolverStatus.NUMERICAL_ISSUE
    assert match in result.message
    assert not result.dual_values


def test_cleanup_rejects_ambiguous_source_row_name():
    problem = build_standard_form(_equality_model())
    problem = replace(problem, row_names=("a", "b", "b"))
    result = revised._remove_artificial_columns(problem, _basis(problem, (3, 0, 1)))
    assert isinstance(result, Solution)
    assert result.status == SolverStatus.NUMERICAL_ISSUE
    assert "ambiguous" in result.message


def test_cleanup_rejects_unique_but_swapped_source_names():
    problem = build_standard_form(_equality_model())
    columns = list(problem.columns)
    columns[2] = replace(columns[2], source_constraint="b")
    columns[3] = replace(columns[3], source_constraint="a")
    problem = replace(problem, columns=tuple(columns))
    result = revised._remove_artificial_columns(problem, _basis(problem, (3, 0, 1)))
    assert isinstance(result, Solution)
    assert result.status == SolverStatus.NUMERICAL_ISSUE
    assert "incompatible" in result.message


@pytest.mark.parametrize("artificial_columns", [(2, 3, 3, 4), (2, 3, 99), (2, 3), (0, 2, 3, 4)])
def test_cleanup_rejects_inconsistent_artificial_column_inventory(artificial_columns):
    problem = build_standard_form(_equality_model())
    basis = _basis(problem, (3, 0, 1))
    problem = replace(problem, artificial_columns=artificial_columns)
    result = revised._remove_artificial_columns(problem, basis)
    assert isinstance(result, Solution)
    assert result.status == SolverStatus.NUMERICAL_ISSUE
    assert "artificial column" in result.message


@pytest.mark.parametrize("value", [0.5, float("nan"), float("inf")])
def test_cleanup_rejects_artificial_column_incompatible_with_unit_source(value):
    problem = build_standard_form(_equality_model())
    matrix = [list(row) for row in problem.matrix]
    matrix[1][3] = value
    problem = replace(problem, matrix=tuple(tuple(row) for row in matrix))
    result = revised._remove_artificial_columns(problem, _basis(problem, (3, 0, 1)))
    assert isinstance(result, Solution)
    assert result.status == SolverStatus.NUMERICAL_ISSUE
    assert "incompatible" in result.message


def test_cleanup_validates_source_even_when_artificial_can_pivot_out():
    problem = build_standard_form(_equality_model((THREE_ROWS[0], THREE_ROWS[2])))
    columns = list(problem.columns)
    columns[2] = replace(columns[2], source_constraint=None)
    problem = replace(problem, columns=tuple(columns))
    result = revised._remove_artificial_columns(problem, problem.initial_basis)
    assert isinstance(result, Solution)
    assert result.status == SolverStatus.NUMERICAL_ISSUE
    assert "missing" in result.message


def test_cleanup_rejects_positive_residual_artificial_value():
    model = _equality_model((("a", "x", 1), ("b", "z", 3), ("c", "z", 2)))
    problem = build_standard_form(model)
    result = revised._remove_artificial_columns(problem, _basis(problem, (3, 0, 1)))
    assert isinstance(result, Solution)
    assert result.status == SolverStatus.NUMERICAL_ISSUE
    assert "artificial basic" in result.message


def test_cleanup_preserves_singular_basis_failure():
    problem = build_standard_form(_equality_model())
    result = revised._remove_artificial_columns(problem, _basis(problem, (0, 1, 2)))
    assert isinstance(result, Solution)
    assert result.status == SolverStatus.NUMERICAL_ISSUE
    assert "basis system" in result.message
    assert not result.dual_values


def test_cleanup_does_not_drop_independent_row_after_direction_solve_failure(monkeypatch):
    model = _equality_model((("a", "x", 0),))
    problem = build_standard_form(model)
    monkeypatch.setattr(revised, "_compute_direction", lambda *args, **kwargs:
                        Solution(SolverStatus.NUMERICAL_ISSUE, message="direction solve failed"))
    result = revised._remove_artificial_columns(problem, problem.initial_basis)
    assert isinstance(result, Solution)
    assert result.status == SolverStatus.NUMERICAL_ISSUE
    assert "dependence" in result.message


def test_cleanup_rejects_nonfinite_basis_state():
    problem = build_standard_form(_equality_model())
    problem = replace(problem, rhs=(float("nan"), 2, 2))
    result = revised._remove_artificial_columns(problem, _basis(problem, (3, 0, 1)))
    assert isinstance(result, Solution)
    assert result.status == SolverStatus.NUMERICAL_ISSUE
    assert not result.dual_values


def test_cleanup_reports_failure_to_solve_retained_basis(monkeypatch):
    problem = build_standard_form(_equality_model())
    solve = np.linalg.solve

    def fail_reduced_basis(matrix, rhs):
        if matrix.shape == (2, 2):
            raise np.linalg.LinAlgError("retained basis solve failed")
        return solve(matrix, rhs)

    monkeypatch.setattr(np.linalg, "solve", fail_reduced_basis)
    result = revised._remove_artificial_columns(problem, _basis(problem, (3, 0, 1)))
    assert isinstance(result, Solution)
    assert result.status == SolverStatus.NUMERICAL_ISSUE
    assert "retained basis solve failed" in result.message


def test_cleanup_near_dependence_cannot_claim_optimality_after_residual_amplification():
    # Locally |Q*C| < 1e-9; at the reduced optimum the original-row error exceeds 1.
    # The exact equations imply z=0, x=1e10. Do not certify the approximate reduction.
    model = Model(
        variables=[Variable("x"), Variable("z")],
        constraints=[
            Constraint("almost", {"x": 1, "z": 1 + 5e-10}, ConstraintSense.EQ, 1e10),
            Constraint("other", {"x": 1, "z": 1}, ConstraintSense.EQ, 1e10),
        ],
        objective=Objective({"z": 1}, OptimizationSense.MAXIMIZE),
    )
    solution = revised.RevisedSimplexSolver().solve(model)
    assert solution.status == SolverStatus.NUMERICAL_ISSUE
    assert "original-model" in solution.message
    assert solution.primal_values == solution.dual_values == solution.reduced_costs == {}
