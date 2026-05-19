from silo.core.bounds import Bounds
from silo.core.model import Model
from silo.core.variable import Variable


class ModelBuilder:
    """Small fluent helper for examples and future expression-system work."""

    def __init__(self, name: str = "model") -> None:
        self.model = Model(name=name)

    def variable(self, name: str, lower: float = 0.0, upper: float = float("inf")) -> Variable:
        variable = Variable(name=name, bounds=Bounds(lower=lower, upper=upper))
        self.model.add_variable(variable)
        return variable

    def build(self) -> Model:
        return self.model
