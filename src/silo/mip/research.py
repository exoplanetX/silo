"""Public read-only MIP research contexts and bounded, validated callbacks.

Callbacks may select existing nodes/branch candidates/verified cuts or propose a
complete incumbent. They never receive the mutable search tree or native arrays.
"""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from time import perf_counter
from types import MappingProxyType


def readonly(value):
    if isinstance(value, Mapping):
        return MappingProxyType({key: readonly(item) for key, item in value.items()})
    if isinstance(value, tuple | list):
        return tuple(readonly(item) for item in value)
    return value


@dataclass(frozen=True)
class OpenNodeView:
    number: int
    parent: int | None
    depth: int
    bound: float


@dataclass(frozen=True)
class VerifiedCutView:
    name: str
    coefficients: Mapping
    lower: float
    scope: str = "node_local"


@dataclass(frozen=True)
class ResearchContext:
    event: str
    node: int | None
    depth: int | None
    point: Mapping
    lower: Mapping
    upper: Mapping
    costs: Mapping
    objective_constant: float
    sense: str
    fractional: tuple[str, ...]
    open_nodes: tuple[OpenNodeView, ...]
    cuts: tuple[VerifiedCutView, ...]
    primal_bound: float | None
    dual_bound: float
    iterations: int
    elapsed_seconds: float
    statistics: Mapping


@dataclass(frozen=True)
class ResearchExtensions:
    branch_rule: Callable | None = None  # -> a name from context.fractional
    node_selector: Callable | None = None  # -> an ID from context.open_nodes
    separator: Callable | None = None  # -> unique indices into verified context.cuts
    heuristic: Callable | None = None  # -> complete primal mapping, or None
    observer: Callable | None = None  # receives immutable iteration contexts
    call_limit: int = 10000

    def __post_init__(self):
        if type(self.call_limit) is not int or self.call_limit < 0:
            raise ValueError("call_limit must be a nonnegative integer.")
        for name in ("branch_rule", "node_selector", "separator", "heuristic", "observer"):
            callback = getattr(self, name)
            if callback is not None and not callable(callback):
                raise TypeError(f"{name} must be callable or None.")


class ResearchControl:
    """Executor-owned callback budget; failures retain the ordinary search frontier."""

    def __init__(self, extensions, deadline):
        self.extensions = extensions or ResearchExtensions()
        self.deadline = deadline
        self.calls = 0
        self.trace = []
        self.error = None
        self.reason = None

    def reject(self, message, reason="invalid_research_action"):
        if self.error is None:
            self.error, self.reason = message, reason

    def invoke(self, name, context, default=None):
        callback = getattr(self.extensions, name)
        if callback is None or self.error is not None:
            return default
        if self.calls >= self.extensions.call_limit:
            self.reject("Research callback call budget exhausted.", "research_call_limit")
            return default
        if perf_counter() >= self.deadline:
            self.reject("Research callback deadline exhausted.", "time_limit")
            return default
        self.calls += 1
        self.trace.append({"hook": name, "event": context.event, "node": context.node})
        try:
            value = callback(context)
        except Exception as exc:
            self.reject(f"{name}: {type(exc).__name__}: {exc}")
            return default
        if perf_counter() >= self.deadline:
            self.reject("Research callback exceeded deadline.", "time_limit")
        return value
