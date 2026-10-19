from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from math import inf, nan

import numpy as np
import pytest

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense as S
from silo.core.enums import OptimizationSense as O
from silo.core.enums import VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.solution import Solution
from silo.core.status import SolverStatus as T
from silo.core.variable import Variable
from silo.lp.optimality import check_lp_optimality
from silo.lp.simplex import basis_snapshot as bs
from silo.lp.simplex import revised as rv
from silo.lp.simplex.basis import Basis


def initial():
    return Model('full', [Variable('x'), Variable('z')],
                 [Constraint('conv', {'x': 1, 'z': 1}, S.EQ, 1),
                  Constraint('lo', {'z': 1}, S.GE, .5)],
                 Objective({'x': 0, 'z': -4}, O.MAXIMIZE, -7))


def extended(m):
    result = deepcopy(m)
    result.variables.append(Variable('q'))
    result.objective.coefficients['q'] = -1
    result.constraints[0].coefficients['q'] = 1
    result.constraints[1].coefficients['q'] = .5
    return result


class Observed(rv.RevisedSimplexSolver):
    def __init__(self, iteration_limit=10000):
        super().__init__(iteration_limit)
        self.cold = 0

    def solve_with_details(self, model, basis=None):
        self.cold += 1
        assert basis is None
        return super().solve_with_details(model, basis)


def assert_empty(solution):
    assert solution.objective_value is None
    assert not any((solution.primal_values, solution.slack_values, solution.dual_values,
                    solution.reduced_costs, solution.basis_status))


def test_full_row_cold_then_phase_two_only_and_new_dual(monkeypatch):
    solver = Observed()
    m = initial()
    first = solver.reoptimize(m)
    assert first.snapshot is not None and first.cold_solve_count == 1
    assert first.details.solution.objective_value == -9
    phases = []
    run = rv._run_primal_revised_simplex

    def observe(**kw):
        phases.append(kw['phase_name'])
        return run(**kw)

    monkeypatch.setattr(rv, '_run_primal_revised_simplex', observe)
    new = extended(m)
    warm = solver.reoptimize(new, first.snapshot)
    assert phases == ['Phase II'] and solver.cold == 1
    assert warm.used_warm_start and warm.warm_phase_two_attempted
    assert warm.cold_solve_count == warm.cold_iterations == 0
    assert warm.details.solution.objective_value == -8
    assert check_lp_optimality(new, warm.details.solution, 1e-9).passed
    assert warm.snapshot is not None and warm.snapshot != first.snapshot


@pytest.mark.parametrize('kind', (
    'row-order', 'row-sense', 'rhs', 'coefficient', 'tiny-coefficient', 'variable-order',
    'bound', 'type', 'cost', 'constant', 'direction',
))
def test_changed_old_mathematical_identity_rejects_before_warm(kind):
    solver = Observed()
    m = initial()
    snapshot = solver.reoptimize(m).snapshot
    if kind == 'row-order':
        m.constraints.reverse()
    elif kind == 'row-sense':
        m.constraints[0] = replace(m.constraints[0], sense=S.GE)
    elif kind == 'rhs':
        m.constraints[0] = replace(m.constraints[0], rhs=1 + 2**-40)
    elif kind in ('coefficient', 'tiny-coefficient'):
        m.constraints[0].coefficients['z'] += 1 if kind == 'coefficient' else 2**-40
    elif kind == 'variable-order':
        m.variables.reverse()
    elif kind == 'bound':
        m.variables[0] = Variable('x', Bounds(-2**-40, inf))
    elif kind == 'type':
        m.variables[0] = Variable('x', var_type=VariableType.INTEGER)
    elif kind == 'cost':
        m.objective.coefficients['x'] = 2**-40
    elif kind == 'constant':
        m.objective = replace(m.objective, constant=-7 + 2**-40)
    else:
        m.objective = replace(m.objective, sense=O.MINIMIZE)
    result = solver.reoptimize(m, snapshot)
    assert not result.used_warm_start and not result.warm_phase_two_attempted
    assert result.cold_solve_count == 1 and solver.cold == 2 and result.fallback_reason


def test_model_name_and_explicit_zero_do_not_change_math_identity():
    solver = Observed()
    m = initial()
    first = solver.reoptimize(m)
    m.name = 'different label'
    m.constraints[1].coefficients['x'] = 0
    del m.objective.coefficients['x']
    result = solver.reoptimize(m, first.snapshot)
    assert result.used_warm_start and result.warm_iterations == 0


def test_nonfinite_new_cost_is_rejected_before_warm():
    solver = Observed()
    m = initial()
    snapshot = solver.reoptimize(m).snapshot
    m.variables.append(Variable('bad'))
    m.objective.coefficients['bad'] = nan
    result = solver.reoptimize(m, snapshot)
    assert not result.warm_phase_two_attempted and result.cold_solve_count == 1
    assert result.details.solution.status == T.NUMERICAL_ISSUE and result.snapshot is None


@pytest.mark.parametrize('kind', ('missing', 'duplicate', 'unknown', 'artificial', 'role', 'source',
                                 'row-order', 'row-content', 'inventory', 'identity'))
def test_malformed_snapshot_content_cannot_authorize_reuse(kind):
    solver = Observed()
    m = initial()
    snapshot = solver.reoptimize(m).snapshot
    keys = snapshot.basis_keys
    changes = {
        'missing': {'basis_keys': keys[:-1]},
        'duplicate': {'basis_keys': (keys[0], keys[0])},
        'unknown': {'basis_keys': (('original', 'absent'), keys[1])},
        'artificial': {'basis_keys': (('artificial', 'conv'), keys[1])},
        'role': {'basis_keys': (('slack', 'conv'), keys[1])},
        'source': {'basis_keys': (('surplus', 'absent'), keys[1])},
        'row-order': {'row_names': snapshot.row_names[::-1]},
        'row-content': {'row_names': ('conv', 'pretend-full')},
        'inventory': {'column_keys': snapshot.column_keys[:-1]},
        'identity': {'model_identity': 'a hash is insufficient'},
    }
    result = solver.reoptimize(m, replace(snapshot, **changes[kind]))
    assert not result.warm_phase_two_attempted
    assert result.cold_solve_count == 1 and result.fallback_reason
    assert result.details.solution.status == T.OPTIMAL


@pytest.mark.parametrize('kind', ('singular', 'nonfinite'))
def test_invalid_fresh_basis_falls_back_exactly_once(monkeypatch, kind):
    m, solver = initial(), Observed()
    snapshot = solver.reoptimize(m).snapshot
    build = rv.build_standard_form
    calls = 0

    def corrupt(model):
        nonlocal calls
        calls += 1
        p = build(model)
        if calls == 1:
            matrix = tuple(tuple(0 if kind == 'singular' else nan for _ in row)
                           for row in p.matrix)
            return replace(p, matrix=matrix)
        return p

    monkeypatch.setattr(rv, 'build_standard_form', corrupt)
    result = solver.reoptimize(m, snapshot)
    assert not result.warm_phase_two_attempted and result.cold_solve_count == 1
    assert result.details.solution.status == T.OPTIMAL
    assert ('Basis solve' if kind == 'singular' else 'Nonfinite') in result.fallback_reason


def test_raw_standard_point_must_pass_original_rows_before_running_phase_two():
    m = Model('lost coefficient', [Variable('x'), Variable('z')],
              [Constraint('fix', {'z': 1}, S.EQ, 1e10),
               Constraint('cap', {'x': 1, 'z': 5e-10}, S.LE, 1)],
              Objective({}, O.MAXIMIZE))
    # Synthetic metadata: standard form is feasible after coefficient cleaning,
    # but the original cap has activity 5 > 1 at the raw basis point.
    snapshot = bs.RevisedBasisSnapshot((('original', 'z'), ('slack', 'cap')),
                                      ('fix', 'cap'),
                                      (('original', 'x'), ('original', 'z'), ('slack', 'cap')),
                                      bs.capture_identity(m))
    result = Observed().reoptimize(m, snapshot)
    assert not result.warm_phase_two_attempted and result.cold_solve_count == 1
    assert "Original point violates row 'cap'" in result.fallback_reason
    assert result.details.solution.status == T.NUMERICAL_ISSUE and result.snapshot is None


@pytest.mark.parametrize('kind', ('limit', 'numerical', 'state-missing', 'state-short',
                                 'state-nonfinite', 'bad-basis', 'false-optimal', 'linalg'))
def test_warm_failure_has_one_cold_and_separate_attempt_diagnostics(monkeypatch, kind):
    m, solver = initial(), Observed()
    snapshot = solver.reoptimize(m).snapshot
    original = rv._run_primal_revised_simplex
    injected = False

    def corrupt(**kw):
        nonlocal injected
        if injected:
            return original(**kw)
        injected = True
        if kind == 'linalg':
            raise np.linalg.LinAlgError('injected warm solve')
        result = original(**kw)
        if kind in ('limit', 'numerical'):
            status = T.ITERATION_LIMIT if kind == 'limit' else T.NUMERICAL_ISSUE
            return replace(result, status=status)
        if kind == 'state-missing':
            return replace(result, state=None)
        if kind == 'bad-basis':
            return replace(result, basis=Basis((0, 0), (1,)))
        values = result.state.primal_values.copy()
        if kind == 'state-short':
            values = values[:0]
        else:
            values[0] = nan if kind == 'state-nonfinite' else 100
        return replace(result, state=replace(result.state, primal_values=values))

    monkeypatch.setattr(rv, '_run_primal_revised_simplex', corrupt)
    result = solver.reoptimize(m, snapshot)
    assert result.warm_phase_two_attempted and not result.used_warm_start
    assert result.cold_solve_count == 1 and solver.cold == 2 and result.fallback_reason
    assert result.details.solution.status == T.OPTIMAL and result.snapshot is not None


def test_verified_warm_unbounded_then_cold_uses_guard_twice(monkeypatch):
    m, solver = initial(), Observed()
    snapshot = solver.reoptimize(m).snapshot
    m.variables.append(Variable('free_gain'))
    m.objective.coefficients['free_gain'] = 1
    calls = []
    guard = rv.check_lp_unboundedness

    def observe(model, point, direction):
        checked = guard(model, point, direction)
        calls.append(checked.passed)
        return checked

    monkeypatch.setattr(rv, 'check_lp_unboundedness', observe)
    result = solver.reoptimize(m, snapshot)
    assert calls == [True, True]
    assert result.warm_phase_two_attempted and not result.used_warm_start
    assert result.cold_solve_count == 1 and result.snapshot is None
    assert 'unbounded' in result.fallback_reason and 'verified exactly' in result.fallback_reason
    assert result.details.solution.status == T.UNBOUNDED
    assert_empty(result.details.solution)


@pytest.mark.parametrize('status', (T.ITERATION_LIMIT, T.NUMERICAL_ISSUE, T.INFEASIBLE))
def test_cold_failure_does_not_retry_or_emit_a_snapshot(status):
    class Failing(Observed):
        def solve_with_details(self, model, basis=None):
            self.cold += 1
            return rv.RevisedSimplexResult(Solution(status, primal_values={'fake': 1}))

    solver = Failing()
    result = solver.reoptimize(initial())
    assert solver.cold == result.cold_solve_count == 1 and result.snapshot is None
    assert result.details.solution.status == status
    assert_empty(result.details.solution)


def test_invalid_cold_optimal_is_rejected_once():
    class Bad(Observed):
        def solve_with_details(self, model, basis=None):
            self.cold += 1
            return rv.RevisedSimplexResult(Solution(T.OPTIMAL, objective_value=0))

    solver = Bad()
    result = solver.reoptimize(initial())
    assert solver.cold == 1 and result.details.solution.status == T.NUMERICAL_ISSUE
    assert result.snapshot is None


@pytest.mark.parametrize('kind', (
    'primal-missing', 'primal-nan', 'dual-missing', 'rc', 'objective',
))
def test_cold_bad_optimal_evidence_is_not_retried(kind):
    class Bad(Observed):
        def solve_with_details(self, model, basis=None):
            details = super().solve_with_details(model, basis)
            solution = details.solution
            changes = {
                'primal-missing': {'primal_values': {}},
                'primal-nan': {'primal_values': {'x': nan, 'z': .5}},
                'dual-missing': {'dual_values': {}},
                'rc': {'reduced_costs': {'x': 99, 'z': 99}},
                'objective': {'objective_value': 100},
            }
            return replace(details, solution=replace(solution, **changes[kind]))

    solver = Bad()
    result = solver.reoptimize(initial())
    assert result.details.solution.status == T.NUMERICAL_ISSUE
    assert result.snapshot is None and result.cold_solve_count == solver.cold == 1
    assert_empty(result.details.solution)


@pytest.mark.parametrize('kind', ('deleted-row', 'bad-source', 'duplicate-key', 'bad-partition',
                                 'no-problem', 'objective'))
def test_valid_math_and_bad_final_metadata_only_disable_snapshot(kind):
    class BadMetadata(Observed):
        def solve_with_details(self, model, basis=None):
            details = super().solve_with_details(model, basis)
            p = details.problem
            if kind == 'deleted-row':
                p = replace(p, row_names=p.row_names[:-1])
            elif kind == 'bad-source':
                p = replace(p, columns=(*p.columns[:-1],
                                       replace(p.columns[-1], source_constraint='absent')))
            elif kind == 'duplicate-key':
                p = replace(p, columns=(p.columns[0], p.columns[0], *p.columns[2:]))
            elif kind == 'no-problem':
                p = None
            elif kind == 'objective':
                p = replace(p, objective_constant=99)
            if kind == 'bad-partition':
                details = replace(details, basis=Basis((0, 0), (1,)))
            return replace(details, problem=p)

    result = BadMetadata().reoptimize(initial())
    assert result.details.solution.status == T.OPTIMAL
    assert result.snapshot is None and result.snapshot_unavailable_reason
    assert result.cold_solve_count == 1


def test_reference_is_independent_of_executable_model_mutation():
    class Mutating(Observed):
        def solve_with_details(self, model, basis=None):
            model.objective = Objective({}, O.MAXIMIZE)
            return super().solve_with_details(model, basis)

    m = initial()
    before = deepcopy(m)
    result = Mutating().reoptimize(m)
    assert m == before
    assert result.details.solution.status == T.NUMERICAL_ISSUE and result.snapshot is None


def test_snapshot_and_new_details_are_defensive_read_only_values():
    m, solver = initial(), Observed()
    result = solver.reoptimize(m)
    snapshot = result.snapshot
    before = deepcopy(snapshot)
    m.constraints[0].coefficients['x'] = 4
    m.variables.reverse()
    assert snapshot == before
    with pytest.raises(FrozenInstanceError):
        snapshot.row_names = ()
    with pytest.raises(FrozenInstanceError):
        snapshot.model_identity.rows[0].rhs = 3
    with pytest.raises(TypeError):
        result.details.solution.primal_values['x'] = 4
    with pytest.raises(TypeError):
        result.details.problem.matrix[0][0] = 4
    assert result.details.solution.objective_value == -9


def test_zero_budget_is_per_run_and_fresh_cold_is_not_retried():
    m = initial()
    snapshot = Observed().reoptimize(m).snapshot
    result = Observed(iteration_limit=0).reoptimize(m, snapshot)
    assert result.warm_phase_two_attempted and result.warm_iterations == 0
    assert result.cold_solve_count == 1 and result.cold_iterations == 0
    assert result.details.solution.status == T.ITERATION_LIMIT and result.snapshot is None


@pytest.mark.parametrize('where', ('map', 'warm', 'cold', 'qualification'))
def test_programming_runtime_errors_are_visible(monkeypatch, where):
    m, solver = initial(), Observed()
    snapshot = solver.reoptimize(m).snapshot

    def bug(*args, **kw):
        raise RuntimeError('programming error')

    if where == 'map':
        monkeypatch.setattr(rv, 'map_snapshot', bug)
    elif where == 'warm':
        monkeypatch.setattr(rv, '_run_primal_revised_simplex', bug)
    elif where == 'cold':
        snapshot = None
        monkeypatch.setattr(solver, 'solve_with_details', bug)
    else:
        monkeypatch.setattr(rv, 'make_snapshot', bug)
    with pytest.raises(RuntimeError, match='programming error'):
        solver.reoptimize(m, snapshot)
