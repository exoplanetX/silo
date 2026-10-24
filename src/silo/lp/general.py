"""Common original-model LP pipeline for users, RMPs and MIP relaxations."""

from math import inf, isfinite
from time import perf_counter

import numpy as np

from silo.core.solve_types import SolveResult
from silo.lp.kernel import solve_canonical
from silo.lp.verification import (
    check_kkt,
    exact_farkas,
    exact_ray,
    primal_check,
    witness_float_point,
)
from silo.modeling.general import normalize
from silo.presolve.activity import propagate


def solve_lp_data(data, options, basis=None, deadline=inf, *, factor_state=None):
    """One shared LP pipeline for direct calls, RMPs and MIP relaxations."""
    if perf_counter() >= deadline:
        return SolveResult("limit", "time_limit")
    activity = propagate(data, enabled=options.presolve, deadline=deadline)
    if activity.timed_out:
        return SolveResult("limit", "time_limit")
    if activity.conflict:
        activity = propagate(data, enabled=False)
    try:
        with np.errstate(over="raise", invalid="raise", divide="raise"):
            norm = normalize(
                data, activity.lower, activity.upper, options.scaling, activity.redundant
            )
            if options.lp_engine == "sparse":
                from silo.lp.sparse_kernel import solve_canonical as sparse_solve

                native = sparse_solve(norm, options, basis, deadline, factor_state=factor_state)
            else:
                native = solve_canonical(norm, options, basis, deadline)
        private_state = getattr(native, "_factor_state", None)
        if hasattr(native, "_factor_state"):
            del native._factor_state
        result = SolveResult(
            native.status,
            native.reason,
            iterations=native.iterations,
            diagnostics={
                **native.diagnostics,
                "presolve_passes": activity.passes,
                "bound_tightenings": len(activity.history),
                "rows_removed": int(sum(activity.redundant)),
                "scaling": options.scaling,
                "lp_engine": options.lp_engine,
            },
            basis=native.snapshot,
        )
        result._lp = (norm, native, activity)
        if factor_state is not None:
            result._factor_state = private_state
        if native.status == "optimal":
            x = norm.point(native.point)
            multipliers = activity.recover_multipliers(
                norm.multipliers(native.dual, native.reduced)
            )
            report = check_kkt(
                data,
                x,
                multipliers,
                primal_tolerance=options.primal_tolerance,
                dual_tolerance=options.dual_tolerance,
                complementarity_tolerance=options.complementarity_tolerance,
                objective_tolerance=options.objective_tolerance,
            )
            if not report["valid"]:
                return SolveResult(
                    "numerical_failure",
                    "original_kkt_failed",
                    optimality=report,
                    diagnostics=result.diagnostics,
                    iterations=native.iterations,
                )
            yl, yu, zl, zu = multipliers
            objective = float(data.constant + data.c @ x)
            activity_values = data.a @ x
            dual = data.sign * (yl - yu)
            rc = data.c - data.a.T @ dual
            result.objective_value = result.primal_bound = result.dual_bound = objective
            result.absolute_gap = result.relative_gap = 0.0
            result.primal_values = dict(zip(data.names, map(float, x), strict=True))
            result.row_activities = dict(
                zip(data.row_names, map(float, activity_values), strict=True)
            )
            result.row_slacks = {
                n: {
                    "lower": float(v - lower) if isfinite(lower) else None,
                    "upper": float(u - v) if isfinite(u) else None,
                }
                for n, v, lower, u in zip(
                    data.row_names, activity_values, data.row_lower, data.row_upper, strict=True
                )
            }
            result.dual_values = dict(zip(data.row_names, map(float, dual), strict=True))
            result.reduced_costs = dict(zip(data.names, map(float, rc), strict=True))
            result.side_multipliers = {
                "row_lower": dict(zip(data.row_names, map(float, yl), strict=True)),
                "row_upper": dict(zip(data.row_names, map(float, yu), strict=True)),
                "variable_lower": dict(zip(data.names, map(float, zl), strict=True)),
                "variable_upper": dict(zip(data.names, map(float, zu), strict=True)),
            }
            result.optimality = report
        elif native.status == "infeasible":
            multipliers = activity.recover_multipliers(
                norm.multipliers(native.dual, native.reduced, objective=False)
            )
            result.witness = exact_farkas(data, multipliers)
            if result.witness is None:
                from silo.lp.tableau_view import exact_basis_farkas

                result.witness = exact_basis_farkas(
                    norm,
                    native,
                    activity,
                    operation_limit=options.proof_operation_limit,
                    deadline=deadline,
                )
                result.diagnostics["exact_basis_farkas"] = result.witness is not None
            if result.witness is None:
                result.status, result.termination_reason = (
                    "numerical_failure",
                    "farkas_check_failed",
                )
        elif native.status == "unbounded":
            x, h = norm.point(native.point), norm.ray(native.ray)
            result.witness = exact_ray(data, x, h)
            if result.witness is None:
                result.status, result.termination_reason = "numerical_failure", "ray_check_failed"
            else:
                anchor = witness_float_point(data, result.witness)
                if anchor is not None and isfinite(float(data.constant + data.c @ anchor)):
                    result.primal_values = dict(zip(data.names, map(float, anchor), strict=True))
                    result.objective_value = result.primal_bound = float(
                        data.constant + data.c @ anchor
                    )
                result.dual_bound = -data.sign * inf
        elif native.point is not None:
            x = norm.point(native.point)
            if primal_check(data, x, options.primal_tolerance):
                result.primal_values = dict(zip(data.names, map(float, x), strict=True))
                result.objective_value = float(data.constant + data.c @ x)
                result.primal_bound = result.objective_value
        return result
    except MemoryError as exc:
        return SolveResult(
            "limit",
            "resource_limit",
            diagnostics={"message": str(exc), "lp_engine": options.lp_engine},
        )
    except ImportError as exc:
        return SolveResult(
            "unsupported", "sparse_dependency_missing", diagnostics={"message": str(exc)}
        )
    except (FloatingPointError, OverflowError, np.linalg.LinAlgError) as exc:
        return SolveResult(
            "numerical_failure", "nonfinite_or_singular", diagnostics={"message": str(exc)}
        )
