from dataclasses import dataclass
from math import isinf

from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.lp.base import LPSolver
from silo.lp.simplex.pricing import choose_entering_column
from silo.lp.simplex.ratio_test import choose_leaving_row
from silo.utils.numerics import DEFAULT_TOLERANCE


@dataclass(frozen=True)
class NormalizedRow:
    name: str
    coefficients: tuple[float, ...]
    sense: ConstraintSense
    rhs: float


@dataclass(frozen=True)
class TableauBuildResult:
    tableau: "SimplexTableau"
    artificial_columns: tuple[int, ...]


@dataclass
class SimplexTableau:
    variable_names: tuple[str, ...]
    original_variable_count: int
    rows: list[list[float]]
    objective_row: list[float]
    basis: list[int]

    @classmethod
    def from_model(cls, model: Model) -> "SimplexTableau":
        build_result = _build_initial_tableau(model)
        tableau = build_result.tableau
        if not build_result.artificial_columns:
            _restore_phase_two_objective(tableau, model)
        return tableau

    def pivot(self, row_index: int, column_index: int) -> None:
        pivot_element = self.rows[row_index][column_index]
        normalized_pivot_row = [value / pivot_element for value in self.rows[row_index]]
        self.rows[row_index] = normalized_pivot_row

        for candidate_index, row in enumerate(self.rows):
            if candidate_index == row_index:
                continue
            row_multiplier = row[column_index]
            if abs(row_multiplier) <= DEFAULT_TOLERANCE:
                continue
            self.rows[candidate_index] = [
                value - row_multiplier * pivot_row_value
                for value, pivot_row_value in zip(row, normalized_pivot_row, strict=True)
            ]

        objective_multiplier = self.objective_row[column_index]
        self.objective_row = [
            value - objective_multiplier * pivot_row_value
            for value, pivot_row_value in zip(
                self.objective_row,
                normalized_pivot_row,
                strict=True,
            )
        ]
        self.basis[row_index] = column_index

    def primal_values(self) -> dict[str, float]:
        values = {name: 0.0 for name in self.variable_names[: self.original_variable_count]}
        for row_index, basic_column in enumerate(self.basis):
            if basic_column < self.original_variable_count:
                values[self.variable_names[basic_column]] = _clean_zero(self.rows[row_index][-1])
        return values

    def objective_value(self) -> float:
        return _clean_zero(self.objective_row[-1])


@dataclass(frozen=True)
class SimplexRunResult:
    status: SolverStatus
    message: str = ""


class TableauSimplexSolver(LPSolver):
    def __init__(self, iteration_limit: int = 10_000) -> None:
        self.iteration_limit = iteration_limit

    def solve(self, model: Model) -> Solution:
        try:
            build_result = _build_initial_tableau(model)
        except ValueError as exc:
            return Solution(status=SolverStatus.ERROR, message=str(exc))

        tableau = build_result.tableau
        if build_result.artificial_columns:
            phase_one_result = _run_simplex_iterations(
                tableau=tableau,
                iteration_limit=self.iteration_limit,
                phase_name="Phase I",
            )
            if phase_one_result.status != SolverStatus.OPTIMAL:
                return Solution(status=phase_one_result.status, message=phase_one_result.message)
            if abs(tableau.objective_value()) > DEFAULT_TOLERANCE:
                return Solution(
                    status=SolverStatus.INFEASIBLE,
                    message="Phase I detected infeasibility.",
                )
            _remove_artificial_columns(tableau, build_result.artificial_columns)

        _restore_phase_two_objective(tableau, model)
        phase_two_result = _run_simplex_iterations(
            tableau=tableau,
            iteration_limit=self.iteration_limit,
            phase_name="Phase II",
        )
        if phase_two_result.status == SolverStatus.OPTIMAL:
            return Solution(
                status=SolverStatus.OPTIMAL,
                objective_value=tableau.objective_value(),
                primal_values=tableau.primal_values(),
                message="Tableau simplex solved the LP.",
            )
        return Solution(status=phase_two_result.status, message=phase_two_result.message)


def _validate_supported_lp(model: Model) -> None:
    model.validate()
    if model.objective.sense != OptimizationSense.MAXIMIZE:
        raise ValueError("Tableau simplex supports only maximization models.")

    for variable in model.variables:
        if variable.var_type != VariableType.CONTINUOUS:
            raise ValueError("Tableau simplex supports only continuous variables.")
        if abs(variable.bounds.lower) > DEFAULT_TOLERANCE:
            raise ValueError("Tableau simplex supports only variables with lower bound 0.")
        if not isinf(variable.bounds.upper) or variable.bounds.upper < 0:
            raise ValueError("Tableau simplex does not support finite variable upper bounds.")


def _build_initial_tableau(model: Model) -> TableauBuildResult:
    _validate_supported_lp(model)
    original_names = tuple(model.variable_names())
    original_count = len(original_names)
    normalized_rows = _normalize_rows(model, original_names)
    variable_names = list(original_names)
    rows: list[list[float]] = []
    basis: list[int] = []
    artificial_columns: list[int] = []

    for normalized_row in normalized_rows:
        row = list(normalized_row.coefficients)
        row.extend(0.0 for _ in range(len(variable_names) - original_count))

        if normalized_row.sense == ConstraintSense.LE:
            slack_column = _append_structural_column(
                variable_names=variable_names,
                rows=rows,
                name=f"slack_{normalized_row.name}",
            )
            row.append(1.0)
            basis.append(slack_column)
        elif normalized_row.sense == ConstraintSense.GE:
            _append_structural_column(
                variable_names=variable_names,
                rows=rows,
                name=f"surplus_{normalized_row.name}",
            )
            row.append(-1.0)
            artificial_column = _append_structural_column(
                variable_names=variable_names,
                rows=rows,
                name=f"artificial_{normalized_row.name}",
            )
            row.append(1.0)
            artificial_columns.append(artificial_column)
            basis.append(artificial_column)
        else:
            artificial_column = _append_structural_column(
                variable_names=variable_names,
                rows=rows,
                name=f"artificial_{normalized_row.name}",
            )
            row.append(1.0)
            artificial_columns.append(artificial_column)
            basis.append(artificial_column)

        row.append(normalized_row.rhs)
        rows.append(row)

    objective_row = _phase_one_objective_row(len(variable_names), artificial_columns)
    tableau = SimplexTableau(
        variable_names=tuple(variable_names),
        original_variable_count=original_count,
        rows=rows,
        objective_row=objective_row,
        basis=basis,
    )
    _canonicalize_objective_row(tableau)
    return TableauBuildResult(
        tableau=tableau,
        artificial_columns=tuple(artificial_columns),
    )


def _normalize_rows(model: Model, original_names: tuple[str, ...]) -> list[NormalizedRow]:
    normalized_rows: list[NormalizedRow] = []
    for constraint in model.constraints:
        coefficients = [constraint.coefficients.get(name, 0.0) for name in original_names]
        sense = constraint.sense
        rhs = constraint.rhs

        if rhs < -DEFAULT_TOLERANCE:
            coefficients = [-coefficient for coefficient in coefficients]
            rhs = -rhs
            sense = _flip_inequality_sense(sense)
        elif abs(rhs) <= DEFAULT_TOLERANCE:
            rhs = 0.0

        normalized_rows.append(
            NormalizedRow(
                name=constraint.name,
                coefficients=tuple(_clean_zero(coefficient) for coefficient in coefficients),
                sense=sense,
                rhs=_clean_zero(rhs),
            )
        )
    return normalized_rows


def _flip_inequality_sense(sense: ConstraintSense) -> ConstraintSense:
    if sense == ConstraintSense.LE:
        return ConstraintSense.GE
    if sense == ConstraintSense.GE:
        return ConstraintSense.LE
    return ConstraintSense.EQ


def _append_structural_column(
    variable_names: list[str],
    rows: list[list[float]],
    name: str,
) -> int:
    column_index = len(variable_names)
    variable_names.append(name)
    for row in rows:
        row.insert(-1, 0.0)
    return column_index


def _phase_one_objective_row(
    variable_count: int,
    artificial_columns: list[int],
) -> list[float]:
    objective_row = [0.0 for _ in range(variable_count)]
    for column_index in artificial_columns:
        # The tableau maximizes -sum(artificial variables), so the row stores
        # -c_j = 1 for each artificial variable before canonicalization.
        objective_row[column_index] = 1.0
    objective_row.append(0.0)
    return objective_row


def _restore_phase_two_objective(tableau: SimplexTableau, model: Model) -> None:
    objective_row = [
        -model.objective.coefficients.get(variable_name, 0.0)
        if column_index < tableau.original_variable_count
        else 0.0
        for column_index, variable_name in enumerate(tableau.variable_names)
    ]
    objective_row.append(model.objective.constant)
    tableau.objective_row = objective_row
    _canonicalize_objective_row(tableau)


def _canonicalize_objective_row(tableau: SimplexTableau) -> None:
    for row_index, basic_column in enumerate(tableau.basis):
        objective_multiplier = tableau.objective_row[basic_column]
        if abs(objective_multiplier) <= DEFAULT_TOLERANCE:
            continue
        tableau.objective_row = [
            value - objective_multiplier * row_value
            for value, row_value in zip(
                tableau.objective_row,
                tableau.rows[row_index],
                strict=True,
            )
        ]


def _remove_artificial_columns(
    tableau: SimplexTableau,
    artificial_columns: tuple[int, ...],
) -> None:
    artificial_column_set = set(artificial_columns)
    row_index = 0
    while row_index < len(tableau.rows):
        if tableau.basis[row_index] not in artificial_column_set:
            row_index += 1
            continue

        pivot_column = _find_non_artificial_pivot_column(
            row=tableau.rows[row_index],
            basis=tableau.basis,
            artificial_columns=artificial_column_set,
        )
        if pivot_column is None:
            del tableau.rows[row_index]
            del tableau.basis[row_index]
            continue

        tableau.pivot(row_index, pivot_column)
        row_index += 1

    kept_columns = [
        column_index
        for column_index in range(len(tableau.variable_names))
        if column_index not in artificial_column_set
    ]
    column_map = {
        old_column_index: new_column_index
        for new_column_index, old_column_index in enumerate(kept_columns)
    }
    tableau.variable_names = tuple(tableau.variable_names[index] for index in kept_columns)
    tableau.rows = [
        [row[index] for index in kept_columns] + [row[-1]]
        for row in tableau.rows
    ]
    tableau.basis = [column_map[basic_column] for basic_column in tableau.basis]
    tableau.objective_row = [
        tableau.objective_row[index] for index in kept_columns
    ] + [tableau.objective_row[-1]]


def _find_non_artificial_pivot_column(
    row: list[float],
    basis: list[int],
    artificial_columns: set[int],
) -> int | None:
    basic_columns = set(basis)
    for column_index, coefficient in enumerate(row[:-1]):
        if column_index in artificial_columns or column_index in basic_columns:
            continue
        if abs(coefficient) > DEFAULT_TOLERANCE:
            return column_index
    return None


def _run_simplex_iterations(
    tableau: SimplexTableau,
    iteration_limit: int,
    phase_name: str,
) -> SimplexRunResult:
    for _ in range(iteration_limit):
        entering_column = choose_entering_column(tableau.objective_row)
        if entering_column is None:
            return SimplexRunResult(status=SolverStatus.OPTIMAL)

        leaving_row = choose_leaving_row(tableau.rows, entering_column)
        if leaving_row is None:
            return SimplexRunResult(
                status=SolverStatus.UNBOUNDED,
                message=(
                    f"{phase_name} detected an unbounded improving direction with no "
                    "positive pivot row."
                ),
            )

        tableau.pivot(leaving_row, entering_column)

    return SimplexRunResult(
        status=SolverStatus.ITERATION_LIMIT,
        message=f"{phase_name} reached the iteration limit: {iteration_limit}",
    )


def _clean_zero(value: float) -> float:
    return 0.0 if abs(value) <= DEFAULT_TOLERANCE else value
