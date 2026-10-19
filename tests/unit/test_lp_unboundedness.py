"""Terminal witness checks, coordinate failures and unchanged caller propagation."""

from copy import deepcopy
from dataclasses import replace
from fractions import Fraction
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
from silo.core.status import SolverStatus as Status
from silo.core.variable import Variable
from silo.decomposition import (
    DagArc,
    DagColumnGenerationProblem,
    DagMasterRow,
    DagPricingProblem,
    RestrictedMasterProblem,
)
from silo.decomposition.dag_column_generation import (
    DagColumnGenerationStatus,
    solve_dag_column_generation,
)
from silo.decomposition.dag_feasibility import DagFeasibilityStatus, restore_dag_feasibility
from silo.lp.simplex import revised, tableau
from silo.lp.simplex.basis import Basis
from silo.lp.unboundedness import check_lp_unboundedness as check
from silo.mip.branch_and_bound import BranchAndBoundSolver

BACKENDS = (tableau.TableauSimplexSolver, revised.RevisedSimplexSolver)


def model(rows=(), names=('x', 'z'), costs=None, constant=5):
    return Model('witness', [Variable(n) for n in names], list(rows),
                 Objective({'z': 1} if costs is None else costs, O.MAXIMIZE, constant))


def empty_evidence(solution, status):
    assert solution.status == status
    assert solution.objective_value is None
    assert not any((solution.primal_values, solution.slack_values, solution.dual_values,
                    solution.reduced_costs, solution.basis_status))


@pytest.mark.parametrize('sense', (S.LE, S.GE, S.EQ))
def test_valid_original_point_and_coupled_direction_are_read_only(sense):
    m = model([Constraint('negative', {'x': -1, 'z': 1}, sense, -2)])
    point, direction = {'x': 2, 'z': 0}, {'x': 1, 'z': 1}
    before = deepcopy((m, point, direction))
    result = check(m, point, direction)
    assert result.passed
    assert (m, point, direction) == before


@pytest.mark.parametrize('sense,coefficient', ((S.LE, 1), (S.GE, -1), (S.EQ, 1)))
@pytest.mark.parametrize('power', (-100, 0, 100))
def test_tiny_direction_residual_is_rejected_under_binary_scaling(sense, coefficient, power):
    m = model([Constraint('tiny', {'z': coefficient * 2**-40}, sense, 0)])
    result = check(m, {'x': 0, 'z': 0}, {'x': 0, 'z': 2.0**power})
    assert not result.passed and 'Direction' in result.message and 'tiny' in result.message


@pytest.mark.parametrize('sense,coefficient', ((S.LE, 1), (S.GE, -1), (S.EQ, 1)))
def test_tiny_point_residual_is_rejected_with_a_valid_direction(sense, coefficient):
    m = model([Constraint('fixed', {'x': coefficient}, sense, 0)])
    result = check(m, {'x': 2**-40, 'z': 0}, {'x': 0, 'z': 1})
    assert not result.passed and 'Point' in result.message and 'fixed' in result.message


@pytest.mark.parametrize('slope', (0, -1))
def test_zero_or_negative_objective_improvement_is_rejected(slope):
    m = model(costs={'z': slope})
    assert 'improvement' in check(m, {'x': 0, 'z': 0}, {'x': 0, 'z': 1}).message


def test_zero_ray_and_tiny_negative_coordinate_are_rejected():
    m = model()
    assert not check(m, {'x': 0, 'z': 0}, {'x': 0, 'z': 0}).passed
    result = check(m, {'x': 0, 'z': 0}, {'x': -2**-50, 'z': 1})
    assert not result.passed and 'Direction' in result.message and "'x'" in result.message


def test_strictly_positive_improvement_has_no_absolute_threshold():
    assert check(model(costs={'z': 2**-100}), {'x': 0, 'z': 0}, {'x': 0, 'z': 1}).passed


@pytest.mark.parametrize('epsilon', (2**-32, 2**-24))
@pytest.mark.parametrize('bound', (0, 1))
@pytest.mark.parametrize('power', (-100, 0, 100))
def test_tiny_negative_coefficients_keep_valid_scaled_rays(epsilon, bound, power):
    m = model([Constraint('tiny', {'z': -epsilon}, S.LE, bound)])
    assert check(m, {'x': 0, 'z': 0}, {'x': 0, 'z': 2.0**power}).passed


@pytest.mark.parametrize('target', ('point', 'direction'))
@pytest.mark.parametrize('bad', ({'x': 0}, {'x': 0, 'z': 1, 'slack_r': 0}, None))
def test_incomplete_or_extra_coordinates(target, bad):
    values = {'point': {'x': 0, 'z': 0}, 'direction': {'x': 0, 'z': 1}}
    values[target] = bad
    result = check(model(), **values)
    assert not result.passed and 'coordinates' in result.message


@pytest.mark.parametrize('target', ('point', 'direction', 'cost', 'constant', 'rhs', 'coefficient'))
@pytest.mark.parametrize('value', (nan, inf, -inf, '1'))
def test_nonfinite_or_nonnumeric_evidence(target, value):
    m = model([Constraint('r', {'x': 1}, S.EQ, 0)])
    point, direction = {'x': 0, 'z': 0}, {'x': 0, 'z': 1}
    if target == 'point':
        point['x'] = value
    elif target == 'direction':
        direction['x'] = value
    elif target == 'cost':
        m.objective.coefficients['z'] = value
    elif target == 'constant':
        m.objective = replace(m.objective, constant=value)
    elif target == 'rhs':
        m.constraints[0] = replace(m.constraints[0], rhs=value)
    else:
        m.constraints[0].coefficients['x'] = value
    result = check(m, point, direction)
    assert not result.passed
    assert ('Nonfinite' if value != '1' else 'Nonnumeric') in result.message


@pytest.mark.parametrize('kind', ('minimum', 'integer', 'upper', 'lower', 'unknown'))
def test_unsupported_or_invalid_model_domain(kind):
    m = model()
    if kind == 'minimum':
        m.objective = replace(m.objective, sense=O.MINIMIZE)
    elif kind == 'integer':
        m.variables[0] = Variable('x', var_type=VariableType.INTEGER)
    elif kind == 'upper':
        m.variables[0] = Variable('x', Bounds(0, 1))
    elif kind == 'lower':
        m.variables[0] = Variable('x', Bounds(-1, inf))
    else:
        m.objective.coefficients['unknown'] = 1
    assert not check(m, {'x': 0, 'z': 0}, {'x': 0, 'z': 1}).passed


def test_actual_small_nonzero_lower_bound_is_respected():
    m = model()
    m.variables[0] = Variable('x', Bounds(2**-40, inf))
    assert not check(m, {'x': 0, 'z': 0}, {'x': 0, 'z': 1}).passed
    assert check(m, {'x': 2**-40, 'z': 0}, {'x': 0, 'z': 1}).passed
    m.variables[0] = Variable('x', Bounds(-2**-40, inf))
    assert check(m, {'x': -2**-40, 'z': 0}, {'x': 0, 'z': 1}).passed


def test_integer_input_above_float_precision_is_preserved():
    big = 2**53 + 1
    m = model([Constraint('big', {'x': 1}, S.EQ, big)])
    assert check(m, {'x': big, 'z': 0}, {'x': 0, 'z': 1}).passed
    assert not check(m, {'x': float(big), 'z': 0}, {'x': 0, 'z': 1}).passed
    m = model(costs={'x': big, 'z': -(big - 1)})
    assert check(m, {'x': 0, 'z': 0}, {'x': 1, 'z': 1}).passed  # exact improvement 1
    m = model([Constraint('big', {'x': big, 'z': -(big - 1)}, S.EQ, 0)])
    assert not check(m, {'x': 0, 'z': 0}, {'x': 1, 'z': 1}).passed


def test_float_inputs_mean_actual_binary_values():
    m = model([Constraint('decimal', {'x': 10}, S.EQ, 1)])
    assert not check(m, {'x': .1, 'z': 0}, {'x': 0, 'z': 1}).passed
    m.constraints[0] = Constraint('binary', {'x': 1}, S.EQ, .1)
    assert check(m, {'x': .1, 'z': 0}, {'x': 0, 'z': 1}).passed


@pytest.mark.parametrize('target', ('point', 'direction'))
def test_convert_original_terms_before_near_cancellation(target):
    a, b = 1 + 2**-27, 1 - 2**-27
    assert a * b - 1 == 0
    assert Fraction(a) * Fraction(b) - 1 == -Fraction(1, 2**54)
    m = model([Constraint('cancellation', {'x': a, 'y': -1}, S.EQ, 0)], ('x', 'y', 'z'))
    point = {'x': 0, 'y': 0, 'z': 0}
    direction = {'x': 0, 'y': 0, 'z': 1}
    (point if target == 'point' else direction).update(x=b, y=1)
    result = check(m, point, direction)
    assert not result.passed and target.capitalize() in result.message


def test_a_recession_direction_cannot_prove_nonempty_feasible_region():
    m = model([Constraint('a', {'x': 1}, S.EQ, 1), Constraint('b', {'x': 1}, S.EQ, 2)])
    result = check(m, {'x': 1, 'z': 0}, {'x': 0, 'z': 1})
    assert not result.passed and 'Point' in result.message


@pytest.mark.parametrize('backend', BACKENDS)
@pytest.mark.parametrize('kind', ('empty', 'coupled', 'negative-rhs', 'mixed', 'internal-name'))
def test_public_unbounded_paths_keep_empty_optimal_fields(backend, kind):
    rows = []
    names, costs = ('x', 'z'), {'z': 1}
    if kind == 'coupled':
        rows = [Constraint('r', {'x': 1, 'z': -1}, S.EQ, 2)]
    elif kind == 'negative-rhs':
        rows = [Constraint('lo', {'x': -1}, S.LE, -2)]
        costs = {'x': 1}
    elif kind == 'mixed':
        rows = [Constraint('eq', {'x': 1, 'z': -1}, S.EQ, 2),
                Constraint('le', {'x': -1, 'z': 1}, S.LE, -2),
                Constraint('ge', {'x': 2, 'z': -2}, S.GE, 4),
                Constraint('duplicate', {'x': 1, 'z': -1}, S.EQ, 2)]
    elif kind == 'internal-name':
        names, costs = ('slack_r', 'z'), {'z': 1}
        rows = [Constraint('r', {'slack_r': -1, 'z': 1}, S.LE, 1)]
    solution = backend().solve(model(rows, names, costs))
    empty_evidence(solution, Status.UNBOUNDED)
    assert 'verified exactly' in solution.message
    if backend is tableau.TableauSimplexSolver:
        assert 'no positive pivot row' in solution.message


@pytest.mark.parametrize('backend', BACKENDS)
@pytest.mark.parametrize('kind', ('third', 'near-contradiction', 'large-int', 'lower-bound'))
def test_conservative_point_rejection_on_original_model(backend, kind):
    rows = [Constraint('fixed', {'x': 3}, S.EQ, 1)]
    if kind == 'near-contradiction':
        rows = [Constraint('a', {'x': 1}, S.EQ, 1),
                Constraint('b', {'x': 1}, S.EQ, 1 + 2**-40)]
    elif kind == 'large-int':
        rows = [Constraint('fixed', {'x': 1}, S.EQ, 2**53 + 1)]
    elif kind == 'lower-bound':
        rows = []
    m = model(rows)
    if kind == 'lower-bound':
        m.variables[0] = Variable('x', Bounds(2**-40, inf))
    solution = backend().solve(m)
    empty_evidence(solution, Status.NUMERICAL_ISSUE)
    assert 'Point' in solution.message


@pytest.mark.parametrize('backend', BACKENDS)
def test_phase_one_unbounded_is_a_numerical_contradiction(monkeypatch, backend):
    m = model([Constraint('r', {'x': 1}, S.EQ, 1)])
    if backend is tableau.TableauSimplexSolver:
        monkeypatch.setattr(tableau, '_run_simplex_iterations',
                            lambda **kw: tableau.SimplexRunResult(Status.UNBOUNDED))
    else:
        monkeypatch.setattr(revised, '_run_primal_revised_simplex',
                            lambda **kw: revised.RevisedRunResult(Status.UNBOUNDED, kw['basis']))
    solution = backend().solve(m)
    empty_evidence(solution, Status.NUMERICAL_ISSUE)
    assert 'Phase I' in solution.message


@pytest.mark.parametrize('backend', BACKENDS)
@pytest.mark.parametrize('kind', ('missing', 'basic', 'out-of-range', 'basis'))
def test_public_terminal_missing_or_invalid_internal_coordinates(monkeypatch, backend, kind):
    m = model([Constraint('r', {'x': 1, 'z': -1}, S.EQ, 1)])
    module = tableau if backend is tableau.TableauSimplexSolver else revised
    name = '_run_simplex_iterations' if module is tableau else '_run_primal_revised_simplex'
    original = getattr(module, name)

    def corrupt(**kw):
        result = original(**kw)
        if kw['phase_name'] == 'Phase II':
            basis = kw['tableau'].basis if module is tableau else result.basis.basic_columns
            entering = {'missing': None, 'basic': basis[0], 'out-of-range': 10,
                        'basis': result.entering_column}[kind]
            result = replace(result, entering_column=entering)
            if kind == 'basis':
                if module is tableau:
                    kw['tableau'].basis.append(basis[0])
                else:
                    result = replace(result, basis=Basis((0, 0), (1,)))
        return result

    monkeypatch.setattr(module, name, corrupt)
    solution = backend().solve(m)
    empty_evidence(solution, Status.NUMERICAL_ISSUE)
    assert 'coordinates' in solution.message


def test_tableau_basic_column_selected_by_drift_is_rejected(monkeypatch):
    # Synthetic drift: basic column x has zero row coefficient but a negative
    # objective entry, so the old pricing/no-leaving signal would claim UNB.
    tab = tableau.SimplexTableau(('x', 'z'), 2, [[0, -1, 1]], [-1, 0, 0], [0])
    monkeypatch.setattr(tableau, '_build_initial_tableau',
                        lambda m: tableau.TableauBuildResult(tab, ()))
    monkeypatch.setattr(tableau, '_restore_phase_two_objective', lambda *a: None)
    empty_evidence(tableau.TableauSimplexSolver().solve(model()), Status.NUMERICAL_ISSUE)


@pytest.mark.parametrize('backend', BACKENDS)
@pytest.mark.parametrize('target,value', (('point', -2**-40), ('direction', -2**-40),
                                         ('point', nan), ('direction', inf)))
def test_terminal_candidate_retains_raw_small_and_nonfinite_coordinates(
    monkeypatch, backend, target, value,
):
    m = model([Constraint('r', {'x': 1, 'z': -1}, S.EQ, 1)])
    if backend is tableau.TableauSimplexSolver:
        original = tableau._run_simplex_iterations

        def corrupt(**kw):
            result = original(**kw)
            if kw['phase_name'] == 'Phase II':
                tab = kw['tableau']
                tab.rows[0][-1 if target == 'point' else result.entering_column] = (
                    value if target == 'point' else -value)
            return result

        monkeypatch.setattr(tableau, '_run_simplex_iterations', corrupt)
    else:
        original_terminal = revised._unbounded_solution
        original_solve = np.linalg.solve

        def corrupt_terminal(*args):
            call = 0

            def corrupt_solve(*solve_args):
                nonlocal call
                call += 1
                raw = original_solve(*solve_args)
                if (call == 1) == (target == 'point'):
                    raw[0] = value if target == 'point' else -value
                return raw

            with monkeypatch.context() as patch:
                patch.setattr(np.linalg, 'solve', corrupt_solve)
                return original_terminal(*args)

        monkeypatch.setattr(revised, '_unbounded_solution', corrupt_terminal)
    result = backend().solve(m)
    empty_evidence(result, Status.NUMERICAL_ISSUE)
    assert target in result.message.lower()


@pytest.mark.parametrize('kind', ('role', 'name', 'duplicate', 'matrix', 'nonnumeric',
                                 'basis-type', 'missing-basis'))
def test_revised_internal_projection_and_basis_failures(kind):
    m = model()
    problem = revised.build_standard_form(m)
    result = revised.RevisedRunResult(Status.UNBOUNDED, problem.initial_basis, entering_column=1)
    if kind == 'role':
        problem = replace(problem, columns=(replace(problem.columns[0], role='slack'),
                                            problem.columns[1]))
    elif kind == 'name':
        problem = replace(problem, columns=(replace(problem.columns[0], original_name='wrong'),
                                            problem.columns[1]))
    elif kind == 'duplicate':
        problem = replace(problem, columns=(problem.columns[1], problem.columns[1]))
    elif kind == 'matrix':
        problem = replace(problem, matrix=((1,),))
    elif kind == 'nonnumeric':
        problem = replace(problem, matrix=(('bad', -1),), row_names=('r',), rhs=(1,))
        result = replace(result, basis=Basis((0,), (1,)))
    elif kind == 'basis-type':
        result = replace(result, basis=Basis((), (0, 'bad')))
    else:
        result = replace(result, basis=None)
    solution = revised._unbounded_solution(m, problem, result)
    empty_evidence(solution, Status.NUMERICAL_ISSUE)
    assert 'coordinates' in solution.message


def test_revised_terminal_basis_solve_failure_and_programming_error(monkeypatch):
    original_terminal = revised._unbounded_solution
    original_solve = np.linalg.solve
    terminal = False

    def mark_terminal(*args):
        nonlocal terminal
        terminal = True
        return original_terminal(*args)

    def solve(*args):
        if terminal:
            raise np.linalg.LinAlgError('injected terminal failure')
        return original_solve(*args)

    monkeypatch.setattr(revised, '_unbounded_solution', mark_terminal)
    monkeypatch.setattr(np.linalg, 'solve', solve)
    solution = revised.RevisedSimplexSolver().solve(model())
    empty_evidence(solution, Status.NUMERICAL_ISSUE)
    assert 'basis solve failed' in solution.message

    def bug(*args):
        raise RuntimeError('programming error')

    monkeypatch.setattr(np.linalg, 'solve', bug)
    with pytest.raises(RuntimeError, match='programming error'):
        original_terminal(model(), revised.build_standard_form(model()),
                          revised.RevisedRunResult(Status.UNBOUNDED, Basis((), (0, 1)),
                                                   entering_column=1))


@pytest.mark.parametrize('backend', BACKENDS)
def test_checker_programming_errors_are_not_swallowed(monkeypatch, backend):
    def broken(*args):
        raise RuntimeError('checker programming error')

    module = tableau if backend is tableau.TableauSimplexSolver else revised
    monkeypatch.setattr(module, 'check_lp_unboundedness', broken)
    with pytest.raises(RuntimeError, match='checker programming error'):
        backend().solve(model())


def test_revised_details_and_compatible_warm_start_use_original_guard(monkeypatch):
    m = model([Constraint('r', {'x': -1, 'z': 1}, S.LE, 0)])
    calls = []
    original = revised.check_lp_unboundedness

    def observe(m, point, direction):
        calls.append((m, dict(point), dict(direction)))
        return original(m, point, direction)

    monkeypatch.setattr(revised, 'check_lp_unboundedness', observe)
    solver = revised.RevisedSimplexSolver()
    cold = solver.solve_with_details(m)
    warm = solver.solve_with_details(m, basis=cold.basis)
    empty_evidence(cold.solution, Status.UNBOUNDED)
    empty_evidence(warm.solution, Status.UNBOUNDED)
    assert warm.used_warm_start and len(calls) == 2 and all(c[0] is m for c in calls)
    assert calls[0][1:] == calls[1][1:] == ({'x': 0.0, 'z': 0.0}, {'x': 1.0, 'z': 1.0})


@pytest.mark.parametrize('backend', BACKENDS)
def test_finite_literal_min_rmp_propagates_numerical_issue_with_empty_fields(backend):
    m = model([Constraint('a', {'x': 1, 'z': -(1 + 5e-10)}, S.EQ, 1e10),
               Constraint('b', {'x': 1, 'z': -1}, S.EQ, 1e10)], costs={'z': -1})
    m.objective = replace(m.objective, sense=O.MINIMIZE)
    result = RestrictedMasterProblem(m).solve(backend())
    assert result.status == Status.NUMERICAL_ISSUE
    assert result.objective_value is None
    assert not any((result.primal_values, result.dual_values, result.reduced_costs))


def dag_example():
    graph = DagPricingProblem(['s', 't'], [DagArc('seed', 's', 't', 1)],
                              's', 't', ['conv'], base_coefficients={'conv': 1})
    return DagColumnGenerationProblem(graph, [DagMasterRow('conv', S.EQ, 1)],
                                      'conv', [('seed',)])


class NumericalBackend:
    def solve(self, model):
        return Solution(Status.NUMERICAL_ISSUE, message='terminal witness rejected')


def test_cg_and_auxiliary_recovery_propagate_master_failure():
    problem = dag_example()
    cg = solve_dag_column_generation(problem, solver=NumericalBackend())
    recovery = restore_dag_feasibility(problem, solver=NumericalBackend())
    assert cg.status == DagColumnGenerationStatus.MASTER_FAILURE
    assert recovery.status == DagFeasibilityStatus.MASTER_FAILURE
    assert cg.last_valid_master is recovery.feasibility_witness is None
    assert cg.iterations[0].master_result.status == Status.NUMERICAL_ISSUE
    assert recovery.iterations[0].master_result.status == Status.NUMERICAL_ISSUE


def test_recovery_original_validation_propagates_numerical_issue():
    class FailValidation:
        def __init__(self):
            self.count = 0

        def solve(self, m):
            self.count += 1
            return (revised.RevisedSimplexSolver().solve(m) if self.count == 1 else
                    NumericalBackend().solve(m))

    result = restore_dag_feasibility(dag_example(), solver=FailValidation())
    assert result.status == DagFeasibilityStatus.NUMERICAL_ISSUE
    assert result.failure_stage == 'original_validation'
    assert result.feasible_problem is result.feasibility_witness is None
    assert result.iterations[0].original_validation.status == Status.NUMERICAL_ISSUE


def test_mip_numerical_failure_propagates_without_incumbent_or_unbounded_status():
    result = BranchAndBoundSolver(lp_solver=NumericalBackend()).solve_with_details(model())
    empty_evidence(result.solution, Status.NUMERICAL_ISSUE)
    assert result.incumbent_value is None
