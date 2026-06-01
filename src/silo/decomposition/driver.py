from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from silo.decomposition.logging import (
    DecompositionIterationLog,
    DecompositionMethod,
    DecompositionRunSummary,
    DecompositionTerminationReason,
)
from silo.decomposition.master import MetadataItems, MetadataValue, _normalize_metadata


@dataclass(frozen=True)
class NoOpDecompositionDriver:
    method: DecompositionMethod | str
    iteration_limit: int = 1
    message: str = ""
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "method", _normalize_method(self.method))
        object.__setattr__(
            self,
            "iteration_limit",
            _normalize_positive_integer(self.iteration_limit, "iteration limit"),
        )
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def run(self) -> DecompositionRunSummary:
        reason = _termination_reason_for(self.method)
        message = self.message or _default_message_for(self.method)
        metadata = _metadata_to_mapping(self.metadata)
        entry = DecompositionIterationLog(
            iteration_id=0,
            method=self.method,
            generated_cut_count=0,
            generated_column_count=0,
            accepted_cut_count=0,
            accepted_column_count=0,
            duplicate_count=0,
            termination_reason=reason,
            message=message,
            metadata=metadata,
        )
        return DecompositionRunSummary(
            method=self.method,
            iterations=(entry,),
            termination_reason=reason,
            message=message,
            metadata=metadata,
        )


def _normalize_method(value: DecompositionMethod | str) -> DecompositionMethod:
    if isinstance(value, DecompositionMethod):
        return value
    try:
        return DecompositionMethod(value)
    except ValueError as exc:
        raise ValueError("method must be a supported DecompositionMethod value.") from exc


def _normalize_positive_integer(value: int, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{label} must be an integer.")
    if value <= 0:
        raise ValueError(f"{label} must be positive.")
    return value


def _termination_reason_for(method: DecompositionMethod) -> DecompositionTerminationReason:
    if method == DecompositionMethod.BENDERS:
        return DecompositionTerminationReason.NO_CUT_GENERATED
    return DecompositionTerminationReason.NO_IMPROVING_COLUMN


def _default_message_for(method: DecompositionMethod) -> str:
    if method == DecompositionMethod.BENDERS:
        return "No-op Benders driver generated no cuts."
    return "No-op column-generation driver found no improving columns."


def _metadata_to_mapping(metadata: MetadataItems) -> dict[str, MetadataValue]:
    return dict(metadata)
