from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from math import isfinite

from silo.core.enums import ConstraintSense

DEFAULT_BENDERS_CUT_TOLERANCE = 1e-9


class BendersCutType(str, Enum):
    FEASIBILITY = "feasibility"
    OPTIMALITY = "optimality"


@dataclass(frozen=True)
class BendersCutCandidate:
    cut_id: str
    cut_type: BendersCutType | str
    coefficients: Mapping[str, float]
    sense: ConstraintSense | str
    rhs: float
    source_subproblem: str
    iteration_id: int
    tolerance: float = DEFAULT_BENDERS_CUT_TOLERANCE
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "cut_id", _normalize_label(self.cut_id, "cut id"))
        object.__setattr__(self, "cut_type", _normalize_cut_type(self.cut_type))
        object.__setattr__(self, "coefficients", _normalize_coefficients(self.coefficients))
        object.__setattr__(self, "sense", _normalize_sense(self.sense))
        object.__setattr__(self, "rhs", _normalize_finite_float(self.rhs, "RHS"))
        object.__setattr__(
            self,
            "source_subproblem",
            _normalize_label(self.source_subproblem, "source subproblem"),
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

    def canonical_key(
        self,
        variable_order: Iterable[str] | None = None,
    ) -> tuple[str, str, tuple[tuple[str, float], ...], str, float]:
        return (
            "benders_cut",
            self.cut_type.value,
            self._ordered_coefficients(variable_order),
            self.sense.value,
            self.rhs,
        )

    def _ordered_coefficients(
        self,
        variable_order: Iterable[str] | None,
    ) -> tuple[tuple[str, float], ...]:
        coefficient_map = dict(self.coefficients)
        if variable_order is None:
            return tuple(sorted(coefficient_map.items()))

        seen: set[str] = set()
        ordered: list[tuple[str, float]] = []
        for variable_name in variable_order:
            if variable_name in coefficient_map and variable_name not in seen:
                ordered.append((variable_name, coefficient_map[variable_name]))
                seen.add(variable_name)

        for variable_name in sorted(coefficient_map):
            if variable_name not in seen:
                ordered.append((variable_name, coefficient_map[variable_name]))

        return tuple(ordered)


def _normalize_label(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _normalize_cut_type(value: BendersCutType | str) -> BendersCutType:
    if isinstance(value, BendersCutType):
        return value
    try:
        return BendersCutType(value)
    except ValueError as exc:
        raise ValueError("cut type must be a supported BendersCutType value.") from exc


def _normalize_sense(value: ConstraintSense | str) -> ConstraintSense:
    try:
        return ConstraintSense(value)
    except ValueError as exc:
        raise ValueError("sense must be a supported ConstraintSense value.") from exc


def _normalize_coefficients(coefficients: Mapping[str, float]) -> tuple[tuple[str, float], ...]:
    if not isinstance(coefficients, Mapping):
        raise TypeError("coefficients must be a mapping.")
    if not coefficients:
        raise ValueError("coefficients must not be empty.")

    normalized: list[tuple[str, float]] = []
    has_nonzero = False
    for variable_name, coefficient in coefficients.items():
        if not isinstance(variable_name, str) or not variable_name.strip():
            raise ValueError("variable names must be nonempty strings.")
        value = float(coefficient)
        if not isfinite(value):
            raise ValueError("coefficients must be finite.")
        if value != 0.0:
            has_nonzero = True
        normalized.append((variable_name, value))

    if not has_nonzero:
        raise ValueError("coefficient vector must contain a nonzero value.")

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
