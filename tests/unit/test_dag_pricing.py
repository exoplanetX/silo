import ast
from dataclasses import FrozenInstanceError, replace
from math import fsum, inf, nan
from pathlib import Path

import pytest

from silo.decomposition import (
    DagArc,
    DagPricingProblem,
    DagPricingResult,
    DagPricingStatus,
    price_dag,
)


def _example():
    return DagPricingProblem(
        nodes=["s", "a", "b", "t"],
        arcs=[DagArc("sa", "s", "a", 2, {"A": 1}),
              DagArc("at", "a", "t", 3, {"B": 1}),
              DagArc("sb", "s", "b", 1), DagArc("bt", "b", "t", 1),
              DagArc("st", "s", "t", 7, {"A": 1})],
        source="s", sink="t", row_names=["A", "B", "conv"],
        base_cost=1, base_coefficients={"conv": 1},
    )


def _chain(costs, *, base_cost=0, row_names=(), coefficients=None):
    nodes = tuple(str(i) for i in range(len(costs) + 1))
    arcs = [DagArc(f"e{i}", str(i), str(i + 1), cost,
                   {} if coefficients is None else coefficients[i])
            for i, cost in enumerate(costs)]
    return DagPricingProblem(nodes, arcs, nodes[0], nodes[-1], row_names, base_cost)


def _assert_empty(result, status):
    assert result.status == status
    assert result.arc_ids == ()
    assert result.row_coefficients == {}
    assert result.cost is result.reduced_cost is result.is_improving is None
    assert result.message


@pytest.mark.parametrize("pi,path,cost,coefficients,rc,improving", [
    ({"A": 3, "B": 4, "conv": 2}, ("sa", "at"), 6,
     {"A": 1, "B": 1, "conv": 1}, -3, True),
    ({"A": 2, "B": 3, "conv": 1}, ("sa", "at"), 6,
     {"A": 1, "B": 1, "conv": 1}, 0, False),
    ({"A": 1, "B": 1, "conv": 0}, ("sb", "bt"), 3,
     {"A": 0, "B": 0, "conv": 1}, 3, False),
])
def test_hand_paths_and_original_minimum_duals(pi, path, cost, coefficients, rc, improving):
    result = price_dag(_example(), pi)
    assert isinstance(result, DagPricingResult)
    assert result.status == DagPricingStatus.OPTIMAL
    assert result.arc_ids == path
    assert result.cost == cost
    assert result.row_coefficients == coefficients
    assert result.reduced_cost == rc
    assert result.is_improving is improving


def test_negative_prefix_difference_is_not_merged_by_improvement_tolerance():
    problem = DagPricingProblem(
        ["s", "v", "t"], [DagArc("a", "s", "v", 0),
                            DagArc("b", "s", "v", -6e-10),
                            DagArc("tail", "v", "t", -6e-10)], "s", "t",
    )
    result = price_dag(problem, {})
    assert result.arc_ids == ("b", "tail")
    assert result.reduced_cost == -1.2e-9
    assert result.is_improving is True
    relaxed = price_dag(problem, {}, tolerance=2e-9)
    assert relaxed.arc_ids == result.arc_ids
    assert relaxed.reduced_cost == result.reduced_cost
    assert relaxed.is_improving is False


@pytest.mark.parametrize("rc,improving", [(-1e-9, False), (-0.9e-9, False), (-1.1e-9, True)])
def test_final_improvement_uses_strict_threshold(rc, improving):
    result = price_dag(_chain([rc]), {})
    assert result.reduced_cost == rc
    assert result.is_improving is improving


@pytest.mark.parametrize("reverse_nodes", [False, True])
@pytest.mark.parametrize("reverse_arcs", [False, True])
def test_full_path_lexicographic_ties_not_just_last_arc(reverse_nodes, reverse_arcs):
    nodes = ["s", "u", "v", "t"]
    arcs = [DagArc("a", "s", "u", -1), DagArc("z", "u", "t", 1),
            DagArc("b", "s", "v", 0), DagArc("c", "v", "t", 0)]
    problem = DagPricingProblem(nodes[::-1] if reverse_nodes else nodes,
                                arcs[::-1] if reverse_arcs else arcs, "s", "t")
    result = price_dag(problem, {})
    assert result.arc_ids == ("a", "z")
    assert result.reduced_cost == 0
    assert result.is_improving is False


def test_tied_prefix_to_same_vertex_keeps_lexicographically_best_complete_path():
    problem = DagPricingProblem(
        ["s", "u", "v", "m", "t"],
        [DagArc("a", "s", "u", 0), DagArc("z", "u", "m", 0),
         DagArc("b", "s", "v", 0), DagArc("c", "v", "m", 0),
         DagArc("end", "m", "t", 0)], "s", "t",
    )
    assert price_dag(problem, {}).arc_ids == ("a", "z", "end")


def test_parallel_arcs_have_distinct_ids_and_deterministic_tie():
    problem = DagPricingProblem(["s", "t"],
                                [DagArc("z", "s", "t", -2), DagArc("a", "s", "t", -2)],
                                "s", "t")
    assert price_dag(problem, {}).arc_ids == ("a",)


def test_coefficient_insertion_order_does_not_change_dot_product_or_choice():
    values = {"r": 1e16, "s": 1, "t": -1e16}
    results = []
    for coefficients in (values, dict(reversed(list(values.items())))):
        problem = DagPricingProblem(["source", "sink"],
            [DagArc("path", "source", "sink", 0, coefficients)], "source", "sink",
            row_names=["t", "s", "r"])
        results.append(price_dag(problem, {"t": 1, "s": 1, "r": 1}))
    assert results[0] == results[1]
    assert results[0].reduced_cost == -1


def test_source_incoming_sink_outgoing_and_dead_branches_do_not_change_path_domain():
    problem = DagPricingProblem(
        ["before", "s", "v", "t", "after", "dead", "isolated"],
        [DagArc("pre", "before", "s", -100), DagArc("sv", "s", "v", 1),
         DagArc("vt", "v", "t", 2), DagArc("post", "t", "after", -100),
         DagArc("dead", "s", "dead", -100)], "s", "t",
    )
    result = price_dag(problem, {})
    assert result.arc_ids == ("sv", "vt")
    assert result.cost == result.reduced_cost == 3


@pytest.mark.parametrize("arcs", [[], [DagArc("away", "s", "u", -1)]])
def test_no_path_is_distinct_from_non_improving_and_numerical_failure(arcs):
    problem = DagPricingProblem(["s", "u", "t"], arcs, "s", "t")
    _assert_empty(price_dag(problem, {}), DagPricingStatus.NO_PATH)


def test_problem_and_result_defensively_own_sequences_and_mappings():
    coefficients = {"conv": 0}
    base = {"conv": 1}
    arc = DagArc("st", "s", "t", 2, coefficients)
    nodes, arcs, rows = ["s", "t"], [arc], ["conv"]
    problem = DagPricingProblem(nodes, arcs, "s", "t", rows, 1, base)
    coefficients["conv"] = 99
    base.clear()
    nodes.clear()
    arcs.clear()
    rows.clear()
    pi = {"conv": 4}
    before = price_dag(problem, pi)
    pi["conv"] = 1
    after = price_dag(problem, pi)
    assert problem.nodes == ("s", "t")
    assert problem.arcs == (arc,)
    assert problem.row_names == ("conv",)
    assert before.reduced_cost == -1
    assert after.reduced_cost == 2
    assert before.row_coefficients == {"conv": 1}
    for mapping in (arc.row_coefficients, problem.base_coefficients, before.row_coefficients):
        with pytest.raises(TypeError):
            mapping["conv"] = 99
    with pytest.raises(FrozenInstanceError):
        before.cost = 0


@pytest.mark.parametrize("changes", [
    {"nodes": ["s", "s", "t"]}, {"nodes": ["s", " ", "t"]}, {"nodes": ["s"]},
    {"source": "absent"}, {"sink": "absent"}, {"sink": "s"},
    {"row_names": ["conv", "conv"]}, {"row_names": [""]},
    {"arcs": [DagArc("e", "s", "unknown", 0)]},
    {"arcs": [DagArc("e", "s", "t", 0), DagArc("e", "s", "t", 0)]},
    {"arcs": [DagArc("loop", "s", "s", 0)]},
    {"arcs": [DagArc("st", "s", "t", 0), DagArc("ts", "t", "s", 0)]},
    {"nodes": ["s", "t", "u", "v"],
     "arcs": [DagArc("uv", "u", "v", 0), DagArc("vu", "v", "u", 0)]},
    {"base_coefficients": {"unknown": 0}},
    {"arcs": [DagArc("st", "s", "t", 0, {"unknown": 0})]},
])
def test_invalid_graph_and_row_structures_fail_before_pricing(changes):
    arguments = dict(nodes=["s", "t"], arcs=[], source="s", sink="t", row_names=["conv"])
    arguments.update(changes)
    with pytest.raises((ValueError, TypeError)):
        DagPricingProblem(**arguments)


@pytest.mark.parametrize("field", ["arc_id", "tail", "head"])
@pytest.mark.parametrize("bad", ["", " ", None])
def test_arc_ids_are_nonblank_strings(field, bad):
    arguments = dict(arc_id="e", tail="s", head="t", cost=0)
    arguments[field] = bad
    with pytest.raises((ValueError, TypeError)):
        DagArc(**arguments)


@pytest.mark.parametrize("bad", [nan, inf, -inf])
def test_nonfinite_input_numbers_are_rejected(bad):
    with pytest.raises(ValueError, match="finite"):
        DagArc("e", "s", "t", bad)
    with pytest.raises(ValueError, match="finite"):
        DagArc("e", "s", "t", 0, {"row": bad})
    with pytest.raises(ValueError, match="finite"):
        replace(_example(), base_cost=bad)
    with pytest.raises(ValueError, match="finite"):
        replace(_example(), base_coefficients={"conv": bad})
    with pytest.raises(ValueError, match="finite"):
        price_dag(_example(), {"A": 0, "B": 0, "conv": bad})


@pytest.mark.parametrize("pi", [{}, {"A": 1, "B": 2},
                                {"A": 1, "B": 2, "conv": 3, "extra": 0}, []])
def test_dual_coordinates_must_exactly_cover_declared_rows(pi):
    with pytest.raises((ValueError, TypeError)):
        price_dag(_example(), pi)


@pytest.mark.parametrize("tolerance", [0, -1, inf, nan, "bad"])
def test_tolerance_must_be_finite_positive(tolerance):
    with pytest.raises((ValueError, TypeError)):
        price_dag(_example(), {"A": 0, "B": 0, "conv": 0}, tolerance=tolerance)


@pytest.mark.parametrize("kind", ["product", "dot-sum", "weight", "path-sum", "column-sum"])
def test_finite_input_nonfinite_arithmetic_returns_empty_numerical_result(kind):
    if kind == "product":
        problem, pi = _chain([0], row_names=["r"], coefficients=[{"r": 1e308}]), {"r": 1e308}
    elif kind == "dot-sum":
        problem = _chain([0], row_names=["r", "q"], coefficients=[{"r": 1e308, "q": 1e308}])
        pi = {"r": 1, "q": 1}
    elif kind == "weight":
        problem, pi = _chain([1e308], row_names=["r"], coefficients=[{"r": -1e308}]), {"r": 1}
    elif kind == "path-sum":
        problem, pi = _chain([1e308, 1e308]), {}
    else:
        problem = _chain([0, 0], row_names=["r"], coefficients=[{"r": 1e308}, {"r": 1e308}])
        pi = {"r": 0}
    _assert_empty(price_dag(problem, pi), DagPricingStatus.NUMERICAL_ISSUE)


def test_large_cancellation_never_publishes_inconsistent_zero_cost():
    result = price_dag(_chain([1, -1e16], base_cost=1e16), {})
    if result.status == DagPricingStatus.OPTIMAL:
        assert result.cost == result.reduced_cost == 1
    else:
        _assert_empty(result, DagPricingStatus.NUMERICAL_ISSUE)


def test_improvement_disagreement_is_rejected_even_inside_reconstruction_tolerance():
    dp = fsum((fsum((-1e-8, -1e-9)), 1e-8))
    reconstructed = fsum((-1e-8, -1e-9, 1e-8))
    assert abs(dp - reconstructed) < 1e-9
    assert (dp < -1e-9) != (reconstructed < -1e-9)
    _assert_empty(price_dag(_chain([-1e-9, 1e-8], base_cost=-1e-8), {}),
                  DagPricingStatus.NUMERICAL_ISSUE)


def test_production_module_has_only_stdlib_and_utils_dependencies():
    source = Path(__file__).resolve().parents[2] / "src/silo/decomposition/dag_pricing.py"
    tree = ast.parse(source.read_text(encoding="utf-8"))
    allowed = {"collections.abc", "dataclasses", "enum", "heapq", "math", "types",
               "silo.utils.numerics", "__future__"}
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module in allowed
        elif isinstance(node, ast.Import):
            assert all(alias.name in allowed for alias in node.names)
