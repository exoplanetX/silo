"""Fixed append-only histories, analytic vertices and observed solver paths."""

from copy import deepcopy
from fractions import Fraction as F
from itertools import combinations, permutations, product

import pytest

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense as S
from silo.core.enums import OptimizationSense as O
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus as Status
from silo.core.variable import Variable
from silo.decomposition import RestrictedMasterProblem
from silo.lp.simplex import revised
from silo.lp.simplex.tableau import TableauSimplexSolver

CASES = list(product(((.5, 1.5), (.25, 1.75)),
                     (((2, 0, -1), 7), ((0, 4, 10), -3), ((0, 0, 0), 0)),
                     (('p0', 'p2'), ('p2', 'p0')), permutations(('conv', 'lo', 'hi')),
                     (False, True)))


def history(case):
    (lo, hi), (costs, constant), order, row_order, negative = case
    means = {'p1': 1, 'p0': 0, 'p2': 2}
    costs = dict(zip(('p1', 'p0', 'p2'), costs, strict=True))
    sign = -1 if negative else 1
    senses = {'conv': S.EQ, 'lo': S.LE if negative else S.GE,
              'hi': S.GE if negative else S.LE}
    rhs = {'conv': 1, 'lo': lo, 'hi': hi}
    rows = [Constraint(n, {'p1': sign}, senses[n], sign * rhs[n]) for n in row_order]
    initial = Model('history', [Variable('p1')], rows,
                    Objective({'p1': costs['p1']}, O.MINIMIZE, constant))
    additions = [(n, costs[n], {r: sign * (1 if r == 'conv' else means[n])
                               for r in row_order}) for n in order]
    models = [initial]
    for n, cost, coefficients in additions:
        m = deepcopy(models[-1])
        m.variables.append(Variable(n))
        m.objective.coefficients[n] = cost
        for row in m.constraints:
            row.coefficients[n] = coefficients[row.name]
        models.append(m)
    return models + [deepcopy(models[-1])], additions, means, costs, F(lo), F(hi)


def analytic_optimum(names, means, costs, lo, hi, constant):
    """Vertices of a probability simplex cut by a one-dimensional interval."""
    candidates = [{n: F(int(n == chosen)) for n in names} for chosen in names]
    for a, b in combinations(names, 2):
        for endpoint in (lo, hi):
            weight = (endpoint - F(means[b])) / F(means[a] - means[b])
            candidates.append({n: weight if n == a else 1 - weight if n == b else F(0)
                               for n in names})
    feasible = [x for x in candidates if min(x.values()) >= 0
                and lo <= sum(F(means[n]) * x[n] for n in names) <= hi]
    assert feasible
    return min(F(constant) + sum(F(costs[n]) * x[n] for n in names) for x in feasible)


def assert_min_evidence(model, result, optimum):
    assert result.status == Status.OPTIMAL
    assert F(result.objective_value) == optimum
    assert set(result.primal_values) == set(result.reduced_costs) == set(model.variable_names())
    assert set(result.dual_values) == {r.name for r in model.constraints}
    x, pi = result.primal_values, result.dual_values
    for row in model.constraints:
        residual = sum(F(a) * F(x[n]) for n, a in row.coefficients.items()) - F(row.rhs)
        if row.sense == S.LE:
            assert residual <= 0 and F(pi[row.name]) <= 0
        elif row.sense == S.GE:
            assert residual >= 0 and F(pi[row.name]) >= 0
        else:
            assert residual == 0
        assert F(pi[row.name]) * residual == 0
    for name in model.variable_names():
        rc = F(model.objective.coefficients[name]) - sum(
            F(row.coefficients.get(name, 0)) * F(pi[row.name]) for row in model.constraints)
        assert rc == F(result.reduced_costs[name]) and rc >= 0 and F(x[name]) >= 0
        assert rc * F(x[name]) == 0
    primal = F(model.objective.constant) + sum(F(c) * F(x[n])
                                             for n, c in model.objective.coefficients.items())
    dual = F(model.objective.constant) + sum(F(r.rhs) * F(pi[r.name]) for r in model.constraints)
    assert primal == dual == optimum


def semantic_keys(problem, basis):
    # Observation only; this does not construct candidates or analytic truth.
    return tuple((problem.columns[j].role, problem.columns[j].original_name
                  if problem.columns[j].role == 'original' else
                  problem.columns[j].source_constraint) for j in basis.basic_columns)


class ObservedRevised(revised.RevisedSimplexSolver):
    def __init__(self):
        super().__init__()
        self.cold_calls = 0
        self.previous = None

    def solve_with_details(self, model, basis=None):
        self.cold_calls += 1
        assert basis is None  # old bare-basis artificial rejection is never used
        return super().solve_with_details(model, basis=basis)

    def reoptimize(self, model, snapshot=None):
        result = super().reoptimize(model, snapshot)
        self.previous = result
        return result


@pytest.mark.parametrize('case', CASES, ids=[f'history-{i:03}' for i in range(144)])
def test_fixed_history_actual_warm_paths_and_independent_truth(case, monkeypatch):
    models, additions, means, costs, lo, hi = history(case)
    owner = RestrictedMasterProblem(models[0])
    references = [RestrictedMasterProblem(models[0]) for _ in range(2)]
    solver = ObservedRevised()
    trace = []
    original = revised._run_primal_revised_simplex

    def observe(**kw):
        entry = (kw['phase_name'], kw['problem'], kw['basis'])
        result = original(**kw)
        trace.append((*entry, result.iterations))
        return result

    monkeypatch.setattr(revised, '_run_primal_revised_simplex', observe)
    for step, m in enumerate(models):
        if step in (1, 2):
            n, cost, coefficients = additions[step - 1]
            for target in (owner, *references):
                target.add_column(name=n, cost=cost, row_coefficients=coefficients)
        old_snapshot = None if solver.previous is None else solver.previous.snapshot
        trace.clear()
        before = solver.cold_calls
        outcome = owner.solve_reoptimized(solver)
        assert outcome.used_warm_start == (step > 0)
        assert outcome.warm_phase_two_attempted == (step > 0)
        assert outcome.cold_solve_count == solver.cold_calls - before == int(step == 0)
        assert not outcome.fallback_reason and outcome.snapshot_available
        assert solver.previous.snapshot is not None
        phases = [entry[0] for entry in trace]
        assert phases == (['Phase I', 'Phase II'] if step == 0 else ['Phase II'])
        if step:
            _, problem, basis, iterations = trace[0]
            assert problem.row_names == tuple(r.name for r in m.constraints)
            assert not problem.artificial_columns
            assert all(c.role != 'artificial' for c in problem.columns)
            assert semantic_keys(problem, basis) == old_snapshot.basis_keys
            if step in (1, 2):
                added = additions[step - 1][0]
                index = next(j for j, c in enumerate(problem.columns)
                             if c.role == 'original' and c.original_name == added)
                assert index in basis.nonbasic_columns
            assert outcome.warm_iterations == iterations
            if step == 3:
                assert iterations == 0
        optimum = analytic_optimum(m.variable_names(), means, costs, lo, hi, m.objective.constant)
        assert_min_evidence(m, outcome.result, optimum)
        # Independent owners: calling ordinary solve must not clear warm owner's cache.
        for reference, backend in zip(references, (revised.RevisedSimplexSolver,
                                                  TableauSimplexSolver), strict=True):
            assert_min_evidence(m, reference.solve(backend()), optimum)
