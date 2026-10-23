from dataclasses import dataclass, field
from math import inf

from silo.core.enums import ConstraintSense


@dataclass(frozen=True)
class Constraint:
    name: str
    coefficients: dict[str, float] = field(default_factory=dict)
    sense: ConstraintSense = ConstraintSense.LE
    rhs: float = 0.0
    lower_bound: float | None = None
    upper_bound: float | None = None

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Constraint name must not be empty.")
        object.__setattr__(self, "sense", ConstraintSense(self.sense))

    @property
    def row_bounds(self) -> tuple[float, float]:
        """Original two-sided row bounds; legacy sense/rhs remains supported."""
        if self.lower_bound is not None or self.upper_bound is not None:
            return (
                self.lower_bound if self.lower_bound is not None else -inf,
                self.upper_bound if self.upper_bound is not None else inf,
            )
        if self.sense == ConstraintSense.LE:
            return -inf, self.rhs
        if self.sense == ConstraintSense.GE:
            return self.rhs, inf
        return self.rhs, self.rhs
