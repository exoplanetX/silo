"""Natural mechanisms and separately marked failure/lifecycle injections."""

from dataclasses import FrozenInstanceError, replace

import numpy as np
import pytest

from silo.core.enums import ConstraintSense as S
from silo.core.status import SolverStatus as T
from silo.decomposition import dag_column_generation as cg
from silo.decomposition import dag_feasibility as df
from silo.decomposition.dag_pricing import (
    DagArc,
    DagPricingProblem,
    DagPricingResult,
    DagPricingStatus,
)
from silo.decomposition.restricted_master import RestrictedMasterProblem, RestrictedMasterResult
from silo.lp.simplex import revised as rv
from silo.lp.simplex.tableau import TableauSimplexSolver


def mechanism_a():
    graph = DagPricingProblem(('s', 't'), [DagArc('x', 's', 't', 2),
        DagArc('q', 's', 't', 0, {'cap': 1}), DagArc('r', 's', 't', 1)],
        's', 't', ('conv', 'cap'), base_coefficients={'conv': 1})
    return cg.DagColumnGenerationProblem(graph, [cg.DagMasterRow('conv', S.EQ, 1),
        cg.DagMasterRow('cap', S.LE, 0)], 'conv', [('x',)])


def mechanism_b():
    graph = DagPricingProblem(('s', 't'), [DagArc('d1', 's', 't', 4, {'R': 1, 'C': 1}),
        DagArc('d2', 's', 't', 6), DagArc('o12', 's', 't', 1, {'R': 1}),
        DagArc('o21', 's', 't', 2, {'C': 1})], 's', 't', ('conv', 'R', 'C'),
        base_coefficients={'conv': 1})
    return cg.DagColumnGenerationProblem(graph, [cg.DagMasterRow('conv', S.EQ, 1),
        cg.DagMasterRow('R', S.EQ, .5), cg.DagMasterRow('C', S.EQ, .5)],
        'conv', [('d1',), ('d2',)], -3)


def seed_only():
    p = mechanism_a()
    return replace(p, graph=replace(p.graph, arcs=p.graph.arcs[:1]))


class Observed(rv.RevisedSimplexSolver):
    def __init__(self, limit=10000):
        super().__init__(limit)
        self.in_cold = False
        self.cold = 0
        self.round = 0
        self.snapshots = []
        self.outcomes = []

    def reoptimize(self, model, snapshot=None):
        self.round += 1
        self.snapshots.append(snapshot)
        result = super().reoptimize(model, snapshot)
        self.outcomes.append(result)
        return result

    def solve_with_details(self, model, basis=None):
        self.cold += 1
        self.in_cold = True
        try:
            return super().solve_with_details(model, basis)
        finally:
            self.in_cold = False


def watch_masters(monkeypatch, include_recovery=False):
    owners = []

    class Master(RestrictedMasterProblem):
        def __init__(self, model):
            super().__init__(model)
            self.original_constant = model.objective.constant
            self.original_costs = dict(model.objective.coefficients)
            self.cold_calls, self.optin_calls, self.outcomes = 0, 0, []
            owners.append(self)

        def solve(self, solver=None):
            self.cold_calls += 1
            return super().solve(solver)

        def solve_reoptimized(self, solver=None):
            self.optin_calls += 1
            outcome = super().solve_reoptimized(solver)
            self.outcomes.append(outcome)
            return outcome

    monkeypatch.setattr(cg, 'RestrictedMasterProblem', Master)
    if include_recovery:
        monkeypatch.setattr(df, 'RestrictedMasterProblem', Master)
    return owners


def assert_empty_bounds(record):
    assert record.numerical_upper_bound is record.dual_objective is record.rho is None
    assert record.numerical_lower_bound is record.numerical_gap is record.accepted_path is None
    assert record.objective_gap is record.roundoff_allowance is None


def test_A_real_zero_step_warm_and_one_owner(monkeypatch):
    owners = watch_masters(monkeypatch)
    solver = Observed()
    phases, ratios = [], []
    run, leaving = rv._run_primal_revised_simplex, rv._choose_leaving_row

    def observe(**kw):
        phases.append((solver.round, solver.in_cold, kw['phase_name']))
        return run(**kw)

    def ratio(values, direction):
        row = leaving(values, direction)
        if solver.round == 2 and not solver.in_cold and row is not None:
            ratios.append(values[row]/direction[row])
        return row

    monkeypatch.setattr(rv, '_run_primal_revised_simplex', observe)
    monkeypatch.setattr(rv, '_choose_leaving_row', ratio)
    result = cg.solve_dag_column_generation(mechanism_a(), solver=solver, reoptimize_rmp=True)
    assert result.status == cg.DagColumnGenerationStatus.TOLERANCE_REACHED
    assert [r.master_result.objective_value for r in result.iterations] == [2, 2, 1]
    assert [r.rmp_reoptimization.used_warm_start for r in result.iterations] == [False, True, True]
    assert result.iterations[1].rmp_reoptimization.warm_iterations >= 1 and 0 in ratios
    assert [p for p in phases if p[0] == 2] == [(2, False, 'Phase II')]
    assert solver.cold == 1 and len(owners) == 1
    assert owners[0].cold_calls == 0 and owners[0].optin_calls == 3
    assert all(r.master_result is r.rmp_reoptimization.result for r in result.iterations)


def test_B_projection_rank_recovery_is_cold_cold_warm(monkeypatch):
    owners = watch_masters(monkeypatch)
    solver = Observed()
    result = cg.solve_dag_column_generation(mechanism_b(), solver=solver, reoptimize_rmp=True)
    assert [r.master_result.objective_value for r in result.iterations] == [2, 2, -1.5]
    outcomes = [r.rmp_reoptimization for r in result.iterations]
    assert [o.cold_solve_count for o in outcomes] == [1, 1, 0]
    assert [o.snapshot_available for o in outcomes] == [False, True, True]
    assert [o.used_warm_start for o in outcomes] == [False, False, True]
    assert solver.snapshots[:2] == [None, None]
    assert solver.outcomes[-1].details.problem.row_names == ('conv', 'R', 'C')
    assert len(owners) == 1 and owners[0].cold_calls == 0


@pytest.mark.parametrize('factory,expected,cold', (
    (mechanism_a, [2, 2, 1], [1, 0, 0]),
    (mechanism_b, [2, 2, -1.5], [1, 1, 0]),
))
def test_literal_mechanisms_in_all_three_modes(factory, expected, cold):
    for kwargs in ({}, {'solver': TableauSimplexSolver()},
                   {'solver': Observed(), 'reoptimize_rmp': True}):
        result = cg.solve_dag_column_generation(factory(), **kwargs)
        assert result.status == cg.DagColumnGenerationStatus.TOLERANCE_REACHED
        assert [r.master_result.objective_value for r in result.iterations] == expected
        if kwargs.get('reoptimize_rmp'):
            assert [r.rmp_reoptimization.cold_solve_count for r in result.iterations] == cold
        else:
            assert all(r.rmp_reoptimization is None for r in result.iterations)


@pytest.mark.parametrize('bad', (0, 1, 'True', '', None, [], {}, np.bool_(True)))
def test_strict_boolean_rejected_before_any_work(monkeypatch, bad):
    def forbidden(*a, **kw):
        raise RuntimeError('must reject before work')
    monkeypatch.setattr(cg, 'RestrictedMasterProblem', forbidden)
    monkeypatch.setattr(cg, 'price_dag', forbidden)
    with pytest.raises(TypeError, match='bool'):
        cg.solve_dag_column_generation(mechanism_a(), reoptimize_rmp=bad)


@pytest.mark.parametrize('backend', (TableauSimplexSolver(), object()))
def test_true_rejects_non_revised_before_rmp_lp_or_pricing(monkeypatch, backend):
    def forbidden(*a, **kw):
        raise RuntimeError('must reject before work')
    monkeypatch.setattr(cg, 'RestrictedMasterProblem', forbidden)
    monkeypatch.setattr(cg, 'price_dag', forbidden)
    with pytest.raises(TypeError, match='Revised'):
        cg.solve_dag_column_generation(mechanism_a(), solver=backend, reoptimize_rmp=True)


def test_default_false_and_legacy_backend_never_call_opt_in(monkeypatch):
    def forbidden(*a, **kw):
        raise RuntimeError('unexpected opt-in')
    monkeypatch.setattr(RestrictedMasterProblem, 'solve_reoptimized', forbidden)
    first = cg.solve_dag_column_generation(mechanism_a())
    explicit = cg.solve_dag_column_generation(mechanism_a(), reoptimize_rmp=False)
    assert first == explicit

    class Legacy:
        def __init__(self):
            self.calls = 0

        def solve(self, model):
            self.calls += 1
            return rv.RevisedSimplexSolver().solve(model)

    legacy = Legacy()
    for solver in (TableauSimplexSolver(), legacy):
        result = cg.solve_dag_column_generation(mechanism_a(), solver=solver,
                                                reoptimize_rmp=False)
        assert result.status == cg.DagColumnGenerationStatus.TOLERANCE_REACHED
        assert all(r.rmp_reoptimization is None for r in result.iterations)
    assert legacy.calls == 3


def test_no_improvement_first_round_and_new_owner_every_run(monkeypatch):
    owners = watch_masters(monkeypatch)
    solver = Observed()
    saved = []
    for _ in range(2):
        result = cg.solve_dag_column_generation(seed_only(), solver=solver, reoptimize_rmp=True)
        saved.append(result)
        assert len(result.iterations) == 1
        assert result.iterations[0].rmp_reoptimization.cold_solve_count == 1
    assert len(owners) == 2 and owners[0] is not owners[1]
    assert solver.snapshots == [None, None] and solver.cold == 2
    assert (saved[0].iterations[0].rmp_reoptimization
            is not saved[1].iterations[0].rmp_reoptimization)


@pytest.mark.parametrize('limit,status', ((1, 'ITERATION_LIMIT'), (2, 'ITERATION_LIMIT'),
                                       (3, 'TOLERANCE_REACHED')))
def test_outer_budget_counts_solved_rounds_and_does_not_append_unsolved_column(limit, status):
    solver = Observed()
    result = cg.solve_dag_column_generation(mechanism_a(), solver=solver,
                                            iteration_limit=limit, reoptimize_rmp=True)
    assert result.status == getattr(cg.DagColumnGenerationStatus, status)
    assert len(result.iterations) == len(result.column_paths) == limit
    assert result.iterations[-1].accepted_path is None
    assert result.column_set_iteration == result.last_valid_master_iteration == limit
    assert all(r.rmp_reoptimization is not None for r in result.iterations)


def inject_warm_failure(monkeypatch, solver, both=False):
    original = rv._run_primal_revised_simplex
    events = []

    def fail(**kw):
        if solver.round == 2 and (not solver.in_cold or both):
            events.append('cold' if solver.in_cold else 'warm')
            return rv.RevisedRunResult(T.NUMERICAL_ISSUE, kw['basis'],
                                        message='injected kernel failure')
        return original(**kw)

    monkeypatch.setattr(rv, '_run_primal_revised_simplex', fail)
    return events


@pytest.mark.parametrize('after', ('none', 'pricing', 'candidate', 'gap'))
@pytest.mark.parametrize('fail_warm', (False, True))
def test_warm_or_single_fallback_then_downstream_branch_keeps_final_evidence(
    monkeypatch, after, fail_warm,
):
    owners = watch_masters(monkeypatch)
    solver = Observed()
    events = inject_warm_failure(monkeypatch, solver) if fail_warm else []
    prices = []
    pricing, objective = cg.price_dag, cg._master_objectives

    def price(*a, **kw):
        prices.append(a[1])
        if solver.round == 2 and after == 'pricing':
            return DagPricingResult(DagPricingStatus.NO_PATH)
        result = pricing(*a, **kw)
        return replace(result, cost=result.cost + 1) if solver.round == 2 and after == 'candidate' \
            else result

    def master_objectives(*a):
        upper, dual, p, d = objective(*a)
        return (upper, dual, (*p, -100), d) if solver.round == 2 and after == 'gap' else (
            upper, dual, p, d)

    monkeypatch.setattr(cg, 'price_dag', price)
    monkeypatch.setattr(cg, '_master_objectives', master_objectives)
    result = cg.solve_dag_column_generation(mechanism_a(), solver=solver, reoptimize_rmp=True)
    record = result.iterations[1]
    outcome = record.rmp_reoptimization
    assert events == (['warm'] if fail_warm else []) and outcome.warm_phase_two_attempted
    assert outcome.used_warm_start is not fail_warm
    assert outcome.cold_solve_count == int(fail_warm) and solver.cold == 1 + int(fail_warm)
    assert bool(outcome.fallback_reason) is fail_warm
    assert prices[1] is outcome.result.dual_values and record.master_result is outcome.result
    assert len(owners) == 1 and owners[0].cold_calls == 0
    assert owners[0].optin_calls == len(result.iterations) == len(prices)
    if after == 'none':
        assert result.status == cg.DagColumnGenerationStatus.TOLERANCE_REACHED
        assert len(result.iterations) == 3 and record.accepted_path == ('r',)
    else:
        assert result.status == (cg.DagColumnGenerationStatus.PRICING_FAILURE if after == 'pricing'
                                 else cg.DagColumnGenerationStatus.NUMERICAL_ISSUE)
        assert_empty_bounds(record)
        assert result.last_valid_master is record.master_result
        assert result.column_set_iteration == result.last_valid_master_iteration == 2
        assert dict(result.column_paths) == dict(record.column_paths)


def test_warm_and_internal_cold_both_fail_without_extra_cg_retry_or_pricing(monkeypatch):
    owners = watch_masters(monkeypatch)
    solver = Observed()
    events = inject_warm_failure(monkeypatch, solver, both=True)
    prices = []
    original = cg.price_dag

    def price(*a, **kw):
        prices.append(a[1])
        return original(*a, **kw)

    monkeypatch.setattr(cg, 'price_dag', price)
    result = cg.solve_dag_column_generation(mechanism_a(), solver=solver, reoptimize_rmp=True)
    assert result.status == cg.DagColumnGenerationStatus.MASTER_FAILURE
    assert events == ['warm', 'cold'] and len(prices) == 1
    assert owners[0].optin_calls == 2 and owners[0].cold_calls == 0 and solver.cold == 2
    failed = result.iterations[1]
    assert failed.rmp_reoptimization.result.status == T.NUMERICAL_ISSUE
    assert failed.rmp_reoptimization.cold_solve_count == 1
    assert failed.pricing_result is None
    assert_empty_bounds(failed)
    assert result.last_valid_master is result.iterations[0].master_result
    assert result.last_valid_master_iteration == result.column_set_iteration == 1
    assert len(result.column_paths) == 1 and len(failed.column_paths) == 2
    # Reusing the solver must still create a new CG owner and first cold.
    again = cg.solve_dag_column_generation(seed_only(), solver=solver, reoptimize_rmp=True)
    assert again.iterations[0].rmp_reoptimization.cold_solve_count == 1
    assert solver.snapshots[-1] is None and owners[-1] is not owners[0]


@pytest.mark.parametrize('status', (T.INFEASIBLE, T.UNBOUNDED, T.ITERATION_LIMIT,
                                  T.ERROR, T.NUMERICAL_ISSUE))
def test_synthetic_first_master_failure_retains_outcome_and_registry(monkeypatch, status):
    original = RestrictedMasterProblem.solve_reoptimized

    def failed(self, solver=None):
        outcome = original(self, solver)
        return replace(outcome, result=RestrictedMasterResult(status, message='synthetic master'))

    monkeypatch.setattr(RestrictedMasterProblem, 'solve_reoptimized', failed)
    def forbidden(*a, **kw):
        raise RuntimeError('Nonoptimal master must not trigger pricing.')
    monkeypatch.setattr(cg, 'price_dag', forbidden)
    result = cg.solve_dag_column_generation(mechanism_a(), reoptimize_rmp=True)
    assert result.status == cg.DagColumnGenerationStatus.MASTER_FAILURE
    assert len(result.iterations) == 1 and result.last_valid_master is None
    assert result.last_valid_master_iteration is None and result.column_set_iteration == 1
    record = result.iterations[0]
    assert record.master_result is record.rmp_reoptimization.result
    assert record.master_result.status == status and record.pricing_result is None
    assert_empty_bounds(record)


@pytest.mark.parametrize('round_number', (1, 2))
def test_original_master_validation_failure_retains_previous_valid_round(monkeypatch, round_number):
    original = RestrictedMasterProblem.solve_reoptimized
    count = 0

    def corrupt(self, solver=None):
        nonlocal count
        count += 1
        outcome = original(self, solver)
        if count == round_number:
            return replace(outcome, result=replace(outcome.result, primal_values={'absent': 1}))
        return outcome

    monkeypatch.setattr(RestrictedMasterProblem, 'solve_reoptimized', corrupt)
    result = cg.solve_dag_column_generation(mechanism_a(), reoptimize_rmp=True)
    assert result.status == cg.DagColumnGenerationStatus.NUMERICAL_ISSUE
    failed = result.iterations[-1]
    assert failed.rmp_reoptimization is not None and failed.pricing_result is None
    assert_empty_bounds(failed)
    assert result.last_valid_master_iteration == (None if round_number == 1 else 1)
    if round_number == 2:
        assert len(result.column_paths) == 1 and len(failed.column_paths) == 2


def test_seed_reconstruction_failure_has_no_rmp_or_diagnostic_history(monkeypatch):
    graph = DagPricingProblem(('s', 'm', 't'), [DagArc('a', 's', 'm', 1e308),
        DagArc('b', 'm', 't', 1e308)], 's', 't', ('conv',), base_coefficients={'conv': 1})
    problem = cg.DagColumnGenerationProblem(graph, [cg.DagMasterRow('conv', S.EQ, 1)],
                                            'conv', [('a', 'b')])
    owners = watch_masters(monkeypatch)
    result = cg.solve_dag_column_generation(problem, reoptimize_rmp=True)
    assert result.status == cg.DagColumnGenerationStatus.NUMERICAL_ISSUE
    assert not owners and not result.iterations and not result.column_paths
    assert result.column_set_iteration is None and result.failure_iteration == 1


def test_independent_inner_budget_is_a_master_failure_without_outer_retry(monkeypatch):
    owners = watch_masters(monkeypatch)
    result = cg.solve_dag_column_generation(mechanism_a(), solver=Observed(0),
                                            iteration_limit=100, reoptimize_rmp=True)
    assert result.status == cg.DagColumnGenerationStatus.MASTER_FAILURE
    assert len(result.iterations) == owners[0].optin_calls == 1
    assert result.iterations[0].rmp_reoptimization.cold_solve_count == 1
    assert result.iterations[0].rmp_reoptimization.cold_iterations == 0


def test_successful_internal_fallback_still_obeys_last_outer_round(monkeypatch):
    solver = Observed()
    inject_warm_failure(monkeypatch, solver)
    result = cg.solve_dag_column_generation(mechanism_a(), solver=solver,
                                            iteration_limit=2, reoptimize_rmp=True)
    assert result.status == cg.DagColumnGenerationStatus.ITERATION_LIMIT
    assert len(result.iterations) == 2 and len(result.column_paths) == 2
    assert result.iterations[1].accepted_path is None
    assert result.iterations[1].rmp_reoptimization.cold_solve_count == 1
    assert solver.cold == 2


def test_restore_then_explicit_economic_cg_has_fresh_owner_and_original_costs(monkeypatch):
    graph = DagPricingProblem(('s', 't'), [DagArc(f'p{i}', 's', 't', cost, {'r': i})
        for i, cost in enumerate((0, 4, 10))], 's', 't', ('conv', 'r'),
        base_coefficients={'conv': 1})
    problem = cg.DagColumnGenerationProblem(graph, [cg.DagMasterRow('conv', S.EQ, 1),
        cg.DagMasterRow('r', S.GE, .5)], 'conv', [('p0',)], 7)
    owners = watch_masters(monkeypatch, include_recovery=True)
    solver = Observed()
    restored = df.restore_dag_feasibility(problem, solver=solver)
    assert restored.status == df.DagFeasibilityStatus.FEASIBLE_SEED_FOUND
    assert not solver.snapshots  # Auxiliary/validation stages only use ordinary solves.
    old_owners = tuple(owners)
    result = cg.solve_dag_column_generation(restored.feasible_problem, solver=solver,
                                            reoptimize_rmp=True)
    assert result.status == cg.DagColumnGenerationStatus.TOLERANCE_REACHED
    assert result.last_valid_master.objective_value == 9
    assert solver.snapshots[0] is None
    assert result.iterations[0].rmp_reoptimization.cold_solve_count == 1
    economic = owners[-1]
    assert all(economic is not owner for owner in old_owners)
    assert economic.original_constant == 7 and set(economic.original_costs.values()) == {0, 10}
    assert all(owner.optin_calls == 0 for owner in old_owners)
    assert economic.optin_calls == len(result.iterations) and economic.cold_calls == 0


def test_iteration_positional_compatibility_and_all_exposed_maps_are_read_only():
    original_registry = {'p': ['x']}
    master = RestrictedMasterResult(T.OPTIMAL)
    old = cg.DagColumnGenerationIteration(1, original_registry, master, None,
                                         None, None, None, None, None, None, None, None)
    original_registry['p'].append('mutated')
    assert old.rmp_reoptimization is None and old.column_paths == {'p': ('x',)}
    assert replace(old, iteration=2).rmp_reoptimization is None
    result = cg.solve_dag_column_generation(mechanism_a(), reoptimize_rmp=True)
    record = result.iterations[0]
    with pytest.raises(FrozenInstanceError):
        record.rmp_reoptimization = None
    with pytest.raises(FrozenInstanceError):
        record.rmp_reoptimization.used_warm_start = True
    for mapping in (record.column_paths, result.column_paths,
                    record.rmp_reoptimization.result.dual_values):
        with pytest.raises(TypeError):
            mapping['bad'] = 9


def test_new_run_after_pricing_exception_starts_with_fresh_cold_owner(monkeypatch):
    owners = watch_masters(monkeypatch)
    solver = Observed()
    pricing = cg.price_dag

    with monkeypatch.context() as patch:
        def broken(*a, **kw):
            if solver.round == 2:
                raise RuntimeError('exception after warm')
            return pricing(*a, **kw)
        patch.setattr(cg, 'price_dag', broken)
        with pytest.raises(RuntimeError, match='after warm'):
            cg.solve_dag_column_generation(mechanism_a(), solver=solver, reoptimize_rmp=True)
    result = cg.solve_dag_column_generation(seed_only(), solver=solver, reoptimize_rmp=True)
    assert len(owners) == 2 and owners[0] is not owners[1]
    assert result.iterations[0].rmp_reoptimization.cold_solve_count == 1
    assert solver.snapshots[-1] is None


@pytest.mark.parametrize('where', ('master', 'pricing', 'numerical'))
def test_programming_runtime_error_remains_visible(monkeypatch, where):
    def broken(*a, **kw):
        raise RuntimeError('programming error')
    if where == 'master':
        monkeypatch.setattr(RestrictedMasterProblem, 'solve_reoptimized', broken)
    elif where == 'pricing':
        monkeypatch.setattr(cg, 'price_dag', broken)
    else:
        monkeypatch.setattr(cg, '_master_objectives', broken)
    with pytest.raises(RuntimeError, match='programming error'):
        cg.solve_dag_column_generation(mechanism_a(), reoptimize_rmp=True)
