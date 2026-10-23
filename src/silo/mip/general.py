"""General-domain deterministic branch-and-bound through the common LP pipeline."""

from dataclasses import dataclass, replace
from math import ceil, floor, inf, isfinite
from time import perf_counter

import numpy as np

from silo.lp.verification import exact_ray, primal_check
from silo.modeling.general import integer_bounds


@dataclass
class SearchNode:
    number: int
    depth: int
    lower: np.ndarray
    upper: np.ndarray
    bound: float = -inf
    basis: object = None
    parent_branch: tuple | None = None
    cuts: tuple = ()


def solve_milp(model, data, options, start):
    from silo.core.solve_types import SolveResult
    from silo.lp.general import solve_lp_data

    deadline = start + options.time_limit
    lo, hi = integer_bounds(data)
    stats = dict(
        lp_calls=0,
        heuristic_calls=0,
        heuristic_incumbents=0,
        branches=0,
        pseudocost_updates=0,
        warm_starts=0,
        dual_pivots=0,
        cold_fallbacks=0,
        cuts_generated=0,
        cuts_added=0,
        cut_rounds=0,
        node_strategy=options.node_strategy,
        frontier_includes_processing=True,
        unbounded_relaxations=0,
        unbounded_state=None,
        node_log=[],
    )
    integer = np.flatnonzero(data.integer)
    if np.any(lo > hi):
        return SolveResult(
            "infeasible",
            "empty_integer_domain",
            witness={"kind": "integer_domain"},
            diagnostics=stats,
        )
    pending = [SearchNode(0, 0, lo, hi)]
    best, incumbent, total_iterations, nodes, next_number = inf, None, 0, 0, 1
    pseudo = np.zeros((len(data.names), 2, 2))
    unresolved = []
    last_reason, failed = "tree_exhausted", None

    def relaxation(node, fixed=None):
        nonlocal total_iterations
        lower, upper = node.lower.copy(), node.upper.copy()
        if fixed is not None:
            lower[integer], upper[integer] = fixed, fixed
        nd = replace(data, lower=lower, upper=upper, integer=np.zeros_like(data.integer))
        if node.cuts:
            nd = replace(
                nd,
                a=np.vstack([nd.a, *[c.coefficients for c in node.cuts]]),
                row_lower=np.append(nd.row_lower, [c.lower for c in node.cuts]),
                row_upper=np.append(nd.row_upper, [c.upper for c in node.cuts]),
                row_names=nd.row_names + tuple(c.name for c in node.cuts),
            )
        remaining = max(0, options.lp_iteration_limit - total_iterations)
        result = solve_lp_data(
            nd,
            replace(options, lp_iteration_limit=remaining),
            node.basis if fixed is None else None,
            deadline,
        )
        stats["lp_calls"] += 1
        total_iterations += result.iterations
        stats["warm_starts"] += result.diagnostics.get("warm_starts", 0)
        stats["dual_pivots"] += result.diagnostics.get("dual_pivots", 0)
        stats["cold_fallbacks"] += bool(result.diagnostics.get("fallback_reason"))
        return result

    def accept(result):
        nonlocal best, incumbent
        if not result.primal_values:
            return False
        x = np.array([result.primal_values[n] for n in data.names])
        # Integrality tolerance identifies a rounding candidate, never grants
        # permission to publish a fractional integer or relax a row constraint.
        if np.any(abs(x[integer] - np.rint(x[integer])) > options.integrality_tolerance):
            return False
        x[integer] = np.rint(x[integer])
        if not primal_check(
            data,
            x,
            options.primal_tolerance,
            integer=True,
            integrality_tolerance=options.integrality_tolerance,
        ):
            return False
        value = float(data.sign * (data.constant + data.c @ x))
        if value < best:
            best, incumbent = value, x.copy()
            return True
        return False

    def global_bound():
        if unresolved:
            return -inf
        return min([best] + [n.bound for n in pending])

    def gap_stop():
        bound = global_bound()
        if incumbent is None or not isfinite(bound):
            return False
        gap = max(0.0, best - bound)
        return (options.absolute_gap > 0 and gap <= options.absolute_gap) or (
            options.relative_gap > 0
            and gap / max(1.0, abs(best), abs(bound)) <= options.relative_gap
        )

    while pending:
        if nodes >= options.node_limit:
            last_reason = "node_limit"
            break
        if perf_counter() >= deadline:
            last_reason = "time_limit"
            break
        if total_iterations >= options.lp_iteration_limit:
            last_reason = "lp_iteration_limit"
            break
        index = (
            -1
            if options.node_strategy == "dfs"
            else min(range(len(pending)), key=lambda i: (pending[i].bound, pending[i].number))
        )
        node = pending.pop(index)
        if node.bound >= best - options.primal_tolerance and incumbent is not None:
            continue
        nodes += 1
        lp = relaxation(node)
        stats["node_log"].append(
            {
                "node": node.number,
                "depth": node.depth,
                "status": lp.status,
                "bound": lp.objective_value,
                "inherited_bound": node.bound,
                "cuts": len(node.cuts),
            }
        )
        if lp.status == "infeasible":
            continue
        if lp.status in ("limit", "numerical_failure", "invalid_model"):
            accept(lp)
            pending.append(node)
            last_reason = lp.termination_reason
            failed = lp.status if lp.status != "limit" else None
            break
        if lp.status == "unbounded":
            stats["unbounded_relaxations"] += 1
            accept(lp)
            point = np.array([lp.primal_values[n] for n in data.names])
            norm, native, _ = lp._lp
            witness = (
                exact_ray(data, point, norm.ray(native.ray), True, options.integer_ray_proof_limit)
                if options.integer_ray_proof_limit
                else None
            )
            if witness is not None:
                stats["unbounded_state"] = "proven_mip_unbounded"
                return SolveResult(
                    "unbounded",
                    "integer_improving_ray",
                    objective_value=float(data.constant + data.c @ point),
                    primal_values=dict(zip(data.names, map(float, point), strict=True)),
                    primal_bound=float(data.constant + data.c @ point),
                    witness=witness,
                    dual_bound=-data.sign * inf,
                    nodes=nodes,
                    iterations=total_iterations,
                    diagnostics=stats,
                )
            fractional = [
                j
                for j in integer
                if abs(point[j] - round(point[j])) > options.integrality_tolerance
            ]
            if not fractional:
                stats["unbounded_state"] = "unresolved_unbounded_relaxation"
                unresolved.append(node)
                last_reason = "unresolved_unbounded_relaxation"
                break
            stats["unbounded_state"] = "branchable_unbounded_relaxation"
            node.bound = -inf
        else:
            point = np.array([lp.primal_values[n] for n in data.names])
            node.bound = data.sign * lp.optimality["dual_objective"]
            if node.parent_branch is not None and isfinite(node.parent_branch[2]):
                j, direction, old_bound, distance = node.parent_branch
                gain = max(0.0, node.bound - old_bound) / max(distance, 1e-8)
                pseudo[j, direction] += (gain, 1)
                stats["pseudocost_updates"] += 1
            if incumbent is not None and node.bound >= best - options.primal_tolerance:
                continue
            fractional = [
                j
                for j in integer
                if abs(point[j] - round(point[j])) > options.integrality_tolerance
            ]
            if not fractional:
                rounded = point.copy()
                rounded[integer] = np.rint(rounded[integer])
                if primal_check(
                    data,
                    rounded,
                    options.primal_tolerance,
                    integer=True,
                    integrality_tolerance=options.integrality_tolerance,
                ):
                    accept(lp)
                    continue
                # A rejected near-integral candidate cannot close a node. Use
                # a genuine floor/ceil split if both sides strictly reduce its
                # integer interval; otherwise retain it as a numerical failure.
                fractional = [
                    j
                    for j in integer
                    if point[j] != round(point[j])
                    and floor(point[j]) < node.upper[j]
                    and ceil(point[j]) > node.lower[j]
                ]
                if not fractional:
                    pending.append(node)
                    failed, last_reason = "numerical_failure", "integer_candidate_check_failed"
                    break
            if options.heuristics and (node.depth == 0 or nodes % 16 == 0):
                for rounded in (np.rint(point[integer]), np.ceil(point[integer])):
                    fixed = np.minimum(
                        np.maximum(rounded, node.lower[integer]), node.upper[integer]
                    )
                    stats["heuristic_calls"] += 1
                    trial = relaxation(node, fixed)
                    if accept(trial):
                        stats["heuristic_incumbents"] += 1
            # The active relaxation remains part of the bound at a gap exit.
            pending.append(node)
            if gap_stop():
                last_reason = "gap_limit"
                break
            pending.pop()

        def score(j, point=point):
            frac = point[j] - floor(point[j])
            if np.all(pseudo[j, :, 1] > 0):
                costs = pseudo[j, :, 0] / pseudo[j, :, 1]
                return min(costs[0] * frac, costs[1] * (1 - frac))
            return min(frac, 1 - frac)

        branch = max(fractional, key=lambda j: (score(j), -j))
        down, up = floor(point[branch]), ceil(point[branch])
        for direction in (0, 1):
            lower, upper = node.lower.copy(), node.upper.copy()
            if direction == 0:
                upper[branch] = min(upper[branch], down)
                distance = point[branch] - down
            else:
                lower[branch] = max(lower[branch], up)
                distance = up - point[branch]
            if lower[branch] <= upper[branch]:
                pending.append(
                    SearchNode(
                        next_number,
                        node.depth + 1,
                        lower,
                        upper,
                        node.bound,
                        lp.basis,
                        (branch, direction, node.bound, distance),
                        node.cuts,
                    )
                )
                next_number += 1
        stats["branches"] += 1
    bound = global_bound()
    exhausted = not pending and not unresolved and failed is None
    status = (
        ("optimal" if incumbent is not None else "infeasible") if exhausted else (failed or "limit")
    )
    result = SolveResult(
        status,
        "optimal" if exhausted and incumbent is not None else last_reason,
        nodes=nodes,
        iterations=total_iterations,
        diagnostics=stats,
    )
    result.dual_bound = data.sign * bound
    if incumbent is not None:
        result.objective_value = result.primal_bound = data.sign * best
        result.primal_values = dict(zip(data.names, map(float, incumbent), strict=True))
        result.row_activities = dict(
            zip(data.row_names, map(float, data.a @ incumbent), strict=True)
        )
        result.optimality = {
            "primal_feasible": True,
            "integer_feasible": True,
            "kind": "branch_and_bound",
            "tree_exhausted": exhausted,
        }
        if isfinite(bound):
            result.absolute_gap = max(0.0, best - bound)
            result.relative_gap = result.absolute_gap / max(1.0, abs(best), abs(bound))
    if exhausted and incumbent is None:
        result.witness = {"kind": "exhausted_integer_tree", "nodes": nodes}
    return result
