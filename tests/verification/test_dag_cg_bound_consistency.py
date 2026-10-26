"""Independent dyadic transportation family and constant-shift regressions."""

import json
from collections import Counter
from dataclasses import replace
from fractions import Fraction
from math import fsum, ulp

import pytest

from silo.core.enums import ConstraintSense as S
from silo.decomposition import (
    DagArc,
    DagColumnGenerationProblem,
    DagColumnGenerationStatus,
    DagMasterRow,
    DagPricingProblem,
    solve_dag_column_generation,
)
from silo.decomposition.restricted_master import RestrictedMasterProblem
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver

MATRICES = ((4, 1, 2, 6), (-3, 2, 1, -4), (0, 0, 0, 0), (-4, -4, 3, 3),
            (2.25, -1.5, .5, 3.25), (1, -5, -2, 0))
BACKENDS = (RevisedSimplexSolver, TableauSimplexSolver)
CONSTANTS = (0, 2**40, -(2**40), 2**60, -(2**60))


def _endpoint_weights(alpha, beta, t):
    return (1 - alpha - beta + t, beta - t, alpha - t, t)


def _family_problem(k, alpha, beta, endpoint, reverse):
    alpha, beta = Fraction(alpha), Fraction(beta)
    ends = (max(Fraction(0), alpha + beta - 1), min(alpha, beta))
    costs = MATRICES[k]
    base, c0 = (1, 2) if k % 2 == 0 else (-2, -3)
    nodes = ('right1', 's', 'left0', 't', 'right0', 'left1')
    arcs = [DagArc(f'start{i}', 's', f'left{i}', (i + 1)/2, {'R': i}) for i in range(2)]
    arcs += [DagArc(f'end{j}', f'right{j}', 't', -(j + 1)/4, {'C': j}) for j in range(2)]
    arcs += [DagArc(f'middle{i}{j}', f'left{i}', f'right{j}',
                    costs[2*i+j] - base - (i + 1)/2 + (j + 1)/4)
             for i in range(2) for j in range(2)]
    graph = DagPricingProblem(nodes, arcs, 's', 't', ('C', 'conv', 'R'), base,
                              {'conv': 1, 'R': .125, 'C': -.25})
    weights = _endpoint_weights(alpha, beta, ends[endpoint])
    seeds = [(f'start{i}', f'middle{i}{j}', f'end{j}')
             for i in range(2) for j in range(2) if weights[2*i+j] > 0]
    problem = DagColumnGenerationProblem(graph, [DagMasterRow('conv', S.EQ, 1),
        DagMasterRow('R', S.EQ, float(alpha) + .125),
        DagMasterRow('C', S.EQ, float(beta) - .25)], 'conv', seeds, c0)
    if reverse:
        problem = replace(problem, graph=replace(graph, nodes=graph.nodes[::-1],
            arcs=graph.arcs[::-1], row_names=graph.row_names[::-1]),
            rows=problem.rows[::-1], seed_paths=problem.seed_paths[::-1])
    optimum = min(Fraction(c0) + sum(Fraction(c)*w for c, w in
        zip(costs, _endpoint_weights(alpha, beta, t), strict=True)) for t in ends)
    return problem, optimum


def _columns(graph):
    # Direct DFS and original-data Fraction sums; no production private helpers.
    outgoing = {node: [] for node in graph.nodes}
    for arc in graph.arcs:
        outgoing[arc.tail].append(arc)
    pending, result = [(graph.source, ())], {}
    while pending:
        node, path = pending.pop()
        if node != graph.sink:
            pending.extend((arc.head, path + (arc,)) for arc in outgoing[node])
            continue
        result[tuple(arc.arc_id for arc in path)] = (
            Fraction(graph.base_cost) + sum(Fraction(arc.cost) for arc in path),
            {j: Fraction(graph.base_coefficients.get(j, 0))
             + sum(Fraction(arc.row_coefficients.get(j, 0)) for arc in path)
             for j in graph.row_names})
    return result


def _audit_round(problem, record, columns, optimum):
    x, pi = record.master_result.primal_values, record.master_result.dual_values
    p = [float(columns[path][0])*x[name] for name, path in record.column_paths.items()]
    d = [row.rhs*pi[row.name] for row in problem.rows]
    delta = min(0, record.rho)
    upper = fsum([problem.objective_constant, *p])
    dual = fsum([problem.objective_constant, *d])
    lower = fsum([problem.objective_constant, *d, delta])
    gap = fsum([*p, *(-v for v in d), -delta])
    absolute = fsum([*(abs(v) for v in p), *(abs(v) for v in d), abs(delta)])
    eta = 32 * ulp(absolute)
    assert record.numerical_upper_bound == upper
    assert record.dual_objective == dual and record.numerical_lower_bound == lower
    assert record.numerical_gap == fsum([upper, -lower])
    assert record.objective_gap == gap and record.roundoff_allowance == eta
    assert gap >= 0 or (eta <= 1e-9 and -gap <= eta)

    # Exact reduced costs from the actual returned binary pi, then a genuine
    # Fraction dual shift. This bound check is distinct from floating estimates.
    exact_rc = {path: c - sum(a[j]*Fraction(pi[j]) for j in problem.graph.row_names)
                for path, (c, a) in columns.items()}
    exact_rho = min(exact_rc.values())
    exact_lower = Fraction(problem.objective_constant) + sum(
        Fraction(row.rhs)*Fraction(pi[row.name]) for row in problem.rows) + min(0, exact_rho)
    assert exact_lower <= optimum
    assert abs(Fraction(lower) - exact_lower) <= Fraction(1, 10**9)
    assert abs(Fraction(record.rho) - exact_rho) <= Fraction(1, 10**9)
    assert abs(Fraction(upper) - optimum) <= Fraction(1, 10**9) or upper > optimum
    assert min(x.values()) >= -1e-9
    for row in problem.rows:
        activity = sum(columns[path][1][row.name]*Fraction(x[name])
                       for name, path in record.column_paths.items())
        assert abs(activity - Fraction(row.rhs)) <= Fraction(1, 10**9)


@pytest.fixture(scope='module')
def family_runs():
    results = []
    yield results
    negative = [r.objective_gap for _, result in results for r in result.iterations
                if r.objective_gap is not None and r.objective_gap < 0]
    final_negative = Counter(backend for backend, result in results
                            if result.iterations[-1].objective_gap is not None
                            and result.iterations[-1].objective_gap < 0)
    allowances = [r.roundoff_allowance for _, result in results for r in result.iterations
                  if r.roundoff_allowance is not None]
    print('FAMILY_AUDIT=' + json.dumps({
        'runs': len(results), 'statuses': dict(Counter(r.status.value for _, r in results)),
        'backend_runs': dict(Counter(b for b, _ in results)),
        'iterations': sum(len(r.iterations) for _, r in results),
        'iteration_counts': dict(Counter(len(r.iterations) for _, r in results)),
        'negative_records': len(negative), 'negative_final_by_backend': dict(final_negative),
        'negative_min': min(negative, default=None), 'negative_max': max(negative, default=None),
        'eta_min': min(allowances, default=None), 'eta_max': max(allowances, default=None)}))


@pytest.mark.parametrize('backend', BACKENDS)
@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('endpoint', [0, 1])
@pytest.mark.parametrize('alpha', [.25, .5, .75])
@pytest.mark.parametrize('beta', [.25, .5, .75])
@pytest.mark.parametrize('k', range(6))
def test_54_models_432_runs_with_fraction_dual_shift(k, alpha, beta, endpoint,
                                                    reverse, backend, family_runs):
    problem, optimum = _family_problem(k, alpha, beta, endpoint, reverse)
    columns = _columns(problem.graph)
    assert len(columns) == 4
    for i in range(2):
        for j in range(2):
            cost, a = columns[(f'start{i}', f'middle{i}{j}', f'end{j}')]
            assert cost == Fraction(MATRICES[k][2*i+j])
            assert a == {'conv': 1, 'R': Fraction(1, 8)+i, 'C': Fraction(-1, 4)+j}
    result = solve_dag_column_generation(problem, solver=backend())
    family_runs.append((backend.__name__, result))
    assert result.status == DagColumnGenerationStatus.TOLERANCE_REACHED, result.message
    assert abs(Fraction(result.last_valid_master.objective_value) - optimum) <= Fraction(1, 10**9)
    for record in result.iterations:
        _audit_round(problem, record, columns, optimum)
    final = result.iterations[-1]
    assert final.rho >= -1e-9 and final.objective_gap <= 1e-9


def _natural_problem():
    arcs = [DagArc(f'p{i}{j}', 's', 't', (-2 if i == 0 else 5), {'R': i, 'C': j})
            for i in range(2) for j in range(2)]
    graph = DagPricingProblem(['s', 't'], arcs, 's', 't', ('R', 'conv', 'C'), -2,
                              {'conv': 1, 'R': .125, 'C': -.25})
    return DagColumnGenerationProblem(graph, [DagMasterRow('C', S.EQ, .5),
        DagMasterRow('R', S.EQ, .875), DagMasterRow('conv', S.EQ, 1)],
        'conv', [('p11',), ('p00',)], -3)


def test_minimal_natural_rounding_failure_recovers_without_rewriting_weights(monkeypatch):
    # Delegate to the real native solve; capture the immutable published result
    # before CG sees it. This observes weights, without injecting a synthetic LP.
    native_solve, published = RestrictedMasterProblem.solve, []

    def observed_solve(self, solver=None):
        returned = native_solve(self, solver)
        published.append((returned, dict(returned.primal_values)))
        return returned

    monkeypatch.setattr(RestrictedMasterProblem, 'solve', observed_solve)
    problem = _natural_problem()
    result = solve_dag_column_generation(problem)
    assert result.status == DagColumnGenerationStatus.TOLERANCE_REACHED, result.message
    record = result.iterations[-1]
    columns, optimum = _columns(problem.graph), Fraction(-7, 4)
    assert len(published) == len(result.iterations)
    for observed, (native, weights) in zip(result.iterations, published, strict=True):
        assert observed.master_result is native
        assert dict(observed.master_result.primal_values) == weights
        _audit_round(problem, observed, columns, optimum)
    assert result.last_valid_master is published[-1][0]
    assert abs(Fraction(record.master_result.objective_value) - optimum) <= Fraction(1, 10**9)
    assert abs(Fraction(record.numerical_upper_bound) - optimum) <= Fraction(1, 10**9)
    assert record.rho >= -1e-9 and record.objective_gap <= 1e-9
    if record.objective_gap < 0:
        assert -record.objective_gap <= record.roundoff_allowance <= 1e-9
        assert 'roundoff' in result.message.lower()
    print('NATURAL_CG_AUDIT=' + json.dumps({
        'native_snapshots': len(published), 'weights': dict(record.master_result.primal_values),
        'upper': record.numerical_upper_bound, 'lower': record.numerical_lower_bound,
        'gap': record.objective_gap, 'eta': record.roundoff_allowance,
        'exact_optimum': str(optimum), 'all_rounds_independently_checked': True}))


@pytest.mark.parametrize('backend', BACKENDS)
@pytest.mark.parametrize('c0', CONSTANTS)
@pytest.mark.parametrize('cheap', [0, 1-5e-10])
def test_real_constant_shift_preserves_stable_gap_allowance_and_flow(c0, cheap, backend):
    graph = DagPricingProblem(['s', 't'], [DagArc('seed', 's', 't', 1),
        DagArc('cheap', 's', 't', cheap)], 's', 't', ['conv'], base_coefficients={'conv': 1})
    problem = DagColumnGenerationProblem(graph, [DagMasterRow('conv', S.EQ, 1)],
                                        'conv', [('seed',)], c0)
    result = solve_dag_column_generation(problem, solver=backend())
    assert result.status == DagColumnGenerationStatus.TOLERANCE_REACHED, result.message
    first = result.iterations[0]
    assert first.master_result.dual_values == {'conv': 1}
    assert first.rho == cheap-1
    p, d, delta = 1.0, 1.0, cheap-1
    assert first.objective_gap == fsum([p, -d, -delta]) == 1-cheap
    assert first.roundoff_allowance == 32*ulp(fsum([abs(p), abs(d), abs(delta)]))
    if abs(c0) == 2**60 or (cheap != 0 and abs(c0) == 2**40):
        assert first.numerical_gap == 0 and first.objective_gap > 0
    if cheap == 0:
        assert len(result.iterations) == 2 and result.iterations[-1].objective_gap == 0
        positive = {result.column_paths[name] for name, value in
                    result.last_valid_master.primal_values.items() if value > 0}
        assert positive == {('cheap',)}
    else:
        assert len(result.iterations) == 1 and 0 < first.objective_gap < 1e-9
