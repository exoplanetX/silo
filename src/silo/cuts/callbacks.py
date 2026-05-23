from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from math import isfinite
from types import MappingProxyType
from typing import Protocol, runtime_checkable


class CallbackHook(str, Enum):
    BEFORE_NODE_SOLVE = "before_node_solve"
    AFTER_LP_RELAXATION = "after_lp_relaxation"
    AFTER_CANDIDATE_CUT_SEPARATION = "after_candidate_cut_separation"
    AFTER_CUT_POOL_UPDATE = "after_cut_pool_update"
    AFTER_INCUMBENT_UPDATE = "after_incumbent_update"
    AFTER_NODE_PRUNE = "after_node_prune"
    AFTER_CHILD_CREATION = "after_child_creation"
    SOLVE_COMPLETE = "solve_complete"


@dataclass(frozen=True)
class CallbackEvent:
    hook: CallbackHook
    node_id: int | None = None
    depth: int | None = None
    parent_id: int | None = None
    lp_status: str | None = None
    lp_objective: float | None = None
    prune_reason: str | None = None
    branching_variable: str | None = None
    incumbent_objective: float | None = None
    cut_count: int = 0
    cut_ids: Iterable[str] = field(default_factory=tuple)
    solver_status: str | None = None
    diagnostics: Mapping[str, object] = field(default_factory=dict)

    def __post_init__(self) -> None:
        object.__setattr__(self, "hook", CallbackHook(self.hook))
        _validate_nonnegative_optional_int(self.node_id, "node id")
        _validate_nonnegative_optional_int(self.depth, "depth")
        _validate_nonnegative_optional_int(self.parent_id, "parent id")
        _validate_optional_label(self.lp_status, "LP status")
        _validate_optional_label(self.prune_reason, "prune reason")
        _validate_optional_label(self.branching_variable, "branching variable")
        _validate_optional_label(self.solver_status, "solver status")
        _validate_optional_finite_float(self.lp_objective, "LP objective")
        _validate_optional_finite_float(self.incumbent_objective, "incumbent objective")

        if self.cut_count < 0:
            raise ValueError("Callback event cut count must be nonnegative.")

        cut_ids = _normalize_cut_ids(self.cut_ids)
        object.__setattr__(self, "cut_ids", cut_ids)
        object.__setattr__(self, "diagnostics", MappingProxyType(dict(self.diagnostics)))


@runtime_checkable
class CutCallback(Protocol):
    name: str

    def on_event(self, event: CallbackEvent) -> None:
        ...


@dataclass(frozen=True)
class NoOpCallback:
    name: str = "noop"

    def __post_init__(self) -> None:
        name = self.name.strip()
        if not name:
            raise ValueError("Callback name must not be empty.")
        object.__setattr__(self, "name", name)

    def on_event(self, event: CallbackEvent) -> None:
        if not isinstance(event, CallbackEvent):
            raise TypeError("NoOpCallback requires a CallbackEvent.")
        return None


def dispatch_callback_events(
    callbacks: Iterable[CutCallback],
    events: Iterable[CallbackEvent],
) -> tuple[CallbackEvent, ...]:
    callback_tuple = tuple(callbacks)
    event_tuple = tuple(events)

    for callback in callback_tuple:
        if not isinstance(callback, CutCallback):
            raise TypeError("Callback dispatch requires CutCallback instances.")

    for event in event_tuple:
        if not isinstance(event, CallbackEvent):
            raise TypeError("Callback dispatch requires CallbackEvent instances.")
        for callback in callback_tuple:
            result = callback.on_event(event)
            if result is not None:
                raise TypeError("Callbacks must not return control signals.")

    return event_tuple


def _validate_nonnegative_optional_int(value: int | None, label: str) -> None:
    if value is not None and value < 0:
        raise ValueError(f"Callback event {label} must be nonnegative.")


def _validate_optional_finite_float(value: float | None, label: str) -> None:
    if value is not None and not isfinite(float(value)):
        raise ValueError(f"Callback event {label} must be finite.")


def _validate_optional_label(value: str | None, label: str) -> None:
    if value is not None and not value.strip():
        raise ValueError(f"Callback event {label} must not be empty when provided.")


def _normalize_cut_ids(cut_ids: Iterable[str]) -> tuple[str, ...]:
    if isinstance(cut_ids, str):
        raise TypeError("Callback event cut ids must be an iterable of cut ids.")

    normalized = tuple(cut_ids)
    if any(not cut_id.strip() for cut_id in normalized):
        raise ValueError("Callback event cut ids must not contain empty values.")
    return normalized
