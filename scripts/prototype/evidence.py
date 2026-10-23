"""Supplementary raw-input evidence for the immutable 2ca6098 prototype freeze.

``python scripts/prototype/evidence.py --verify`` rebuilds every input and exact
reference without importing SILO, invoking a native solver, or writing files.
``--json`` emits the supplemental manifest, including the 64 concrete diagnostic
calls. Frozen recipes are used only to reconstruct input payloads; no generated
expected value or generator parameter enters an oracle calculation.

The original-model convention is exact integers and exact binary floats:
``Fraction(value)`` preserves each actual input value. Decimal reconstruction
with ``Fraction(str(value))`` changes the model and is forbidden for certificate
checks. Frozen legacy vertices are candidate evidence, rechecked against these
binary-rational original sides before acceptance.
"""

import argparse
import copy
import hashlib
import itertools
import json
import math
import runpy
from collections import Counter
from dataclasses import dataclass
from fractions import Fraction as F
from functools import lru_cache
from pathlib import Path
from time import perf_counter

ROOT = Path(__file__).resolve().parents[2]
FROZEN_COMMIT = "2ca6098"
FROZEN_HASHES = {
    "scripts/prototype/freeze_manifest.py": {
        "2aa6f3609ae439a09aec4ef33b7ee865408e21c6b660d6549eb15e5df1474c70"
    },
    "scripts/prototype/oracles.py": {
        "31dc97f39b2dfec8669ee76a42c6c98f725a1bf054cd81da3b8a8018b0628da5"
    },
    # Git stores LF; the frozen Windows checkout has CRLF. These are the two
    # transport byte identities, whose JSON content is identical.
    "tests/fixtures/prototype_manifest.json": {
        "cf5736a21ea033c7b152b451e795ed8a2e69efa95ccd357d836806360b27eac9",
        "5b037ced206fdf349ca2524dca478a9427902ee136d0a668a449fa62af08c71e",
    },
    "docs/prototype_model_contract.md": {
        "1cf50e1f2eee7128715d94ea38284691a26c96be9bae9f704326c9285fcd6f58"
    },
}
OPERATION_CAP = 2_000_000


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def digest(payload):
    return sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    )


def q(value):
    """Preserve integers and the exact binary value of each finite input float."""
    if isinstance(value, F):
        return value
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"Expected a finite raw number: {value!r}")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("Nonfinite raw input")
    return F(value)


def row_bounds(row):
    if "lower" in row or "upper" in row:
        return row.get("lower"), row.get("upper")
    rhs, sense = row.get("rhs", 0), row.get("sense", "<=")
    if sense == "<=":
        return None, rhs
    if sense == ">=":
        return rhs, None
    if sense == "=":
        return rhs, rhs
    raise ValueError("Unknown raw row sense")


@dataclass(frozen=True)
class Side:
    name: str
    coefficients: dict
    rhs: F


def raw_sides(payload):
    """Read raw original sides as a*x<=b; no production transformations."""
    names = [v["name"] for v in payload["variables"]]
    assert len(names) == len(set(names))
    assert payload["sense"] in ("minimize", "maximize")
    q(payload["objective"].get("constant", 0))
    for name, value in payload["objective"]["coefficients"].items():
        assert name in names
        q(value)
    result = []
    row_names = set()
    for row in payload["constraints"]:
        assert row["name"] not in row_names
        row_names.add(row["name"])
        coefficients = {n: q(a) for n, a in row["coefficients"].items() if q(a)}
        assert set(coefficients) <= set(names)
        if "rhs" in row:
            q(row["rhs"])
        assert row.get("sense", "<=") in ("<=", ">=", "=")
        lower, upper = row_bounds(row)
        for value, sign, label in ((lower, -1, "lower"), (upper, 1, "upper")):
            if value is not None:
                result.append(
                    Side(
                        f"row:{row['name']}:{label}",
                        {n: sign * a for n, a in coefficients.items()},
                        sign * q(value),
                    )
                )
    for variable in payload["variables"]:
        assert variable["type"] in ("continuous", "integer", "binary")
        for label, sign, default in (("lower", -1, 0), ("upper", 1, None)):
            bound = variable.get(label, default)
            if bound is not None:
                result.append(
                    Side(
                        f"var:{variable['name']}:{label}",
                        {variable["name"]: F(sign)},
                        sign * q(bound),
                    )
                )
    return names, result


def dot(coefficients, values):
    return sum((a * values[n] for n, a in coefficients.items()), F(0))


def objective(payload, point):
    return q(payload["objective"].get("constant", 0)) + sum(
        (q(c) * point[n] for n, c in payload["objective"]["coefficients"].items()), F(0)
    )


def check_point(payload, point, integer=False):
    names, sides = raw_sides(payload)
    assert set(point) == set(names), "Incomplete primal point"
    assert all(dot(side.coefficients, point) <= side.rhs for side in sides), "Infeasible point"
    if integer:
        assert all(
            point[v["name"]].denominator == 1
            for v in payload["variables"]
            if v["type"] != "continuous"
        )
    return True


def check_certificate(payload, truth):
    """Independently check sparse exact primal/dual, Farkas, or ray evidence."""
    names, sides = raw_sides(payload)
    lookup = {side.name: side for side in sides}
    sign = 1 if payload["sense"] == "minimize" else -1
    cost = {n: sign * q(payload["objective"]["coefficients"].get(n, 0)) for n in names}
    if truth["status"] == "infeasible":
        multipliers = truth["farkas"]["multipliers"]
        assert multipliers and set(multipliers) <= set(lookup)
        assert all(value >= 0 for value in multipliers.values())
        assert all(
            sum(
                (lookup[k].coefficients.get(n, 0) * value for k, value in multipliers.items()), F(0)
            )
            == 0
            for n in names
        )
        contradiction = sum((lookup[k].rhs * value for k, value in multipliers.items()), F(0))
        assert contradiction < 0, "Farkas combination does not contradict 0<=b"
        assert truth["farkas"]["contradiction"] == contradiction
        return True
    point = truth["point"]
    check_point(payload, point, truth.get("integer_compatible", False))
    if truth["status"] == "unbounded":
        ray = truth["ray"]
        assert set(ray) == set(names) and any(ray.values())
        assert all(dot(side.coefficients, ray) <= 0 for side in sides), "Invalid recession ray"
        assert dot(cost, ray) < 0, "Ray does not improve the signed objective"
        if truth.get("integer_compatible"):
            assert all(
                ray[v["name"]].denominator == 1
                for v in payload["variables"]
                if v["type"] != "continuous"
            )
        return True
    assert truth["status"] == "optimal"
    assert objective(payload, point) == truth["objective"]
    multipliers = truth["dual"]["multipliers"]
    assert set(multipliers) <= set(lookup)
    assert all(value >= 0 for value in multipliers.values())
    assert all(
        cost[n]
        + sum((lookup[k].coefficients.get(n, 0) * value for k, value in multipliers.items()), F(0))
        == 0
        for n in names
    )
    assert all(
        value * (lookup[k].rhs - dot(lookup[k].coefficients, point)) == 0
        for k, value in multipliers.items()
    )
    dual = sign * q(payload["objective"].get("constant", 0)) - sum(
        (lookup[k].rhs * value for k, value in multipliers.items()), F(0)
    )
    assert dual == sign * truth["objective"], "Exact primal/dual objectives disagree"
    return True


def intervals(payload):
    """Strongest singleton sides with their positive normalization multipliers."""
    names, sides = raw_sides(payload)
    bounds = {n: {"lower": None, "upper": None} for n in names}
    for side in sides:
        if not side.coefficients and side.rhs < 0:
            return bounds, {side.name: F(1)}
        if len(side.coefficients) != 1:
            continue
        name, coefficient = next(iter(side.coefficients.items()))
        value = side.rhs / coefficient
        label = "upper" if coefficient > 0 else "lower"
        old = bounds[name][label]
        if old is None or (value < old[0] if label == "upper" else value > old[0]):
            bounds[name][label] = (value, side.name, 1 / abs(coefficient))
    for bound in bounds.values():
        lower, upper = bound["lower"], bound["upper"]
        if lower is not None and upper is not None and lower[0] > upper[0]:
            return bounds, {lower[1]: lower[2], upper[1]: upper[2]}
    return bounds, None


def constructive_lp_truth(payload, integer_ray=False):
    """Construct and verify evidence entirely from raw sides and objective data.

    Supported structures: singleton boxes, disjoint positive covering/equality
    groups with a separable residual, equality-proportional objectives, singleton
    contradictions and improving coordinate rays. Failure raises; it never maps
    a family number to a status.
    """
    names, sides = raw_sides(payload)
    lookup = {side.name: side for side in sides}
    bounds, farkas = intervals(payload)
    if farkas is not None:
        contradiction = sum((lookup[k].rhs * v for k, v in farkas.items()), F(0))
        truth = {
            "status": "infeasible",
            "oracle_kind": "raw_fraction_farkas",
            "farkas": {"multipliers": farkas, "contradiction": contradiction},
            "operations": len(sides),
        }
        check_certificate(payload, truth)
        return truth
    sign = 1 if payload["sense"] == "minimize" else -1
    cost = {n: sign * q(payload["objective"]["coefficients"].get(n, 0)) for n in names}
    point = {}
    for name in names:
        preferred = "upper" if cost[name] < 0 else "lower"
        other = "lower" if preferred == "upper" else "upper"
        bound = bounds[name][preferred] or bounds[name][other]
        point[name] = bound[0] if bound else F(0)
    # Fill violated positive lower groups using their cheapest raw marginal cost.
    for _ in range(len(sides) + 1):
        changed = False
        for side in sides:
            excess = dot(side.coefficients, point) - side.rhs
            if (
                excess <= 0
                or not side.coefficients
                or any(a > 0 for a in side.coefficients.values())
            ):
                continue
            ordered = sorted(side.coefficients, key=lambda n: (cost[n] / -side.coefficients[n], n))
            for name in ordered:
                coefficient = -side.coefficients[name]
                upper = bounds[name]["upper"]
                movement = excess / coefficient
                if upper is not None:
                    movement = min(movement, upper[0] - point[name])
                if movement > 0:
                    point[name] += movement
                    excess -= coefficient * movement
                    changed = True
                if excess <= 0:
                    break
        if not changed:
            break
    check_point(payload, point)
    for name in names:
        if not cost[name]:
            continue
        ray = dict.fromkeys(names, F(0))
        ray[name] = F(-1 if cost[name] > 0 else 1)
        if all(dot(side.coefficients, ray) <= 0 for side in sides):
            truth = {
                "status": "unbounded",
                "oracle_kind": "raw_fraction_point_ray",
                "point": point,
                "ray": ray,
                "integer_compatible": integer_ray,
                "operations": len(sides) * len(names),
            }
            check_certificate(payload, truth)
            return truth
    # Equality-proportional objectives also cover the frozen lineality model.
    for row in payload["constraints"]:
        lower, upper = row_bounds(row)
        coefficients = {n: q(a) for n, a in row["coefficients"].items() if q(a)}
        if lower is None or upper is None or lower != upper or not coefficients:
            continue
        pivot = next(iter(coefficients))
        ratio = cost[pivot] / coefficients[pivot]
        if all(cost[n] == ratio * coefficients.get(n, 0) for n in names):
            label = "lower" if ratio >= 0 else "upper"
            multipliers = {f"row:{row['name']}:{label}": abs(ratio)} if ratio else {}
            truth = {
                "status": "optimal",
                "oracle_kind": "raw_fraction_primal_dual",
                "point": point,
                "objective": objective(payload, point),
                "dual": {"multipliers": multipliers},
                "operations": len(sides),
            }
            check_certificate(payload, truth)
            return truth
    residual, multipliers, covered = cost.copy(), {}, set()
    for side in sides:
        members = set(side.coefficients)
        if (
            not side.name.startswith("row:")
            or len(members) < 2
            or covered & members
            or any(a >= 0 for a in side.coefficients.values())
        ):
            continue
        ratio = min(residual[n] / -a for n, a in side.coefficients.items())
        if ratio < 0:
            continue
        covered.update(members)
        if ratio:
            multipliers[side.name] = ratio
        for name, coefficient in side.coefficients.items():
            residual[name] += ratio * coefficient
    for name, value in residual.items():
        if not value:
            continue
        bound = bounds[name]["lower" if value > 0 else "upper"]
        if bound is None:
            raise ValueError("Raw structure has no constructive objective bound")
        multipliers[bound[1]] = multipliers.get(bound[1], F(0)) + abs(value) * bound[2]
    truth = {
        "status": "optimal",
        "oracle_kind": "raw_fraction_primal_dual",
        "point": point,
        "objective": objective(payload, point),
        "dual": {"multipliers": multipliers},
        "operations": len(sides) * len(names),
    }
    check_certificate(payload, truth)
    return truth


def _integer(value):
    value = q(value)
    assert value.denominator == 1
    return int(value)


def _binary_domain(payload):
    for variable in payload["variables"]:
        assert variable["type"] == "binary" and q(variable["lower"]) == 0
        assert q(variable["upper"]) == 1


def resource_dp_truth(payload, grouped=False):
    """Exact multiple-choice resource DP using raw rows, choices and costs."""
    _binary_domain(payload)
    names, _ = raw_sides(payload)
    resources, groups = [], []
    assigned = set()
    for row in payload["constraints"]:
        lower, upper = row_bounds(row)
        if lower is not None and upper is not None and q(lower) == q(upper):
            assert grouped and q(lower) == 1
            assert all(q(a) == 1 for a in row["coefficients"].values())
            group = list(row["coefficients"])
            assert group and not assigned.intersection(group)
            assigned.update(group)
            groups.append(group)
        else:
            assert lower is None and upper is not None
            resources.append(
                ({n: _integer(a) for n, a in row["coefficients"].items()}, _integer(upper))
            )
    assert 1 <= len(resources) <= 2 and all(cap >= 0 for _, cap in resources)
    assert all(a >= 0 for coefficients, _ in resources for a in coefficients.values())
    if grouped:
        assert assigned == set(names)
        choices = [[(name,) for name in group] for group in groups]
    else:
        assert not groups
        choices = [[(), (name,)] for name in names]
    costs = {n: q(payload["objective"]["coefficients"].get(n, 0)) for n in names}
    assert payload["sense"] == "minimize"
    states = {(0,) * len(resources): (F(0), ())}
    operations, peak = 0, 1
    for group in choices:
        updated = {}
        for used, (value, selected) in states.items():
            for choice in group:
                operations += 1
                assert operations <= OPERATION_CAP
                key = tuple(
                    u + sum(coefficients.get(n, 0) for n in choice)
                    for u, (coefficients, _) in zip(used, resources, strict=True)
                )
                if any(u > cap for u, (_, cap) in zip(key, resources, strict=True)):
                    continue
                candidate = value + sum((costs[n] for n in choice), F(0))
                if key not in updated or candidate < updated[key][0]:
                    updated[key] = (candidate, selected + choice)
        states = updated
        peak = max(peak, len(states))
    assert states, "Resource DP has no feasible terminal state"
    _, selected = min(states.values(), key=lambda item: item[0])
    point = {n: F(n in selected) for n in names}
    check_point(payload, point, True)
    return {
        "status": "optimal",
        "objective": objective(payload, point),
        "point": point,
        "oracle_kind": "raw_group_resource_dp" if grouped else "raw_resource_dp",
        "operations": operations,
        "domain": {"resources": len(resources), "groups": len(choices), "peak_states": peak},
    }


def cover_dp_truth(payload):
    """Exact raw 0/1 covering DP; every subset is represented by its coverage mask."""
    _binary_domain(payload)
    names, _ = raw_sides(payload)
    masks = dict.fromkeys(names, 0)
    rows = payload["constraints"]
    for index, row in enumerate(rows):
        lower, upper = row_bounds(row)
        assert q(lower) == 1 and upper is None
        assert all(q(a) == 1 for a in row["coefficients"].values())
        for name in row["coefficients"]:
            masks[name] |= 1 << index
    costs = {n: q(payload["objective"]["coefficients"].get(n, 0)) for n in names}
    assert payload["sense"] == "minimize"
    states, operations, peak = {0: (F(0), ())}, 0, 1
    for name in names:
        updated = dict(states)
        for covered, (value, selected) in states.items():
            operations += 1
            assert operations <= OPERATION_CAP
            key, candidate = covered | masks[name], value + costs[name]
            if key not in updated or candidate < updated[key][0]:
                updated[key] = candidate, selected + (name,)
        states = updated
        peak = max(peak, len(states))
    _, selected = states[(1 << len(rows)) - 1]
    point = {n: F(n in selected) for n in names}
    check_point(payload, point, True)
    return {
        "status": "optimal",
        "objective": objective(payload, point),
        "point": point,
        "oracle_kind": "raw_cover_mask_dp",
        "operations": operations,
        "domain": {"cover_rows": len(rows), "peak_states": peak},
    }


def flow_dp_truth(payload):
    """Raw fixed-charge/group flow DP with an integral continuous-subproblem proof.

    For fixed openings, each disjoint group's flow polytope is one integer-sum
    equality plus integer boxes. Its vertices are integral: at most one flow is
    off a box bound and that last value is integral. Nonnegative opening costs
    permit closing zero-flow facilities. Thus enumerating integer flow amounts
    loses no continuous optimum; no generator capacity or fee arrays are used.
    """
    names, _ = raw_sides(payload)
    variables = {v["name"]: v for v in payload["variables"]}
    openings = {n for n, v in variables.items() if v["type"] == "binary"}
    flows = set(names) - openings
    assert openings and all(variables[n]["type"] == "continuous" for n in flows)
    assert all(q(variables[n]["lower"]) == 0 and q(variables[n]["upper"]) == 1 for n in openings)
    costs = {n: q(payload["objective"]["coefficients"].get(n, 0)) for n in names}
    assert payload["sense"] == "minimize" and all(costs[n] >= 0 for n in openings)
    links, groups = {}, []
    used_openings, grouped_flows = set(), set()
    for row in payload["constraints"]:
        lower, upper = row_bounds(row)
        coefficients = {n: q(a) for n, a in row["coefficients"].items() if q(a)}
        row_flows, row_openings = set(coefficients) & flows, set(coefficients) & openings
        if row_openings:
            assert lower is None and q(upper) == 0 and len(row_flows) == len(row_openings) == 1
            flow, opening = next(iter(row_flows)), next(iter(row_openings))
            assert flow not in links and opening not in used_openings
            assert coefficients[flow] == 1
            capacity = _integer(-coefficients[opening])
            assert capacity > 0 and q(variables[flow]["lower"]) == 0
            assert q(variables[flow]["upper"]) == capacity
            links[flow] = (opening, capacity)
            used_openings.add(opening)
        else:
            assert lower is not None and upper is not None and q(lower) == q(upper)
            assert row_flows and all(a == 1 for a in coefficients.values())
            assert not grouped_flows & row_flows
            grouped_flows.update(row_flows)
            groups.append((list(coefficients), _integer(lower)))
    assert set(links) == grouped_flows == flows and used_openings == openings
    point, operations, peak = dict.fromkeys(names, F(0)), 0, 1
    for group, demand in groups:
        assert demand >= 0
        states = {0: (F(0), ())}
        for flow in group:
            opening, capacity = links[flow]
            updated = {}
            for used, (value, selected) in states.items():
                for amount in range(min(capacity, demand - used) + 1):
                    operations += 1
                    assert operations <= OPERATION_CAP
                    candidate = value + amount * costs[flow] + (costs[opening] if amount else 0)
                    key = used + amount
                    if key not in updated or candidate < updated[key][0]:
                        updated[key] = candidate, selected + ((flow, amount),)
            states = updated
            peak = max(peak, len(states))
        _, selected = states[demand]
        for flow, amount in selected:
            point[flow] = F(amount)
            point[links[flow][0]] = F(bool(amount))
    check_point(payload, point, True)
    return {
        "status": "optimal",
        "objective": objective(payload, point),
        "point": point,
        "oracle_kind": "raw_fixed_charge_flow_dp",
        "operations": operations,
        "domain": {
            "flow_variables": len(flows),
            "groups": len(groups),
            "peak_states": peak,
            "continuous_integrality": "integer box plus one integer-sum row per group",
        },
    }


def verify_frozen_sources():
    actual = {}
    for path, accepted in FROZEN_HASHES.items():
        value = sha256((ROOT / path).read_bytes())
        assert value in accepted, f"Frozen source changed: {path}: {value}"
        actual[path] = value
    return actual


@lru_cache(maxsize=1)
def frozen_modules():
    verify_frozen_sources()
    return (
        runpy.run_path(str(ROOT / "scripts/prototype/freeze_manifest.py")),
        runpy.run_path(str(ROOT / "scripts/prototype/oracles.py")),
    )


def load_manifest():
    verify_frozen_sources()
    return json.loads((ROOT / "tests/fixtures/prototype_manifest.json").read_text(encoding="utf-8"))


def raw_payload(entry):
    # payload_for discards every generated expected status/objective. Only this
    # immutable input reconstruction boundary may call the frozen recipes.
    return frozen_modules()[0]["payload_for"](entry)


def small_truth(payload, suite):
    names, _ = raw_sides(payload)
    discrete = [v for v in payload["variables"] if v["type"] != "continuous"]
    domain = {
        "variables": len(names),
        "rows": len(payload["constraints"]),
        "integer_variables": len(discrete),
        "continuous_variables": len(names) - len(discrete),
    }
    if not discrete:
        assert len(names) <= 4 and len(payload["constraints"]) <= 8
        try:
            result = constructive_lp_truth(payload)
        except (AssertionError, ValueError):
            result = None
        if result is not None:
            result["domain"] = domain
            return result
    else:
        assert suite == "milp_small" and len(discrete) <= 8
        widths = []
        for variable in discrete:
            assert variable["lower"] is not None and variable["upper"] is not None
            widths.append(
                max(0, math.floor(q(variable["upper"])) - math.ceil(q(variable["lower"])) + 1)
            )
        assert all(width <= 4 for width in widths) and math.prod(widths) <= 256
        assert len(names) - len(discrete) <= 2 and len(payload["constraints"]) <= 6
        domain.update(integer_assignments=math.prod(widths), largest_integer_domain=max(widths))
    # Family=0 deliberately avoids every family-only shortcut in the old file.
    result = frozen_modules()[1]["exact_small"](payload, suite, 0, OPERATION_CAP)
    assert result["operations"] <= OPERATION_CAP
    if result["status"] == "optimal":
        check_point(payload, result["point"], bool(discrete))
        assert objective(payload, result["point"]) == result["objective"]
    result.update(
        oracle_kind="raw_integer_enumeration_vertices" if discrete else "raw_fraction_vertices",
        domain=domain,
    )
    return result


def case_truth(entry, payload):
    suite = entry["suite"]
    if suite in ("lp_small", "milp_small"):
        return small_truth(payload, suite)
    if suite == "lp_scale":
        assert all(v["type"] == "continuous" for v in payload["variables"])
        result = constructive_lp_truth(payload)
        result["domain"] = {
            "variables": len(payload["variables"]),
            "rows": len(payload["constraints"]),
            "exact_certificate": True,
        }
        return result
    assert suite == "milp_scale"
    # Family selects a structural domain checker; all numbers and DP states come
    # from payload, never from the family index, recipe arrays, or expected data.
    family = entry["family"]
    if family in (0, 1, 4):
        return resource_dp_truth(payload, grouped=family == 4)
    if family == 2:
        return cover_dp_truth(payload)
    assert family in (3, 5)
    return flow_dp_truth(payload)


def integer_interval_contradiction(payload):
    bounds, _ = intervals(payload)
    for variable in payload["variables"]:
        if variable["type"] == "continuous":
            continue
        bound = bounds[variable["name"]]
        if bound["lower"] is None or bound["upper"] is None:
            continue
        lower, upper = bound["lower"][0], bound["upper"][0]
        if math.ceil(lower) > math.floor(upper):
            return {
                "variable": variable["name"],
                "raw_lower": lower,
                "raw_upper": upper,
                "ceil_lower": math.ceil(lower),
                "floor_upper": math.floor(upper),
                "lower_source": bound["lower"][1],
                "upper_source": bound["upper"][1],
            }
    raise AssertionError("No raw integer-interval contradiction")


# Explicit semantic reasons supplement the old generic boundary oracle label.
# Exact API reason equality is mandatory for B07--B11. Other strings identify the
# controlled mathematical/input event and are accompanied by concrete assertions.
BOUNDARY_SPECS = (
    (
        "B00",
        "raw_fraction_vertices",
        "combined_general_model_optimum",
        {"original_kkt": True, "free_upper_fixed_and_range_recovered": True},
    ),
    (
        "B01",
        "raw_integer_enumeration_vertices",
        "negative_integer_domain_optimum",
        {"original_integer_feasible": True, "negative_bounds_preserved": True},
    ),
    (
        "B02",
        "raw_empty_integer_interval",
        "empty_integer_domain",
        {"has_primal_solution": False, "no_lp_dual_optimality_claim": True},
    ),
    (
        "B03",
        "raw_fraction_farkas",
        "zero_row_contradiction",
        {"has_primal_solution": False, "farkas_exactly_verified": True},
    ),
    (
        "B04",
        "raw_fraction_point_ray",
        "original_lp_unboundedness_proved",
        {"point_and_improving_ray": True, "original_recession_sides": True},
    ),
    (
        "B05",
        "raw_integer_point_ray",
        "original_integer_unboundedness_proved",
        {"point_x": "0", "ray_x": "1", "integer_compatible": True},
    ),
    (
        "B06",
        "raw_integer_interval_and_lp_ray",
        "integer_infeasible_despite_lp_unbounded",
        {"has_primal_solution": False, "lp_unbounded_is_insufficient_for_mip": True},
    ),
    (
        "B07",
        "controlled_integer_ray_proof_budget",
        "unresolved_unbounded_relaxation",
        {
            "expected_termination_reason": "unresolved_unbounded_relaxation",
            "dual_bound": "negative_infinity",
            "relative_gap": None,
            "absolute_gap": None,
            "frontier_retained": True,
            "incumbent_if_present_original_integer_feasible": True,
        },
    ),
    (
        "B08",
        "controlled_zero_node_budget",
        "node_limit",
        {
            "expected_termination_reason": "node_limit",
            "nodes_max": 0,
            "bounds_bracket_exact_optimum": True,
            "incumbent_if_present_original_integer_feasible": True,
            "gap_without_incumbent": None,
        },
    ),
    (
        "B09",
        "controlled_zero_time_budget",
        "time_limit",
        {
            "expected_termination_reason": "time_limit",
            "no_search_after_budget": True,
            "bounds_bracket_exact_optimum": True,
            "incumbent_if_present_original_integer_feasible": True,
            "gap_without_incumbent": None,
        },
    ),
    (
        "B10",
        "controlled_zero_lp_iteration_budget",
        "lp_iteration_limit",
        {
            "expected_termination_reason": "lp_iteration_limit",
            "iterations_max": 0,
            "bounds_bracket_exact_optimum": True,
            "incumbent_if_present_original_feasible": True,
            "gap_without_incumbent": None,
        },
    ),
    (
        "B11",
        "controlled_relative_gap_with_incumbent",
        "gap_limit",
        {
            "expected_termination_reason": "gap_limit",
            "has_primal_solution": True,
            "original_integer_feasible": True,
            "bounds_bracket_exact_optimum": True,
            "relative_gap_max": 1,
            "relative_gap_formula": "abs(P-D)/max(1,abs(P),abs(D))",
        },
    ),
    (
        "B12",
        "raw_enumeration_plus_cut_scope",
        "local_cut_scope_preserved",
        {
            "local_bound_cut_default_local": True,
            "no_sibling_cut_leak": True,
            "all_added_cuts_valid_on_their_domain": True,
            "objective_matches_exact_oracle": True,
        },
    ),
    (
        "B13",
        "raw_enumeration_plus_gmi_boundary",
        "mixed_gmi_reoptimization",
        {
            "gmi_tableau_conditions_verified": True,
            "fractional_point_removed": True,
            "mixed_feasible_region_preserved": True,
            "objective_matches_exact_oracle": True,
        },
    ),
    (
        "B14",
        "raw_vertices_plus_stale_basis_control",
        "stale_basis_cold_fallback",
        {"fallback_count": 1, "fallback_reason_recorded": True, "cold_objective_equal": True},
    ),
    (
        "B15",
        "raw_modified_rhs_vertices",
        "rhs_dual_reoptimization",
        {"actual_dual_simplex_path": True, "cold_objective_equal": True, "original_kkt": True},
    ),
    (
        "B16",
        "raw_appended_row_vertices",
        "append_row_reoptimization",
        {"new_row_identity_present": True, "cold_objective_equal": True, "original_kkt": True},
    ),
    (
        "B17",
        "raw_appended_column_vertices",
        "append_column_reoptimization",
        {"new_column_identity_present": True, "cold_objective_equal": True, "original_kkt": True},
    ),
    (
        "B18",
        "raw_fraction_vertices",
        "scaled_original_kkt_recovered",
        {
            "positive_scaling_applied": True,
            "original_kkt": True,
            "scaled_and_unscaled_objectives_equal": True,
        },
    ),
    (
        "B19",
        "raw_vertices_plus_singular_basis_control",
        "singular_basis_cold_fallback",
        {"fallback_count": 1, "singular_reason_recorded": True, "cold_objective_equal": True},
    ),
    (
        "B20",
        "raw_nonfinite_mutation_rejection",
        "nonfinite_input_rejected",
        {"has_primal_solution": False, "native_algorithm_entered": False},
    ),
    (
        "B21",
        "frozen_mps_syntax_rejection",
        "malformed_mps_rejected",
        {"has_primal_solution": False, "native_algorithm_entered": False},
    ),
    (
        "B22",
        "frozen_unsupported_mps_rejection",
        "quadratic_section_unsupported",
        {
            "has_primal_solution": False,
            "native_algorithm_entered": False,
            "unsupported_token": "QMATRIX",
        },
    ),
    (
        "B23",
        "exact_fraction_objective_float_overflow",
        "finite_input_objective_overflow",
        {
            "has_primal_solution": False,
            "no_optimal_claim": True,
            "finite_inputs": True,
            "nonfinite_float_objective_detected": True,
        },
    ),
)


def modified_boundary_payload(boundary):
    data = boundary["input"]
    payload = copy.deepcopy(data["model"])
    action = data.get("action") or {}
    if action.get("type") == "rhs":
        target = next(row for row in payload["constraints"] if row["name"] == action["row"])
        target["rhs"] = action["rhs"]
    elif action.get("type") == "append_row":
        payload["constraints"].append(copy.deepcopy(action["row"]))
    elif action.get("type") == "append_column":
        payload["variables"].append(copy.deepcopy(action["variable"]))
        name = action["variable"]["name"]
        payload["objective"]["coefficients"][name] = action["cost"]
        for row in payload["constraints"]:
            if row["name"] in action["coefficients"]:
                row["coefficients"][name] = action["coefficients"][row["name"]]
    return payload


def boundary_evidence(boundaries):
    assert len(boundaries) == len(BOUNDARY_SPECS) == 24
    records = []
    for index, (boundary, spec) in enumerate(zip(boundaries, BOUNDARY_SPECS, strict=True)):
        identifier, kind, reason, assertions = spec
        assert boundary["id"] == identifier
        rebuilt_status = (
            "infeasible"
            if index in (2, 3, 6)
            else "unbounded"
            if index in (4, 5)
            else "limit"
            if 7 <= index <= 11
            else "invalid_model"
            if index in (20, 21)
            else "unsupported"
            if index == 22
            else "numerical_failure"
            if index == 23
            else "optimal"
        )
        assert boundary["expected_status"] == boundary["expected_terminal_state"] == rebuilt_status
        assert digest(boundary["input"]) == boundary["input_sha256"]
        assert boundary["input"] == frozen_modules()[0]["boundary_input"](index)
        record = {
            "id": identifier,
            "input_sha256": boundary["input_sha256"],
            "expected_status": boundary["expected_status"],
            "oracle_kind": kind,
            "expected_control_reason": reason,
            "assertions": copy.deepcopy(assertions),
            "source_hash": boundary["source_hash"],
            "native_calls": 0,
            "runtime_assertions_executed": False,
            "oracle_operation_cap": boundary["oracle_operation_cap"],
        }
        if index in (21, 22):
            tokens = boundary["input"]["text"].split()
            record["oracle_domain"] = {"format": "mps", "syntax_only": True}
            if index == 21:
                assert "N" not in tokens and "x r\n" in boundary["input"]["text"]
                record["proof"] = {
                    "syntax_faults": ["missing N objective row", "missing column value"]
                }
            else:
                assert "QMATRIX" in tokens
                record["proof"] = {"unsupported_section": "QMATRIX"}
        else:
            payload = modified_boundary_payload(boundary)
            integer_count = sum(v["type"] != "continuous" for v in payload["variables"])
            record["oracle_domain"] = {
                "format": "json",
                "variables": len(payload["variables"]),
                "rows": len(payload["constraints"]),
                "integer_variables": integer_count,
                "continuous_variables": len(payload["variables"]) - integer_count,
            }
            if index in (2, 6):
                record["proof"] = integer_interval_contradiction(payload)
                if index == 6:
                    record["lp_relaxation_proof"] = constructive_lp_truth(payload)
                    assert record["lp_relaxation_proof"]["status"] == "unbounded"
            elif index in (3, 4, 5, 7):
                record["proof"] = constructive_lp_truth(payload, integer_ray=index in (5, 7))
                if index == 5:
                    assert record["proof"]["point"] == {"x": F(0)}
                    assert record["proof"]["ray"] == {"x": F(1)}
                if index == 7:
                    assert boundary["input"]["options"] == {"integer_ray_proof_limit": 0}
                    assert record["proof"]["status"] == "unbounded"
                    record["mathematical_status"] = "unbounded"
            elif index == 20:
                action = boundary["input"]["action"]
                assert action == {"type": "nonfinite", "target": "objective.x", "value": "NaN"}
                assert "x" in payload["objective"]["coefficients"]
                invalid = copy.deepcopy(payload)
                invalid["objective"]["coefficients"]["x"] = float("nan")
                try:
                    raw_sides(invalid)
                except ValueError:
                    record["proof"] = {"nonfinite_value_rejected": True}
                else:
                    raise AssertionError("Nonfinite raw data accepted")
            elif index == 23:
                point = {v["name"]: q(v["lower"]) for v in payload["variables"]}
                check_point(payload, point)
                value = objective(payload, point)
                try:
                    overflow = not math.isfinite(float(value))
                except OverflowError:
                    overflow = True
                assert overflow
                record["proof"] = {"point": point, "exact_objective": value, "float_overflow": True}
            else:
                suite = (
                    "milp_small"
                    if any(v["type"] != "continuous" for v in payload["variables"])
                    else "lp_small"
                )
                record["proof"] = small_truth(payload, suite)
                assert record["proof"]["status"] == "optimal"
                record["reference_objective"] = record["proof"]["objective"]
                if index in (8, 9, 10):
                    option = {8: "node_limit", 9: "time_limit", 10: "lp_iteration_limit"}[index]
                    assert boundary["input"]["options"] == {option: 0}
                elif index == 11:
                    assert boundary["input"]["options"] == {
                        "relative_gap": 1,
                        "cuts": False,
                        "heuristics": True,
                    }
                    relaxation = constructive_lp_truth(payload)
                    assert relaxation["status"] == "optimal"
                    record["lp_relaxation_proof"] = relaxation
                    primal, dual = record["reference_objective"], relaxation["objective"]
                    assert dual < primal
                    assert abs(primal - dual) / max(1, abs(primal), abs(dual)) <= 1
            if index not in (20, 23):
                record["oracle_model_sha256"] = digest(payload)
        record["operations"] = sum(
            record[key].get("operations", 1)
            for key in ("proof", "lp_relaxation_proof")
            if key in record
        )
        assert record["operations"] <= record["oracle_operation_cap"]
        records.append(record)
    return records


LP_DIAGNOSTIC_IDS = ("LP000", "LP008", "LP032", "LP056")
MIP_DIAGNOSTIC_IDS = ("MI000", "MI024", "MI072", "MI088")
LP_DIAGNOSTIC_ACTIONS = {
    "LP000": (
        {"type": "rhs", "row": "diag_rhs", "rhs": 0},
        {"type": "bound", "variable": "x", "side": "lower", "value": -1},
    ),
    "LP008": (
        {"type": "rhs", "row": "r", "rhs": 2},
        {"type": "bound", "variable": "y", "side": "upper", "value": 2},
    ),
    "LP032": (
        {"type": "rhs", "row": "range", "side": "upper", "rhs": 2},
        {"type": "bound", "variable": "x", "side": "upper", "value": 1},
    ),
    "LP056": (
        {"type": "rhs", "row": "a", "rhs": 20000},
        {"type": "bound", "variable": "x", "side": "upper", "value": 1},
    ),
}


def diagnostic_payload(base, actions):
    payload = copy.deepcopy(base)
    for action in actions:
        kind = action["type"]
        if kind == "rhs":
            row = next(r for r in payload["constraints"] if r["name"] == action["row"])
            row[action.get("side", "rhs")] = action["rhs"]
        elif kind == "bound":
            variable = next(v for v in payload["variables"] if v["name"] == action["variable"])
            variable[action["side"]] = action["value"]
        elif kind == "append_row":
            payload["constraints"].append(copy.deepcopy(action["row"]))
        elif kind == "append_column":
            variable = copy.deepcopy(action["variable"])
            payload["variables"].append(variable)
            payload["objective"]["coefficients"][variable["name"]] = action["cost"]
            for row in payload["constraints"]:
                if row["name"] in action["coefficients"]:
                    row["coefficients"][variable["name"]] = action["coefficients"][row["name"]]
        else:
            assert kind in ("solve", "invalidate_basis")
    return payload


def diagnostic_evidence(manifest):
    """Exactly one additional solve per explicit entry; baselines are shared."""
    frozen = manifest["diagnostics"]
    assert frozen["ids"] == list(LP_DIAGNOSTIC_IDS + MIP_DIAGNOSTIC_IDS)
    variants = (
        "cold",
        "rhs_warm",
        "bound_warm",
        "row_warm",
        "column_warm",
        "presolve_off",
        "scaling_off",
        "invalid_basis_fallback",
    )
    assert frozen["LP_variants"] == list(variants) and frozen["calls_max"] == 64
    entries = {e["id"]: e for e in manifest["cases"]}
    records, cache = [], {}

    def reference(payload, suite):
        key = digest(payload)
        if key not in cache:
            cache[key] = small_truth(payload, suite)
        assert cache[key]["status"] == "optimal"
        return cache[key]

    for identifier in LP_DIAGNOSTIC_IDS:
        original = raw_payload(entries[identifier])
        assert digest(original) == entries[identifier]["model_sha256"]
        preparation = []
        if identifier == "LP000":
            preparation = [
                {
                    "type": "append_row",
                    "row": {
                        "name": "diag_rhs",
                        "coefficients": {"x": 1, "y": 1},
                        "sense": "<=",
                        "rhs": 1,
                    },
                }
            ]
        base = diagnostic_payload(original, preparation)
        rhs, bound = LP_DIAGNOSTIC_ACTIONS[identifier]
        new_row = {
            "type": "append_row",
            "row": {
                "name": "diag_row",
                "coefficients": {bound["variable"]: 1},
                "sense": ">=" if bound["side"] == "lower" else "<=",
                "rhs": bound["value"],
            },
        }
        new_column = {
            "type": "append_column",
            "variable": {"name": "diag_column", "lower": 0, "upper": 1, "type": "continuous"},
            "cost": -1,
            "coefficients": {},
        }
        for index, variant in enumerate(variants):
            mutations = {
                "rhs_warm": [rhs],
                "bound_warm": [bound],
                "row_warm": [new_row],
                "column_warm": [new_column],
                "invalid_basis_fallback": [{"type": "invalidate_basis", "indices": [999]}],
            }.get(variant, [])
            options = dict(entries[identifier]["options"])
            if variant == "presolve_off":
                options["presolve"] = False
            elif variant == "scaling_off":
                options["scaling"] = False
            warm = variant in (
                "rhs_warm",
                "bound_warm",
                "row_warm",
                "column_warm",
                "invalid_basis_fallback",
            )
            preferred = "primal" if variant == "column_warm" else "dual" if warm else "cold"
            solve_action = {"type": "solve", "basis": "shared_cold" if warm else "none"}
            derived = diagnostic_payload(base, mutations)
            truth = reference(derived, "lp_small")
            expected = {
                "status": "optimal",
                "objective": truth["objective"],
                "original_kkt": True,
                "must_equal_independent_cold_reference": True,
                "preferred_path": preferred,
                "reuse_attempt_required": warm,
                "fallback_max": 1 if warm else 0,
                "fallback_requires_recorded_incompatibility": warm,
            }
            if variant == "invalid_basis_fallback":
                expected.update(
                    preferred_path="cold_fallback", fallback_count=1, fallback_reason_required=True
                )
            records.append(
                {
                    "id": f"D-{identifier}-{index}",
                    "case_id": identifier,
                    "variant": variant,
                    "original_model_sha256": digest(original),
                    "diagnostic_base_sha256": digest(base),
                    "model_sha256": digest(derived),
                    "prepare_model": preparation,
                    "actions": copy.deepcopy(mutations) + [solve_action],
                    "options": options,
                    "shared_cold_call": f"D-{identifier}-0",
                    "expected": expected,
                    "oracle_kind": truth["oracle_kind"],
                    "reference_proof": truth,
                    "planned_native_calls": 1,
                    "hidden_setup_solves": 0,
                    "budget_stage": "M2_or_M5",
                    "time_limit_seconds": 20,
                    "runtime_assertions_executed": False,
                }
            )
    for identifier in MIP_DIAGNOSTIC_IDS:
        payload = raw_payload(entries[identifier])
        truth = reference(payload, "milp_small")
        for index, (cuts, heuristics, strategy) in enumerate(
            itertools.product((False, True), (False, True), ("best_bound", "dfs"))
        ):
            options = {
                **entries[identifier]["options"],
                "cuts": cuts,
                "heuristics": heuristics,
                "node_strategy": strategy,
                "node_limit": 100000,
                "time_limit": 60,
            }
            records.append(
                {
                    "id": f"D-{identifier}-{index}",
                    "case_id": identifier,
                    "variant": f"cuts_{int(cuts)}_heuristics_{int(heuristics)}_{strategy}",
                    "original_model_sha256": digest(payload),
                    "diagnostic_base_sha256": digest(payload),
                    "model_sha256": digest(payload),
                    "prepare_model": [],
                    "actions": [{"type": "solve", "basis": "none"}],
                    "options": options,
                    "expected": {
                        "status": "optimal",
                        "objective": truth["objective"],
                        "original_integer_feasible": True,
                        "zero_final_gap": True,
                        "cuts_enabled": cuts,
                        "heuristics_enabled": heuristics,
                        "node_selection_policy": strategy,
                        "actual_enabled_mechanism_attempts_traced": True,
                        "disabled_mechanism_calls": 0,
                    },
                    "oracle_kind": truth["oracle_kind"],
                    "reference_proof": truth,
                    "planned_native_calls": 1,
                    "hidden_setup_solves": 0,
                    "budget_stage": "M3_or_M5",
                    "time_limit_seconds": 60,
                    "runtime_assertions_executed": False,
                }
            )
    assert len(records) == len({r["id"] for r in records}) == 64
    assert Counter(r["case_id"] for r in records) == Counter(dict.fromkeys(frozen["ids"], 8))
    assert sum(r["planned_native_calls"] for r in records) == 64
    return records


def build_evidence():
    """Rebuild all 264 references, 24 controls and 64 declared diagnostics read-only."""
    start = perf_counter()
    sources = verify_frozen_sources()
    manifest = load_manifest()
    recipe_hash = sources["scripts/prototype/freeze_manifest.py"]
    old_oracle_hash = sources["scripts/prototype/oracles.py"]
    assert manifest["recipe_sha256"] == recipe_hash
    assert manifest["independent_oracle_sha256"] == old_oracle_hash
    entries = manifest["cases"]
    assert len(entries) == len({e["id"] for e in entries}) == 264
    assert Counter(e["suite"] for e in entries) == {
        "lp_small": 96,
        "milp_small": 96,
        "lp_scale": 48,
        "milp_scale": 24,
    }
    records = []
    for entry in entries:
        assert entry["truth_source"] == "scripts/prototype/freeze_manifest.py"
        assert entry["source_hash"] == recipe_hash
        payload = raw_payload(entry)
        assert digest(payload) == entry["model_sha256"], f"Input hash mismatch: {entry['id']}"
        assert (len(payload["variables"]), len(payload["constraints"])) == (
            entry["variables"],
            entry["rows"],
        )
        truth = case_truth(entry, payload)
        assert truth["status"] == entry["expected_status"] == entry["expected_terminal_state"]
        assert truth["operations"] <= entry["oracle_operation_cap"] == OPERATION_CAP
        if entry["expected_objective"] is not None:
            assert truth["status"] == "optimal"
            assert truth["objective"] == q(entry["expected_objective"]), entry["id"]
        if entry["suite"] == "lp_small" and entry["family"] in (8, 9):
            assert truth["oracle_kind"] == (
                "raw_fraction_farkas" if entry["family"] == 8 else "raw_fraction_point_ray"
            )
            check_certificate(payload, truth)
        if entry["suite"] == "lp_scale":
            assert entry["variables"] <= 200 and entry["rows"] <= 400
            check_certificate(payload, truth)
        elif entry["suite"] == "milp_scale":
            assert entry["variables"] <= 100 and entry["rows"] <= 200
            assert sum(v["type"] != "continuous" for v in payload["variables"]) <= 30
        records.append(
            {
                "id": entry["id"],
                "suite": entry["suite"],
                "model_sha256": entry["model_sha256"],
                "input_source_sha256": recipe_hash,
                "oracle_operation_cap": entry["oracle_operation_cap"],
                "truth": truth,
            }
        )
    assert (
        sum(
            e["suite"] == "lp_scale"
            and e["expected_status"] == "optimal"
            and 100 <= e["variables"] <= 200
            and 100 <= e["rows"] <= 400
            for e in entries
        )
        >= 8
    )
    boundaries = manifest["boundaries"]
    for boundary in boundaries:
        assert boundary["truth_source"] == "docs/prototype_model_contract.md"
        assert boundary["source_hash"] == sources["docs/prototype_model_contract.md"]
        assert boundary["oracle_operation_cap"] == 10000
    boundary_records = boundary_evidence(boundaries)
    diagnostic_records = diagnostic_evidence(manifest)
    assert verify_frozen_sources() == sources, "Frozen bytes changed during verification"
    elapsed = perf_counter() - start
    return {
        "schema": 1,
        "program": manifest["program"],
        "frozen_commit": FROZEN_COMMIT,
        "frozen_sources_sha256": sources,
        "accepted_manifest_transport_sha256": sorted(
            FROZEN_HASHES["tests/fixtures/prototype_manifest.json"]
        ),
        "oracle_source": "scripts/prototype/evidence.py",
        "oracle_source_sha256": sha256(Path(__file__).read_bytes()),
        "legacy_small_oracle_source_sha256": old_oracle_hash,
        "native_solver_calls": 0,
        "files_written": 0,
        "runtime_boundary_or_diagnostic_assertions_executed": False,
        "cases": records,
        "boundaries": boundary_records,
        "diagnostics": diagnostic_records,
        "budget_accounting": {
            "verification_seconds": elapsed,
            "charged_to": "current_module",
            "diagnostic_calls_max": 64,
            "hidden_setup_solves": 0,
            "shared_cold_per_lp_id": 1,
            "every_physical_diagnostic_solve_charged_once": True,
            "native_scale_runs": 0,
        },
    }


def json_ready(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {key: json_ready(item) for key, item in value.items()}
    if isinstance(value, list | tuple):
        return [json_ready(item) for item in value]
    return value


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--verify", action="store_true", help="read-only verification of the freeze"
    )
    parser.add_argument("--json", action="store_true", help="emit rebuilt supplementary manifest")
    args = parser.parse_args(argv)
    if not (args.verify or args.json):
        parser.error("choose --verify or --json")
    evidence = build_evidence()
    if args.json:
        print(json.dumps(json_ready(evidence), sort_keys=True, indent=2, allow_nan=False))
    else:
        print(
            json.dumps(
                {
                    "verified_cases": len(evidence["cases"]),
                    "verified_boundaries": len(evidence["boundaries"]),
                    "explicit_diagnostic_calls": len(evidence["diagnostics"]),
                    "oracle_kinds": dict(
                        Counter(r["truth"]["oracle_kind"] for r in evidence["cases"])
                    ),
                    "frozen_manifest_sha256": evidence["frozen_sources_sha256"][
                        "tests/fixtures/prototype_manifest.json"
                    ],
                    "oracle_source_sha256": evidence["oracle_source_sha256"],
                    "verification_seconds": evidence["budget_accounting"]["verification_seconds"],
                    "native_solver_calls": 0,
                    "files_written": 0,
                    "runtime_assertions_executed": False,
                },
                sort_keys=True,
                indent=2,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
