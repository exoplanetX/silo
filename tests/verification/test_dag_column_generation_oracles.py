from dataclasses import replace
from fractions import Fraction
from math import fsum, ulp

import pytest

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense as S
from silo.core.enums import OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.decomposition import (
    DagArc,
    DagColumnGenerationProblem,
    DagColumnGenerationStatus,
    DagMasterRow,
    DagPricingProblem,
    RestrictedMasterProblem,
    solve_dag_column_generation,
)
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver


def _complete_columns(graph):
    # Independent exhaustive DFS and Fraction arithmetic from original graph data.
    # No controller/pricing private reconstruction, registry or model helpers.
    outgoing = {node: [] for node in graph.nodes}
    for arc in graph.arcs:
        outgoing[arc.tail].append(arc)
    stack = [(graph.source, ())]
    columns = {}
    while stack:
        node, path = stack.pop()
        if node != graph.sink:
            stack.extend((arc.head, path + (arc,)) for arc in outgoing[node])
            continue
        ids = tuple(arc.arc_id for arc in path)
        cost = Fraction(graph.base_cost) + sum(Fraction(arc.cost) for arc in path)
        a = {row: Fraction(graph.base_coefficients.get(row, 0))
             + sum(Fraction(arc.row_coefficients.get(row, 0)) for arc in path)
             for row in graph.row_names}
        columns[ids] = (cost, a)
    return columns


def _full_lp(problem, all_columns, backend):
    paths = sorted(all_columns)
    names = [f'oracle_{i}' for i in range(len(paths))]
    model = Model(variables=[Variable(name) for name in names],
        constraints=[Constraint(row.name, {name: float(all_columns[path][1][row.name])
            for name, path in zip(names, paths, strict=True)}, row.sense, row.rhs)
            for row in problem.rows],
        objective=Objective({name: float(all_columns[path][0])
                             for name, path in zip(names, paths, strict=True)},
                            OptimizationSense.MINIMIZE, problem.objective_constant))
    return RestrictedMasterProblem(model).solve(backend())


def _coupled():
    graph = DagPricingProblem(['s', 't'], [
        DagArc('d1', 's', 't', 4, {'R': 1, 'C': 1}), DagArc('d2', 's', 't', 6),
        DagArc('o12', 's', 't', 1, {'R': 1}), DagArc('o21', 's', 't', 2, {'C': 1})],
        's', 't', ['conv', 'R', 'C'], base_coefficients={'conv': 1})
    return DagColumnGenerationProblem(graph, [DagMasterRow('conv', S.EQ, 1),
        DagMasterRow('R', S.EQ, .5), DagMasterRow('C', S.EQ, .5)],
        'conv', [('d1',), ('d2',)], -3)


def _models():
    # Eight distinct models; each branch is a true two-arc path via its own vertex.
    cases = [
        ('conv', (3, 1, 0), (), {}, (0,), 0, 0, {}, 0),
        ('ge', (0, 4, 1), (('r', S.GE, .5),), {'r': (0, 1, 2)}, (0, 1), 0, 0, {}, .25),
        ('le', (3, 0, 1), (('r', S.LE, .5),), {'r': (0, 2, 1)}, (0,), 0, 0, {}, 2),
        ('eq', (3, -1, -7), (('r', S.EQ, .5),), {'r': (0, 1, 2)}, (0, 1), 2, 1,
         {'r': .25}, 2.5),
        ('negative_rhs', (2, 2, 0), (('r', S.EQ, -1),), {'r': (-2, 0, -1)},
         (0, 1), -2, 0, {}, -2),
        ('mixed', (2, 1, 0), (('r', S.GE, .5), ('q', S.LE, 1.5)),
         {'r': (0, 1, 2), 'q': (2, 1, 0)}, (0, 1), 3, -1, {'q': .25}, 3),
        ('equal_identity', (0, 0, -1), (), {}, (0, 1), 0, -2, {}, -1),
        ('asymmetric', (0, 2, -2, 0), (('r', S.EQ, .25), ('q', S.EQ, .75)),
         {'r': (1, 0, 1, 0), 'q': (1, 0, 0, 1)}, (1, 2, 3), -1, 1,
         {'r': .125}, -1.5),
    ]
    result = []
    for label, costs, rows, coefficients, seeds, c0, base, a_base, optimum in cases:
        nodes = ['s', 't', *(f'v{i}' for i in range(len(costs)))]
        arcs = []
        for i, cost in enumerate(costs):
            arcs.extend([DagArc(f'a{i}', 's', f'v{i}', 1),
                DagArc(f'z{i}', f'v{i}', 't', cost - base - 1,
                    {row: values[i] - a_base.get(row, 0) for row, values in coefficients.items()})])
        graph = DagPricingProblem(nodes, arcs, 's', 't', ['conv', *coefficients], base,
                                  {'conv': 1, **a_base})
        problem = DagColumnGenerationProblem(graph,
            [DagMasterRow('conv', S.EQ, 1), *(DagMasterRow(*row) for row in rows)],
            'conv', [(f'a{i}', f'z{i}') for i in seeds], c0)
        result.append(pytest.param(problem, optimum, id=label))
    return result


def _permuted(problem):
    return replace(problem, graph=replace(problem.graph, nodes=problem.graph.nodes[::-1],
        arcs=problem.graph.arcs[::-1], row_names=problem.graph.row_names[::-1]),
        rows=problem.rows[::-1], seed_paths=problem.seed_paths[::-1])


def _assert_run(problem, optimum, backend):
    columns = _complete_columns(problem.graph)
    full = _full_lp(problem, columns, backend)
    assert full.status == SolverStatus.OPTIMAL
    assert full.objective_value == pytest.approx(optimum, abs=1e-9, rel=0)
    result = solve_dag_column_generation(problem, solver=backend())
    assert result.status == DagColumnGenerationStatus.TOLERANCE_REACHED, result.message
    assert result.last_valid_master.objective_value == pytest.approx(optimum, abs=1e-9, rel=0)
    assert result.last_valid_master_iteration == result.column_set_iteration
    assert result.column_set_iteration == len(result.iterations)
    for record in result.iterations:
        pi = record.master_result.dual_values
        x = record.master_result.primal_values
        p_terms = [float(columns[path][0]) * x[name]
                   for name, path in record.column_paths.items()]
        d_terms = [row.rhs * pi[row.name] for row in problem.rows]
        p = fsum([problem.objective_constant, *p_terms])
        d = fsum([problem.objective_constant, *d_terms])
        rho = min(float(cost) - sum(float(a[j]) * pi[j] for j in problem.graph.row_names)
                  for cost, a in columns.values())
        delta = min(0, record.rho)
        lower = fsum([problem.objective_constant, *d_terms, delta])
        assert record.numerical_upper_bound == pytest.approx(p, abs=1e-9, rel=0)
        assert record.dual_objective == pytest.approx(d, abs=1e-9, rel=0)
        assert record.rho == pytest.approx(rho, abs=1e-9, rel=0)
        assert record.numerical_lower_bound == pytest.approx(lower, abs=1e-9, rel=0)
        assert record.numerical_gap == pytest.approx(p - lower, abs=1e-9, rel=0)
        assert record.objective_gap == fsum([*p_terms, *(-v for v in d_terms), -delta])
        assert record.roundoff_allowance == 32*ulp(fsum([
            *(abs(v) for v in p_terms), *(abs(v) for v in d_terms), abs(delta)]))
        assert lower <= optimum + 1e-9 and p >= optimum - 1e-9
        assert min(x.values()) >= -1e-9
        for row in problem.rows:
            activity = sum(float(columns[path][1][row.name]) * x[name]
                           for name, path in record.column_paths.items())
            if row.sense == S.EQ:
                assert abs(activity - row.rhs) <= 1e-9
            elif row.sense == S.LE:
                assert activity <= row.rhs + 1e-9 and pi[row.name] <= 1e-9
            else:
                assert activity >= row.rhs - 1e-9 and pi[row.name] >= -1e-9
    return result


@pytest.mark.parametrize('backend', [RevisedSimplexSolver, TableauSimplexSolver])
@pytest.mark.parametrize('reverse', [False, True])
def test_degenerate_coupled_example_against_analytic_line_and_complete_lp(backend, reverse):
    problem = _permuted(_coupled()) if reverse else _coupled()
    result = _assert_run(problem, -1.5, backend)
    assert [r.numerical_upper_bound for r in result.iterations] == [2, 2, -1.5]
    weights = {path: result.last_valid_master.primal_values[name]
               for name, path in result.column_paths.items()}
    assert weights == {('d1',): 0, ('d2',): 0, ('o12',): .5, ('o21',): .5}
    # Independent exact analytic line: P(t)=-3/2+7t, 0<=t<=1/2.
    assert min(Fraction(-3, 2) + 7*t for t in [Fraction(0), Fraction(1, 2)]) == Fraction(-3, 2)


@pytest.mark.parametrize('backend', [RevisedSimplexSolver, TableauSimplexSolver])
@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('problem,optimum', _models())
def test_eight_other_models_complete_lp_and_analytic_targets(problem, optimum, backend, reverse):
    _assert_run(_permuted(problem) if reverse else problem, optimum, backend)


@pytest.mark.parametrize('backend', [RevisedSimplexSolver, TableauSimplexSolver])
@pytest.mark.parametrize('reverse', [False, True])
def test_alternative_feasible_seed_for_same_ge_model(backend, reverse):
    problem = _models()[1].values[0]
    problem = replace(problem, seed_paths=[('a0', 'z0'), ('a2', 'z2')])
    _assert_run(_permuted(problem) if reverse else problem, .25, backend)


def test_seed_infeasible_but_complete_master_feasible():
    problem = _models()[1].values[0]
    problem = replace(problem, seed_paths=[('a0', 'z0')])
    full = _full_lp(problem, _complete_columns(problem.graph), RevisedSimplexSolver)
    assert full.status == SolverStatus.OPTIMAL and full.objective_value == .25
    result = solve_dag_column_generation(problem)
    assert result.status == DagColumnGenerationStatus.MASTER_FAILURE
    assert result.iterations[0].master_result.status == SolverStatus.INFEASIBLE
    assert result.last_valid_master is None and result.iterations[0].pricing_result is None


def test_positive_cost_small_negative_price_has_exact_nonzero_remaining_improvement():
    graph = DagPricingProblem(['s', 't'], [DagArc('expensive', 's', 't', 1),
        DagArc('cheap', 's', 't', 1 - 5e-10)], 's', 't', ['conv'],
        base_coefficients={'conv': 1})
    problem = DagColumnGenerationProblem(graph, [DagMasterRow('conv', S.EQ, 1)],
                                        'conv', [('expensive',)])
    result = solve_dag_column_generation(problem)
    record = result.iterations[0]
    exact = min(cost for cost, _ in _complete_columns(graph).values())
    assert exact < 1 and Fraction(1) - exact > 0
    assert result.status == DagColumnGenerationStatus.TOLERANCE_REACHED
    assert record.rho < 0 and 0 < record.numerical_gap <= 1e-9
    assert record.numerical_upper_bound == 1 and len(result.column_paths) == 1


def test_delimiter_ids_and_equal_vectors_keep_distinct_path_identity():
    graph = DagPricingProblem(['s', 'v', 't'], [DagArc('a|b', 's', 'v', 1),
        DagArc('c', 'v', 't', 1), DagArc('a', 's', 'v', 1), DagArc('b|c', 'v', 't', 1)],
        's', 't', ['conv'], base_coefficients={'conv': 1})
    problem = DagColumnGenerationProblem(graph, [DagMasterRow('conv', S.EQ, 1)],
        'conv', [('a|b', 'c'), ('a', 'b|c')])
    result = solve_dag_column_generation(problem)
    assert len(result.column_paths) == 2 and len(result.iterations) == 1
    assert set(result.column_paths.values()) == set(problem.seed_paths)
