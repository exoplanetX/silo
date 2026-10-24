"""Independent O(nnz) original-input numeric checks; no solver transformations."""

from fractions import Fraction
from math import fsum, isfinite


def bounds(row):
    if "lower" in row or "upper" in row:
        return row.get("lower"), row.get("upper")
    sense, rhs = row.get("sense", "<="), row.get("rhs", 0)
    return (None, rhs) if sense == "<=" else (rhs, None) if sense == ">=" else (rhs, rhs)


def close(value, reference, tolerance=1e-7):
    assert value is not None and isfinite(value)
    assert abs(value - reference) <= tolerance * (1 + abs(reference)), (value, reference)


def check(payload, result, truth=None, options=None, mip=False):
    options = options or {}
    ptol = options.get("primal_tolerance", 1e-7)
    dtol = options.get("dual_tolerance", 1e-7)
    ctol = options.get("complementarity_tolerance", 1e-7)
    otol = options.get("objective_tolerance", 1e-7)
    if not result.get("has_primal_solution", result.get("objective_value") is not None):
        assert result.get("absolute_gap") is result.get("relative_gap") is None
        return {"has_primal": False}
    point = result["primal_values"]
    assert set(point) == {v["name"] for v in payload["variables"]}
    assert all(isfinite(value) for value in point.values())
    sign = 1 if payload.get("sense", "minimize") == "minimize" else -1
    costs = payload["objective"]["coefficients"]
    constant = payload["objective"].get("constant", 0)
    primal = constant + fsum(c * point[name] for name, c in costs.items())
    close(result["objective_value"], primal, otol)
    largest = 0.0
    for variable in payload["variables"]:
        value = point[variable["name"]]
        for bound, side in ((variable.get("lower", 0), -1), (variable.get("upper"), 1)):
            if bound is not None:
                residual = side * (value - bound) / (1 + abs(value) + abs(bound))
                largest = max(largest, residual)
                assert residual <= ptol
        if mip and variable.get("type", "continuous") != "continuous":
            assert Fraction(value).denominator == 1
    activities = {}
    for row in payload["constraints"]:
        terms = [a * point[n] for n, a in row["coefficients"].items()]
        value, scale = fsum(terms), 1 + fsum(map(abs, terms))
        activities[row["name"]] = value
        for bound, side in zip(bounds(row), (-1, 1), strict=True):
            if bound is not None:
                residual = side * (value - bound) / (scale + abs(bound))
                largest = max(largest, residual)
                assert residual <= ptol, (row["name"], residual)
    reference = None
    if truth is not None and truth.get("status") == "optimal":
        reference = float(Fraction(truth.get("objective_exact", truth["objective"])))
        if result["status"] == "optimal":
            close(primal, reference)
        if result.get("dual_bound") is not None:
            assert sign * result["dual_bound"] <= sign * reference + 1e-7 * (1 + abs(reference))
    report = {
        "has_primal": True,
        "maximum_scaled_primal_residual": largest,
        "objective": primal,
        "reference": reference,
    }
    if mip or result["status"] != "optimal":
        return report
    sides = result["side_multipliers"]
    stationarity = {v["name"]: [sign * costs.get(v["name"], 0)] for v in payload["variables"]}
    scales = {v["name"]: [1 + abs(costs.get(v["name"], 0))] for v in payload["variables"]}
    dual_terms = [sign * constant]
    max_comp = 0.0
    for objects, label in ((payload["constraints"], "row"), (payload["variables"], "variable")):
        for obj in objects:
            name = obj["name"]
            lower, upper = (
                bounds(obj) if label == "row" else (obj.get("lower", 0), obj.get("upper"))
            )
            value = activities[name] if label == "row" else point[name]
            multipliers = [sides[label + "_" + side][name] for side in ("lower", "upper")]
            for bound, mult, direction in zip((lower, upper), multipliers, (1, -1), strict=True):
                assert isfinite(mult) and mult >= -dtol * (1 + abs(mult))
                if bound is None:
                    assert abs(mult) <= dtol
                else:
                    residual = abs(mult * (value - bound)) / (
                        1 + abs(mult * value) + abs(mult * bound)
                    )
                    assert residual <= ctol
                    max_comp = max(max_comp, residual)
                    dual_terms.append(direction * bound * mult)
            yl, yu = multipliers
            if label == "row":
                for n, a in obj["coefficients"].items():
                    stationarity[n].append(a * (yu - yl))
                    scales[n].append(abs(a) * (abs(yl) + abs(yu)))
            else:
                stationarity[name].extend((-yl, yu))
                scales[name].extend((abs(yl), abs(yu)))
    max_stationarity = max((abs(fsum(stationarity[n])) / fsum(scales[n]) for n in point), default=0)
    assert max_stationarity <= dtol
    dual = fsum(dual_terms)
    assert abs(sign * primal - dual) <= otol * (1 + abs(primal) + abs(dual))
    report.update(
        maximum_scaled_stationarity=max_stationarity,
        maximum_scaled_complementarity=max_comp,
        dual_objective=sign * dual,
    )
    return report


def certificate(payload, result):
    """Check the published original rational witness, never a reconstructed model."""
    from .oracles import point_ray

    proof = result.get("witness")
    assert proof is not None
    if result["status"] == "unbounded":
        return point_ray(
            payload, {k: {n: Fraction(v) for n, v in proof[k].items()} for k in ("point", "ray")}
        )
    assert result["status"] == "infeasible" and proof["kind"] == "farkas"
    names = [v["name"] for v in payload["variables"]]
    normal = dict.fromkeys(names, Fraction(0))
    separation = Fraction(0)
    for objects, label in ((payload["constraints"], "row"), (payload["variables"], "variable")):
        lo, up = [list(map(Fraction, proof[label + "_" + s])) for s in ("lower", "upper")]
        assert len(lo) == len(up) == len(objects)
        for obj, yl, yu in zip(objects, lo, up, strict=True):
            assert yl >= 0 and yu >= 0
            lower, upper = (
                bounds(obj) if label == "row" else (obj.get("lower", 0), obj.get("upper"))
            )
            for b, y, sign in zip((lower, upper), (yl, yu), (1, -1), strict=True):
                if b is None:
                    assert not y
                else:
                    separation += sign * Fraction(b) * y
            coefficients = obj["coefficients"] if label == "row" else {obj["name"]: 1}
            for name, a in coefficients.items():
                normal[name] += Fraction(a) * (yu - yl)
    assert separation > 0 and not any(normal.values())
    return {"kind": "independent_exact_farkas", "separation": str(separation)}
