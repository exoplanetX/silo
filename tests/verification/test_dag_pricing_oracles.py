from fractions import Fraction

import pytest

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.decomposition import DagArc, DagPricingProblem, DagPricingStatus, price_dag
from silo.decomposition.restricted_master import RestrictedMasterProblem
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver

PAIRS = ((0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3))
DUALS = ({"r": 2, "q": -1, "conv": 3},
         {"r": -1, "q": 2, "conv": -2}, {"r": 0, "q": 0, "conv": 0})


def _all_paths(problem, pi):
    # Independent exhaustive DFS: no production topological/weight/rebuild helpers.
    outgoing = {node: [] for node in problem.nodes}
    for arc in problem.arcs:
        outgoing[arc.tail].append(arc)
    pending = [(problem.source, ())]
    complete = []
    while pending:
        node, path = pending.pop()
        if node == problem.sink:
            cost = Fraction(problem.base_cost) + sum(Fraction(arc.cost) for arc in path)
            coefficients = {
                row: Fraction(problem.base_coefficients.get(row, 0))
                + sum(Fraction(arc.row_coefficients.get(row, 0)) for arc in path)
                for row in problem.row_names
            }
            rc = cost - sum(coefficients[row] * Fraction(pi[row]) for row in problem.row_names)
            complete.append((rc, tuple(arc.arc_id for arc in path), cost, coefficients))
        else:
            pending.extend((arc.head, path + (arc,)) for arc in outgoing[node])
    return complete


def _assert_oracle(problem, pi):
    all_paths = _all_paths(problem, pi)
    result = price_dag(problem, pi)
    if not all_paths:
        assert result.status == DagPricingStatus.NO_PATH
        assert result.arc_ids == () and result.row_coefficients == {}
        assert result.cost is result.reduced_cost is result.is_improving is None
        return
    rc, arc_ids, cost, coefficients = min(all_paths, key=lambda item: (item[0], item[1]))
    assert result.status == DagPricingStatus.OPTIMAL
    assert result.arc_ids == arc_ids
    assert result.cost == float(cost)
    assert result.row_coefficients == {row: float(value) for row, value in coefficients.items()}
    assert result.reduced_cost == float(rc)
    assert result.is_improving is (rc < Fraction(1, -10**9))
    by_id = {arc.arc_id: arc for arc in problem.arcs}
    node = problem.source
    for arc_id in result.arc_ids:
        assert by_id[arc_id].tail == node
        node = by_id[arc_id].head
    assert node == problem.sink


@pytest.mark.parametrize("mask", range(64))
@pytest.mark.parametrize("pi", DUALS)
def test_all_64_forward_subgraphs_against_complete_fraction_path_enumeration(mask, pi):
    costs = (-1, 2, 3, 0, -2, 1)
    arcs = [DagArc(f"e{i}", str(u), str(v), costs[i], {"r": i % 2, "q": (i % 3) - 1})
            for i, (u, v) in enumerate(PAIRS) if mask & (1 << i)]
    problem = DagPricingProblem(["0", "1", "2", "3"], arcs, "0", "3",
                                row_names=["r", "q", "conv"],
                                base_cost=1, base_coefficients={"conv": 1})
    _assert_oracle(problem, pi)


@pytest.mark.parametrize("row_names,base,pi", [
    ([], {}, {}), (["conv"], {"conv": 1}, {"conv": 3}),
    (["q", "r"], {"r": -2}, {"r": -1, "q": 2}),
])
def test_parallel_paths_base_terms_and_input_orders_against_oracle(row_names, base, pi):
    arcs = [DagArc("a", "s", "v", 0), DagArc("b", "s", "v", 0),
            DagArc("z", "v", "t", -1), DagArc("c", "s", "t", -1)]
    for nodes, edges in ((["s", "v", "t"], arcs), (["t", "v", "s"], arcs[::-1])):
        _assert_oracle(DagPricingProblem(nodes, edges, "s", "t", row_names, 2, base), pi)


@pytest.mark.parametrize("backend", [RevisedSimplexSolver, TableauSimplexSolver])
def test_manual_rmp_price_add_resolve_bridge_keeps_global_constant_out_of_pricing(backend):
    graph = DagPricingProblem(
        ["s", "a", "b", "t"],
        [DagArc("sa", "s", "a", 1), DagArc("at", "a", "t", 3),
         DagArc("sb", "s", "b", 1), DagArc("bt", "b", "t", 1)],
        "s", "t", ["conv"], base_cost=1, base_coefficients={"conv": 1},
    )
    seed = Model(variables=[Variable("A")],
                 constraints=[Constraint("conv", {"A": 1}, ConstraintSense.EQ, 1)],
                 objective=Objective({"A": 5}, OptimizationSense.MINIMIZE, constant=7))
    rmp = RestrictedMasterProblem(seed)
    initial = rmp.solve(backend())
    assert initial.status == SolverStatus.OPTIMAL
    assert initial.objective_value == 12
    assert initial.dual_values == {"conv": 5}
    priced = price_dag(graph, initial.dual_values)
    assert priced.status == DagPricingStatus.OPTIMAL
    assert priced.arc_ids == ("sb", "bt")
    assert priced.cost == 3 and priced.row_coefficients == {"conv": 1}
    assert priced.reduced_cost == -2 and priced.is_improving is True
    _assert_oracle(graph, initial.dual_values)
    rmp.add_column(name="B", cost=priced.cost, row_coefficients=priced.row_coefficients)
    after = rmp.solve(backend())
    assert after.status == SolverStatus.OPTIMAL
    assert after.objective_value == 10 and after.dual_values == {"conv": 3}
    assert after.primal_values == {"A": 0, "B": 1}
    final = price_dag(graph, after.dual_values)
    assert final.status == DagPricingStatus.OPTIMAL
    assert final.arc_ids == priced.arc_ids  # Existing paths remain in the pricing domain.
    assert final.reduced_cost == 0 and final.is_improving is False
    _assert_oracle(graph, after.dual_values)
