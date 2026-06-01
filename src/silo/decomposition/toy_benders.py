from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from silo.core.enums import ConstraintSense
from silo.decomposition.benders_cut import (
    DEFAULT_BENDERS_CUT_TOLERANCE,
    BendersCutCandidate,
    BendersCutType,
)
from silo.decomposition.logging import (
    DecompositionIterationLog,
    DecompositionMethod,
    DecompositionRunSummary,
    DecompositionTerminationReason,
)
from silo.decomposition.master import MetadataItems, MetadataValue, _normalize_metadata

_FixtureItems = tuple["ToyBendersIterationFixture", ...]


@dataclass(frozen=True)
class ToyBendersCutSpec:
    """Fixture-level Benders cut placeholder, not a proof of validity for arbitrary models."""

    cut_id: str
    cut_type: BendersCutType | str
    coefficients: Mapping[str, float]
    sense: ConstraintSense | str
    rhs: float
    source_subproblem: str = "toy_subproblem"
    tolerance: float = DEFAULT_BENDERS_CUT_TOLERANCE
    message: str = ""

    def __post_init__(self) -> None:
        candidate = BendersCutCandidate(
            cut_id=self.cut_id,
            cut_type=self.cut_type,
            coefficients=self.coefficients,
            sense=self.sense,
            rhs=self.rhs,
            source_subproblem=self.source_subproblem,
            iteration_id=0,
            tolerance=self.tolerance,
            message=self.message,
        )
        object.__setattr__(self, "cut_id", candidate.cut_id)
        object.__setattr__(self, "cut_type", candidate.cut_type)
        object.__setattr__(self, "coefficients", candidate.coefficients)
        object.__setattr__(self, "sense", candidate.sense)
        object.__setattr__(self, "rhs", candidate.rhs)
        object.__setattr__(self, "source_subproblem", candidate.source_subproblem)
        object.__setattr__(self, "tolerance", candidate.tolerance)
        object.__setattr__(self, "message", candidate.message)

    def to_candidate(self, iteration_id: int) -> BendersCutCandidate:
        return BendersCutCandidate(
            cut_id=self.cut_id,
            cut_type=self.cut_type,
            coefficients=dict(self.coefficients),
            sense=self.sense,
            rhs=self.rhs,
            source_subproblem=self.source_subproblem,
            iteration_id=iteration_id,
            tolerance=self.tolerance,
            message=self.message,
        )


@dataclass(frozen=True)
class ToyBendersIterationFixture:
    """One toy outer iteration with precomputed cut placeholders."""

    cut_specs: Sequence[ToyBendersCutSpec] = ()
    message: str = ""
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.cut_specs, ToyBendersCutSpec):
            raise TypeError("cut specs must be a sequence of ToyBendersCutSpec records.")
        normalized: list[ToyBendersCutSpec] = []
        for cut_spec in self.cut_specs:
            if not isinstance(cut_spec, ToyBendersCutSpec):
                raise TypeError("cut specs must contain ToyBendersCutSpec records.")
            normalized.append(cut_spec)
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")
        object.__setattr__(self, "cut_specs", tuple(normalized))
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))


@dataclass(frozen=True)
class ToyBendersDriver:
    """Educational fixture driver; it never solves or mutates optimization models."""

    iterations: Sequence[ToyBendersIterationFixture]
    iteration_limit: int
    message: str = ""
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "iterations", _normalize_fixtures(self.iterations))
        object.__setattr__(
            self,
            "iteration_limit",
            _normalize_positive_integer(self.iteration_limit, "iteration limit"),
        )
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def run(self) -> DecompositionRunSummary:
        seen_cut_keys: set[tuple[str, str, tuple[tuple[str, float], ...], str, float]] = set()
        logs: list[DecompositionIterationLog] = []
        final_reason = DecompositionTerminationReason.ITERATION_LIMIT
        final_message = "Toy Benders iteration limit reached."

        for iteration_id in range(self.iteration_limit):
            fixture = self.iterations[iteration_id] if iteration_id < len(self.iterations) else None
            if fixture is None or not fixture.cut_specs:
                final_reason = DecompositionTerminationReason.NO_CUT_GENERATED
                final_message = _fixture_message(
                    fixture,
                    "Toy Benders fixture generated no cuts.",
                )
                logs.append(
                    _iteration_log(
                        iteration_id=iteration_id,
                        generated_count=0,
                        accepted_count=0,
                        duplicate_count=0,
                        cut_ids=(),
                        termination_reason=final_reason,
                        message=final_message,
                        metadata=_fixture_metadata(fixture),
                    )
                )
                break

            candidates = tuple(
                cut_spec.to_candidate(iteration_id) for cut_spec in fixture.cut_specs
            )
            cut_ids: list[str] = []
            accepted_count = 0
            duplicate_count = 0
            for candidate in candidates:
                cut_ids.append(candidate.cut_id)
                key = candidate.canonical_key()
                if key in seen_cut_keys:
                    duplicate_count += 1
                else:
                    seen_cut_keys.add(key)
                    accepted_count += 1

            if duplicate_count > 0:
                final_reason = DecompositionTerminationReason.DUPLICATE_CANDIDATE
                final_message = _fixture_message(
                    fixture,
                    "Toy Benders duplicate cut candidate detected.",
                )
            elif iteration_id + 1 == self.iteration_limit:
                final_reason = DecompositionTerminationReason.ITERATION_LIMIT
                final_message = _fixture_message(fixture, "Toy Benders iteration limit reached.")
            else:
                final_reason = DecompositionTerminationReason.NOT_TERMINATED
                final_message = _fixture_message(fixture, "")

            logs.append(
                _iteration_log(
                    iteration_id=iteration_id,
                    generated_count=len(candidates),
                    accepted_count=accepted_count,
                    duplicate_count=duplicate_count,
                    cut_ids=tuple(cut_ids),
                    termination_reason=final_reason,
                    message=final_message,
                    metadata=_fixture_metadata(fixture),
                )
            )
            if final_reason != DecompositionTerminationReason.NOT_TERMINATED:
                break

        summary_message = self.message or final_message
        return DecompositionRunSummary(
            method=DecompositionMethod.BENDERS,
            iterations=tuple(logs),
            termination_reason=final_reason,
            message=summary_message,
            metadata=_metadata_to_mapping(self.metadata),
        )


def _normalize_fixtures(values: Sequence[ToyBendersIterationFixture]) -> _FixtureItems:
    if isinstance(values, ToyBendersIterationFixture):
        raise TypeError("iterations must be a sequence of ToyBendersIterationFixture records.")
    normalized: list[ToyBendersIterationFixture] = []
    for fixture in values:
        if not isinstance(fixture, ToyBendersIterationFixture):
            raise TypeError("iterations must contain ToyBendersIterationFixture records.")
        normalized.append(fixture)
    if not normalized:
        raise ValueError("iterations must include at least one toy fixture iteration.")
    return tuple(normalized)


def _normalize_positive_integer(value: int, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{label} must be an integer.")
    if value <= 0:
        raise ValueError(f"{label} must be positive.")
    return value


def _iteration_log(
    *,
    iteration_id: int,
    generated_count: int,
    accepted_count: int,
    duplicate_count: int,
    cut_ids: Sequence[str],
    termination_reason: DecompositionTerminationReason,
    message: str,
    metadata: Mapping[str, MetadataValue],
) -> DecompositionIterationLog:
    return DecompositionIterationLog(
        iteration_id=iteration_id,
        method=DecompositionMethod.BENDERS,
        generated_cut_count=generated_count,
        accepted_cut_count=accepted_count,
        duplicate_count=duplicate_count,
        cut_ids=cut_ids,
        generated_column_count=0,
        accepted_column_count=0,
        termination_reason=termination_reason,
        message=message,
        metadata=metadata,
    )


def _fixture_message(fixture: ToyBendersIterationFixture | None, default: str) -> str:
    if fixture is not None and fixture.message:
        return fixture.message
    return default


def _fixture_metadata(fixture: ToyBendersIterationFixture | None) -> dict[str, MetadataValue]:
    if fixture is None:
        return {}
    return _metadata_to_mapping(fixture.metadata)


def _metadata_to_mapping(metadata: MetadataItems) -> dict[str, MetadataValue]:
    return dict(metadata)
