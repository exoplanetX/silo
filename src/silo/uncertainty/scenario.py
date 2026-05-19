from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    name: str
    probability: float = 1.0
