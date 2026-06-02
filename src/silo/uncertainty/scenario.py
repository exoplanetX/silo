from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite

DEFAULT_PROBABILITY_TOLERANCE = 1e-9

MetadataValue = str | int | float | bool | None
MetadataItems = tuple[tuple[str, MetadataValue], ...]
NumericItems = tuple[tuple[str, float], ...]
NestedNumericItems = tuple[tuple[str, NumericItems], ...]


@dataclass(frozen=True)
class Scenario:
    """Finite-scenario data record; it stores data only and never solves a model."""

    name: str
    probability: float = 1.0
    objective_coefficients: Mapping[str, float] = field(default_factory=dict)
    rhs_values: Mapping[str, float] = field(default_factory=dict)
    constraint_coefficients: Mapping[str, Mapping[str, float]] = field(default_factory=dict)
    parameters: Mapping[str, float] = field(default_factory=dict)
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", _normalize_label(self.name, "scenario id"))
        object.__setattr__(
            self,
            "probability",
            _normalize_nonnegative_float(self.probability, "scenario probability"),
        )
        object.__setattr__(
            self,
            "objective_coefficients",
            _normalize_numeric_mapping(
                self.objective_coefficients,
                "objective coefficient overrides",
            ),
        )
        object.__setattr__(
            self,
            "rhs_values",
            _normalize_numeric_mapping(self.rhs_values, "RHS overrides"),
        )
        object.__setattr__(
            self,
            "constraint_coefficients",
            _normalize_nested_numeric_mapping(self.constraint_coefficients),
        )
        object.__setattr__(
            self,
            "parameters",
            _normalize_numeric_mapping(self.parameters, "scenario parameters"),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")

    @property
    def scenario_id(self) -> str:
        return self.name


@dataclass(frozen=True)
class ScenarioSet:
    """Finite scenario collection with strict probability and id validation."""

    scenarios: Sequence[Scenario]
    probability_tolerance: float = DEFAULT_PROBABILITY_TOLERANCE

    def __post_init__(self) -> None:
        tolerance = _normalize_positive_float(
            self.probability_tolerance,
            "probability tolerance",
        )
        object.__setattr__(self, "probability_tolerance", tolerance)

        normalized = _normalize_scenarios(self.scenarios)
        _validate_unique_scenario_ids(normalized)
        _validate_probability_total(normalized, tolerance)
        object.__setattr__(self, "scenarios", tuple(sorted(normalized, key=lambda s: s.name)))

    @property
    def scenario_ids(self) -> tuple[str, ...]:
        return tuple(scenario.name for scenario in self.scenarios)

    @property
    def probability_total(self) -> float:
        return sum(scenario.probability for scenario in self.scenarios)


def _normalize_scenarios(values: Sequence[Scenario]) -> tuple[Scenario, ...]:
    if isinstance(values, Scenario):
        raise TypeError("scenarios must be a sequence of Scenario records.")
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("scenarios must be a sequence of Scenario records.")

    normalized: list[Scenario] = []
    for scenario in values:
        if not isinstance(scenario, Scenario):
            raise TypeError("scenarios must contain Scenario records.")
        normalized.append(scenario)
    if not normalized:
        raise ValueError("scenarios must include at least one Scenario record.")
    return tuple(normalized)


def _validate_unique_scenario_ids(scenarios: Sequence[Scenario]) -> None:
    seen: set[str] = set()
    for scenario in scenarios:
        if scenario.name in seen:
            raise ValueError("scenario ids must be unique.")
        seen.add(scenario.name)


def _validate_probability_total(
    scenarios: Sequence[Scenario],
    probability_tolerance: float,
) -> None:
    total = sum(scenario.probability for scenario in scenarios)
    if total <= 0.0:
        raise ValueError("scenario probability total must be positive.")
    if abs(total - 1.0) > probability_tolerance:
        raise ValueError("scenario probabilities must sum to one within tolerance.")


def _normalize_label(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _normalize_numeric_mapping(values: Mapping[str, float], label: str) -> NumericItems:
    if not isinstance(values, Mapping):
        raise TypeError(f"{label} must be a mapping.")
    normalized: list[tuple[str, float]] = []
    for key, value in values.items():
        normalized.append(
            (
                _normalize_label(key, f"{label} key"),
                _normalize_finite_float(value, f"{label} value"),
            )
        )
    return tuple(sorted(normalized))


def _normalize_nested_numeric_mapping(
    values: Mapping[str, Mapping[str, float]],
) -> NestedNumericItems:
    if not isinstance(values, Mapping):
        raise TypeError("constraint coefficient overrides must be a mapping.")
    normalized: list[tuple[str, NumericItems]] = []
    for constraint_name, coefficients in values.items():
        normalized.append(
            (
                _normalize_label(constraint_name, "constraint override key"),
                _normalize_numeric_mapping(coefficients, "constraint coefficient overrides"),
            )
        )
    return tuple(sorted(normalized))


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


def _normalize_nonnegative_float(value: float, label: str) -> float:
    numeric = _normalize_finite_float(value, label)
    if numeric < 0.0:
        raise ValueError(f"{label} must be nonnegative.")
    return numeric


def _normalize_positive_float(value: float, label: str) -> float:
    numeric = _normalize_finite_float(value, label)
    if numeric <= 0.0:
        raise ValueError(f"{label} must be positive.")
    return numeric


def _normalize_finite_float(value: float, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be numeric.")
    numeric = float(value)
    if not isfinite(numeric):
        raise ValueError(f"{label} must be finite.")
    return numeric
