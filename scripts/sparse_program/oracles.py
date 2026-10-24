"""Independent raw-input truth and checks; no SILO production imports.

Every coefficient is converted to Fraction before arithmetic, preserving actual
binary float inputs. Small LPs use bounded exact vertex enumeration plus an exact
dual certificate; small MILPs exhaust the integer box. Constructed large witnesses
are proposals until every original side and dual inequality is checked.
The optional HiGHS comparison is invoked only by an explicit reference function.
"""

import itertools
import math
from fractions import Fraction as F


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
        "point": {n: str(v) for n, v in point.items() if v},
        "row_duals": {n: str(v) for n, v in duals.items() if v},
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
    return {
        "status": "optimal",
        "objective_exact": str(sign * best),
        "objective": float(sign * best),
        "point": {name: str(value) for name, value in point.items()},
        "inequality_signed_duals": certificate,
        "kind": "exact_original_binary_vertex_enumeration",
        "active_sets_checked": checked,
    }


def integer_truth(payload, assignment_cap=2_000_000):
    integer = [v for v in payload["variables"] if v.get("type", "continuous") != "continuous"]
    domains = []
    for v in integer:
        if v.get("lower", 0) is None or v.get("upper") is None:
            raise ValueError("Independent integer enumeration needs a finite original box")
        domains.append(range(math.ceil(q(v.get("lower", 0))), math.floor(q(v["upper"])) + 1))
    count = math.prod(map(len, domains))
    if count > assignment_cap:
        raise ValueError("Independent integer assignment budget")
    sign, best, found, total_vertices = (1 if payload["sense"] == "minimize" else -1), None, None, 0
    for values in itertools.product(*domains):
        fixed = dict(zip((v["name"] for v in integer), map(F, values), strict=True))
        reference = vertex_truth(payload, fixed)
        total_vertices += reference["active_sets_checked"]
        if reference["status"] == "optimal":
            value = F(reference["objective_exact"])
            if best is None or sign * value < sign * best:
                best, found = value, reference["point"]
    return {
        "status": "infeasible" if best is None else "optimal",
        "kind": "exact_integer_box_and_continuous_vertices",
        "objective_exact": None if best is None else str(best),
        "objective": None if best is None else float(best),
        "point": found,
        "integer_assignments": count,
        "active_sets_checked": total_vertices,
    }


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


def exact_truth(case):
    p = case["payload"]
    if case["group"] == "cg":
        p = full_pool_payload(case)
        if case["id"] == "CG-UNBOUNDED-GUARD":
            return point_ray(
                p, {"point": {"a": 0, "b": 1, "c": 0}, "ray": {"a": 1, "b": 0, "c": 1}}
            )
        return vertex_truth(p)
    if case["group"] == "mip":
        return integer_truth(p)
    if case["group"] in ("capacity", "mechanism"):
        return primal_dual_pair(p, case["candidate"])
    if case["id"].startswith("PRESS-INF"):
        return farkas(p, case["candidate"])
    if case["id"].startswith("PRESS-UNB"):
        return point_ray(p, case["candidate"])
    if case["id"].startswith("PRESS-LIMIT"):
        return {"status": "optimal", "kind": "underlying_math_unlimited", **vertex_truth(p)}
    return vertex_truth(p)


def reference_lp(payload):
    """Explicit optional comparison call; caller freezes input and accounts timing."""
    import numpy as np
    from scipy.optimize import linprog
    from scipy.sparse import coo_matrix

    names = [v["name"] for v in payload["variables"]]
    positions = {n: j for j, n in enumerate(names)}
    eq, ub, eq_rhs, ub_rhs = [], [], [], []
    for r in payload["constraints"]:
        lower, upper = row_bounds(r)
        if lower is not None and upper is not None and lower == upper:
            eq.append(r["coefficients"])
            eq_rhs.append(lower)
        else:
            if upper is not None:
                ub.append(r["coefficients"])
                ub_rhs.append(upper)
            if lower is not None:
                ub.append({n: -a for n, a in r["coefficients"].items()})
                ub_rhs.append(-lower)

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
    result = linprog(
        c,
        A_ub=sparse(ub) if ub else None,
        b_ub=ub_rhs if ub else None,
        A_eq=sparse(eq) if eq else None,
        b_eq=eq_rhs if eq else None,
        bounds=[(v.get("lower", 0), v.get("upper")) for v in payload["variables"]],
        method="highs",
        options={"time_limit": 120},
    )
    return result, {
        "names": names,
        "sense_sign": sign,
        "constant": payload["objective"].get("constant", 0),
    }
