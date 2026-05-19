from dataclasses import dataclass


@dataclass(frozen=True)
class BranchingDecision:
    variable_name: str
    value: float
