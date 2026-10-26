"""Original-space independent result checks; no production solver imports."""

from fractions import Fraction as F
from math import isfinite

from .exact import bounds

TOL = F(1e-7)


def dot(a, x):
    return sum((F(v) * x[n] for n, v in a.items()), F(0))


def check(payload, result, truth, *, branching=False):
    assert result["status"] == truth["status"], (result["status"], truth["status"])
    rows, variables = payload.get("constraints", []), payload["variables"]
    names = [v["name"] for v in variables]
    sign = -1 if payload.get("sense") == "maximize" else 1
    integer = any(v.get("type", "continuous") != "continuous" for v in variables)
    if result["status"] == "infeasible":
        witness = result.get("witness") or {}
        if integer:
            assert witness.get("kind") in ("exhausted_integer_tree", "integer_domain")
            assert all(s["status"] == "infeasible" for s in truth["slices"])
            return {"integer_enumeration_proved": len(truth["slices"])}
        assert witness.get("kind") == "farkas" and witness.get("exact") is True
        sides = []
        for key, items, attr, direction in (
            ("row_lower", rows, "lower", 1), ("row_upper", rows, "upper", -1),
            ("variable_lower", variables, "lower", 1),
            ("variable_upper", variables, "upper", -1),
        ):
            multipliers = list(map(F, witness[key]))
            assert len(multipliers) == len(items)
            for item, multiplier in zip(items, multipliers, strict=True):
                assert multiplier >= 0
                if key.startswith("row"):
                    bound = bounds(item)[0 if attr == "lower" else 1]
                    coefficients = item.get("coefficients", {})
                else:
                    bound = item.get(attr, 0 if attr == "lower" else None)
                    coefficients = {item["name"]: 1}
                assert bound is not None or not multiplier
                sides.append((coefficients, bound, direction * multiplier))
        normal = {n: sum((weight * F(a.get(n, 0)) for a, _, weight in sides), F(0))
                  for n in names}
        contradiction = sum((weight * F(b) for _, b, weight in sides if b is not None), F(0))
        assert all(v == 0 for v in normal.values()) and contradiction > 0
        assert F(witness["contradiction"]) == contradiction
        return {"exact_farkas": True, "contradiction": str(contradiction)}
    if result["status"] == "unbounded":
        w = result["witness"]
        assert w["kind"] == "point_ray" and w["exact"] is True
        x, h = {n: F(w["point"][n]) for n in names}, {n: F(w["ray"][n]) for n in names}
        assert any(h.values())
        for v in variables:
            n = v["name"]
            lo, hi = v.get("lower", 0), v.get("upper")
            if lo is not None:
                assert x[n] >= F(lo) and h[n] >= 0
            if hi is not None:
                assert x[n] <= F(hi) and h[n] <= 0
        for row in rows:
            lo, hi = bounds(row)
            value, direction = dot(row["coefficients"], x), dot(row["coefficients"], h)
            if lo is not None:
                assert value >= F(lo) and direction >= 0
            if hi is not None:
                assert value <= F(hi) and direction <= 0
        improvement = sign * dot(payload["objective"].get("coefficients", {}), h)
        assert improvement < 0 and F(w["improvement"]) == improvement
        return {"exact_point_ray": True, "improvement": str(improvement)}
    assert result["status"] == "optimal"
    point = result["primal_values"]
    assert set(point) == set(names) and all(isfinite(v) for v in point.values())
    x = {n: F(point[n]) for n in names}
    max_primal = F(0)
    for v in variables:
        n = v["name"]
        for bound, direction in ((v.get("lower", 0), -1), (v.get("upper"), 1)):
            if bound is not None:
                residual = max(F(0), direction * (x[n] - F(bound)))
                ratio = residual / (1 + abs(x[n]) + abs(F(bound)))
                assert ratio <= TOL
                max_primal = max(max_primal, ratio)
        if v.get("type", "continuous") != "continuous":
            assert abs(x[n] - round(x[n])) <= TOL
    for row in rows:
        coefficients = row.get("coefficients", {})
        value = dot(coefficients, x)
        scale = 1 + sum((abs(F(c) * x[n]) for n, c in coefficients.items()), F(0))
        for bound, direction in zip(bounds(row), (-1, 1), strict=True):
            if bound is not None:
                ratio = max(F(0), direction * (value - F(bound))) / (scale + abs(F(bound)))
                assert ratio <= TOL
                max_primal = max(max_primal, ratio)
    objective = payload.get("objective", {})
    value = dot(objective.get("coefficients", {}), x) + F(objective.get("constant", 0))
    expected, actual = F(truth["objective"]), F(result["objective_value"])
    for a, b in ((value, actual), (actual, expected)):
        assert abs(a - b) <= TOL * (1 + abs(a) + abs(b))
    for key in ("primal_bound", "dual_bound"):
        assert result[key] is not None and isfinite(result[key])
        assert abs(F(result[key]) - expected) <= TOL * (1 + abs(expected) + abs(F(result[key])))
    assert result["absolute_gap"] == result["relative_gap"] == 0
    if integer:
        assert result["optimality"]["kind"] == "branch_and_bound"
        assert result["optimality"]["tree_exhausted"] is True
        if branching:
            assert result["diagnostics"]["branches"] > 0
        return {"primal_scaled": float(max_primal), "enumeration_objective": str(expected),
                "branches": result["diagnostics"].get("branches", 0)}
    multipliers = result["side_multipliers"]
    dual = sign * F(objective.get("constant", 0))
    stationarity = {n: sign * F(objective.get("coefficients", {}).get(n, 0)) for n in names}
    scales = {n: 1 + abs(F(objective.get("coefficients", {}).get(n, 0))) for n in names}
    max_complementarity = F(0)
    for key, items, attr, direction in (
        ("row_lower", rows, "lower", 1), ("row_upper", rows, "upper", -1),
        ("variable_lower", variables, "lower", 1),
        ("variable_upper", variables, "upper", -1),
    ):
        assert set(multipliers[key]) == {i["name"] for i in items}
        for item in items:
            lam = F(multipliers[key][item["name"]])
            assert lam >= -TOL * (1 + abs(lam))
            if key.startswith("row"):
                bound = bounds(item)[0 if attr == "lower" else 1]
                coefficients = item.get("coefficients", {})
            else:
                bound = item.get(attr, 0 if attr == "lower" else None)
                coefficients = {item["name"]: 1}
            activity = dot(coefficients, x)
            for n, coefficient in coefficients.items():
                stationarity[n] -= direction * lam * F(coefficient)
                scales[n] += abs(lam * F(coefficient))
            if bound is None:
                assert abs(lam) <= TOL
            else:
                dual += direction * F(bound) * lam
                ratio = abs(lam * (activity - F(bound))) / (
                    1 + abs(lam * activity) + abs(lam * F(bound)))
                assert ratio <= TOL
                max_complementarity = max(max_complementarity, ratio)
    max_stationarity = max(abs(stationarity[n]) / scales[n] for n in names)
    assert max_stationarity <= TOL
    assert abs(sign * value - dual) <= TOL * (1 + abs(value) + abs(dual))
    return {"primal_scaled": float(max_primal), "stationarity_scaled": float(max_stationarity),
            "complementarity_scaled": float(max_complementarity), "objective": str(expected)}
