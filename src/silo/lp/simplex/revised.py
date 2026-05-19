from dataclasses import dataclass

import numpy as np

from silo.core.enums import ConstraintSense
from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.lp.base import LPSolver
from silo.lp.simplex.basis import Basis
from silo.lp.simplex.standard_form import COLUMN_ORIGINAL, StandardFormProblem, build_standard_form
from silo.utils.numerics import DEFAULT_TOLERANCE


@dataclass(frozen=True)
class BasisState:
    primal_values: np.ndarray
    basic_values: np.ndarray
    reduced_costs: np.ndarray


class RevisedSimplexSolver(LPSolver):
    def __init__(self, iteration_limit: int = 10_000) -> None:
        self.iteration_limit = iteration_limit

    def solve(self, model: Model) -> Solution:
        try:
            problem = build_standard_form(model)
        except ValueError as exc:
            return Solution(status=SolverStatus.ERROR, message=str(exc))

        if problem.artificial_columns:
            return Solution(
                status=SolverStatus.ERROR,
                message=(
                    "Revised simplex feasible-basis solver does not support "
                    "artificial columns yet."
                ),
            )

        basis = problem.initial_basis
        for _ in range(self.iteration_limit):
            state_result = _compute_basis_state(problem, basis)
            if isinstance(state_result, Solution):
                return state_result
            state = state_result

            entering_column = _choose_entering_column(problem, basis, state.reduced_costs)
            if entering_column is None:
                return _optimal_solution(model, problem, basis, state)

            direction_result = _compute_direction(problem, basis, entering_column)
            if isinstance(direction_result, Solution):
                return direction_result
            direction = direction_result

            leaving_row = _choose_leaving_row(state.basic_values, direction)
            if leaving_row is None:
                return Solution(
                    status=SolverStatus.UNBOUNDED,
                    message="Revised simplex detected an unbounded improving direction.",
                )

            basis = basis.pivot(leaving_row=leaving_row, entering_column=entering_column)
            basis.validate(
                column_count=len(problem.columns),
                row_count=len(problem.row_names),
            )

        return Solution(
            status=SolverStatus.ITERATION_LIMIT,
            message=f"Revised simplex reached the iteration limit: {self.iteration_limit}",
        )


def _compute_basis_state(
    problem: StandardFormProblem,
    basis: Basis,
) -> BasisState | Solution:
    matrix = _matrix(problem)
    rhs = np.asarray(problem.rhs, dtype=float)
    objective = np.asarray(problem.objective_coefficients, dtype=float)
    basic_columns = list(basis.basic_columns)

    try:
        basis_matrix = matrix[:, basic_columns]
        basic_values = np.linalg.solve(basis_matrix, rhs)
        simplex_multipliers = np.linalg.solve(basis_matrix.T, objective[basic_columns])
    except np.linalg.LinAlgError as exc:
        return Solution(
            status=SolverStatus.NUMERICAL_ISSUE,
            message=f"Revised simplex failed to solve the basis system: {exc}",
        )

    reduced_costs = objective - simplex_multipliers @ matrix
    primal_values = np.zeros(len(problem.columns))
    for row_index, basic_column in enumerate(basic_columns):
        primal_values[basic_column] = basic_values[row_index]

    return BasisState(
        primal_values=np.asarray([_clean_zero(value) for value in primal_values]),
        basic_values=np.asarray([_clean_zero(value) for value in basic_values]),
        reduced_costs=np.asarray([_clean_zero(value) for value in reduced_costs]),
    )


def _compute_direction(
    problem: StandardFormProblem,
    basis: Basis,
    entering_column: int,
) -> np.ndarray | Solution:
    matrix = _matrix(problem)
    basic_columns = list(basis.basic_columns)
    try:
        direction = np.linalg.solve(matrix[:, basic_columns], matrix[:, entering_column])
    except np.linalg.LinAlgError as exc:
        return Solution(
            status=SolverStatus.NUMERICAL_ISSUE,
            message=f"Revised simplex failed to solve the direction system: {exc}",
        )
    return np.asarray([_clean_zero(value) for value in direction])


def _choose_entering_column(
    problem: StandardFormProblem,
    basis: Basis,
    reduced_costs: np.ndarray,
) -> int | None:
    for column_index in basis.nonbasic_columns:
        if column_index >= len(problem.columns):
            continue
        if reduced_costs[column_index] > DEFAULT_TOLERANCE:
            return column_index
    return None


def _choose_leaving_row(
    basic_values: np.ndarray,
    direction: np.ndarray,
) -> int | None:
    best_row: int | None = None
    best_ratio: float | None = None
    for row_index, direction_value in enumerate(direction):
        if direction_value <= DEFAULT_TOLERANCE:
            continue
        ratio = basic_values[row_index] / direction_value
        if best_ratio is None or (ratio, row_index) < (best_ratio, best_row):
            best_ratio = ratio
            best_row = row_index
    return best_row


def _optimal_solution(
    model: Model,
    problem: StandardFormProblem,
    basis: Basis,
    state: BasisState,
) -> Solution:
    primal_values = _original_primal_values(problem, state.primal_values)
    return Solution(
        status=SolverStatus.OPTIMAL,
        objective_value=_objective_value(problem, state.primal_values),
        primal_values=primal_values,
        slack_values=_constraint_slacks(model, primal_values),
        reduced_costs=_original_reduced_costs(problem, state.reduced_costs),
        basis_status=_original_basis_status(problem, basis),
        message="Revised simplex solved the LP.",
    )


def _original_primal_values(
    problem: StandardFormProblem,
    primal_values: np.ndarray,
) -> dict[str, float]:
    values: dict[str, float] = {}
    for column_index, column in enumerate(problem.columns[: problem.original_variable_count]):
        if column.role == COLUMN_ORIGINAL:
            values[column.name] = _clean_zero(float(primal_values[column_index]))
    return values


def _original_reduced_costs(
    problem: StandardFormProblem,
    reduced_costs: np.ndarray,
) -> dict[str, float]:
    values: dict[str, float] = {}
    for column_index, column in enumerate(problem.columns[: problem.original_variable_count]):
        if column.role == COLUMN_ORIGINAL:
            values[column.name] = _clean_zero(float(reduced_costs[column_index]))
    return values


def _original_basis_status(
    problem: StandardFormProblem,
    basis: Basis,
) -> dict[str, str]:
    return {
        column.name: basis.status_for_column(column_index)
        for column_index, column in enumerate(problem.columns[: problem.original_variable_count])
        if column.role == COLUMN_ORIGINAL
    }


def _objective_value(
    problem: StandardFormProblem,
    primal_values: np.ndarray,
) -> float:
    objective = np.asarray(problem.objective_coefficients, dtype=float)
    return _clean_zero(float(objective @ primal_values + problem.objective_constant))


def _matrix(problem: StandardFormProblem) -> np.ndarray:
    return np.asarray(problem.matrix, dtype=float).reshape(
        len(problem.row_names),
        len(problem.columns),
    )


def _constraint_slacks(model: Model, primal_values: dict[str, float]) -> dict[str, float]:
    slack_values: dict[str, float] = {}
    for constraint in model.constraints:
        activity = sum(
            coefficient * primal_values[variable_name]
            for variable_name, coefficient in constraint.coefficients.items()
        )
        if constraint.sense == ConstraintSense.GE:
            slack = activity - constraint.rhs
        else:
            slack = constraint.rhs - activity
        slack_values[constraint.name] = _clean_zero(slack)
    return slack_values


def _clean_zero(value: float) -> float:
    return 0.0 if abs(value) <= DEFAULT_TOLERANCE else value
