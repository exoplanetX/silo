from dataclasses import dataclass, field


@dataclass(frozen=True)
class LinearExpression:
    coefficients: dict[str, float] = field(default_factory=dict)
    constant: float = 0.0

    def coefficient(self, variable_name: str) -> float:
        return self.coefficients.get(variable_name, 0.0)
