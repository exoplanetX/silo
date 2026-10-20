"""Run with: python examples/resource_dag_pricing.py."""

from silo.decomposition import (
    DagArc,
    DagPricingProblem,
    ResourceDagPricingProblem,
    ResourceDagPricingStatus,
    price_resource_dag,
)


def main():
    graph = DagPricingProblem(("s", "u", "t"), (
        DagArc("a", "s", "u", 0), DagArc("b", "s", "u", 1), DagArc("c", "u", "t", 0),
    ), "s", "t")
    problem = ResourceDagPricingProblem(graph, (2,), {"a": (2,), "b": (0,), "c": (1,)})
    result = price_resource_dag(problem, {}, state_limit=4, transition_limit=4)
    assert result.status == ResourceDagPricingStatus.OPTIMAL
    assert result.arc_ids == ("b", "c") and result.cost == result.reduced_cost == 1
    assert result.resource_usage == (1,) and result.is_improving is False
    assert (result.states_discovered, result.transitions_checked) == (4, 4)
    # Independent second resource: b consumes two units; a cannot take the suffix.
    two = ResourceDagPricingProblem(graph, (2, 2), {"a": (2, 0), "b": (0, 2), "c": (1, 0)})
    answer = price_resource_dag(two, {})
    assert answer.arc_ids == ("b", "c") and answer.resource_usage == (1, 2)
    for kwargs, status in (({"state_limit": 3}, ResourceDagPricingStatus.STATE_LIMIT),
                           ({"transition_limit": 3}, ResourceDagPricingStatus.TRANSITION_LIMIT)):
        limited = price_resource_dag(problem, {}, **kwargs)
        assert limited.status == status and limited.is_improving is None
        assert limited.arc_ids == () and limited.resource_usage is None
    print("path=b,c cost=1 resources=(1,); states=4 transitions=4; two resources=(1,2)")


if __name__ == "__main__":
    main()
