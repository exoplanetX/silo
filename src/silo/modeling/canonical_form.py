from dataclasses import dataclass

from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model


@dataclass(frozen=True)
class CanonicalForm:
    variable_names: tuple[str, ...]
    constraint_names: tuple[str, ...]
    objective_coefficients: tuple[float, ...]
    constraint_matrix: tuple[tuple[float, ...], ...]
    rhs: tuple[float, ...]
    constraint_senses: tuple[ConstraintSense, ...]
    objective_sense: OptimizationSense


def to_canonical_form(model: Model) -> CanonicalForm:
    """Convert the current core model into a deterministic dense placeholder form."""

    variable_names = tuple(model.variable_names())
    constraint_names = tuple(constraint.name for constraint in model.constraints)
    objective_coefficients = tuple(
        model.objective.coefficients.get(name, 0.0) for name in variable_names
    )
    constraint_matrix = tuple(
        tuple(constraint.coefficients.get(name, 0.0) for name in variable_names)
        for constraint in model.constraints
    )
    rhs = tuple(constraint.rhs for constraint in model.constraints)
    constraint_senses = tuple(constraint.sense for constraint in model.constraints)
    return CanonicalForm(
        variable_names=variable_names,
        constraint_names=constraint_names,
        objective_coefficients=objective_coefficients,
        constraint_matrix=constraint_matrix,
        rhs=rhs,
        constraint_senses=constraint_senses,
        objective_sense=model.objective.sense,
    )
