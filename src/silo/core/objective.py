from dataclasses import dataclass, field

from silo.core.enums import OptimizationSense


@dataclass(frozen=True)
class Objective:
    coefficients: dict[str, float] = field(default_factory=dict)
    sense: OptimizationSense = OptimizationSense.MINIMIZE
    constant: float = 0.0
