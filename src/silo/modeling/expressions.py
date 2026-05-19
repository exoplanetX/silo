from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field


@dataclass(frozen=True)
class LinearExpression:
    coefficients: dict[str, float] = field(default_factory=dict)
    constant: float = 0.0

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "coefficients",
            _clean_coefficients(self.coefficients.items()),
        )

    @classmethod
    def from_terms(
        cls,
        terms: Iterable[tuple[str, float]],
        constant: float = 0.0,
    ) -> LinearExpression:
        return cls(dict(_aggregate_terms(terms)), constant=constant)

    def coefficient(self, variable_name: str) -> float:
        return self.coefficients.get(variable_name, 0.0)

    def to_dict(self) -> dict[str, float]:
        return dict(self.coefficients)

    def __add__(self, other: LinearExpression | float | int) -> LinearExpression:
        if isinstance(other, int | float):
            return LinearExpression(self.coefficients, self.constant + float(other))
        if not isinstance(other, LinearExpression):
            return NotImplemented
        return LinearExpression.from_terms(
            (*self.coefficients.items(), *other.coefficients.items()),
            constant=self.constant + other.constant,
        )

    def __radd__(self, other: float | int) -> LinearExpression:
        return self + other

    def __sub__(self, other: LinearExpression | float | int) -> LinearExpression:
        if isinstance(other, int | float):
            return LinearExpression(self.coefficients, self.constant - float(other))
        if not isinstance(other, LinearExpression):
            return NotImplemented
        return LinearExpression.from_terms(
            (
                *self.coefficients.items(),
                *((name, -value) for name, value in other.coefficients.items()),
            ),
            constant=self.constant - other.constant,
        )

    def __rsub__(self, other: float | int) -> LinearExpression:
        if isinstance(other, int | float):
            return (-self) + other
        return NotImplemented

    def __mul__(self, scalar: float | int) -> LinearExpression:
        if not isinstance(scalar, int | float):
            return NotImplemented
        return LinearExpression(
            {name: value * float(scalar) for name, value in self.coefficients.items()},
            constant=self.constant * float(scalar),
        )

    def __rmul__(self, scalar: float | int) -> LinearExpression:
        return self * scalar

    def __neg__(self) -> LinearExpression:
        return self * -1.0


def _aggregate_terms(terms: Iterable[tuple[str, float]]) -> dict[str, float]:
    coefficients: dict[str, float] = {}
    for name, value in terms:
        if not name:
            raise ValueError("Variable name in expression must not be empty.")
        coefficients[name] = coefficients.get(name, 0.0) + float(value)
    return coefficients


def _clean_coefficients(
    coefficients: Iterable[tuple[str, float]] | Mapping[str, float],
) -> dict[str, float]:
    items = coefficients.items() if isinstance(coefficients, Mapping) else coefficients
    aggregated = _aggregate_terms(items)
    return {name: value for name, value in sorted(aggregated.items()) if value != 0.0}
