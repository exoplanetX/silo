"""Optional SciPy/HiGHS comparison, isolated from every native solver layer.

SciPy is imported only when an availability query or external solve is requested.
LP and MILP share one external evidence stream, ``scipy_highs``. An external
status/objective comparison never substitutes for SILO's original-model proofs.
"""

from dataclasses import asdict, dataclass, field, replace
from importlib import import_module
from math import fsum, inf, isfinite
from time import perf_counter

import numpy as np

from silo.core.enums import OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.solve_types import SolveOptions


@dataclass
class HighsComparisonResult:
    status: str
    termination_reason: str
    available: bool = True
    objective_value: float | None = None
    primal_values: dict[str, float] = field(default_factory=dict)
    primal_bound: float | None = None
    dual_bound: float | None = None
    absolute_gap: float | None = None
    relative_gap: float | None = None
    backend_relative_gap: float | None = None
    original_primal_valid: bool = False
    backend_status: int | None = None
    backend_message: str = ""
    backend_method: str = ""
    scipy_version: str | None = None
    highs_version: str | None = None
    evidence_stream: str = "scipy_highs"
    external_algorithm_count: int = 0
    iterations: int = 0
    nodes: int = 0
    elapsed_seconds: float = 0.0
    diagnostics: dict = field(default_factory=dict)

    @property
    def has_primal_solution(self) -> bool:
        return self.objective_value is not None and self.original_primal_valid

    def to_dict(self) -> dict:
        """Return standard JSON values; preserve an explicit infinite-bound flag."""

        def clean(value):
            if isinstance(value, float) and not isfinite(value):
                return None
            if isinstance(value, dict):
                return {key: clean(item) for key, item in value.items()}
            if isinstance(value, list | tuple):
                return [clean(item) for item in value]
            return value

        return clean(
            {
                **asdict(self),
                "has_primal_solution": self.has_primal_solution,
                "dual_bound_is_infinite": self.dual_bound is not None
                and not isfinite(self.dual_bound),
            }
        )


def _scipy_modules():
    scipy = import_module("scipy")
    optimize = import_module("scipy.optimize")
    if not all(
        hasattr(optimize, name) for name in ("linprog", "milp", "Bounds", "LinearConstraint")
    ):
        raise ImportError("SciPy >=1.11 with optimize.linprog/milp is required")
    return scipy, optimize


def highs_availability() -> dict:
    """Report the optional dependency explicitly; no solve is performed."""
    try:
        scipy, _ = _scipy_modules()
    except ImportError as exc:
        return {
            "available": False,
            "reason": "optional_dependency_missing",
            "message": str(exc),
            "evidence_stream": "scipy_highs",
        }
    return {
        "available": True,
        "reason": "available",
        "scipy_version": scipy.__version__,
        "highs_version": None,
        "evidence_stream": "scipy_highs",
    }


def _checked_float(value, label, allowed_infinity=None):
    """Keep native input policy: finite data and exactly representable integers."""
    if not isfinite(value):
        if allowed_infinity is not None and value == allowed_infinity:
            return allowed_infinity
        raise ValueError(f"{label} must be finite or an allowed missing bound")
    converted = float(value)
    if not isfinite(converted):
        raise FloatingPointError(f"{label} is outside the finite float64 range")
    if isinstance(value, int) and int(converted) != value:
        raise FloatingPointError(f"{label} integer is not exactly representable in float64")
    return converted


def _checked_bounds(lower, upper, label):
    lower = _checked_float(lower, f"{label} lower", -inf)
    upper = _checked_float(upper, f"{label} upper", inf)
    if lower > upper:
        raise ValueError(f"Invalid {label}: lower exceeds upper")
    return lower, upper


def _arrays(model, options):
    model.validate()
    constant = _checked_float(model.objective.constant, "Objective constant")
    names = model.variable_names()
    positions = {name: index for index, name in enumerate(names)}
    if len(names) * max(1, len(model.constraints)) > options.max_dense_cells:
        raise MemoryError("Comparison dense matrix exceeds max_dense_cells")
    matrix = np.zeros((len(model.constraints), len(names)), dtype=float)
    row_lower, row_upper = [], []
    for index, row in enumerate(model.constraints):
        if row.lower_bound is None and row.upper_bound is None:
            _checked_float(row.rhs, f"Legacy row {row.name} RHS")
        lower, upper = _checked_bounds(*row.row_bounds, f"Row {row.name}")
        row_lower.append(lower)
        row_upper.append(upper)
        for name, coefficient in row.coefficients.items():
            matrix[index, positions[name]] = _checked_float(
                coefficient, f"Row {row.name} coefficient"
            )
    bounds = [
        _checked_bounds(v.bounds.lower, v.bounds.upper, f"Variable {v.name}")
        for v in model.variables
    ]
    costs = [
        _checked_float(model.objective.coefficients.get(n, 0), f"Objective coefficient {n}")
        for n in names
    ]
    sign = 1 if model.objective.sense == OptimizationSense.MINIMIZE else -1
    return {
        "names": names,
        "constant": constant,
        "sign": sign,
        "a": matrix,
        "row_lower": np.asarray(row_lower, dtype=float),
        "row_upper": np.asarray(row_upper, dtype=float),
        "lower": np.asarray([lower for lower, _ in bounds], dtype=float),
        "upper": np.asarray([upper for _, upper in bounds], dtype=float),
        "c": sign * np.asarray(costs, dtype=float),
        "integrality": np.asarray(
            [v.var_type != VariableType.CONTINUOUS for v in model.variables], dtype=int
        ),
    }


def _lp_call(optimize, data, options):
    inequalities, rhs, equalities, equality_rhs = [], [], [], []
    for coefficients, lower, upper in zip(
        data["a"], data["row_lower"], data["row_upper"], strict=True
    ):
        if lower == upper:
            equalities.append(coefficients)
            equality_rhs.append(upper)
        else:
            if isfinite(upper):
                inequalities.append(coefficients)
                rhs.append(upper)
            if isfinite(lower):
                inequalities.append(-coefficients)
                rhs.append(-lower)
    settings = {"presolve": options.presolve, "maxiter": options.lp_iteration_limit}
    if isfinite(options.time_limit):
        settings["time_limit"] = options.time_limit
    bounds = [
        (None if lower == -inf else lower, None if upper == inf else upper)
        for lower, upper in zip(data["lower"], data["upper"], strict=True)
    ]
    result = optimize.linprog(
        data["c"],
        A_ub=np.asarray(inequalities) if inequalities else None,
        b_ub=np.asarray(rhs) if rhs else None,
        A_eq=np.asarray(equalities) if equalities else None,
        b_eq=np.asarray(equality_rhs) if equality_rhs else None,
        bounds=bounds,
        method="highs",
        options=settings,
    )
    return result, settings


def _milp_call(optimize, data, options):
    settings = {
        "presolve": options.presolve,
        "node_limit": options.node_limit,
        "mip_rel_gap": options.relative_gap,
    }
    if isfinite(options.time_limit):
        settings["time_limit"] = options.time_limit
    constraints = (
        optimize.LinearConstraint(data["a"], data["row_lower"], data["row_upper"])
        if len(data["a"])
        else None
    )
    result = optimize.milp(
        data["c"],
        integrality=data["integrality"],
        bounds=optimize.Bounds(data["lower"], data["upper"]),
        constraints=constraints,
        options=settings,
    )
    return result, settings


def _ambiguous_presolve(raw):
    message = str(raw.message).lower()
    return int(raw.status) == 4 and "infeasible" in message and "unbounded" in message


def _run_with_retry(optimize, data, options, start, mixed_integer):
    """At most two backend calls; a retry consumes only remaining shared budgets."""
    call = _milp_call if mixed_integer else _lp_call
    remaining_time = (
        max(0.0, options.time_limit - (perf_counter() - start))
        if isfinite(options.time_limit)
        else inf
    )
    if remaining_time == 0:
        return None, {}, [], "time_limit"
    current_options = replace(options, time_limit=remaining_time)
    attempts = []
    raw, settings = call(optimize, data, current_options)
    attempts.append(
        {
            "backend_status": int(raw.status),
            "backend_message": str(raw.message),
            "options": dict(settings),
            "nodes": int(getattr(raw, "mip_node_count", 0) or 0),
            "iterations": int(getattr(raw, "nit", 0) or 0),
        }
    )
    if not options.presolve or not _ambiguous_presolve(raw):
        return raw, settings, attempts, None
    remaining_time = (
        max(0.0, options.time_limit - (perf_counter() - start))
        if isfinite(options.time_limit)
        else inf
    )
    remaining_nodes = max(0, options.node_limit - attempts[0]["nodes"])
    remaining_iterations = max(0, options.lp_iteration_limit - attempts[0]["iterations"])
    exhausted = (
        "time_limit"
        if remaining_time == 0
        else "node_limit"
        if mixed_integer and remaining_nodes == 0
        else "lp_iteration_limit"
        if not mixed_integer and remaining_iterations == 0
        else None
    )
    if exhausted is not None:
        return raw, settings, attempts, exhausted
    retry = replace(
        options,
        presolve=False,
        time_limit=remaining_time,
        node_limit=remaining_nodes,
        lp_iteration_limit=remaining_iterations,
    )
    raw, settings = call(optimize, data, retry)
    attempts.append(
        {
            "backend_status": int(raw.status),
            "backend_message": str(raw.message),
            "options": dict(settings),
            "nodes": int(getattr(raw, "mip_node_count", 0) or 0),
            "iterations": int(getattr(raw, "nit", 0) or 0),
        }
    )
    return raw, settings, attempts, None


def _original_primal(model, point, options):
    if set(point) != set(model.variable_names()) or not all(isfinite(x) for x in point.values()):
        return False, None
    for variable in model.variables:
        value = point[variable.name]
        for bound, direction in ((variable.bounds.lower, -1), (variable.bounds.upper, 1)):
            if isfinite(bound):
                scale = options.primal_tolerance * (1 + abs(bound) + abs(value))
                if direction * (value - bound) > scale:
                    return False, None
        if variable.var_type != VariableType.CONTINUOUS:
            if abs(value - round(value)) > options.integrality_tolerance:
                return False, None
    for row in model.constraints:
        terms = [coefficient * point[name] for name, coefficient in row.coefficients.items()]
        if not all(isfinite(term) for term in terms):
            return False, None
        activity = fsum(terms)
        for bound, direction in ((row.row_bounds[0], -1), (row.row_bounds[1], 1)):
            if isfinite(bound):
                scale = options.primal_tolerance * (1 + abs(bound) + fsum(abs(x) for x in terms))
                if direction * (activity - bound) > scale:
                    return False, None
    terms = [model.objective.constant] + [
        coefficient * point[name] for name, coefficient in model.objective.coefficients.items()
    ]
    if not all(isfinite(term) for term in terms):
        return False, None
    value = fsum(terms)
    return isfinite(value), value if isfinite(value) else None


def _finite_optional(value):
    return float(value) if value is not None and isfinite(value) else None


def solve_with_highs(model: Model, options: SolveOptions | None = None) -> HighsComparisonResult:
    """Solve a general LP/MILP through optional SciPy; never call a native solver.

    Only documented SciPy controls are forwarded. Their exact mapping is returned
    in diagnostics; native scaling/cut/heuristic/basis controls are separate.
    Returned primal points are checked in the original model. This check supplies
    no external Farkas/ray or optimality proof.
    """
    options = SolveOptions() if options is None else options
    if not isinstance(options, SolveOptions):
        raise TypeError("options must be SolveOptions")
    start = perf_counter()
    try:
        scipy, optimize = _scipy_modules()
    except ImportError as exc:
        return HighsComparisonResult(
            "unavailable",
            "optional_dependency_missing",
            available=False,
            backend_message=str(exc),
            elapsed_seconds=perf_counter() - start,
        )
    output = HighsComparisonResult(
        "numerical_failure", "comparison_not_completed", scipy_version=scipy.__version__
    )
    try:
        data = _arrays(model, options)
        output.diagnostics["input_validation"] = "finite_data_and_exact_integer_float64_conversion"
        mixed_integer = bool(data["integrality"].any())
        if not data["names"]:
            feasible = all(
                lower <= 0 <= upper
                for lower, upper in zip(data["row_lower"], data["row_upper"], strict=True)
            )
            output.status = "optimal" if feasible else "infeasible"
            output.termination_reason = "empty_model_evaluated"
            if feasible:
                output.objective_value = data["constant"]
                output.primal_bound = output.dual_bound = output.objective_value
                output.absolute_gap = output.relative_gap = 0.0
                output.original_primal_valid = True
            output.diagnostics["highs_called"] = False
            return output
        output.backend_method = (
            "scipy.optimize.milp" if mixed_integer else "scipy.optimize.linprog/highs"
        )
        raw, settings, attempts, exhausted = _run_with_retry(
            optimize, data, options, start, mixed_integer
        )
        output.external_algorithm_count = int(bool(attempts))
        output.diagnostics.update(
            highs_called=bool(attempts),
            backend_calls=len(attempts),
            backend_attempts=attempts,
            ambiguous_presolve_retry=len(attempts) == 2,
            ambiguous_presolve_resolved=len(attempts) == 2 and int(raw.status) in (0, 2, 3),
        )
        if exhausted is not None:
            output.diagnostics["retry_budget_exhausted"] = exhausted
        if raw is None:
            output.status, output.termination_reason = "limit", exhausted
            return output
        output.backend_status = int(raw.status)
        output.backend_message = str(raw.message)
        output.status = {0: "optimal", 1: "limit", 2: "infeasible", 3: "unbounded"}.get(
            int(raw.status), "numerical_failure"
        )
        output.termination_reason = f"highs_status_{raw.status}"
        if exhausted is not None:
            output.status, output.termination_reason = "limit", exhausted
        output.iterations = sum(attempt["iterations"] for attempt in attempts)
        output.nodes = sum(attempt["nodes"] for attempt in attempts)
        output.diagnostics.update(
            highs_called=True,
            forwarded_options=settings,
            primal_check="original_model_scaled_residuals",
            optimality_proof_provided=False,
            native_controls_not_forwarded=[
                "scaling",
                "cuts",
                "heuristics",
                "node_strategy",
                "lp_method",
                "absolute_gap",
                "integer_ray_proof_limit",
                "native_basis",
            ],
        )
        if mixed_integer:
            output.diagnostics["native_controls_not_forwarded"].append("lp_iteration_limit")
        output.diagnostics["native_controls_not_forwarded"].extend(
            [
                "dual_tolerance",
                "primal_tolerance",
                "integrality_tolerance",
                "pivot_tolerance",
                "complementarity_tolerance",
                "objective_tolerance",
                "cut_round_limit",
                "cuts_per_round",
                "cut_depth_limit",
            ]
        )
        raw_point = getattr(raw, "x", None)
        if raw_point is not None and len(raw_point) == len(data["names"]):
            point = dict(zip(data["names"], map(float, raw_point), strict=True))
            valid, value = _original_primal(model, point, options)
            if valid:
                raw_fun = _finite_optional(getattr(raw, "fun", None))
                if raw_fun is None and output.status == "optimal":
                    valid = False
                expected = (
                    fsum([model.objective.constant, data["sign"] * raw_fun])
                    if raw_fun is not None
                    else None
                )
                if expected is not None and abs(expected - value) > options.objective_tolerance * (
                    1 + abs(expected) + abs(value)
                ):
                    valid = False
                if valid and output.status in ("optimal", "limit", "unbounded"):
                    output.original_primal_valid = True
                    output.primal_values = point
                    output.objective_value = output.primal_bound = value
            if not valid:
                output.status, output.termination_reason = (
                    "numerical_failure",
                    "original_primal_failed",
                )
        if output.status == "optimal" and not output.has_primal_solution:
            output.status, output.termination_reason = "numerical_failure", "missing_optimal_primal"
        raw_bound = getattr(raw, "mip_dual_bound", None) if mixed_integer else None
        if raw_bound is not None and not np.isnan(raw_bound):
            output.dual_bound = float(model.objective.constant + data["sign"] * raw_bound)
        elif output.status == "optimal" and (not mixed_integer or options.relative_gap == 0):
            output.dual_bound = output.objective_value
        output.backend_relative_gap = _finite_optional(getattr(raw, "mip_gap", None))
        if (
            output.has_primal_solution
            and output.dual_bound is not None
            and isfinite(output.dual_bound)
        ):
            output.absolute_gap = abs(output.objective_value - output.dual_bound)
            output.relative_gap = output.absolute_gap / max(
                1, abs(output.objective_value), abs(output.dual_bound)
            )
            reversed_bound = data["sign"] * (output.dual_bound - output.objective_value)
            if reversed_bound > options.objective_tolerance * (1 + abs(output.objective_value)):
                output.status, output.termination_reason = "numerical_failure", "invalid_dual_bound"
        if mixed_integer and output.status == "optimal" and options.relative_gap > 0:
            if output.relative_gap is None or output.relative_gap > options.objective_tolerance:
                output.status, output.termination_reason = "limit", "highs_gap_limit"
    except MemoryError as exc:
        output.status, output.termination_reason = "limit", "resource_limit"
        output.backend_message = str(exc)
    except (ValueError, TypeError, AttributeError) as exc:
        output.status, output.termination_reason = "invalid_model", "comparison_input_rejected"
        output.backend_message = str(exc)
    except (FloatingPointError, OverflowError) as exc:
        output.status, output.termination_reason = "numerical_failure", "comparison_numeric_failure"
        output.backend_message = str(exc)
    finally:
        output.elapsed_seconds = perf_counter() - start
    return output


def compare_with_highs(model: Model, native_result, options: SolveOptions | None = None) -> dict:
    """Compare an already-computed native result with the single HiGHS stream."""
    options = SolveOptions() if options is None else options
    external = solve_with_highs(model, options)
    native_status = native_result.status
    status_match = external.available and native_status == external.status
    objective_match, native_primal_valid = None, False
    if native_status == external.status == "optimal":
        native_primal_valid, value = _original_primal(model, native_result.primal_values, options)
        if native_primal_valid and native_result.objective_value is not None:
            native_primal_valid = abs(value - native_result.objective_value) <= (
                options.objective_tolerance * (1 + abs(value))
            )
        if native_result.objective_value is not None and external.objective_value is not None:
            objective_match = abs(native_result.objective_value - external.objective_value) <= (
                options.objective_tolerance * (1 + abs(external.objective_value))
            )
    return {
        "evidence_stream": "scipy_highs",
        "external_algorithm_count": external.external_algorithm_count,
        "native_status": native_status,
        "external": external.to_dict(),
        "status_match": status_match,
        "objective_match": objective_match,
        "native_primal_valid": native_primal_valid,
        "optimal_comparison_passed": bool(
            status_match
            and objective_match
            and native_primal_valid
            and external.original_primal_valid
        ),
        "comparison_only": True,
    }


__all__ = ["HighsComparisonResult", "compare_with_highs", "highs_availability", "solve_with_highs"]
