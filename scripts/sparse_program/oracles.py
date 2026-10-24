"""Independent raw-input truth and checks; no SILO production imports.

Every coefficient is converted to Fraction before arithmetic, preserving actual
binary float inputs. Small LPs use bounded exact vertex enumeration plus an exact
dual certificate; small MILPs exhaust the integer box. Constructed large witnesses
are proposals until every original side and dual inequality is checked.
The optional HiGHS comparison is invoked only by an explicit reference function.
"""

import hashlib
import itertools
import json
import math
import os
import platform
import subprocess
import sys
import time
import warnings
from datetime import UTC, datetime
from fractions import Fraction as F
from pathlib import Path


def q(value):
    if isinstance(value, bool) or not isinstance(value, int | float | F):
        raise ValueError("Expected original finite integer or binary float")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Nonfinite oracle input")
    return F(value)


def row_bounds(row):
    if "lower" in row or "upper" in row:
        return row.get("lower"), row.get("upper")
    sense, rhs = row.get("sense", "<="), row.get("rhs", 0)
    return (None, rhs) if sense == "<=" else (rhs, None) if sense == ">=" else (rhs, rhs)


def dot(coefficients, values):
    return sum((q(a) * values.get(name, F(0)) for name, a in coefficients.items()), F(0))


def objective(payload, point):
    return q(payload["objective"].get("constant", 0)) + dot(
        payload["objective"]["coefficients"], point
    )


def primal(payload, candidate, integer=False):
    names = {v["name"] for v in payload["variables"]}
    if set(candidate) - names:
        raise ValueError("Unknown primal coordinate")
    point = {name: q(candidate.get(name, 0)) for name in names}
    for v in payload["variables"]:
        x = point[v["name"]]
        if v.get("lower", 0) is not None and x < q(v.get("lower", 0)):
            raise ValueError("Original lower bound violated")
        if v.get("upper") is not None and x > q(v["upper"]):
            raise ValueError("Original upper bound violated")
        if integer and v.get("type", "continuous") != "continuous" and x.denominator != 1:
            raise ValueError("Original integrality violated")
    for r in payload["constraints"]:
        activity = dot(r["coefficients"], point)
        lower, upper = row_bounds(r)
        if lower is not None and activity < q(lower):
            raise ValueError(f"Original lower row violated: {r['name']}")
        if upper is not None and activity > q(upper):
            raise ValueError(f"Original upper row violated: {r['name']}")
    return point


def primal_dual_pair(payload, candidate):
    """Exact original-box weak duality including signed row and variable sides."""
    point = primal(payload, candidate["point"])
    sign = 1 if payload["sense"] == "minimize" else -1
    reduced = {
        v["name"]: sign * q(payload["objective"]["coefficients"].get(v["name"], 0))
        for v in payload["variables"]
    }
    duals = {name: q(value) for name, value in candidate.get("row_duals", {}).items()}
    if set(duals) - {r["name"] for r in payload["constraints"]}:
        raise ValueError("Unknown dual row")
    dual = sign * q(payload["objective"].get("constant", 0))
    for r in payload["constraints"]:
        y = duals.get(r["name"], F(0))
        lower, upper = row_bounds(r)
        side = lower if y >= 0 else upper
        if y and side is None:
            raise ValueError("Dual sign on absent row side")
        if y:
            dual += y * q(side)
            for name, a in r["coefficients"].items():
                reduced[name] -= y * q(a)
    for v in payload["variables"]:
        rc = reduced[v["name"]]
        side = v.get("lower", 0) if rc >= 0 else v.get("upper")
        if rc and side is None:
            raise ValueError("Dual sign on absent variable side")
        if rc:
            dual += rc * q(side)
    p = sign * objective(payload, point)
    if p != dual:
        raise ValueError(f"Original exact primal/dual objectives differ: {p - dual}")
    return {
        "status": "optimal",
        "objective_exact": str(sign * p),
        "objective": float(sign * p),
        "kind": "exact_original_binary_primal_dual_pair",
        "point": {n: str(v) for n, v in point.items()},
        "row_duals": {r["name"]: str(duals.get(r["name"], 0)) for r in payload["constraints"]},
        "variable_reduced_costs": {n: str(v) for n, v in reduced.items()},
        "normalized_primal_objective_exact": str(p),
        "normalized_dual_objective_exact": str(dual),
        "all_original_rows_checked": len(payload["constraints"]),
        "all_original_columns_checked": len(payload["variables"]),
    }


def farkas(payload, candidate):
    """Check a sufficient nonnegative-column Farkas separation on raw inputs."""
    if any(v.get("lower", 0) != 0 or v.get("upper") is not None for v in payload["variables"]):
        raise ValueError("This independent Farkas check requires lambda>=0 without upper bounds")
    products = dict.fromkeys((v["name"] for v in payload["variables"]), F(0))
    separation = F(0)
    for r in payload["constraints"]:
        y = q(candidate["row_duals"].get(r["name"], 0))
        lower, upper = row_bounds(r)
        side = lower if y >= 0 else upper
        if y and side is None:
            raise ValueError("Farkas sign on absent side")
        if y:
            separation += y * q(side)
        for name, a in r["coefficients"].items():
            products[name] += y * q(a)
    if separation <= 0 or any(v > 0 for v in products.values()):
        raise ValueError("Invalid original Farkas separation")
    return {
        "status": "infeasible",
        "kind": "exact_original_binary_farkas",
        "separation": str(separation),
        "row_duals": {
            r["name"]: str(candidate["row_duals"].get(r["name"], 0)) for r in payload["constraints"]
        },
        "column_products": {n: str(v) for n, v in products.items()},
    }


def point_ray(payload, candidate):
    point = primal(payload, candidate["point"])
    ray = {v["name"]: q(candidate["ray"].get(v["name"], 0)) for v in payload["variables"]}
    if not any(ray.values()):
        raise ValueError("Zero recession direction")
    for v in payload["variables"]:
        direction = ray[v["name"]]
        if v.get("lower", 0) is not None and direction < 0:
            raise ValueError("Ray violates lower variable side")
        if v.get("upper") is not None and direction > 0:
            raise ValueError("Ray violates upper variable side")
    for r in payload["constraints"]:
        direction = dot(r["coefficients"], ray)
        lower, upper = row_bounds(r)
        if (lower is not None and direction < 0) or (upper is not None and direction > 0):
            raise ValueError("Ray violates original row recession cone")
    sign = 1 if payload["sense"] == "minimize" else -1
    improvement = sign * dot(payload["objective"]["coefficients"], ray)
    if improvement >= 0:
        raise ValueError("Ray does not strictly improve the original objective")
    return {
        "status": "unbounded",
        "kind": "exact_original_binary_point_ray",
        "point": {n: str(v) for n, v in point.items()},
        "ray": {n: str(v) for n, v in ray.items()},
        "normalized_improvement": str(improvement),
    }


def inequalities(payload, fixed=None):
    fixed = {} if fixed is None else fixed
    names = [v["name"] for v in payload["variables"] if v["name"] not in fixed]
    sides = []
    for r in payload["constraints"]:
        lower, upper = row_bounds(r)
        offset = dot(r["coefficients"], fixed)
        coefficients = tuple(q(r["coefficients"].get(n, 0)) for n in names)
        if lower is not None:
            sides.append(
                (tuple(-a for a in coefficients), -q(lower) + offset, "row:" + r["name"] + ":lower")
            )
        if upper is not None:
            sides.append((coefficients, q(upper) - offset, "row:" + r["name"] + ":upper"))
    for v in payload["variables"]:
        for side, sign in (("lower", -1), ("upper", 1)):
            bound = v.get(side, 0 if side == "lower" else None)
            if bound is None:
                continue
            vector = tuple(F(sign if n == v["name"] else 0) for n in names)
            rhs = sign * (q(bound) - fixed.get(v["name"], 0))
            sides.append((vector, rhs, "var:" + v["name"] + ":" + side))
    return names, sides


def equations(matrix, rhs):
    n = len(rhs)
    rows = [[q(v) for v in row] + [q(b)] for row, b in zip(matrix, rhs, strict=True)]
    for k in range(n):
        pivot = next((i for i in range(k, n) if rows[i][k]), None)
        if pivot is None:
            return None
        rows[k], rows[pivot] = rows[pivot], rows[k]
        divisor = rows[k][k]
        rows[k] = [v / divisor for v in rows[k]]
        for i in range(n):
            if i != k:
                scale = rows[i][k]
                rows[i] = [a - scale * b for a, b in zip(rows[i], rows[k], strict=True)]
    return tuple(row[-1] for row in rows)


def vertex_truth(payload, fixed=None, combination_cap=2_000_000):
    """Enumerate small vertices; require a global exact dual pair for an LP claim."""
    fixed = {} if fixed is None else {n: q(v) for n, v in fixed.items()}
    names, sides = inequalities(payload, fixed)
    n = len(names)
    if n > 4 or math.comb(len(sides), n) > combination_cap:
        raise ValueError("Independent exact vertex oracle size budget")
    sign = 1 if payload["sense"] == "minimize" else -1
    normalized_cost = tuple(
        sign * q(payload["objective"]["coefficients"].get(name, 0)) for name in names
    )
    best, point, certificate, checked = None, None, None, 0
    for active in itertools.combinations(sides, n):
        checked += 1
        values = equations([a for a, _, _ in active], [b for _, b, _ in active])
        if values is None or any(
            sum((a * x for a, x in zip(coeff, values, strict=True)), F(0)) > b
            for coeff, b, _ in sides
        ):
            continue
        candidate = {**fixed, **dict(zip(names, values, strict=True))}
        value = sign * objective(payload, candidate)
        if best is None or value < best:
            best, point, certificate = value, candidate, None
        if value == best and certificate is None:
            dual = equations(list(zip(*(a for a, _, _ in active), strict=True)), normalized_cost)
            if dual is not None and all(y <= 0 for y in dual):
                certificate = {
                    label: str(y) for (_, _, label), y in zip(active, dual, strict=True) if y
                }
    if best is None:
        return {
            "status": "infeasible",
            "kind": "no_feasible_vertex_in_bounded_enumerated_integer_slice",
            "active_sets_checked": checked,
        }
    if not fixed and certificate is None:
        raise ValueError("Vertex value lacks an independent exact dual optimality certificate")
    answer = {
        "status": "optimal",
        "objective_exact": str(sign * best),
        "objective": float(sign * best),
        "point": {name: str(value) for name, value in point.items()},
        "inequality_signed_duals": certificate,
        "kind": "exact_original_binary_vertex_enumeration",
        "active_sets_checked": checked,
    }
    if not fixed:
        row_duals = {}
        for label, value in certificate.items():
            kind, name, side = label.split(":")
            if kind == "row":
                row_duals[name] = row_duals.get(name, F(0)) + (
                    -F(value) if side == "lower" else F(value)
                )
        verified = primal_dual_pair(payload, {"point": point, "row_duals": row_duals})
        answer["row_duals"] = verified["row_duals"]
        answer["variable_reduced_costs"] = verified["variable_reduced_costs"]
        answer["normalized_primal_objective_exact"] = verified["normalized_primal_objective_exact"]
        answer["normalized_dual_objective_exact"] = verified["normalized_dual_objective_exact"]
    return answer


def integer_truth(payload, assignment_cap=2_000_000, retain_slices=False):
    integer = [v for v in payload["variables"] if v.get("type", "continuous") != "continuous"]
    domains = []
    for v in integer:
        if v.get("lower", 0) is None or v.get("upper") is None:
            raise ValueError("Independent integer enumeration needs a finite original box")
        domains.append(range(math.ceil(q(v.get("lower", 0))), math.floor(q(v["upper"])) + 1))
    count = math.prod(map(len, domains))
    if count > assignment_cap:
        raise ValueError("Independent integer assignment budget")
    box_proof = finite_box_proof(payload)
    sign, best, found, total_vertices = (1 if payload["sense"] == "minimize" else -1), None, None, 0
    slices = []
    for values in itertools.product(*domains):
        fixed = dict(zip((v["name"] for v in integer), map(F, values), strict=True))
        reference = vertex_truth(payload, fixed)
        if retain_slices:
            slices.append({"fixed": {n: str(v) for n, v in fixed.items()}, "truth": reference})
        total_vertices += reference["active_sets_checked"]
        if reference["status"] == "optimal":
            value = F(reference["objective_exact"])
            if best is None or sign * value < sign * best:
                best, found = value, reference["point"]
    if found is not None:
        primal(payload, {n: F(v) for n, v in found.items()}, integer=True)
    answer = {
        "status": "infeasible" if best is None else "optimal",
        "kind": "exact_integer_box_and_continuous_vertices",
        "objective_exact": None if best is None else str(best),
        "objective": None if best is None else float(best),
        "point": found,
        "integer_assignments": count,
        "active_sets_checked": total_vertices,
        "finite_box_proof": box_proof,
    }
    if retain_slices:
        answer["integer_slices"] = slices
    return answer


def full_pool_payload(case):
    p = {
        **case["payload"],
        "variables": [
            {"name": c["name"], "lower": 0, "upper": None, "type": "continuous"}
            for c in case["pool"]
        ],
        "objective": {
            "constant": case["payload"]["objective"].get("constant", 0),
            "coefficients": {c["name"]: c["cost"] for c in case["pool"]},
        },
        "constraints": [],
    }
    for r in case["payload"]["constraints"]:
        p["constraints"].append(
            {
                **r,
                "coefficients": {
                    c["name"]: c["coefficients"][r["name"]]
                    for c in case["pool"]
                    if r["name"] in c["coefficients"]
                },
            }
        )
    return p


def exact_truth(case, retain_proof=False):
    p = case["payload"]
    if case["group"] == "cg":
        p = full_pool_payload(case)
        if case["id"] == "CG-UNBOUNDED-GUARD":
            return point_ray(
                p, {"point": {"a": 0, "b": 1, "c": 0}, "ray": {"a": 1, "b": 0, "c": 1}}
            )
        return vertex_truth(p)
    if case["group"] == "mip":
        return integer_truth(p, retain_slices=retain_proof)
    if case["group"] in ("capacity", "mechanism"):
        return primal_dual_pair(p, case["candidate"])
    if case["id"].startswith("PRESS-INF"):
        return farkas(p, case["candidate"])
    if case["id"].startswith("PRESS-UNB"):
        return point_ray(p, case["candidate"])
    if case["id"].startswith("PRESS-LIMIT"):
        return {"status": "optimal", "kind": "underlying_math_unlimited", **vertex_truth(p)}
    return vertex_truth(p)


def finite_box_proof(payload):
    """Prove compactness for exhaustive integer slices using original row sides."""
    bounds = {
        v["name"]: [
            None if v.get("lower", 0) is None else q(v.get("lower", 0)),
            None if v.get("upper") is None else q(v["upper"]),
        ]
        for v in payload["variables"]
    }
    derivations = []
    sides = []
    for row in payload["constraints"]:
        lower, upper = row_bounds(row)
        if upper is not None:
            sides.append((row["name"] + ":upper", row["coefficients"], q(upper)))
        if lower is not None:
            sides.append(
                (
                    row["name"] + ":lower",
                    {n: -q(a) for n, a in row["coefficients"].items()},
                    -q(lower),
                )
            )
    for _ in range(len(bounds) + 1):
        changed = False
        for label, coefficients, rhs in sides:
            for name, coefficient in coefficients.items():
                a = q(coefficient)
                if not a:
                    continue
                others = []
                for other, value in coefficients.items():
                    if other == name or not value:
                        continue
                    bound = bounds[other][0 if value > 0 else 1]
                    if bound is None:
                        break
                    others.append(q(value) * bound)
                else:
                    value = (rhs - sum(others, F(0))) / a
                    side = 1 if a > 0 else 0
                    old = bounds[name][side]
                    if old is None or (value < old if side else value > old):
                        bounds[name][side] = value
                        derivations.append(
                            {
                                "name": name,
                                "side": side,
                                "value": str(value),
                                "original_row_side": label,
                            }
                        )
                        changed = True
        if not changed:
            break
    if any(value is None for pair in bounds.values() for value in pair):
        raise ValueError("Integer vertex enumeration lacks an original finite-box proof")
    return {
        "bounds": {n: list(map(str, pair)) for n, pair in bounds.items()},
        "derived_bounds": derivations,
    }


def _fraction_solve(matrix, rhs):
    """Sparse exact elimination for the small cyclic witness systems only."""
    n = len(rhs)
    rows = [{j: q(a) for j, a in row.items() if a} for row in matrix]
    right = [q(v) for v in rhs]
    for j in range(n):
        pivot = next((i for i in range(j, n) if rows[i].get(j)), None)
        if pivot is None:
            raise ValueError("Singular exact witness system")
        rows[j], rows[pivot] = rows[pivot], rows[j]
        right[j], right[pivot] = right[pivot], right[j]
        divisor = rows[j][j]
        rows[j] = {k: a / divisor for k, a in rows[j].items()}
        right[j] /= divisor
        for i in range(j + 1, n):
            factor = rows[i].pop(j, F(0))
            if not factor:
                continue
            for k, a in rows[j].items():
                if k > j:
                    value = rows[i].get(k, F(0)) - factor * a
                    if value:
                        rows[i][k] = value
                    else:
                        rows[i].pop(k, None)
            right[i] -= factor * right[j]
    values = [F(0)] * n
    for j in reversed(range(n)):
        values[j] = right[j] - sum((a * values[k] for k, a in rows[j].items() if k > j), F(0))
    return values


def warm_exact_truth(chain, payload):
    """Analytic active systems; all acceptance still uses the full original LP."""
    kind = chain["metadata"]["kind"]
    if kind not in ("RHS", "BOUND") or (kind == "BOUND" and chain["recipe"]["family"] != "GENERAL"):
        return None
    active = list(chain["candidate"]["point"])
    positions = {name: i for i, name in enumerate(active)}
    caps = {r["name"]: r for r in payload["constraints"]}
    labels = list(chain["candidate"]["row_duals"])
    matrix = [
        {
            positions[name]: q(a)
            for name, a in caps[label]["coefficients"].items()
            if name in positions
        }
        for label in labels
    ]
    rhs = [q(row_bounds(caps[label])[1]) for label in labels]
    if kind == "BOUND":
        controlled = active[0]
        bound = next(v["upper"] for v in payload["variables"] if v["name"] == controlled)
        matrix[0], rhs[0] = {0: F(1)}, q(bound)
    values = _fraction_solve(matrix, rhs)
    point = dict(zip(active, values, strict=True))
    if kind == "RHS":
        duals = {name: F(value) for name, value in chain["candidate"]["row_duals"].items()}
    else:
        transpose = [
            {i: row[j] for i, row in enumerate(matrix) if j in row} for j in range(len(active))
        ]
        dual_values = _fraction_solve(
            transpose, [q(payload["objective"]["coefficients"].get(name, 0)) for name in active]
        )
        duals = {name: value for name, value in zip(labels[1:], dual_values[1:], strict=True)}
    truth = primal_dual_pair(payload, {"point": point, "row_duals": duals})
    truth["derivation"] = {
        "kind": "exact_raw_active_cap_system"
        if kind == "RHS"
        else "exact_cap_system_with_original_upper_bound",
        "positive_coordinates": active,
        "linear_equations": len(active),
        "proposed_active_rows": labels if kind == "RHS" else labels[1:],
        "solver_optimization_calls": 0,
    }
    return truth


REFERENCE_POLICY = {
    "model_space": (
        "all original binary-float coefficients, row sides, variable bounds, sense and constant"
    ),
    "kkt_scaled_tolerance": 1e-8,
    "primal_scale": "1 + abs(side) + sum(abs(a_j*x_j))",
    "stationarity_scale": "1 + abs(c_j) + sum(abs(a_ij*y_i)) + abs(z_lower) + abs(z_upper)",
    "complementarity_scale": "1 + abs(normalized_primal) + abs(normalized_dual)",
    "objective_gap_scale": "1 + max(abs(normalized_primal), abs(normalized_dual))",
    "dual_sign_scale": "1 + abs(multiplier)",
    "highs_primal_feasibility_tolerance": 1e-9,
    "highs_dual_feasibility_tolerance": 1e-9,
    "highs_threads": 1,
    "highs_method": "highs-ds",
    "single_call_wall_seconds": 120,
    "batch_wall_seconds": 500,
    "exact_checks": (
        "Fraction(int/actual float), zero tolerance; "
        "integer slices compactness proved from raw sides"
    ),
}


def reference_lp(payload, time_limit=115):
    """Explicit single-thread independent comparison; never imported by SILO."""
    import numpy as np
    from scipy.optimize import linprog
    from scipy.sparse import coo_matrix

    names = [v["name"] for v in payload["variables"]]
    positions = {n: j for j, n in enumerate(names)}
    eq, ub, eq_rhs, ub_rhs, eq_sources, ub_sources = [], [], [], [], [], []
    for r in payload["constraints"]:
        lower, upper = row_bounds(r)
        if lower is not None and upper is not None and lower == upper:
            eq.append(r["coefficients"])
            eq_rhs.append(lower)
            eq_sources.append(r["name"])
        else:
            if upper is not None:
                ub.append(r["coefficients"])
                ub_rhs.append(upper)
                ub_sources.append((r["name"], "upper"))
            if lower is not None:
                ub.append({n: -a for n, a in r["coefficients"].items()})
                ub_rhs.append(-lower)
                ub_sources.append((r["name"], "lower"))

    def sparse(rows):
        rr, cc, vv = [], [], []
        for i, coefficients in enumerate(rows):
            for n, a in coefficients.items():
                rr.append(i)
                cc.append(positions[n])
                vv.append(a)
        return coo_matrix((vv, (rr, cc)), shape=(len(rows), len(names))).tocsr()

    sign = 1 if payload["sense"] == "minimize" else -1
    c = sign * np.array([payload["objective"]["coefficients"].get(n, 0) for n in names])
    options = {
        "time_limit": time_limit,
        "threads": 1,
        "parallel": False,
        "primal_feasibility_tolerance": 1e-9,
        "dual_feasibility_tolerance": 1e-9,
    }
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        result = linprog(
            c,
            A_ub=sparse(ub) if ub else None,
            b_ub=ub_rhs if ub else None,
            A_eq=sparse(eq) if eq else None,
            b_eq=eq_rhs if eq else None,
            bounds=[(v.get("lower", 0), v.get("upper")) for v in payload["variables"]],
            method="highs-ds",
            options=options,
        )
    return result, {
        "names": names,
        "sense_sign": sign,
        "constant": payload["objective"].get("constant", 0),
        "eq_sources": eq_sources,
        "ub_sources": ub_sources,
        "options": options,
        "warnings": [str(w.message) for w in caught],
    }


def original_kkt(payload, result, metadata):
    """Recompute KKT from untouched original coefficients, independently of SciPy residuals."""
    if result["status"] != 0 or not result["success"]:
        raise ValueError(f"Independent reference is not optimal: {result['message']}")
    names, sign = metadata["names"], metadata["sense_sign"]
    point = dict(zip(names, map(float, result["x"]), strict=True))
    if not all(math.isfinite(v) for v in point.values()):
        raise ValueError("Nonfinite numerical reference point")
    sides = {
        r["name"]: {"lower": 0.0, "upper": 0.0, "equality": 0.0} for r in payload["constraints"]
    }
    for name, value in zip(metadata["eq_sources"], result["eqlin"]["marginals"], strict=True):
        sides[name]["equality"] = float(value)
    for (name, side), value in zip(
        metadata["ub_sources"], result["ineqlin"]["marginals"], strict=True
    ):
        sides[name][side] = float(value) * (-1 if side == "lower" else 1)
    lower_duals = dict(zip(names, map(float, result["lower"]["marginals"]), strict=True))
    upper_duals = dict(zip(names, map(float, result["upper"]["marginals"]), strict=True))
    all_duals = [
        *lower_duals.values(),
        *upper_duals.values(),
        *(v for row in sides.values() for v in row.values()),
    ]
    if not all(math.isfinite(v) for v in all_duals):
        raise ValueError("Nonfinite numerical reference dual")
    metrics = {}

    def observe(kind, value, scale, label):
        absolute, scaled = abs(value), abs(value) / scale
        metric = metrics.setdefault(
            kind, {"max_absolute": 0.0, "max_scaled": 0.0, "worst_scaled_at": None}
        )
        metric["max_absolute"] = max(metric["max_absolute"], absolute)
        if scaled >= metric["max_scaled"]:
            metric["max_scaled"], metric["worst_scaled_at"] = scaled, label

    contributions = {name: [] for name in names}
    dual_parts = [sign * float(payload["objective"].get("constant", 0))]
    complementarity = []
    for row in payload["constraints"]:
        name, coefficients = row["name"], row["coefficients"]
        terms = [float(a) * point[n] for n, a in coefficients.items()]
        activity = math.fsum(terms)
        magnitude = math.fsum(map(abs, terms))
        lower, upper = row_bounds(row)
        y = math.fsum(sides[name].values())
        for n, a in coefficients.items():
            contributions[n].append(float(a) * y)
        if lower is not None:
            observe(
                "primal",
                max(float(lower) - activity, 0),
                1 + abs(float(lower)) + magnitude,
                name + ":lower",
            )
        if upper is not None:
            observe(
                "primal",
                max(activity - float(upper), 0),
                1 + abs(float(upper)) + magnitude,
                name + ":upper",
            )
        if sides[name]["equality"]:
            if lower is None or upper is None or lower != upper:
                raise ValueError("Reference equality multiplier on non-equality row")
            dual_parts.append(sides[name]["equality"] * float(lower))
            complementarity.append((sides[name]["equality"] * (activity - float(lower)), name))
        for side, bound in (("lower", lower), ("upper", upper)):
            multiplier = sides[name][side]
            if bound is None:
                if multiplier:
                    raise ValueError("Reference row multiplier on absent side")
                continue
            observe(
                "dual_sign",
                max(-multiplier if side == "lower" else multiplier, 0),
                1 + abs(multiplier),
                name + ":" + side,
            )
            dual_parts.append(multiplier * float(bound))
            complementarity.append((multiplier * (activity - float(bound)), name + ":" + side))
    for var in payload["variables"]:
        name, x = var["name"], point[var["name"]]
        for side, multiplier in (("lower", lower_duals[name]), ("upper", upper_duals[name])):
            bound = var.get(side, 0 if side == "lower" else None)
            if bound is None:
                if multiplier:
                    raise ValueError("Reference bound multiplier on absent side")
                continue
            violation = max(float(bound) - x if side == "lower" else x - float(bound), 0)
            observe("primal", violation, 1 + abs(float(bound)) + abs(x), name + ":" + side)
            observe(
                "dual_sign",
                max(-multiplier if side == "lower" else multiplier, 0),
                1 + abs(multiplier),
                name + ":" + side,
            )
            dual_parts.append(multiplier * float(bound))
            complementarity.append((multiplier * (x - float(bound)), name + ":" + side))
        cost = sign * float(payload["objective"]["coefficients"].get(name, 0))
        observe(
            "stationarity",
            math.fsum(
                [cost, -lower_duals[name], -upper_duals[name], *(-v for v in contributions[name])]
            ),
            1
            + abs(cost)
            + abs(lower_duals[name])
            + abs(upper_duals[name])
            + math.fsum(map(abs, contributions[name])),
            name,
        )
    p = sign * math.fsum(
        [
            float(payload["objective"].get("constant", 0)),
            *(float(a) * point[n] for n, a in payload["objective"]["coefficients"].items()),
        ]
    )
    d = math.fsum(dual_parts)
    for value, label in complementarity:
        observe("complementarity", value, 1 + abs(p) + abs(d), label)
    observe("objective_gap", p - d, 1 + max(abs(p), abs(d)), "original P-D")
    reported = float(result["fun"]) + sign * float(payload["objective"].get("constant", 0))
    observe(
        "reported_objective", p - reported, 1 + abs(p), "original P versus normalized solver fun"
    )
    tolerance = REFERENCE_POLICY["kkt_scaled_tolerance"]
    passed = all(m["max_scaled"] <= tolerance for m in metrics.values())
    return {
        "status": "optimal",
        "kind": "independent_highs_original_model_kkt",
        "objective": sign * p,
        "normalized_primal_objective": p,
        "normalized_dual_objective": d,
        "point": point,
        "row_side_duals": sides,
        "row_duals": {n: math.fsum(v.values()) for n, v in sides.items()},
        "variable_lower_duals": lower_duals,
        "variable_upper_duals": upper_duals,
        "kkt": {
            "passed": passed,
            "tolerance": tolerance,
            "metrics": metrics,
            "original_rows_checked": len(payload["constraints"]),
            "original_columns_checked": len(payload["variables"]),
            "objective_sense": payload["sense"],
            "original_constant": payload["objective"].get("constant", 0),
        },
    }


def _json_safe(value):
    if hasattr(value, "tolist"):
        return _json_safe(value.tolist())
    if isinstance(value, dict):
        return {str(n): _json_safe(v) for n, v in value.items()}
    if isinstance(value, list | tuple):
        return [_json_safe(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return "NaN" if math.isnan(value) else "Infinity" if value > 0 else "-Infinity"
    return value


def _bytes(value):
    return (
        json.dumps(_json_safe(value), sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _write(path, value):
    path.write_bytes(_bytes(value))


def _utc():
    return datetime.now(UTC).isoformat()


def _environment():
    import numpy
    import scipy
    from scipy.optimize._highspy._core import _Highs

    return {
        "python": sys.version,
        "executable": sys.executable,
        "platform": platform.platform(),
        "numpy": numpy.__version__,
        "scipy": scipy.__version__,
        "highs": _Highs().version(),
        "reference_module_sha256": _digest(Path(__file__).read_bytes()),
    }


def verify_frozen_inputs(root, frozen_commit):
    """Pure read/rebuild guard: never creates or rewrites a frozen input file."""
    from .cases import apply_edit, build_cases, build_trajectories, sha

    root = Path(root)
    manifest_path = root / "tests/fixtures/sparse_program_manifest.json"
    sources_path = root / "tests/fixtures/sparse_program_sources.json"
    manifest_bytes, source_bytes = manifest_path.read_bytes(), sources_path.read_bytes()
    for relative, current in (
        ("tests/fixtures/sparse_program_manifest.json", manifest_bytes),
        ("tests/fixtures/sparse_program_sources.json", source_bytes),
    ):
        frozen = subprocess.run(
            ["git", "show", f"{frozen_commit}:{relative}"],
            cwd=root,
            check=True,
            capture_output=True,
        ).stdout
        if frozen != current:
            raise ValueError(f"Frozen commit identity differs: {relative}")
    manifest = json.loads(manifest_bytes)
    cases = {item["id"]: item for item in build_cases(include_external=True, root=root)}
    chains = {item["id"]: item for item in build_trajectories()}
    if set(cases) != {item["id"] for item in manifest["cases"]}:
        raise ValueError("Frozen ordinary case ID set differs")
    if set(chains) != {item["id"] for item in manifest["trajectories"]}:
        raise ValueError("Frozen warm chain ID set differs")
    checked = []

    def check(identifier, path, expected, rebuilt):
        raw = (root / path).read_bytes()
        if _digest(raw) != expected or sha(rebuilt) != expected or sha(json.loads(raw)) != expected:
            raise ValueError(f"Frozen payload SHA mismatch: {identifier}")
        checked.append({"id": identifier, "payload_sha256": expected, "payload_path": path})

    for record in manifest["cases"]:
        item = cases[record["id"]]
        check(record["id"], record["payload_path"], record["payload_sha256"], item["payload"])
        if "candidate_sha256" in record and sha(item["candidate"]) != record["candidate_sha256"]:
            raise ValueError(f"Frozen candidate SHA mismatch: {record['id']}")
        for key in ("pool", "recipe", "options", "expected_statuses", "metadata"):
            if item.get(key) != record.get(key):
                raise ValueError(f"Frozen case metadata differs: {record['id']}:{key}")
    for record in manifest["trajectories"]:
        item = chains[record["id"]]
        payload = item["initial_payload"]
        check(record["id"] + "-initial", record["initial_path"], record["initial_sha256"], payload)
        if len(item["edits"]) != len(record["states"]) or len(record["states"]) != 20:
            raise ValueError("Frozen warm state count differs")
        for state, edit in zip(record["states"], item["edits"], strict=True):
            if state["edit"] != edit:
                raise ValueError(f"Frozen edit differs: {state['id']}")
            payload = apply_edit(payload, edit)
            check(state["id"], state["payload_path"], state["payload_sha256"], payload)
    return (
        manifest,
        cases,
        chains,
        {
            "manifest_sha256": _digest(manifest_bytes),
            "sources_sha256": _digest(source_bytes),
            "checked_payloads": checked,
            "count": len(checked),
        },
    )


def _kkt_selfcheck():
    """Known raw minimization/maximization KKT pairs plus a deliberate bad point."""
    payload = {
        "sense": "minimize",
        "variables": [{"name": "x", "lower": -1, "upper": 2}],
        "constraints": [{"name": "r", "coefficients": {"x": 1}, "lower": 0.5, "upper": 1}],
        "objective": {"constant": 3, "coefficients": {"x": -1}},
    }
    result = {
        "status": 0,
        "success": True,
        "x": [1],
        "fun": -1,
        "eqlin": {"marginals": []},
        "ineqlin": {"marginals": [-1, 0]},
        "lower": {"marginals": [0]},
        "upper": {"marginals": [0]},
    }
    metadata = {
        "names": ["x"],
        "sense_sign": 1,
        "eq_sources": [],
        "ub_sources": [("r", "upper"), ("r", "lower")],
    }
    if not original_kkt(payload, result, metadata)["kkt"]["passed"]:
        raise ValueError("Numerical KKT selfcheck failed on known minimization pair")
    payload["sense"], payload["objective"]["coefficients"]["x"] = "maximize", 1
    metadata["sense_sign"] = -1
    if not original_kkt(payload, result, metadata)["kkt"]["passed"]:
        raise ValueError("Numerical KKT selfcheck failed on known maximization pair")
    result["x"], result["fun"] = [1.125], -1.125
    if original_kkt(payload, result, metadata)["kkt"]["passed"]:
        raise ValueError("Numerical KKT selfcheck accepted an infeasible point")


def _numeric_worker(request_path, result_path):
    """One independently timed child, bounded by the sequential parent watchdog."""
    for name in (
        "OMP_NUM_THREADS",
        "OPENBLAS_NUM_THREADS",
        "MKL_NUM_THREADS",
        "VECLIB_MAXIMUM_THREADS",
        "NUMEXPR_NUM_THREADS",
    ):
        os.environ[name] = "1"
    request = json.loads(Path(request_path).read_bytes())
    record = {
        "id": request["id"],
        "payload_sha256": request["payload_sha256"],
        "started_utc": _utc(),
        "policy": REFERENCE_POLICY,
    }
    started = time.perf_counter()
    try:
        raw = Path(request["payload_path"]).read_bytes()
        if _digest(raw) != request["payload_sha256"]:
            raise ValueError("Reference child frozen payload SHA mismatch")
        payload = json.loads(raw)
        solve_started = time.perf_counter()
        result, metadata = reference_lp(payload, request["time_limit_seconds"])
        record.update(
            raw_result=_json_safe(dict(result)),
            metadata=metadata,
            optimization_seconds=time.perf_counter() - solve_started,
        )
        # Preserve the raw independent optimization even if the subsequent check fails.
        _write(Path(result_path), record)
        record["truth"] = original_kkt(payload, result, metadata)
        if not record["truth"]["kkt"]["passed"]:
            raise ValueError("Independent reference failed frozen original-model KKT policy")
        record["status"] = "passed"
    except Exception as error:
        record.update(status="failed", error=f"{type(error).__name__}: {error}")
    record.update(finished_utc=_utc(), child_wall_seconds=time.perf_counter() - started)
    _write(Path(result_path), record)
    return 0 if record["status"] == "passed" else 2


def export_references(
    root=None, frozen_commit="a3cff29ca9311f7bdab03105405b29cc11f81b9b", total_seconds=500
):
    """Freeze exact and independent numerical truth; stop at the first failed reference.

    The committed fixture is a scalar index. Complete raw points, duals, integer
    slices and independent optimization results live in ignored reference files,
    with byte hashes in every index entry. No frozen input or shared ledger write.
    """
    from .cases import ROOT

    root = ROOT if root is None else Path(root)
    started, started_utc = time.perf_counter(), _utc()
    folder = root / "outputs/sparse_lp_program_20261024/reference/frozen_a3cff29_truth_v1"
    folder.mkdir(parents=True, exist_ok=False)
    events_path = folder / "events.jsonl"
    events = []
    index = {
        "schema": 1,
        "program": "SILO-SPARSE-LP-20261024",
        "frozen_commit": frozen_commit,
        "started_utc": started_utc,
        "cases": {},
        "trajectories": {},
        "verification_policy": REFERENCE_POLICY,
        "status": "running",
    }
    optimization_calls = []

    def remaining():
        value = total_seconds - (time.perf_counter() - started)
        if value <= 0:
            raise TimeoutError("Independent reference batch wall budget exhausted")
        return value

    def event(record):
        events.append(record)
        with events_path.open("ab") as stream:
            stream.write(_bytes(record))

    def save_index():
        _write(folder / "partial_index.json", index)

    def compact(witness, payload_sha256, path):
        truth = witness["truth"]
        scalar = {
            key: truth[key]
            for key in ("status", "kind", "objective", "objective_exact")
            if key in truth
        }
        if "kkt" in truth:
            scalar["kkt_passed"] = truth["kkt"]["passed"]
            scalar["max_kkt_scaled_error"] = max(
                value["max_scaled"] for value in truth["kkt"]["metrics"].values()
            )
        return {
            "payload_sha256": payload_sha256,
            "truth": scalar,
            "witness_path": path.relative_to(root).as_posix(),
            "witness_sha256": _digest(path.read_bytes()),
        }

    def exact_record(identifier, payload_sha256, payload, compute, pool_payload=None):
        remaining()
        path = folder / (identifier + ".json")
        begin = time.perf_counter()
        event({"id": identifier, "kind": "exact_fraction", "event": "started", "utc": _utc()})
        truth = compute()
        record = {
            "id": identifier,
            "payload_sha256": payload_sha256,
            "truth": truth,
            "method": "exact_original_binary_fraction",
            "solver_optimization_calls": 0,
            "all_original_rows": len(payload["constraints"]),
            "all_original_variables": len(payload["variables"]),
        }
        if pool_payload is not None:
            record["full_pool_payload_sha256"] = _digest(_bytes(pool_payload))
            record["full_pool_payload"] = pool_payload
        _write(path, record)
        event(
            {
                "id": identifier,
                "kind": "exact_fraction",
                "event": "completed",
                "utc": _utc(),
                "wall_seconds": time.perf_counter() - begin,
            }
        )
        return compact(record, payload_sha256, path)

    def numeric_record(identifier, payload_path, payload_sha256):
        available = remaining()
        if available < 5:
            raise TimeoutError("Insufficient remaining reference batch budget for a new call")
        path = folder / (identifier + ".json")
        request_path = folder / (identifier + ".request.json")
        wall_limit = min(120.0, available)
        request = {
            "id": identifier,
            "payload_path": str(root / payload_path),
            "payload_sha256": payload_sha256,
            "time_limit_seconds": max(0.1, min(115.0, wall_limit - 3.0)),
        }
        _write(request_path, request)
        begin = time.perf_counter()
        call = {
            "id": identifier,
            "kind": "independent_highs",
            "started_utc": _utc(),
            "payload_sha256": payload_sha256,
            "wall_limit_seconds": wall_limit,
        }
        optimization_calls.append(call)
        event({**call, "event": "started"})
        command = [
            sys.executable,
            "-m",
            "scripts.sparse_program.oracles",
            "_numeric",
            str(request_path),
            str(path),
        ]
        try:
            completed = subprocess.run(
                command, cwd=root, capture_output=True, text=True, timeout=wall_limit, check=False
            )
            call.update(
                exit_code=completed.returncode, stdout=completed.stdout, stderr=completed.stderr
            )
        except subprocess.TimeoutExpired as error:
            call.update(
                exit_code=None, timeout=True, stdout=str(error.stdout), stderr=str(error.stderr)
            )
        call.update(finished_utc=_utc(), wall_seconds=time.perf_counter() - begin, command=command)
        _write(folder / (identifier + ".call.json"), call)
        event({**call, "event": "completed"})
        if call.get("exit_code") != 0 or not path.exists():
            raise ValueError(f"Independent reference child failed: {identifier}; see {path}")
        record = json.loads(path.read_bytes())
        if record.get("status") != "passed" or not record["truth"]["kkt"]["passed"]:
            raise ValueError(f"Independent original-model reference failed: {identifier}")
        return compact(record, payload_sha256, path)

    try:
        _kkt_selfcheck()
        manifest, cases, chains, identity = verify_frozen_inputs(root, frozen_commit)
        _write(folder / "frozen_identity.json", identity)
        index.update(
            manifest_sha256=identity["manifest_sha256"],
            sources_sha256=identity["sources_sha256"],
            environment=_environment(),
        )
        for record in manifest["cases"]:
            case = cases[record["id"]]
            if case["group"] == "netlib":
                continue
            pool = full_pool_payload(case) if case["group"] == "cg" else None
            index["cases"][case["id"]] = exact_record(
                case["id"],
                record["payload_sha256"],
                case["payload"],
                lambda item=case: exact_truth(item, retain_proof=True),
                pool,
            )
        save_index()
        for record in manifest["cases"]:
            if record["group"] == "netlib":
                index["cases"][record["id"]] = numeric_record(
                    record["id"], record["payload_path"], record["payload_sha256"]
                )
                save_index()
        for record in manifest["trajectories"]:
            chain = chains[record["id"]]
            initial = exact_record(
                record["id"] + "-initial",
                record["initial_sha256"],
                chain["initial_payload"],
                lambda item=chain: primal_dual_pair(item["initial_payload"], item["candidate"]),
            )
            states = {}
            index["trajectories"][record["id"]] = {"initial": initial, "states": states}
            analytic = chain["metadata"]["kind"] == "RHS" or (
                chain["metadata"]["kind"] == "BOUND" and chain["recipe"]["family"] == "GENERAL"
            )
            for state in record["states"]:
                if analytic:
                    payload = json.loads((root / state["payload_path"]).read_bytes())
                    states[state["id"]] = exact_record(
                        state["id"],
                        state["payload_sha256"],
                        payload,
                        lambda item=chain, p=payload: warm_exact_truth(item, p),
                    )
                else:
                    states[state["id"]] = numeric_record(
                        state["id"], state["payload_path"], state["payload_sha256"]
                    )
            save_index()
        # Final read-only guard detects any concurrent frozen-input mutation.
        verify_frozen_inputs(root, frozen_commit)
        index["status"] = "passed"
    except Exception as error:
        index.update(status="failed", error=f"{type(error).__name__}: {error}")
    index.update(
        finished_utc=_utc(),
        accounting={
            "wall_seconds": time.perf_counter() - started,
            "external_optimization_calls": len(optimization_calls),
            "native_solver_calls": 0,
            "external_call_wall_seconds": math.fsum(
                call.get("wall_seconds", 0) for call in optimization_calls
            ),
            "exact_fraction_records": sum(
                e.get("event") == "completed" and e.get("kind") == "exact_fraction" for e in events
            ),
            "external_child_optimization_seconds": math.fsum(
                json.loads((folder / (call["id"] + ".json")).read_bytes()).get(
                    "optimization_seconds", 0
                )
                for call in optimization_calls
                if (folder / (call["id"] + ".json")).exists()
            ),
            "wall_budget_seconds": total_seconds,
        },
    )
    save_index()
    _write(folder / "export_receipt.json", index)
    if index["status"] != "passed":
        raise ValueError(f"Reference export stopped: {index.get('error')}; receipts: {folder}")
    target = root / "tests/fixtures/sparse_program_oracles.json"
    if target.exists():
        raise ValueError("Existing oracle fixture must not be overwritten")
    _write(target, index)
    return index


if __name__ == "__main__":
    if len(sys.argv) == 4 and sys.argv[1] == "_numeric":
        raise SystemExit(_numeric_worker(sys.argv[2], sys.argv[3]))
    if len(sys.argv) == 2 and sys.argv[1] == "export":
        exported = export_references()
        print(json.dumps({"status": exported["status"], "accounting": exported["accounting"]}))
    else:
        raise SystemExit("Use: python -m scripts.sparse_program.oracles export")
