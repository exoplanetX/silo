from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite

from silo.core.model import Model
from silo.uncertainty.scenario import MetadataItems, MetadataValue, Scenario, ScenarioSet

NameItems = tuple[str, ...]


@dataclass(frozen=True)
class StochasticModel:
    """Passive stochastic wrapper; it records uncertainty structure only."""

    base_model: Model
    scenarios: ScenarioSet | Sequence[Scenario]
    first_stage_variables: Sequence[str] = ()
    scenario_dependent_variables: Sequence[str] = ()
    scenario_dependent_constraints: Sequence[str] = ()
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)
    message: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.base_model, Model):
            raise TypeError("base_model must be a Model.")
        self.base_model.validate()

        scenarios = _normalize_scenario_set(self.scenarios)
        first_stage_variables = _normalize_name_sequence(
            self.first_stage_variables,
            "first-stage variables",
        )
        scenario_dependent_variables = _normalize_name_sequence(
            self.scenario_dependent_variables,
            "scenario-dependent variables",
        )
        scenario_dependent_constraints = _normalize_name_sequence(
            self.scenario_dependent_constraints,
            "scenario-dependent constraints",
        )

        base_variable_names = set(self.base_model.variable_names())
        base_constraint_names = {constraint.name for constraint in self.base_model.constraints}
        _validate_declared_names(
            first_stage_variables,
            base_variable_names,
            "first-stage variable",
        )
        _validate_declared_names(
            scenario_dependent_variables,
            base_variable_names,
            "scenario-dependent variable",
        )
        _validate_declared_names(
            scenario_dependent_constraints,
            base_constraint_names,
            "scenario-dependent constraint",
        )
        _validate_disjoint_variables(first_stage_variables, scenario_dependent_variables)

        object.__setattr__(self, "scenarios", scenarios)
        object.__setattr__(self, "first_stage_variables", first_stage_variables)
        object.__setattr__(self, "scenario_dependent_variables", scenario_dependent_variables)
        object.__setattr__(
            self,
            "scenario_dependent_constraints",
            scenario_dependent_constraints,
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")

    @property
    def scenario_ids(self) -> tuple[str, ...]:
        return self.scenarios.scenario_ids

    @property
    def variable_names(self) -> tuple[str, ...]:
        return tuple(self.base_model.variable_names())

    @property
    def constraint_names(self) -> tuple[str, ...]:
        return tuple(constraint.name for constraint in self.base_model.constraints)


def _normalize_scenario_set(value: ScenarioSet | Sequence[Scenario]) -> ScenarioSet:
    if isinstance(value, ScenarioSet):
        return value
    return ScenarioSet(value)


def _normalize_name_sequence(values: Sequence[str], label: str) -> NameItems:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError(f"{label} must be a sequence of names.")

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        name = _normalize_name(value, f"{label} entry")
        if name in seen:
            raise ValueError(f"{label} must not contain duplicate names.")
        seen.add(name)
        normalized.append(name)
    return tuple(sorted(normalized))


def _normalize_name(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _validate_declared_names(
    declared_names: Sequence[str],
    valid_names: set[str],
    label: str,
) -> None:
    for name in declared_names:
        if name not in valid_names:
            raise ValueError(f"Unknown {label}: {name}")


def _validate_disjoint_variables(
    first_stage_variables: Sequence[str],
    scenario_dependent_variables: Sequence[str],
) -> None:
    overlap = set(first_stage_variables).intersection(scenario_dependent_variables)
    if overlap:
        first_name = sorted(overlap)[0]
        raise ValueError(
            "First-stage and scenario-dependent variables must not overlap: "
            f"{first_name}"
        )


def _normalize_metadata(values: Mapping[str, MetadataValue]) -> MetadataItems:
    if not isinstance(values, Mapping):
        raise TypeError("metadata must be a mapping.")

    normalized: list[tuple[str, MetadataValue]] = []
    for key, value in values.items():
        label = _normalize_name(key, "metadata key")
        if isinstance(value, float) and not isfinite(value):
            raise ValueError("metadata float values must be finite.")
        if not isinstance(value, (str, int, float, bool, type(None))):
            raise TypeError("metadata values must be scalar strings, numbers, bools, or None.")
        normalized.append((label, value))
    return tuple(sorted(normalized))
