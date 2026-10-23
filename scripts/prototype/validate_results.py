"""Independent raw-input checks for actual prototype outputs.

This module imports no production model transformations or verification helpers.
Floats are checked as their actual binary Fractions under the frozen tolerances.
"""

from fractions import Fraction as F
from math import isfinite

from evidence import check_certificate, dot, objective, q, raw_sides

TOL = F(1, 10_000_000)


def close(actual, reference, message):
    assert actual is not None and isfinite(float(actual)), message
    assert abs(q(actual) - reference) <= TOL * (1 + abs(reference)), message


def check_gaps(output):
    """Check flags and gap algebra without trusting a reported optimality flag."""
    if output["status"] == "optimal":
        assert output["has_primal_solution"] is True, "Optimal output lacks a primal flag"
    if not output["has_primal_solution"]:
        assert output["absolute_gap"] is output["relative_gap"] is None, "Gap without incumbent"
        return
    close(output["primal_bound"], q(output["objective_value"]), "Primal flag/bound mismatch")
    if output["dual_bound"] is None or not isfinite(float(output["dual_bound"])):
        assert output["status"] != "optimal", "Infinite optimal bound"
        assert output["absolute_gap"] is output["relative_gap"] is None, "Gap without finite bound"
        return
    p, d = q(output["primal_bound"]), q(output["dual_bound"])
    gap = abs(p - d)
    for key, expected in (("absolute_gap", gap), ("relative_gap", gap / max(F(1), abs(p), abs(d)))):
        value = output[key]
        assert value is not None and isfinite(float(value)) and value >= 0, f"Invalid {key}"
        close(value, expected, f"Inconsistent {key}")


def primal(payload, values):
    names, sides = raw_sides(payload)
    assert set(values) == set(names), "Incomplete published point"
    point = {name: q(value) for name, value in values.items()}
    largest = F(0)
    for side in sides:
        value = dot(side.coefficients, point)
        scale = 1 + abs(side.rhs) + sum(abs(a * point[n]) for n, a in side.coefficients.items())
        residual = max(F(0), value - side.rhs) / scale
        largest = max(largest, residual)
        assert residual <= TOL, f"Original side violated: {side.name}"
    for variable in payload["variables"]:
        if variable["type"] != "continuous":
            assert point[variable["name"]].denominator == 1, "Published integer is fractional"
    return point, float(largest)


def side_multipliers(payload, output, exact=False):
    groups = output["witness"] if exact else output["side_multipliers"]
    result = {}
    for label, objects, kind in (
        ("row", payload["constraints"], "row"),
        ("variable", payload["variables"], "var"),
    ):
        names = [item["name"] for item in objects]
        for side in ("lower", "upper"):
            values = groups[f"{label}_{side}"]
            if exact:
                assert len(values) == len(names)
                values = dict(zip(names, map(F, values), strict=True))
            else:
                assert set(values) == set(names)
                values = {name: q(value) for name, value in values.items()}
            result.update({f"{kind}:{name}:{side}": value for name, value in values.items()})
    _, sides = raw_sides(payload)
    present = {side.name for side in sides}
    for name, value in result.items():
        assert value >= (0 if exact else -TOL * (1 + abs(value))), "Negative side multiplier"
        if name not in present:
            assert abs(value) <= (0 if exact else TOL), "Multiplier on absent side"
    return result


def kkt(payload, output, point):
    names, sides = raw_sides(payload)
    multipliers = side_multipliers(payload, output)
    sign = 1 if payload["sense"] == "minimize" else -1
    maximum = F(0)
    for name in names:
        cost = sign * q(payload["objective"]["coefficients"].get(name, 0))
        products = [side.coefficients.get(name, 0) * multipliers[side.name] for side in sides]
        residual = abs(cost + sum(products, F(0))) / (1 + abs(cost) + sum(map(abs, products)))
        maximum = max(maximum, residual)
        assert residual <= TOL, f"Original stationarity: {name}"
    for side in sides:
        value, multiplier = dot(side.coefficients, point), multipliers[side.name]
        assert abs(multiplier * (side.rhs - value)) <= TOL * (
            1 + abs(multiplier * side.rhs) + abs(multiplier * value)
        ), f"Original complementarity: {side.name}"
    dual = sign * q(payload["objective"].get("constant", 0)) - sum(
        (side.rhs * multipliers[side.name] for side in sides), F(0)
    )
    normalized = sign * objective(payload, point)
    assert abs(normalized - dual) <= TOL * (1 + abs(normalized) + abs(dual)), "Primal/dual gap"
    for row in payload["constraints"]:
        name = row["name"]
        public_dual = sign * (multipliers[f"row:{name}:lower"] - multipliers[f"row:{name}:upper"])
        close(output["dual_values"][name], public_dual, "Public signed dual mapping")
    for name in names:
        reduced = q(payload["objective"]["coefficients"].get(name, 0)) - sum(
            (
                q(row["coefficients"].get(name, 0)) * q(output["dual_values"][row["name"]])
                for row in payload["constraints"]
            ),
            F(0),
        )
        close(output["reduced_costs"][name], reduced, "Public reduced-cost mapping")
    return float(maximum)


def validate(payload, output, truth):
    expected = truth["status"]
    assert output["status"] == expected, (output["status"], expected, output["termination_reason"])
    integer = any(v["type"] != "continuous" for v in payload["variables"])
    record = {"status": expected, "independent_raw_check": True}
    if expected == "optimal":
        check_gaps(output)
        point, residual = primal(payload, output["primal_values"])
        close(output["objective_value"], truth["objective"], "Independent objective")
        close(output["objective_value"], objective(payload, point), "Published original objective")
        close(output["primal_bound"], truth["objective"], "Primal bound")
        close(output["dual_bound"], truth["objective"], "Dual bound")
        assert output["absolute_gap"] is not None and output["absolute_gap"] <= float(TOL) * (
            1 + abs(float(truth["objective"]))
        ), "Nonzero optimal gap"
        record["maximum_scaled_primal_residual"] = residual
        assert set(output["row_activities"]) == {row["name"] for row in payload["constraints"]}
        for row in payload["constraints"]:
            value = dot({n: q(a) for n, a in row["coefficients"].items()}, point)
            close(output["row_activities"][row["name"]], value, "Published row activity")
        if not integer:
            record["maximum_scaled_stationarity_residual"] = kkt(payload, output, point)
        else:
            record["integer_feasible"] = True
    elif expected == "unbounded":
        witness = output["witness"]
        assert witness and witness["exact"]
        proof = {
            "status": "unbounded",
            "point": {n: F(v) for n, v in witness["point"].items()},
            "ray": {n: F(v) for n, v in witness["ray"].items()},
            "integer_compatible": integer,
        }
        check_certificate(payload, proof)
        if output["has_primal_solution"]:
            assert {n: q(v) for n, v in output["primal_values"].items()} == proof["point"], (
                "Published anchor differs from exact witness"
            )
        record["exact_ray_checked"] = True
    elif expected == "infeasible" and not integer:
        multipliers = side_multipliers(payload, output, exact=True)
        _, sides = raw_sides(payload)
        rhs = sum((side.rhs * multipliers[side.name] for side in sides), F(0))
        check_certificate(
            payload,
            {
                "status": "infeasible",
                "farkas": {
                    "multipliers": {side.name: multipliers[side.name] for side in sides},
                    "contradiction": rhs,
                },
            },
        )
        assert F(output["witness"]["contradiction"]) == -rhs
        record["exact_farkas_checked"] = True
    elif expected == "infeasible":
        record["integer_oracle_infeasibility_checked"] = True
    return record
