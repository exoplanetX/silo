from dataclasses import dataclass

from silo.core.model import Model
from silo.presolve.diagnostics import PresolveWarning


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


def scale_model(model: Model) -> Model:
    return model
