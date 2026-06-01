from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite

from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus

MetadataValue = str | int | float | bool | None
MetadataItems = tuple[tuple[str, MetadataValue], ...]
NumericItems = tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class MasterProblem:
    model: Model
    name: str = "master"
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_model(self.model, "master model")
        object.__setattr__(self, "name", _normalize_label(self.name, "master name"))
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))


@dataclass(frozen=True)
class MasterProblemContext:
    problem: MasterProblem
    iteration_id: int = 0
    incumbent_values: Mapping[str, float] = field(default_factory=dict)
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.problem, MasterProblem):
            raise TypeError("master context problem must be a MasterProblem.")
        object.__setattr__(
            self,
            "iteration_id",
            _normalize_iteration_id(self.iteration_id, "master iteration id"),
        )
        object.__setattr__(
            self,
            "incumbent_values",
            _normalize_numeric_mapping(self.incumbent_values, "incumbent values"),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))


@dataclass(frozen=True)
class MasterProblemResult:
    status: SolverStatus | str
    objective_value: float | None = None
    primal_values: Mapping[str, float] = field(default_factory=dict)
    dual_values: Mapping[str, float] = field(default_factory=dict)
    reduced_costs: Mapping[str, float] = field(default_factory=dict)
    message: str = ""
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "status",
            _normalize_status(self.status, "master result status"),
        )
        object.__setattr__(
            self,
            "objective_value",
            _normalize_optional_float(self.objective_value, "master objective value"),
        )
        object.__setattr__(
            self,
            "primal_values",
            _normalize_numeric_mapping(self.primal_values, "master primal values"),
        )
        object.__setattr__(
            self,
            "dual_values",
            _normalize_numeric_mapping(self.dual_values, "master dual values"),
        )
        object.__setattr__(
            self,
            "reduced_costs",
            _normalize_numeric_mapping(self.reduced_costs, "master reduced costs"),
        )
        object.__setattr__(self, "message", _normalize_message(self.message))
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))

    @classmethod
    def from_solution(
        cls,
        solution: Solution,
        *,
        metadata: Mapping[str, MetadataValue] | None = None,
    ) -> MasterProblemResult:
        if not isinstance(solution, Solution):
            raise TypeError("master result source must be a Solution.")
        return cls(
            status=solution.status,
            objective_value=solution.objective_value,
            primal_values=solution.primal_values,
            dual_values=solution.dual_values,
            reduced_costs=solution.reduced_costs,
            message=solution.message,
            metadata=metadata or {},
        )


def _validate_model(model: Model, label: str) -> None:
    if not isinstance(model, Model):
        raise TypeError(f"{label} must be a Model.")


def _normalize_label(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _normalize_iteration_id(value: int, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{label} must be an integer.")
    if value < 0:
        raise ValueError(f"{label} must be nonnegative.")
    return value


def _normalize_status(value: SolverStatus | str, label: str) -> SolverStatus:
    if isinstance(value, SolverStatus):
        return value
    try:
        return SolverStatus(value)
    except ValueError as exc:
        raise ValueError(f"{label} must be a supported SolverStatus value.") from exc


def _normalize_optional_float(value: float | None, label: str) -> float | None:
    if value is None:
        return None
    numeric = float(value)
    if not isfinite(numeric):
        raise ValueError(f"{label} must be finite.")
    return numeric


def _normalize_numeric_mapping(
    values: Mapping[str, float],
    label: str,
) -> NumericItems:
    if not isinstance(values, Mapping):
        raise TypeError(f"{label} must be a mapping.")
    normalized: list[tuple[str, float]] = []
    for key, value in values.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError(f"{label} keys must be nonempty strings.")
        numeric = float(value)
        if not isfinite(numeric):
            raise ValueError(f"{label} values must be finite.")
        normalized.append((key, numeric))
    return tuple(sorted(normalized))


def _normalize_metadata(values: Mapping[str, MetadataValue]) -> MetadataItems:
    if not isinstance(values, Mapping):
        raise TypeError("metadata must be a mapping.")
    normalized: list[tuple[str, MetadataValue]] = []
    for key, value in values.items():
        if not isinstance(key, str) or not key.strip():
            raise ValueError("metadata keys must be nonempty strings.")
        if isinstance(value, float) and not isfinite(value):
            raise ValueError("metadata float values must be finite.")
        if not isinstance(value, (str, int, float, bool, type(None))):
            raise TypeError("metadata values must be scalar strings, numbers, bools, or None.")
        normalized.append((key, value))
    return tuple(sorted(normalized))


def _normalize_message(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("message must be a string.")
    return value
