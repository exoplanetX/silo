from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from silo.core.model import Model
from silo.core.status import SolverStatus
from silo.decomposition.master import (
    MetadataValue,
    _normalize_iteration_id,
    _normalize_label,
    _normalize_metadata,
    _normalize_numeric_mapping,
    _normalize_optional_float,
    _normalize_status,
    _validate_model,
)


@dataclass(frozen=True)
class Subproblem:
    model: Model
    name: str = "subproblem"
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_model(self.model, "subproblem model")
        object.__setattr__(self, "name", _normalize_label(self.name, "subproblem name"))
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))


@dataclass(frozen=True)
class SubproblemContext:
    problem: Subproblem
    iteration_id: int = 0
    master_values: Mapping[str, float] = field(default_factory=dict)
    master_objective: float | None = None
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.problem, Subproblem):
            raise TypeError("subproblem context problem must be a Subproblem.")
        object.__setattr__(
            self,
            "iteration_id",
            _normalize_iteration_id(self.iteration_id, "subproblem iteration id"),
        )
        object.__setattr__(
            self,
            "master_values",
            _normalize_numeric_mapping(self.master_values, "subproblem master values"),
        )
        object.__setattr__(
            self,
            "master_objective",
            _normalize_optional_float(
                self.master_objective,
                "subproblem master objective",
            ),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))


@dataclass(frozen=True)
class SubproblemResult:
    status: SolverStatus | str
    objective_value: float | None = None
    generated_cut_count: int = 0
    generated_column_count: int = 0
    message: str = ""
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "status",
            _normalize_status(self.status, "subproblem result status"),
        )
        object.__setattr__(
            self,
            "objective_value",
            _normalize_optional_float(self.objective_value, "subproblem objective value"),
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
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))


def _normalize_nonnegative_count(value: int, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{label} must be an integer.")
    if value < 0:
        raise ValueError(f"{label} must be nonnegative.")
    return value
