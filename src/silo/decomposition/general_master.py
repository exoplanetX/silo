"""General nonnegative-column masters and finite-pool column generation.

The master is ``min c0 + sum(c_j * lambda_j)`` with ``lambda >= 0`` and
the caller's original row intervals. No convex-combination row is inserted.
Pricing uses ``c_j - a_j.T @ dual`` in the public minimization convention.
``FiniteColumnPricer`` enumerates a declared, immutable complete pool; arbitrary
pricers are heuristic, even when they claim completeness. Reduced-cost sums are
evaluated with Fraction(actual_binary_value). Any strictly negative finite-pool
reduced cost adds a column. Optimality requires an exact original-data primal/dual
pair over every pool column; infeasibility needs an exact binary-data Farkas check.

CG always begins with one cost-one artificial per finite row side: +1 for a
lower side and -1 for an upper side. Original columns have auxiliary cost zero.
At a feasible zero auxiliary optimum the artificial columns are discarded and
the original objective is solved in a fresh public LPSession. Within each phase
append_column preserves the session basis; actual reuse/fallback is in trace.
The 20-round cap counts *all* auxiliary and original-objective LP solves.
"""

import hashlib
import json
from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import asdict, dataclass, field, replace
from fractions import Fraction
from math import fsum, inf, isfinite, nextafter
from numbers import Integral, Real
from time import perf_counter
from types import MappingProxyType
from typing import Protocol

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.solve_types import SolveOptions, SolveResult
from silo.core.variable import Variable
from silo.lp.session import LPSession
from silo.utils.rational import ProofBudget, ProofLimitError


def _name(value, what):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{what} must be a nonempty string.")
    return value


def _number(value, what):
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{what} must be a finite real number.")
    try:
        converted = float(value)
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{what} must be finite and float64 representable.") from exc
    if not isfinite(converted):
        raise ValueError(f"{what} must be finite.")
    if isinstance(value, Integral) and int(converted) != value:
        raise ValueError(f"{what} loses integer precision in float64.")
    return converted


def _frozen_mapping(values):
    return MappingProxyType(dict(values))


@dataclass(frozen=True)
class MasterColumn:
    """A continuous variable with bounds [0, infinity), cost and sparse column."""

    name: str
    cost: float
    row_coefficients: Mapping[str, float] = field(default_factory=dict)

    def __post_init__(self):
        _name(self.name, "Column name")
        object.__setattr__(self, "cost", _number(self.cost, "Column cost"))
        if not isinstance(self.row_coefficients, Mapping):
            raise ValueError("row_coefficients must be a mapping.")
        coefficients = {
            _name(name, "Row name"): _number(value, "Column coefficient")
            for name, value in self.row_coefficients.items()
        }
        object.__setattr__(self, "row_coefficients", _frozen_mapping(coefficients))


class GeneralRestrictedMaster:
    """An owned general-row LP master, reoptimized through public LPSession.

    Columns must be continuous and nonnegative with no finite upper bound.
    Objectives are minimization; constants and all valid original row intervals
    are retained. ``model`` and ``history`` return independent snapshots.
    ``solve(options)`` overrides options for that call without resetting basis.
    """

    def __init__(self, model: Model, options: SolveOptions | None = None):
        if not isinstance(model, Model):
            raise TypeError("A general restricted master requires a Model.")
        model = deepcopy(model)
        model.validate()
        if model.objective.sense != OptimizationSense.MINIMIZE:
            raise ValueError("A general restricted master requires minimization.")
        for variable in model.variables:
            _name(variable.name, "Column name")
            if variable.var_type != VariableType.CONTINUOUS:
                raise ValueError("Master columns must be continuous.")
            if variable.bounds.lower != 0 or variable.bounds.upper != inf:
                raise ValueError("Master columns require bounds [0, infinity).")
        _number(model.objective.constant, "Objective constant")
        for value in model.objective.coefficients.values():
            _number(value, "Objective coefficient")
        for row in model.constraints:
            _name(row.name, "Row name")
            _number(row.rhs, "Legacy row RHS")
            lower, upper = row.row_bounds
            if lower != -inf:
                _number(lower, "Row lower bound")
            if upper != inf:
                _number(upper, "Row upper bound")
            for value in row.coefficients.values():
                _number(value, "Row coefficient")
        self.options = SolveOptions() if options is None else options
        if not isinstance(self.options, SolveOptions):
            raise TypeError("options must be SolveOptions.")
        self._session = LPSession(model, self.options)

    @property
    def model(self):
        return self._session.model

    @property
    def basis(self):
        return self._session.basis

    @property
    def history(self):
        return tuple(deepcopy(self._session.history))

    def add_column(self, name: str, cost: float, row_coefficients: Mapping[str, float]):
        """Atomically append a column, retaining the previous public basis."""
        column = MasterColumn(name, cost, row_coefficients)
        rows = {row.name for row in self.model.constraints}
        if set(column.row_coefficients) - rows:
            raise ValueError("Unknown row in appended column.")
        self._session.append_column(
            Variable(column.name), dict(column.row_coefficients), column.cost
        )

    def solve(self, options: SolveOptions | None = None) -> SolveResult:
        selected = self.options if options is None else options
        if not isinstance(selected, SolveOptions):
            raise TypeError("options must be SolveOptions.")
        self._session.options = selected
        return self._session.solve()


@dataclass(frozen=True)
class PricingContext:
    """Owned row duals and shared remaining wall budget for one pricing call."""

    phase: str
    dual_values: Mapping[str, float]
    existing_columns: tuple[str, ...]
    dual_tolerance: float
    remaining_seconds: float

    def __post_init__(self):
        if self.phase not in ("phase1", "phase2"):
            raise ValueError("Unknown pricing phase.")
        duals = {_name(k, "Row name"): _number(v, "Row dual") for k, v in self.dual_values.items()}
        object.__setattr__(self, "dual_values", _frozen_mapping(duals))
        if _number(self.dual_tolerance, "Dual tolerance") <= 0:
            raise ValueError("Dual tolerance must be positive.")
        object.__setattr__(self, "existing_columns", tuple(self.existing_columns))

    def _score(self, column, budget=None):
        if budget is not None:
            budget.charge()
        unknown = set(column.row_coefficients) - set(self.dual_values)
        if unknown:
            raise ValueError(f"Unknown pricing rows: {sorted(unknown)}")
        guard = (lambda value: value) if budget is None else budget.guard
        terms = [
            guard(guard(Fraction(value)) * guard(Fraction(self.dual_values[name])))
            for name, value in column.row_coefficients.items()
        ]
        cost = guard(Fraction(0 if self.phase == "phase1" else column.cost))
        reduced = cost
        for term in terms:
            reduced = guard(reduced - term)
        threshold = Fraction(self.dual_tolerance) * (1 + abs(cost) + sum(map(abs, terms)))
        return reduced, threshold

    def reduced_cost(self, column: MasterColumn) -> float:
        return float(self._score(column)[0])


@dataclass(frozen=True)
class PricingResult:
    """Proposed columns. A user-supplied complete flag is informational only."""

    columns: tuple[MasterColumn, ...] = ()
    complete: bool = False

    def __post_init__(self):
        columns = tuple(self.columns)
        if not all(isinstance(column, MasterColumn) for column in columns):
            raise TypeError("Pricing must return MasterColumn objects.")
        if len({column.name for column in columns}) != len(columns):
            raise ValueError("Pricing returned duplicate column names.")
        object.__setattr__(self, "columns", columns)


class ColumnPricer(Protocol):
    def price(self, context: PricingContext) -> PricingResult: ...


class _PricingCallbackError(Exception):
    pass


def _heuristic_price(pricer, context):
    try:
        return pricer.price(context)
    except Exception as exc:
        raise _PricingCallbackError(f"{type(exc).__name__}: {exc}") from exc


@dataclass(frozen=True)
class FiniteColumnPricer:
    """Exact enumeration over a complete finite pool, including initial columns.

    Every initial column must occur identically in this pool. At each call all
    pool reduced costs are examined and the best improving unused column is
    proposed, with deterministic pool-order ties. The CG driver independently
    runs this enumeration; overriding price or claiming complete cannot certify
    another oracle. Completeness concerns this pool, not an implicit larger one.
    """

    columns: tuple[MasterColumn, ...]

    def __init__(self, columns: Sequence[MasterColumn]):
        columns = tuple(columns)
        if not all(type(column) is MasterColumn for column in columns):
            raise TypeError("A finite pool must contain MasterColumn objects.")
        if len({column.name for column in columns}) != len(columns):
            raise ValueError("A finite pool must have unique column names.")
        object.__setattr__(self, "columns", columns)

    def price(self, context: PricingContext) -> PricingResult:
        proposal, _ = _finite_price(self.columns, context)
        return proposal


def _finite_price(pool, context, deadline=inf, budget=None):
    scores, improving = {}, []
    for index, column in enumerate(pool):
        if perf_counter() >= deadline:
            return None, scores
        score, _threshold = context._score(column, budget)
        scores[column.name] = float(score)
        if score < 0 and column.name not in context.existing_columns:
            improving.append((score, index, column))
    best = (min(improving, key=lambda item: item[:2])[2],) if improving else ()
    return PricingResult(best, complete=True), scores


def _verify_pool(pool, model):
    rows = {row.name for row in model.constraints}
    by_name = {column.name: column for column in pool}
    for column in pool:
        if set(column.row_coefficients) - rows:
            raise ValueError("Finite pool contains unknown rows.")
    for name in model.variable_names():
        column = by_name.get(name)
        if column is None:
            raise ValueError("Finite pool must include every initial column.")
        if column.cost != model.objective.coefficients.get(name, 0):
            raise ValueError(f"Finite pool cost differs from initial column: {name}")
        if any(
            column.row_coefficients.get(row.name, 0) != row.coefficients.get(name, 0)
            for row in model.constraints
        ):
            raise ValueError(f"Finite pool vector differs from initial column: {name}")


def _auxiliary(model, reserved_names):
    variables = list(model.variables)
    rows, sides, artificial = [], {}, []
    used = set(reserved_names) | set(model.variable_names())
    for index, row in enumerate(model.constraints):
        lower, upper = row.row_bounds
        for side, bound, coefficient, sense in (
            ("lower", lower, 1, ConstraintSense.GE),
            ("upper", upper, -1, ConstraintSense.LE),
        ):
            if not isfinite(bound):
                continue
            name = f"__cg_art_{index}_{side}"
            while name in used:
                name += "_"
            used.add(name)
            variables.append(Variable(name))
            artificial.append(name)
            side_name = f"__cg_row_{index}_{side}"
            coefficients = {**row.coefficients, name: coefficient}
            rows.append(Constraint(side_name, coefficients, sense, bound))
            sides[side_name] = (row.name, side, bound)
    auxiliary = Model(
        name=f"{model.name}_phase1",
        variables=variables,
        constraints=rows,
        objective=Objective(dict.fromkeys(artificial, 1.0)),
    )
    return auxiliary, sides, tuple(artificial)


def _phase1_duals(model, sides, result):
    return {
        row.name: fsum(
            result.dual_values[side_name]
            for side_name, (original, _, _) in sides.items()
            if original == row.name
        )
        for row in model.constraints
    }


def _phase1_certificate(pool, sides, result, budget=None):
    """A^T d <= 0 and b^T d > 0 exactly imply infeasibility for lambda>=0."""
    budget = ProofBudget() if budget is None else budget
    dual = {name: budget.guard(Fraction(result.dual_values[name])) for name in sides}
    if any(
        (dual[name] < 0 if side == "lower" else dual[name] > 0)
        for name, (_, side, _) in sides.items()
    ):
        return None
    separation = Fraction(0)
    for name, (_, _, bound) in sides.items():
        separation = budget.guard(separation + budget.guard(Fraction(bound) * dual[name]))
    products = {}
    for column in pool:
        value = Fraction(0)
        for name, (original, _, _) in sides.items():
            value = budget.guard(
                value
                + budget.guard(Fraction(column.row_coefficients.get(original, 0)) * dual[name])
            )
        products[column.name] = value
    if separation <= 0 or any(value > 0 for value in products.values()):
        return None
    return {
        "kind": "finite_pool_farkas",
        "rational_convention": "Fraction(actual_binary_value)",
        "side_multipliers": {
            name: {"row": original, "side": side, "signed_dual": str(dual[name])}
            for name, (original, side, _) in sides.items()
        },
        "separation": str(separation),
        "column_products": {name: str(value) for name, value in products.items()},
    }


def _projected_point(model, result, options):
    if result is None or not result.has_primal_solution:
        return None, {}
    values = {name: result.primal_values.get(name, 0.0) for name in model.variable_names()}
    if any(not isfinite(value) or value < -options.primal_tolerance for value in values.values()):
        return None, {}
    for row in model.constraints:
        terms = [value * values[name] for name, value in row.coefficients.items()]
        activity = fsum(terms)
        lower, upper = row.row_bounds
        tolerance = options.primal_tolerance * (1 + fsum(map(abs, terms)))
        if not isfinite(activity) or activity < lower - tolerance or activity > upper + tolerance:
            return None, {}
    objective = model.objective.constant + fsum(
        coefficient * values[name] for name, coefficient in model.objective.coefficients.items()
    )
    return (objective, values) if isfinite(objective) else (None, {})


def _full_pool_certificate(model, pool, result, options, budget):
    """Prove original-binary full-pool optimality by an exact feasible pair.

    Float and rational reconstructions propose candidates only. Every original
    row, side sign, pool column and P=D is checked; tolerances grant no proof.
    """
    from silo.lp.tableau_view import exact_basis_candidates

    budget.charge()
    q = budget.guard
    names = tuple(column.name for column in pool)

    def verify_pair(candidate):
        if candidate is None:
            return None
        point, duals = candidate
        values = {name: q(point.get(name, Fraction(0))) for name in names}
        if any(value < 0 for value in values.values()):
            return None
        primal = q(Fraction(model.objective.constant))
        dual = primal
        for column in pool:
            primal = q(primal + q(Fraction(column.cost) * values[column.name]))
        for row in model.constraints:
            activity = Fraction(0)
            for column in pool:
                activity = q(
                    activity
                    + q(Fraction(column.row_coefficients.get(row.name, 0)) * values[column.name])
                )
            lower, upper = row.row_bounds
            if (isfinite(lower) and activity < Fraction(lower)) or (
                isfinite(upper) and activity > Fraction(upper)
            ):
                return None
            pi = q(duals.get(row.name, Fraction(0)))
            bound = lower if pi >= 0 else upper
            if pi and not isfinite(bound):
                return None
            if pi:
                dual = q(dual + q(pi * Fraction(bound)))
        reduced = {}
        for column in pool:
            value = q(Fraction(column.cost))
            for name, coefficient in column.row_coefficients.items():
                value = q(value - q(Fraction(coefficient) * duals.get(name, Fraction(0))))
            if value < 0:
                return None
            reduced[column.name] = value
        if primal != dual:
            return None
        proof = {
            "kind": "finite_pool_optimality",
            "rational_convention": "Fraction(actual_binary_value)",
            "point": {name: str(q(value)) for name, value in values.items()},
            "row_duals": {
                row.name: str(q(duals.get(row.name, Fraction(0)))) for row in model.constraints
            },
            "reduced_costs": {name: str(q(value)) for name, value in reduced.items()},
            "primal_objective": str(primal),
            "dual_objective": str(dual),
            "exact_gap": "0",
            "all_pool_columns_checked": len(pool),
        }
        budget.charge()
        return proof

    raw = {name: q(Fraction(value)) for name, value in result.primal_values.items()}
    raw_dual = {name: q(Fraction(value)) for name, value in result.dual_values.items()}
    proof = verify_pair((raw, raw_dual))
    if proof is None:
        proof = verify_pair(
            (
                {name: q(value.limit_denominator(100_000_000)) for name, value in raw.items()},
                {name: q(value.limit_denominator(100_000_000)) for name, value in raw_dual.items()},
            )
        )
    if proof is None:
        proof = verify_pair(exact_basis_candidates(result, budget))
    budget.charge()
    return proof


def _refined_dual_tolerance(context, pool, result, current, budget):
    """A witnessed existing-column violation requests stricter LP work, never looser."""
    if result._lp is None:
        return None
    norm = result._lp[0]
    scales = {
        norm.data.names[i]: abs(Fraction(float(scale)))
        for (i, _), scale in zip(norm.column_origins, norm.col_scale, strict=True)
    }
    negative = []
    for column in pool:
        score, _ = context._score(column, budget)
        if score < 0 and column.name in context.existing_columns and column.name in scales:
            negative.append(budget.guard(-score * scales[column.name]))
    if not negative:
        return None
    cost_scale = 1 + max((abs(Fraction(float(cost))) for cost in norm.costs), default=0)
    target = float(budget.guard(min(negative) / (8 * cost_scale)))
    return target if 0 < target < current else None


@dataclass(frozen=True)
class ColumnGenerationStep:
    iteration: int
    phase: str
    status: str
    objective: float | None
    restricted_primal_bound: float | None
    restricted_dual_bound: float | None
    column_names: tuple[str, ...]
    added_columns: tuple[str, ...]
    dual_values: Mapping[str, float]
    pricing_reduced_costs: Mapping[str, float]
    pricing_complete: bool
    basis_available: bool
    basis_reused: bool
    lp_iterations: int
    elapsed_seconds: float
    termination_reason: str
    lp_diagnostics: dict

    def __post_init__(self):
        for name in ("dual_values", "pricing_reduced_costs"):
            object.__setattr__(self, name, _frozen_mapping(getattr(self, name)))

    def to_dict(self):
        return {
            **{
                name: value
                for name, value in vars(self).items()
                if name not in ("dual_values", "pricing_reduced_costs")
            },
            "dual_values": dict(self.dual_values),
            "pricing_reduced_costs": dict(self.pricing_reduced_costs),
        }


@dataclass(frozen=True)
class ColumnGenerationResult:
    """Current restricted-master duals are omitted after an unsolved addition.

    A full-pool dual bound is published only at complete finite-pool optimality.
    The trace retains each solved model's column identities and original duals.
    """

    status: str
    termination_reason: str
    objective_value: float | None
    primal_values: Mapping[str, float]
    dual_values: Mapping[str, float]
    phase1_objective: float | None
    iterations: int
    lp_iterations: int
    elapsed_seconds: float
    pricing_complete: bool
    pool_size: int | None
    trace: tuple[ColumnGenerationStep, ...]
    witness: dict | None
    parameters: dict
    input_identity: str | None = None
    input_sha256: str | None = None
    input_payload: dict | None = None

    def __post_init__(self):
        for name in ("primal_values", "dual_values"):
            object.__setattr__(self, name, _frozen_mapping(getattr(self, name)))

    @property
    def has_primal_solution(self):
        return self.objective_value is not None

    @property
    def primal_bound(self):
        if self.status == "optimal" and self.witness is not None:
            exact = Fraction(self.witness["primal_objective"])
            value = float(exact)
            return nextafter(value, inf) if Fraction(value) < exact else value
        return self.objective_value

    @property
    def dual_bound(self):
        if self.status == "optimal":
            if self.witness is None or self.witness.get("kind") != "finite_pool_optimality":
                return None
            exact = Fraction(self.witness["dual_objective"])
            value = float(exact)
            return nextafter(value, -inf) if Fraction(value) > exact else value
        return -inf if self.status == "unbounded" else None

    def to_dict(self):
        data = {
            **{
                name: value
                for name, value in vars(self).items()
                if name not in ("primal_values", "dual_values", "trace")
            },
            "primal_values": dict(self.primal_values),
            "dual_values": dict(self.dual_values),
            "trace": [step.to_dict() for step in self.trace],
            "has_primal_solution": self.has_primal_solution,
            "primal_bound": self.primal_bound,
            "dual_bound": self.dual_bound,
            "dual_bound_is_infinite": self.dual_bound == -inf,
        }
        return _json_numbers(data)


def _json_numbers(value):
    if isinstance(value, dict):
        return {name: _json_numbers(item) for name, item in value.items()}
    if isinstance(value, list | tuple):
        return [_json_numbers(item) for item in value]
    return None if isinstance(value, float) and not isfinite(value) else value


def column_generation(
    master: GeneralRestrictedMaster,
    pricer: ColumnPricer,
    *,
    max_iterations: int = 20,
    options: SolveOptions | None = None,
) -> ColumnGenerationResult:
    """Mutate an owned master by adding priced columns, within shared budgets.

    ``max_iterations`` is in [0, 20]. Both time and LP pivots are shared across
    phases and rounds. Heuristic pricing is cooperative: it receives remaining
    time, and an over-budget response is rejected before any column is added.
    Ordinary callback exceptions become pricing_error with trace and incumbent;
    process-control BaseExceptions propagate to the caller.
    """
    if not isinstance(master, GeneralRestrictedMaster):
        raise TypeError("master must be GeneralRestrictedMaster.")
    if type(max_iterations) is not int or not 0 <= max_iterations <= 20:
        raise ValueError("max_iterations must be an integer in [0, 20].")
    options = master.options if options is None else options
    if not isinstance(options, SolveOptions):
        raise TypeError("options must be SolveOptions.")
    if not callable(getattr(pricer, "price", None)):
        raise TypeError("pricer must provide price(PricingContext).")
    started = perf_counter()
    deadline = started + options.time_limit
    finite = type(pricer) is FiniteColumnPricer
    pool = pricer.columns if finite else ()
    original = master.model
    if finite:
        _verify_pool(pool, original)
    auxiliary, sides, artificial = _auxiliary(original, [column.name for column in pool])
    phase_master = GeneralRestrictedMaster(auxiliary, options)
    phase, phase1_objective = "phase1", None
    trace, total_pivots = [], 0
    last, last_original, certificate = None, None, None
    last_original_columns = None
    incumbent = None
    proof_budget = ProofBudget(options.proof_operation_limit, deadline, clock=perf_counter)
    work_dual_tolerance = options.dual_tolerance
    proof_without_presolve = False

    def finish(status, reason, complete=False):
        objective, point = (
            (None, {})
            if status == "infeasible"
            else _projected_point(master.model, last_original, options)
        )
        if status == "optimal" and certificate is not None:
            objective = float(Fraction(certificate["primal_objective"]))
            point = {
                name: float(Fraction(certificate["point"][name]))
                for name in master.model.variable_names()
            }
        if objective is None and status != "infeasible":
            objective, point = _projected_point(master.model, incumbent, options)
        return ColumnGenerationResult(
            status,
            reason,
            objective,
            point,
            {name: float(Fraction(value)) for name, value in certificate["row_duals"].items()}
            if status == "optimal" and certificate is not None
            else last_original.dual_values
            if last_original is not None
            and last_original_columns == tuple(master.model.variable_names())
            else {},
            phase1_objective,
            len(trace),
            total_pivots,
            perf_counter() - started,
            complete,
            len(pool) if finite else None,
            tuple(trace),
            certificate
            if certificate is not None
            else (last_original.witness if last_original is not None else None),
            {**asdict(options), "max_iterations": max_iterations},
        )

    for iteration in range(1, max_iterations + 1):
        remaining = deadline - perf_counter()
        if remaining <= 0:
            return finish("limit", "time_limit")
        if total_pivots >= options.lp_iteration_limit:
            return finish("limit", "lp_iteration_limit")
        round_started = perf_counter()
        column_names = tuple(phase_master.model.variable_names())
        last = phase_master.solve(
            replace(
                options,
                time_limit=remaining,
                lp_iteration_limit=options.lp_iteration_limit - total_pivots,
                dual_tolerance=work_dual_tolerance,
                presolve=options.presolve and not proof_without_presolve,
            )
        )
        total_pivots += last.iterations
        if phase == "phase2":
            last_original = last
            last_original_columns = column_names
            if _projected_point(master.model, last, options)[0] is not None:
                incumbent = last
        duals, scores, added, complete = {}, {}, (), False
        status, reason = last.status, last.termination_reason
        terminal = None
        if last.status != "optimal":
            terminal = (last.status, last.termination_reason)
            if last.status in ("infeasible", "unbounded") and phase == "phase1":
                terminal = ("numerical_failure", "phase1_auxiliary_failure")
            if last.status == "infeasible" and phase == "phase2":
                terminal = ("numerical_failure", "phase1_cleanup_failed")
        elif phase == "phase1":
            phase1_objective = last.objective_value
            duals = _phase1_duals(master.model, sides, last)
            objective, _ = _projected_point(master.model, last, options)
            if abs(phase1_objective) <= options.primal_tolerance and objective is not None:
                # No artificial variable is transferred to the original model.
                last_original = replace(last, dual_values={}, witness=None)
                incumbent = last_original
                reason = "phase1_feasible_remove_artificials"
            else:
                reason = "price_columns"
        else:
            duals = dict(last.dual_values)
            reason = "price_columns"

        if terminal is None and reason == "price_columns":
            context = PricingContext(
                phase,
                duals,
                tuple(master.model.variable_names()),
                options.dual_tolerance,
                max(0, deadline - perf_counter()),
            )
            try:
                if finite:
                    proposal, scores = _finite_price(pool, context, deadline, proof_budget)
                    complete = proposal is not None
                else:
                    proposal = _heuristic_price(pricer, context)
                    if not isinstance(proposal, PricingResult):
                        raise TypeError("A pricer must return PricingResult.")
                    scores = {c.name: context.reduced_cost(c) for c in proposal.columns}
                if perf_counter() >= deadline or proposal is None:
                    terminal = ("limit", "time_limit")
                else:
                    for column in proposal.columns:
                        _verify_proposal(column, master.model)
                        if phase == "phase1" and column.name in artificial:
                            raise ValueError("Pricing column collides with an artificial name.")
                    # Finite enumeration has already selected its single best
                    # unused strict-negative candidate under this proof budget.
                    candidates = (
                        proposal.columns
                        if finite
                        else [
                            column
                            for column in proposal.columns
                            if column.name not in context.existing_columns
                            and context._score(column)[0] < -context._score(column)[1]
                        ]
                    )
                    if candidates:
                        column = (
                            candidates[0] if finite else min(candidates, key=context.reduced_cost)
                        )
                        master.add_column(column.name, column.cost, column.row_coefficients)
                        if phase == "phase1":
                            coefficients = {
                                side_name: column.row_coefficients.get(original_name, 0)
                                for side_name, (original_name, _, _) in sides.items()
                            }
                            phase_master.add_column(column.name, 0, coefficients)
                        added, reason = (column.name,), "column_added"
                    elif not complete:
                        terminal = ("limit", "incomplete_pricing")
                    elif phase == "phase2":
                        certificate = _full_pool_certificate(
                            master.model, pool, last, options, proof_budget
                        )
                        if certificate is not None:
                            terminal = ("optimal", "finite_pool_optimal")
                        else:
                            refined = _refined_dual_tolerance(
                                context, pool, last, work_dual_tolerance, proof_budget
                            )
                            if options.presolve and not proof_without_presolve:
                                proof_without_presolve = True
                                reason = "proof_reoptimize_without_presolve"
                            elif refined is None:
                                terminal = ("numerical_failure", "full_pool_proof_failed")
                            else:
                                work_dual_tolerance = refined
                                last.diagnostics["cg_work_dual_tolerance"] = refined
                                reason = "refine_dual_tolerance"
                    else:
                        certificate = _phase1_certificate(pool, sides, last, proof_budget)
                        terminal = (
                            ("infeasible", "finite_pool_infeasible")
                            if certificate is not None
                            else ("numerical_failure", "phase1_certificate_failed")
                        )
            except ProofLimitError:
                terminal = ("limit", "time_limit" if perf_counter() >= deadline else "proof_limit")
            except _PricingCallbackError as exc:
                terminal = ("numerical_failure", "pricing_error")
                last.diagnostics["pricing_error"] = str(exc)
            except (ValueError, TypeError, OverflowError, FloatingPointError) as exc:
                terminal = ("invalid_model", "invalid_pricing")
                last.diagnostics["pricing_error"] = str(exc)
        if terminal is not None:
            status, reason = terminal
        trace.append(
            ColumnGenerationStep(
                iteration,
                phase,
                status,
                last.objective_value,
                last.primal_bound,
                last.dual_bound,
                column_names,
                added,
                duals,
                scores,
                complete,
                phase_master.basis is not None,
                bool(last.diagnostics.get("warm_starts", 0)),
                last.iterations,
                perf_counter() - round_started,
                reason,
                deepcopy(last.diagnostics),
            )
        )
        if terminal is not None:
            return finish(*terminal, complete=complete)
        if reason == "phase1_feasible_remove_artificials":
            phase, phase_master = "phase2", master
    return finish("limit", "cg_iteration_limit")


def _verify_proposal(column, model):
    if type(column) is not MasterColumn:
        raise TypeError("Pricing must return MasterColumn objects.")
    rows = {row.name for row in model.constraints}
    if set(column.row_coefficients) - rows:
        raise ValueError("Pricing column contains unknown rows.")
    if column.name in model.variable_names():
        if column.cost != model.objective.coefficients.get(column.name, 0) or any(
            column.row_coefficients.get(row.name, 0) != row.coefficients.get(column.name, 0)
            for row in model.constraints
        ):
            raise ValueError("Pricing attempted to change an existing column.")


def covering_input_payload():
    """Frozen integration identity; this fresh payload also constructs the LP."""
    return {
        "row_lower": [1, 1],
        "row_upper": [None, None],
        "columns": [[1, 0], [0, 1], [1, 1], [2, 0]],
        "costs": [3, 2, 4, 1],
        "initial": [0, 1],
        "round_limit": 20,
        "expected_objective": 2.5,
        "oracle_kind": "fraction_vertices",
    }


def covering_example(options: SolveOptions | None = None) -> ColumnGenerationResult:
    """Public fixed integration example: two covering rows, full-pool optimum 2.5."""
    payload = covering_input_payload()
    names, row_names = ("a", "b", "ab", "double_a"), ("cover_a", "cover_b")
    pool = (
        MasterColumn(name, cost, dict(zip(row_names, coefficients, strict=True)))
        for name, cost, coefficients in zip(
            names, payload["costs"], payload["columns"], strict=True
        )
    )
    pool = tuple(pool)
    initial = [pool[index] for index in payload["initial"]]
    model = Model(
        name="general_covering_cg",
        variables=[Variable(column.name) for column in initial],
        constraints=[
            Constraint(
                name,
                {column.name: column.row_coefficients[name] for column in initial},
                lower_bound=lower if lower is not None else -inf,
                upper_bound=upper if upper is not None else inf,
            )
            for name, lower, upper in zip(
                row_names, payload["row_lower"], payload["row_upper"], strict=True
            )
        ],
        objective=Objective({column.name: column.cost for column in initial}),
    )
    result = column_generation(
        GeneralRestrictedMaster(model, options),
        FiniteColumnPricer(pool),
        max_iterations=payload["round_limit"],
    )
    return replace(
        result,
        input_identity="prototype_manifest.integrations.finite_cg",
        input_sha256=hashlib.sha256(
            json.dumps(
                payload,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode()
        ).hexdigest(),
        input_payload=payload,
    )
