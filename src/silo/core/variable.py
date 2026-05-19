from dataclasses import dataclass, field

from silo.core.bounds import Bounds
from silo.core.enums import VariableType


@dataclass(frozen=True)
class Variable:
    name: str
    bounds: Bounds = field(default_factory=Bounds)
    var_type: VariableType = VariableType.CONTINUOUS

    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("Variable name must not be empty.")
        object.__setattr__(self, "var_type", VariableType(self.var_type))
        self.bounds.validate()
