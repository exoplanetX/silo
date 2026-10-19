"""Unit-violation feasibility restoration over a fixed ordinary DAG path domain.

Artificial columns have convexity coefficient zero. Real paths have coefficient
one and auxiliary cost zero. A small penalty requires a separate original-row
LP witness; original-cost optimization is an explicit later caller action.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from enum import Enum
from math import fsum, isfinite, ulp
from types import MappingProxyType

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.decomposition.dag_column_generation import DagColumnGenerationProblem
from silo.decomposition.dag_pricing import DagPricingResult, DagPricingStatus, price_dag
from silo.decomposition.restricted_master import RestrictedMasterProblem, RestrictedMasterResult
from silo.lp.base import LPSolver
from silo.utils.numerics import DEFAULT_TOLERANCE


class DagFeasibilityStatus(str, Enum):
    FEASIBLE_SEED_FOUND = 'feasible_seed_found'
    POSITIVE_VIOLATION_BOUND = 'positive_violation_bound'
    ITERATION_LIMIT = 'iteration_limit'
    MASTER_FAILURE = 'master_failure'
    PRICING_FAILURE = 'pricing_failure'
    NUMERICAL_ISSUE = 'numerical_issue'


def _mapping_copy(items):
    return MappingProxyType({name: tuple(value) for name, value in items.items()})


@dataclass(frozen=True)
class DagFeasibilityIteration:
    iteration: int
    column_paths: Mapping[str, tuple[str, ...]]
    artificial_columns: Mapping[str, tuple[str, float]]
    master_result: RestrictedMasterResult
    penalty_objective: float | None = None
    pricing_result: DagPricingResult | None = None
    original_validation: RestrictedMasterResult | None = None
    dual_objective: float | None = None
    rho: float | None = None
    numerical_lower_bound: float | None = None
    numerical_gap: float | None = None
    objective_gap: float | None = None
    roundoff_allowance: float | None = None
    accepted_path: tuple[str, ...] | None = None

    def __post_init__(self):
        object.__setattr__(self, 'column_paths', _mapping_copy(self.column_paths))
        object.__setattr__(self, 'artificial_columns', _mapping_copy(self.artificial_columns))
        if self.accepted_path is not None:
            object.__setattr__(self, 'accepted_path', tuple(self.accepted_path))


@dataclass(frozen=True)
class DagFeasibilityResult:
    status: DagFeasibilityStatus
    iterations: tuple[DagFeasibilityIteration, ...] = ()
    column_paths: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    artificial_columns: Mapping[str, tuple[str, float]] = field(default_factory=dict)
    column_set_iteration: int | None = None
    last_valid_master: RestrictedMasterResult | None = None
    last_valid_master_iteration: int | None = None
    feasible_problem: DagColumnGenerationProblem | None = None
    feasibility_witness: RestrictedMasterResult | None = None
    failure_iteration: int | None = None
    failure_stage: str | None = None
    auxiliary_solve_count: int = 0
    validation_solve_count: int = 0
    message: str = ''

    def __post_init__(self):
        object.__setattr__(self, 'iterations', tuple(self.iterations))
        object.__setattr__(self, 'column_paths', _mapping_copy(self.column_paths))
        object.__setattr__(self, 'artificial_columns', _mapping_copy(self.artificial_columns))


def restore_dag_feasibility(
    problem: DagColumnGenerationProblem, *, solver: LPSolver | None = None,
    tolerance: float = DEFAULT_TOLERANCE, iteration_limit: int = 100,
) -> DagFeasibilityResult:
    """Restore seeds, returning an original-row witness only after an extra LP.

    Auxiliary iterations and the at-most-one validation solve have separate
    counters. POSITIVE_VIOLATION_BOUND is numerical evidence, not a global
    INFEASIBLE status or a strict Farkas certificate.
    """
    if not isinstance(problem, DagColumnGenerationProblem):
        raise TypeError('problem must be a DagColumnGenerationProblem.')
    tolerance = _finite_input(tolerance)
    if tolerance <= 0:
        raise ValueError('tolerance must be positive.')
    if not isinstance(iteration_limit, int) or isinstance(iteration_limit, bool):
        raise TypeError('iteration_limit must be an integer.')
    if iteration_limit <= 0:
        raise ValueError('iteration_limit must be positive.')

    zero_graph = replace(problem.graph, base_cost=0,
                         arcs=tuple(replace(arc, cost=0) for arc in problem.graph.arcs))
    paths = {f'path_{i}': path for i, path in enumerate(problem.seed_paths)}
    artificial = {}
    for row in problem.rows:
        if row.name != problem.convexity_row:
            signs = (-1,) if row.sense == ConstraintSense.LE else (
                (1,) if row.sense == ConstraintSense.GE else (1, -1))
            for sign in signs:
                artificial[f'art_{len(artificial)}'] = (row.name, sign)
    history, last_paths = [], None
    last_master = last_iteration = None
    auxiliary_count = validation_count = 0

    def finish(status, message, failure=None, stage=None, feasible=None, witness=None):
        return DagFeasibilityResult(
            status=status, iterations=history,
            column_paths=last_paths if last_paths is not None else (
                history[-1].column_paths if history else {}),
            artificial_columns=artificial,
            column_set_iteration=last_iteration if last_paths is not None else (
                history[-1].iteration if history else None),
            last_valid_master=last_master, last_valid_master_iteration=last_iteration,
            feasible_problem=feasible, feasibility_witness=witness,
            failure_iteration=failure, failure_stage=stage,
            auxiliary_solve_count=auxiliary_count, validation_solve_count=validation_count,
            message=message,
        )

    try:
        columns = {name: (0.0, _path_data(zero_graph, path)) for name, path in paths.items()}
        for name, (row, sign) in artificial.items():
            columns[name] = (1.0, {j: float(sign) if j == row else 0.0
                                   for j in zero_graph.row_names})
    except _NumericalFailure as exc:
        return finish(DagFeasibilityStatus.NUMERICAL_ISSUE, str(exc), 1, 'initialization')
    master = _build_master(problem, columns)
    for iteration in range(1, iteration_limit + 1):
        auxiliary_count += 1
        snapshot = master.solve(solver)
        penalty = pricing = validation = None
        stage = 'auxiliary_master'

        record = DagFeasibilityIteration(iteration, paths, artificial, snapshot)
        if snapshot.status != SolverStatus.OPTIMAL:
            history.append(record)
            return finish(DagFeasibilityStatus.MASTER_FAILURE,
                          f'Auxiliary RMP: {snapshot.status.value}. {snapshot.message}',
                          iteration, stage)
        try:
            penalty, dual, p_terms, d_terms = _check_snapshot(
                problem, columns, artificial, snapshot)
            record = replace(record, penalty_objective=penalty)
            if penalty < -DEFAULT_TOLERANCE:
                raise _NumericalFailure('Auxiliary objective is below its nonnegative domain.')
            last_master, last_iteration, last_paths = snapshot, iteration, dict(paths)
            if penalty <= tolerance:
                stage = 'original_validation'
                real_columns = {name: columns[name] for name in paths}
                validation_count += 1
                validation = _build_master(problem, real_columns).solve(solver)
                record = replace(record, original_validation=validation)
                if validation.status != SolverStatus.OPTIMAL:
                    raise _NumericalFailure(
                        f'Original validation: {validation.status.value}. {validation.message}')
                _check_snapshot(problem, real_columns, {}, validation)
                history.append(record)
                feasible = replace(problem, seed_paths=tuple(paths.values()))
                return finish(DagFeasibilityStatus.FEASIBLE_SEED_FOUND,
                              'Original rows verified without artificial variables; original '
                              'objective optimization remains an explicit caller action.',
                              feasible=feasible, witness=validation)

            stage = 'pricing'
            pricing = price_dag(zero_graph, snapshot.dual_values, tolerance=tolerance)
            if not isinstance(pricing, DagPricingResult):
                raise _NumericalFailure('Pricing returned an invalid record.')
            record = replace(record, pricing_result=pricing)
            if pricing.status != DagPricingStatus.OPTIMAL:
                history.append(record)
                return finish(DagFeasibilityStatus.PRICING_FAILURE,
                              f'Zero-cost DAG pricing: {pricing.status}. {pricing.message}',
                              iteration, stage)
            path, coefficients, rho = _check_candidate(zero_graph, pricing,
                                                       snapshot.dual_values, tolerance)
            stage = 'bound_check'
            delta = min(0, rho)
            lower = _sum([*d_terms, delta])
            raw_gap = _sum([penalty, -lower])
            gap = _sum([*p_terms, *(-v for v in d_terms), -delta])
            scale = _sum([*(abs(v) for v in p_terms), *(abs(v) for v in d_terms), abs(delta)])
            eta = _product(32, ulp(scale))
            if gap < 0 and (eta > tolerance or -gap > eta):
                raise _NumericalFailure('Negative objective gap exceeds the local roundoff rule.')
            if rho >= -tolerance and gap > tolerance:
                raise _NumericalFailure('Objective gap exceeds tolerance after full pricing.')
            if rho < -tolerance and path in paths.values():
                raise _NumericalFailure('Significantly negative path is already existing.')
            if rho >= -tolerance and lower <= tolerance:
                raise _NumericalFailure('Positive restricted penalty lacks a separated lower bound')
        except _NumericalFailure as exc:
            history.append(record)
            return finish(DagFeasibilityStatus.NUMERICAL_ISSUE, str(exc), iteration, stage)

        accepted = path if rho < -tolerance and iteration < iteration_limit else None
        history.append(replace(record, dual_objective=dual, rho=rho, numerical_lower_bound=lower,
                               numerical_gap=raw_gap, objective_gap=gap,
                               roundoff_allowance=eta, accepted_path=accepted))
        if rho >= -tolerance:
            message = 'Full auxiliary path domain has a positive numerical violation lower bound.'
            if gap < 0:
                message += ' Negative objective gap accepted under the local roundoff rule.'
            return finish(DagFeasibilityStatus.POSITIVE_VIOLATION_BOUND, message)
        if iteration == iteration_limit:
            return finish(DagFeasibilityStatus.ITERATION_LIMIT,
                          'Auxiliary round budget exhausted; no unsolved path appended.')
        name = f'path_{len(paths)}'
        master.add_column(name=name, cost=0, row_coefficients=coefficients)
        paths[name], columns[name] = path, (0.0, coefficients)
    raise AssertionError('Positive round budget must produce a stopping decision.')


def _build_master(problem, columns):
    return RestrictedMasterProblem(Model(
        variables=[Variable(name) for name in columns],
        constraints=[Constraint(row.name, {name: a[row.name] for name, (_, a) in columns.items()},
                                row.sense, row.rhs) for row in problem.rows],
        objective=Objective({name: cost for name, (cost, _) in columns.items()},
                            OptimizationSense.MINIMIZE, 0),
    ))


def _path_data(graph, path):
    if isinstance(path, str | bytes):
        raise _NumericalFailure('A path must be a complete arc-ID sequence.')
    by_id = {arc.arc_id: arc for arc in graph.arcs}
    node, arcs = graph.source, []
    for arc_id in path:
        if not isinstance(arc_id, str) or arc_id not in by_id or by_id[arc_id].tail != node:
            raise _NumericalFailure('Pricing path is unknown or disconnected.')
        arcs.append(by_id[arc_id])
        node = arcs[-1].head
    if not arcs or node != graph.sink:
        raise _NumericalFailure('Path does not reach the declared sink.')
    return {row: _sum([graph.base_coefficients.get(row, 0),
                       *(arc.row_coefficients.get(row, 0) for arc in arcs)])
            for row in graph.row_names}


def _check_candidate(graph, result, pi, tolerance):
    coefficients = _path_data(graph, result.arc_ids)
    if set(result.row_coefficients) != set(graph.row_names):
        raise _NumericalFailure('Pricing coordinates differ from the fixed rows.')
    _close(result.cost, 0)
    for row in graph.row_names:
        _close(result.row_coefficients[row], coefficients[row])
    rho = -_sum(_product(coefficients[j], pi[j]) for j in sorted(graph.row_names))
    _close(result.reduced_cost, rho)
    if result.is_improving is not (rho < -tolerance) or (
        (_number(result.reduced_cost) < -tolerance) != (rho < -tolerance)
    ):
        raise _NumericalFailure('Pricing improvement classification differs from reconstruction.')
    return tuple(result.arc_ids), coefficients, rho


def _check_snapshot(problem, columns, artificial, snapshot):
    rows = {row.name: row for row in problem.rows}
    if (set(snapshot.primal_values) != set(columns)
        or set(snapshot.reduced_costs) != set(columns) or set(snapshot.dual_values) != set(rows)):
        raise _NumericalFailure('RMP coordinates differ from the attempted column/row set.')
    x = {name: _number(value) for name, value in snapshot.primal_values.items()}
    pi = {name: _number(value) for name, value in snapshot.dual_values.items()}
    if any(value < -DEFAULT_TOLERANCE for value in x.values()):
        raise _NumericalFailure('RMP violates nonnegative weights.')
    for row in problem.rows:
        activity = _sum(_product(a[row.name], x[name]) for name, (_, a) in columns.items())
        residual = _sum([activity, -row.rhs])
        if ((row.sense == ConstraintSense.EQ and abs(residual) > DEFAULT_TOLERANCE)
            or (row.sense == ConstraintSense.LE and residual > DEFAULT_TOLERANCE)
            or (row.sense == ConstraintSense.GE and residual < -DEFAULT_TOLERANCE)):
            raise _NumericalFailure('Original row fails the existing absolute feasibility check.')
        if ((row.sense == ConstraintSense.LE and pi[row.name] > DEFAULT_TOLERANCE)
            or (row.sense == ConstraintSense.GE and pi[row.name] < -DEFAULT_TOLERANCE)):
            raise _NumericalFailure('Original row multiplier has an invalid sign.')
    for name, (row, sign) in artificial.items():
        cost, a = columns[name]
        if cost != 1 or a[problem.convexity_row] != 0 or any(
            a[j] != (sign if j == row else 0) for j in rows
        ):
            raise _NumericalFailure('Artificial column metadata is inconsistent.')
        if _sum([1, -_product(sign, pi[row])]) < -DEFAULT_TOLERANCE:
            raise _NumericalFailure('Artificial column dual constraint is violated.')
    for name, (cost, a) in columns.items():
        actual_rc = _sum([cost, -_sum(_product(a[j], pi[j]) for j in sorted(rows))])
        _close(snapshot.reduced_costs[name], actual_rc)
    p = tuple(_product(cost, x[name]) for name, (cost, _) in columns.items())
    d = tuple(_product(row.rhs, pi[row.name]) for row in problem.rows)
    objective, dual = _sum(p), _sum(d)
    _close(snapshot.objective_value, objective)
    return objective, dual, p, d


class _NumericalFailure(ArithmeticError):
    pass


def _finite_input(value):
    try:
        number = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError('Numeric parameter must be finite.') from exc
    if not isfinite(number):
        raise ValueError('Numeric parameter must be finite.')
    return number


def _number(value):
    try:
        return _finite_input(value)
    except ValueError as exc:
        raise _NumericalFailure('Nonfinite or invalid arithmetic in feasibility recovery.') from exc


def _sum(values):
    try:
        return _number(fsum(values))
    except (OverflowError, ValueError) as exc:
        raise _NumericalFailure('Nonfinite sum in feasibility recovery.') from exc


def _product(a, b):
    return _number(a*b)


def _close(reported, actual):
    if abs(_sum([_number(reported), -actual])) > DEFAULT_TOLERANCE:
        raise _NumericalFailure('Reported field differs from reconstructed auxiliary/original data')
