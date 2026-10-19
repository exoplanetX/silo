"""Cold RMP / full-DAG pricing loop for a fixed continuous convexity master.

Bounds are floating-point estimates. TOLERANCE_REACHED retains small negative
prices and is scoped to this graph, row system and tolerance.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from math import fsum, isfinite, ulp
from types import MappingProxyType

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.decomposition.dag_pricing import (
    DagPricingProblem,
    DagPricingResult,
    DagPricingStatus,
    price_dag,
)
from silo.decomposition.restricted_master import RestrictedMasterProblem, RestrictedMasterResult
from silo.lp.base import LPSolver
from silo.utils.numerics import DEFAULT_TOLERANCE


class DagColumnGenerationStatus(str, Enum):
    TOLERANCE_REACHED = 'tolerance_reached'
    ITERATION_LIMIT = 'iteration_limit'
    MASTER_FAILURE = 'master_failure'
    PRICING_FAILURE = 'pricing_failure'
    NUMERICAL_ISSUE = 'numerical_issue'


@dataclass(frozen=True)
class DagMasterRow:
    name: str
    sense: ConstraintSense
    rhs: float

    def __post_init__(self):
        _name(self.name)
        object.__setattr__(self, 'sense', ConstraintSense(self.sense))
        object.__setattr__(self, 'rhs', _finite_input(self.rhs))


@dataclass(frozen=True)
class DagColumnGenerationProblem:
    graph: DagPricingProblem
    rows: tuple[DagMasterRow, ...]
    convexity_row: str
    seed_paths: tuple[tuple[str, ...], ...]
    objective_constant: float = 0.0

    def __post_init__(self):
        if not isinstance(self.graph, DagPricingProblem):
            raise TypeError('graph must be a DagPricingProblem.')
        rows = tuple(self.rows)
        if any(not isinstance(row, DagMasterRow) for row in rows):
            raise TypeError('rows must contain DagMasterRow records.')
        names = [row.name for row in rows]
        if len(set(names)) != len(names) or set(names) != set(self.graph.row_names):
            raise ValueError('Unique master rows must exactly match graph row names.')
        _name(self.convexity_row)
        conv = next((row for row in rows if row.name == self.convexity_row), None)
        if conv is None or conv.sense != ConstraintSense.EQ or conv.rhs != 1:
            raise ValueError('Convexity row must be an equality with RHS exactly one.')
        if self.graph.base_coefficients.get(conv.name, 0) != 1 or any(
            arc.row_coefficients.get(conv.name, 0) != 0 for arc in self.graph.arcs
        ):
            raise ValueError('Convexity coefficients must be exactly base=1 and arc=0.')
        if isinstance(self.seed_paths, str | bytes):
            raise TypeError('seed_paths must contain complete arc-ID sequences.')
        paths = tuple(_path_ids(self.graph, path) for path in self.seed_paths)
        if not paths or len(set(paths)) != len(paths):
            raise ValueError('Seed paths must be nonempty and distinct.')
        object.__setattr__(self, 'rows', rows)
        object.__setattr__(self, 'seed_paths', paths)
        object.__setattr__(self, 'objective_constant', _finite_input(self.objective_constant))


def _registry_copy(paths):
    return MappingProxyType({name: tuple(path) for name, path in paths.items()})


@dataclass(frozen=True)
class DagColumnGenerationIteration:
    """One round's snapshot, with signed published and c0-cancelled gaps.

    objective_gap and roundoff_allowance are appended compatibility fields.
    Failed rounds leave all new numerical evidence fields at None.
    """

    iteration: int
    column_paths: Mapping[str, tuple[str, ...]]
    master_result: RestrictedMasterResult
    pricing_result: DagPricingResult | None = None
    numerical_upper_bound: float | None = None
    dual_objective: float | None = None
    rho: float | None = None
    numerical_lower_bound: float | None = None
    numerical_gap: float | None = None
    accepted_path: tuple[str, ...] | None = None
    objective_gap: float | None = None
    roundoff_allowance: float | None = None

    def __post_init__(self):
        object.__setattr__(self, 'column_paths', _registry_copy(self.column_paths))
        if self.accepted_path is not None:
            object.__setattr__(self, 'accepted_path', tuple(self.accepted_path))


@dataclass(frozen=True)
class DagColumnGenerationResult:
    status: DagColumnGenerationStatus
    iterations: tuple[DagColumnGenerationIteration, ...] = ()
    column_paths: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    column_set_iteration: int | None = None
    last_valid_master: RestrictedMasterResult | None = None
    last_valid_master_iteration: int | None = None
    failure_iteration: int | None = None
    message: str = ''

    def __post_init__(self):
        object.__setattr__(self, 'iterations', tuple(self.iterations))
        object.__setattr__(self, 'column_paths', _registry_copy(self.column_paths))


def solve_dag_column_generation(
    problem: DagColumnGenerationProblem, *, solver: LPSolver | None = None,
    tolerance: float = DEFAULT_TOLERANCE, iteration_limit: int = 100,
) -> DagColumnGenerationResult:
    """Solve at most iteration_limit RMP/pricing rounds, adding one path per round.

    Final registry and last_valid_master belong to the same successful master
    round. A later failed attempt has its own registry in iterations, and no new
    bounds. If the first master fails, only its attempted registry is returned.
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

    paths = {f'path_{i}': path for i, path in enumerate(problem.seed_paths)}
    history = []
    last_master = None
    last_iteration = None
    last_paths = None

    def finish(status, message, failure=None):
        return DagColumnGenerationResult(
            status=status, iterations=history,
            column_paths=last_paths if last_paths is not None else (
                history[-1].column_paths if history else {}),
            column_set_iteration=last_iteration if last_paths is not None else (
                history[-1].iteration if history else None),
            last_valid_master=last_master, last_valid_master_iteration=last_iteration,
            failure_iteration=failure, message=message,
        )

    try:
        columns = {name: _reconstruct(problem.graph, path) for name, path in paths.items()}
    except _NumericalFailure as exc:
        return finish(DagColumnGenerationStatus.NUMERICAL_ISSUE, str(exc), 1)
    model = Model(
        variables=[Variable(name) for name in paths],
        constraints=[Constraint(row.name, {name: data[1][row.name]
                     for name, data in columns.items()}, row.sense, row.rhs)
                     for row in problem.rows],
        objective=Objective({name: data[0] for name, data in columns.items()},
                            OptimizationSense.MINIMIZE, problem.objective_constant),
    )
    master = RestrictedMasterProblem(model)
    for iteration in range(1, iteration_limit + 1):
        snapshot = master.solve(solver)
        pricing = None
        if snapshot.status != SolverStatus.OPTIMAL:
            history.append(DagColumnGenerationIteration(iteration, paths, snapshot))
            return finish(DagColumnGenerationStatus.MASTER_FAILURE,
                          f'RMP round {iteration}: {snapshot.status.value}. {snapshot.message}',
                          iteration)
        try:
            upper, dual, primal_terms, dual_terms = _master_objectives(problem, columns, snapshot)
            last_master, last_iteration, last_paths = snapshot, iteration, dict(paths)
            pricing = price_dag(problem.graph, snapshot.dual_values, tolerance=tolerance)
            if not isinstance(pricing, DagPricingResult):
                raise _NumericalFailure('Pricing returned an invalid result record.')
            if pricing.status != DagPricingStatus.OPTIMAL:
                history.append(DagColumnGenerationIteration(iteration, paths, snapshot, pricing))
                return finish(DagColumnGenerationStatus.PRICING_FAILURE,
                              f'Pricing round {iteration}: {pricing.status}. {pricing.message}',
                              iteration)
            path, cost, coefficients, rho = _check_candidate(
                problem.graph, pricing, snapshot.dual_values, tolerance)
            delta = min(0.0, rho)
            lower = _sum([problem.objective_constant, *dual_terms, delta])
            gap = _sum((upper, -lower))
            objective_gap = _sum([*primal_terms, *(-v for v in dual_terms), -delta])
            absolute_scale = _sum([*(abs(v) for v in primal_terms),
                                   *(abs(v) for v in dual_terms), abs(delta)])
            # Fixed local engineering allowance, excluding the common c0.
            # This is not a bound on LP linear-algebra errors.
            allowance = _product(32, ulp(absolute_scale))
            if objective_gap < 0 and (allowance > tolerance or -objective_gap > allowance):
                raise _NumericalFailure(
                    'Numerical bound inconsistency: negative objective gap exceeds local roundoff '
                    f'rule (g={objective_gap}, eta={allowance}, tolerance={tolerance}).')
            if rho >= -tolerance and objective_gap > tolerance:
                raise _NumericalFailure('Objective gap exceeds tolerance despite pricing tolerance')
            if rho < -tolerance and path in paths.values():
                raise _NumericalFailure('Significantly negative pricing path is already existing.')
        except _NumericalFailure as exc:
            history.append(DagColumnGenerationIteration(iteration, paths, snapshot, pricing))
            return finish(DagColumnGenerationStatus.NUMERICAL_ISSUE, str(exc), iteration)

        accepted = path if rho < -tolerance and iteration < iteration_limit else None
        history.append(DagColumnGenerationIteration(
            iteration, paths, snapshot, pricing, upper, dual, rho, lower, gap, accepted,
            objective_gap=objective_gap, roundoff_allowance=allowance))
        if rho >= -tolerance:
            message = 'Full-DAG price and objective gap meet tolerance.'
            if objective_gap < 0:
                message += (f' Negative objective gap accepted by local roundoff rule '
                            f'(g={objective_gap}, eta={allowance}).')
            return finish(DagColumnGenerationStatus.TOLERANCE_REACHED,
                          message)
        if iteration == iteration_limit:
            return finish(DagColumnGenerationStatus.ITERATION_LIMIT,
                          'Round limit reached; no unsolved new column was appended.')
        name = f'path_{len(paths)}'
        # Use reconstructed original data, never tolerance-close returned fields.
        master.add_column(name=name, cost=cost, row_coefficients=coefficients)
        paths[name], columns[name] = path, (cost, coefficients)
    raise AssertionError('Positive iteration limit must produce a stopping decision.')


def _path_ids(graph, path):
    if isinstance(path, str | bytes):
        raise TypeError('A path must be a sequence of arc IDs.')
    ids = tuple(path)
    if not ids:
        raise ValueError('A complete source-to-sink path must be nonempty.')
    by_id = {arc.arc_id: arc for arc in graph.arcs}
    node = graph.source
    for arc_id in ids:
        _name(arc_id)
        arc = by_id.get(arc_id)
        if arc is None or arc.tail != node:
            raise ValueError('Path contains an unknown or disconnected arc.')
        node = arc.head
    if node != graph.sink:
        raise ValueError('Path must finish at the declared sink.')
    return ids


def _reconstruct(graph, path):
    by_id = {arc.arc_id: arc for arc in graph.arcs}
    arcs = [by_id[arc_id] for arc_id in path]
    return (_sum([graph.base_cost, *(arc.cost for arc in arcs)]),
            {row: _sum([graph.base_coefficients.get(row, 0),
                        *(arc.row_coefficients.get(row, 0) for arc in arcs)])
             for row in graph.row_names})


def _check_candidate(graph, result, duals, tolerance):
    try:
        path = _path_ids(graph, result.arc_ids)
    except (ValueError, TypeError) as exc:
        raise _NumericalFailure(f'Invalid pricing path: {exc}') from exc
    cost, coefficients = _reconstruct(graph, path)
    if set(result.row_coefficients) != set(graph.row_names):
        raise _NumericalFailure('Pricing column has incorrect row coordinates.')
    _close(result.cost, cost)
    for row in graph.row_names:
        _close(result.row_coefficients[row], coefficients[row])
    rho = _sum((cost, -_sum(_product(coefficients[row], duals[row])
                           for row in sorted(graph.row_names))))
    _close(result.reduced_cost, rho)
    if result.is_improving is not (rho < -tolerance) or (
        (_number(result.reduced_cost) < -tolerance) != (rho < -tolerance)
    ):
        raise _NumericalFailure('Pricing improvement classification disagrees with reconstruction.')
    return path, cost, coefficients, rho


def _master_objectives(problem, columns, snapshot):
    if set(snapshot.primal_values) != set(columns) or set(snapshot.dual_values) != {
        row.name for row in problem.rows
    }:
        raise _NumericalFailure('Master coordinates do not match this solved column set.')
    x = {name: _number(value) for name, value in snapshot.primal_values.items()}
    pi = {name: _number(value) for name, value in snapshot.dual_values.items()}
    if any(value < -DEFAULT_TOLERANCE for value in x.values()):
        raise _NumericalFailure('Master primal weight violates nonnegativity.')
    for row in problem.rows:
        activity = _sum(_product(data[1][row.name], x[name]) for name, data in columns.items())
        residual = _sum((activity, -row.rhs))
        if ((row.sense == ConstraintSense.EQ and abs(residual) > DEFAULT_TOLERANCE)
            or (row.sense == ConstraintSense.LE and residual > DEFAULT_TOLERANCE)
            or (row.sense == ConstraintSense.GE and residual < -DEFAULT_TOLERANCE)):
            raise _NumericalFailure('Master primal row fails the existing absolute tolerance.')
        if ((row.sense == ConstraintSense.LE and pi[row.name] > DEFAULT_TOLERANCE)
            or (row.sense == ConstraintSense.GE and pi[row.name] < -DEFAULT_TOLERANCE)):
            raise _NumericalFailure('Master dual row sign is inconsistent.')
    primal_terms = tuple(_product(data[0], x[name]) for name, data in columns.items())
    dual_terms = tuple(_product(row.rhs, pi[row.name]) for row in problem.rows)
    upper = _sum([problem.objective_constant, *primal_terms])
    _close(snapshot.objective_value, upper)
    dual = _sum([problem.objective_constant, *dual_terms])
    return upper, dual, primal_terms, dual_terms


class _NumericalFailure(ArithmeticError):
    pass


def _finite_input(value):
    try:
        result = float(value)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('Numeric input must be finite.') from exc
    if not isfinite(result):
        raise ValueError('Numeric input must be finite.')
    return result


def _number(value):
    try:
        return _finite_input(value)
    except ValueError as exc:
        raise _NumericalFailure('Nonfinite or invalid numeric result.') from exc


def _sum(values):
    try:
        return _number(fsum(values))
    except (OverflowError, ValueError) as exc:
        raise _NumericalFailure('Nonfinite arithmetic while reconstructing CG data.') from exc


def _product(a, b):
    return _number(a * b)


def _close(reported, actual):
    if abs(_sum((_number(reported), -actual))) > DEFAULT_TOLERANCE:
        raise _NumericalFailure('Reported numeric field disagrees with reconstructed data.')


def _name(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError('IDs must be nonblank strings with exact spelling.')
