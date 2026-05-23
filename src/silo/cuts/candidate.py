from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import Enum
from math import isfinite

from silo.core.enums import ConstraintSense

DEFAULT_CUT_TOLERANCE = 1e-9


class CutValidityScope(str, Enum):
    GLOBAL = "global"
    NODE_LOCAL = "node_local"


class CutActivityState(str, Enum):
    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    ACTIVE = "active"
    DUPLICATE = "duplicate"
    REJECTED = "rejected"
    EXPIRED = "expired"


@dataclass(frozen=True)
class CutMetadata:
    source: str
    scope: CutValidityScope = CutValidityScope.GLOBAL
    cut_id: str | None = None
    node_id: int | None = None
    tolerance: float = DEFAULT_CUT_TOLERANCE
    message: str = ""
    state: CutActivityState = CutActivityState.CANDIDATE

    def __post_init__(self) -> None:
        source = self.source.strip()
        if not source:
            raise ValueError("Cut metadata source must not be empty.")
        object.__setattr__(self, "source", source)

        if self.cut_id is not None:
            cut_id = self.cut_id.strip()
            if not cut_id:
                raise ValueError("Cut metadata cut id must not be empty when provided.")
            object.__setattr__(self, "cut_id", cut_id)

        if self.node_id is not None and self.node_id < 0:
            raise ValueError("Cut metadata node id must be nonnegative when provided.")

        tolerance = float(self.tolerance)
        if not isfinite(tolerance) or tolerance <= 0.0:
            raise ValueError("Cut metadata tolerance must be positive and finite.")
        object.__setattr__(self, "tolerance", tolerance)
        object.__setattr__(self, "scope", CutValidityScope(self.scope))
        object.__setattr__(self, "state", CutActivityState(self.state))


@dataclass(frozen=True)
class CutCandidate:
    coefficients: Mapping[str, float]
    sense: ConstraintSense
    rhs: float
    metadata: CutMetadata

    def __post_init__(self) -> None:
        normalized = _normalize_coefficients(self.coefficients)
        object.__setattr__(self, "coefficients", normalized)
        object.__setattr__(self, "sense", ConstraintSense(self.sense))

        rhs = float(self.rhs)
        if not isfinite(rhs):
            raise ValueError("Cut candidate RHS must be finite.")
        object.__setattr__(self, "rhs", rhs)

    def canonical_key(
        self,
        variable_order: Iterable[str] | None = None,
    ) -> tuple[str, tuple[tuple[str, float], ...], str, float, str, int | None]:
        return (
            "cut",
            self._ordered_coefficients(variable_order),
            self.sense.value,
            self.rhs,
            self.metadata.scope.value,
            self.metadata.node_id,
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


def _normalize_coefficients(coefficients: Mapping[str, float]) -> tuple[tuple[str, float], ...]:
    if not coefficients:
        raise ValueError("Cut candidate coefficients must not be empty.")

    normalized: list[tuple[str, float]] = []
    has_nonzero = False
    for variable_name, coefficient in coefficients.items():
        if not variable_name:
            raise ValueError("Cut candidate variable names must not be empty.")
        value = float(coefficient)
        if not isfinite(value):
            raise ValueError("Cut candidate coefficients must be finite.")
        if value != 0.0:
            has_nonzero = True
        normalized.append((variable_name, value))

    if not has_nonzero:
        raise ValueError("Cut candidate coefficient vector must contain a nonzero value.")

    return tuple(sorted(normalized))
