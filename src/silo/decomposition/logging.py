from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from enum import Enum

from silo.core.status import SolverStatus
from silo.decomposition.master import (
    MetadataValue,
    _normalize_metadata,
    _normalize_optional_float,
    _normalize_status,
)
from silo.decomposition.subproblem import _normalize_nonnegative_count

IdItems = tuple[str, ...]


class DecompositionMethod(str, Enum):
    BENDERS = "benders"
    COLUMN_GENERATION = "column_generation"


class DecompositionTerminationReason(str, Enum):
    NOT_TERMINATED = "not_terminated"
    NO_CUT_GENERATED = "no_cut_generated"
    NO_IMPROVING_COLUMN = "no_improving_column"
    DUPLICATE_CANDIDATE = "duplicate_candidate"
    ITERATION_LIMIT = "iteration_limit"
    UNSUPPORTED_STATUS = "unsupported_status"
    ERROR = "error"


@dataclass(frozen=True)
class DecompositionIterationLog:
    iteration_id: int
    method: DecompositionMethod | str
    master_status: SolverStatus | str | None = None
    subproblem_status: SolverStatus | str | None = None
    master_objective: float | None = None
    best_bound: float | None = None
    generated_cut_count: int = 0
    generated_column_count: int = 0
    accepted_cut_count: int = 0
    accepted_column_count: int = 0
    duplicate_count: int = 0
    cut_ids: Sequence[str] = ()
    column_ids: Sequence[str] = ()
    termination_reason: DecompositionTerminationReason | str = (
        DecompositionTerminationReason.NOT_TERMINATED
    )
    message: str = ""
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "iteration_id", _normalize_iteration_id(self.iteration_id))
        object.__setattr__(self, "method", _normalize_method(self.method))
        object.__setattr__(
            self,
            "master_status",
            _normalize_optional_status(self.master_status, "master status"),
        )
        object.__setattr__(
            self,
            "subproblem_status",
            _normalize_optional_status(self.subproblem_status, "subproblem status"),
        )
        object.__setattr__(
            self,
            "master_objective",
            _normalize_optional_float(self.master_objective, "master objective"),
        )
        object.__setattr__(
            self,
            "best_bound",
            _normalize_optional_float(self.best_bound, "best bound"),
        )
        object.__setattr__(
            self,
            "generated_cut_count",
            _normalize_nonnegative_count(
                self.generated_cut_count,
                "generated cut count",
            ),
        )
        object.__setattr__(
            self,
            "generated_column_count",
            _normalize_nonnegative_count(
                self.generated_column_count,
                "generated column count",
            ),
        )
        object.__setattr__(
            self,
            "accepted_cut_count",
            _normalize_nonnegative_count(self.accepted_cut_count, "accepted cut count"),
        )
        object.__setattr__(
            self,
            "accepted_column_count",
            _normalize_nonnegative_count(
                self.accepted_column_count,
                "accepted column count",
            ),
        )
        object.__setattr__(
            self,
            "duplicate_count",
            _normalize_nonnegative_count(self.duplicate_count, "duplicate count"),
        )
        object.__setattr__(self, "cut_ids", _normalize_ids(self.cut_ids, "cut ids"))
        object.__setattr__(
            self,
            "column_ids",
            _normalize_ids(self.column_ids, "column ids"),
        )
        object.__setattr__(
            self,
            "termination_reason",
            _normalize_termination_reason(self.termination_reason),
        )
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))


@dataclass(frozen=True)
class DecompositionRunSummary:
    method: DecompositionMethod | str
    iterations: Iterable[DecompositionIterationLog] = ()
    termination_reason: DecompositionTerminationReason | str = (
        DecompositionTerminationReason.NOT_TERMINATED
    )
    final_status: SolverStatus | str | None = None
    final_objective: float | None = None
    message: str = ""
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        method = _normalize_method(self.method)
        object.__setattr__(self, "method", method)
        iterations = _normalize_iterations(self.iterations, method)
        object.__setattr__(self, "iterations", iterations)
        object.__setattr__(
            self,
            "termination_reason",
            _normalize_termination_reason(self.termination_reason),
        )
        object.__setattr__(
            self,
            "final_status",
            _normalize_optional_status(self.final_status, "final status"),
        )
        object.__setattr__(
            self,
            "final_objective",
            _normalize_optional_float(self.final_objective, "final objective"),
        )
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @property
    def iteration_count(self) -> int:
        return len(self.iterations)


def _normalize_iteration_id(value: int) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("iteration id must be an integer.")
    if value < 0:
        raise ValueError("iteration id must be nonnegative.")
    return value


def _normalize_method(value: DecompositionMethod | str) -> DecompositionMethod:
    if isinstance(value, DecompositionMethod):
        return value
    try:
        return DecompositionMethod(value)
    except ValueError as exc:
        raise ValueError("method must be a supported DecompositionMethod value.") from exc


def _normalize_termination_reason(
    value: DecompositionTerminationReason | str,
) -> DecompositionTerminationReason:
    if isinstance(value, DecompositionTerminationReason):
        return value
    try:
        return DecompositionTerminationReason(value)
    except ValueError as exc:
        raise ValueError(
            "termination reason must be a supported DecompositionTerminationReason value."
        ) from exc


def _normalize_optional_status(
    value: SolverStatus | str | None,
    label: str,
) -> SolverStatus | None:
    if value is None:
        return None
    return _normalize_status(value, label)


def _normalize_ids(values: Sequence[str], label: str) -> IdItems:
    if isinstance(values, str) or not isinstance(values, Sequence):
        raise TypeError(f"{label} must be a sequence of strings.")
    normalized: list[str] = []
    for value in values:
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{label} must contain nonempty strings.")
        normalized.append(value.strip())
    return tuple(sorted(normalized))


def _normalize_iterations(
    values: Iterable[DecompositionIterationLog],
    method: DecompositionMethod,
) -> tuple[DecompositionIterationLog, ...]:
    if isinstance(values, DecompositionIterationLog):
        raise TypeError("iterations must be an iterable of DecompositionIterationLog records.")
    normalized = tuple(values)
    seen_iteration_ids: set[int] = set()
    for entry in normalized:
        if not isinstance(entry, DecompositionIterationLog):
            raise TypeError("iterations must contain DecompositionIterationLog records.")
        if entry.method != method:
            raise ValueError("iteration methods must match the run summary method.")
        if entry.iteration_id in seen_iteration_ids:
            raise ValueError("iteration ids must be unique within a run summary.")
        seen_iteration_ids.add(entry.iteration_id)
    return tuple(sorted(normalized, key=lambda entry: entry.iteration_id))
