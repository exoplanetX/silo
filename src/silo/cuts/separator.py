from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from silo.cuts.candidate import CutCandidate
from silo.cuts.cut_pool import CutPool


@dataclass(frozen=True)
class SeparatorContext:
    variable_names: Iterable[str] = field(default_factory=tuple)
    node_id: int | None = None
    relaxation_values: Mapping[str, float] = field(default_factory=dict)
    cut_pool: CutPool | None = None
    metadata: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        variable_names = _normalize_variable_names(self.variable_names)
        object.__setattr__(self, "variable_names", variable_names)

        if self.node_id is not None and self.node_id < 0:
            raise ValueError("Separator context node id must be nonnegative.")

        if self.cut_pool is not None and not isinstance(self.cut_pool, CutPool):
            raise TypeError("Separator context cut pool must be a CutPool when provided.")

        relaxation_values = _immutable_float_mapping(
            self.relaxation_values,
            allowed_keys=variable_names,
            label="relaxation values",
        )
        object.__setattr__(self, "relaxation_values", relaxation_values)
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))


@runtime_checkable
class Separator(Protocol):
    name: str

    def separate(self, context: SeparatorContext) -> Iterable[CutCandidate]:
        ...


@dataclass(frozen=True)
class NoOpSeparator:
    name: str = "noop"

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name:
            raise ValueError("Separator name must not be empty.")
        object.__setattr__(self, "name", name)

    def separate(self, context: SeparatorContext) -> tuple[CutCandidate, ...]:
        if not isinstance(context, SeparatorContext):
            raise TypeError("NoOpSeparator requires a SeparatorContext.")
        return ()


def separate_cuts(
    separator: Separator,
    context: SeparatorContext,
) -> tuple[CutCandidate, ...]:
    if not isinstance(context, SeparatorContext):
        raise TypeError("Separator runner requires a SeparatorContext.")

    candidates = tuple(separator.separate(context))
    for candidate in candidates:
        if not isinstance(candidate, CutCandidate):
            raise TypeError("Separator outputs must be CutCandidate instances.")
    return candidates


def _normalize_variable_names(variable_names: Iterable[str]) -> tuple[str, ...]:
    if isinstance(variable_names, str):
        raise TypeError("Separator context variable names must be an iterable of names.")

    normalized = tuple(variable_names)
    if any(not variable_name for variable_name in normalized):
        raise ValueError("Separator context variable names must not contain empty names.")
    if len(set(normalized)) != len(normalized):
        raise ValueError("Separator context variable names must not contain duplicates.")
    return normalized


def _immutable_float_mapping(
    values: Mapping[str, float],
    *,
    allowed_keys: tuple[str, ...],
    label: str,
) -> Mapping[str, float]:
    normalized: dict[str, float] = {}
    allowed_key_set = set(allowed_keys)
    for key, value in values.items():
        if not key:
            raise ValueError(f"Separator context {label} keys must not be empty.")
        if allowed_key_set and key not in allowed_key_set:
            raise ValueError(f"Separator context {label} contains unknown variable {key!r}.")
        value = float(value)
        if not isfinite(value):
            raise ValueError(f"Separator context {label} must be finite.")
        normalized[key] = value
    return MappingProxyType(normalized)
