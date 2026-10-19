from dataclasses import FrozenInstanceError, replace
from math import fsum, inf, nan, nextafter, ulp

import pytest

import silo.decomposition.dag_feasibility as df
from silo.core.enums import ConstraintSense as S
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.decomposition import (
    DagArc,
    DagColumnGenerationProblem,
    DagMasterRow,
    DagPricingProblem,
    DagPricingResult,
    DagPricingStatus,
    solve_dag_column_generation,
)
from silo.decomposition.dag_pricing import price_dag
from silo.decomposition.restricted_master import RestrictedMasterResult
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver


def example(rhs=.5, seed='p0'):
    graph = DagPricingProblem(['s', 't'], [DagArc(f'p{i}', 's', 't', c, {'r': i})
        for i, c in enumerate((-1, 3, 9))], 's', 't', ['conv', 'r'], 1, {'conv': 1})
    return DagColumnGenerationProblem(graph, [DagMasterRow('conv', S.EQ, 1),
        DagMasterRow('r', S.GE, rhs)], 'conv', [(seed,)], 7)


def degenerate():
    graph = DagPricingProblem(['s', 't'], [DagArc('seed', 's', 't', 0),
        DagArc('above', 's', 't', 4, {'R': 1, 'C': 1}),
        DagArc('below', 's', 't', 2, {'R': 1, 'C': -1})],
        's', 't', ['conv', 'R', 'C'], base_coefficients={'conv': 1})
    return DagColumnGenerationProblem(graph, [DagMasterRow('conv', S.EQ, 1),
        DagMasterRow('R', S.EQ, 1), DagMasterRow('C', S.EQ, 0)], 'conv', [('seed',)])


class Spy:
    def __init__(self, backend):
        self.backend, self.models = backend(), []

    def solve(self, model):
        self.models.append(model)
        return self.backend.solve(model)


@pytest.mark.parametrize('backend', [RevisedSimplexSolver, TableauSimplexSolver])
def test_restore_then_explicit_original_optimization_and_cost_identity(backend):
    problem = example()
    solver = Spy(backend)
    result = df.restore_dag_feasibility(problem, solver=solver)
    assert result.status == df.DagFeasibilityStatus.FEASIBLE_SEED_FOUND
    assert [r.penalty_objective for r in result.iterations] == [.5, 0]
    assert result.iterations[0].rho == -2 and result.iterations[0].accepted_path == ('p2',)
    assert result.auxiliary_solve_count == 2 and result.validation_solve_count == 1
    assert len(solver.models) == 3
    assert result.feasible_problem.graph is problem.graph
    assert result.feasible_problem.rows == problem.rows
    assert result.feasible_problem.objective_constant == 7
    assert result.feasible_problem.seed_paths == tuple(result.column_paths.values())
    assert set(result.feasibility_witness.primal_values) == set(result.column_paths)
    final = result.iterations[-1]
    assert final.original_validation is result.feasibility_witness
    assert final.pricing_result is None and final.rho is final.numerical_lower_bound is None
    assert final.objective_gap is final.roundoff_allowance is None
    # Internal native MAX models have negated auxiliary costs, never original costs/c0.
    for model in solver.models:
        assert model.objective.constant == 0
        assert all(value == 0 for name, value in model.objective.coefficients.items()
                   if name.startswith('path_'))
    assert not any(v.name.startswith('art_') for v in solver.models[-1].variables)
    optimized = solve_dag_column_generation(result.feasible_problem, solver=backend())
    assert [r.numerical_upper_bound for r in optimized.iterations] == [9.5, 9]
    assert optimized.last_valid_master.objective_value == 9


@pytest.mark.parametrize('backend', [RevisedSimplexSolver, TableauSimplexSolver])
def test_positive_full_domain_violation_bound_requires_pricing(backend):
    result = df.restore_dag_feasibility(example(3), solver=backend())
    assert result.status == df.DagFeasibilityStatus.POSITIVE_VIOLATION_BOUND
    assert [r.penalty_objective for r in result.iterations] == [3, 1]
    assert result.iterations[-1].rho == 0 and result.iterations[-1].numerical_lower_bound == 1
    assert result.validation_solve_count == 0
    assert result.feasible_problem is result.feasibility_witness is None


@pytest.mark.parametrize('limit,size,status', [(1, 1, 'ITERATION_LIMIT'),
    (2, 2, 'ITERATION_LIMIT'), (3, 3, 'FEASIBLE_SEED_FOUND')])
@pytest.mark.parametrize('backend', [RevisedSimplexSolver, TableauSimplexSolver])
def test_degenerate_one_one_zero_and_separate_validation_budget(limit, size, status, backend):
    solver = Spy(backend)
    result = df.restore_dag_feasibility(degenerate(), solver=solver, iteration_limit=limit)
    assert result.status == getattr(df.DagFeasibilityStatus, status)
    assert [r.penalty_objective for r in result.iterations] == [1, 1, 0][:limit]
    assert len(result.column_paths) == size and result.iterations[-1].accepted_path is None
    assert result.auxiliary_solve_count == limit
    assert result.validation_solve_count == (1 if limit == 3 else 0)
    assert len(solver.models) == result.auxiliary_solve_count + result.validation_solve_count


def test_small_penalty_is_not_an_original_feasibility_witness():
    problem = example(5e-4)
    problem = replace(problem, graph=replace(problem.graph, arcs=problem.graph.arcs[:1]))
    result = df.restore_dag_feasibility(problem, tolerance=1e-3)
    assert result.status == df.DagFeasibilityStatus.NUMERICAL_ISSUE
    assert result.failure_stage == 'original_validation' and result.failure_iteration == 1
    assert result.validation_solve_count == 1
    assert result.iterations[0].original_validation.status == SolverStatus.INFEASIBLE
    assert result.feasible_problem is result.feasibility_witness is None
    assert result.iterations[0].rho is result.iterations[0].objective_gap is None


@pytest.mark.parametrize('sense,rhs,coefficient', [(S.LE, -1, -1), (S.GE, 1, 1),
    (S.EQ, -1, -1), (S.EQ, 1, 1)])
def test_artificial_signs_and_unit_violation(sense, rhs, coefficient):
    graph = DagPricingProblem(['s', 't'], [DagArc('a|b', 's', 't', -90)],
        's', 't', ['conv', 'r|x'], base_coefficients={'conv': 1})
    problem = DagColumnGenerationProblem(graph, [DagMasterRow('conv', S.EQ, 1),
        DagMasterRow('r|x', sense, rhs)], 'conv', [('a|b',)], 2**60)
    result = df.restore_dag_feasibility(problem)
    assert result.status == df.DagFeasibilityStatus.POSITIVE_VIOLATION_BOUND
    assert result.iterations[-1].penalty_objective == 1
    assert ('r|x', coefficient) in result.artificial_columns.values()
    assert set(result.column_paths).isdisjoint(result.artificial_columns)
    assert all(row != 'conv' for row, sign in result.artificial_columns.values())


def test_only_conv_and_already_feasible_seed_validate_without_pricing():
    graph = DagPricingProblem(['s', 't'], [DagArc('a', 's', 't', -1)], 's', 't',
        ['conv'], base_coefficients={'conv': 1})
    problem = DagColumnGenerationProblem(graph, [DagMasterRow('conv', S.EQ, 1)],
                                        'conv', [('a',)], -2**60)
    result = df.restore_dag_feasibility(problem, iteration_limit=1)
    assert result.status == df.DagFeasibilityStatus.FEASIBLE_SEED_FOUND
    assert result.artificial_columns == {} and result.iterations[0].pricing_result is None
    assert result.auxiliary_solve_count == result.validation_solve_count == 1


@pytest.mark.parametrize('kwargs', [{'iteration_limit': True}, {'iteration_limit': 0},
    {'iteration_limit': 1.5}, {'tolerance': 0}, {'tolerance': -1},
    {'tolerance': inf}, {'tolerance': nan}])
def test_bad_parameters(kwargs):
    with pytest.raises((TypeError, ValueError)):
        df.restore_dag_feasibility(example(), **kwargs)


def test_bad_problem_type():
    with pytest.raises(TypeError):
        df.restore_dag_feasibility(None)


def _inject_master(monkeypatch, *, weight=1, pi_r=1, tolerance=1e-9):
    # Synthetic complete auxiliary evidence for seed r=2, target r>=3.
    pi_conv = -2*pi_r
    snapshot = RestrictedMasterResult(SolverStatus.OPTIMAL, weight,
        {'path_0': 1, 'art_0': weight}, {'conv': pi_conv, 'r': pi_r},
        {'path_0': 0, 'art_0': 1-pi_r})
    monkeypatch.setattr(df.RestrictedMasterProblem, 'solve', lambda *a, **kw: snapshot)
    return df.restore_dag_feasibility(example(3, 'p2'), tolerance=tolerance)


def test_artificial_dual_constraint_blocks_false_positive_lower_bound(monkeypatch):
    # All actual rows/weights and claimed F=2,D=2,rho=0 fit. Artificial rc=-1 is decisive.
    snapshot = RestrictedMasterResult(SolverStatus.OPTIMAL, 2,
        {'path_0': 1, 'art_0': 2}, {'conv': -4, 'r': 2},
        {'path_0': 2, 'art_0': 0})  # Deliberately forged artificial rc.
    monkeypatch.setattr(df.RestrictedMasterProblem, 'solve', lambda *a, **kw: snapshot)
    result = df.restore_dag_feasibility(example(3, 'p1'))
    assert result.status == df.DagFeasibilityStatus.NUMERICAL_ISSUE
    assert 'artificial' in result.message.lower()
    assert result.feasible_problem is result.feasibility_witness is None
    assert result.iterations[0].numerical_lower_bound is result.iterations[0].objective_gap is None


@pytest.mark.parametrize('case', ['inside', 'equal', 'outside', 'over_budget', 'nonnegative'])
def test_auxiliary_gap_uses_existing_local_roundoff_rule(monkeypatch, case):
    weight = 1-2**-45
    if case == 'inside':
        weight = nextafter(weight, 1)
    if case == 'outside':
        weight = nextafter(weight, 0)
    if case == 'nonnegative':
        weight = 1
    gap = fsum([weight, 2, -3])
    eta = 32*ulp(fsum([abs(weight), 2, 3]))
    tolerance = nextafter(eta, 0) if case in ('over_budget', 'nonnegative') else 1e-9
    result = _inject_master(monkeypatch, weight=weight, tolerance=tolerance)
    if case in ('outside', 'over_budget'):
        assert result.status == df.DagFeasibilityStatus.NUMERICAL_ISSUE
        assert result.iterations[-1].objective_gap is None
    else:
        assert result.status == df.DagFeasibilityStatus.POSITIVE_VIOLATION_BOUND
        assert result.iterations[-1].objective_gap == gap
        assert result.iterations[-1].roundoff_allowance == eta


@pytest.mark.parametrize('budget', ['inside', 'equal', 'outside'])
def test_positive_gap_threshold_has_no_extra_allowance(monkeypatch, budget):
    gap = 2**-30
    tolerance = (nextafter(gap, inf) if budget == 'inside' else
                 gap if budget == 'equal' else nextafter(gap, 0))
    result = _inject_master(monkeypatch, pi_r=1-gap, tolerance=tolerance)
    assert result.status == (df.DagFeasibilityStatus.NUMERICAL_ISSUE if budget == 'outside'
                             else df.DagFeasibilityStatus.POSITIVE_VIOLATION_BOUND)


def test_positive_restricted_penalty_without_separated_lower_bound_is_uncertain(monkeypatch):
    tau = 2**-30
    problem = example(1.5*tau)
    problem = replace(problem, graph=replace(problem.graph, arcs=problem.graph.arcs[:1]))
    snapshot = RestrictedMasterResult(SolverStatus.OPTIMAL, 1.5*tau,
        {'path_0': 1, 'art_0': 1.5*tau}, {'conv': 0, 'r': 1/3},
        {'path_0': 0, 'art_0': 1-1/3})
    monkeypatch.setattr(df.RestrictedMasterProblem, 'solve', lambda *a, **kw: snapshot)
    result = df.restore_dag_feasibility(problem, tolerance=tau)
    assert result.status == df.DagFeasibilityStatus.NUMERICAL_ISSUE
    assert 'lower' in result.message.lower()
    assert result.feasible_problem is None


@pytest.mark.parametrize('status', [SolverStatus.INFEASIBLE, SolverStatus.UNBOUNDED,
    SolverStatus.NOT_SOLVED, SolverStatus.NUMERICAL_ISSUE, SolverStatus.ITERATION_LIMIT])
def test_master_failures_remain_auxiliary_diagnostics(status):
    class Failed:
        def solve(self, model):
            return Solution(status, message='injected failure')
    result = df.restore_dag_feasibility(example(), solver=Failed())
    assert result.status == df.DagFeasibilityStatus.MASTER_FAILURE
    assert result.failure_stage == 'auxiliary_master' and result.failure_iteration == 1
    assert result.auxiliary_solve_count == 1 and result.validation_solve_count == 0
    assert result.iterations[0].master_result.status == status
    assert result.feasible_problem is result.feasibility_witness is None


def test_bad_optimal_evidence_is_rejected_by_existing_rmp():
    class Bad:
        def solve(self, model):
            return Solution(SolverStatus.OPTIMAL, objective_value=0)
    result = df.restore_dag_feasibility(example(), solver=Bad())
    assert result.status == df.DagFeasibilityStatus.MASTER_FAILURE
    assert result.iterations[0].master_result.status == SolverStatus.NUMERICAL_ISSUE


@pytest.mark.parametrize('status', [DagPricingStatus.NO_PATH, DagPricingStatus.NUMERICAL_ISSUE])
def test_pricing_failure_cannot_produce_a_witness_or_positive_bound(monkeypatch, status):
    monkeypatch.setattr(df, 'price_dag', lambda *a, **kw: DagPricingResult(status))
    result = df.restore_dag_feasibility(example())
    assert result.status == df.DagFeasibilityStatus.PRICING_FAILURE
    assert result.failure_stage == 'pricing'
    assert result.iterations[0].penalty_objective == .5
    assert result.iterations[0].rho is result.iterations[0].objective_gap is None
    assert result.last_valid_master_iteration == 1
    assert result.feasible_problem is result.feasibility_witness is None


@pytest.mark.parametrize('changes', [dict(cost=4), dict(arc_ids=('unknown',)),
    dict(row_coefficients={'conv': 1, 'r': 7}), dict(reduced_cost=1), dict(is_improving=False),
    dict(cost=nan)])
def test_bad_pricing_fields_or_original_cost_leak_are_rejected(monkeypatch, changes):
    real = price_dag
    monkeypatch.setattr(df, 'price_dag', lambda *a, **kw: replace(real(*a, **kw), **changes))
    result = df.restore_dag_feasibility(example())
    assert result.status == df.DagFeasibilityStatus.NUMERICAL_ISSUE
    assert result.iterations[0].numerical_lower_bound is None


def test_later_auxiliary_failure_retains_historical_column_scope(monkeypatch):
    real = df.RestrictedMasterProblem.solve
    calls = []
    def solve(master, solver=None):
        calls.append(1)
        return (real(master, solver) if len(calls) == 1 else
                RestrictedMasterResult(SolverStatus.NUMERICAL_ISSUE, message='later failure'))
    monkeypatch.setattr(df.RestrictedMasterProblem, 'solve', solve)
    result = df.restore_dag_feasibility(example())
    assert result.status == df.DagFeasibilityStatus.MASTER_FAILURE
    assert result.failure_iteration == 2 and result.last_valid_master_iteration == 1
    assert len(result.column_paths) == 1 and len(result.iterations[1].column_paths) == 2
    assert result.iterations[1].numerical_lower_bound is None


def test_input_and_snapshot_ownership_and_repeated_calls():
    problem = example()
    rows, seeds = list(problem.rows), [['p0']]
    problem = replace(problem, rows=rows, seed_paths=seeds)
    rows.clear()
    seeds[0].append('bad')
    first = df.restore_dag_feasibility(problem)
    second = df.restore_dag_feasibility(example(3))
    assert first.iterations[0].column_paths == {'path_0': ('p0',)}
    assert first.feasible_problem.graph.base_cost == 1
    assert second.feasible_problem is None
    with pytest.raises(TypeError):
        first.column_paths['x'] = ('p1',)
    with pytest.raises(TypeError):
        first.artificial_columns['x'] = ('r', 1)
    with pytest.raises(FrozenInstanceError):
        first.iterations[0].penalty_objective = 9


def test_programming_errors_are_visible(monkeypatch):
    def broken(*a, **kw):
        raise RuntimeError('injected programming error')
    monkeypatch.setattr(df, 'price_dag', broken)
    with pytest.raises(RuntimeError, match='programming'):
        df.restore_dag_feasibility(example())


@pytest.mark.parametrize('case', ['inside', 'equal', 'outside'])
def test_small_negative_rho_threshold_and_existing_path_guard(monkeypatch, case):
    tolerance = 2**-35
    pi_conv = -2+tolerance
    if case == 'inside':
        pi_conv = nextafter(pi_conv, -inf)
    if case == 'outside':
        pi_conv = nextafter(pi_conv, inf)
    rho = -fsum([pi_conv, 2])
    snapshot = RestrictedMasterResult(SolverStatus.OPTIMAL, 1,
        {'path_0': 1, 'art_0': 1}, {'conv': pi_conv, 'r': 1},
        {'path_0': rho, 'art_0': 0})
    monkeypatch.setattr(df.RestrictedMasterProblem, 'solve', lambda *a, **kw: snapshot)
    result = df.restore_dag_feasibility(example(3, 'p2'), tolerance=tolerance)
    if case == 'outside':
        assert result.status == df.DagFeasibilityStatus.NUMERICAL_ISSUE
        assert 'existing' in result.message.lower()
    else:
        assert result.status == df.DagFeasibilityStatus.POSITIVE_VIOLATION_BOUND
        assert result.iterations[-1].rho == rho >= -tolerance


@pytest.mark.parametrize('field,value', [('objective_value', inf),
    ('primal_values', {'path_0': 1, 'art_0': inf}),
    ('dual_values', {'conv': 0, 'r': inf}),
    ('reduced_costs', {'path_0': 0, 'art_0': nan})])
def test_nonfinite_master_evidence_is_rejected(monkeypatch, field, value):
    snapshot = RestrictedMasterResult(SolverStatus.OPTIMAL, .5,
        {'path_0': 1, 'art_0': .5}, {'conv': 0, 'r': 1}, {'path_0': 0, 'art_0': 0})
    monkeypatch.setattr(df.RestrictedMasterProblem, 'solve', lambda *a, **kw:
                        replace(snapshot, **{field: value}))
    result = df.restore_dag_feasibility(example())
    assert result.status == df.DagFeasibilityStatus.NUMERICAL_ISSUE
    assert result.iterations[-1].numerical_lower_bound is None


def test_finite_absolute_scale_overflow_cannot_publish_a_positive_bound(monkeypatch):
    problem = example(1e308)
    problem = replace(problem, graph=replace(problem.graph, arcs=problem.graph.arcs[:1]))
    snapshot = RestrictedMasterResult(SolverStatus.OPTIMAL, 1e308,
        {'path_0': 1, 'art_0': 1e308}, {'conv': 0, 'r': 1}, {'path_0': 0, 'art_0': 0})
    monkeypatch.setattr(df.RestrictedMasterProblem, 'solve', lambda *a, **kw: snapshot)
    result = df.restore_dag_feasibility(problem)
    assert result.status == df.DagFeasibilityStatus.NUMERICAL_ISSUE
    assert result.failure_stage == 'bound_check'
    assert result.iterations[0].objective_gap is result.iterations[0].roundoff_allowance is None


def test_finite_path_coefficient_sum_overflow_precedes_any_lp_call():
    graph = DagPricingProblem(['s', 'v', 't'], [DagArc('a', 's', 'v', 0, {'r': 1e308}),
        DagArc('b', 'v', 't', 0, {'r': 1e308})], 's', 't', ['conv', 'r'],
        base_coefficients={'conv': 1})
    problem = replace(example(), graph=graph, seed_paths=[('a', 'b')])
    result = df.restore_dag_feasibility(problem)
    assert result.status == df.DagFeasibilityStatus.NUMERICAL_ISSUE
    assert result.failure_stage == 'initialization'
    assert result.auxiliary_solve_count == result.validation_solve_count == 0
    assert result.iterations == () and result.column_paths == {}


def test_bad_original_optimal_snapshot_requires_independent_row_recheck(monkeypatch):
    real = df.RestrictedMasterProblem.solve
    calls = []
    def solve(master, solver=None):
        calls.append(1)
        if len(calls) == 1:
            return real(master, solver)
        return RestrictedMasterResult(SolverStatus.OPTIMAL, 0, {'path_0': 1},
                                      {'conv': 0, 'r': 0}, {'path_0': 0})
    monkeypatch.setattr(df.RestrictedMasterProblem, 'solve', solve)
    problem = example(5e-4)
    problem = replace(problem, graph=replace(problem.graph, arcs=problem.graph.arcs[:1]))
    result = df.restore_dag_feasibility(problem, tolerance=1e-3)
    assert result.status == df.DagFeasibilityStatus.NUMERICAL_ISSUE
    assert result.failure_stage == 'original_validation'
    assert result.feasible_problem is result.feasibility_witness is None


def test_wrong_artificial_cost_evidence_cannot_pass(monkeypatch):
    real = df.RestrictedMasterProblem
    def corrupt(model):
        for name in model.objective.coefficients:
            if name.startswith('art_'):
                model.objective.coefficients[name] = 2
        return real(model)
    monkeypatch.setattr(df, 'RestrictedMasterProblem', corrupt)
    result = df.restore_dag_feasibility(example())
    assert result.status == df.DagFeasibilityStatus.NUMERICAL_ISSUE
    assert result.iterations[0].numerical_lower_bound is None


def test_same_vector_paths_and_reserved_looking_ids_keep_separate_identity():
    graph = DagPricingProblem(['s', 't'], [DagArc('path_0', 's', 't', -3, {'r': 1}),
        DagArc('art_0|x', 's', 't', 8, {'r': 1})], 's', 't', ['conv', 'r'],
        base_coefficients={'conv': 1})
    problem = replace(example(), graph=graph, seed_paths=[('path_0',), ('art_0|x',)])
    result = df.restore_dag_feasibility(problem)
    assert result.status == df.DagFeasibilityStatus.FEASIBLE_SEED_FOUND
    assert result.feasible_problem.seed_paths == problem.seed_paths
    assert len(result.column_paths) == 2
    assert set(result.column_paths).isdisjoint(result.artificial_columns)


def test_recovery_imports_no_private_cg_helpers_or_original_optimizer():
    import ast
    from pathlib import Path
    tree = ast.parse(Path(df.__file__).read_text(encoding='utf-8'))
    imports = [node for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    assert not any('interfaces' in node.module or 'oracle' in node.module for node in imports)
    assert not any(alias.name.startswith('_') for node in imports for alias in node.names)
    assert not any(alias.name == 'solve_dag_column_generation' for node in imports
                   for alias in node.names)


def test_small_negative_penalty_is_retained_but_original_rows_still_validate(monkeypatch):
    real = df.RestrictedMasterProblem.solve
    calls = []
    def solve(master, solver=None):
        calls.append(1)
        if len(calls) == 1:
            return RestrictedMasterResult(SolverStatus.OPTIMAL, -5e-10,
                {'path_0': 1, 'art_0': -5e-10}, {'conv': 0, 'r': 0},
                {'path_0': 0, 'art_0': 1})
        return real(master, solver)
    monkeypatch.setattr(df.RestrictedMasterProblem, 'solve', solve)
    result = df.restore_dag_feasibility(example(0))
    assert result.status == df.DagFeasibilityStatus.FEASIBLE_SEED_FOUND
    assert result.iterations[0].penalty_objective == -5e-10
    assert result.iterations[0].master_result.primal_values['art_0'] == -5e-10
    assert result.feasibility_witness.objective_value == 0 and result.validation_solve_count == 1


def test_total_negative_penalty_guard_is_distinct_from_individual_weight_tolerance(monkeypatch):
    graph = DagPricingProblem(['s', 't'], [DagArc('seed', 's', 't', 0)],
        's', 't', ['conv', 'R', 'C'], base_coefficients={'conv': 1})
    problem = DagColumnGenerationProblem(graph, [DagMasterRow('conv', S.EQ, 1),
        DagMasterRow('R', S.GE, 0), DagMasterRow('C', S.GE, 0)], 'conv', [('seed',)])
    snapshot = RestrictedMasterResult(SolverStatus.OPTIMAL, -1.5e-9,
        {'path_0': 1, 'art_0': -.75e-9, 'art_1': -.75e-9},
        {'conv': 0, 'R': 0, 'C': 0}, {'path_0': 0, 'art_0': 1, 'art_1': 1})
    monkeypatch.setattr(df.RestrictedMasterProblem, 'solve', lambda *a, **kw: snapshot)
    result = df.restore_dag_feasibility(problem)
    assert result.status == df.DagFeasibilityStatus.NUMERICAL_ISSUE
    assert 'objective' in result.message.lower()
    assert result.validation_solve_count == 0 and result.feasibility_witness is None


def test_tolerance_close_candidate_fields_do_not_pollute_inserted_real_columns(monkeypatch):
    real = price_dag
    def drift(*a, **kw):
        candidate = real(*a, **kw)
        return replace(candidate, cost=5e-10,
            row_coefficients={j: v+5e-10 for j, v in candidate.row_coefficients.items()})
    monkeypatch.setattr(df, 'price_dag', drift)
    solver = Spy(RevisedSimplexSolver)
    result = df.restore_dag_feasibility(example(), solver=solver)
    assert result.status == df.DagFeasibilityStatus.FEASIBLE_SEED_FOUND
    for model in solver.models:
        assert all(value == 0 for name, value in model.objective.coefficients.items()
                   if name.startswith('path_'))
    optimized = solve_dag_column_generation(result.feasible_problem)
    assert optimized.last_valid_master.objective_value == 9
