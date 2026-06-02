from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite

OBJECTIVE_TARGET = "objective"
RHS_TARGET = "rhs"
CONSTRAINT_COEFFICIENT_TARGET = "constraint_coefficient"
PARAMETER_TARGET = "parameter"
UNCERTAINTY_TARGETS = (
    OBJECTIVE_TARGET,
    RHS_TARGET,
    CONSTRAINT_COEFFICIENT_TARGET,
    PARAMETER_TARGET,
)

MetadataValue = str | int | float | bool | None
MetadataItems = tuple[tuple[str, MetadataValue], ...]


@dataclass(frozen=True)
class IntervalUncertainty:
    """Passive scalar interval uncertainty record."""

    name: str
    target: str
    lower: float
    upper: float
    nominal: float | None = None
    constraint_name: str = ""
    variable_name: str = ""
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)
    message: str = ""

    def __post_init__(self) -> None:
        lower = _normalize_finite_float(self.lower, "lower bound")
        upper = _normalize_finite_float(self.upper, "upper bound")
        if lower > upper:
            raise ValueError("lower bound must not exceed upper bound.")

        nominal = None
        if self.nominal is not None:
            nominal = _normalize_finite_float(self.nominal, "nominal value")
            if nominal < lower or nominal > upper:
                raise ValueError("nominal value must lie within interval bounds.")

        object.__setattr__(self, "name", _normalize_label(self.name, "interval name"))
        object.__setattr__(self, "target", _normalize_target(self.target))
        object.__setattr__(self, "lower", lower)
        object.__setattr__(self, "upper", upper)
        object.__setattr__(self, "nominal", nominal)
        object.__setattr__(
            self,
            "constraint_name",
            _normalize_optional_label(self.constraint_name, "constraint name"),
        )
        object.__setattr__(
            self,
            "variable_name",
            _normalize_optional_label(self.variable_name, "variable name"),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")

    @property
    def width(self) -> float:
        return self.upper - self.lower


@dataclass(frozen=True)
class UncertaintySet:
    """Independent box uncertainty set built from scalar intervals."""

    name: str
    intervals: Sequence[IntervalUncertainty]
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _normalize_label(self.name, "uncertainty set name"))
        object.__setattr__(self, "intervals", _normalize_intervals(self.intervals))
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")

    @property
    def dimension(self) -> int:
        return len(self.intervals)

    @property
    def interval_names(self) -> tuple[str, ...]:
        return tuple(interval.name for interval in self.intervals)


def _normalize_intervals(values: Sequence[IntervalUncertainty]) -> tuple[IntervalUncertainty, ...]:
    if isinstance(values, IntervalUncertainty):
        raise TypeError("intervals must be a sequence of IntervalUncertainty records.")
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("intervals must be a sequence of IntervalUncertainty records.")

    normalized: list[IntervalUncertainty] = []
    seen: set[str] = set()
    for interval in values:
        if not isinstance(interval, IntervalUncertainty):
            raise TypeError("intervals must contain IntervalUncertainty records.")
        if interval.name in seen:
            raise ValueError("interval names must be unique.")
        seen.add(interval.name)
        normalized.append(interval)
    if not normalized:
        raise ValueError("intervals must include at least one interval.")
    return tuple(sorted(normalized, key=lambda interval: interval.name))


def _normalize_target(value: str) -> str:
    target = _normalize_label(value, "target")
    if target not in UNCERTAINTY_TARGETS:
        allowed = ", ".join(UNCERTAINTY_TARGETS)
        raise ValueError(f"target must be one of: {allowed}.")
    return target


def _normalize_optional_label(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    return value.strip()


def _normalize_label(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _normalize_finite_float(value: float, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be numeric.")
    numeric = float(value)
    if not isfinite(numeric):
        raise ValueError(f"{label} must be finite.")
    return numeric


def _normalize_metadata(values: Mapping[str, MetadataValue]) -> MetadataItems:
    if not isinstance(values, Mapping):
        raise TypeError("metadata must be a mapping.")

    normalized: list[tuple[str, MetadataValue]] = []
    for key, value in values.items():
        label = _normalize_label(key, "metadata key")
        if isinstance(value, float) and not isfinite(value):
            raise ValueError("metadata float values must be finite.")
        if not isinstance(value, (str, int, float, bool, type(None))):
            raise TypeError("metadata values must be scalar strings, numbers, bools, or None.")
        normalized.append((label, value))
    return tuple(sorted(normalized))
