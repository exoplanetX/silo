"""Independent exhaustive path truth on the contract's fixed dyadic family."""

from fractions import Fraction

import pytest

from silo.decomposition import (
    DagArc,
    DagPricingProblem,
    ResourceDagPricingProblem,
    ResourceDagPricingStatus,
    price_dag,
    price_resource_dag,
)

PAIRS = (("s", "a"), ("s", "b"), ("s", "t"),
         ("a", "b"), ("a", "t"), ("b", "t"))
DUALS = ({"R": -0.5, "conv": -0.25}, {"R": 0, "conv": 0},
         {"R": 0.75, "conv": 0.5})


def enumerate_truth(problem, duals):
    # Raw-data DFS: no production transition, topology, reconstruction or sum helpers.
    graph = problem.graph
    pending = [(graph.source, ())]
    feasible = []
    while pending:
        node, path = pending.pop()
        if node != graph.sink:
            pending.extend((arc.head, path + (arc,)) for arc in graph.arcs if arc.tail == node)
            continue
        usage = tuple(sum(problem.arc_resources[arc.arc_id][j] for arc in path)
                      for j in range(len(problem.resource_limits)))
        if any(value > limit for value, limit in zip(usage, problem.resource_limits, strict=True)):
            continue
        cost = Fraction(graph.base_cost) + sum(Fraction(arc.cost) for arc in path)
        rows = {row: Fraction(graph.base_coefficients.get(row, 0))
                + sum(Fraction(arc.row_coefficients.get(row, 0)) for arc in path)
                for row in graph.row_names}
        rc = cost - sum(rows[row] * Fraction(duals[row]) for row in graph.row_names)
        feasible.append((rc, tuple(arc.arc_id for arc in path), cost, rows, usage))
    return feasible


@pytest.mark.parametrize("mask", range(64))
@pytest.mark.parametrize("resource_kind", range(3))
@pytest.mark.parametrize("duals", DUALS)
@pytest.mark.parametrize("reverse", [False, True])
def test_1152_cold_calls_against_independent_fraction_truth(mask, resource_kind, duals, reverse):
    arcs = [DagArc(f"e{j}", tail, head, ((3 * j) % 7 - 3) / 4,
                   {"R": ((j % 3) - 1) / 2})
            for j, (tail, head) in enumerate(PAIRS) if mask & (1 << j)]
    capacities = ((), (2,), (2, 2))[resource_kind]
    resources = {f"e{j}": ((), (j % 3,), (j % 2, (j // 2) % 2))[resource_kind]
                 for j in range(6) if mask & (1 << j)}
    nodes, rows, base = ("s", "a", "b", "t"), ("R", "conv"), {"R": 0.125, "conv": 1}
    if reverse:
        nodes, arcs, rows = nodes[::-1], arcs[::-1], rows[::-1]
        base, duals = dict(reversed(list(base.items()))), dict(reversed(list(duals.items())))
        resources = dict(reversed(list(resources.items())))
    graph = DagPricingProblem(nodes, arcs, "s", "t", rows, 0.25, base)
    problem = ResourceDagPricingProblem(graph, capacities, resources)
    truth = enumerate_truth(problem, duals)
    result = price_resource_dag(problem, duals)
    if not truth:
        assert result.status == ResourceDagPricingStatus.NO_PATH
        assert result.arc_ids == () and result.row_coefficients == {}
        assert result.cost is result.reduced_cost is result.is_improving is None
        assert result.resource_usage is None
    else:
        optimum = min(item[0] for item in truth)
        optimal_set = [item for item in truth if item[0] == optimum]
        rc, path, cost, coefficients, usage = min(optimal_set, key=lambda item: item[1])
        assert result.status == ResourceDagPricingStatus.OPTIMAL
        assert result.arc_ids == path
        assert result.cost == float(cost)
        assert result.row_coefficients == {row: float(value) for row, value in coefficients.items()}
        assert result.reduced_cost == float(rc)
        assert result.resource_usage == usage
        assert result.is_improving is (rc < -Fraction(1, 10**9))
    if resource_kind == 0:
        ordinary = price_dag(graph, duals)
        assert result.status.value == ordinary.status.value
        for field in ("arc_ids", "cost", "row_coefficients", "reduced_cost", "is_improving"):
            assert getattr(result, field) == getattr(ordinary, field)
