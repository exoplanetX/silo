from dataclasses import FrozenInstanceError
from math import nan

import pytest

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense as S
from silo.core.enums import OptimizationSense as O
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus as T
from silo.core.variable import Variable
from silo.decomposition import RestrictedMasterProblem, RestrictedMasterReoptimizationResult
from silo.decomposition import restricted_master as rmp
from silo.lp.optimality import LPOptimalityCheck
from silo.lp.simplex import revised as rv
from silo.lp.simplex.tableau import TableauSimplexSolver


def make(names, costs, rows, constant=0):
    return Model('minimum', [Variable(n) for n in names], list(rows),
                 Objective(dict(zip(names, costs, strict=True)), O.MINIMIZE, constant))


def degenerate():
    return make(['x'], [2], [Constraint('conv', {'x': 1}, S.EQ, 1),
                            Constraint('cap', {}, S.LE, 0)])


class Observed(rv.RevisedSimplexSolver):
    def __init__(self):
        super().__init__()
        self.cold = 0
        self.arguments = []
        self.outcomes = []

    def solve_with_details(self, m, basis=None):
        self.cold += 1
        assert basis is None
        return super().solve_with_details(m, basis)

    def reoptimize(self, m, snapshot=None):
        self.arguments.append(snapshot)
        result = super().reoptimize(m, snapshot)
        self.outcomes.append(result)
        return result


def test_A_initial_cold_then_improving_equality_warm():
    m = make(['p0', 'p2'], [0, 10], [Constraint('conv', {'p0': 1, 'p2': 1}, S.EQ, 1),
                                   Constraint('r', {'p2': 2}, S.GE, .5)], 7)
    owner, solver = RestrictedMasterProblem(m), Observed()
    first = owner.solve_reoptimized(solver)
    owner.add_column(name='p1', cost=4, row_coefficients={'conv': 1, 'r': 1})
    second = owner.solve_reoptimized(solver)
    assert [r.result.objective_value for r in (first, second)] == [9.5, 9]
    assert second.used_warm_start and second.cold_solve_count == 0 and solver.cold == 1
    assert isinstance(second, RestrictedMasterReoptimizationResult)


def test_B_actual_zero_step_pivot_and_shifted_structural_basis(monkeypatch):
    owner, solver = RestrictedMasterProblem(degenerate()), Observed()
    first = owner.solve_reoptimized(solver)
    snapshot = solver.outcomes[-1].snapshot
    old_slack = solver.outcomes[-1].details.problem.columns.index(
        next(c for c in solver.outcomes[-1].details.problem.columns if c.role == 'slack'))
    entries, ratios = [], []
    run, leaving = rv._run_primal_revised_simplex, rv._choose_leaving_row

    def observe(**kw):
        entries.append((kw['problem'], kw['basis'], kw['phase_name']))
        return run(**kw)

    def observe_ratio(basic_values, direction):
        row = leaving(basic_values, direction)
        if row is not None:
            ratios.append(basic_values[row] / direction[row])
        return row

    monkeypatch.setattr(rv, '_run_primal_revised_simplex', observe)
    monkeypatch.setattr(rv, '_choose_leaving_row', observe_ratio)
    owner.add_column(name='q', cost=0, row_coefficients={'conv': 1, 'cap': 1})
    second = owner.solve_reoptimized(solver)
    assert second.used_warm_start and second.warm_iterations >= 1 and 0 in ratios
    assert len(entries) == 1 and entries[0][2] == 'Phase II'
    problem, basis, _ = entries[0]
    keys = tuple((problem.columns[j].role, problem.columns[j].original_name
                  if problem.columns[j].role == 'original' else
                  problem.columns[j].source_constraint) for j in basis.basic_columns)
    assert keys == snapshot.basis_keys
    slack = next(j for j, c in enumerate(problem.columns) if c.role == 'slack')
    assert slack in basis.basic_columns and slack != old_slack
    owner.add_column(name='r', cost=-1, row_coefficients={'conv': 1})
    third = owner.solve_reoptimized(solver)
    assert third.used_warm_start and solver.cold == 1
    assert [o.result.objective_value for o in (first, second, third)] == [2, 2, -1]


@pytest.mark.parametrize('reverse_rows', (False, True))
@pytest.mark.parametrize('q_row', ('a', 'b'))
def test_C_deleted_projection_cannot_be_reused_then_rank_recovery_can(reverse_rows, q_row):
    rows = [Constraint('a', {'x': 1}, S.EQ, 1), Constraint('b', {'x': 1}, S.EQ, 1)]
    owner = RestrictedMasterProblem(make(['x'], [2], rows[::-1] if reverse_rows else rows))
    solver = Observed()
    first = owner.solve_reoptimized(solver)
    assert first.result.status == T.OPTIMAL and not first.snapshot_available
    assert 'deleted' in first.snapshot_unavailable_reason
    owner.add_column(name='q', cost=0, row_coefficients={q_row: 1})
    second = owner.solve_reoptimized(solver)
    assert second.cold_solve_count == 1 and not second.warm_phase_two_attempted
    assert solver.arguments[-1] is None and second.snapshot_available
    owner.add_column(name='r', cost=-1, row_coefficients={'a': 1, 'b': 1})
    third = owner.solve_reoptimized(solver)
    assert third.used_warm_start and third.cold_solve_count == 0 and solver.cold == 2
    assert [o.result.objective_value for o in (first, second, third)] == [2, 2, -1]
    assert len(solver.outcomes[-1].details.problem.row_names) == 2


def test_two_independent_equalities_skip_multiple_fresh_artificials():
    owner = RestrictedMasterProblem(make(['x', 'y'], [0, 4],
        [Constraint('conv', {'x': 1, 'y': 1}, S.EQ, 1),
         Constraint('balance', {'y': 1}, S.EQ, .5)], 7))
    solver = Observed()
    results = [owner.solve_reoptimized(solver)]
    for name, cost in (('q', 1), ('r', 0)):
        owner.add_column(name=name, cost=cost, row_coefficients={'conv': 1, 'balance': .5})
        results.append(owner.solve_reoptimized(solver))
    assert [r.result.objective_value for r in results] == [9, 8, 7]
    assert all(r.used_warm_start for r in results[1:]) and solver.cold == 1


def test_multi_append_reserved_looking_names_and_equal_vectors():
    owner, solver = RestrictedMasterProblem(degenerate()), Observed()
    owner.solve_reoptimized(solver)
    owner.add_column(name='slack_cap', cost=1, row_coefficients={'conv': 1})
    owner.add_column(name='artificial_conv', cost=1, row_coefficients={'conv': 1})
    result = owner.solve_reoptimized(solver)
    assert result.used_warm_start and result.result.objective_value == 1
    assert set(result.result.primal_values) == {'x', 'slack_cap', 'artificial_conv'}
    assert owner.solve_reoptimized(solver).warm_iterations == 0


@pytest.mark.parametrize('bound_cost', (2**-24, -2**-24))
def test_no_row_append_small_cost_and_constant(bound_cost):
    owner = RestrictedMasterProblem(make(['x'], [bound_cost], [], -3))
    solver = Observed()
    result = owner.solve_reoptimized(solver)
    if bound_cost > 0:
        assert result.result.objective_value == -3 and result.snapshot_available
        owner.add_column(name='z', cost=bound_cost, row_coefficients={})
        assert owner.solve_reoptimized(solver).used_warm_start
    else:
        assert result.result.status == T.UNBOUNDED and not result.snapshot_available


def test_empty_basis_can_be_reused_after_first_variable_is_appended():
    owner = RestrictedMasterProblem(make([], [], [], 5))
    first = owner.solve_reoptimized()
    assert first.snapshot_available and first.result.objective_value == 5
    owner.add_column(name='x', cost=2, row_coefficients={})
    second = owner.solve_reoptimized()
    assert second.used_warm_start and second.warm_iterations == 0
    assert second.result.primal_values == {'x': 0} and second.result.objective_value == 5


def test_ordinary_cold_solve_clears_opt_in_cache_even_with_tableau():
    owner, solver = RestrictedMasterProblem(degenerate()), Observed()
    owner.solve_reoptimized(solver)
    result = owner.solve(TableauSimplexSolver())
    assert result.objective_value == 2
    fresh = owner.solve_reoptimized(solver)
    assert fresh.cold_solve_count == 1 and solver.arguments[-1] is None
    assert not fresh.warm_phase_two_attempted


@pytest.mark.parametrize('kind', ('duplicate', 'unknown-row', 'nonfinite'))
def test_failed_atomic_add_keeps_model_and_cache(kind):
    owner, solver = RestrictedMasterProblem(degenerate()), Observed()
    old = owner.solve_reoptimized(solver)
    with pytest.raises(ValueError):
        owner.add_column(name='x' if kind == 'duplicate' else 'bad',
                         cost=nan if kind == 'nonfinite' else 0,
                         row_coefficients={'absent': 1} if kind == 'unknown-row' else {})
    again = owner.solve_reoptimized(solver)
    assert again.used_warm_start and again.result.objective_value == old.result.objective_value
    assert set(again.result.primal_values) == {'x'}


@pytest.mark.parametrize('backend', (TableauSimplexSolver(), object()))
def test_incompatible_backend_parameter_does_not_touch_cache(backend):
    owner, solver = RestrictedMasterProblem(degenerate()), Observed()
    owner.solve_reoptimized(solver)
    with pytest.raises(TypeError, match='Revised'):
        owner.solve_reoptimized(backend)
    assert owner.solve_reoptimized(solver).used_warm_start


def test_instance_input_and_historical_result_isolation():
    m = degenerate()
    left, right = RestrictedMasterProblem(m), RestrictedMasterProblem(m)
    a, b = Observed(), Observed()
    first = left.solve_reoptimized(a)
    right.solve_reoptimized(b)
    m.constraints[0].coefficients['x'] = 99
    left.add_column(name='q', cost=1, row_coefficients={'conv': 1})
    assert left.solve_reoptimized(a).result.objective_value == 1
    assert right.solve_reoptimized(b).result.objective_value == 2
    assert first.result.primal_values == {'x': 1}
    with pytest.raises(TypeError):
        first.result.dual_values['conv'] = 99
    with pytest.raises(FrozenInstanceError):
        first.used_warm_start = True
    assert a.outcomes[0].snapshot is not b.outcomes[0].snapshot


def test_final_rmp_verification_failure_clears_lp_qualified_cache(monkeypatch):
    owner, solver = RestrictedMasterProblem(degenerate()), Observed()
    owner.solve_reoptimized(solver)
    with monkeypatch.context() as patch:
        patch.setattr(rmp, 'check_lp_optimality',
                      lambda *a, **kw: LPOptimalityCheck(False, message='RMP layer rejection'))
        failed = owner.solve_reoptimized(solver)
    assert solver.outcomes[-1].snapshot is not None  # LP independently accepted
    assert failed.result.status == T.NUMERICAL_ISSUE and not failed.snapshot_available
    assert failed.warm_phase_two_attempted and not failed.used_warm_start
    fresh = owner.solve_reoptimized(solver)
    assert fresh.cold_solve_count == 1 and solver.arguments[-1] is None


def test_cold_failure_clears_cache_and_later_fresh_success_reestablishes_it():
    owner, solver = RestrictedMasterProblem(degenerate()), Observed()
    owner.solve_reoptimized(solver)
    solver.iteration_limit = 0
    failed = owner.solve_reoptimized(solver)
    assert failed.warm_phase_two_attempted and failed.cold_solve_count == 1
    assert failed.result.status == T.ITERATION_LIMIT and not failed.snapshot_available
    assert not failed.result.primal_values and failed.result.objective_value is None
    solver.iteration_limit = 10000
    fresh = owner.solve_reoptimized(solver)
    assert fresh.cold_solve_count == 1 and solver.arguments[-1] is None and fresh.snapshot_available
    assert owner.solve_reoptimized(solver).used_warm_start
    solver.iteration_limit = 0
    owner.solve(solver)  # later ordinary cold failure must also clear the current cache
    solver.iteration_limit = 10000
    assert owner.solve_reoptimized(solver).cold_solve_count == 1


def test_mutating_compatible_backend_cannot_rewrite_rmp_reference():
    class Mutating(Observed):
        def reoptimize(self, model, snapshot=None):
            model.objective = Objective({}, O.MAXIMIZE)
            return super().reoptimize(model, snapshot)

    owner = RestrictedMasterProblem(degenerate())
    failed = owner.solve_reoptimized(Mutating())
    assert failed.result.status == T.NUMERICAL_ISSUE and not failed.snapshot_available
    assert owner.solve_reoptimized().result.objective_value == 2


def test_default_opt_in_and_old_solve_use_separate_paths(monkeypatch):
    owner = RestrictedMasterProblem(degenerate())
    assert owner.solve_reoptimized().result.objective_value == 2
    with monkeypatch.context() as patch:
        def forbidden(*args, **kw):
            raise RuntimeError('ordinary solve called opt-in')
        patch.setattr(rv.RevisedSimplexSolver, 'reoptimize', forbidden)
        assert owner.solve().objective_value == 2


def test_rmp_programming_error_remains_visible():
    class Broken(rv.RevisedSimplexSolver):
        def reoptimize(self, model, snapshot=None):
            raise RuntimeError('programming error')

    with pytest.raises(RuntimeError, match='programming error'):
        RestrictedMasterProblem(degenerate()).solve_reoptimized(Broken())
