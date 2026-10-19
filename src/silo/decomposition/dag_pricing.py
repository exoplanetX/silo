"""All-s-t-path pricing on a finite ordinary DAG, using original MIN duals.

Topological labels cover the whole graph-defined path domain. Floating-point
checks protect published candidates; they do not establish symbolic exactness.
"""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import Enum
from heapq import heapify, heappop, heappush
from math import fsum, isfinite
from types import MappingProxyType

from silo.utils.numerics import DEFAULT_TOLERANCE


class DagPricingStatus(str, Enum):
    OPTIMAL = "optimal"
    NO_PATH = "no_path"
    NUMERICAL_ISSUE = "numerical_issue"


@dataclass(frozen=True)
class DagArc:
    arc_id: str
    tail: str
    head: str
    cost: float
    row_coefficients: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for name in ("arc_id", "tail", "head"):
            _validate_id(getattr(self, name), name)
        object.__setattr__(self, "cost", _finite_input(self.cost, "Arc cost"))
        object.__setattr__(self, "row_coefficients", _coefficient_copy(self.row_coefficients))


@dataclass(frozen=True)
class DagPricingProblem:
    nodes: tuple[str, ...]
    arcs: tuple[DagArc, ...]
    source: str
    sink: str
    row_names: tuple[str, ...] = ()
    base_cost: float = 0.0
    base_coefficients: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self) -> None:
        nodes = _id_sequence(self.nodes, "Node")
        rows = _id_sequence(self.row_names, "Row")
        if isinstance(self.arcs, str | bytes):
            raise TypeError("Arcs must be an iterable of DagArc records.")
        arcs = tuple(self.arcs)
        if any(not isinstance(arc, DagArc) for arc in arcs):
            raise TypeError("Arcs must contain only DagArc records.")
        if len({arc.arc_id for arc in arcs}) != len(arcs):
            raise ValueError("Arc IDs must be unique.")
        for name in ("source", "sink"):
            _validate_id(getattr(self, name), name)
        if self.source not in nodes or self.sink not in nodes or self.source == self.sink:
            raise ValueError("Source and sink must be distinct declared nodes.")
        node_set = set(nodes)
        row_set = set(rows)
        base = _coefficient_copy(self.base_coefficients)
        if set(base) - row_set:
            raise ValueError("Base coefficients contain unknown rows.")
        for arc in arcs:
            if arc.tail not in node_set or arc.head not in node_set:
                raise ValueError(f"Arc {arc.arc_id!r} has an unknown endpoint.")
            if set(arc.row_coefficients) - row_set:
                raise ValueError(f"Arc {arc.arc_id!r} contains unknown rows.")
        _topological_order(nodes, arcs)  # Validate every component, including unreachable cycles.
        object.__setattr__(self, "nodes", nodes)
        object.__setattr__(self, "arcs", arcs)
        object.__setattr__(self, "row_names", rows)
        object.__setattr__(self, "base_cost", _finite_input(self.base_cost, "Base cost"))
        object.__setattr__(self, "base_coefficients", base)


@dataclass(frozen=True)
class DagPricingResult:
    """An immutable path/column snapshot; check status before is_improving.

    OPTIMAL includes non-improving paths. Failure/empty-domain fields are None
    or empty, so an unknown improvement result cannot be confused with False.
    """

    status: DagPricingStatus
    arc_ids: tuple[str, ...] = ()
    cost: float | None = None
    row_coefficients: Mapping[str, float] = field(default_factory=dict)
    reduced_cost: float | None = None
    is_improving: bool | None = None
    message: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "arc_ids", tuple(self.arc_ids))
        object.__setattr__(self, "row_coefficients", MappingProxyType(dict(self.row_coefficients)))


def price_dag(
    problem: DagPricingProblem,
    dual_values: Mapping[str, float],
    *,
    tolerance: float = DEFAULT_TOLERANCE,
) -> DagPricingResult:
    """Find the minimum reduced-cost s-t path for this MIN dual snapshot.

    Labels use strict comparisons; exact ties use complete arc-ID tuples.
    tolerance affects only final improvement classification, never relaxation.
    """
    if not isinstance(problem, DagPricingProblem):
        raise TypeError("Pricing requires a DagPricingProblem.")
    if not isinstance(dual_values, Mapping):
        raise TypeError("Dual values must be a mapping.")
    if set(dual_values) != set(problem.row_names):
        raise ValueError("Dual keys must exactly match the declared row names.")
    duals = {row: _finite_input(dual_values[row], "Dual value") for row in problem.row_names}
    tolerance = _finite_input(tolerance, "Improvement tolerance")
    if tolerance <= 0:
        raise ValueError("Improvement tolerance must be positive.")

    try:
        base_weight = _sum((problem.base_cost, -_dot(problem.base_coefficients, duals)))
        weights = {arc.arc_id: _sum((arc.cost, -_dot(arc.row_coefficients, duals)))
                   for arc in problem.arcs}
        outgoing: dict[str, list[DagArc]] = {node: [] for node in problem.nodes}
        for arc in sorted(problem.arcs, key=lambda item: item.arc_id):
            outgoing[arc.tail].append(arc)
        labels: dict[str, tuple[float, tuple[str, ...]]] = {
            problem.source: (base_weight, ()),
        }
        for node in _topological_order(problem.nodes, problem.arcs):
            if node not in labels:
                continue
            value, prefix = labels[node]
            for arc in outgoing[node]:
                candidate = (_sum((value, weights[arc.arc_id])), prefix + (arc.arc_id,))
                current = labels.get(arc.head)
                # Tuple ordering gives strict numeric order, then the full-path tie rule.
                if current is None or candidate < current:
                    labels[arc.head] = candidate
        if problem.sink not in labels:
            return DagPricingResult(DagPricingStatus.NO_PATH, message="No source-to-sink path.")

        label, arc_ids = labels[problem.sink]
        by_id = {arc.arc_id: arc for arc in problem.arcs}
        path = [by_id[arc_id] for arc_id in arc_ids]
        # Rebuild from original data, independently of reduced weights and labels.
        cost = _sum([problem.base_cost, *(arc.cost for arc in path)])
        coefficients = {
            row: _sum([problem.base_coefficients.get(row, 0.0),
                       *(arc.row_coefficients.get(row, 0.0) for arc in path)])
            for row in problem.row_names
        }
        reduced_cost = _sum((cost, -_dot(coefficients, duals)))
        if abs(_sum((reduced_cost, -label))) > DEFAULT_TOLERANCE:
            raise _NumericalFailure("Reconstructed reduced cost disagrees with the DP label.")
        improving = reduced_cost < -tolerance
        if improving != (label < -tolerance):
            raise _NumericalFailure("Reconstruction and label disagree on improvement.")
        return DagPricingResult(
            status=DagPricingStatus.OPTIMAL, arc_ids=arc_ids, cost=cost,
            row_coefficients=coefficients, reduced_cost=reduced_cost, is_improving=improving,
            message="Minimum reduced-cost path over all graph-defined s-t paths.",
        )
    except (ArithmeticError, ValueError) as exc:
        return DagPricingResult(DagPricingStatus.NUMERICAL_ISSUE, message=str(exc))


def _topological_order(nodes: tuple[str, ...], arcs: tuple[DagArc, ...]) -> list[str]:
    indegree = dict.fromkeys(nodes, 0)
    outgoing: dict[str, list[str]] = {node: [] for node in nodes}
    for arc in arcs:
        indegree[arc.head] += 1
        outgoing[arc.tail].append(arc.head)
    ready = [node for node in nodes if indegree[node] == 0]
    heapify(ready)
    order = []
    while ready:
        node = heappop(ready)
        order.append(node)
        for head in outgoing[node]:
            indegree[head] -= 1
            if indegree[head] == 0:
                heappush(ready, head)
    if len(order) != len(nodes):
        raise ValueError("Pricing graph must be acyclic in every component.")
    return order


def _id_sequence(values: Iterable[str], label: str) -> tuple[str, ...]:
    if isinstance(values, str | bytes):
        raise TypeError(f"{label} IDs require an iterable of strings.")
    result = tuple(values)
    for value in result:
        _validate_id(value, label)
    if len(set(result)) != len(result):
        raise ValueError(f"{label} IDs must be unique.")
    return result


def _validate_id(value: str, label: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} must be a nonblank string.")


def _coefficient_copy(values: Mapping[str, float]) -> Mapping[str, float]:
    if not isinstance(values, Mapping):
        raise TypeError("Coefficients must be a mapping.")
    copied = {}
    for row, value in values.items():
        _validate_id(row, "Coefficient row name")
        copied[row] = _finite_input(value, "Coefficient")
    return MappingProxyType(copied)


def _finite_input(value: float, label: str) -> float:
    try:
        numeric = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"{label} must be a finite number.") from exc
    if not isfinite(numeric):
        raise ValueError(f"{label} must be finite.")
    return numeric


class _NumericalFailure(ArithmeticError):
    pass


def _sum(values: Iterable[float]) -> float:
    value = fsum(values)
    if not isfinite(value):
        raise _NumericalFailure("Nonfinite arithmetic in DAG pricing.")
    return value


def _dot(coefficients: Mapping[str, float], duals: Mapping[str, float]) -> float:
    products = []
    for row in sorted(coefficients):
        product = coefficients[row] * duals[row]
        if not isfinite(product):
            raise _NumericalFailure("Nonfinite row/dual product in DAG pricing.")
        products.append(product)
    return _sum(products)
