from dataclasses import dataclass
from math import inf


@dataclass(frozen=True)
class Bounds:
    lower: float = 0.0
    upper: float = inf

    def is_fixed(self) -> bool:
        return self.lower == self.upper

    def validate(self) -> None:
        if self.lower > self.upper:
            raise ValueError(f"Invalid bounds: lower={self.lower}, upper={self.upper}")
