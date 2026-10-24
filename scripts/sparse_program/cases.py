"""Frozen sparse-program input recipes, with no production solver imports.

Each case has an independent hash-derived sub-seed. Capacity families have actual
flow, transportation, assignment, angular-resource, inventory or general rows.
Constructed primal/dual pairs are proposals for independent raw-input checking,
never accepted truth merely because this generator produced them.
"""

import copy
import hashlib
import json
import math
import random
from pathlib import Path

SEED = 20261024
ROOT = Path(__file__).resolve().parents[2]
GROUP_ORDER = ("tiny", "pressure", "capacity", "netlib", "mechanism", "mip", "cg")
CAPACITY = (
    ("FLOW", 1, 256, 512, 4096),
    ("FLOW", 2, 1000, 1500, 20000),
    ("TRANS", 1, 400, 600, 6000),
    ("TRANS", 2, 1500, 2000, 30000),
    ("ASSIGN", 1, 625, 500, 6000),
    ("ASSIGN", 2, 1600, 1000, 30000),
    ("BLOCK", 1, 800, 800, 16000),
    ("BLOCK", 2, 2000, 5000, 100000),
    ("INVENT", 1, 600, 700, 8000),
    ("INVENT", 2, 1200, 1500, 25000),
    ("GENERAL", 1, 1000, 1100, 25000),
    ("GENERAL", 2, 1800, 2200, 60000),
)
PIVOT_CAPACITY_IDS = tuple(
    f"CAP-{family}-02"
    for family in (
        "FLOW",
        "TRANS",
        "ASSIGN",
        "BLOCK",
        "INVENT",
        "GENERAL",
    )
)


def canonical(value):
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()


def sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _same_or_new(path, data):
    if path.exists():
        if path.read_bytes() != data:
            raise ValueError(f"Existing frozen input differs; preserve it and report: {path}")
        return
    path.write_bytes(data)


def subseed(identifier):
    return int(hashlib.sha256(f"{SEED}:{identifier}".encode()).hexdigest()[:16], 16)


def variable(name, lower=0, upper=None, kind="continuous"):
    return {"name": name, "lower": lower, "upper": upper, "type": kind}


def row(name, coefficients, sense="<=", rhs=0, **sides):
    return {"name": name, "coefficients": coefficients, "sense": sense, "rhs": rhs, **sides}


def model(name, variables, rows, costs, constant=0, sense="minimize"):
    return {
        "name": name,
        "sense": sense,
        "variables": variables,
        "constraints": rows,
        "objective": {"coefficients": costs, "constant": constant},
    }


def entry(
    identifier, group, payload, statuses=("optimal",), options=None, metadata=None, recipe=None
):
    return {
        "id": identifier,
        "group": group,
        "payload": payload,
        "expected_statuses": list(statuses),
        "options": {} if options is None else options,
        "metadata": {} if metadata is None else metadata,
        "recipe": {"kind": identifier.split("-")[0], "subseed": subseed(identifier)}
        if recipe is None
        else recipe,
    }


def _affine_tiny(payload, variant):
    """Physical z=(x-offset)/direction, retaining exact dyadic input arithmetic."""
    p = copy.deepcopy(payload)
    for j, v in enumerate(p["variables"]):
        name = v["name"]
        offset = (-2, -0.5, 0)[(variant + j) % 3]
        direction = -1 if (variant + j) % 4 == 0 else 1
        lower, upper = v["lower"], v["upper"]
        v["lower"], v["upper"] = (
            (offset + lower, offset + upper) if direction == 1 else (offset - upper, offset - lower)
        )
        cost = p["objective"]["coefficients"].get(name, 0) / direction
        p["objective"]["coefficients"][name] = cost
        p["objective"]["constant"] -= cost * offset
        for r in p["constraints"]:
            if name in r["coefficients"]:
                value = r["coefficients"][name] / direction
                r["coefficients"][name] = value
                if "lower" in r or "upper" in r:
                    for side in ("lower", "upper"):
                        if r.get(side) is not None:
                            r[side] += value * offset
                else:
                    r["rhs"] += value * offset
    # Free and upper-only variables retain their finite physical domain as rows.
    v = p["variables"][variant % len(p["variables"])]
    if v["lower"] != v["upper"] and variant % 3 == 0:
        p["constraints"].append(
            row("explicit_box", {v["name"]: 1}, lower=v["lower"], upper=v["upper"])
        )
        v["lower"] = v["upper"] = None
    elif v["lower"] != v["upper"] and variant % 3 == 1:
        p["constraints"].append(row("explicit_lower", {v["name"]: 1}, ">=", v["lower"]))
        v["lower"] = None
    if variant % 4 == 3:
        p["constraints"].append(row("zero", {}, "<=", 1))
    if variant % 2:
        p["sense"] = "maximize"
        p["objective"]["coefficients"] = {n: -c for n, c in p["objective"]["coefficients"].items()}
        p["objective"]["constant"] *= -1
    assert len(p["variables"]) <= 4 and len(p["constraints"]) <= 8
    return p


def tiny_cases():
    records = []
    for family in ("NET", "TRANS", "BLOCK", "GENERAL"):
        for i in range(1, 13):
            identifier = f"TINY-{family}-{i:02}"
            rng = random.Random(subseed(identifier))
            names = [f"x{j}" for j in range(4)]
            variables = [variable(n, 0, 3) for n in names]
            costs = {n: rng.randrange(-8, 9) / 4 for n in names}
            if family == "NET":
                demand = 1 + (i % 3) / 2
                rows = [
                    row("source", {"x0": 1, "x2": 1}, "=", demand),
                    row("transit", {"x0": 1, "x3": 1, "x1": -1}, "=", 0),
                ]
            elif family == "TRANS":
                rows = [
                    row("supply0", {"x0": 1, "x1": 1}, "=", 1),
                    row("supply1", {"x2": 1, "x3": 1}, "=", 2),
                    row("demand0", {"x0": 1, "x2": 1}, "=", 1.5),
                ]
            elif family == "BLOCK":
                rows = [
                    row("block0", {"x0": 1, "x1": 1}, "<=", 2),
                    row("block1", {"x2": 1, "x3": 1}, "<=", 2),
                    row("couple", {"x1": 1, "x2": 1}, lower=0.5, upper=2.5),
                ]
            else:
                rows = [
                    row("interval", {"x0": 1, "x1": 2, "x2": -1}, lower=0, upper=3),
                    row("mix", {"x0": -1, "x2": 1, "x3": 2}, "<=", 4),
                ]
            if i == 5:
                variables[3]["lower"] = variables[3]["upper"] = 0.5 if family == "TRANS" else 0
            if i == 12 and family == "GENERAL":
                for r in rows:
                    r["coefficients"].pop("x3", None)
                costs["x3"] = 0
            payload = _affine_tiny(
                model(identifier, variables, rows, costs, 7 if i % 3 == 0 else -0.375), i
            )
            records.append(
                entry(
                    identifier,
                    "tiny",
                    payload,
                    options={"time_limit": 10},
                    metadata={"oracle": "independent_fraction_vertices", "family": family},
                )
            )
    return records


def pressure_cases():
    records = []
    base = model(
        "pressure",
        [variable("x", 0, 3), variable("y", 0, 3)],
        [row("cap", {"x": 1, "y": 1}, "<=", 3), row("low", {"x": 1}, ">=", 0.5)],
        {"x": -2, "y": -1},
        0.25,
    )
    for i in range(1, 9):
        p = copy.deepcopy(base)
        if i <= 4:
            p["constraints"].append(row("redundant", {"x": i + 1, "y": i + 1}, "<=", 3 * (i + 1)))
            p["constraints"].append(row("zero", {}, "=", 0))
        else:
            factor = (1e-6, 1e-2, 1e2, 1e6)[i - 5]
            for r in p["constraints"]:
                r["coefficients"] = {n: factor * c for n, c in r["coefficients"].items()}
                r["rhs"] *= factor
        identifier = f"PRESS-OPT-{i:02}"
        p["name"] = identifier
        records.append(
            entry(
                identifier,
                "pressure",
                p,
                options={"presolve": False, "time_limit": 10},
                metadata={"oracle": "independent_fraction_vertices"},
            )
        )
    for i in range(1, 5):
        factor = (1, 2, 0.5, 4)[i - 1]
        p = model(
            f"PRESS-INF-{i:02}",
            [variable("x"), variable("y")],
            [
                row("upper", {"x": factor, "y": factor}, "<=", 0),
                row("lower", {"x": factor, "y": factor}, ">=", factor),
            ],
            {},
        )
        r = entry(
            p["name"],
            "pressure",
            p,
            ("infeasible",),
            {"time_limit": 10},
            {"oracle": "exact_raw_farkas"},
        )
        r["candidate"] = {"row_duals": {"upper": -1, "lower": 1}}
        records.append(r)
        p = model(
            f"PRESS-UNB-{i:02}",
            [variable("x"), variable("y")],
            [row("balance", {"x": factor, "y": -factor}, "=", factor)],
            {"x": -1, "y": -1},
            i - 3,
        )
        r = entry(
            p["name"],
            "pressure",
            p,
            ("unbounded",),
            {"presolve": False, "time_limit": 10},
            {"oracle": "exact_raw_point_ray"},
        )
        r["candidate"] = {"point": {"x": 1, "y": 0}, "ray": {"x": 1, "y": 1}}
        records.append(r)
    for i in range(1, 5):
        epsilon = 0 if i <= 2 else 2 ** (-40 if i == 3 else -36)
        p = model(
            f"PRESS-NUM-{i:02}",
            [variable("x", 0, 2), variable("y", 0, 2)],
            [
                row("a", {"x": 1, "y": 1}, "=", 1),
                row("b", {"x": 2, "y": 2 * (1 + epsilon)}, "=", 2),
            ],
            {"x": 1} if i <= 2 else {"y": -1},
        )
        records.append(
            entry(
                p["name"],
                "pressure",
                p,
                ("optimal",) if i <= 2 else ("optimal", "numerical_failure"),
                {"presolve": False, "time_limit": 10},
                {"oracle": "independent_fraction_vertices", "numeric_conservative_allowed": i > 2},
            )
        )
    limits = (
        ("time_limit", 0, "time_limit"),
        ("lp_iteration_limit", 0, "lp_iteration_limit"),
        ("max_sparse_nnz", 0, "sparse_nnz_limit"),
        ("max_factor_nnz", 0, "factor_nnz_limit"),
    )
    for i, (option, value, reason) in enumerate(limits, 1):
        p = copy.deepcopy(base)
        p["name"] = f"PRESS-LIMIT-{i:02}"
        records.append(
            entry(
                p["name"],
                "pressure",
                p,
                ("limit",),
                {"time_limit": 10, option: value},
                {"expected_reason": reason, "oracle": "declared_resource_exit"},
            )
        )
    return records


def _active_and_base(family, n, m, rng):
    names = [f"x{j}" for j in range(n)]
    positive, base, role = {}, [], ""
    if family in ("TRANS", "ASSIGN"):
        if family == "ASSIGN":
            supply = demand = math.isqrt(n)
            assert supply * demand == n
            matchings = 8 if supply < 20 else 4
            for shift in range(matchings):
                for r in range(supply):
                    positive[r * demand + (r + shift) % demand] = 1 / matchings
            role = "continuous bipartite assignment with distinct resource side constraints"
        else:
            supply = 20 if n == 400 else 30 if n == 1500 else math.isqrt(n)
            demand = n // supply
            assert supply * demand == n
            for shift in range(max(2, math.ceil(64 / demand))):
                for c in range(demand):
                    positive[(c % supply) * demand + (c + shift) % demand] = 1
            role = "transportation supply/demand conservation with lane-resource side constraints"
        for r in range(supply):
            coeff = {names[r * demand + c]: 1 for c in range(demand)}
            rhs = sum(positive.get(r * demand + c, 0) for c in range(demand))
            base.append(row(f"supply_{r:03}", coeff, "=", rhs))
        for c in range(demand - 1):
            coeff = {names[r * demand + c]: 1 for r in range(supply)}
            rhs = sum(positive.get(r * demand + c, 0) for r in range(supply))
            base.append(row(f"demand_{c:03}", coeff, "=", rhs))
    elif family == "INVENT":
        products = 10 if n == 600 else 20 if n == 1200 else 6
        periods = n // (2 * products)
        assert 2 * products * periods == n
        produce = products * periods
        active_periods = min(periods, max(6, math.ceil(64 / products)))
        positive = {j: 1 for j in range(products * active_periods)}
        for t in range(periods):
            for p in range(products):
                j = t * products + p
                coeff = {names[produce + j]: 1, names[j]: -1}
                if t:
                    coeff[names[produce + j - products]] = -1
                base.append(row(f"stock_{t:03}_{p:03}", coeff, "=", -positive.get(j, 0)))
        role = "multi-product inventory balance with production/storage resource constraints"
    else:
        count = min(80, n // 2)
        if family == "BLOCK":
            blocks = 8 if n % 8 == 0 else 10
            width = n // blocks
            assert width * blocks == n
            for b in range(blocks):
                for j in range(min(10, width // 2)):
                    positive[b * width + j] = 1
            role = "block-angular local resource facets and cross-block coupling resources"
        else:
            positive = dict.fromkeys(range(count), 1)
            role = "general nonnegative sparse coupling with independent raw primal/dual proof"
        if family == "FLOW":
            nodes = max(8, min(n // 4, 180))
            for node in range(nodes - 1):
                coeff = {}
                for j, name in enumerate(names):
                    tail = j % nodes
                    head = (tail + 1 + j // nodes) % nodes
                    value = int(tail == node) - int(head == node)
                    if value:
                        coeff[name] = value
                rhs = sum(c * positive.get(int(name[1:]), 0) for name, c in coeff.items())
                base.append(row(f"flow_{node:03}", coeff, "=", rhs))
            role = "directed network flow conservation with shared arc-resource side constraints"
    assert len(base) + len(positive) < m
    return positive, base, role


def capacity_payload(identifier, family, n, m, width=None):
    rng = random.Random(subseed(identifier))
    names = [f"x{j}" for j in range(n)]
    positive, base, role = _active_and_base(family, n, m, rng)
    active = sorted(positive)
    inactive = [j for j in range(n) if j not in positive]
    width = (20 if family == "BLOCK" else 8 if n < 1000 else 12) if width is None else width
    width = min(n, width)
    constraints, duals = list(base), {}
    for position, j in enumerate(active):
        if family == "BLOCK":
            blocks = 8 if n % 8 == 0 else 10
            block_width = n // blocks
            near = [a for a in active if a // block_width == j // block_width]
            possible = [a for a in inactive if a // block_width == j // block_width]
        else:
            near, possible = active, inactive
        at = near.index(j)
        coefficients = {names[j]: 4}
        for step, coefficient in ((1, 0.25), (2, 0.125)):
            if len(near) > step:
                coefficients[names[near[(at + step) % len(near)]]] = coefficient
        take = min(width - len(coefficients), len(possible))
        for other in rng.sample(possible, take):
            coefficients[names[other]] = rng.randrange(1, 5) / 64
        # Very narrow diagnostic blocks may need additional active support.
        for other in near:
            if len(coefficients) >= width:
                break
            coefficients.setdefault(names[other], 1 / 64)
        rhs = sum(c * positive.get(int(name[1:]), 0) for name, c in coefficients.items())
        name = f"cap_{position:04}"
        constraints.append(row(name, coefficients, "<=", rhs))
        duals[name] = -1
    for i in range(m - len(constraints)):
        if family == "BLOCK" and i % 7:
            blocks = 8 if n % 8 == 0 else 10
            block_width = n // blocks
            b = i % blocks
            support = [b * block_width + (i + j) % block_width for j in range(width)]
        else:
            support = [(i * width + j) % n for j in range(width)]
        coefficients = {names[j]: rng.randrange(1, 9) / 8 for j in support}
        rhs = sum(c * positive.get(int(name[1:]), 0) for name, c in coefficients.items())
        rhs += (1 + i % 5) / 8
        constraints.append(row(f"resource_{i:04}", coefficients, "<=", rhs))
    cost = dict.fromkeys(names, 1)
    for j in active:
        cost[names[j]] = -sum(
            r["coefficients"].get(names[j], 0) for r in constraints if r["name"] in duals
        )
    p = model(identifier, [variable(name) for name in names], constraints, cost, 0.375)
    candidate = {"point": {names[j]: value for j, value in positive.items()}, "row_duals": duals}
    metadata = {
        "structural_role": role,
        "positive_optimum_coordinates": len(positive),
        "base_conservation_rows": len(base),
        "resource_rows": m - len(base),
        "candidate_is_not_accepted_truth": True,
    }
    return p, candidate, metadata


def capacity_cases():
    records = []
    for family, variant, n, m, nnz_cap in CAPACITY:
        identifier = f"CAP-{family}-{variant:02}"
        p, candidate, metadata = capacity_payload(identifier, family, n, m)
        metadata.update(
            nnz_cap=nnz_cap,
            require_coupled_pivots=identifier in PIVOT_CAPACITY_IDS,
            minimum_pivots=20 if identifier in PIVOT_CAPACITY_IDS else 0,
            sp2_smoke=identifier in ("CAP-FLOW-01", "CAP-TRANS-01"),
            peak_rss_limit_bytes=1024**3,
        )
        r = entry(
            identifier,
            "capacity",
            p,
            options={
                "time_limit": 120,
                "lp_iteration_limit": 100000,
                "presolve": identifier not in PIVOT_CAPACITY_IDS,
            },
            metadata=metadata,
            recipe={
                "kind": "capacity",
                "family": family,
                "variables": n,
                "rows": m,
                "subseed": subseed(identifier),
            },
        )
        r["candidate"] = candidate
        records.append(r)
    return records


def mechanism_cases():
    profiles = (
        ("FLOW", 128, 192),
        ("TRANS", 100, 160),
        ("ASSIGN", 144, 160),
        ("BLOCK", 160, 192),
        ("INVENT", 120, 140),
        ("GENERAL", 128, 192),
        ("BLOCK", 192, 256),
        ("GENERAL", 256, 320),
    )
    records = []
    for i, (family, n, m) in enumerate(profiles, 1):
        identifier = f"UPDATE-{i:02}"
        p, candidate, metadata = capacity_payload(identifier, family, n, m)
        metadata.update(
            diagnostic_of=f"CAP-{family}-01",
            minimum_pivots=50,
            minimum_true_update_fraction=0.7,
            stable_update_group=True,
        )
        r = entry(
            identifier,
            "mechanism",
            p,
            options={"time_limit": 60, "presolve": False, "lp_iteration_limit": 100000},
            metadata=metadata,
            recipe={
                "kind": "capacity_diagnostic",
                "family": family,
                "variables": n,
                "rows": m,
                "subseed": subseed(identifier),
            },
        )
        r["candidate"] = candidate
        records.append(r)
    return records


def mip_cases():
    records = []
    for family in ("KNAP", "MULTIKNAP", "COVER", "FACILITY", "ASSIGN", "FIXEDCOST"):
        for i in (1, 2):
            identifier = f"MIP-{family}-{i:02}"
            variables = [variable(f"x{j}", 0, 1, "binary") for j in range(5)]
            costs = {f"x{j}": -(3, 4, 7, 10, 15)[j] for j in range(5)}
            constraints = [
                row(
                    "capacity",
                    dict(zip(costs, (2, 3, 5, 7, 11), strict=True)),
                    "<=",
                    13.5 if i == 1 else 15.5,
                )
            ]
            if family == "MULTIKNAP":
                constraints.append(
                    row(
                        "resource",
                        dict(zip(costs, (3, 1, 4, 2, 5), strict=True)),
                        "<=",
                        7.5 if i == 1 else 9.5,
                    )
                )
            elif family == "COVER":
                costs = {f"x{j}": j + 1 for j in range(5)}
                constraints = [
                    row(
                        "cover",
                        {f"x{j}": (2, 3, 1, 4, 2)[j] for j in range(5)},
                        ">=",
                        5.5 if i == 1 else 6.5,
                    )
                ]
            elif family == "FACILITY":
                variables = [
                    variable("b0", 0, 1, "binary"),
                    variable("b1", 0, 1, "binary"),
                    variable("f0", 0, 3),
                    variable("f1", 0, 3),
                ]
                costs = {"b0": 2, "b1": 3, "f0": 0.5, "f1": 0.25}
                constraints = [
                    row("demand", {"f0": 1, "f1": 1}, ">=", 3.5 if i == 1 else 4.5),
                    row("open0", {"f0": 1, "b0": -3}, "<=", 0),
                    row("open1", {"f1": 1, "b1": -3}, "<=", 0),
                ]
            elif family == "ASSIGN":
                variables = [variable(f"x{j}", 0, 1, "binary") for j in range(4)]
                costs = {"x0": -3, "x1": -1, "x2": -1, "x3": -4 - i}
                constraints = [
                    row("person0", {"x0": 1, "x1": 1}, "=", 1),
                    row("person1", {"x2": 1, "x3": 1}, "=", 1),
                    row("task0", {"x0": 1, "x2": 1}, "=", 1),
                    row("diagonal_resource", {"x0": 1, "x3": 1}, "<=", 1.5),
                ]
            elif family == "FIXEDCOST":
                variables = [variable("b", 0, 1, "binary"), variable("f", 0, 4)]
                costs = {"b": 2 + i, "f": 0.5}
                constraints = [
                    row("demand", {"f": 1}, ">=", 1.5 if i == 1 else 2.5),
                    row("activation", {"f": 1, "b": -(2 if i == 1 else 3)}, "<=", 0),
                ]
            p = model(identifier, variables, constraints, costs, -0.5)
            branch = family in ("KNAP", "MULTIKNAP")
            records.append(
                entry(
                    identifier,
                    "mip",
                    p,
                    options={
                        "time_limit": 60,
                        "node_limit": 100000,
                        "lp_iteration_limit": 100000,
                        "presolve": False,
                        "heuristics": False,
                        "cuts": not branch,
                    },
                    metadata={
                        "family": family,
                        "require_branch": branch,
                        "require_gmi": family == "FIXEDCOST",
                        "oracle": "integer_fraction_enumeration",
                    },
                )
            )
    return records


def cg_cases():
    specifications = [
        (
            "CG-COVER",
            [{"name": "cover_a", "lower": 1}, {"name": "cover_b", "lower": 1}],
            [
                ("a", 3, {"cover_a": 1}),
                ("b", 2, {"cover_b": 1}),
                ("ab", 4, {"cover_a": 1, "cover_b": 1}),
                ("double_a", 1, {"cover_a": 2}),
            ],
            ["a", "b"],
            0,
        ),
        (
            "CG-GENERAL",
            [{"name": "r", "lower": 1, "upper": 3}, {"name": "s", "lower": 1, "upper": 3}],
            [
                ("a", 3, {"r": 2}),
                ("b", 3, {"s": 1}),
                ("ab", 4, {"r": 1, "s": 1}),
                ("cheap_ab", 0.5, {"r": 1, "s": 1}),
            ],
            [],
            7,
        ),
        ("CG-TINYRC", [{"name": "cap", "upper": 1e12}], [("x", -1e-8, {"cap": 1})], [], 0),
        (
            "CG-UNBOUNDED-GUARD",
            [{"name": "r1", "lower": 1, "upper": 1}, {"name": "r2", "lower": 2, "upper": 2}],
            [
                ("a", 0, {"r1": 1, "r2": 1}),
                ("b", -1e7, {"r1": 1, "r2": 2}),
                ("c", -1, {"r1": -1, "r2": -1}),
            ],
            ["a", "b"],
            0,
        ),
    ]
    records = []
    for identifier, intervals, pool, initial, constant in specifications:
        costs = {name: cost for name, cost, _ in pool if name in initial}
        constraints = []
        for interval in intervals:
            name = interval["name"]
            coefficients = {n: a[name] for n, _, a in pool if n in initial and name in a}
            constraints.append(
                row(name, coefficients, lower=interval.get("lower"), upper=interval.get("upper"))
            )
        p = model(identifier, [variable(name) for name in initial], constraints, costs, constant)
        if identifier == "CG-COVER":
            p["name"] = "general_covering_cg"
        statuses = (
            ("unbounded", "numerical_failure", "limit")
            if identifier.endswith("GUARD")
            else ("optimal",)
        )
        r = entry(
            identifier,
            "cg",
            p,
            statuses,
            {"time_limit": 60, "presolve": False},
            {
                "max_cg_iterations": 20,
                "require_phase1_added_column": identifier == "CG-GENERAL",
                "require_phase2_cross_solve_reuse": identifier == "CG-GENERAL",
            },
        )
        r["pool"] = [{"name": n, "cost": c, "coefficients": a} for n, c, a in pool]
        if identifier == "CG-COVER":
            r["metadata"]["public_example"] = "silo.decomposition.general_master.covering_example"
        records.append(r)
    return records


def build_trajectories():
    profiles = (
        ("RHS", 1, "GENERAL", 128, 160),
        ("RHS", 2, "GENERAL", 1000, 600),
        ("BOUND", 1, "GENERAL", 160, 220),
        ("BOUND", 2, "TRANS", 400, 600),
        ("ROW", 1, "GENERAL", 128, 160),
        ("ROW", 2, "GENERAL", 512, 700),
        ("COL", 1, "GENERAL", 128, 160),
        ("COL", 2, "GENERAL", 1000, 600),
    )
    result = []
    for kind, index, family, n, m in profiles:
        identifier = f"WARM-{kind}-{index:02}"
        p, candidate, metadata = capacity_payload(identifier, family, n, m)
        controls = list(candidate["point"])
        caps = list(candidate["row_duals"])
        edits = []
        if kind == "BOUND":
            p["variables"][int(controls[0][1:])]["upper"] = 2
        for step in range(20):
            if kind == "RHS":
                cap = next(r for r in p["constraints"] if r["name"] == caps[step])
                edits.append(
                    {"kind": "rhs", "row": cap["name"], "rhs": cap["rhs"] + ((step % 5) - 2) / 32}
                )
            elif kind == "BOUND":
                edits.append(
                    {
                        "kind": "bounds",
                        "variable": controls[0],
                        "lower": 0,
                        "upper": candidate["point"][controls[0]] * (1 - (step + 1) / 1024),
                    }
                )
            elif kind == "ROW":
                coefficients = {
                    controls[2 * step % len(controls)]: 1,
                    controls[(2 * step + 1) % len(controls)]: 1,
                }
                rhs = sum(candidate["point"][name] for name in coefficients) - 1 / 32
                edits.append(
                    {
                        "kind": "append_row",
                        "row": row(f"edit_row_{step:02}", coefficients, "<=", rhs),
                    }
                )
            else:
                edits.append(
                    {
                        "kind": "append_column",
                        "variable": variable(f"new_{step:02}"),
                        "cost": -3,
                        "coefficients": {caps[2 * step]: 1, caps[2 * step + 1]: 1},
                    }
                )
        result.append(
            {
                "id": identifier,
                "group": "warm",
                "initial_payload": p,
                "edits": edits,
                "candidate": candidate,
                "expected_statuses": ["optimal"],
                "options": {"presolve": False, "lp_iteration_limit": 100000},
                "metadata": {
                    **metadata,
                    "kind": kind,
                    "modifications": 20,
                    "minimum_variables": n,
                    "minimum_rows": m,
                    "per_chain_seconds_including_initial": 60,
                },
                "recipe": {
                    "kind": "warm",
                    "family": family,
                    "variables": n,
                    "rows": m,
                    "subseed": subseed(identifier),
                },
            }
        )
    return result


def apply_edit(payload, edit):
    p = copy.deepcopy(payload)
    kind = edit["kind"]
    if kind == "rhs":
        next(r for r in p["constraints"] if r["name"] == edit["row"])["rhs"] = edit["rhs"]
    elif kind == "bounds":
        v = next(v for v in p["variables"] if v["name"] == edit["variable"])
        v["lower"], v["upper"] = edit["lower"], edit["upper"]
    elif kind == "append_row":
        p["constraints"].append(copy.deepcopy(edit["row"]))
    elif kind == "append_column":
        p["variables"].append(copy.deepcopy(edit["variable"]))
        name = edit["variable"]["name"]
        p["objective"]["coefficients"][name] = edit["cost"]
        for r in p["constraints"]:
            if edit["coefficients"].get(r["name"], 0):
                r["coefficients"][name] = edit["coefficients"][r["name"]]
    else:
        raise ValueError(f"Unknown frozen edit {kind}")
    return p


def structural_stats(payload):
    names = [v["name"] for v in payload["variables"]]
    used = {n for r in payload["constraints"] for n, c in r["coefficients"].items() if c}
    signatures = [
        tuple(sorted((n, c) for n, c in r["coefficients"].items() if c))
        for r in payload["constraints"]
    ]
    return {
        "variables": len(names),
        "rows": len(payload["constraints"]),
        "nonfixed_variables": sum(
            not (v["lower"] is not None and v["upper"] is not None and v["lower"] == v["upper"])
            for v in payload["variables"]
        ),
        "matrix_nonzeros": sum(len(r["coefficients"]) for r in payload["constraints"]),
        "zero_columns": sorted(set(names) - used),
        "zero_rows": sum(not s for s in signatures),
        "duplicate_coefficient_rows": len(signatures) - len(set(signatures)),
    }


def build_cases(include_external=False, root=ROOT):
    cases = [
        *tiny_cases(),
        *pressure_cases(),
        *capacity_cases(),
        *mechanism_cases(),
        *mip_cases(),
        *cg_cases(),
    ]
    if include_external:
        from .netlib_data import load_external_cases

        cases += load_external_cases(root)
    return sorted(cases, key=lambda c: (GROUP_ORDER.index(c["group"]), c["id"]))


def write_input_freeze(root=ROOT, include_external=True):
    root = Path(root)
    folder = root / "outputs/sparse_lp_program_20261024/inputs/models"
    folder.mkdir(parents=True, exist_ok=True)
    records = []
    for item in build_cases(include_external, root):
        stats = structural_stats(item["payload"])
        if item["group"] in ("capacity", "mechanism"):
            assert not stats["zero_columns"] and not stats["zero_rows"]
            assert stats["duplicate_coefficient_rows"] == 0
            if item["group"] == "capacity":
                assert stats["matrix_nonzeros"] <= item["metadata"]["nnz_cap"]
        path = folder / (item["id"] + ".json")
        _same_or_new(path, canonical(item["payload"]))
        record = {k: v for k, v in item.items() if k not in ("payload", "candidate")}
        record.update(
            payload_sha256=sha(item["payload"]),
            statistics=stats,
            payload_path=str(path.relative_to(root)).replace("\\", "/"),
        )
        if "candidate" in item:
            record["candidate_sha256"] = sha(item["candidate"])
        records.append(record)
    trajectories = []
    for chain in build_trajectories():
        p = chain["initial_payload"]
        initial = folder / (chain["id"] + "-initial.json")
        _same_or_new(initial, canonical(p))
        states = []
        for index, edit in enumerate(chain["edits"], 1):
            p = apply_edit(p, edit)
            path = folder / (chain["id"] + f"-{index:02}.json")
            _same_or_new(path, canonical(p))
            states.append(
                {
                    "id": chain["id"] + f"-{index:02}",
                    "edit": edit,
                    "payload_sha256": sha(p),
                    "payload_path": str(path.relative_to(root)).replace("\\", "/"),
                }
            )
        record = {
            k: v for k, v in chain.items() if k not in ("initial_payload", "candidate", "edits")
        }
        record.update(
            initial_sha256=sha(chain["initial_payload"]),
            states=states,
            initial_path=str(initial.relative_to(root)).replace("\\", "/"),
        )
        trajectories.append(record)
    manifest = {
        "program": "SILO-SPARSE-LP-20261024",
        "schema": 1,
        "seed": SEED,
        "ordering": "fixed GROUP_ORDER then lexicographic ID; independent SHA256(seed:ID) sub-seed",
        "serialization": (
            "UTF-8 json sort_keys,separators comma/colon,LF final newline; "
            "binary floats preserved"
        ),
        "cases": records,
        "trajectories": trajectories,
        "fixed_denominators": {
            "tiny": 48,
            "pressure": 24,
            "capacity": 12,
            "netlib": 12,
            "mechanism": 8,
            "warm_chains": 8,
            "warm_modified_states": 160,
            "warm_timed_state_solves_per_round": 1600,
            "warm_initial_solves_per_round": 80,
            "mip": 12,
            "cg": 4,
        },
        "thresholds": {
            "capacity_seconds": 120,
            "capacity_peak_rss_bytes": 1024**3,
            "objective_relative_tolerance": 1e-7,
            "warm_repetitions": 5,
            "warm_median_ratio": 1.5,
            "warm_non_slower_chains": 6,
            "stable_update_fraction": 0.7,
            "max_eta_updates": 20,
        },
        "budgets_seconds": {
            "SP1": 1800,
            "SP2": 3600,
            "SP3": 10800,
            "SP4": 10800,
            "reserve": 1800,
            "total": 28800,
        },
        "round_caps": {
            "stage_attempts": 3,
            "capacity_netlib": 2,
            "warm": 2,
            "full_quality": 3,
            "extra_diagnostic_batches": 20,
            "extra_diagnostic_batch_seconds": 60,
            "environment_retry_per_install": 1,
        },
        "source_rule": (
            "all input definitions freeze before SILO baseline or product implementation"
        ),
    }
    _same_or_new(root / "tests/fixtures/sparse_program_manifest.json", canonical(manifest))
    return manifest
