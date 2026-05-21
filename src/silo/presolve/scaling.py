from dataclasses import dataclass

from silo.core.model import Model
from silo.presolve.diagnostics import PresolveWarning
from silo.utils.numerics import DEFAULT_TOLERANCE

LARGE_COEFFICIENT_RATIO = 1e8
LARGE_RHS_MAGNITUDE = 1e8
LARGE_OBJECTIVE_MAGNITUDE = 1e8


@dataclass(frozen=True)
class ScalingDiagnostics:
    max_abs_coefficient: float = 0.0
    min_abs_nonzero_coefficient: float | None = None
    coefficient_ratio: float | None = None
    max_abs_rhs: float = 0.0
    max_abs_objective: float = 0.0
    warnings: tuple[PresolveWarning, ...] = ()


def empty_scaling_diagnostics() -> ScalingDiagnostics:
    return ScalingDiagnostics()


def analyze_scaling(
    model: Model,
    tolerance: float = DEFAULT_TOLERANCE,
) -> ScalingDiagnostics:
    coefficient_values: list[float] = []
    warnings: list[PresolveWarning] = []

    for constraint in model.constraints:
        for variable_name, coefficient in constraint.coefficients.items():
            abs_coefficient = abs(coefficient)
            if abs_coefficient > tolerance:
                coefficient_values.append(abs_coefficient)
            elif abs_coefficient > 0.0:
                warnings.append(
                    PresolveWarning(
                        code="near_zero_coefficient",
                        message="Coefficient is nonzero but within numerical tolerance.",
                        source=f"{constraint.name}:{variable_name}",
                    )
                )

    max_abs_coefficient = max(coefficient_values, default=0.0)
    min_abs_nonzero_coefficient = (
        min(coefficient_values) if coefficient_values else None
    )
    coefficient_ratio = (
        max_abs_coefficient / min_abs_nonzero_coefficient
        if min_abs_nonzero_coefficient is not None
        else None
    )
    max_abs_rhs = max((abs(constraint.rhs) for constraint in model.constraints), default=0.0)
    max_abs_objective = max(
        (abs(coefficient) for coefficient in model.objective.coefficients.values()),
        default=0.0,
    )

    for variable_name, coefficient in model.objective.coefficients.items():
        abs_coefficient = abs(coefficient)
        if 0.0 < abs_coefficient <= tolerance:
            warnings.append(
                PresolveWarning(
                    code="near_zero_objective",
                    message="Objective coefficient is nonzero but within numerical tolerance.",
                    source=f"objective:{variable_name}",
                )
            )

    if coefficient_ratio is not None and coefficient_ratio >= LARGE_COEFFICIENT_RATIO:
        warnings.append(
            PresolveWarning(
                code="large_coefficient_ratio",
                message="Constraint coefficient range is large.",
            )
        )
    if max_abs_rhs >= LARGE_RHS_MAGNITUDE:
        warnings.append(
            PresolveWarning(
                code="large_rhs",
                message="RHS magnitude is large.",
            )
        )
    if max_abs_objective >= LARGE_OBJECTIVE_MAGNITUDE:
        warnings.append(
            PresolveWarning(
                code="large_objective",
                message="Objective coefficient magnitude is large.",
            )
        )

    return ScalingDiagnostics(
        max_abs_coefficient=max_abs_coefficient,
        min_abs_nonzero_coefficient=min_abs_nonzero_coefficient,
        coefficient_ratio=coefficient_ratio,
        max_abs_rhs=max_abs_rhs,
        max_abs_objective=max_abs_objective,
        warnings=tuple(warnings),
    )


def scale_model(model: Model) -> Model:
    """Return the model unchanged; automatic scaling is intentionally deferred."""
    return model
