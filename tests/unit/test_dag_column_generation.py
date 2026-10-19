from dataclasses import FrozenInstanceError, replace
from math import fsum, inf, nan, nextafter, ulp

import pytest

import silo.decomposition.dag_column_generation as cg
from silo.core.enums import ConstraintSense as S
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.decomposition import DagArc, DagPricingProblem, DagPricingResult, DagPricingStatus
from silo.decomposition.dag_pricing import price_dag
from silo.decomposition.restricted_master import RestrictedMasterResult


def coupled():
    graph = DagPricingProblem(
        ['s', 't'], [DagArc('d1', 's', 't', 4, {'R': 1, 'C': 1}),
                     DagArc('d2', 's', 't', 6), DagArc('o12', 's', 't', 1, {'R': 1}),
                     DagArc('o21', 's', 't', 2, {'C': 1})],
        's', 't', ['conv', 'R', 'C'], base_coefficients={'conv': 1})
    return cg.DagColumnGenerationProblem(graph, [cg.DagMasterRow('conv', S.EQ, 1),
        cg.DagMasterRow('R', S.EQ, .5), cg.DagMasterRow('C', S.EQ, .5)],
        'conv', [('d1',), ('d2',)], objective_constant=-3)


def single(cost=0.0):
    graph = DagPricingProblem(['s', 't'], [DagArc('seed', 's', 't', 0),
        DagArc('other', 's', 't', cost)], 's', 't', ['conv'],
        base_coefficients={'conv': 1})
    return cg.DagColumnGenerationProblem(graph, [cg.DagMasterRow('conv', S.EQ, 1)],
                                        'conv', [('seed',)])


@pytest.mark.parametrize('limit,count,reason', [(1, 2, 'ITERATION_LIMIT'),
    (2, 3, 'ITERATION_LIMIT'), (3, 4, 'TOLERANCE_REACHED')])
def test_limit_counts_solved_rounds_and_never_returns_an_unsolved_column(limit, count, reason):
    result = cg.solve_dag_column_generation(coupled(), iteration_limit=limit)
    assert result.status == getattr(cg.DagColumnGenerationStatus, reason)
    assert len(result.iterations) == limit and len(result.column_paths) == count
    assert result.column_set_iteration == result.last_valid_master_iteration == limit
    assert set(result.column_paths) == set(result.last_valid_master.primal_values)
    assert result.iterations[-1].accepted_path is None
    assert [r.numerical_upper_bound for r in result.iterations] == [2, 2, -1.5][:limit]


@pytest.mark.parametrize('cost,improving', [(-1e-9, False), (-.9e-9, False), (-1.1e-9, True)])
def test_strict_threshold_and_true_gap(cost, improving):
    result = cg.solve_dag_column_generation(single(cost), iteration_limit=1)
    record = result.iterations[0]
    assert record.rho == cost and record.numerical_gap == -cost
    assert record.pricing_result.is_improving is improving
    assert result.status == (cg.DagColumnGenerationStatus.ITERATION_LIMIT if improving
                             else cg.DagColumnGenerationStatus.TOLERANCE_REACHED)


def test_small_negative_price_is_preserved_with_positive_gap():
    problem = single(-5e-10)
    result = cg.solve_dag_column_generation(problem)
    record = result.iterations[0]
    assert result.status == cg.DagColumnGenerationStatus.TOLERANCE_REACHED
    assert record.rho == -5e-10 and record.numerical_lower_bound == -5e-10
    assert record.numerical_upper_bound == 0 and record.numerical_gap == 5e-10
    assert len(result.column_paths) == 1


@pytest.mark.parametrize('value', [True, False, 1.5, '2', 0, -1])
def test_invalid_iteration_limit(value):
    with pytest.raises((ValueError, TypeError)):
        cg.solve_dag_column_generation(single(), iteration_limit=value)


@pytest.mark.parametrize('value', [0, -1, inf, nan, 'bad'])
def test_invalid_tolerance(value):
    with pytest.raises((ValueError, TypeError)):
        cg.solve_dag_column_generation(single(), tolerance=value)


@pytest.mark.parametrize('seeds', [[], [()], [('unknown',)], [('seed',), ('seed',)],
    [('seed', 'other')], ['seed']])
def test_invalid_seed_paths(seeds):
    with pytest.raises((ValueError, TypeError)):
        replace(single(), seed_paths=seeds)


@pytest.mark.parametrize('rows,conv', [([], 'conv'),
    ([('conv', S.LE, 1)], 'conv'), ([('conv', S.EQ, 1 + 1e-12)], 'conv'),
    ([('conv', S.EQ, 1), ('conv', S.EQ, 1)], 'conv'),
    ([('wrong', S.EQ, 1)], 'wrong'), ([('conv', S.EQ, 1)], 'missing')])
def test_invalid_master_rows(rows, conv):
    with pytest.raises((ValueError, TypeError)):
        replace(single(), rows=[cg.DagMasterRow(*r) for r in rows], convexity_row=conv)


@pytest.mark.parametrize('base,arc', [(1 + 1e-12, 0), (1, 1e-12), (0, 0)])
def test_convexity_structure_is_exact(base, arc):
    graph = DagPricingProblem(['s', 't'], [DagArc('seed', 's', 't', 0, {'conv': arc})],
        's', 't', ['conv'], base_coefficients={'conv': base})
    with pytest.raises(ValueError):
        replace(single(), graph=graph)


@pytest.mark.parametrize('name,sense,rhs', [('', S.EQ, 1), ('r', 'bad', 1),
    ('r', S.EQ, inf), ('r', S.EQ, nan)])
def test_bad_row_fields(name, sense, rhs):
    with pytest.raises((ValueError, TypeError)):
        cg.DagMasterRow(name, sense, rhs)


def test_snapshots_input_ownership_and_repeated_runs():
    problem = single(-1)
    rows, seeds = list(problem.rows), [['seed']]
    owned = replace(problem, rows=rows, seed_paths=seeds)
    rows.clear()
    seeds[0].append('other')
    first = cg.solve_dag_column_generation(owned)
    second = cg.solve_dag_column_generation(owned)
    assert first == second
    assert first.iterations[0].column_paths == {'path_0': ('seed',)}
    assert first.iterations[0].accepted_path == ('other',)
    assert len(first.column_paths) == 2
    with pytest.raises(TypeError):
        first.column_paths['x'] = ('seed',)
    with pytest.raises(TypeError):
        first.iterations[0].column_paths['x'] = ('other',)
    with pytest.raises(FrozenInstanceError):
        first.message = 'changed'
    with pytest.raises(TypeError):
        first.last_valid_master.primal_values['path_0'] = 9


@pytest.mark.parametrize('status', [SolverStatus.INFEASIBLE, SolverStatus.UNBOUNDED,
    SolverStatus.ITERATION_LIMIT, SolverStatus.NOT_SOLVED, SolverStatus.NUMERICAL_ISSUE])
def test_backend_failure_is_scoped_to_rmp(status):
    class Failed:
        def solve(self, model):
            return Solution(status, message='synthetic backend failure')
    result = cg.solve_dag_column_generation(single(), solver=Failed())
    assert result.status == cg.DagColumnGenerationStatus.MASTER_FAILURE
    assert result.last_valid_master is None and result.failure_iteration == 1
    assert result.iterations[0].master_result.status == status
    assert result.iterations[0].pricing_result is None
    assert result.iterations[0].numerical_gap is None
    assert result.iterations[0].objective_gap is result.iterations[0].roundoff_allowance is None


def test_fake_backend_optimal_evidence_is_rejected_by_real_rmp():
    class Broken:
        def solve(self, model):
            return Solution(SolverStatus.OPTIMAL, objective_value=0)
    result = cg.solve_dag_column_generation(single(), solver=Broken())
    assert result.status == cg.DagColumnGenerationStatus.MASTER_FAILURE
    assert result.iterations[0].master_result.status == SolverStatus.NUMERICAL_ISSUE


@pytest.mark.parametrize('status', [DagPricingStatus.NO_PATH, DagPricingStatus.NUMERICAL_ISSUE])
def test_pricing_failure_never_becomes_convergence(monkeypatch, status):
    monkeypatch.setattr(cg, 'price_dag', lambda *a, **kw: DagPricingResult(status))
    result = cg.solve_dag_column_generation(single())
    assert result.status == cg.DagColumnGenerationStatus.PRICING_FAILURE
    assert result.failure_iteration == result.last_valid_master_iteration == 1
    assert result.iterations[0].rho is result.iterations[0].numerical_upper_bound is None
    assert result.iterations[0].objective_gap is result.iterations[0].roundoff_allowance is None


@pytest.mark.parametrize('change', [dict(arc_ids=('bad',)), dict(cost=2),
    dict(row_coefficients={}), dict(row_coefficients={'conv': 2}),
    dict(reduced_cost=-2), dict(cost=nan), dict(is_improving=False), dict(is_improving=None),
    dict(reduced_cost=None), dict(row_coefficients={'conv': 1, 'extra': 0})])
def test_bad_candidate_fields_are_numerical_failure(monkeypatch, change):
    real = price_dag
    monkeypatch.setattr(cg, 'price_dag', lambda *a, **kw: replace(real(*a, **kw), **change))
    result = cg.solve_dag_column_generation(single(-1))
    assert result.status == cg.DagColumnGenerationStatus.NUMERICAL_ISSUE
    assert result.iterations[-1].numerical_gap is None and len(result.column_paths) == 1


def test_within_tolerance_candidate_drift_is_not_written_to_master(monkeypatch):
    real = price_dag
    def drift(*a, **kw):
        candidate = real(*a, **kw)
        return replace(candidate, cost=candidate.cost + 5e-10,
                       row_coefficients={'conv': 1 + 5e-10})
    monkeypatch.setattr(cg, 'price_dag', drift)
    result = cg.solve_dag_column_generation(single(-1))
    assert result.status == cg.DagColumnGenerationStatus.TOLERANCE_REACHED
    assert result.last_valid_master.objective_value == -1
    assert sum(result.last_valid_master.primal_values.values()) == 1


def test_significant_existing_negative_column_is_not_convergence(monkeypatch):
    problem = single(1)
    wrong = RestrictedMasterResult(SolverStatus.OPTIMAL, 0, {'path_0': 1}, {'conv': 1},
                                   {'path_0': -1})
    monkeypatch.setattr(cg.RestrictedMasterProblem, 'solve', lambda *a, **kw: wrong)
    result = cg.solve_dag_column_generation(problem)
    assert result.status == cg.DagColumnGenerationStatus.NUMERICAL_ISSUE
    assert 'existing' in result.message.lower()


@pytest.mark.parametrize('dual,price,reason', [(0, -7e-10, 'gap'), (1e-10, 0, 'bound')])
def test_gap_gate_and_negative_gap_are_not_clipped(monkeypatch, dual, price, reason):
    # Synthetic RMP evidence: isolates gap gating and bound-order protection.
    problem = single(price)
    result_snapshot = RestrictedMasterResult(SolverStatus.OPTIMAL, 0,
        {'path_0': 1}, {'conv': dual}, {'path_0': -dual})
    if reason == 'gap':
        problem = replace(problem, objective_constant=1)
        result_snapshot = replace(result_snapshot, objective_value=1,
                                  dual_values={'conv': -8e-10})
        problem = replace(problem, graph=replace(problem.graph,
            arcs=[DagArc('seed', 's', 't', 0), DagArc('other', 's', 't', -1.5e-9)]))
    else:
        problem = replace(problem, graph=replace(problem.graph,
            arcs=[DagArc('seed', 's', 't', 1), DagArc('other', 's', 't', 1)]))
        result_snapshot = replace(result_snapshot, objective_value=1 - 5e-10,
            primal_values={'path_0': 1 - 5e-10}, dual_values={'conv': 1})
    monkeypatch.setattr(cg.RestrictedMasterProblem, 'solve', lambda *a, **kw: result_snapshot)
    result = cg.solve_dag_column_generation(problem)
    assert result.status == cg.DagColumnGenerationStatus.NUMERICAL_ISSUE
    assert reason in result.message.lower()
    assert result.iterations[-1].numerical_gap is None


@pytest.mark.parametrize('field,value', [('objective_value', inf),
    ('dual_values', {'conv': inf}), ('primal_values', {'path_0': inf})])
def test_nonfinite_master_arithmetic_is_diagnosed(monkeypatch, field, value):
    snapshot = RestrictedMasterResult(SolverStatus.OPTIMAL, 0,
        {'path_0': 1}, {'conv': 0}, {'path_0': 0})
    monkeypatch.setattr(cg.RestrictedMasterProblem, 'solve', lambda *a, **kw:
                        replace(snapshot, **{field: value}))
    result = cg.solve_dag_column_generation(single())
    assert result.status == cg.DagColumnGenerationStatus.NUMERICAL_ISSUE
    assert result.iterations[-1].rho is None


def test_later_master_failure_does_not_relabel_old_evidence(monkeypatch):
    real = cg.RestrictedMasterProblem.solve
    calls = []
    def solve(master, solver=None):
        calls.append(1)
        return (real(master, solver) if len(calls) == 1 else
                RestrictedMasterResult(SolverStatus.NUMERICAL_ISSUE, message='second failure'))
    monkeypatch.setattr(cg.RestrictedMasterProblem, 'solve', solve)
    result = cg.solve_dag_column_generation(coupled())
    assert result.failure_iteration == 2 and result.last_valid_master_iteration == 1
    assert result.column_set_iteration == 1 and len(result.column_paths) == 2
    assert len(result.iterations[1].column_paths) == 3
    assert result.iterations[1].numerical_lower_bound is None
    assert result.iterations[1].objective_gap is result.iterations[1].roundoff_allowance is None
    assert set(result.column_paths) == set(result.last_valid_master.primal_values)


def test_programming_errors_are_not_swallowed(monkeypatch):
    def broken(*a, **kw):
        raise RuntimeError('synthetic programming error')
    monkeypatch.setattr(cg, 'price_dag', broken)
    with pytest.raises(RuntimeError, match='programming'):
        cg.solve_dag_column_generation(single())


@pytest.mark.parametrize('value', [inf, nan, 'bad'])
def test_nonfinite_objective_constant_is_input_error(value):
    with pytest.raises(ValueError):
        replace(single(), objective_constant=value)


def test_disconnected_multiarc_seed_is_rejected():
    graph = DagPricingProblem(['s', 'v', 't'], [DagArc('a', 's', 'v', 0),
        DagArc('b', 'v', 't', 0)], 's', 't', ['conv'], base_coefficients={'conv': 1})
    with pytest.raises(ValueError):
        replace(single(), graph=graph, seed_paths=[('a',)])
    with pytest.raises(ValueError):
        replace(single(), graph=graph, seed_paths=[('b', 'a')])


def test_seed_reconstruction_overflow_has_no_solved_registry():
    graph = DagPricingProblem(['s', 'v', 't'], [DagArc('a', 's', 'v', 1e308),
        DagArc('b', 'v', 't', 1e308)], 's', 't', ['conv'], base_coefficients={'conv': 1})
    result = cg.solve_dag_column_generation(replace(single(), graph=graph, seed_paths=[('a', 'b')]))
    assert result.status == cg.DagColumnGenerationStatus.NUMERICAL_ISSUE
    assert result.iterations == () and result.column_paths == {}
    assert result.failure_iteration == 1 and result.column_set_iteration is None


@pytest.mark.parametrize('field', ['P', 'D', 'L'])
def test_finite_data_overflow_in_bound_arithmetic(monkeypatch, field):
    problem = single(-1e308)
    snapshot = RestrictedMasterResult(SolverStatus.OPTIMAL, -1e308,
        {'path_0': 1}, {'conv': 0}, {'path_0': 0})
    problem = replace(problem, objective_constant=-1e308)
    if field == 'P':
        problem = replace(problem, objective_constant=1e308, graph=replace(problem.graph,
            arcs=[DagArc('seed', 's', 't', 1e308), DagArc('other', 's', 't', 1e308)]))
    if field == 'D':
        graph = replace(problem.graph, row_names=['conv', 'r'],
                        base_coefficients={'conv': 1, 'r': 1e308})
        problem = replace(problem, graph=graph,
                          rows=[*problem.rows, cg.DagMasterRow('r', S.EQ, 1e308)])
        snapshot = replace(snapshot, dual_values={'conv': 0, 'r': 1e308})
    monkeypatch.setattr(cg.RestrictedMasterProblem, 'solve', lambda *a, **kw: snapshot)
    result = cg.solve_dag_column_generation(problem)
    assert result.status == cg.DagColumnGenerationStatus.NUMERICAL_ISSUE
    assert result.iterations[-1].numerical_gap is None


def test_controller_import_boundary_and_no_private_rmp_access():
    import ast
    from pathlib import Path
    tree = ast.parse(Path(cg.__file__).read_text(encoding='utf-8'))
    imports = {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert not any('interfaces' in module or 'oracle' in module for module in imports)
    assert not any(isinstance(node, ast.Attribute) and node.attr == '_model'
                   for node in ast.walk(tree))


def _synthetic_convexity_snapshot(monkeypatch, *, cost=1, other=1, weight=1, pi=1,
                                  c0=0, tolerance=1e-9):
    # Explicit dependency fault injection, not a claim of natural LP reachability.
    graph = replace(single().graph, arcs=[DagArc('seed', 's', 't', cost),
                                         DagArc('other', 's', 't', other)])
    problem = replace(single(), graph=graph, objective_constant=c0)
    snapshot = RestrictedMasterResult(SolverStatus.OPTIMAL, fsum([c0, cost*weight]),
        {'path_0': weight}, {'conv': pi}, {'path_0': cost-pi})
    monkeypatch.setattr(cg.RestrictedMasterProblem, 'solve', lambda *a, **kw: snapshot)
    return cg.solve_dag_column_generation(problem, tolerance=tolerance)


@pytest.mark.parametrize('case', ['inside', 'equal', 'outside', 'equal_budget', 'over_budget'])
def test_negative_objective_gap_local_exception_boundaries(monkeypatch, case):
    weight = 1 - 2**-47
    if case == 'inside':
        weight = nextafter(weight, 1)
    if case == 'outside':
        weight = nextafter(weight, 0)
    gap = fsum([weight, -1])
    scale = fsum([abs(weight), 1])
    eta = 32*ulp(scale)
    tolerance = eta if case == 'equal_budget' else (
        nextafter(eta, 0) if case == 'over_budget' else 1e-9)
    if case in ('equal', 'equal_budget', 'over_budget'):
        assert -gap == eta
    elif case == 'inside':
        assert -gap < eta
    else:
        assert -gap > eta
    expected = case not in ('outside', 'over_budget')
    assert (eta <= tolerance and -gap <= eta) is expected
    result = _synthetic_convexity_snapshot(monkeypatch, weight=weight, tolerance=tolerance)
    record = result.iterations[-1]
    if expected:
        assert result.status == cg.DagColumnGenerationStatus.TOLERANCE_REACHED
        assert record.objective_gap == gap < 0 and record.roundoff_allowance == eta
        assert record.numerical_gap == gap
        assert record.master_result.primal_values['path_0'] == weight
        assert 'roundoff' in result.message.lower()
    else:
        assert result.status == cg.DagColumnGenerationStatus.NUMERICAL_ISSUE
        assert record.numerical_gap is record.objective_gap is record.roundoff_allowance is None


def test_eta_larger_than_user_tolerance_allows_nonnegative_gap(monkeypatch):
    result = _synthetic_convexity_snapshot(monkeypatch, tolerance=1e-15)
    record = result.iterations[-1]
    assert result.status == cg.DagColumnGenerationStatus.TOLERANCE_REACHED
    assert record.roundoff_allowance > 1e-15 and record.objective_gap == 0


@pytest.mark.parametrize('gap', [nextafter(1e-9, 0), 1e-9, nextafter(1e-9, inf)])
def test_positive_gap_threshold_is_not_padded_by_roundoff(monkeypatch, gap):
    pi, rho = -8e-10, -gap + 8e-10
    expected = fsum([0, -pi, -min(0, rho)])
    eta = 32*ulp(fsum([abs(pi), abs(rho)]))
    assert expected == gap and rho >= -1e-9
    if gap > 1e-9:
        assert gap - 1e-9 < eta  # Even this much smaller excess must be rejected.
    result = _synthetic_convexity_snapshot(monkeypatch, cost=0, other=-gap, pi=pi)
    if gap <= 1e-9:
        assert result.status == cg.DagColumnGenerationStatus.TOLERANCE_REACHED
        assert result.iterations[-1].objective_gap == gap
    else:
        assert result.status == cg.DagColumnGenerationStatus.NUMERICAL_ISSUE


@pytest.mark.parametrize('c0', [0, 2**40, -(2**40)])
@pytest.mark.parametrize('conflict', ['positive', 'negative'])
def test_substantive_gap_conflicts_survive_large_constants(monkeypatch, c0, conflict):
    cost, other, pi, weight = (0, -1.5e-9, -8e-10, 1) if conflict == 'positive' else (
        1, 1, 1, 1-5e-10)
    p, d, delta = cost*weight, pi, min(0, other-pi)
    gap = fsum([p, -d, -delta])
    scale = fsum([abs(p), abs(d), abs(delta)])
    eta = 32*ulp(scale)
    if conflict == 'negative':
        assert -gap > eta, (gap, scale, eta)
    else:
        assert gap > 1e-9
    if c0:
        assert fsum([fsum([c0, p]), -fsum([c0, d, delta])]) == 0
    result = _synthetic_convexity_snapshot(monkeypatch, cost=cost, other=other,
                                          weight=weight, pi=pi, c0=c0)
    assert result.status == cg.DagColumnGenerationStatus.NUMERICAL_ISSUE
    assert result.iterations[-1].objective_gap is result.iterations[-1].roundoff_allowance is None


def test_zero_absolute_scale_uses_actual_ulp_zero_and_signed_cancellation():
    zero = cg.solve_dag_column_generation(single()).iterations[-1]
    assert zero.objective_gap == zero.numerical_gap == 0
    assert zero.roundoff_allowance == 32*ulp(0) > 0
    record = cg.solve_dag_column_generation(single(-1)).iterations[-1]
    assert record.objective_gap == 0 and record.roundoff_allowance == 32*ulp(2)


@pytest.mark.parametrize('cost', [1e308, -1e308])
def test_absolute_contribution_sum_overflow_is_not_a_valid_allowance(monkeypatch, cost):
    assert fsum([cost, -cost]) == 0  # The signed sum is finite; the absolute sum overflows.
    result = _synthetic_convexity_snapshot(monkeypatch, cost=cost, other=cost, pi=cost)
    assert result.status == cg.DagColumnGenerationStatus.NUMERICAL_ISSUE
    record = result.iterations[-1]
    assert record.numerical_gap is record.objective_gap is record.roundoff_allowance is None


def test_appended_fields_preserve_legacy_positional_constructor_and_immutability():
    master = RestrictedMasterResult(SolverStatus.OPTIMAL)
    registry = {'legacy': ['seed']}
    legacy = cg.DagColumnGenerationIteration(7, registry, master, None, 1, 1, 0, 1, 0, ('seed',))
    assert legacy.accepted_path == ('seed',)
    assert legacy.objective_gap is legacy.roundoff_allowance is None
    registry['legacy'].append('other')
    assert legacy.column_paths == {'legacy': ('seed',)}
    with pytest.raises(FrozenInstanceError):
        legacy.objective_gap = 0
    first = cg.solve_dag_column_generation(single(-1))
    second = cg.solve_dag_column_generation(single())
    assert first.iterations[0].objective_gap == 1
    assert second.iterations[0].objective_gap == 0
