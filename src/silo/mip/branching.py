from math import ceil, floor

from silo.core.enums import ConstraintSense
from silo.mip.node import BranchingConstraint

DEFAULT_INTEGER_TOLERANCE = 1e-6


def is_integral_value(
    value: float,
    tolerance: float = DEFAULT_INTEGER_TOLERANCE,
) -> bool:
    return abs(value - round(value)) <= tolerance


def fractional_part(value: float) -> float:
    return abs(value - floor(value))


def choose_branching_variable(
    variable_names: tuple[str, ...],
    integer_variable_names: tuple[str, ...],
    values: dict[str, float],
    tolerance: float = DEFAULT_INTEGER_TOLERANCE,
) -> str | None:
    integer_variables = set(integer_variable_names)
    for variable_name in variable_names:
        if variable_name not in integer_variables:
            continue
        if variable_name not in values:
            raise ValueError(f"Missing relaxation value for integer variable: {variable_name}")
        if not is_integral_value(values[variable_name], tolerance=tolerance):
            return variable_name
    return None


def branch_on_value(
    variable_name: str,
    value: float,
) -> tuple[BranchingConstraint, BranchingConstraint]:
    return (
        BranchingConstraint(variable_name, ConstraintSense.LE, float(floor(value))),
        BranchingConstraint(variable_name, ConstraintSense.GE, float(ceil(value))),
    )
