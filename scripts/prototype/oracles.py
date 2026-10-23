"""Independent exact small-model truth. No production imports or transformations.

All arithmetic uses the input's decimal rationals. Vertex enumeration is used only
for pointed models with attained optima; the frozen lineality example has a
separate constructive primal/dual argument. This is deliberately slow and small.
"""

import itertools
import math
from fractions import Fraction as F


def rational(value):
    return F(str(value))


def row_sides(row):
    if "lower" in row or "upper" in row:
        return row.get("lower"), row.get("upper")
    return (
        (None, row["rhs"])
        if row["sense"] == "<="
        else (row["rhs"], None)
        if row["sense"] == ">="
        else (row["rhs"], row["rhs"])
    )


def equations(matrix, rhs):
    """Unique square rational solve; singular bases return None."""
    n = len(rhs)
    a = [list(r) + [b] for r, b in zip(matrix, rhs, strict=True)]
    for k in range(n):
        pivot = next((i for i in range(k, n) if a[i][k]), None)
        if pivot is None:
            return None
        a[k], a[pivot] = a[pivot], a[k]
        scale = a[k][k]
        a[k] = [v / scale for v in a[k]]
        for i in range(n):
            if i != k:
                scale = a[i][k]
                a[i] = [v - scale * u for v, u in zip(a[i], a[k], strict=True)]
    return tuple(a[i][-1] for i in range(n))


def inequalities(payload, fixed):
    names = [v["name"] for v in payload["variables"] if v["name"] not in fixed]
    sides = []
    for r in payload["constraints"]:
        lower, upper = row_sides(r)
        offset = sum(rational(a) * fixed.get(k, 0) for k, a in r["coefficients"].items())
        coeff = tuple(rational(r["coefficients"].get(n, 0)) for n in names)
        if lower is not None:
            sides.append((tuple(-a for a in coeff), -rational(lower) + offset))
        if upper is not None:
            sides.append((coeff, rational(upper) - offset))
    for v in payload["variables"]:
        n = v["name"]
        for side, sign in (("lower", -1), ("upper", 1)):
            if v[side] is not None:
                if n in fixed:
                    coeff = (F(0),) * len(names)
                    bound = sign * (rational(v[side]) - fixed[n])
                else:
                    coeff = tuple(F(sign if k == n else 0) for k in names)
                    bound = sign * rational(v[side])
                sides.append((coeff, bound))
    return names, sides


def vertices(payload, fixed=None, operation_cap=2000000):
    fixed = {} if fixed is None else fixed
    names, sides = inequalities(payload, fixed)
    n = len(names)
    combinations = math.comb(len(sides), n)
    if combinations > operation_cap:
        raise ValueError("Exact oracle operation cap exceeded.")
    found = []
    for active in itertools.combinations(sides, n):
        point = equations([r for r, _ in active], [b for _, b in active])
        if point is None or any(
            sum(a * x for a, x in zip(r, point, strict=True)) > b for r, b in sides
        ):
            continue
        values = {**fixed, **dict(zip(names, point, strict=True))}
        objective = rational(payload["objective"]["constant"]) + sum(
            rational(c) * values[k] for k, c in payload["objective"]["coefficients"].items()
        )
        found.append((objective, values))
    return found, combinations


def exact_small(payload, suite, family, operation_cap=2000000):
    """Return independently computed exact objective and a feasible point."""
    if suite == "lp_small" and family in (8, 9):
        # Direct contradiction x>=2, x<=1; or the absent x column's improving ray.
        # Reordering, objective negation and coordinate translation preserve this.
        return {"status": "infeasible" if family == 8 else "unbounded", "operations": 1}
    if suite == "lp_small" and family == 11:
        names = [v["name"] for v in payload["variables"]]
        values = dict.fromkeys(names, F(0))
        r = payload["constraints"][0]
        pivot = next(n for n in names if r["coefficients"].get(n))
        values[pivot] = rational(r["rhs"]) / rational(r["coefficients"][pivot])
        # c is proportional to this equality; its multiplier proves optimality.
        ratio = rational(payload["objective"]["coefficients"][pivot]) / rational(
            r["coefficients"][pivot]
        )
        assert all(
            rational(payload["objective"]["coefficients"].get(n, 0))
            == ratio * rational(r["coefficients"].get(n, 0))
            for n in names
        )
        value = rational(payload["objective"]["constant"]) + ratio * rational(r["rhs"])
        return {"status": "optimal", "objective": value, "point": values, "operations": 1}
    discrete = [v for v in payload["variables"] if v["type"] != "continuous"]
    domains = []
    for v in discrete:
        if v["lower"] is None or v["upper"] is None:
            raise ValueError("Enumeration needs complete finite integer domains.")
        domain = range(math.ceil(rational(v["lower"])), math.floor(rational(v["upper"])) + 1)
        if len(domain) > 4:
            raise ValueError("Per-variable enumeration cap exceeded.")
        domains.append(domain)
    candidates = math.prod(map(len, domains))
    if candidates > 256:
        raise ValueError("Integer Cartesian-product cap exceeded.")
    if discrete and (
        len(payload["variables"]) - len(discrete) > 2 or len(payload["constraints"]) > 6
    ):
        raise ValueError("Continuous subproblem oracle domain exceeded.")
    best, operations = None, 0
    minimize = payload["sense"] == "minimize"
    for assignment in itertools.product(*domains):
        fixed = dict(zip([v["name"] for v in discrete], map(F, assignment), strict=True))
        found, count = vertices(payload, fixed, operation_cap - operations)
        operations += count
        for value, point in found:
            if best is None or (value < best[0] if minimize else value > best[0]):
                best = value, point
    return (
        {"status": "infeasible", "operations": operations}
        if best is None
        else {"status": "optimal", "objective": best[0], "point": best[1], "operations": operations}
    )
