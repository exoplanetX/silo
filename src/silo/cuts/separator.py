from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from math import isfinite
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from silo.core.enums import ConstraintSense
from silo.cuts.candidate import (
    DEFAULT_CUT_TOLERANCE,
    CutCandidate,
    CutMetadata,
    CutValidityScope,
)
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


@dataclass(frozen=True)
class ToyUpperBoundSeparator:
    variable_name: str
    upper_bound: float
    name: str = "toy_upper_bound"
    tolerance: float = DEFAULT_CUT_TOLERANCE

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name:
            raise ValueError("Separator name must not be empty.")
        object.__setattr__(self, "name", name)

        variable_name = self.variable_name.strip()
        if not variable_name:
            raise ValueError("Toy upper-bound separator variable name must not be empty.")
        object.__setattr__(self, "variable_name", variable_name)

        upper_bound = float(self.upper_bound)
        if not isfinite(upper_bound):
            raise ValueError("Toy upper-bound separator upper bound must be finite.")
        object.__setattr__(self, "upper_bound", upper_bound)

        tolerance = float(self.tolerance)
        if not isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError("Toy upper-bound separator tolerance must be positive and finite.")
        object.__setattr__(self, "tolerance", tolerance)

    def separate(self, context: SeparatorContext) -> tuple[CutCandidate, ...]:
        if not isinstance(context, SeparatorContext):
            raise TypeError("ToyUpperBoundSeparator requires a SeparatorContext.")
        if self.variable_name not in context.variable_names:
            raise ValueError(
                "Toy upper-bound separator variable must be present in context variable names."
            )
        if self.variable_name not in context.relaxation_values:
            return ()

        value = context.relaxation_values[self.variable_name]
        if value <= self.upper_bound + self.tolerance:
            return ()

        return (
            CutCandidate(
                coefficients={self.variable_name: 1.0},
                sense=ConstraintSense.LE,
                rhs=self.upper_bound,
                metadata=CutMetadata(
                    source=self.name,
                    scope=CutValidityScope.GLOBAL,
                    cut_id=f"{self.name}:{self.variable_name}:upper_bound",
                    tolerance=self.tolerance,
                    message=(
                        "Toy upper-bound cut; valid only for fixtures where the "
                        "configured upper bound is documented as globally valid."
                    ),
                ),
            ),
        )


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
