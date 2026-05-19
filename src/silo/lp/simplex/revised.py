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


@dataclass(frozen=True)
class RevisedRunResult:
    status: SolverStatus
    basis: Basis
    state: BasisState | None = None
    message: str = ""


class RevisedSimplexSolver(LPSolver):
    def __init__(self, iteration_limit: int = 10_000) -> None:
        self.iteration_limit = iteration_limit

    def solve(self, model: Model) -> Solution:
        try:
            problem = build_standard_form(model)
        except ValueError as exc:
            return Solution(status=SolverStatus.ERROR, message=str(exc))

        basis = problem.initial_basis
        if problem.artificial_columns:
            phase_one_objective = _phase_one_objective(problem)
            phase_one_result = _run_primal_revised_simplex(
                problem=problem,
                basis=basis,
                objective_coefficients=phase_one_objective,
                iteration_limit=self.iteration_limit,
                phase_name="Phase I",
            )
            if phase_one_result.status == SolverStatus.UNBOUNDED:
                return Solution(
                    status=SolverStatus.NUMERICAL_ISSUE,
                    message=(
                        "Revised simplex Phase I became unbounded; "
                        "the artificial problem should be bounded."
                    ),
                )
            if phase_one_result.status != SolverStatus.OPTIMAL:
                return Solution(status=phase_one_result.status, message=phase_one_result.message)
            if phase_one_result.state is None:
                return Solution(
                    status=SolverStatus.NUMERICAL_ISSUE,
                    message="Revised simplex Phase I did not return a basis state.",
                )

            phase_one_value = _objective_value(
                primal_values=phase_one_result.state.primal_values,
                objective_coefficients=phase_one_objective,
                objective_constant=0.0,
            )
            if phase_one_value < -DEFAULT_TOLERANCE:
                return Solution(
                    status=SolverStatus.INFEASIBLE,
                    message="Revised simplex Phase I detected infeasibility.",
                )

            cleanup_result = _remove_artificial_columns(
                problem=problem,
                basis=phase_one_result.basis,
            )
            if isinstance(cleanup_result, Solution):
                return cleanup_result
            problem, basis = cleanup_result

        phase_two_result = _run_primal_revised_simplex(
            problem=problem,
            basis=basis,
            objective_coefficients=np.asarray(problem.objective_coefficients, dtype=float),
            iteration_limit=self.iteration_limit,
            phase_name="Phase II",
        )
        if phase_two_result.status == SolverStatus.OPTIMAL:
            if phase_two_result.state is None:
                return Solution(
                    status=SolverStatus.NUMERICAL_ISSUE,
                    message="Revised simplex Phase II did not return a basis state.",
                )
            return _optimal_solution(model, problem, phase_two_result.basis, phase_two_result.state)
        return Solution(status=phase_two_result.status, message=phase_two_result.message)


def _run_primal_revised_simplex(
    problem: StandardFormProblem,
    basis: Basis,
    objective_coefficients: np.ndarray,
    iteration_limit: int,
    phase_name: str,
) -> RevisedRunResult:
    basis.validate(column_count=len(problem.columns), row_count=len(problem.row_names))
    for _ in range(iteration_limit):
        state_result = _compute_basis_state(problem, basis, objective_coefficients)
        if isinstance(state_result, Solution):
            return RevisedRunResult(
                status=state_result.status,
                basis=basis,
                message=state_result.message,
            )
        state = state_result

        entering_column = _choose_entering_column(problem, basis, state.reduced_costs)
        if entering_column is None:
            return RevisedRunResult(status=SolverStatus.OPTIMAL, basis=basis, state=state)

        direction_result = _compute_direction(problem, basis, entering_column)
        if isinstance(direction_result, Solution):
            return RevisedRunResult(
                status=direction_result.status,
                basis=basis,
                message=direction_result.message,
            )
        direction = direction_result

        leaving_row = _choose_leaving_row(state.basic_values, direction)
        if leaving_row is None:
            return RevisedRunResult(
                status=SolverStatus.UNBOUNDED,
                basis=basis,
                message=(
                    f"Revised simplex {phase_name} detected an unbounded "
                    "improving direction."
                ),
            )

        basis = basis.pivot(leaving_row=leaving_row, entering_column=entering_column)
        basis.validate(
            column_count=len(problem.columns),
            row_count=len(problem.row_names),
        )

    return RevisedRunResult(
        status=SolverStatus.ITERATION_LIMIT,
        basis=basis,
        message=f"Revised simplex {phase_name} reached the iteration limit: {iteration_limit}",
    )


def _phase_one_objective(problem: StandardFormProblem) -> np.ndarray:
    objective = np.zeros(len(problem.columns))
    for column_index in problem.artificial_columns:
        # Phase I minimizes sum(artificial variables) by maximizing its negative.
        objective[column_index] = -1.0
    return objective


def _remove_artificial_columns(
    problem: StandardFormProblem,
    basis: Basis,
) -> tuple[StandardFormProblem, Basis] | Solution:
    artificial_set = set(problem.artificial_columns)
    basis = _pivot_artificial_basics_out(problem, basis, artificial_set)
    if isinstance(basis, Solution):
        return basis

    state_result = _compute_basis_state(
        problem=problem,
        basis=basis,
        objective_coefficients=np.asarray(problem.objective_coefficients, dtype=float),
    )
    if isinstance(state_result, Solution):
        return state_result

    redundant_rows: set[int] = set()
    for row_index, basic_column in enumerate(basis.basic_columns):
        if basic_column not in artificial_set:
            continue
        if abs(state_result.basic_values[row_index]) > DEFAULT_TOLERANCE:
            return Solution(
                status=SolverStatus.NUMERICAL_ISSUE,
                message="Revised simplex could not remove a positive artificial basic variable.",
            )
        redundant_rows.add(row_index)

    kept_columns = [
        column_index
        for column_index in range(len(problem.columns))
        if column_index not in artificial_set
    ]
    kept_rows = [
        row_index
        for row_index in range(len(problem.row_names))
        if row_index not in redundant_rows
    ]
    column_map = {
        old_column: new_column
        for new_column, old_column in enumerate(kept_columns)
    }

    new_basic_columns = tuple(
        column_map[basis.basic_columns[row_index]]
        for row_index in kept_rows
    )
    basic_set = set(new_basic_columns)
    new_basis = Basis(
        basic_columns=new_basic_columns,
        nonbasic_columns=tuple(
            new_column
            for new_column in range(len(kept_columns))
            if new_column not in basic_set
        ),
    )

    new_problem = StandardFormProblem(
        name=problem.name,
        columns=tuple(problem.columns[column_index] for column_index in kept_columns),
        row_names=tuple(problem.row_names[row_index] for row_index in kept_rows),
        matrix=tuple(
            tuple(problem.matrix[row_index][column_index] for column_index in kept_columns)
            for row_index in kept_rows
        ),
        rhs=tuple(problem.rhs[row_index] for row_index in kept_rows),
        objective_coefficients=tuple(
            problem.objective_coefficients[column_index]
            for column_index in kept_columns
        ),
        objective_constant=problem.objective_constant,
        initial_basis=new_basis,
        artificial_columns=(),
        original_variable_count=problem.original_variable_count,
    )
    new_basis.validate(
        column_count=len(new_problem.columns),
        row_count=len(new_problem.row_names),
    )
    return new_problem, new_basis


def _pivot_artificial_basics_out(
    problem: StandardFormProblem,
    basis: Basis,
    artificial_set: set[int],
) -> Basis | Solution:
    while True:
        pivoted = False
        for row_index, basic_column in enumerate(basis.basic_columns):
            if basic_column not in artificial_set:
                continue
            entering_column = _find_artificial_cleanup_entering_column(
                problem=problem,
                basis=basis,
                leaving_row=row_index,
                artificial_set=artificial_set,
            )
            if entering_column is None:
                continue
            basis = basis.pivot(leaving_row=row_index, entering_column=entering_column)
            basis.validate(column_count=len(problem.columns), row_count=len(problem.row_names))
            pivoted = True
            break
        if not pivoted:
            return basis


def _find_artificial_cleanup_entering_column(
    problem: StandardFormProblem,
    basis: Basis,
    leaving_row: int,
    artificial_set: set[int],
) -> int | None:
    for column_index in basis.nonbasic_columns:
        if column_index in artificial_set:
            continue
        direction_result = _compute_direction(problem, basis, column_index)
        if isinstance(direction_result, Solution):
            continue
        if abs(direction_result[leaving_row]) > DEFAULT_TOLERANCE:
            return column_index
    return None


def _compute_basis_state(
    problem: StandardFormProblem,
    basis: Basis,
    objective_coefficients: np.ndarray,
) -> BasisState | Solution:
    matrix = _matrix(problem)
    rhs = np.asarray(problem.rhs, dtype=float)
    objective = np.asarray(objective_coefficients, dtype=float)
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
        objective_value=_objective_value(
            primal_values=state.primal_values,
            objective_coefficients=np.asarray(problem.objective_coefficients, dtype=float),
            objective_constant=problem.objective_constant,
        ),
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
    primal_values: np.ndarray,
    objective_coefficients: np.ndarray,
    objective_constant: float,
) -> float:
    objective = np.asarray(objective_coefficients, dtype=float)
    return _clean_zero(float(objective @ primal_values + objective_constant))


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
