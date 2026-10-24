"""General-domain deterministic branch-and-bound through the common LP pipeline."""

from dataclasses import dataclass, replace
from fractions import Fraction
from math import ceil, floor, inf, isfinite
from time import perf_counter

import numpy as np

from silo.lp.verification import exact_ray, primal_check, witness_float_point
from silo.modeling.general import integer_bounds
from silo.modeling.matrix_ops import append_rows
from silo.presolve.activity import propagate


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
    parent: int | None = None


@dataclass(frozen=True)
class NodeCut:
    name: str
    coefficients: tuple[float, ...]
    lower: float
    upper: float
    origin_node: int
    exact_key: tuple
    proof: dict


def solve_milp(model, data, options, start, extensions=None):
    from silo.core.solve_types import SolveResult
    from silo.lp.general import solve_lp_data
    from silo.mip.research import (
        OpenNodeView,
        ResearchContext,
        ResearchControl,
        VerifiedCutView,
        readonly,
    )

    deadline = start + options.time_limit
    control = ResearchControl(extensions, deadline)
    lo, hi = integer_bounds(data)
    stats = dict(
        lp_calls=0,
        lp_engine=options.lp_engine,
        lp_engine_counts={"dense": 0, "sparse": 0},
        sparse_base_factorizations=0,
        sparse_eta_updates=0,
        heuristic_calls=0,
        heuristic_incumbents=0,
        heuristic_skips_integral=0,
        heuristics_enabled=options.heuristics,
        cuts_enabled=options.cuts,
        node_selections=0,
        branches=0,
        pseudocost_updates=0,
        warm_starts=0,
        dual_pivots=0,
        cold_fallbacks=0,
        cuts_generated=0,
        cuts_added=0,
        cut_rounds=0,
        gmi_attempts=0,
        cut_duplicates=0,
        bound_propagations=0,
        integer_roundings=0,
        cut_events=[],
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

    def context(event, active=None, point=None, fractional=(), cuts=()):
        lower = data.lower if active is None else active.lower
        upper = data.upper if active is None else active.upper
        bound = global_bound()
        if active is not None:
            bound = min(bound, active.bound)
        return ResearchContext(
            event,
            None if active is None else active.number,
            None if active is None else active.depth,
            readonly(
                {} if point is None else dict(zip(data.names, map(float, point), strict=True))
            ),
            readonly(dict(zip(data.names, map(float, lower), strict=True))),
            readonly(dict(zip(data.names, map(float, upper), strict=True))),
            readonly(dict(zip(data.names, map(float, data.c), strict=True))),
            data.constant,
            "minimize" if data.sign == 1 else "maximize",
            tuple(data.names[j] for j in fractional),
            tuple(OpenNodeView(n.number, n.parent, n.depth, data.sign * n.bound) for n in pending),
            tuple(
                VerifiedCutView(
                    c.name, readonly(dict(zip(data.names, c.coefficients, strict=True))), c.lower
                )
                for c in cuts
            ),
            None if incumbent is None else data.sign * best,
            data.sign * bound,
            total_iterations,
            perf_counter() - start,
            readonly(
                {key: value for key, value in stats.items() if not isinstance(value, list | dict)}
            ),
        )

    def observe(event, active=None, point=None):
        if control.extensions.observer is not None:
            control.invoke("observer", context(event, active, point))

    def relaxation(node, fixed=None):
        nonlocal total_iterations
        lower, upper = node.lower.copy(), node.upper.copy()
        if fixed is not None:
            lower[integer], upper[integer] = fixed, fixed
        nd = replace(data, lower=lower, upper=upper, integer=np.zeros_like(data.integer))
        if node.cuts:
            if (
                options.lp_engine == "sparse"
                and nd.a.nnz
                + sum(sum(value != 0 for value in cut.coefficients) for cut in node.cuts)
                > options.max_sparse_nnz
            ):
                return SolveResult(
                    "limit",
                    "resource_limit",
                    diagnostics={
                        "message": "Sparse local-cut rows exceed max_sparse_nnz.",
                        "lp_engine": "sparse",
                    },
                )
            nd = replace(
                nd,
                a=append_rows(nd.a, [c.coefficients for c in node.cuts]),
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
        stats["lp_engine_counts"][options.lp_engine] += 1
        stats["sparse_base_factorizations"] += result.diagnostics.get("base_factorizations", 0)
        stats["sparse_eta_updates"] += result.diagnostics.get("eta_updates", 0)
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

    def cut_loop(node, lp):
        from silo.cuts.gmi import derive_gmi
        from silo.lp.tableau_view import exact_tableau_rows
        from silo.utils.rational import ProofBudget

        if not options.cuts or node.depth > options.cut_depth_limit:
            return lp
        for _ in range(options.cut_round_limit):
            if lp.status != "optimal" or perf_counter() >= deadline:
                break
            stats["gmi_attempts"] += 1
            budget = ProofBudget(options.proof_operation_limit, deadline)
            norm, native, _ = lp._lp
            views = exact_tableau_rows(
                norm,
                native,
                data.integer,
                options.cuts_per_round,
                operation_limit=options.proof_operation_limit,
                deadline=deadline,
                budget=budget,
            )
            point = np.array([lp.primal_values[n] for n in data.names])
            selected, existing = [], {c.exact_key for c in node.cuts}
            for view in views:
                exact = derive_gmi(view, len(data.names), budget=budget)
                if exact is None:
                    continue
                stats["cuts_generated"] += 1
                proof = exact.proof(budget=budget)
                if proof is None:
                    continue
                if not any(exact.coefficients) and exact.lower > 0:
                    stats["cut_events"].append(
                        {"node": node.number, "contradiction": True, "proof": proof}
                    )
                    return SolveResult(
                        "infeasible",
                        "gmi_integer_contradiction",
                        witness={"kind": "gmi", "proof": proof},
                    )
                pivot = next((abs(v) for v in exact.coefficients if v), None)
                if pivot is None:
                    continue
                try:
                    key = tuple(budget.guard(v / pivot) for v in exact.coefficients) + (
                        budget.guard(exact.lower / pivot),
                    )
                except ValueError:
                    break
                if key in existing:
                    stats["cut_duplicates"] += 1
                    continue
                candidate = exact.to_candidate(
                    data.names,
                    node.lower,
                    node.upper,
                    node.number,
                    stats["cuts_added"] + len(selected),
                    budget=budget,
                )
                if candidate is None:
                    continue
                float_proof = exact.float_proof(
                    candidate, data.names, node.lower, node.upper, budget=budget
                )
                if float_proof is None:
                    continue
                vector = np.array([dict(candidate.coefficients).get(n, 0) for n in data.names])
                violation = candidate.rhs - vector @ point
                if violation <= options.primal_tolerance * (
                    1 + abs(candidate.rhs) + abs(vector) @ abs(point)
                ):
                    continue
                name = candidate.metadata.cut_id
                while name in data.row_names or any(c.name == name for c in node.cuts):
                    name += "_"
                selected.append(
                    NodeCut(
                        name,
                        tuple(vector),
                        candidate.rhs,
                        inf,
                        node.number,
                        key,
                        {
                            **proof,
                            "float_conversion": float_proof,
                        },
                    )
                )
                existing.add(key)
            if not selected:
                break
            if control.extensions.separator is not None:
                choice = control.invoke(
                    "separator", context("separate", node, point, cuts=selected)
                )
                if (
                    not isinstance(choice, tuple | list)
                    or any(type(i) is not int or i < 0 or i >= len(selected) for i in choice)
                    or len(set(choice)) != len(choice)
                ):
                    control.reject("separator must select unique verified cut indices.")
                if control.error is not None:
                    node.bound = max(node.bound, data.sign * lp.optimality["dual_objective"])
                    return replace(lp, status="limit", termination_reason=control.reason)
                selected = [selected[i] for i in choice]
                if not selected:
                    break
            previous = lp.objective_value
            node.bound = max(node.bound, data.sign * lp.optimality["dual_objective"])
            node.basis = lp.basis
            node.cuts = (*node.cuts, *selected)
            stats["cuts_added"] += len(selected)
            stats["cut_rounds"] += 1
            lp = relaxation(node)
            stats["cut_events"].append(
                {
                    "node": node.number,
                    "depth": node.depth,
                    "added": [c.name for c in selected],
                    "origin_nodes": [c.origin_node for c in node.cuts],
                    "scope": "node_local",
                    "before": previous,
                    "after": lp.objective_value,
                    "status": lp.status,
                    "lp_engine": options.lp_engine,
                    "lp_diagnostics": lp.diagnostics.copy(),
                    "proofs": [c.proof for c in selected],
                }
            )
        if perf_counter() >= deadline:
            if lp.status == "optimal":
                node.bound = max(node.bound, data.sign * lp.optimality["dual_objective"])
            return replace(lp, status="limit", termination_reason="time_limit")
        return lp

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
        if control.extensions.node_selector is not None:
            choice = control.invoke("node_selector", context("select_node"), pending[index].number)
            indices = [
                i for i, n in enumerate(pending) if type(choice) is int and n.number == choice
            ]
            if not indices:
                control.reject("node_selector must select an existing open node ID.")
            if control.error is not None:
                last_reason = control.reason
                break
            index = indices[0]
        node = pending.pop(index)
        stats["node_selections"] += 1
        observe("node_selected", node)
        if control.error is not None:
            pending.append(node)
            last_reason = control.reason
            break
        if node.bound >= best and incumbent is not None:
            continue
        nodes += 1
        tightened = propagate(
            data, node.lower, node.upper, enabled=options.presolve, integral=True, deadline=deadline
        )
        if tightened.timed_out:
            pending.append(node)
            last_reason = "time_limit"
            break
        stats["bound_propagations"] += len(tightened.history)
        stats["integer_roundings"] += tightened.integer_roundings
        if tightened.conflict or np.any(tightened.lower > tightened.upper):
            continue
        node.lower, node.upper = tightened.lower, tightened.upper
        lp = relaxation(node)
        lp = cut_loop(node, lp)
        observe(
            "relaxation",
            node,
            (np.array([lp.primal_values[n] for n in data.names]) if lp.primal_values else None),
        )
        if control.error is not None:
            if lp.status == "optimal":
                node.bound = max(node.bound, data.sign * lp.optimality["dual_objective"])
            accept(lp)
            pending.append(node)
            if lp.status in ("numerical_failure", "invalid_model"):
                failed, last_reason = lp.status, lp.termination_reason
            else:
                last_reason = control.reason
            break
        stats["node_log"].append(
            {
                "node": node.number,
                "parent": node.parent,
                "depth": node.depth,
                "status": lp.status,
                "bound": lp.objective_value,
                "inherited_bound": node.bound,
                "cuts": len(node.cuts),
                "local_cut_origins": [c.origin_node for c in node.cuts],
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
            if isfinite(node.bound):
                unresolved.append(node)
                stats["unbounded_state"] = "conflicting_unbounded_relaxation"
                failed, last_reason = (
                    "numerical_failure",
                    "unbounded_child_conflicts_with_finite_bound",
                )
                break
            stats["unbounded_relaxations"] += 1
            accept(lp)
            exact_point = [Fraction(lp.witness["point"][n]) for n in data.names]
            exact_direction = [Fraction(lp.witness["ray"][n]) for n in data.names]
            point = np.array(list(map(float, exact_point)))
            witness = (
                exact_ray(data, exact_point, exact_direction, True, options.integer_ray_proof_limit)
                if options.integer_ray_proof_limit
                else None
            )
            if witness is not None:
                stats["unbounded_state"] = "proven_mip_unbounded"
                result = SolveResult(
                    "unbounded",
                    "integer_improving_ray",
                    witness=witness,
                    dual_bound=-data.sign * inf,
                    nodes=nodes,
                    iterations=total_iterations,
                    diagnostics=stats,
                )
                anchor = witness_float_point(data, witness)
                if anchor is not None and isfinite(float(data.constant + data.c @ anchor)):
                    result.objective_value = result.primal_bound = float(
                        data.constant + data.c @ anchor
                    )
                    result.primal_values = dict(zip(data.names, map(float, anchor), strict=True))
                return result
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
            node.bound = max(node.bound, data.sign * lp.optimality["dual_objective"])
            if node.parent_branch is not None and isfinite(node.parent_branch[2]):
                j, direction, old_bound, distance = node.parent_branch
                gain = max(0.0, node.bound - old_bound) / max(distance, 1e-8)
                pseudo[j, direction] += (gain, 1)
                stats["pseudocost_updates"] += 1
            if incumbent is not None and node.bound >= best:
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
                    stats["heuristic_skips_integral"] += bool(options.heuristics)
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
            if control.extensions.heuristic is not None:
                proposal = control.invoke(
                    "heuristic", context("heuristic", node, point, fractional)
                )
                if proposal is not None:
                    try:
                        if set(proposal) != set(data.names):
                            raise ValueError(
                                "heuristic requires every original variable exactly once."
                            )
                        values = np.array([float(proposal[n]) for n in data.names])
                        if not np.isfinite(values).all() or not primal_check(
                            data,
                            values,
                            options.primal_tolerance,
                            integer=True,
                            integrality_tolerance=options.integrality_tolerance,
                        ):
                            raise ValueError(
                                "heuristic candidate failed original feasibility/integrality."
                            )
                        trial = SolveResult(
                            "limit",
                            "research_candidate",
                            primal_values=dict(zip(data.names, map(float, values), strict=True)),
                        )
                        if not accept(trial):
                            stats["research_heuristic_rejections"] = (
                                stats.get("research_heuristic_rejections", 0) + 1
                            )
                    except (TypeError, ValueError, OverflowError) as exc:
                        control.reject(str(exc))
                if control.error is not None:
                    pending.append(node)
                    last_reason = control.reason
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
        if control.extensions.branch_rule is not None:
            choice = control.invoke(
                "branch_rule", context("branch", node, point, fractional), data.names[branch]
            )
            if not isinstance(choice, str) or choice not in tuple(
                data.names[j] for j in fractional
            ):
                control.reject("branch_rule must select a fractional candidate name.")
            if control.error is not None:
                pending.append(node)
                last_reason = control.reason
                break
            branch = data.names.index(choice)
        observe("branch", node, point)
        if control.error is not None:
            pending.append(node)
            last_reason = control.reason
            break
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
                        node.number,
                    )
                )
                next_number += 1
        stats["branches"] += 1
    bound = global_bound()
    stats.update(
        open_nodes=len(pending), unresolved_nodes=len(unresolved), global_bound_normalized=bound
    )
    exhausted = not pending and not unresolved and failed is None
    observe("terminated")
    stats.update(
        research_calls=control.calls, research_error=control.error, research_trace=control.trace
    )
    if control.error is not None:
        exhausted = False
        if failed is None:
            last_reason = control.reason
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
