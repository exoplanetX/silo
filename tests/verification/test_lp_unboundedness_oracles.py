"""Analytic truth and independent exact checks of actual terminal candidates.

Old status masks were recorded on 26f3c48 before changing production code.
Cartesian-product order below fixes each baseline case's identity.
"""

from collections import Counter
from fractions import Fraction as F
from itertools import product

import pytest

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense as S
from silo.core.enums import OptimizationSense as O
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus as Status
from silo.core.variable import Variable
from silo.lp.optimality import check_lp_optimality
from silo.lp.simplex import revised, tableau

BACKENDS = (tableau.TableauSimplexSolver, revised.RevisedSimplexSolver)
EPSILONS = (-2**-24, -2**-32, 0, 2**-32, 2**-24)
# Measured old OPTIMAL cases: 96, not a prediction from epsilon magnitude.
OLD_OPTIMAL_IDS = frozenset((
    0, 1, 2, 3, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23,
    24, 25, 26, 27, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47,
    68, 69, 70, 71, 92, 93, 94, 95, 164, 165, 166, 167, 188, 189, 190, 191,
    192, 193, 194, 195, 200, 201, 202, 203, 204, 205, 206, 207, 208, 209, 210, 211,
    212, 213, 214, 215, 216, 217, 218, 219, 224, 225, 226, 227, 228, 229, 230, 231,
    232, 233, 234, 235, 236, 237, 238, 239,
))


def paired_model(epsilon, bound, scale, reverse_rows, reverse_variables, constant=-3):
    rows = [
        Constraint('r1', {'x': scale, 'z': -scale * (1 + epsilon)}, S.EQ, scale * bound),
        Constraint('r2', {'x': 1, 'z': -1}, S.EQ, bound),
    ]
    names = ('z', 'x') if reverse_variables else ('x', 'z')
    return Model('paired', [Variable(n) for n in names],
                 rows[::-1] if reverse_rows else rows, Objective({'z': 1}, O.MAXIMIZE, constant))


def core_cases():
    for i, (e, b, q, r, v, k) in enumerate(product(
        EPSILONS, (1, 2**32), (2**-8, 1, 2**8), (0, 1), (0, 1), (0, 1),
    )):
        yield i, e, k, paired_model(e, b, q, r, v)


def control_cases():
    for r, v, k in product((0, 1), repeat=3):
        yield 'literal', k, paired_model(5e-10, 1e10, 1, r, v, 0), Status.OPTIMAL, 0
    for inconsistent in (False, True):
        for v, k in product((0, 1), repeat=2):
            rows = ([Constraint('lo', {'x': -1}, S.LE, -2),
                     Constraint('hi', {'x': -1}, S.GE, -1)] if inconsistent else
                    [Constraint('lo', {'x': -1, 'z': 1}, S.LE, -1)])
            model = Model('negative-rhs', [Variable(n) for n in
                          (('z', 'x') if v else ('x', 'z'))], rows,
                          Objective({'z': 1}, O.MAXIMIZE, 5))
            yield ('infeasible' if inconsistent else 'negative-rhs'), k, model, (
                Status.INFEASIBLE if inconsistent else Status.UNBOUNDED), None
    for e, b, sign, k in product((2**-32, 2**-24), (0, 1), (-1, 1), (0, 1)):
        model = Model('tiny', [Variable('z')],
                      [Constraint('bound', {'z': sign * e}, S.LE, b)],
                      Objective({'z': 1}, O.MAXIMIZE, 5))
        yield ('tiny-large' if e == 2**-24 else 'tiny-small'), k, model, (
            Status.UNBOUNDED if sign < 0 else Status.OPTIMAL), 5 + b / e


def assert_exact_witness(model, point, direction):
    """Independent original-term arithmetic; no production checker/reconstruction."""
    assert set(point) == set(direction) == set(model.variable_names())
    for variable in model.variables:
        assert F(point[variable.name]) >= F(variable.bounds.lower)
        assert F(direction[variable.name]) >= 0
    for row in model.constraints:
        activity = sum((F(a) * F(point[n]) for n, a in row.coefficients.items()), F(0))
        slope = sum((F(a) * F(direction[n]) for n, a in row.coefficients.items()), F(0))
        if row.sense == S.LE:
            assert activity <= F(row.rhs) and slope <= 0, row.name
        elif row.sense == S.GE:
            assert activity >= F(row.rhs) and slope >= 0, row.name
        else:
            assert activity == F(row.rhs) and slope == 0, row.name
    assert sum((F(c) * F(direction[n]) for n, c in model.objective.coefficients.items()),
               F(0)) > 0


def observe_guard(monkeypatch, k):
    module = (tableau, revised)[k]
    original = module.check_lp_unboundedness
    calls = []

    def observe(model, point, direction):
        result = original(model, point, direction)
        calls.append((model, dict(point), dict(direction), result))
        return result

    monkeypatch.setattr(module, 'check_lp_unboundedness', observe)
    return calls


def assert_empty_nonoptimal(solution):
    assert solution.objective_value is None
    assert not any((solution.primal_values, solution.slack_values, solution.dual_values,
                    solution.reduced_costs, solution.basis_status))


@pytest.mark.parametrize('case', list(core_cases()), ids=lambda c: f'core-{c[0]}')
def test_core_original_truth_and_actual_candidates(case, monkeypatch):
    i, epsilon, k, model = case
    # Solve the two original equations analytically in exact input arithmetic.
    rows = {r.name: r for r in model.constraints}
    scaled_z = F(rows['r1'].coefficients['z']) / F(rows['r1'].coefficients['x'])
    difference = scaled_z - F(rows['r2'].coefficients['z'])
    assert (difference == 0) == (epsilon == 0)
    calls = observe_guard(monkeypatch, k)
    solution = BACKENDS[k]().solve(model)
    if difference:
        assert solution.status in (Status.OPTIMAL, Status.NUMERICAL_ISSUE)
        if i in OLD_OPTIMAL_IDS:
            assert solution.status == Status.OPTIMAL
        if solution.status == Status.OPTIMAL:
            assert solution.objective_value == -3
            assert check_lp_optimality(model, solution, tolerance=1e-9).passed
        else:
            assert calls and not calls[-1][3].passed
            assert_empty_nonoptimal(solution)
    else:
        assert solution.status == Status.UNBOUNDED
        assert len(calls) == 1 and calls[0][0] is model and calls[0][3].passed
        assert_exact_witness(model, calls[0][1], calls[0][2])
        assert_empty_nonoptimal(solution)


@pytest.mark.parametrize('case', list(control_cases()), ids=lambda c: c[0])
def test_controls_original_truth_and_actual_candidates(case, monkeypatch):
    label, k, model, expected, optimum = case
    calls = observe_guard(monkeypatch, k)
    solution = BACKENDS[k]().solve(model)
    allowed = (expected, Status.NUMERICAL_ISSUE) if (
        expected == Status.OPTIMAL and label in ('literal', 'tiny-small')) else (expected,)
    assert solution.status in allowed
    if solution.status == Status.OPTIMAL:
        assert solution.objective_value == optimum
        assert check_lp_optimality(model, solution, tolerance=1e-9).passed
    else:
        assert_empty_nonoptimal(solution)
    if expected == Status.UNBOUNDED:
        assert len(calls) == 1 and calls[0][0] is model and calls[0][3].passed
        assert_exact_witness(model, calls[0][1], calls[0][2])
    elif solution.status == Status.NUMERICAL_ISSUE:
        assert calls and not calls[-1][3].passed


def test_fixed_family_inventory_and_old_optimal_baseline():
    cases = list(core_cases())
    assert len(cases) == 240 and len(OLD_OPTIMAL_IDS) == 96
    assert Counter(e == 0 for _, e, _, _ in cases) == {False: 192, True: 48}
    assert Counter(abs(cases[i][1]) for i in OLD_OPTIMAL_IDS) == {2**-24: 80, 2**-32: 16}
    assert Counter(c[3] for c in control_cases()) == {
        Status.OPTIMAL: 16, Status.UNBOUNDED: 12, Status.INFEASIBLE: 4,
    }
