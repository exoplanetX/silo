"""Independent original-payload semantics. No production imports or tolerances.

Finite numbers mean their actual binary rational values, not a decimal guess.
Rows are compared by original named finite sides; LP interval names use the
frozen collision-avoiding mapping below. Zero entries do not erase variables.
"""

from fractions import Fraction
from math import isfinite


def scalar(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int | float) or not isfinite(value):
        raise ValueError("expected finite scalar or null infinite side")
    q = Fraction(value)
    return (q.numerator, q.denominator)


def bounds(row):
    if "lower" in row or "upper" in row:
        return row.get("lower"), row.get("upper")
    sense, rhs = row.get("sense", "<="), row.get("rhs", 0)
    return (None, rhs) if sense == "<=" else (rhs, None) if sense == ">=" else (rhs, rhs)


def split_names(payload):
    used = {v["name"] for v in payload["variables"]}
    used.update(r["name"] for r in payload.get("constraints", []))
    result = {}
    for row in payload.get("constraints", []):
        lo, hi = bounds(row)
        if lo is not None and hi is not None and lo != hi:
            for side in ("lower", "upper"):
                base = row["name"] + "__" + side
                name, index = base, 1
                while name in used:
                    name = f"{base}_{index}"
                    index += 1
                used.add(name)
                result[(row["name"], side)] = name
        else:
            result[(row["name"], "single")] = row["name"]
    return result


def signature(payload, *, lp_sides=False):
    variables = []
    for v in payload["variables"]:
        lo, hi = v.get("lower", 0), v.get("upper")
        typ = v.get("type", "continuous")
        # Binary and integer [0,1] have the same mathematical lattice.
        if typ == "binary":
            lo = max(0, lo) if lo is not None else 0
            hi = min(1, hi) if hi is not None else 1
            typ = "integer"
        variables.append((v["name"], scalar(lo), scalar(hi), typ))
    objective = payload.get("objective", {})
    def coeff(data):
        return tuple(sorted((k, scalar(v)) for k, v in data.items() if v != 0))
    names = split_names(payload)
    rows = []
    for r in payload.get("constraints", []):
        lo, hi = bounds(r)
        c = coeff(r.get("coefficients", {}))
        if lp_sides and lo is not None and hi is not None and lo != hi:
            rows.extend([(names[(r["name"], "lower")], c, scalar(lo), None),
                         (names[(r["name"], "upper")], c, None, scalar(hi))])
        else:
            rows.append((r["name"], c, scalar(lo), scalar(hi)))
    return (payload.get("sense", "minimize"), scalar(objective.get("constant", 0)),
            coeff(objective.get("coefficients", {})), tuple(sorted(variables)), tuple(sorted(rows)))


def equivalent(expected, actual, *, lp=False):
    if signature(expected, lp_sides=lp) != signature(actual):
        raise AssertionError("exact format semantics differ")
