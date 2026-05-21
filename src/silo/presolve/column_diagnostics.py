from dataclasses import dataclass
from math import isinf

from silo.core.enums import OptimizationSense
from silo.core.model import Model
from silo.presolve.diagnostics import PresolveWarning
from silo.utils.numerics import DEFAULT_TOLERANCE


@dataclass(frozen=True)
class EmptyColumnDiagnostics:
    warnings: tuple[PresolveWarning, ...]
    unbounded_variable: str | None = None


def inspect_empty_columns(
    model: Model,
    tolerance: float = DEFAULT_TOLERANCE,
) -> EmptyColumnDiagnostics:
    warnings: list[PresolveWarning] = []
    for variable in model.variables:
        if not _is_empty_column(model, variable.name, tolerance):
            continue

        objective_coefficient = model.objective.coefficients.get(variable.name, 0.0)
        if (
            model.objective.sense == OptimizationSense.MAXIMIZE
            and objective_coefficient > tolerance
            and isinf(variable.bounds.upper)
        ):
            warnings.append(
                PresolveWarning(
                    code="empty_column_unbounded",
                    message=(
                        "Empty column with positive objective coefficient and no finite "
                        "upper bound makes the model unbounded."
                    ),
                    source=variable.name,
                )
            )
            return EmptyColumnDiagnostics(
                warnings=tuple(warnings),
                unbounded_variable=variable.name,
            )

        warnings.append(
            PresolveWarning(
                code="empty_column",
                message="Variable does not appear in any constraint.",
                source=variable.name,
            )
        )

    return EmptyColumnDiagnostics(warnings=tuple(warnings))


def _is_empty_column(model: Model, variable_name: str, tolerance: float) -> bool:
    for constraint in model.constraints:
        coefficient = constraint.coefficients.get(variable_name, 0.0)
        if abs(coefficient) > tolerance:
            return False
    return True
