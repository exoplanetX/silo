from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from math import isfinite

from silo.core.enums import OptimizationSense

DEFAULT_COLUMN_TOLERANCE = 1e-9


@dataclass(frozen=True)
class ColumnCandidate:
    column_id: str
    variable_name: str
    objective_coefficient: float
    row_coefficients: Mapping[str, float]
    reduced_cost: float
    source_pricing_subproblem: str
    iteration_id: int
    tolerance: float = DEFAULT_COLUMN_TOLERANCE
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "column_id", _normalize_label(self.column_id, "column id"))
        object.__setattr__(
            self,
            "variable_name",
            _normalize_label(self.variable_name, "variable name"),
        )
        object.__setattr__(
            self,
            "objective_coefficient",
            _normalize_finite_float(self.objective_coefficient, "objective coefficient"),
        )
        object.__setattr__(
            self,
            "row_coefficients",
            _normalize_row_coefficients(self.row_coefficients),
        )
        object.__setattr__(
            self,
            "reduced_cost",
            _normalize_finite_float(self.reduced_cost, "reduced cost"),
        )
        object.__setattr__(
            self,
            "source_pricing_subproblem",
            _normalize_label(
                self.source_pricing_subproblem,
                "source pricing subproblem",
            ),
        )
        object.__setattr__(
            self,
            "iteration_id",
            _normalize_iteration_id(self.iteration_id),
        )
        object.__setattr__(
            self,
            "tolerance",
            _normalize_positive_float(self.tolerance, "tolerance"),
        )
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")

    def is_improving_for(self, objective_sense: OptimizationSense | str) -> bool:
        sense = _normalize_objective_sense(objective_sense)
        if sense == OptimizationSense.MINIMIZE:
            return self.reduced_cost < -self.tolerance
        return self.reduced_cost > self.tolerance

    def canonical_key(
        self,
        row_order: Iterable[str] | None = None,
    ) -> tuple[str, str, float, tuple[tuple[str, float], ...]]:
        return (
            "column",
            self.variable_name,
            self.objective_coefficient,
            self._ordered_row_coefficients(row_order),
        )

    def _ordered_row_coefficients(
        self,
        row_order: Iterable[str] | None,
    ) -> tuple[tuple[str, float], ...]:
        coefficient_map = dict(self.row_coefficients)
        if row_order is None:
            return tuple(sorted(coefficient_map.items()))

        seen: set[str] = set()
        ordered: list[tuple[str, float]] = []
        for row_name in row_order:
            if row_name in coefficient_map and row_name not in seen:
                ordered.append((row_name, coefficient_map[row_name]))
                seen.add(row_name)

        for row_name in sorted(coefficient_map):
            if row_name not in seen:
                ordered.append((row_name, coefficient_map[row_name]))

        return tuple(ordered)


def _normalize_label(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _normalize_row_coefficients(
    coefficients: Mapping[str, float],
) -> tuple[tuple[str, float], ...]:
    if not isinstance(coefficients, Mapping):
        raise TypeError("row coefficients must be a mapping.")
    if not coefficients:
        raise ValueError("row coefficients must not be empty.")

    normalized: list[tuple[str, float]] = []
    has_nonzero = False
    for row_name, coefficient in coefficients.items():
        row_label = _normalize_label(row_name, "row name")
        value = _normalize_finite_float(coefficient, "row coefficient")
        if value != 0.0:
            has_nonzero = True
        normalized.append((row_label, value))

    if not has_nonzero:
        raise ValueError("row coefficient vector must contain a nonzero value.")

    return tuple(sorted(normalized))


def _normalize_finite_float(value: float, label: str) -> float:
    numeric = float(value)
    if not isfinite(numeric):
        raise ValueError(f"{label} must be finite.")
    return numeric


def _normalize_positive_float(value: float, label: str) -> float:
    numeric = _normalize_finite_float(value, label)
    if numeric <= 0.0:
        raise ValueError(f"{label} must be positive.")
    return numeric


def _normalize_iteration_id(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("iteration id must be an integer.")
    if value < 0:
        raise ValueError("iteration id must be nonnegative.")
    return value


def _normalize_objective_sense(value: OptimizationSense | str) -> OptimizationSense:
    try:
        return OptimizationSense(value)
    except ValueError as exc:
        raise ValueError("objective sense must be a supported OptimizationSense value.") from exc
