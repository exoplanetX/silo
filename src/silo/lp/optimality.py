"""Original-input floating-point LP optimality checks; never solves a model.

Supported evidence: continuous maximization, nonnegative unbounded-above variables
and exactly fixed finite coordinates (the existing presolve recovery domain).
See docs/lp_duality.md for signs, fixed-bound contributions and tolerance limits.
"""

from dataclasses import dataclass
from math import inf, isfinite

from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus


@dataclass(frozen=True)
class LPOptimalityCheck:
    passed: bool
    primal_violation: float = inf
    dual_violation: float = inf
    stationarity_violation: float = inf
    objective_gap: float = inf
    complementarity_violation: float = inf
    primal_objective: float | None = None
    dual_objective: float | None = None
    message: str = ""


def check_lp_optimality(
    model: Model, solution: Solution, tolerance: float = 1e-7,
) -> LPOptimalityCheck:
    """Validate complete evidence against the original model, using absolute tolerance.

    Does not trust reported slacks, basis status or backend status alone. Invalid,
    missing, nonfinite, nonoptimal and out-of-domain evidence fails explicitly.
    Alternative optimal dual vectors are accepted. No external solver is called.
    """
    if not isfinite(tolerance) or tolerance <= 0:
        raise ValueError("Optimality tolerance must be finite and positive.")
    problem = _evidence_problem(model, solution)
    if problem:
        return LPOptimalityCheck(False, message=problem)

    x, y = solution.primal_values, solution.dual_values
    primal = dual = stationarity = complementarity = 0.0
    for row in model.constraints:
        activity = sum(a * x[name] for name, a in row.coefficients.items())
        if not isfinite(activity):
            return LPOptimalityCheck(False, message="Nonfinite row activity in LP evidence.")
        residual = activity - row.rhs
        if row.sense == ConstraintSense.LE:
            primal = max(primal, residual)
            dual = max(dual, -y[row.name])
        elif row.sense == ConstraintSense.GE:
            primal = max(primal, -residual)
            dual = max(dual, y[row.name])
        else:
            primal = max(primal, abs(residual))
        complementarity = max(complementarity, abs(y[row.name] * residual))

    dual_objective = model.objective.constant + sum(
        row.rhs * y[row.name] for row in model.constraints
    )
    for variable in model.variables:
        name = variable.name
        rc = model.objective.coefficients.get(name, 0.0) - sum(
            row.coefficients.get(name, 0.0) * y[row.name] for row in model.constraints
        )
        if not isfinite(rc):
            return LPOptimalityCheck(False, message="Nonfinite reduced cost in LP evidence.")
        stationarity = max(stationarity, abs(solution.reduced_costs[name] - rc))
        if variable.bounds.is_fixed():
            primal = max(primal, abs(x[name] - variable.bounds.lower))
            dual_objective += rc * variable.bounds.lower
        else:
            primal = max(primal, -x[name])
            dual = max(dual, rc)
            complementarity = max(complementarity, abs(x[name] * rc))
    primal_objective = model.objective.constant + sum(
        c * x[name] for name, c in model.objective.coefficients.items()
    )
    gap = max(abs(primal_objective - dual_objective),
              abs(primal_objective - solution.objective_value),
              abs(dual_objective - solution.objective_value))
    residuals = (primal, dual, stationarity, gap, complementarity)
    if not all(isfinite(value) for value in (*residuals, primal_objective, dual_objective)):
        return LPOptimalityCheck(False, message="Nonfinite arithmetic in optimality evidence.")
    passed = max(residuals) <= tolerance
    return LPOptimalityCheck(
        passed, *residuals, primal_objective, dual_objective,
        message="Original-space LP optimality checks passed." if passed
        else "Original-space LP optimality residual exceeds tolerance.",
    )


def _evidence_problem(model: Model, solution: Solution) -> str:
    try:
        model.validate()
        if model.objective.sense != OptimizationSense.MAXIMIZE:
            return "Optimality checker supports maximization only."
        for variable in model.variables:
            if variable.var_type != VariableType.CONTINUOUS:
                return "Optimality checker requires continuous LP variables."
            lower, upper = variable.bounds.lower, variable.bounds.upper
            if not ((lower == 0 and upper == inf) or (lower == upper and isfinite(lower))):
                return "Unsupported bounds: require [0, infinity) or exactly fixed finite bounds."
        numbers = [model.objective.constant, *model.objective.coefficients.values()]
        for row in model.constraints:
            if row.lower_bound is not None or row.upper_bound is not None:
                return "General row intervals require the unified original-space checker."
            numbers.extend([row.rhs, *row.coefficients.values()])
        if solution.status != SolverStatus.OPTIMAL:
            return "Optimality evidence requires an optimal LP result."
        variables = set(model.variable_names())
        rows = {row.name for row in model.constraints}
        if set(solution.primal_values) != variables or set(solution.reduced_costs) != variables:
            return "Incomplete or unexpected primal/reduced-cost coordinates."
        if set(solution.dual_values) != rows:
            return "Incomplete or unexpected original-row dual coordinates."
        numbers.extend([solution.objective_value, *solution.primal_values.values(),
                        *solution.dual_values.values(), *solution.reduced_costs.values()])
        if not all(isfinite(value) for value in numbers):
            return "Nonfinite model or solution evidence."
    except (ValueError, TypeError, OverflowError):
        return "Invalid model or nonnumeric optimality evidence."
    return ""
