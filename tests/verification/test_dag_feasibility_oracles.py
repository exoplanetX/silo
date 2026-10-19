"""Complete auxiliary LPs and independent square-domain Fraction violation values."""

import json
from collections import Counter
from dataclasses import replace
from fractions import Fraction as F
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
    DagFeasibilityStatus,
    DagMasterRow,
    DagPricingProblem,
    RestrictedMasterProblem,
    restore_dag_feasibility,
    solve_dag_column_generation,
)
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver

SETTINGS = tuple((sense, rhs) for sense in (S.LE, S.GE, S.EQ)
                 for rhs in (F(-1, 4), F(1, 2), F(5, 4)))
BACKENDS = (RevisedSimplexSolver, TableauSimplexSolver)


def _violation(sense, b):
    return (max(F(0), -b) if sense == S.LE else max(F(0), b-1) if sense == S.GE
            else max(F(0), -b, b-1))


def _problem(r_index, c_index, seed, reverse):
    m = 9*r_index+c_index
    costs, base, c0 = ((0, 4, 10, 7), 1, 5) if m % 2 == 0 else ((3, -2, 1, -4), -2, -5)
    arcs = [DagArc(f'start{i}', 's', f'left{i}', (i+1)/2, {'R': i}) for i in range(2)]
    arcs += [DagArc(f'end{j}', f'right{j}', 't', -(j+1)/4, {'C': j}) for j in range(2)]
    arcs += [DagArc(f'middle{i}{j}', f'left{i}', f'right{j}',
                   costs[2*i+j]-base-(i+1)/2+(j+1)/4) for i in range(2) for j in range(2)]
    graph = DagPricingProblem(('right1', 's', 'left0', 't', 'right0', 'left1'), arcs,
        's', 't', ('conv', 'R', 'C'), base, {'conv': 1, 'R': .125, 'C': -.25})
    sr, br = SETTINGS[r_index]
    sc, bc = SETTINGS[c_index]
    problem = DagColumnGenerationProblem(graph, [DagMasterRow('conv', S.EQ, 1),
        DagMasterRow('R', sr, float(br+F(1, 8))), DagMasterRow('C', sc, float(bc-F(1, 4)))],
        'conv', [(f'start{seed}', f'middle{seed}{seed}', f'end{seed}')], c0)
    if reverse:
        problem = replace(problem, graph=replace(graph, nodes=graph.nodes[::-1],
            arcs=graph.arcs[::-1], row_names=graph.row_names[::-1]), rows=problem.rows[::-1])
    return problem, _violation(sr, br)+_violation(sc, bc), costs


def _columns(graph):
    # Entire tiny path domain, with original costs and coefficients, independently.
    outgoing = {node: [] for node in graph.nodes}
    for arc in graph.arcs:
        outgoing[arc.tail].append(arc)
    pending, columns = [(graph.source, ())], {}
    while pending:
        node, path = pending.pop()
        if node != graph.sink:
            pending.extend((arc.head, path+(arc,)) for arc in outgoing[node])
            continue
        columns[tuple(arc.arc_id for arc in path)] = (
            F(graph.base_cost)+sum(F(arc.cost) for arc in path),
            {j: F(graph.base_coefficients.get(j, 0))
             + sum(F(arc.row_coefficients.get(j, 0)) for arc in path) for j in graph.row_names})
    return columns


def _full_lp(problem, columns, backend, auxiliary):
    paths = sorted(columns)
    data = {f'oracle_path_{i}': (0 if auxiliary else float(columns[p][0]), columns[p][1])
            for i, p in enumerate(paths)}
    if auxiliary:
        for row in problem.rows:
            if row.name == problem.convexity_row:
                continue
            signs = (-1,) if row.sense == S.LE else (1,) if row.sense == S.GE else (1, -1)
            for sign in signs:
                data[f'oracle_art_{len(data)}'] = (1, {row.name: sign})
    model = Model(variables=[Variable(name) for name in data],
        constraints=[Constraint(row.name, {name: float(a.get(row.name, 0))
            for name, (_, a) in data.items()}, row.sense, row.rhs) for row in problem.rows],
        objective=Objective({name: c for name, (c, a) in data.items()},
                            OptimizationSense.MINIMIZE,
                            0 if auxiliary else problem.objective_constant))
    return RestrictedMasterProblem(model).solve(backend())


class _CountingBackend:
    def __init__(self, backend):
        self.backend, self.models = backend(), []

    def solve(self, model):
        self.models.append((tuple(v.name for v in model.variables),
                            dict(model.objective.coefficients), model.objective.constant))
        return self.backend.solve(model)


def _assert_rows(problem, paths, columns, x, artificial):
    assert min(x.values()) >= -1e-9
    for row in problem.rows:
        activity = sum(columns[path][1][row.name]*F(x[name]) for name, path in paths.items())
        activity += sum(F(sign)*F(x[name]) for name, (j, sign) in artificial.items()
                        if j == row.name)
        residual = activity-F(row.rhs)
        assert (abs(residual) <= F(1, 10**9) if row.sense == S.EQ else
                residual <= F(1, 10**9) if row.sense == S.LE else residual >= -F(1, 10**9))


def _audit_round(problem, record, columns, optimum):
    x, pi = record.master_result.primal_values, record.master_result.dual_values
    arts = record.artificial_columns
    assert set(x) == set(record.column_paths) | set(arts)
    _assert_rows(problem, record.column_paths, columns, x, arts)
    exact_art_rc = []
    for name, (j, sign) in arts.items():
        assert j != problem.convexity_row and sign in (1, -1)
        rc = F(1)-F(sign)*F(pi[j])
        exact_art_rc.append(rc)
        assert rc >= -F(1, 10**9)  # Existing floating check; retain exact violations below.
        assert abs(F(record.master_result.reduced_costs[name])-rc) <= F(1, 10**9)
    minimum = min(exact_art_rc, default=F(0))
    sign_violation = any((row.sense == S.LE and pi[row.name] > 0)
                         or (row.sense == S.GE and pi[row.name] < 0) for row in problem.rows)
    audit = {'exact_art_min': float(minimum), 'exact_sign_violation': sign_violation,
             'exact_dual_feasible': minimum >= 0 and not sign_violation,
             'formal_shift_excess': None}
    p = [*(0*x[name] for name in record.column_paths), *(x[name] for name in arts)]
    assert record.penalty_objective == fsum(p)
    if record.pricing_result is None:
        assert record.penalty_objective <= 1e-9
        assert record.original_validation.status == SolverStatus.OPTIMAL
        assert all(getattr(record, field) is None for field in ('dual_objective', 'rho',
            'numerical_lower_bound', 'numerical_gap', 'objective_gap', 'roundoff_allowance'))
        return audit
    d = [row.rhs*pi[row.name] for row in problem.rows]
    delta = min(0, record.rho)
    assert record.dual_objective == fsum(d)
    assert record.numerical_lower_bound == fsum([*d, delta])
    assert record.numerical_gap == fsum([fsum(p), -fsum([*d, delta])])
    assert record.objective_gap == fsum([*p, *(-v for v in d), -delta])
    assert record.roundoff_allowance == 32*ulp(fsum([
        *(abs(v) for v in p), *(abs(v) for v in d), abs(delta)]))
    assert record.objective_gap >= 0 or (
        record.roundoff_allowance <= 1e-9 and -record.objective_gap <= record.roundoff_allowance)
    exact_rc = {p: -sum(a[j]*F(pi[j]) for j in problem.graph.row_names)
                for p, (_, a) in columns.items()}
    exact_rho = min(exact_rc.values())
    assert abs(F(record.rho)-exact_rho) <= F(1, 10**9)
    exact_lower = sum(F(row.rhs)*F(pi[row.name]) for row in problem.rows)+min(0, exact_rho)
    if audit['exact_dual_feasible']:
        assert exact_lower <= optimum
    else:
        # Contract explicitly requires documenting rounding violations, without
        # projecting pi or calling this shifted objective an exact dual bound.
        assert exact_lower-optimum <= F(1, 10**9)
    audit['formal_shift_excess'] = float(exact_lower-optimum)
    assert abs(F(record.numerical_lower_bound)-exact_lower) <= F(1, 10**9)
    # Convexity shift changes real rc, never the fixed artificial rc (conv=0).
    assert all(rc-min(0, exact_rho) >= 0 for rc in exact_rc.values())
    return audit


@pytest.fixture(scope='module')
def family_runs():
    data = {'runs': [], 'audits': []}
    yield data
    records, audits = data['runs'], data['audits']
    exact_bad = [(b, final, a) for b, final, a in audits if a['exact_art_min'] < 0]
    excess = [a['formal_shift_excess'] for _, _, a in audits
              if a['formal_shift_excess'] is not None and a['formal_shift_excess'] > 0]
    print('FEASIBILITY_FAMILY=' + json.dumps({
        'runs': len(records), 'statuses': dict(Counter(r.status.value for _, _, r in records)),
        'by_backend': {b.__name__: dict(Counter(r.status.value for name, _, r in records
                                              if name == b.__name__)) for b in BACKENDS},
        'by_order': {str(order): dict(Counter(r.status.value for _, o, r in records if o == order))
                     for order in (False, True)},
        'auxiliary_solves': sum(r.auxiliary_solve_count for _, _, r in records),
        'validation_solves': sum(r.validation_solve_count for _, _, r in records),
        'auxiliary_counts': dict(Counter(r.auxiliary_solve_count for _, _, r in records)),
        'priced_rounds': sum(r.pricing_result is not None for _, _, result in records
                             for r in result.iterations),
        'original_objective_handoffs': sum(r.feasible_problem is not None for _, _, r in records),
        'exact_art_violations': len(exact_bad),
        'exact_art_violations_final': sum(final for _, final, _ in exact_bad),
        'exact_art_violations_by_backend': dict(Counter(b for b, _, _ in exact_bad)),
        'min_exact_art_rc': min((a['exact_art_min'] for _, _, a in audits), default=None),
        'exact_sign_violations': sum(a['exact_sign_violation'] for _, _, a in audits),
        'formal_shift_above_optimum': len(excess),
        'formal_excess_max': max(excess, default=None)}))


@pytest.mark.parametrize('backend', BACKENDS)
@pytest.mark.parametrize('reverse', [False, True])
@pytest.mark.parametrize('seed', [0, 1])
@pytest.mark.parametrize('r_index', range(9))
@pytest.mark.parametrize('c_index', range(9))
def test_81_models_648_runs_against_complete_auxiliary_lp_and_fraction_square(
    r_index, c_index, seed, reverse, backend, family_runs,
):
    problem, optimum, costs = _problem(r_index, c_index, seed, reverse)
    columns = _columns(problem.graph)
    assert len(columns) == 4
    for i in range(2):
        for j in range(2):
            cost, a = columns[(f'start{i}', f'middle{i}{j}', f'end{j}')]
            assert cost == costs[2*i+j]
            assert a == {'conv': 1, 'R': F(1, 8)+i, 'C': F(-1, 4)+j}
    full = _full_lp(problem, columns, backend, auxiliary=True)
    assert full.status == SolverStatus.OPTIMAL
    assert abs(F(full.objective_value)-optimum) <= F(1, 10**9)
    solver = _CountingBackend(backend)
    result = restore_dag_feasibility(problem, solver=solver)
    family_runs['runs'].append((backend.__name__, reverse, result))
    expected = (DagFeasibilityStatus.FEASIBLE_SEED_FOUND if optimum == 0 else
                DagFeasibilityStatus.POSITIVE_VIOLATION_BOUND)
    assert result.status == expected, result.message
    assert len(result.iterations) == result.auxiliary_solve_count
    assert len(solver.models) == result.auxiliary_solve_count + result.validation_solve_count
    assert result.last_valid_master_iteration == result.column_set_iteration
    assert result.column_set_iteration == len(result.iterations)
    assert set(result.last_valid_master.primal_values) == set(result.column_paths) | set(
        result.artificial_columns)
    for record in result.iterations:
        assert record.artificial_columns == result.artificial_columns
        audit = _audit_round(problem, record, columns, optimum)
        family_runs['audits'].append((backend.__name__, record is result.iterations[-1], audit))
    for names, native_costs, constant in solver.models[:result.auxiliary_solve_count]:
        assert set(result.artificial_columns) <= set(names)
        assert constant == 0
        assert all(native_costs[name] == -1 for name in result.artificial_columns)
        assert all(native_costs[name] == 0 for name in names
                   if name not in result.artificial_columns)
    if optimum == 0:
        assert result.validation_solve_count == 1
        assert result.feasible_problem.graph is problem.graph
        assert result.feasible_problem.rows == problem.rows
        assert result.feasible_problem.objective_constant == problem.objective_constant
        assert result.feasible_problem.seed_paths == tuple(result.column_paths.values())
        assert _columns(result.feasible_problem.graph) == columns
        assert set(result.feasibility_witness.primal_values) == set(result.column_paths)
        _assert_rows(problem, result.column_paths, columns,
                     result.feasibility_witness.primal_values, {})
        optimized = solve_dag_column_generation(result.feasible_problem, solver=backend())
        full_original = _full_lp(problem, columns, backend, auxiliary=False)
        assert optimized.status == DagColumnGenerationStatus.TOLERANCE_REACHED
        assert full_original.status == SolverStatus.OPTIMAL
        assert optimized.last_valid_master.objective_value == pytest.approx(
            full_original.objective_value, abs=1e-9, rel=0)
    else:
        assert result.validation_solve_count == 0
        assert result.feasible_problem is result.feasibility_witness is None
        assert abs(F(result.iterations[-1].penalty_objective)-optimum) <= F(1, 10**9)
        assert result.iterations[-1].numerical_lower_bound > 1e-9
