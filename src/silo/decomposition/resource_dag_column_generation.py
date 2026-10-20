"""Resource-feasible path convex-combination CG, with cold pricing each round.

The single convexity row is essential to the inherited dual-shift bounds. This
reference model does not implement real multi-route covering or VRPTW.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import ulp

from silo.core.constraint import Constraint
from silo.core.enums import OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.decomposition.dag_column_generation import (
    DagColumnGenerationProblem,
    DagColumnGenerationStatus,
    _check_candidate,
    _finite_input,
    _master_objectives,
    _NumericalFailure,
    _product,
    _reconstruct,
    _registry_copy,
    _sum,
)
from silo.decomposition.resource_dag_pricing import (
    ResourceDagPricingProblem,
    ResourceDagPricingResult,
    ResourceDagPricingStatus,
    price_resource_dag,
)
from silo.decomposition.restricted_master import (
    RestrictedMasterProblem,
    RestrictedMasterReoptimizationResult,
    RestrictedMasterResult,
)
from silo.lp.base import LPSolver
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.utils.numerics import DEFAULT_TOLERANCE


@dataclass(frozen=True)
class ResourceDagColumnGenerationIteration:
    """One round's snapshot, with signed published and c0-cancelled gaps.

    objective_gap and roundoff_allowance are appended compatibility fields.
    Failed rounds leave all new numerical evidence fields at None.
    Opt-in rounds retain the actual public RMP reoptimization outcome.
    """

    iteration: int
    column_paths: Mapping[str, tuple[str, ...]]
    master_result: RestrictedMasterResult
    pricing_result: ResourceDagPricingResult | None = None
    numerical_upper_bound: float | None = None
    dual_objective: float | None = None
    rho: float | None = None
    numerical_lower_bound: float | None = None
    numerical_gap: float | None = None
    accepted_path: tuple[str, ...] | None = None
    objective_gap: float | None = None
    roundoff_allowance: float | None = None
    rmp_reoptimization: RestrictedMasterReoptimizationResult | None = None

    def __post_init__(self):
        object.__setattr__(self, 'column_paths', _registry_copy(self.column_paths))
        if self.accepted_path is not None:
            object.__setattr__(self, 'accepted_path', tuple(self.accepted_path))


@dataclass(frozen=True)
class ResourceDagColumnGenerationResult:
    status: DagColumnGenerationStatus
    iterations: tuple[ResourceDagColumnGenerationIteration, ...] = ()
    column_paths: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    column_set_iteration: int | None = None
    last_valid_master: RestrictedMasterResult | None = None
    last_valid_master_iteration: int | None = None
    failure_iteration: int | None = None
    message: str = ''

    def __post_init__(self):
        object.__setattr__(self, 'iterations', tuple(self.iterations))
        object.__setattr__(self, 'column_paths', _registry_copy(self.column_paths))


def solve_resource_dag_column_generation(
    problem: DagColumnGenerationProblem, resources: ResourceDagPricingProblem, *,
    solver: LPSolver | None = None,
    tolerance: float = DEFAULT_TOLERANCE, iteration_limit: int = 100,
    reoptimize_rmp: bool = False,
    pricing_state_limit: int = 100000, pricing_transition_limit: int = 1000000,
) -> ResourceDagColumnGenerationResult:
    """Solve at most iteration_limit RMP/pricing rounds, adding one path per round.

    Final registry and last_valid_master belong to the same successful master
    round. A later failed attempt has its own registry in iterations, and no new
    bounds. If the first master fails, only its attempted registry is returned.
    reoptimize_rmp=True consumes one public opt-in RMP result per round; any
    internal cold fallback belongs to the RMP, within the same CG round.
    """
    if not isinstance(problem, DagColumnGenerationProblem):
        raise TypeError('problem must be a DagColumnGenerationProblem.')
    if not isinstance(resources, ResourceDagPricingProblem):
        raise TypeError('resources must be a ResourceDagPricingProblem.')
    if resources.graph is not problem.graph:
        raise ValueError('resources.graph must be the same object as problem.graph.')
    if type(reoptimize_rmp) is not bool:
        raise TypeError('reoptimize_rmp must be a bool.')
    if reoptimize_rmp and solver is not None and not isinstance(solver, RevisedSimplexSolver):
        raise TypeError('RMP reoptimization requires a native RevisedSimplexSolver.')
    tolerance = _finite_input(tolerance)
    if tolerance <= 0:
        raise ValueError('tolerance must be positive.')
    if not isinstance(iteration_limit, int) or isinstance(iteration_limit, bool):
        raise TypeError('iteration_limit must be an integer.')
    if iteration_limit <= 0:
        raise ValueError('iteration_limit must be positive.')

    for name, value in (("pricing_state_limit", pricing_state_limit),
                        ("pricing_transition_limit", pricing_transition_limit)):
        if type(value) is not int:
            raise TypeError(f'{name} must be a strict positive integer.')
        if value <= 0:
            raise ValueError(f'{name} must be positive.')
    # All seed resource checks precede numeric reconstruction and any solver call.
    for seed in problem.seed_paths:
        _resource_usage(resources, seed)

    paths = {f'path_{i}': path for i, path in enumerate(problem.seed_paths)}
    history = []
    last_master = None
    last_iteration = None
    last_paths = None

    def finish(status, message, failure=None):
        return ResourceDagColumnGenerationResult(
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
        if reoptimize_rmp:
            outcome = master.solve_reoptimized(solver)
            snapshot = outcome.result
        else:
            outcome = None
            snapshot = master.solve(solver)
        pricing = None
        if snapshot.status != SolverStatus.OPTIMAL:
            history.append(ResourceDagColumnGenerationIteration(
                iteration, paths, snapshot, rmp_reoptimization=outcome))
            return finish(DagColumnGenerationStatus.MASTER_FAILURE,
                          f'RMP round {iteration}: {snapshot.status.value}. {snapshot.message}',
                          iteration)
        try:
            upper, dual, primal_terms, dual_terms = _master_objectives(problem, columns, snapshot)
            last_master, last_iteration, last_paths = snapshot, iteration, dict(paths)
            pricing = price_resource_dag(
                resources, snapshot.dual_values, tolerance=tolerance,
                state_limit=pricing_state_limit, transition_limit=pricing_transition_limit,
            )
            if not isinstance(pricing, ResourceDagPricingResult) or not isinstance(
                pricing.status, ResourceDagPricingStatus,
            ):
                pricing = None  # Keep the typed history free of invalid oracle records.
                raise _NumericalFailure('Pricing returned an invalid result record.')
            if pricing.status != ResourceDagPricingStatus.OPTIMAL:
                history.append(ResourceDagColumnGenerationIteration(
                    iteration, paths, snapshot, pricing, rmp_reoptimization=outcome))
                return finish(DagColumnGenerationStatus.PRICING_FAILURE,
                              f'Pricing round {iteration}: {pricing.status}. {pricing.message}',
                              iteration)
            path, cost, coefficients, rho = _check_candidate(
                problem.graph, pricing, snapshot.dual_values, tolerance)
            _check_resource_candidate(resources, path, pricing.resource_usage)
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
            history.append(ResourceDagColumnGenerationIteration(
                iteration, paths, snapshot, pricing, rmp_reoptimization=outcome))
            return finish(DagColumnGenerationStatus.NUMERICAL_ISSUE, str(exc), iteration)

        accepted = path if rho < -tolerance and iteration < iteration_limit else None
        history.append(ResourceDagColumnGenerationIteration(
            iteration, paths, snapshot, pricing, upper, dual, rho, lower, gap, accepted,
            objective_gap=objective_gap, roundoff_allowance=allowance,
            rmp_reoptimization=outcome))
        if rho >= -tolerance:
            message = 'Full resource-domain price and objective gap meet tolerance.'
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


def _resource_usage(resources, path):
    # Independent of the pricing DP: accumulate original resource inputs anew.
    usage = [0] * len(resources.resource_limits)
    for arc_id in path:
        for index, increment in enumerate(resources.arc_resources[arc_id]):
            usage[index] += increment
            if usage[index] > resources.resource_limits[index]:
                raise ValueError('Path exceeds a resource limit.')
    return tuple(usage)


def _check_resource_candidate(resources, path, reported):
    if not isinstance(reported, tuple) or len(reported) != len(resources.resource_limits):
        raise _NumericalFailure('Pricing resource usage has an invalid tuple dimension.')
    if any(type(value) is not int or value < 0 for value in reported):
        raise _NumericalFailure('Pricing resource usage must contain strict nonnegative integers.')
    try:
        usage = _resource_usage(resources, path)
    except ValueError as exc:
        raise _NumericalFailure(f'Invalid pricing resource path: {exc}') from exc
    if usage != reported:
        raise _NumericalFailure('Pricing resources disagree with independent path reconstruction.')
