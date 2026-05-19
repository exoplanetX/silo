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


@dataclass
class SimplexTableau:
    variable_names: tuple[str, ...]
    original_variable_count: int
    rows: list[list[float]]
    objective_row: list[float]
    basis: list[int]

    @classmethod
    def from_model(cls, model: Model) -> "SimplexTableau":
        _validate_supported_standard_form(model)
        original_names = tuple(model.variable_names())
        slack_names = tuple(f"slack_{constraint.name}" for constraint in model.constraints)
        variable_names = original_names + slack_names
        original_count = len(original_names)
        rows: list[list[float]] = []
        basis: list[int] = []

        for row_index, constraint in enumerate(model.constraints):
            row = [constraint.coefficients.get(name, 0.0) for name in original_names]
            row.extend(
                1.0 if index == row_index else 0.0
                for index in range(len(model.constraints))
            )
            row.append(constraint.rhs)
            rows.append(row)
            basis.append(original_count + row_index)

        objective_row = [-model.objective.coefficients.get(name, 0.0) for name in original_names]
        objective_row.extend(0.0 for _ in model.constraints)
        objective_row.append(model.objective.constant)
        return cls(
            variable_names=variable_names,
            original_variable_count=original_count,
            rows=rows,
            objective_row=objective_row,
            basis=basis,
        )

    def pivot(self, row_index: int, column_index: int) -> None:
        pivot_value = self.rows[row_index][column_index]
        self.rows[row_index] = [value / pivot_value for value in self.rows[row_index]]
        pivot_row = self.rows[row_index]

        for candidate_index, row in enumerate(self.rows):
            if candidate_index == row_index:
                continue
            multiplier = row[column_index]
            if abs(multiplier) <= DEFAULT_TOLERANCE:
                continue
            self.rows[candidate_index] = [
                value - multiplier * pivot_value
                for value, pivot_value in zip(row, pivot_row, strict=True)
            ]

        multiplier = self.objective_row[column_index]
        self.objective_row = [
            value - multiplier * pivot_value
            for value, pivot_value in zip(self.objective_row, pivot_row, strict=True)
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


class TableauSimplexSolver(LPSolver):
    def __init__(self, iteration_limit: int = 10_000) -> None:
        self.iteration_limit = iteration_limit

    def solve(self, model: Model) -> Solution:
        try:
            tableau = SimplexTableau.from_model(model)
        except ValueError as exc:
            return Solution(status=SolverStatus.ERROR, message=str(exc))

        for _ in range(self.iteration_limit):
            entering_column = choose_entering_column(tableau.objective_row)
            if entering_column is None:
                return Solution(
                    status=SolverStatus.OPTIMAL,
                    objective_value=tableau.objective_value(),
                    primal_values=tableau.primal_values(),
                    message="Tableau simplex solved the LP relaxation.",
                )

            leaving_row = choose_leaving_row(tableau.rows, entering_column)
            if leaving_row is None:
                return Solution(
                    status=SolverStatus.UNBOUNDED,
                    message=(
                        "Tableau simplex detected an improving direction with no "
                        "positive pivot row."
                    ),
                )

            tableau.pivot(leaving_row, entering_column)

        return Solution(
            status=SolverStatus.ITERATION_LIMIT,
            message=f"Tableau simplex reached the iteration limit: {self.iteration_limit}",
        )


def _validate_supported_standard_form(model: Model) -> None:
    model.validate()
    if model.objective.sense != OptimizationSense.MAXIMIZE:
        raise ValueError("Tableau MVP supports only maximization models.")

    for variable in model.variables:
        if variable.var_type != VariableType.CONTINUOUS:
            raise ValueError("Tableau MVP supports only continuous variables.")
        if abs(variable.bounds.lower) > DEFAULT_TOLERANCE:
            raise ValueError("Tableau MVP supports only variables with lower bound 0.")
        if not isinf(variable.bounds.upper) or variable.bounds.upper < 0:
            raise ValueError("Tableau MVP does not support finite variable upper bounds.")

    for constraint in model.constraints:
        if constraint.sense != ConstraintSense.LE:
            raise ValueError("Tableau MVP supports only <= constraints.")
        if constraint.rhs < -DEFAULT_TOLERANCE:
            raise ValueError("Tableau MVP requires nonnegative RHS values.")


def _clean_zero(value: float) -> float:
    return 0.0 if abs(value) <= DEFAULT_TOLERANCE else value
