from dataclasses import dataclass, field

from silo.core.enums import ConstraintSense


@dataclass(frozen=True)
class Constraint:
    name: str
    coefficients: dict[str, float] = field(default_factory=dict)
    sense: ConstraintSense = ConstraintSense.LE
    rhs: float = 0.0

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Constraint name must not be empty.")
