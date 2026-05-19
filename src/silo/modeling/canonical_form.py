from dataclasses import dataclass

from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model


@dataclass(frozen=True)
class CanonicalForm:
    variable_names: tuple[str, ...]
    constraint_names: tuple[str, ...]
    objective_coefficients: tuple[float, ...]
    objective_constant: float
    constraint_matrix: tuple[tuple[float, ...], ...]
    rhs: tuple[float, ...]
    constraint_senses: tuple[ConstraintSense, ...]
    objective_sense: OptimizationSense
    variable_lower_bounds: tuple[float, ...]
    variable_upper_bounds: tuple[float, ...]
    variable_types: tuple[VariableType, ...]


def to_canonical_form(model: Model) -> CanonicalForm:
    """Convert the current core model into a deterministic dense solver-facing form."""

    model.validate()
    variable_names = tuple(model.variable_names())
    constraint_names = tuple(constraint.name for constraint in model.constraints)
    objective_coefficients = tuple(
        model.objective.coefficients.get(name, 0.0) for name in variable_names
    )
    # Later phases may replace row senses and RHS with row_lower <= A x <= row_upper.
    constraint_matrix = tuple(
        tuple(constraint.coefficients.get(name, 0.0) for name in variable_names)
        for constraint in model.constraints
    )
    rhs = tuple(constraint.rhs for constraint in model.constraints)
    constraint_senses = tuple(constraint.sense for constraint in model.constraints)
    variable_lower_bounds = tuple(variable.bounds.lower for variable in model.variables)
    variable_upper_bounds = tuple(variable.bounds.upper for variable in model.variables)
    variable_types = tuple(variable.var_type for variable in model.variables)
    return CanonicalForm(
        variable_names=variable_names,
        constraint_names=constraint_names,
        objective_coefficients=objective_coefficients,
        objective_constant=model.objective.constant,
        constraint_matrix=constraint_matrix,
        rhs=rhs,
        constraint_senses=constraint_senses,
        objective_sense=model.objective.sense,
        variable_lower_bounds=variable_lower_bounds,
        variable_upper_bounds=variable_upper_bounds,
        variable_types=variable_types,
    )
