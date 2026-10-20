from dataclasses import FrozenInstanceError, replace
from math import inf, nan

import pytest

import silo.decomposition.resource_dag_pricing as module
from silo.decomposition import (
    DagArc,
    DagPricingProblem,
    ResourceDagPricingProblem,
    ResourceDagPricingResult,
    ResourceDagPricingStatus,
    price_dag,
    price_resource_dag,
)


def example():
    graph = DagPricingProblem(("s", "u", "t"), (
        DagArc("a", "s", "u", 0), DagArc("b", "s", "u", 1), DagArc("c", "u", "t", 0),
    ), "s", "t")
    return ResourceDagPricingProblem(graph, (2,), {"a": (2,), "b": (0,), "c": (1,)})


def empty(result, status):
    assert result.status == status
    assert result.arc_ids == () and result.row_coefficients == {}
    assert result.cost is result.reduced_cost is result.is_improving is None
    assert result.resource_usage is None
    assert result.message


def test_complete_state_hand_example_and_exact_budget():
    problem = example()
    assert price_dag(problem.graph, {}).arc_ids == ("a", "c")
    result = price_resource_dag(problem, {}, state_limit=4, transition_limit=4)
    assert result.status == ResourceDagPricingStatus.OPTIMAL
    assert result.arc_ids == ("b", "c")
    assert result.cost == result.reduced_cost == 1
    assert result.resource_usage == (1,) and result.is_improving is False
    assert (result.states_discovered, result.transitions_checked) == (4, 4)


@pytest.mark.parametrize("kwargs,status,counts", [
    ({"state_limit": 3}, ResourceDagPricingStatus.STATE_LIMIT, (3, 3)),
    ({"transition_limit": 3}, ResourceDagPricingStatus.TRANSITION_LIMIT, (4, 3)),
    ({"state_limit": 1}, ResourceDagPricingStatus.STATE_LIMIT, (1, 1)),
    ({"transition_limit": 1}, ResourceDagPricingStatus.TRANSITION_LIMIT, (2, 1)),
])
def test_budget_stops_have_no_candidate_even_after_a_sink(kwargs, status, counts):
    result = price_resource_dag(example(), {}, **kwargs)
    empty(result, status)
    assert (result.states_discovered, result.transitions_checked) == counts


def test_same_state_replacement_does_not_consume_new_state_budget():
    problem = example()
    problem = replace(problem, arc_resources={"a": (0,), "b": (0,), "c": (1,)},
                      graph=replace(problem.graph, arcs=(
                          DagArc("a", "s", "u", 5), DagArc("b", "s", "u", -1),
                          DagArc("c", "u", "t", 0))))
    result = price_resource_dag(problem, {}, state_limit=3, transition_limit=3)
    assert result.status == ResourceDagPricingStatus.OPTIMAL
    assert result.arc_ids == ("b", "c") and result.cost == -1
    assert (result.states_discovered, result.transitions_checked) == (3, 3)


def test_strict_labels_and_final_improvement_threshold_are_separate():
    problem = example()
    graph = replace(problem.graph, arcs=(DagArc("a", "s", "u", 0),
                    DagArc("b", "s", "u", -6e-10), DagArc("c", "u", "t", -6e-10)))
    problem = replace(problem, graph=graph, arc_resources=dict.fromkeys(("a", "b", "c"), (0,)))
    result = price_resource_dag(problem, {})
    assert result.arc_ids == ("b", "c") and result.reduced_cost == -1.2e-9
    assert result.is_improving is True
    relaxed = price_resource_dag(problem, {}, tolerance=2e-9)
    assert relaxed.arc_ids == result.arc_ids and relaxed.is_improving is False


def test_two_resources_require_distinct_states_at_one_node():
    problem = replace(example(), resource_limits=(2, 2),
                      arc_resources={"a": (2, 0), "b": (0, 2), "c": (1, 0)})
    result = price_resource_dag(problem, {})
    assert result.arc_ids == ("b", "c") and result.resource_usage == (1, 2)


def test_sink_ties_compare_complete_paths_not_resources():
    graph = DagPricingProblem(("s", "t"), (DagArc("a", "s", "t", 0),
                                          DagArc("b", "s", "t", 0)), "s", "t")
    problem = ResourceDagPricingProblem(graph, (2,), {"a": (2,), "b": (0,)})
    result = price_resource_dag(problem, {})
    assert result.arc_ids == ("a",) and result.resource_usage == (2,)


def test_full_path_ties_and_parallel_arcs_at_same_state():
    graph = DagPricingProblem(("s", "u", "v", "m", "t"), (
        DagArc("a", "s", "u", -1), DagArc("z", "u", "m", 1),
        DagArc("b", "s", "v", 0), DagArc("c", "v", "m", 0),
        DagArc("end", "m", "t", 0), DagArc("zz", "m", "t", 0)), "s", "t")
    problem = ResourceDagPricingProblem(graph, (0,), {a.arc_id: (0,) for a in graph.arcs})
    assert price_resource_dag(problem, {}).arc_ids == ("a", "z", "end")


@pytest.mark.parametrize("capacity", [0, 1])
def test_resource_infeasible_is_no_path_and_counts_rejected_attempts(capacity):
    problem = replace(example(), resource_limits=(capacity,),
                      arc_resources={"a": (2,), "b": (2,), "c": (0,)})
    result = price_resource_dag(problem, {}, state_limit=1, transition_limit=2)
    empty(result, ResourceDagPricingStatus.NO_PATH)
    assert (result.states_discovered, result.transitions_checked) == (1, 2)


def test_unreachable_sink_has_no_candidate():
    graph = DagPricingProblem(("s", "t"), (), "s", "t")
    result = price_resource_dag(ResourceDagPricingProblem(graph, (), {}), {}, state_limit=1)
    empty(result, ResourceDagPricingStatus.NO_PATH)
    assert result.states_discovered == 1 and result.transitions_checked == 0


def test_sink_is_not_expanded_but_dead_states_are_counted():
    graph = DagPricingProblem(("s", "t", "z", "dead"), (
        DagArc("a", "s", "t", 1), DagArc("b", "s", "dead", 0),
        DagArc("c", "t", "z", 1e308), DagArc("d", "z", "dead", 1e308)), "s", "t")
    problem = ResourceDagPricingProblem(graph, (), {a.arc_id: () for a in graph.arcs})
    result = price_resource_dag(problem, {}, state_limit=3, transition_limit=2)
    assert result.status == ResourceDagPricingStatus.OPTIMAL and result.arc_ids == ("a",)
    assert (result.states_discovered, result.transitions_checked) == (3, 2)


@pytest.mark.parametrize("capacity", [2**53, 2**100])
def test_resource_arithmetic_preserves_integers_beyond_float_precision(capacity):
    problem = replace(example(), resource_limits=(capacity,),
                      arc_resources={"a": (capacity,), "b": (capacity - 1,), "c": (1,)})
    result = price_resource_dag(problem, {})
    assert result.arc_ids == ("b", "c") and result.resource_usage == (capacity,)


def test_zero_dimension_and_nonbinding_resources_agree_with_ordinary_pricing():
    graph = example().graph
    ordinary = price_dag(graph, {})
    for cap, resources in (((), dict.fromkeys(("a", "b", "c"), ())),
                           ((100,), example().arc_resources)):
        result = price_resource_dag(ResourceDagPricingProblem(graph, cap, resources), {})
        assert result.arc_ids == ordinary.arc_ids
        assert result.cost == ordinary.cost and result.reduced_cost == ordinary.reduced_cost


def test_original_columns_base_terms_and_dual_updates_are_cold_snapshots():
    graph = DagPricingProblem(("s", "t"), (DagArc("a", "s", "t", 1, {"R": 1}),
                                          DagArc("b", "s", "t", -1, {"R": -1})),
                              "s", "t", ("R", "conv", "zero"), 2, {"conv": 1})
    data = {"a": (0,), "b": (1,)}
    problem = ResourceDagPricingProblem(graph, (1,), data)
    data["a"] = (100,)
    first = price_resource_dag(problem, {"R": 3, "conv": 2, "zero": 0})
    second = price_resource_dag(problem, {"R": -3, "conv": 2, "zero": 0})
    again = price_resource_dag(problem, {"R": 3, "conv": 2, "zero": 0})
    assert first == again and first.arc_ids == ("a",) and second.arc_ids == ("b",)
    assert first.cost == 3 and first.row_coefficients == {"R": 1, "conv": 1, "zero": 0}
    assert first.reduced_cost == -2 and first.resource_usage == (0,)
    with pytest.raises(TypeError):
        problem.arc_resources["a"] = (2,)
    with pytest.raises(TypeError):
        first.row_coefficients["R"] = 5
    with pytest.raises(FrozenInstanceError):
        problem.graph = graph
    with pytest.raises(FrozenInstanceError):
        first.states_discovered = 500


def test_result_defensively_copies_user_provided_data():
    rows = {"r": 1}
    result = ResourceDagPricingResult(ResourceDagPricingStatus.OPTIMAL,
                                      arc_ids=["a"], row_coefficients=rows, resource_usage=[1])
    rows["r"] = 2
    assert result.row_coefficients == {"r": 1}
    assert result.arc_ids == ("a",) and result.resource_usage == (1,)


@pytest.mark.parametrize("limits", [[2], (True,), (2.0,), (-1,), "2", None])
def test_invalid_resource_limits(limits):
    with pytest.raises((TypeError, ValueError)):
        replace(example(), resource_limits=limits)


@pytest.mark.parametrize("resources", [
    None, [], {}, {"a": (0,), "b": (0,)},
    {"a": (0,), "b": (0,), "c": (0,), "extra": (0,)},
    {"a": [0], "b": (0,), "c": (0,)},
    {"a": (True,), "b": (0,), "c": (0,)},
    {"a": (0.0,), "b": (0,), "c": (0,)},
    {"a": (-1,), "b": (0,), "c": (0,)},
    {"a": (), "b": (0,), "c": (0,)},
])
def test_invalid_arc_resources(resources):
    with pytest.raises((TypeError, ValueError)):
        replace(example(), arc_resources=resources)


def test_invalid_graph_and_problem_types():
    with pytest.raises(TypeError):
        replace(example(), graph=None)
    with pytest.raises(TypeError):
        price_resource_dag(example().graph, {})


@pytest.mark.parametrize("name", ["state_limit", "transition_limit"])
@pytest.mark.parametrize("value", [True, 1.0, "1", None, 0, -1, inf, nan])
def test_invalid_budgets_rejected_before_search(name, value):
    with pytest.raises((TypeError, ValueError)):
        price_resource_dag(example(), {}, **{name: value})


@pytest.mark.parametrize("tolerance", [0, -1, nan, inf, "bad", None])
def test_invalid_tolerances(tolerance):
    with pytest.raises(ValueError):
        price_resource_dag(example(), {}, tolerance=tolerance)


@pytest.mark.parametrize("duals", [None, [], {"extra": 0}])
def test_invalid_dual_mapping_or_keys(duals):
    with pytest.raises((TypeError, ValueError)):
        price_resource_dag(example(), duals)


@pytest.mark.parametrize("value", [nan, inf, -inf, "bad", None])
def test_nonfinite_duals_raise_before_arithmetic(value):
    problem = replace(example(), graph=replace(example().graph, row_names=("R",)))
    with pytest.raises(ValueError):
        price_resource_dag(problem, {"R": value})


def test_full_arc_precomputation_failure_precedes_source_discovery():
    graph = DagPricingProblem(("s", "t", "u", "v"), (
        DagArc("a", "s", "t", 0), DagArc("dead", "u", "v", 0, {"r": 1e308})),
                              "s", "t", ("r",))
    problem = ResourceDagPricingProblem(graph, (), {"a": (), "dead": ()})
    result = price_resource_dag(problem, {"r": 1e308})
    empty(result, ResourceDagPricingStatus.NUMERICAL_ISSUE)
    assert (result.states_discovered, result.transitions_checked) == (0, 0)


def test_nonfinite_label_arithmetic_is_numerical_issue():
    graph = replace(example().graph, arcs=(DagArc("a", "s", "u", 1e308),
                    DagArc("b", "s", "u", 1e308), DagArc("c", "u", "t", 1e308)))
    problem = replace(example(), graph=graph)
    empty(price_resource_dag(problem, {}), ResourceDagPricingStatus.NUMERICAL_ISSUE)


def test_natural_cancellation_disagreement_is_numerical_issue():
    graph = DagPricingProblem(("s", "a", "b", "t"), (
        DagArc("a", "s", "a", 1e16), DagArc("b", "a", "b", 1),
        DagArc("c", "b", "t", -1e16)), "s", "t")
    problem = ResourceDagPricingProblem(graph, (), {arc.arc_id: () for arc in graph.arcs})
    result = price_resource_dag(problem, {})
    empty(result, ResourceDagPricingStatus.NUMERICAL_ISSUE)
    assert "disagrees" in result.message


def test_missing_dual_row_is_invalid_input():
    graph = replace(example().graph, row_names=("R",))
    with pytest.raises(ValueError):
        price_resource_dag(replace(example(), graph=graph), {})


@pytest.mark.parametrize("label_shift,message", [(2e-9, "disagrees"),
                                                 (0.5e-9, "improvement")])
def test_reconstruction_mismatch_and_improvement_disagreement_fail_closed(monkeypatch,
                                                                        label_shift, message):
    graph = DagPricingProblem(("s", "t"), (DagArc("e", "s", "t", -1.25e-9),), "s", "t")
    problem = ResourceDagPricingProblem(graph, (), {"e": ()})
    original = module._reconstruct

    def shifted(problem, duals, arc_ids, resources, label, tolerance):
        return original(problem, duals, arc_ids, resources, label + label_shift, tolerance)

    monkeypatch.setattr(module, "_reconstruct", shifted)
    result = price_resource_dag(problem, {})
    empty(result, ResourceDagPricingStatus.NUMERICAL_ISSUE)
    assert message in result.message
    assert (result.states_discovered, result.transitions_checked) == (2, 1)
