"""Small, bounded rational oracle; no SILO, NumPy, or external optimizer.

LP optimality has a feasible rational vertex and nonnegative multipliers of
original <= sides with A.T lambda = -c. Infeasibility has Farkas multipliers.
Unboundedness requires a supplied, independently checked feasible anchor/ray.
MILP enumerates the complete finite integer lattice, solving each continuous
slice. Every rational basic arithmetic operation in the linear algebra is
metered, as are candidate bases and wall time.
"""

import itertools
import math
import time
from fractions import Fraction as F

from .exact import bounds


class Meter:
    def __init__(self):
        self.operations = 0
        self.bases = 0
        self.start = time.perf_counter()

    def check(self, bases=0, ops=0):
        self.bases += bases
        self.operations += ops
        if (self.bases > 20000 or self.operations > 2000000
                or time.perf_counter() - self.start > 30):
            raise RuntimeError("independent oracle budget exceeded")

    def add(self, a, b):
        self.check(ops=1)
        return a + b

    def mul(self, a, b):
        self.check(ops=1)
        return a * b

    def div(self, a, b):
        self.check(ops=1)
        return a / b

    def dot(self, a, b):
        result = F(0)
        for x, y in zip(a, b, strict=True):
            result = self.add(result, self.mul(x, y))
        return result


def system(payload):
    names = [v["name"] for v in payload["variables"]]
    sides = []
    for row in payload.get("constraints", []):
        a = [F(row.get("coefficients", {}).get(n, 0)) for n in names]
        lo, hi = bounds(row)
        if lo is not None:
            sides.append(([-x for x in a], -F(lo), row["name"] + ":lower"))
        if hi is not None:
            sides.append((a, F(hi), row["name"] + ":upper"))
    for i, v in enumerate(payload["variables"]):
        a = [F(int(j == i)) for j in range(len(names))]
        lo, hi = v.get("lower", 0), v.get("upper")
        if v.get("type") == "binary":
            lo, hi = max(0, lo or 0), min(1, 1 if hi is None else hi)
        if lo is not None:
            sides.append(([-x for x in a], -F(lo), v["name"] + ":lower"))
        if hi is not None:
            sides.append((a, F(hi), v["name"] + ":upper"))
    c = [F(payload.get("objective", {}).get("coefficients", {}).get(n, 0)) for n in names]
    sign = -1 if payload.get("sense") == "maximize" else 1
    return names, sides, [sign * x for x in c], sign


def linear(a, b, meter):
    """Exact square solve; None for rank deficient candidate."""
    n = len(b)
    matrix = [list(row) + [rhs] for row, rhs in zip(a, b, strict=True)]
    for j in range(n):
        pivot = next((i for i in range(j, n) if matrix[i][j]), None)
        if pivot is None:
            return None
        matrix[j], matrix[pivot] = matrix[pivot], matrix[j]
        scale = matrix[j][j]
        matrix[j] = [meter.div(x, scale) for x in matrix[j]]
        for i in range(n):
            if i != j and matrix[i][j]:
                scale = matrix[i][j]
                matrix[i] = [meter.add(x, -meter.mul(scale, y))
                             for x, y in zip(matrix[i], matrix[j], strict=True)]
    return [row[-1] for row in matrix]


def farkas(sides, n, meter):
    # An extreme normalized Farkas vector needs at most n+1 nonzero entries.
    for k in range(1, min(n + 1, len(sides)) + 1):
        for ids in itertools.combinations(range(len(sides)), k):
            meter.check(bases=1)
            equations = [[sides[i][0][j] for i in ids] for j in range(n)]
            equations.append([F(1)] * k)
            rhs = [F(0)] * n + [F(1)]
            for eq in itertools.combinations(range(n + 1), k):
                lam = linear([equations[j] for j in eq], [rhs[j] for j in eq], meter)
                if lam is None or any(x < 0 for x in lam):
                    continue
                if any(meter.dot(row, lam) != value
                       for row, value in zip(equations, rhs, strict=True)):
                    continue
                if meter.dot(lam, [sides[i][1] for i in ids]) < 0:
                    return {sides[i][2]: str(x) for i, x in zip(ids, lam, strict=True) if x}
    return None


def lp(sides, c, meter):
    n = len(c)
    if not n:
        return ({"status": "optimal", "x": [], "value": F(0), "dual": {}}
                if all(b >= 0 for _, b, _ in sides)
                else {"status": "infeasible", "farkas": farkas(sides, n, meter)})
    best = None
    for ids in itertools.combinations(range(len(sides)), n):
        meter.check(bases=1)
        x = linear([sides[i][0] for i in ids], [sides[i][1] for i in ids], meter)
        if x is None or any(meter.dot(a, x) > b for a, b, _ in sides):
            continue
        value = meter.dot(c, x)
        if best is None or value < best[0]:
            best = (value, x)
        lam = linear([[sides[i][0][j] for i in ids] for j in range(n)], [-v for v in c], meter)
        if lam is not None and all(v >= 0 for v in lam):
            return {"status": "optimal", "x": x, "value": value,
                    "dual": {sides[i][2]: str(v) for i, v in zip(ids, lam, strict=True) if v}}
    cert = farkas(sides, n, meter)
    if cert is not None:
        return {"status": "infeasible", "farkas": cert}
    raise ValueError("no exact optimum or infeasibility proof; supply checked unbounded witness")


def solve(payload, witness=None):
    meter = Meter()
    names, sides, c, sign = system(payload)
    constant = F(payload.get("objective", {}).get("constant", 0))
    integers = [i for i, v in enumerate(payload["variables"])
                if v.get("type", "continuous") != "continuous"]
    if witness is not None:
        if integers:
            raise ValueError("unbounded MILP outside frozen domain")
        anchor = [F(witness["anchor"][n]) for n in names]
        ray = [F(witness["ray"][n]) for n in names]
        assert all(meter.dot(a, anchor) <= b for a, b, _ in sides)
        assert all(meter.dot(a, ray) <= 0 for a, _, _ in sides)
        assert meter.dot(c, ray) < 0
        answer = {"status": "unbounded", "anchor": dict(zip(names, map(str, anchor), strict=True)),
                  "ray": dict(zip(names, map(str, ray), strict=True))}
    elif not integers:
        raw = lp(sides, c, meter)
        answer = encode(raw, names, constant, sign)
    else:
        continuous = [i for i in range(len(names)) if i not in integers]
        domains = []
        for i in integers:
            v = payload["variables"][i]
            lower, upper = v.get("lower", 0), v.get("upper")
            if v.get("type") == "binary":
                lower, upper = max(0, lower or 0), min(1, 1 if upper is None else upper)
            assert lower is not None and upper is not None
            domain = range(math.ceil(F(lower)), math.floor(F(upper)) + 1)
            assert len(domain) <= 5
            domains.append(domain)
        slices, best = [], None
        for values in itertools.product(*domains):
            fixed = dict(zip(integers, map(F, values), strict=True))
            shifted = [([a[j] for j in continuous],
                        meter.add(b, -meter.dot([a[j] for j in integers], list(fixed.values()))),
                        label)
                       for a, b, label in sides]
            raw = lp(shifted, [c[j] for j in continuous], meter)
            item = {"integer_assignment": {names[i]: str(v) for i, v in fixed.items()},
                    "status": raw["status"]}
            if raw["status"] == "optimal":
                x = [fixed.get(i, F(0)) for i in range(len(names))]
                for i, value in zip(continuous, raw["x"], strict=True):
                    x[i] = value
                value = meter.dot(c, x)
                item.update(value=str(sign * value + constant), dual=raw["dual"])
                if best is None or value < best[0]:
                    best = (value, x)
            else:
                assert raw.get("farkas")
                item["farkas"] = raw["farkas"]
            slices.append(item)
        if best is None:
            answer = {"status": "infeasible", "slices": slices}
        else:
            answer = {"status": "optimal", "objective": str(sign * best[0] + constant),
                      "point": dict(zip(names, map(str, best[1]), strict=True)), "slices": slices}
            relaxation = lp(sides, c, meter)
            answer["relaxation"] = encode(relaxation, names, constant, sign)
            answer["strict_fractional_gap"] = (
                relaxation["value"] < best[0] and
                any(relaxation["x"][i].denominator != 1 for i in integers))
    answer["meter"] = {"candidate_bases": meter.bases, "rational_operations": meter.operations,
                       "seconds": time.perf_counter() - meter.start}
    return answer


def encode(raw, names, constant, sign):
    if raw["status"] == "infeasible":
        assert raw.get("farkas")
        return raw
    return {"status": "optimal", "objective": str(sign * raw["value"] + constant),
            "point": dict(zip(names, map(str, raw["x"]), strict=True)), "dual": raw["dual"]}
