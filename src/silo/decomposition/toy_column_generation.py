from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from silo.core.enums import OptimizationSense
from silo.decomposition.column_candidate import (
    DEFAULT_COLUMN_TOLERANCE,
    ColumnCandidate,
)
from silo.decomposition.logging import (
    DecompositionIterationLog,
    DecompositionMethod,
    DecompositionRunSummary,
    DecompositionTerminationReason,
)
from silo.decomposition.master import MetadataItems, MetadataValue, _normalize_metadata

_FixtureItems = tuple["ToyColumnGenerationIterationFixture", ...]


@dataclass(frozen=True)
class ToyColumnCandidateSpec:
    """Fixture-level column placeholder, not a pricing proof for arbitrary models."""

    column_id: str
    variable_name: str
    objective_coefficient: float
    row_coefficients: Mapping[str, float]
    reduced_cost: float
    source_pricing_subproblem: str = "toy_pricing_subproblem"
    tolerance: float = DEFAULT_COLUMN_TOLERANCE
    message: str = ""

    def __post_init__(self) -> None:
        candidate = ColumnCandidate(
            column_id=self.column_id,
            variable_name=self.variable_name,
            objective_coefficient=self.objective_coefficient,
            row_coefficients=self.row_coefficients,
            reduced_cost=self.reduced_cost,
            source_pricing_subproblem=self.source_pricing_subproblem,
            iteration_id=0,
            tolerance=self.tolerance,
            message=self.message,
        )
        object.__setattr__(self, "column_id", candidate.column_id)
        object.__setattr__(self, "variable_name", candidate.variable_name)
        object.__setattr__(
            self,
            "objective_coefficient",
            candidate.objective_coefficient,
        )
        object.__setattr__(self, "row_coefficients", candidate.row_coefficients)
        object.__setattr__(self, "reduced_cost", candidate.reduced_cost)
        object.__setattr__(
            self,
            "source_pricing_subproblem",
            candidate.source_pricing_subproblem,
        )
        object.__setattr__(self, "tolerance", candidate.tolerance)
        object.__setattr__(self, "message", candidate.message)

    def to_candidate(self, iteration_id: int) -> ColumnCandidate:
        return ColumnCandidate(
            column_id=self.column_id,
            variable_name=self.variable_name,
            objective_coefficient=self.objective_coefficient,
            row_coefficients=dict(self.row_coefficients),
            reduced_cost=self.reduced_cost,
            source_pricing_subproblem=self.source_pricing_subproblem,
            iteration_id=iteration_id,
            tolerance=self.tolerance,
            message=self.message,
        )


@dataclass(frozen=True)
class ToyColumnGenerationIterationFixture:
    """One toy column-generation iteration with precomputed column candidates."""

    column_specs: Sequence[ToyColumnCandidateSpec] = ()
    message: str = ""
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if isinstance(self.column_specs, ToyColumnCandidateSpec):
            raise TypeError(
                "column specs must be a sequence of ToyColumnCandidateSpec records."
            )
        normalized: list[ToyColumnCandidateSpec] = []
        for column_spec in self.column_specs:
            if not isinstance(column_spec, ToyColumnCandidateSpec):
                raise TypeError("column specs must contain ToyColumnCandidateSpec records.")
            normalized.append(column_spec)
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")
        object.__setattr__(self, "column_specs", tuple(normalized))
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))


@dataclass(frozen=True)
class ToyColumnGenerationDriver:
    """Educational fixture driver; it never solves masters, prices columns, or mutates models.

    Reduced-cost conventions are relative to the configured objective sense:
    minimization accepts columns with reduced cost below ``-tolerance`` and maximization
    accepts columns with reduced cost above ``tolerance``.
    """

    iterations: Sequence[ToyColumnGenerationIterationFixture]
    objective_sense: OptimizationSense | str
    iteration_limit: int
    message: str = ""
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "iterations", _normalize_fixtures(self.iterations))
        object.__setattr__(
            self,
            "objective_sense",
            _normalize_objective_sense(self.objective_sense),
        )
        object.__setattr__(
            self,
            "iteration_limit",
            _normalize_positive_integer(self.iteration_limit, "iteration limit"),
        )
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    def run(self) -> DecompositionRunSummary:
        seen_column_keys: set[
            tuple[str, str, float, tuple[tuple[str, float], ...]]
        ] = set()
        logs: list[DecompositionIterationLog] = []
        final_reason = DecompositionTerminationReason.ITERATION_LIMIT
        final_message = "Toy column-generation iteration limit reached."

        for iteration_id in range(self.iteration_limit):
            fixture = self.iterations[iteration_id] if iteration_id < len(self.iterations) else None
            if fixture is None or not fixture.column_specs:
                final_reason = DecompositionTerminationReason.NO_IMPROVING_COLUMN
                final_message = _fixture_message(
                    fixture,
                    "Toy column-generation fixture found no improving columns.",
                )
                logs.append(
                    _iteration_log(
                        iteration_id=iteration_id,
                        generated_count=0,
                        accepted_count=0,
                        duplicate_count=0,
                        column_ids=(),
                        termination_reason=final_reason,
                        message=final_message,
                        metadata=_fixture_metadata(fixture),
                    )
                )
                break

            candidates = tuple(
                column_spec.to_candidate(iteration_id)
                for column_spec in fixture.column_specs
            )
            column_ids: list[str] = []
            improving_count = 0
            accepted_count = 0
            duplicate_count = 0
            for candidate in candidates:
                column_ids.append(candidate.column_id)
                if not candidate.is_improving_for(self.objective_sense):
                    continue
                improving_count += 1
                key = candidate.canonical_key()
                if key in seen_column_keys:
                    duplicate_count += 1
                else:
                    seen_column_keys.add(key)
                    accepted_count += 1

            if improving_count == 0:
                final_reason = DecompositionTerminationReason.NO_IMPROVING_COLUMN
                final_message = _fixture_message(
                    fixture,
                    "Toy column-generation fixture found no improving columns.",
                )
            elif duplicate_count > 0:
                final_reason = DecompositionTerminationReason.DUPLICATE_CANDIDATE
                final_message = _fixture_message(
                    fixture,
                    "Toy column-generation duplicate column candidate detected.",
                )
            elif iteration_id + 1 == self.iteration_limit:
                final_reason = DecompositionTerminationReason.ITERATION_LIMIT
                final_message = _fixture_message(
                    fixture,
                    "Toy column-generation iteration limit reached.",
                )
            else:
                final_reason = DecompositionTerminationReason.NOT_TERMINATED
                final_message = _fixture_message(fixture, "")

            logs.append(
                _iteration_log(
                    iteration_id=iteration_id,
                    generated_count=len(candidates),
                    accepted_count=accepted_count,
                    duplicate_count=duplicate_count,
                    column_ids=tuple(column_ids),
                    termination_reason=final_reason,
                    message=final_message,
                    metadata=_fixture_metadata(fixture),
                )
            )
            if final_reason != DecompositionTerminationReason.NOT_TERMINATED:
                break

        summary_message = self.message or final_message
        return DecompositionRunSummary(
            method=DecompositionMethod.COLUMN_GENERATION,
            iterations=tuple(logs),
            termination_reason=final_reason,
            message=summary_message,
            metadata=_metadata_to_mapping(self.metadata),
        )


def _normalize_fixtures(
    values: Sequence[ToyColumnGenerationIterationFixture],
) -> _FixtureItems:
    if isinstance(values, ToyColumnGenerationIterationFixture):
        raise TypeError(
            "iterations must be a sequence of ToyColumnGenerationIterationFixture records."
        )
    normalized: list[ToyColumnGenerationIterationFixture] = []
    for fixture in values:
        if not isinstance(fixture, ToyColumnGenerationIterationFixture):
            raise TypeError(
                "iterations must contain ToyColumnGenerationIterationFixture records."
            )
        normalized.append(fixture)
    if not normalized:
        raise ValueError("iterations must include at least one toy fixture iteration.")
    return tuple(normalized)


def _normalize_objective_sense(value: OptimizationSense | str) -> OptimizationSense:
    try:
        return OptimizationSense(value)
    except ValueError as exc:
        raise ValueError("objective sense must be a supported OptimizationSense value.") from exc


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
    column_ids: Sequence[str],
    termination_reason: DecompositionTerminationReason,
    message: str,
    metadata: Mapping[str, MetadataValue],
) -> DecompositionIterationLog:
    return DecompositionIterationLog(
        iteration_id=iteration_id,
        method=DecompositionMethod.COLUMN_GENERATION,
        generated_cut_count=0,
        accepted_cut_count=0,
        generated_column_count=generated_count,
        accepted_column_count=accepted_count,
        duplicate_count=duplicate_count,
        column_ids=column_ids,
        termination_reason=termination_reason,
        message=message,
        metadata=metadata,
    )


def _fixture_message(
    fixture: ToyColumnGenerationIterationFixture | None,
    default: str,
) -> str:
    if fixture is not None and fixture.message:
        return fixture.message
    return default


def _fixture_metadata(
    fixture: ToyColumnGenerationIterationFixture | None,
) -> dict[str, MetadataValue]:
    if fixture is None:
        return {}
    return _metadata_to_mapping(fixture.metadata)


def _metadata_to_mapping(metadata: MetadataItems) -> dict[str, MetadataValue]:
    return dict(metadata)
