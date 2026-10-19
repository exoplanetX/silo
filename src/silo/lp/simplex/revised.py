from copy import deepcopy
from dataclasses import dataclass, replace
from types import MappingProxyType

import numpy as np

from silo.core.enums import ConstraintSense
from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.lp.base import LPSolver
from silo.lp.optimality import check_lp_optimality
from silo.lp.simplex.basis import Basis
from silo.lp.simplex.basis_snapshot import (
    RevisedBasisSnapshot,
    capture_identity,
    make_snapshot,
    map_snapshot,
)
from silo.lp.simplex.standard_form import (
    COLUMN_ARTIFICIAL,
    COLUMN_ORIGINAL,
    StandardFormProblem,
    build_standard_form,
)
from silo.lp.unboundedness import check_lp_unboundedness
from silo.utils.numerics import DEFAULT_TOLERANCE


@dataclass(frozen=True)
class BasisState:
    primal_values: np.ndarray
    basic_values: np.ndarray
    reduced_costs: np.ndarray
    simplex_multipliers: np.ndarray


@dataclass(frozen=True)
class RevisedRunResult:
    status: SolverStatus
    basis: Basis
    state: BasisState | None = None
    message: str = ""
    iterations: int = 0
    entering_column: int | None = None


@dataclass(frozen=True)
class RevisedSimplexResult:
    solution: Solution
    problem: StandardFormProblem | None = None
    basis: Basis | None = None
    iterations: int = 0
    used_warm_start: bool = False


@dataclass(frozen=True)
class RevisedReoptimizationResult:
    details: RevisedSimplexResult
    snapshot: RevisedBasisSnapshot | None = None
    used_warm_start: bool = False
    warm_phase_two_attempted: bool = False
    warm_iterations: int = 0
    cold_solve_count: int = 0
    cold_iterations: int = 0
    fallback_reason: str = ""
    snapshot_unavailable_reason: str = ""


class RevisedSimplexSolver(LPSolver):
    def __init__(self, iteration_limit: int = 10_000) -> None:
        self.iteration_limit = iteration_limit

    def solve(self, model: Model) -> Solution:
        return self.solve_with_details(model).solution

    def reoptimize(
        self, model: Model, snapshot: RevisedBasisSnapshot | None = None,
    ) -> RevisedReoptimizationResult:
        """Opt in to append-only full-row basis reuse, with at most one cold fallback.

        Each warm/cold run inherits iteration_limit separately. No basis search
        or Phase I occurs on an accepted warm path. Ordinary solve stays cold.
        """
        reference = deepcopy(model)
        identity = None
        identity_reason = ""
        try:
            identity = capture_identity(reference)
        except (ValueError, TypeError, OverflowError) as exc:
            identity_reason = f"Invalid original identity: {exc}"
        attempted, warm_iterations, cold_count = False, 0, 0
        fallback = ""

        def finish(details, used_warm):
            new_snapshot, reason = None, identity_reason
            if details.solution.status == SolverStatus.OPTIMAL and identity is not None:
                try:
                    new_snapshot = make_snapshot(
                        reference, identity, details.problem, details.basis,
                    )
                except (ValueError, TypeError, OverflowError) as exc:
                    reason = str(exc)
            elif not reason:
                reason = f"Final status {details.solution.status.value}; no optimal snapshot."
            return RevisedReoptimizationResult(
                details=_freeze_reoptimization_details(details), snapshot=new_snapshot,
                used_warm_start=used_warm, warm_phase_two_attempted=attempted,
                warm_iterations=warm_iterations, cold_solve_count=cold_count,
                cold_iterations=details.iterations if cold_count else 0,
                fallback_reason=fallback, snapshot_unavailable_reason=reason,
            )

        if snapshot is not None:
            try:
                if identity is None:
                    raise ValueError(identity_reason)
                fresh = build_standard_form(deepcopy(reference))
                problem, basis = map_snapshot(reference, identity, fresh, snapshot)
            except (ValueError, TypeError, OverflowError) as exc:
                fallback = f"Snapshot rejected: {exc}"
            else:
                attempted = True
                try:
                    run = _run_primal_revised_simplex(
                        problem=problem, basis=basis,
                        objective_coefficients=np.asarray(problem.objective_coefficients,
                                                          dtype=float),
                        iteration_limit=self.iteration_limit, phase_name="Phase II",
                    )
                except np.linalg.LinAlgError as exc:
                    fallback = f"Warm basis solve failed: {exc}"
                else:
                    warm_iterations = run.iterations
                    if run.status == SolverStatus.OPTIMAL:
                        solution = (_optimal_solution(reference, problem, run.basis, run.state)
                                    if _valid_reoptimization_state(problem, run) else
                                    Solution(SolverStatus.NUMERICAL_ISSUE,
                                             message="Warm optimal state/basis is invalid."))
                    elif run.status == SolverStatus.UNBOUNDED:
                        solution = _unbounded_solution(reference, problem, run)
                    else:
                        solution = Solution(run.status, message=run.message)
                    solution = _checked_reoptimization_solution(reference, solution)
                    if solution.status == SolverStatus.OPTIMAL:
                        return finish(RevisedSimplexResult(solution, problem, run.basis,
                                                           run.iterations, True), True)
                    fallback = f"Warm {solution.status.value}: {solution.message}"
        cold_count = 1
        # The executable copy is never the independent original verification source.
        cold = self.solve_with_details(deepcopy(reference))
        cold = replace(cold, solution=_checked_reoptimization_solution(reference, cold.solution))
        return finish(cold, False)

    def solve_with_details(
        self,
        model: Model,
        basis: Basis | None = None,
    ) -> RevisedSimplexResult:
        try:
            problem = build_standard_form(model)
        except ValueError as exc:
            return RevisedSimplexResult(
                solution=Solution(status=SolverStatus.ERROR, message=str(exc))
            )

        used_warm_start = False
        initial_basis = problem.initial_basis
        if basis is not None:
            if problem.artificial_columns:
                return RevisedSimplexResult(
                    solution=Solution(
                        status=SolverStatus.ERROR,
                        message=(
                            "Warm-start basis is not supported for models requiring "
                            "artificial variables yet."
                        ),
                    ),
                    problem=problem,
                )
            warm_start_result = _validate_warm_start_basis(problem, basis)
            if isinstance(warm_start_result, Solution):
                return RevisedSimplexResult(solution=warm_start_result, problem=problem)
            initial_basis = basis
            used_warm_start = True

        iterations = 0
        basis = initial_basis
        if problem.artificial_columns:
            phase_one_objective = _phase_one_objective(problem)
            phase_one_result = _run_primal_revised_simplex(
                problem=problem,
                basis=basis,
                objective_coefficients=phase_one_objective,
                iteration_limit=self.iteration_limit,
                phase_name="Phase I",
            )
            iterations += phase_one_result.iterations
            if phase_one_result.status == SolverStatus.UNBOUNDED:
                return RevisedSimplexResult(
                    solution=Solution(
                        status=SolverStatus.NUMERICAL_ISSUE,
                        message=(
                            "Revised simplex Phase I became unbounded; "
                            "the artificial problem should be bounded."
                        ),
                    ),
                    problem=problem,
                    basis=phase_one_result.basis,
                    iterations=iterations,
                )
            if phase_one_result.status != SolverStatus.OPTIMAL:
                return RevisedSimplexResult(
                    solution=Solution(
                        status=phase_one_result.status,
                        message=phase_one_result.message,
                    ),
                    problem=problem,
                    basis=phase_one_result.basis,
                    iterations=iterations,
                )
            if phase_one_result.state is None:
                return RevisedSimplexResult(
                    solution=Solution(
                        status=SolverStatus.NUMERICAL_ISSUE,
                        message="Revised simplex Phase I did not return a basis state.",
                    ),
                    problem=problem,
                    basis=phase_one_result.basis,
                    iterations=iterations,
                )

            phase_one_value = _objective_value(
                primal_values=phase_one_result.state.primal_values,
                objective_coefficients=phase_one_objective,
                objective_constant=0.0,
            )
            if phase_one_value < -DEFAULT_TOLERANCE:
                return RevisedSimplexResult(
                    solution=Solution(
                        status=SolverStatus.INFEASIBLE,
                        message="Revised simplex Phase I detected infeasibility.",
                    ),
                    problem=problem,
                    basis=phase_one_result.basis,
                    iterations=iterations,
                )

            cleanup_result = _remove_artificial_columns(
                problem=problem,
                basis=phase_one_result.basis,
            )
            if isinstance(cleanup_result, Solution):
                return RevisedSimplexResult(
                    solution=cleanup_result,
                    problem=problem,
                    basis=phase_one_result.basis,
                    iterations=iterations,
                )
            problem, basis = cleanup_result

        phase_two_result = _run_primal_revised_simplex(
            problem=problem,
            basis=basis,
            objective_coefficients=np.asarray(problem.objective_coefficients, dtype=float),
            iteration_limit=self.iteration_limit,
            phase_name="Phase II",
        )
        iterations += phase_two_result.iterations
        if phase_two_result.status == SolverStatus.OPTIMAL:
            if phase_two_result.state is None:
                return RevisedSimplexResult(
                    solution=Solution(
                        status=SolverStatus.NUMERICAL_ISSUE,
                        message="Revised simplex Phase II did not return a basis state.",
                    ),
                    problem=problem,
                    basis=phase_two_result.basis,
                    iterations=iterations,
                    used_warm_start=used_warm_start,
                )
            return RevisedSimplexResult(
                solution=_optimal_solution(
                    model,
                    problem,
                    phase_two_result.basis,
                    phase_two_result.state,
                ),
                problem=problem,
                basis=phase_two_result.basis,
                iterations=iterations,
                used_warm_start=used_warm_start,
            )
        solution = (_unbounded_solution(model, problem, phase_two_result)
                    if phase_two_result.status == SolverStatus.UNBOUNDED else
                    Solution(status=phase_two_result.status, message=phase_two_result.message))
        return RevisedSimplexResult(
            solution=solution,
            problem=problem,
            basis=phase_two_result.basis,
            iterations=iterations,
            used_warm_start=used_warm_start,
        )


def _checked_reoptimization_solution(model: Model, solution: Solution) -> Solution:
    if solution.status != SolverStatus.OPTIMAL:
        return Solution(solution.status, message=solution.message)
    checked = check_lp_optimality(model, solution, tolerance=DEFAULT_TOLERANCE)
    if not checked.passed:
        return Solution(
            SolverStatus.NUMERICAL_ISSUE,
            message=f"Reoptimization original-model optimality failed: {checked.message}",
        )
    return solution


def _valid_reoptimization_state(problem: StandardFormProblem, run: RevisedRunResult) -> bool:
    if not isinstance(run.state, BasisState) or not isinstance(run.basis, Basis):
        return False
    try:
        if any(type(j) is not int for j in (*run.basis.basic_columns, *run.basis.nonbasic_columns)):
            return False
        run.basis.validate(column_count=len(problem.columns), row_count=len(problem.row_names))
        return all(np.asarray(values).shape == (size,) and np.all(np.isfinite(values))
                   for values, size in (
                       (run.state.primal_values, len(problem.columns)),
                       (run.state.reduced_costs, len(problem.columns)),
                       (run.state.basic_values, len(problem.row_names)),
                       (run.state.simplex_multipliers, len(problem.row_names)),
                   ))
    except (ValueError, TypeError):
        return False


def _freeze_reoptimization_details(details: RevisedSimplexResult) -> RevisedSimplexResult:
    solution = replace(details.solution, **{
        name: MappingProxyType(dict(getattr(details.solution, name))) for name in
        ('primal_values', 'slack_values', 'dual_values', 'reduced_costs', 'basis_status')
    })
    problem, basis = deepcopy(details.problem), deepcopy(details.basis)
    if isinstance(basis, Basis):
        basis = Basis(tuple(basis.basic_columns), tuple(basis.nonbasic_columns))
    if isinstance(problem, StandardFormProblem):
        try:
            initial = problem.initial_basis
            problem = replace(
                problem, columns=tuple(problem.columns), row_names=tuple(problem.row_names),
                matrix=tuple(tuple(row) for row in problem.matrix), rhs=tuple(problem.rhs),
                objective_coefficients=tuple(problem.objective_coefficients),
                artificial_columns=tuple(problem.artificial_columns),
                initial_basis=Basis(tuple(initial.basic_columns), tuple(initial.nonbasic_columns)),
            )
        except (TypeError, AttributeError):
            problem = None  # Bad metadata cannot invalidate independently valid math evidence.
    return replace(details, solution=solution, problem=problem, basis=basis)


def _unbounded_solution(
    model: Model, problem: StandardFormProblem, result: RevisedRunResult,
) -> Solution:
    """Re-solve only at a terminal candidate to retain uncleaned basis values."""
    def failure(reason: str) -> Solution:
        return Solution(status=SolverStatus.NUMERICAL_ISSUE,
                        message=f"Phase II unbounded candidate rejected: {reason}")

    basis, entering = result.basis, result.entering_column
    count, rows = len(problem.columns), len(problem.row_names)
    if not isinstance(basis, Basis) or any(
        type(j) is not int for j in (*basis.basic_columns, *basis.nonbasic_columns)
    ):
        return failure("invalid basis coordinates.")
    try:
        basis.validate(column_count=count, row_count=rows)
    except ValueError as exc:
        return failure(f"invalid basis coordinates: {exc}")
    originals = [(j, c.original_name) for j, c in enumerate(problem.columns)
                 if c.role == COLUMN_ORIGINAL]
    if (type(entering) is not int or entering not in basis.nonbasic_columns
            or len(problem.matrix) != rows or len(problem.rhs) != rows
            or any(len(row) != count for row in problem.matrix)
            or len(originals) != problem.original_variable_count
            or len(originals) != len(model.variables)
            or {n for _, n in originals} != set(model.variable_names())
            or any(problem.columns[j].name != n for j, n in originals)):
        return failure("invalid original/basis/entering coordinates.")
    try:
        matrix = _matrix(problem)
        rhs = np.asarray(problem.rhs, dtype=float)
    except (ValueError, TypeError, OverflowError) as exc:
        return failure(f"nonnumeric basis coordinates: {exc}")
    try:
        basic_matrix = matrix[:, list(basis.basic_columns)]
        raw_point = np.linalg.solve(basic_matrix, rhs)
        raw_direction = np.linalg.solve(basic_matrix, matrix[:, entering])
    except np.linalg.LinAlgError as exc:
        return failure(f"point/direction basis solve failed: {exc}")
    # No _clean_zero: tiny negative coordinates and tiny nonzero slopes matter.
    point = np.zeros(count)
    direction = np.zeros(count)
    point[list(basis.basic_columns)] = raw_point
    direction[entering] = 1.0
    direction[list(basis.basic_columns)] = -raw_direction
    checked = check_lp_unboundedness(
        model, {n: float(point[j]) for j, n in originals},
        {n: float(direction[j]) for j, n in originals},
    )
    return Solution(
        status=SolverStatus.UNBOUNDED if checked.passed else SolverStatus.NUMERICAL_ISSUE,
        message=f"{result.message} {checked.message}" if checked.passed
        else f"Phase II unbounded candidate rejected: {checked.message}",
    )


def _run_primal_revised_simplex(
    problem: StandardFormProblem,
    basis: Basis,
    objective_coefficients: np.ndarray,
    iteration_limit: int,
    phase_name: str,
) -> RevisedRunResult:
    basis.validate(column_count=len(problem.columns), row_count=len(problem.row_names))
    iterations = 0
    for _ in range(iteration_limit):
        state_result = _compute_basis_state(problem, basis, objective_coefficients)
        if isinstance(state_result, Solution):
            return RevisedRunResult(
                status=state_result.status,
                basis=basis,
                message=state_result.message,
                iterations=iterations,
            )
        state = state_result

        entering_column = _choose_entering_column(problem, basis, state.reduced_costs)
        if entering_column is None:
            return RevisedRunResult(
                status=SolverStatus.OPTIMAL,
                basis=basis,
                state=state,
                iterations=iterations,
            )

        direction_result = _compute_direction(problem, basis, entering_column)
        if isinstance(direction_result, Solution):
            return RevisedRunResult(
                status=direction_result.status,
                basis=basis,
                message=direction_result.message,
                iterations=iterations,
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
                iterations=iterations,
                entering_column=entering_column,
            )

        basis = basis.pivot(leaving_row=leaving_row, entering_column=entering_column)
        iterations += 1
        basis.validate(
            column_count=len(problem.columns),
            row_count=len(problem.row_names),
        )

    return RevisedRunResult(
        status=SolverStatus.ITERATION_LIMIT,
        basis=basis,
        message=f"Revised simplex {phase_name} reached the iteration limit: {iteration_limit}",
        iterations=iterations,
    )


def _validate_warm_start_basis(
    problem: StandardFormProblem,
    basis: Basis,
) -> BasisState | Solution:
    try:
        basis.validate(column_count=len(problem.columns), row_count=len(problem.row_names))
    except ValueError as exc:
        return Solution(
            status=SolverStatus.ERROR,
            message=f"Invalid warm-start basis: {exc}",
        )

    state_result = _compute_basis_state(
        problem=problem,
        basis=basis,
        objective_coefficients=np.asarray(problem.objective_coefficients, dtype=float),
    )
    if isinstance(state_result, Solution):
        return Solution(
            status=SolverStatus.ERROR,
            message=f"Invalid warm-start basis: {state_result.message}",
        )

    if np.any(state_result.basic_values < -DEFAULT_TOLERANCE):
        return Solution(
            status=SolverStatus.ERROR,
            message="Warm-start basis is not primal feasible.",
        )

    return state_result


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
    source_rows = _artificial_source_rows(problem)
    if isinstance(source_rows, Solution):
        return source_rows
    try:
        basis.validate(column_count=len(problem.columns), row_count=len(problem.row_names))
    except ValueError as exc:
        return _cleanup_failure(f"invalid basis: {exc}")

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
    if not _finite_basis_state(state_result):
        return _cleanup_failure("nonfinite basis state")

    redundant_basis_slots: list[int] = []
    redundant_rows: list[int] = []
    for basis_slot, basic_column in enumerate(basis.basic_columns):
        if basic_column not in artificial_set:
            continue
        if abs(state_result.basic_values[basis_slot]) > DEFAULT_TOLERANCE:
            return _cleanup_failure("nonzero artificial basic value")
        redundant_basis_slots.append(basis_slot)
        redundant_rows.append(source_rows[basic_column])

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
    kept_basis_slots = [
        basis_slot
        for basis_slot in range(len(basis.basic_columns))
        if basis_slot not in redundant_basis_slots
    ]
    if redundant_basis_slots:
        failure = _check_cleanup_dependence(
            problem, basis, redundant_basis_slots, redundant_rows, kept_columns,
        )
        if failure is not None:
            return failure
    column_map = {
        old_column: new_column
        for new_column, old_column in enumerate(kept_columns)
    }

    new_basic_columns = tuple(
        column_map[basis.basic_columns[basis_slot]]
        for basis_slot in kept_basis_slots
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
    # Structural validation alone cannot establish numerical invertibility.
    retained_state = _compute_basis_state(
        new_problem, new_basis, np.asarray(new_problem.objective_coefficients, dtype=float),
    )
    if isinstance(retained_state, Solution):
        return retained_state
    if not _finite_basis_state(retained_state):
        return _cleanup_failure("nonfinite retained basis state")
    return new_problem, new_basis


def _cleanup_failure(reason: str) -> Solution:
    return Solution(
        status=SolverStatus.NUMERICAL_ISSUE,
        message=f"Revised simplex Phase-I cleanup: {reason}.",
    )


def _artificial_source_rows(problem: StandardFormProblem) -> dict[int, int] | Solution:
    artificial = problem.artificial_columns
    if len(set(artificial)) != len(artificial) or any(
        not isinstance(j, int) or j < 0 or j >= len(problem.columns) for j in artificial
    ):
        return _cleanup_failure("duplicate or invalid artificial column index")
    if set(artificial) != {
        j for j, column in enumerate(problem.columns) if column.role == COLUMN_ARTIFICIAL
    }:
        return _cleanup_failure("artificial column inventory disagrees with column roles")

    matrix = _matrix(problem)
    source_rows: dict[int, int] = {}
    for column_index in artificial:
        column = problem.columns[column_index]
        source = column.source_constraint
        if not source:
            return _cleanup_failure(f"missing source for artificial column {column.name!r}")
        matches = [i for i, name in enumerate(problem.row_names) if name == source]
        if not matches:
            return _cleanup_failure(f"artificial column source {source!r} not found")
        if len(matches) != 1 or matches[0] in source_rows.values():
            return _cleanup_failure(f"ambiguous artificial column source {source!r}")
        row_index = matches[0]
        unit_column = np.zeros(len(problem.row_names))
        unit_column[row_index] = 1.0
        if not np.allclose(matrix[:, column_index], unit_column,
                           rtol=0, atol=DEFAULT_TOLERANCE):
            return _cleanup_failure(
                f"artificial column {column.name!r} incompatible with source {source!r}",
            )
        source_rows[column_index] = row_index
    return source_rows


def _check_cleanup_dependence(
    problem: StandardFormProblem,
    basis: Basis,
    basis_slots: list[int],
    source_rows: list[int],
    non_artificial_columns: list[int],
) -> Solution | None:
    matrix = _matrix(problem)
    selector = np.eye(len(problem.row_names))[:, basis_slots]
    try:
        # Q = (B^-1)[I,:], obtained without explicitly forming the inverse.
        q = np.linalg.solve(matrix[:, list(basis.basic_columns)].T, selector).T
    except np.linalg.LinAlgError as exc:
        return _cleanup_failure(f"could not verify redundant-row dependence: {exc}")
    residuals = (
        q[:, source_rows] - np.eye(len(basis_slots)),
        q @ matrix[:, non_artificial_columns],
        q @ np.asarray(problem.rhs, dtype=float),
    )
    if any(not np.all(np.isfinite(r)) or np.any(np.abs(r) > DEFAULT_TOLERANCE)
           for r in residuals):
        return _cleanup_failure("could not verify redundant-row dependence")
    return None


def _finite_basis_state(state: BasisState) -> bool:
    return all(np.all(np.isfinite(values)) for values in (
        state.primal_values, state.basic_values, state.reduced_costs, state.simplex_multipliers,
    ))


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
        simplex_multipliers=simplex_multipliers,
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
    solution = Solution(
        status=SolverStatus.OPTIMAL,
        objective_value=_objective_value(
            primal_values=state.primal_values,
            objective_coefficients=np.asarray(problem.objective_coefficients, dtype=float),
            objective_constant=problem.objective_constant,
        ),
        primal_values=primal_values,
        slack_values=_constraint_slacks(model, primal_values),
        dual_values=_original_dual_values(model, problem, state),
        reduced_costs=_original_reduced_costs(problem, state.reduced_costs),
        basis_status=_original_basis_status(problem, basis),
        message="Revised simplex solved the LP.",
    )
    if len(problem.row_names) < len(model.constraints):
        # A locally tiny dependence residual can grow at the reduced optimum.
        # Certify the restored candidate against every original row before claiming optimality.
        checked = check_lp_optimality(model, solution, tolerance=DEFAULT_TOLERANCE)
        if not checked.passed:
            return _cleanup_failure(
                f"post-cleanup original-model optimality check failed: {checked.message}",
            )
    return solution


def _original_dual_values(
    model: Model, problem: StandardFormProblem, state: BasisState,
) -> dict[str, float]:
    # Cleanup retains a subset of ORIGINAL normalized rows. Removed redundant
    # equalities get zero multipliers; undo each surviving row's RHS sign flip.
    normalized = dict(zip(problem.row_names, state.simplex_multipliers, strict=True))
    return {
        # Preserve small multipliers: y_i*b_i can still be significant.
        row.name: float(normalized.get(row.name, 0.0)) * (
            -1.0 if row.rhs < -DEFAULT_TOLERANCE else 1.0
        )
        for row in model.constraints
    }


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
