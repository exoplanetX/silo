from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite

from silo.core.model import Model
from silo.uncertainty.naming import (
    NONANTICIPATIVITY_PREFIX,
    SCENARIO_COMPONENT_DELIMITER,
)
from silo.uncertainty.scenario import (
    DEFAULT_PROBABILITY_TOLERANCE,
    MetadataItems,
    MetadataValue,
)
from silo.uncertainty.stochastic_model import StochasticModel

EXPECTED_VALUE_OBJECTIVE = "expected_value"
DEFAULT_DETERMINISTIC_EQUIVALENT_NAMING = (
    f"scenario_component={SCENARIO_COMPONENT_DELIMITER};"
    f"nonanticipativity={NONANTICIPATIVITY_PREFIX}"
    "{base_variable}::{scenario_id}"
)


@dataclass(frozen=True)
class DeterministicEquivalentDiagnostics:
    """Passive deterministic-equivalent diagnostics; it records dimensions only."""

    scenario_ids: Sequence[str]
    generated_variables: int = 0
    generated_constraints: int = 0
    nonanticipativity_constraints: int = 0
    objective_aggregation: str = EXPECTED_VALUE_OBJECTIVE
    probability_total: float = 1.0
    probability_tolerance: float = DEFAULT_PROBABILITY_TOLERANCE
    naming_convention: str = DEFAULT_DETERMINISTIC_EQUIVALENT_NAMING
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "scenario_ids", _normalize_scenario_ids(self.scenario_ids))
        object.__setattr__(
            self,
            "generated_variables",
            _normalize_nonnegative_count(
                self.generated_variables,
                "generated variable count",
            ),
        )
        object.__setattr__(
            self,
            "generated_constraints",
            _normalize_nonnegative_count(
                self.generated_constraints,
                "generated constraint count",
            ),
        )
        object.__setattr__(
            self,
            "nonanticipativity_constraints",
            _normalize_nonnegative_count(
                self.nonanticipativity_constraints,
                "nonanticipativity constraint count",
            ),
        )
        object.__setattr__(
            self,
            "objective_aggregation",
            _normalize_nonempty_text(
                self.objective_aggregation,
                "objective aggregation convention",
            ),
        )
        object.__setattr__(
            self,
            "probability_total",
            _normalize_positive_float(self.probability_total, "probability total"),
        )
        object.__setattr__(
            self,
            "probability_tolerance",
            _normalize_positive_float(
                self.probability_tolerance,
                "probability tolerance",
            ),
        )
        object.__setattr__(
            self,
            "naming_convention",
            _normalize_nonempty_text(self.naming_convention, "naming convention"),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")

    @property
    def scenario_count(self) -> int:
        return len(self.scenario_ids)


@dataclass(frozen=True)
class DeterministicEquivalentResult:
    """Passive deterministic-equivalent result record."""

    model: Model
    diagnostics: DeterministicEquivalentDiagnostics
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)
    message: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.model, Model):
            raise TypeError("model must be a Model.")
        self.model.validate()
        if not isinstance(self.diagnostics, DeterministicEquivalentDiagnostics):
            raise TypeError("diagnostics must be DeterministicEquivalentDiagnostics.")
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")


def build_deterministic_equivalent(model: StochasticModel) -> Model:
    return model.base_model


def _normalize_scenario_ids(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("scenario ids must be a sequence of strings.")

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        scenario_id = _normalize_nonempty_text(value, "scenario id")
        if scenario_id in seen:
            raise ValueError("scenario ids must be unique.")
        seen.add(scenario_id)
        normalized.append(scenario_id)
    if not normalized:
        raise ValueError("scenario ids must include at least one id.")
    return tuple(sorted(normalized))


def _normalize_nonnegative_count(value: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer.")
    if value < 0:
        raise ValueError(f"{label} must be nonnegative.")
    return value


def _normalize_positive_float(value: float, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be numeric.")
    numeric = float(value)
    if not isfinite(numeric):
        raise ValueError(f"{label} must be finite.")
    if numeric <= 0.0:
        raise ValueError(f"{label} must be positive.")
    return numeric


def _normalize_nonempty_text(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _normalize_metadata(values: Mapping[str, MetadataValue]) -> MetadataItems:
    if not isinstance(values, Mapping):
        raise TypeError("metadata must be a mapping.")

    normalized: list[tuple[str, MetadataValue]] = []
    for key, value in values.items():
        label = _normalize_nonempty_text(key, "metadata key")
        if isinstance(value, float) and not isfinite(value):
            raise ValueError("metadata float values must be finite.")
        if not isinstance(value, (str, int, float, bool, type(None))):
            raise TypeError("metadata values must be scalar strings, numbers, bools, or None.")
        normalized.append((label, value))
    return tuple(sorted(normalized))
