"""Original-graph DFS, exact current-column vertices and observed public paths.

No production reconstruction, numerical, pricing or snapshot helper supplies
oracle truth. Private runner hooks below only observe actual execution.
"""

from collections import Counter
from contextlib import contextmanager
from fractions import Fraction as F
from itertools import combinations, permutations, product
from math import fsum, ulp

import pytest

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense as S
from silo.core.enums import OptimizationSense as O
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus as Status
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
from silo.lp.simplex import revised, tableau
from silo.lp.simplex.tableau import TableauSimplexSolver

MATRICES = ((4, 1, 2, 6), (-3, 2, 1, -4), (0, 0, 0, 0), (-4, -4, 3, 3),
            (F(9, 4), F(-3, 2), F(1, 2), F(13, 4)), (1, -5, -2, 0))
INTERVAL_COSTS = ((2, 0, -1), (0, 4, 10), (0, 0, 0))
MAIN_CASES = ([('interval', v) for v in product((0, 1), range(3),
                permutations(('conv', 'lo', 'hi')), (False, True))]
              + [('square', v) for v in product(range(6), (F(1, 4), F(1, 2), F(3, 4)),
                  (F(1, 4), F(1, 2), F(3, 4)), (0, 1), (False, True))])
MODES = ('cold-revised', 'cold-tableau', 'warm-revised')
TOL = F(1e-9)


def interval_problem(which, k, order, negative):
    lo, hi = ((F(1, 2), F(3, 2)), (F(1, 4), F(7, 4)))[which]
    total, base = INTERVAL_COSTS[k], 1 if k % 2 == 0 else -2
    sign = -1 if negative else 1
    arcs = []
    paths = []
    for i, (label, mean) in enumerate(zip(('p1', 'p0', 'p2'), (1, 0, 2), strict=True)):
        first, last = f'{label}a', f'{label}b'
        arcs.extend((DagArc(first, 's', f'v{i}', (i + 1)/2),
                     DagArc(last, f'v{i}', 't', float(F(total[i]) - base - F(i + 1, 2)),
                            {'lo': float(sign * (F(mean) - F(1, 8))),
                             'hi': float(sign * (F(mean) - F(1, 8)))})))
        paths.append((first, last))
    senses = {'conv': S.EQ, 'lo': S.LE if negative else S.GE,
              'hi': S.GE if negative else S.LE}
    rhs = {'conv': 1, 'lo': float(sign * lo), 'hi': float(sign * hi)}
    graph = DagPricingProblem(('v2', 's', 'v0', 't', 'v1'),
        arcs[::-1] if negative else arcs, 's', 't', order, base,
        {'conv': 1, 'lo': sign/8, 'hi': sign/8})
    problem = DagColumnGenerationProblem(graph, [DagMasterRow(n, senses[n], rhs[n])
        for n in order], 'conv', [paths[0]], (7, -3, 0)[k])
    # Independent interval endpoints / pure feasible mean=1.
    choices = [F(total[0])]
    for endpoint in (lo, hi):
        choices.append((1 - endpoint/2)*F(total[1]) + endpoint/2*F(total[2]))
    return problem, min(choices)


def square_problem(k, alpha, beta, endpoint, reverse, constant=None):
    base = 1 if k % 2 == 0 else -2
    vertices = (max(F(0), alpha + beta - 1), min(alpha, beta))
    def weights(t):
        return (1 - alpha - beta + t, beta - t, alpha - t, t)
    arcs = []
    for i in (0, 1):
        arcs.append(DagArc(f's{i}', 's', f'left{i}', (i + 1)/2, {'R': i}))
    for j in (0, 1):
        arcs.append(DagArc(f'e{j}', f'right{j}', 't', -(j + 1)/4, {'C': j}))
    for i, j in product((0, 1), repeat=2):
        cost = F(MATRICES[k][2*i+j]) - base - F(i + 1, 2) + F(j + 1, 4)
        arcs.append(DagArc(f'm{i}{j}', f'left{i}', f'right{j}', float(cost)))
    nodes = ('right1', 's', 'left0', 't', 'right0', 'left1')
    names = ('C', 'conv', 'R')
    rows = [DagMasterRow('conv', S.EQ, 1), DagMasterRow('R', S.EQ, float(alpha + F(1, 8))),
            DagMasterRow('C', S.EQ, float(beta - F(1, 4)))]
    seed = [(f's{i}', f'm{i}{j}', f'e{j}') for i, j in product((0, 1), repeat=2)
            if weights(vertices[endpoint])[2*i+j] > 0]
    graph = DagPricingProblem(nodes[::-1] if reverse else nodes,
        arcs[::-1] if reverse else arcs, 's', 't', names[::-1] if reverse else names,
        base, {'conv': 1, 'R': 1/8, 'C': -1/4})
    problem = DagColumnGenerationProblem(graph, rows[::-1] if reverse else rows, 'conv',
        seed[::-1] if reverse else seed,
        (2 if k % 2 == 0 else -3) if constant is None else constant)
    optimum = min(sum(F(c)*w for c, w in zip(MATRICES[k], weights(t), strict=True))
                  for t in vertices)
    return problem, optimum


def build_case(case):
    kind, args = case
    return (interval_problem if kind == 'interval' else square_problem)(*args)


def original_paths(graph):
    outgoing = {n: [] for n in graph.nodes}
    for arc in graph.arcs:
        outgoing[arc.tail].append(arc)
    pending, found = [(graph.source, ())], {}
    while pending:
        node, path = pending.pop()
        if node != graph.sink:
            assert len(path) < len(graph.nodes)
            pending.extend((a.head, (*path, a)) for a in outgoing[node])
        else:
            found[tuple(a.arc_id for a in path)] = (
                F(graph.base_cost) + sum((F(a.cost) for a in path), F(0)),
                {n: F(graph.base_coefficients.get(n, 0)) + sum(
                    (F(a.row_coefficients.get(n, 0)) for a in path), F(0))
                 for n in graph.row_names})
    return found


def exact_solve(matrix, rhs):
    n = len(rhs)
    augmented = [list(row) + [value] for row, value in zip(matrix, rhs, strict=True)]
    for j in range(n):
        pivot = next((i for i in range(j, n) if augmented[i][j]), None)
        if pivot is None:
            return None
        augmented[j], augmented[pivot] = augmented[pivot], augmented[j]
        divisor = augmented[j][j]
        augmented[j] = [v/divisor for v in augmented[j]]
        for i in range(n):
            if i != j:
                multiplier = augmented[i][j]
                augmented[i] = [a - multiplier*b for a, b in
                                zip(augmented[i], augmented[j], strict=True)]
    return tuple(row[-1] for row in augmented)


def satisfies(row, activity):
    residual = activity - F(row.rhs)
    if row.sense == S.EQ:
        return residual == 0
    return residual <= 0 if row.sense == S.LE else residual >= 0


def vertex_value(problem, columns):
    names = tuple(columns)
    conv = next(row for row in problem.rows if row.name == problem.convexity_row)
    others = [row for row in problem.rows if row is not conv]
    objectives = []
    for count in range(1, min(len(names), len(problem.rows)) + 1):
        for support in combinations(names, count):
            for active in combinations(others, count - 1):
                rows = (conv, *active)
                values = exact_solve([[columns[n][1][r.name] for n in support] for r in rows],
                                     [F(r.rhs) for r in rows])
                if values is None or min(values) < 0:
                    continue
                if all(satisfies(r, sum(columns[n][1][r.name]*v for n, v in
                                       zip(support, values, strict=True))) for r in problem.rows):
                    objectives.append(sum(columns[n][0]*v for n, v in
                                          zip(support, values, strict=True)))
    assert objectives, 'Every current column set in these histories is feasible.'
    return min(objectives)


def close(a, b):
    assert abs(F(a) - F(b)) <= TOL, (a, b)


def audit_minimum(problem, columns, solution, optimum):
    assert solution.status == Status.OPTIMAL
    assert set(solution.primal_values) == set(solution.reduced_costs) == set(columns)
    assert set(solution.dual_values) == {r.name for r in problem.rows}
    x = {n: F(v) for n, v in solution.primal_values.items()}
    pi = {n: F(v) for n, v in solution.dual_values.items()}
    assert min(x.values()) >= -TOL
    for row in problem.rows:
        residual = sum(columns[n][1][row.name]*x[n] for n in columns) - F(row.rhs)
        assert abs(residual) <= TOL if row.sense == S.EQ else (
            residual <= TOL if row.sense == S.LE else residual >= -TOL)
        if row.sense != S.EQ:
            assert pi[row.name] <= TOL if row.sense == S.LE else pi[row.name] >= -TOL
        assert abs(pi[row.name]*residual) <= TOL
    for n in columns:
        rc = columns[n][0] - sum(columns[n][1][r.name]*pi[r.name] for r in problem.rows)
        close(rc, solution.reduced_costs[n])
        assert rc >= -TOL and abs(x[n]*rc) <= TOL
    primal = sum(columns[n][0]*x[n] for n in columns)
    dual = sum(F(r.rhs)*pi[r.name] for r in problem.rows)
    close(primal, optimum)
    close(primal, dual)
    return primal


def audit_result(problem, result, data, full_optimum, warm=False):
    assert result.status == DagColumnGenerationStatus.TOLERANCE_REACHED
    previous = None
    for i, record in enumerate(result.iterations, 1):
        assert record.iteration == i
        columns = {n: data[p] for n, p in record.column_paths.items()}
        current = vertex_value(problem, columns)
        audit_minimum(problem, columns, record.master_result, current)
        if previous is not None:
            expected = dict(previous.column_paths)
            expected[f'path_{len(expected)}'] = previous.accepted_path
            assert dict(record.column_paths) == expected
        outcome = getattr(record, 'rmp_reoptimization', None)
        if warm:
            assert outcome is not None and record.master_result is outcome.result
        else:
            assert outcome is None
        price = record.pricing_result
        assert price.arc_ids in data
        exact_prices = {p: c - sum(a[r]*F(record.master_result.dual_values[r]) for r in a)
                        for p, (c, a) in data.items()}
        selected_cost, selected_coefficients = data[price.arc_ids]
        close(exact_prices[price.arc_ids], min(exact_prices.values()))
        close(price.cost, selected_cost)
        for r in selected_coefficients:
            close(price.row_coefficients[r], selected_coefficients[r])
        close(price.reduced_cost, exact_prices[price.arc_ids])
        close(record.rho, price.reduced_cost)
        assert price.is_improving is (record.rho < -1e-9)
        p_terms = [float(c)*record.master_result.primal_values[n] for n, (c, _) in columns.items()]
        d_terms = [r.rhs*record.master_result.dual_values[r.name] for r in problem.rows]
        upper = fsum([problem.objective_constant, *p_terms])
        dual = fsum([problem.objective_constant, *d_terms])
        delta = min(0, record.rho)
        lower = fsum([problem.objective_constant, *d_terms, delta])
        gap = fsum([*p_terms, *(-v for v in d_terms), -delta])
        allowance = 32*ulp(fsum([*(abs(v) for v in p_terms), *(abs(v) for v in d_terms),
                                abs(delta)]))
        assert (record.numerical_upper_bound, record.dual_objective, record.numerical_lower_bound,
                record.numerical_gap, record.objective_gap, record.roundoff_allowance) == (
                    upper, dual, lower, fsum((upper, -lower)), gap, allowance)
        close(record.master_result.objective_value, upper)
        if gap < 0:
            assert allowance <= 1e-9 and -gap <= allowance
        if price.is_improving:
            assert price.arc_ids not in record.column_paths.values()
            assert record.accepted_path == price.arc_ids
        else:
            assert record.accepted_path is None and gap <= 1e-9
        previous = record
    last = result.iterations[-1]
    final_columns = {n: data[p] for n, p in last.column_paths.items()}
    close(vertex_value(problem, final_columns), full_optimum)
    assert result.last_valid_master is last.master_result
    assert (result.last_valid_master_iteration == result.column_set_iteration
            == len(result.iterations))
    assert dict(result.column_paths) == dict(last.column_paths) and result.failure_iteration is None


def full_cold_references(problem, data, optimum):
    columns = {f'all_{i}': data[p] for i, p in enumerate(sorted(data))}
    model = Model('full-domain-reference', [Variable(n) for n in columns],
        [Constraint(r.name, {n: float(a[r.name]) for n, (_, a) in columns.items()}, r.sense, r.rhs)
         for r in problem.rows], Objective({n: float(c) for n, (c, _) in columns.items()},
                                          O.MINIMIZE, problem.objective_constant))
    for backend in (revised.RevisedSimplexSolver, TableauSimplexSolver):
        audit_minimum(problem, columns, RestrictedMasterProblem(model).solve(backend()), optimum)


class Trace:
    def __init__(self, patch):
        self.calls = []
        self.current = None
        self.in_cold = False
        ordinary = RestrictedMasterProblem.solve
        optin = RestrictedMasterProblem.solve_reoptimized
        cold = revised.RevisedSimplexSolver.solve_with_details
        reuse = revised.RevisedSimplexSolver.reoptimize
        runner = revised._run_primal_revised_simplex
        tableau_solve = TableauSimplexSolver.solve
        tableau_runner = tableau._run_simplex_iterations
        pivot = tableau.SimplexTableau.pivot
        self.tableau_pivots = 0

        @contextmanager
        def call(owner, kind):
            assert self.current is None
            item = dict(owner=owner, kind=kind, cold=0, runs=[])
            self.current = item
            self.calls.append(item)
            try:
                yield item
            finally:
                self.current = None

        def solve(owner, solver=None):
            with call(owner, 'ordinary') as item:
                item['result'] = ordinary(owner, solver)
                return item['result']

        def optimized(owner, solver=None):
            with call(owner, 'optin') as item:
                item['outcome'] = optin(owner, solver)
                return item['outcome']

        def details(solver, model, basis=None):
            self.current['cold'] += 1
            prior = self.in_cold
            self.in_cold = True
            try:
                return cold(solver, model, basis)
            finally:
                self.in_cold = prior

        def reoptimize(solver, model, snapshot=None):
            self.current['incoming'] = snapshot
            result = reuse(solver, model, snapshot)
            self.current['lp_outcome'] = result
            return result

        def run(**kw):
            item = (self.in_cold, kw['phase_name'], kw['problem'], kw['basis'])
            result = runner(**kw)
            self.current['runs'].append((*item, result.iterations))
            return result

        def solve_tableau(solver, model):
            self.current['cold'] += 1
            return tableau_solve(solver, model)

        def tableau_pivot(tab, row_index, column_index):
            self.tableau_pivots += 1
            return pivot(tab, row_index, column_index)

        def run_tableau(**kw):
            before = self.tableau_pivots
            result = tableau_runner(**kw)
            self.current['runs'].append((True, kw['phase_name'], None, None,
                                         self.tableau_pivots - before))
            return result

        patch.setattr(RestrictedMasterProblem, 'solve', solve)
        patch.setattr(RestrictedMasterProblem, 'solve_reoptimized', optimized)
        patch.setattr(revised.RevisedSimplexSolver, 'solve_with_details', details)
        patch.setattr(revised.RevisedSimplexSolver, 'reoptimize', reoptimize)
        patch.setattr(revised, '_run_primal_revised_simplex', run)
        patch.setattr(TableauSimplexSolver, 'solve', solve_tableau)
        patch.setattr(tableau, '_run_simplex_iterations', run_tableau)
        patch.setattr(tableau.SimplexTableau, 'pivot', tableau_pivot)

    def audit(self, result, warm):
        assert len(self.calls) == len(result.iterations)
        assert len({id(item['owner']) for item in self.calls}) == 1
        for item, record in zip(self.calls, result.iterations, strict=True):
            assert item['kind'] == ('optin' if warm else 'ordinary')
            if not warm:
                assert item['cold'] == 1
                continue
            outcome = record.rmp_reoptimization
            assert outcome is item['outcome']
            assert outcome.cold_solve_count == item['cold']
            warm_runs = [entry for entry in item['runs'] if not entry[0]]
            assert outcome.warm_phase_two_attempted == bool(warm_runs)
            assert outcome.warm_iterations == sum(e[-1] for e in warm_runs)
            assert outcome.cold_iterations == sum(e[-1] for e in item['runs'] if e[0])
            if outcome.used_warm_start:
                assert len(warm_runs) == 1 and item['cold'] == 0
                _, phase, p, basis, _ = warm_runs[0]
                assert phase == 'Phase II' and not p.artificial_columns
                assert p.row_names == item['incoming'].row_names
                keys = tuple((c.role, c.original_name if c.role == 'original' else
                              c.source_constraint) for c in p.columns)
                assert tuple(keys[j] for j in basis.basic_columns) == item['incoming'].basis_keys
                old_names = {v.name for v in item['incoming'].model_identity.variables}
                assert all(j in basis.nonbasic_columns for j, c in enumerate(p.columns)
                           if c.role == 'original' and c.original_name not in old_names)

    def counts(self):
        result = Counter(cg=1, rounds=len(self.calls))
        for item in self.calls:
            result[item['kind']] += 1
            result['cold'] += item['cold']
            for is_cold, phase, _, _, pivots in item['runs']:
                key = ('cold_' if is_cold else 'warm_') + phase.replace(' ', '_')
                result[key] += 1
                result[key + '_pivots'] += pivots
            if item['kind'] == 'optin':
                o = item['outcome']
                result['warm'] += o.used_warm_start
                result['warm_zero'] += o.used_warm_start and o.warm_iterations == 0
                result['fallback'] += bool(o.fallback_reason)
        return result


def run_mode(problem, mode):
    if mode == 'cold-revised':
        return solve_dag_column_generation(problem)
    if mode == 'cold-tableau':
        return solve_dag_column_generation(problem, solver=TableauSimplexSolver())
    return solve_dag_column_generation(problem, solver=revised.RevisedSimplexSolver(),
                                       reoptimize_rmp=True)


@pytest.mark.parametrize('case', MAIN_CASES, ids=[f'graph-{i:03}' for i in range(288)])
def test_current_sets_full_domain_and_real_solver_paths(case, monkeypatch):
    problem, optimum = build_case(case)
    data = original_paths(problem.graph)
    assert vertex_value(problem, data) == optimum
    full_cold_references(problem, data, optimum)
    for mode in MODES:
        with monkeypatch.context() as patch:
            trace = Trace(patch)
            result = run_mode(problem, mode)
            audit_result(problem, result, data, optimum, mode == 'warm-revised')
            trace.audit(result, mode == 'warm-revised')
