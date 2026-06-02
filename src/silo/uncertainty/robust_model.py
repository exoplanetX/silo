from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite

from silo.core.model import Model
from silo.uncertainty.uncertainty_set import (
    MetadataItems,
    MetadataValue,
    UncertaintySet,
)

AssumptionItems = tuple[str, ...]


@dataclass(frozen=True)
class RobustModel:
    """Passive robust wrapper; it records model/uncertainty-set structure only."""

    base_model: Model
    uncertainty_set: UncertaintySet
    assumptions: Sequence[str] = ()
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)
    message: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.base_model, Model):
            raise TypeError("base_model must be a Model.")
        self.base_model.validate()
        if not isinstance(self.uncertainty_set, UncertaintySet):
            raise TypeError("uncertainty_set must be an UncertaintySet.")

        object.__setattr__(self, "assumptions", _normalize_assumptions(self.assumptions))
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")

    @property
    def uncertainty_set_name(self) -> str:
        return self.uncertainty_set.name

    @property
    def assumption_count(self) -> int:
        return len(self.assumptions)


def _normalize_assumptions(values: Sequence[str]) -> AssumptionItems:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("assumptions must be a sequence of strings.")

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        assumption = _normalize_label(value, "assumption")
        if assumption in seen:
            raise ValueError("assumptions must not contain duplicates.")
        seen.add(assumption)
        normalized.append(assumption)
    return tuple(sorted(normalized))


def _normalize_label(value: str, label: str) -> str:
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
        label = _normalize_label(key, "metadata key")
        if isinstance(value, float) and not isfinite(value):
            raise ValueError("metadata float values must be finite.")
        if not isinstance(value, (str, int, float, bool, type(None))):
            raise TypeError("metadata values must be scalar strings, numbers, bools, or None.")
        normalized.append((label, value))
    return tuple(sorted(normalized))
