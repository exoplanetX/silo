"""Cold pricing on a finite DAG with exact nonnegative integer resource caps.

Only identical (node, resource tuple) states share a label. Objective arithmetic
follows the ordinary DAG floating-point reference; it is not symbolic exactness.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType

from silo.decomposition.dag_pricing import (
    DagArc,
    DagPricingProblem,
    _dot,
    _finite_input,
    _NumericalFailure,
    _sum,
    _topological_order,
)
from silo.utils.numerics import DEFAULT_TOLERANCE


class ResourceDagPricingStatus(str, Enum):
    OPTIMAL = "optimal"
    NO_PATH = "no_path"
    NUMERICAL_ISSUE = "numerical_issue"
    STATE_LIMIT = "state_limit"
    TRANSITION_LIMIT = "transition_limit"


def _resource_tuple(values: tuple[int, ...], label: str) -> tuple[int, ...]:
    if not isinstance(values, tuple):
        raise TypeError(f"{label} must be a tuple of nonnegative integers.")
    if any(type(value) is not int for value in values):
        raise TypeError(f"{label} requires strict integers, excluding bool.")
    if any(value < 0 for value in values):
        raise ValueError(f"{label} must be nonnegative.")
    return tuple(values)


@dataclass(frozen=True)
class ResourceDagPricingProblem:
    """A fixed ordinary DAG plus explicit, immutable per-arc resource vectors."""

    graph: DagPricingProblem
    resource_limits: tuple[int, ...]
    arc_resources: Mapping[str, tuple[int, ...]]

    def __post_init__(self) -> None:
        if not isinstance(self.graph, DagPricingProblem):
            raise TypeError("graph must be a DagPricingProblem.")
        limits = _resource_tuple(self.resource_limits, "Resource limits")
        if not isinstance(self.arc_resources, Mapping):
            raise TypeError("Arc resources must be a mapping.")
        if set(self.arc_resources) != {arc.arc_id for arc in self.graph.arcs}:
            raise ValueError("Resource keys must exactly match all graph arc IDs.")
        resources = {}
        for arc_id, values in self.arc_resources.items():
            vector = _resource_tuple(values, f"Resources of {arc_id!r}")
            if len(vector) != len(limits):
                raise ValueError("Each arc resource dimension must match the limits.")
            resources[arc_id] = vector
        object.__setattr__(self, "resource_limits", limits)
        object.__setattr__(self, "arc_resources", MappingProxyType(resources))


@dataclass(frozen=True)
class ResourceDagPricingResult:
    """Immutable candidate or empty failure, together with actual search counters.

Only OPTIMAL publishes a column and an improvement decision. Search limits are
incomplete searches, even when a feasible sink was already discovered.
"""

    status: ResourceDagPricingStatus
    arc_ids: tuple[str, ...] = ()
    cost: float | None = None
    row_coefficients: Mapping[str, float] = field(default_factory=dict)
    reduced_cost: float | None = None
    is_improving: bool | None = None
    resource_usage: tuple[int, ...] | None = None
    states_discovered: int = 0
    transitions_checked: int = 0
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "arc_ids", tuple(self.arc_ids))
        object.__setattr__(self, "row_coefficients", MappingProxyType(dict(self.row_coefficients)))
        if self.resource_usage is not None:
            object.__setattr__(self, "resource_usage", tuple(self.resource_usage))


def price_resource_dag(
    problem: ResourceDagPricingProblem,
    dual_values: Mapping[str, float],
    *,
    tolerance: float = DEFAULT_TOLERANCE,
    state_limit: int = 100000,
    transition_limit: int = 1000000,
) -> ResourceDagPricingResult:
    """Cold topological DP over all resource-feasible s-t paths within budgets.

Counts include discovered source/sink/dead states and infeasible arc attempts.
Sink states are never expanded. A budget equal to completed work is sufficient.
No dominance pruning, full-path enumeration, or cross-call cache is used.
"""
    if not isinstance(problem, ResourceDagPricingProblem):
        raise TypeError("Pricing requires a ResourceDagPricingProblem.")
    graph = problem.graph
    if not isinstance(dual_values, Mapping):
        raise TypeError("Dual values must be a mapping.")
    if set(dual_values) != set(graph.row_names):
        raise ValueError("Dual keys must exactly match the declared row names.")
    duals = {row: _finite_input(dual_values[row], "Dual value") for row in graph.row_names}
    tolerance = _finite_input(tolerance, "Improvement tolerance")
    if tolerance <= 0:
        raise ValueError("Improvement tolerance must be positive.")
    for name, value in (("state_limit", state_limit), ("transition_limit", transition_limit)):
        if type(value) is not int:
            raise TypeError(f"{name} must be a strict positive integer.")
        if value <= 0:
            raise ValueError(f"{name} must be positive.")

    states = transitions = 0

    def failure(status: ResourceDagPricingStatus, message: str) -> ResourceDagPricingResult:
        return ResourceDagPricingResult(
            status, states_discovered=states, transitions_checked=transitions, message=message,
        )

    try:
        # Precomputation includes every arc, even an unreachable one, as in price_dag.
        base = _sum((graph.base_cost, -_dot(graph.base_coefficients, duals)))
        weights = {arc.arc_id: _sum((arc.cost, -_dot(arc.row_coefficients, duals)))
                   for arc in graph.arcs}
        outgoing: dict[str, list[DagArc]] = {node: [] for node in graph.nodes}
        for arc in sorted(graph.arcs, key=lambda item: item.arc_id):
            outgoing[arc.tail].append(arc)
        labels: dict[str, dict[tuple[int, ...], tuple[float, tuple[str, ...]]]] = {
            node: {} for node in graph.nodes
        }
        labels[graph.source][(0,) * len(problem.resource_limits)] = (base, ())
        states = 1
        for node in _topological_order(graph.nodes, graph.arcs):
            if node == graph.sink:
                continue
            for resources in sorted(labels[node]):
                value, prefix = labels[node][resources]
                for arc in outgoing[node]:
                    if transitions == transition_limit:
                        return failure(ResourceDagPricingStatus.TRANSITION_LIMIT,
                                       "Transition limit reached before the next arc check.")
                    transitions += 1
                    used = tuple(a + b for a, b in zip(
                        resources, problem.arc_resources[arc.arc_id], strict=True,
                    ))
                    if any(a > b for a, b in zip(used, problem.resource_limits, strict=True)):
                        continue
                    current = labels[arc.head].get(used)
                    if current is None and states == state_limit:
                        return failure(ResourceDagPricingStatus.STATE_LIMIT,
                                       "State limit reached before inserting a feasible successor.")
                    candidate = (_sum((value, weights[arc.arc_id])), prefix + (arc.arc_id,))
                    if current is None:
                        labels[arc.head][used] = candidate
                        states += 1
                    elif candidate < current:
                        labels[arc.head][used] = candidate
        if not labels[graph.sink]:
            return failure(ResourceDagPricingStatus.NO_PATH, "No resource-feasible s-t path.")
        resources, (label, arc_ids) = min(labels[graph.sink].items(), key=lambda item: item[1])
        cost, coefficients, reduced_cost, improving, usage = _reconstruct(
            problem, duals, arc_ids, resources, label, tolerance,
        )
        return ResourceDagPricingResult(
            ResourceDagPricingStatus.OPTIMAL, arc_ids=arc_ids, cost=cost,
            row_coefficients=coefficients, reduced_cost=reduced_cost, is_improving=improving,
            resource_usage=usage, states_discovered=states, transitions_checked=transitions,
            message="Minimum label over the complete resource-feasible s-t path domain.",
        )
    except (ArithmeticError, ValueError) as exc:
        return failure(ResourceDagPricingStatus.NUMERICAL_ISSUE, str(exc))


def _reconstruct(problem, duals, arc_ids, resources, label, tolerance):
    """Rebuild the selected column from original arc data, not DP aggregates."""
    graph = problem.graph
    by_id = {arc.arc_id: arc for arc in graph.arcs}
    path = []
    usage = [0] * len(problem.resource_limits)
    node = graph.source
    for arc_id in arc_ids:
        arc = by_id[arc_id]
        if arc.tail != node or node == graph.sink:
            raise _NumericalFailure("Reconstructed path is not a contiguous s-t path.")
        node = arc.head
        path.append(arc)
        for index, increment in enumerate(problem.arc_resources[arc_id]):
            usage[index] += increment
            if usage[index] > problem.resource_limits[index]:
                raise _NumericalFailure("Reconstructed path exceeds a resource limit.")
    if node != graph.sink or tuple(usage) != resources:
        raise _NumericalFailure("Reconstructed endpoint or resource tuple disagrees with DP.")
    cost = _sum([graph.base_cost, *(arc.cost for arc in path)])
    coefficients = {
        row: _sum([graph.base_coefficients.get(row, 0.0),
                   *(arc.row_coefficients.get(row, 0.0) for arc in path)])
        for row in graph.row_names
    }
    reduced_cost = _sum((cost, -_dot(coefficients, duals)))
    if abs(_sum((reduced_cost, -label))) > DEFAULT_TOLERANCE:
        raise _NumericalFailure("Reconstructed reduced cost disagrees with the DP label.")
    improving = reduced_cost < -tolerance
    if improving != (label < -tolerance):
        raise _NumericalFailure("Reconstruction and label disagree on improvement.")
    return cost, coefficients, reduced_cost, improving, tuple(usage)
