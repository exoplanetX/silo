"""216 complete CG runs, checked against independent raw-data Fraction vertices."""

from collections import Counter
from fractions import Fraction
from itertools import combinations
from math import fsum, ulp

import pytest

from silo.core.enums import ConstraintSense as S
from silo.decomposition import (
    DagArc,
    DagColumnGenerationProblem,
    DagColumnGenerationStatus,
    DagMasterRow,
    DagPricingProblem,
    ResourceDagPricingProblem,
    ResourceDagPricingStatus,
    solve_resource_dag_column_generation,
)
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver

COSTS = ((4, 1, 3, 6), (0, 2, 1, 0), (-2, 1, -1, 3), (0, 0, 0, 0),
         (1.75, -0.5, 1.25, 2.25), (6, 4, 2, 0))


@pytest.fixture(scope="module")
def observations(request):
    counts = {mode: Counter() for mode in ("revised", "tableau", "reuse")}
    yield counts
    reporter = request.config.pluginmanager.getplugin("terminalreporter")
    if reporter is not None:
        reporter.write_line(f"Resource CG observed calls/rounds/RMP: {counts}")


def family(index, alpha, sign, reverse):
    arcs = [DagArc(f"p{i}", "s", "u", cost, {"R": sign * i})
            for i, cost in enumerate(COSTS[index])]
    arcs += [DagArc("x", "s", "u", -20, {"R": sign * 1.5}), DagArc("z", "u", "t", 0)]
    rows = [DagMasterRow("conv", S.EQ, 1), DagMasterRow("R", S.EQ, sign * (alpha + 0.125))]
    row_names, base = ("R", "conv"), {"R": sign * 0.125, "conv": 1}
    nodes, seeds = ("s", "u", "t"), (("p0", "z"), ("p3", "z"))
    resources = {f"p{i}": (i % 2,) for i in range(4)} | {"x": (2,), "z": (1,)}
    if reverse:
        nodes, arcs, rows, seeds = nodes[::-1], arcs[::-1], rows[::-1], seeds[::-1]
        row_names, base = row_names[::-1], dict(reversed(list(base.items())))
        resources = dict(reversed(list(resources.items())))
    graph = DagPricingProblem(nodes, arcs, "s", "t", row_names, 0.375, base)
    problem = DagColumnGenerationProblem(graph, rows, "conv", seeds, 7 if index % 2 == 0 else -3)
    return problem, ResourceDagPricingProblem(graph, (2,), resources)


def raw_columns(resources):
    # Independent DFS, integer aggregation and Fraction column construction.
    # No production topology/transition/price/reconstruction helpers supply truth.
    graph = resources.graph
    pending, columns = [(graph.source, ())], {}
    while pending:
        node, path = pending.pop()
        if node != graph.sink:
            pending.extend((arc.head, path + (arc,)) for arc in graph.arcs if arc.tail == node)
            continue
        usage = tuple(sum(resources.arc_resources[arc.arc_id][j] for arc in path)
                      for j in range(len(resources.resource_limits)))
        if any(usage[j] > resources.resource_limits[j] for j in range(len(usage))):
            continue
        cost = Fraction(graph.base_cost) + sum(Fraction(arc.cost) for arc in path)
        rows = {row: Fraction(graph.base_coefficients.get(row, 0))
                + sum(Fraction(arc.row_coefficients.get(row, 0)) for arc in path)
                for row in graph.row_names}
        columns[tuple(arc.arc_id for arc in path)] = cost, rows, usage
    return columns


def vertex_optimum(problem, columns, paths):
    # All feasible two-column bracketing vertices, in original (possibly flipped) R coordinates.
    rhs = Fraction(next(row.rhs for row in problem.rows if row.name == "R"))
    values = []
    for left, right in combinations(paths, 2):
        cl, al, _ = columns[left]
        cr, ar, _ = columns[right]
        if al["R"] == ar["R"]:
            continue
        weight = (ar["R"] - rhs) / (ar["R"] - al["R"])
        if 0 <= weight <= 1:
            values.append(Fraction(problem.objective_constant) + weight * cl + (1 - weight) * cr)
    assert values
    return min(values)


def near(actual, expected):
    assert actual == pytest.approx(float(expected), rel=0, abs=1e-9)


def audit_round(problem, record, columns, full_optimum):
    registry = record.column_paths
    master = record.master_result
    x, pi = master.primal_values, master.dual_values
    assert set(x) == set(registry)
    assert set(pi) == set(problem.graph.row_names)
    assert all(path in columns for path in registry.values())
    assert all(value >= -1e-9 for value in x.values())
    for row in problem.rows:
        activity = sum(columns[path][1][row.name] * Fraction(x[name])
                       for name, path in registry.items())
        near(activity, row.rhs)
    current_optimum = vertex_optimum(problem, columns, registry.values())
    near(master.objective_value, current_optimum)
    exact_prices = {
        path: cost - sum(a[row] * Fraction(pi[row]) for row in a)
        for path, (cost, a, _) in columns.items()
    }
    for name, path in registry.items():
        near(master.reduced_costs[name], exact_prices[path])
        assert exact_prices[path] >= -Fraction(1, 10**9)
        near(Fraction(x[name]) * exact_prices[path], 0)
    original_dual = Fraction(problem.objective_constant) + sum(
        Fraction(row.rhs) * Fraction(pi[row.name]) for row in problem.rows)
    near(original_dual, current_optimum)
    near(master.objective_value, original_dual)
    priced = record.pricing_result
    assert priced.status == ResourceDagPricingStatus.OPTIMAL
    cost, rows, usage = columns[priced.arc_ids]
    near(priced.cost, cost)
    assert priced.row_coefficients == {row: float(value) for row, value in rows.items()}
    assert priced.resource_usage == usage
    near(priced.reduced_cost, exact_prices[priced.arc_ids])
    near(priced.reduced_cost, min(exact_prices.values()))
    near(record.rho, min(exact_prices.values()))
    assert priced.is_improving is (priced.reduced_cost < -1e-9)
    primal_terms = [float(columns[path][0]) * x[name] for name, path in registry.items()]
    dual_terms = [row.rhs * pi[row.name] for row in problem.rows]
    delta = min(0, record.rho)
    upper = fsum([problem.objective_constant, *primal_terms])
    dual = fsum([problem.objective_constant, *dual_terms])
    lower = fsum([problem.objective_constant, *dual_terms, delta])
    gap = fsum([*primal_terms, *(-term for term in dual_terms), -delta])
    absolute = fsum([*(abs(term) for term in primal_terms),
                     *(abs(term) for term in dual_terms), abs(delta)])
    assert record.numerical_upper_bound == upper
    assert record.dual_objective == dual
    assert record.numerical_lower_bound == lower
    assert record.numerical_gap == fsum((upper, -lower))
    assert record.objective_gap == gap
    assert record.roundoff_allowance == 32 * ulp(absolute)
    assert lower <= float(full_optimum) + 1e-9 <= upper + 2e-9
    if record.accepted_path is not None:
        assert record.accepted_path == priced.arc_ids
        assert record.rho < -1e-9 and priced.arc_ids not in registry.values()


@pytest.mark.parametrize("index", range(6))
@pytest.mark.parametrize("alpha", (0.5, 1.5, 2.5))
@pytest.mark.parametrize("sign", (1, -1))
@pytest.mark.parametrize("reverse", (False, True))
@pytest.mark.parametrize("mode", ("revised", "tableau", "reuse"))
def test_216_complete_runs_against_independent_vertices(index, alpha, sign, reverse, mode,
                                                       observations):
    problem, resources = family(index, alpha, sign, reverse)
    columns = raw_columns(resources)
    assert len(columns) == 4 and ("x", "z") not in columns
    optimum = vertex_optimum(problem, columns, columns)
    backend = TableauSimplexSolver() if mode == "tableau" else RevisedSimplexSolver()
    result = solve_resource_dag_column_generation(problem, resources, solver=backend,
                                                  reoptimize_rmp=mode == "reuse")
    assert result.status == DagColumnGenerationStatus.TOLERANCE_REACHED
    registry = {f"path_{i}": path for i, path in enumerate(problem.seed_paths)}
    for index, record in enumerate(result.iterations, 1):
        assert record.iteration == index and record.column_paths == registry
        audit_round(problem, record, columns, optimum)
        if mode == "reuse":
            assert record.master_result is record.rmp_reoptimization.result
        else:
            assert record.rmp_reoptimization is None
        if record.accepted_path is not None:
            registry = dict(registry) | {f"path_{len(registry)}": record.accepted_path}
    assert result.column_paths == result.iterations[-1].column_paths
    assert result.column_set_iteration == result.last_valid_master_iteration
    assert result.column_set_iteration == len(result.iterations)
    assert result.last_valid_master is result.iterations[-1].master_result
    assert result.failure_iteration is None
    near(result.last_valid_master.objective_value, optimum)
    observed = observations[mode]
    observed["calls"] += 1
    observed["rounds"] += len(result.iterations)
    if mode == "reuse":
        observed["public_optin"] += len(result.iterations)
        for record in result.iterations:
            outcome = record.rmp_reoptimization
            observed["warm"] += int(outcome.used_warm_start)
            observed["internal_cold"] += outcome.cold_solve_count
            observed["fallback"] += int(bool(outcome.fallback_reason))
    else:
        observed["public_cold"] += len(result.iterations)
