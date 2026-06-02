from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.uncertainty.robust_model import RobustModel
from silo.uncertainty.uncertainty_set import (
    RHS_TARGET,
    IntervalUncertainty,
    MetadataItems,
    MetadataValue,
)

ROBUST_RHS_WORST_CASE = "interval_rhs_worst_case"


@dataclass(frozen=True)
class RobustCounterpartDiagnostics:
    """Passive robust-counterpart diagnostics; it records transformation shape only."""

    interval_names: Sequence[str]
    adjusted_constraints: Sequence[str]
    generated_constraints: int = 0
    rhs_convention: str = ROBUST_RHS_WORST_CASE
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "interval_names", _normalize_labels(self.interval_names))
        object.__setattr__(
            self,
            "adjusted_constraints",
            _normalize_labels(self.adjusted_constraints),
        )
        object.__setattr__(
            self,
            "generated_constraints",
            _normalize_nonnegative_count(
                self.generated_constraints,
                "generated constraint count",
            ),
        )
        object.__setattr__(
            self,
            "rhs_convention",
            _normalize_nonempty_text(self.rhs_convention, "RHS convention"),
        )
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")

    @property
    def adjusted_constraint_count(self) -> int:
        return len(self.adjusted_constraints)

    @property
    def interval_count(self) -> int:
        return len(self.interval_names)


@dataclass(frozen=True)
class RobustCounterpartResult:
    """Robust counterpart result paired with deterministic diagnostics."""

    model: Model
    diagnostics: RobustCounterpartDiagnostics
    metadata: Mapping[str, MetadataValue] = field(default_factory=dict)
    message: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.model, Model):
            raise TypeError("model must be a Model.")
        self.model.validate()
        if not isinstance(self.diagnostics, RobustCounterpartDiagnostics):
            raise TypeError("diagnostics must be RobustCounterpartDiagnostics.")
        object.__setattr__(self, "metadata", _normalize_metadata(self.metadata))
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")


def build_robust_counterpart(model: RobustModel) -> Model | RobustCounterpartResult:
    if not isinstance(model, RobustModel):
        raise TypeError("model must be a RobustModel.")

    intervals = tuple(model.uncertainty_set.intervals)
    if not intervals:
        return model.base_model

    rhs_intervals = _validate_interval_rhs_scope(model)
    if not rhs_intervals:
        return model.base_model

    base_model = model.base_model
    constraints_by_name = {constraint.name: constraint for constraint in base_model.constraints}
    adjusted_constraints = tuple(interval.constraint_name for interval in rhs_intervals)
    adjusted_rhs = {
        interval.constraint_name: _worst_case_rhs(
            constraints_by_name[interval.constraint_name],
            interval,
        )
        for interval in rhs_intervals
    }
    result_model = Model(
        name=f"{base_model.name}_robust_counterpart",
        variables=[_copy_variable(variable) for variable in base_model.variables],
        constraints=[
            _copy_constraint(
                constraint,
                rhs=adjusted_rhs.get(constraint.name, constraint.rhs),
            )
            for constraint in base_model.constraints
        ],
        objective=_copy_objective(base_model.objective),
    )
    diagnostics = RobustCounterpartDiagnostics(
        interval_names=tuple(interval.name for interval in rhs_intervals),
        adjusted_constraints=adjusted_constraints,
        generated_constraints=0,
        metadata={"builder": "toy_interval_rhs"},
        message="Toy interval-RHS robust counterpart transformation.",
    )
    return RobustCounterpartResult(
        model=result_model,
        diagnostics=diagnostics,
        message="Toy robust counterpart result.",
    )


def _validate_interval_rhs_scope(model: RobustModel) -> tuple[IntervalUncertainty, ...]:
    constraint_names = {constraint.name for constraint in model.base_model.constraints}
    constraints_by_name = {
        constraint.name: constraint for constraint in model.base_model.constraints
    }
    rhs_intervals: list[IntervalUncertainty] = []
    seen_constraints: set[str] = set()

    for interval in model.uncertainty_set.intervals:
        if interval.target != RHS_TARGET:
            raise ValueError("robust counterparts currently support RHS intervals only.")
        if not interval.constraint_name:
            raise ValueError("RHS intervals must include a constraint name.")
        if interval.constraint_name not in constraint_names:
            raise ValueError(f"Unknown RHS interval constraint: {interval.constraint_name}")
        if interval.variable_name:
            raise ValueError("RHS intervals must not include a variable name.")
        if interval.constraint_name in seen_constraints:
            raise ValueError(f"Duplicate RHS interval constraint: {interval.constraint_name}")
        seen_constraints.add(interval.constraint_name)

        base_constraint = constraints_by_name[interval.constraint_name]
        if interval.nominal is not None and interval.nominal != float(base_constraint.rhs):
            raise ValueError(
                "RHS interval nominal value must match the base constraint RHS: "
                f"{interval.constraint_name}"
            )
        rhs_intervals.append(interval)

    return tuple(rhs_intervals)


def _worst_case_rhs(constraint: Constraint, interval: IntervalUncertainty) -> float:
    if constraint.sense == ConstraintSense.LE:
        return interval.lower
    if constraint.sense == ConstraintSense.GE:
        return interval.upper
    if constraint.sense == ConstraintSense.EQ:
        if interval.lower != interval.upper:
            raise ValueError(
                "equality RHS intervals must be degenerate for robust counterpart conversion."
            )
        return interval.lower
    raise ValueError(f"Unsupported constraint sense for robust counterpart: {constraint.sense}")


def _copy_variable(variable: Variable) -> Variable:
    return Variable(
        name=variable.name,
        bounds=variable.bounds,
        var_type=variable.var_type,
    )


def _copy_constraint(constraint: Constraint, rhs: float) -> Constraint:
    return Constraint(
        name=constraint.name,
        coefficients=dict(constraint.coefficients),
        sense=constraint.sense,
        rhs=rhs,
    )


def _copy_objective(objective: Objective) -> Objective:
    return Objective(
        coefficients=dict(objective.coefficients),
        sense=objective.sense,
        constant=objective.constant,
    )


def _normalize_labels(values: Sequence[str]) -> tuple[str, ...]:
    if isinstance(values, (str, bytes)) or not isinstance(values, Sequence):
        raise TypeError("values must be a sequence of strings.")

    normalized: list[str] = []
    seen: set[str] = set()
    for value in values:
        label = _normalize_nonempty_text(value, "label")
        if label in seen:
            raise ValueError("values must not contain duplicates.")
        seen.add(label)
        normalized.append(label)
    return tuple(sorted(normalized))


def _normalize_nonnegative_count(value: int, label: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{label} must be an integer.")
    if value < 0:
        raise ValueError(f"{label} must be nonnegative.")
    return value


def _normalize_nonempty_text(value: str, label: str) -> str:
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
        label = _normalize_nonempty_text(key, "metadata key")
        if isinstance(value, float) and not isfinite(value):
            raise ValueError("metadata float values must be finite.")
        if not isinstance(value, (str, int, float, bool, type(None))):
            raise TypeError("metadata values must be scalar strings, numbers, bools, or None.")
        normalized.append((label, value))
    return tuple(sorted(normalized))
