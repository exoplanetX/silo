from dataclasses import dataclass

from silo.core.constraint import Constraint
from silo.core.model import Model
from silo.core.objective import Objective
from silo.presolve.reductions import ReductionRecord, ReductionType, reduction_data
from silo.utils.numerics import DEFAULT_TOLERANCE

FixedValue = tuple[str, float]


@dataclass(frozen=True)
class FixedVariableElimination:
    model: Model
    reductions: tuple[ReductionRecord, ...]
    fixed_values: tuple[FixedValue, ...]

    @property
    def fixed_variables(self) -> tuple[str, ...]:
        return tuple(name for name, _ in self.fixed_values)


def eliminate_fixed_variables(
    model: Model,
    tolerance: float = DEFAULT_TOLERANCE,
) -> FixedVariableElimination:
    fixed_values = tuple(
        (variable.name, _clean_zero(variable.bounds.lower, tolerance))
        for variable in model.variables
        if variable.bounds.is_fixed()
    )
    if not fixed_values:
        return FixedVariableElimination(
            model=model,
            reductions=(),
            fixed_values=(),
        )

    fixed_value_by_name = dict(fixed_values)
    reduced_model = Model(
        name=model.name,
        variables=[
            variable
            for variable in model.variables
            if variable.name not in fixed_value_by_name
        ],
        constraints=_substitute_constraints(
            model=model,
            fixed_value_by_name=fixed_value_by_name,
            tolerance=tolerance,
        ),
        objective=_substitute_objective(
            model=model,
            fixed_value_by_name=fixed_value_by_name,
            tolerance=tolerance,
        ),
    )

    return FixedVariableElimination(
        model=reduced_model,
        reductions=_fixed_variable_reductions(
            model=model,
            fixed_values=fixed_values,
            tolerance=tolerance,
        ),
        fixed_values=fixed_values,
    )


def _substitute_constraints(
    model: Model,
    fixed_value_by_name: dict[str, float],
    tolerance: float,
) -> list[Constraint]:
    constraints: list[Constraint] = []
    for constraint in model.constraints:
        fixed_activity = sum(
            constraint.coefficients.get(variable_name, 0.0) * fixed_value
            for variable_name, fixed_value in fixed_value_by_name.items()
        )
        coefficients = {
            variable_name: _clean_zero(coefficient, tolerance)
            for variable_name, coefficient in constraint.coefficients.items()
            if variable_name not in fixed_value_by_name and abs(coefficient) > tolerance
        }
        constraints.append(
            Constraint(
                name=constraint.name,
                coefficients=coefficients,
                sense=constraint.sense,
                rhs=_clean_zero(constraint.rhs - fixed_activity, tolerance),
            )
        )
    return constraints


def _substitute_objective(
    model: Model,
    fixed_value_by_name: dict[str, float],
    tolerance: float,
) -> Objective:
    fixed_contribution = sum(
        model.objective.coefficients.get(variable_name, 0.0) * fixed_value
        for variable_name, fixed_value in fixed_value_by_name.items()
    )
    coefficients = {
        variable_name: _clean_zero(coefficient, tolerance)
        for variable_name, coefficient in model.objective.coefficients.items()
        if variable_name not in fixed_value_by_name and abs(coefficient) > tolerance
    }
    return Objective(
        coefficients=coefficients,
        sense=model.objective.sense,
        constant=_clean_zero(model.objective.constant + fixed_contribution, tolerance),
    )


def _fixed_variable_reductions(
    model: Model,
    fixed_values: tuple[FixedValue, ...],
    tolerance: float,
) -> tuple[ReductionRecord, ...]:
    records: list[ReductionRecord] = []
    for variable_name, fixed_value in fixed_values:
        objective_coefficient = _clean_zero(
            model.objective.coefficients.get(variable_name, 0.0),
            tolerance,
        )
        objective_contribution = _clean_zero(
            objective_coefficient * fixed_value,
            tolerance,
        )
        records.append(
            ReductionRecord(
                reduction_type=ReductionType.FIXED_VARIABLE,
                target=variable_name,
                description="Eliminated fixed variable.",
                data=reduction_data(
                    objective_coefficient=objective_coefficient,
                    objective_contribution=objective_contribution,
                    value=fixed_value,
                ),
            )
        )
    return tuple(records)


def _clean_zero(value: float, tolerance: float) -> float:
    return 0.0 if abs(value) <= tolerance else value
