"""Fixed prototype inputs, independent of every production solver module.

The manifest contains recipes/identities rather than generated benchmark data.
Scale generation and exact combinatorial reference values do not run a solver.
"""

import copy
import hashlib
import json
import random
from pathlib import Path

SEED = 20261023
ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "tests/fixtures/prototype_manifest.json"


def variable(name, lower=0, upper=None, kind="continuous"):
    return {"name": name, "lower": lower, "upper": upper, "type": kind}


def row(name, values, sense="<=", rhs=0, **sides):
    return {"name": name, "coefficients": values, "sense": sense, "rhs": rhs, **sides}


def model(variables, rows, costs, constant=0):
    return {
        "name": "frozen",
        "sense": "minimize",
        "variables": variables,
        "constraints": rows,
        "objective": {"coefficients": costs, "constant": constant},
    }


def small_lp(template):
    x, y = "x", "y"
    v = [variable(x, -2, 3), variable(y, 1, 4)]
    rows, costs = [], {x: 2, y: -1}
    if template == 1:
        v = [variable(x, None, None), variable(y, 0, 3)]
        rows, costs = [row("r", {x: 1, y: 2}, "=", 3)], {x: 1, y: -2}
    elif template == 2:
        v = [variable(x, None, 3), variable(y, -1, 2)]
        rows, costs = [row("lo", {x: 1}, ">=", -2)], {x: -1, y: 2}
    elif template == 3:
        v, rows, costs = [variable(x, 0, 2)], [row("fix", {x: 1}, "=", 1)], {x: 1}
    elif template == 4:
        v = [variable(x, -1, 3), variable(y, 0, 2)]
        rows = [row("range", {x: 2, y: -1}, lower=-1, upper=3)]
        costs = {x: -1, y: 0.5}
    elif template == 5:
        v = [variable(x, 0, 4), variable(y, 0, 3)]
        rows = [row("demand", {x: 1, y: 1}, ">=", 2), row("cap", {x: 2, y: 1}, "<=", 5)]
        costs = {x: 1, y: -1}
    elif template == 6:
        v = [variable(x, 0, 3), variable(y, 0, 3)]
        rows = [
            row("a", {x: 1, y: 1}, "<=", 3),
            row("dup", {x: 2, y: 2}, "<=", 6),
            row("lo", {x: 1}, ">=", 0.5),
        ]
        costs = {x: -1, y: -1}
    elif template == 7:
        v = [variable(x, 0, 3), variable(y, 0, 3)]
        rows = [
            row("a", {x: 10000, y: 10000}, "<=", 30000),
            row("b", {x: 0.001, y: -0.001}, ">=", 0.0005),
        ]
        costs = {x: -2, y: -1}
    elif template == 8:
        v = [variable(x, 0, 3)]
        rows, costs = [row("a", {x: 1}, ">=", 2), row("b", {x: 1}, "<=", 1)], {x: 1}
    elif template == 9:
        v = [variable(x, None, None), variable(y, 0, 1)]
        rows, costs = [row("lo", {y: 1}, ">=", 0.5)], {x: -1, y: 1}
    elif template == 10:
        v = [variable(x, -2, 4), variable(y, None, None), variable("z", 3, 3)]
        rows = [row("range", {x: 1, y: 1}, lower=1, upper=3)]
        return model(v, rows, {x: 1, y: 2, "z": 5}, 7)
    elif template == 11:
        v = [variable(x, None, None), variable(y, None, None)]
        rows, costs = [row("line", {x: 1, y: -1}, "=", 0)], {x: 1, y: -1}
    return model(v, rows, costs, 0.375)


def small_milp(template):
    count = 3 if template != 10 else 4
    v = [variable(f"x{i}", 0, 1, "binary") for i in range(count)]
    costs = {f"x{i}": -(i + 2) for i in range(count)}
    rows = [row("capacity", {f"x{i}": i + 1 for i in range(count)}, "<=", 3)]
    if template in (1, 2, 6):
        lower = {1: 0, 2: -2, 6: -3}[template]
        v = [variable(f"x{i}", lower, lower + 3, "integer") for i in range(3)]
        rows = [row("r", {"x0": 2, "x1": -1, "x2": 1}, "<=", 3)]
        costs = {"x0": -2, "x1": 3, "x2": -1}
        if template == 6:
            v[0] = variable("x0", -2, -2, "integer")
    elif template == 3:
        v = [variable("x0", 0, 3, "integer"), variable("x1", -1, 2, "integer"), variable("y", 0, 4)]
        rows = [
            row("demand", {"x0": 1, "x1": 1, "y": 1}, ">=", 2.5),
            row("link", {"y": 1, "x0": -2}, "<=", 1),
        ]
        costs = {"x0": 2, "x1": 1, "y": 0.5}
    elif template == 4:
        v = [
            variable("x0", -1, 2, "integer"),
            variable("x1", -1, 2, "integer"),
            variable("y", 0, 3),
            variable("z", 0, 3),
        ]
        rows = [
            row("d", {"x0": 1, "x1": 1, "y": 1, "z": 1}, ">=", 2.5),
            row("l", {"y": 2, "z": 1, "x0": -1}, "<=", 4),
        ]
        costs = {"x0": 2, "x1": -1, "y": 0.25, "z": 0.75}
    elif template == 5:
        v, rows, costs = (
            [variable("x", 0, 3, "integer")],
            [row("half", {"x": 1}, "=", 0.5)],
            {"x": 1},
        )
    elif template == 7:
        rows = [row("cover", {f"x{i}": 1 for i in range(3)}, ">=", 1.5)]
        costs = {"x0": 2, "x1": 1, "x2": 3}
    elif template == 8:
        rows = [row("p", {"x0": 1, "x1": 1}, "=", 1), row("q", {"x1": 1, "x2": 1}, "=", 1)]
    elif template == 9:
        v = [
            variable("x0", 0, 1, "binary"),
            variable("x1", 0, 1, "binary"),
            variable("f0", 0, 3),
            variable("f1", 0, 3),
        ]
        rows = [
            row("d", {"f0": 1, "f1": 1}, "=", 3),
            row("c0", {"f0": 1, "x0": -3}, "<=", 0),
            row("c1", {"f1": 1, "x1": -3}, "<=", 0),
        ]
        costs = {"x0": 2, "x1": 3, "f0": 2, "f1": 1}
    elif template == 10:
        rows = [
            row("p", {"x0": 1, "x1": 1}, "=", 1),
            row("q", {"x2": 1, "x3": 1}, "=", 1),
            row("c", {"x0": 2, "x2": 2}, "<=", 3),
        ]
    elif template == 11:
        v = [variable("x0", 0, 3, "integer"), variable("x1", 0, 3, "integer"), variable("y", 0, 3)]
        rows = [row("link", {"y": 1, "x0": -2, "x1": -1}, "<=", 0), row("d", {"y": 1}, ">=", 1.5)]
        costs = {"x0": 2, "x1": 1, "y": -0.5}
    return model(v, rows, costs, -0.5)


def variant(payload, index):
    p = copy.deepcopy(payload)
    if index in (1, 7):
        p["sense"] = "maximize"
        p["objective"]["coefficients"] = {k: -v for k, v in p["objective"]["coefficients"].items()}
        p["objective"]["constant"] *= -1
    if index in (2, 7):
        p["variables"].reverse()
        p["constraints"].reverse()
    if index in (3, 7):
        p["objective"]["constant"] += 7
    if index == 4:
        shifts = {v["name"]: (0 if v["type"] == "binary" else 1) for v in p["variables"]}
        for v in p["variables"]:
            for side in ("lower", "upper"):
                if v[side] is not None:
                    v[side] -= shifts[v["name"]]
        for r in p["constraints"]:
            shift = sum(a * shifts[n] for n, a in r["coefficients"].items())
            r["rhs"] -= shift
            for side in ("lower", "upper"):
                if r.get(side) is not None:
                    r[side] -= shift
        p["objective"]["constant"] += sum(
            c * shifts[n] for n, c in p["objective"]["coefficients"].items()
        )
    return p


def scale_lp(family, index):
    n = ((4, 6, 8, 10, 12, 14) if family in (0, 1) else (4, 8, 16, 32, 100, 128))[index]
    if family == 2:
        n = (8, 12, 20, 40, 100, 160)[index]
    v, rows, costs = [], [], {}
    if family in (0, 1):
        for i in range(n):
            for j in range(n):
                name = f"x{i}_{j}"
                v.append(variable(name))
                costs[name] = ((i % 3 + 1) if family == 1 else 0) + (
                    0 if i == j else 10 + abs(i - j)
                )
                rows.append(row(f"cap{i}_{j}", {name: 1}, "<=", 1))
        for i in range(n):
            rows.append(row(f"s{i}", {f"x{i}_{j}": 1 for j in range(n)}, "=", 1))
            rows.append(row(f"d{i}", {f"x{j}_{i}": 1 for j in range(n)}, "=", 1))
        optimum = 7 + (sum(i % 3 + 1 for i in range(n)) if family == 1 else 0)
    else:
        for i in range(n):
            name = f"x{i}"
            v.append(variable(name, -1 if family == 3 else 0, 2 if family == 3 else None))
            costs[name] = i + 1 if family == 2 else 1 if family == 3 else -1
            if family == 3:
                rows.append(row(f"r{i}", {name: 1, f"x{(i + 1) % n}": -1}, "<=", 4))
            elif family not in (4, 5):
                a = 10.0 ** ((i % 9) - 4) if family == 7 else 1
                rows.append(row(f"r{i}", {name: a}, "<=", a))
                if family == 6:
                    rows.append(row(f"dup{i}", {name: 2}, "<=", 2))
            elif family == 5 and i > 0:
                rows.append(row(f"r{i}", {name: 1}, "<=", 1))
        optimum = 7 - n
        if family == 2:
            rows.append(row("mix", {f"x{i}": 1 for i in range(n)}, ">=", 1))
            optimum = 8
        elif family == 4:
            rows += [row("lo", {"x0": 1}, ">=", 2), row("hi", {"x0": 1}, "<=", 1)]
    status = "infeasible" if family == 4 else "unbounded" if family == 5 else "optimal"
    p = model(v, rows, costs, 7)
    if family == 3 and index % 2:
        p["sense"] = "maximize"
        p["objective"]["coefficients"] = {name: -c for name, c in costs.items()}
        p["objective"]["constant"] = -7
        optimum = -optimum
    return p, status, optimum if status == "optimal" else None


def capacity_dp(caps, fixed, unit, demand):
    values = [0] + [10**12] * demand
    for cap, opening, cost in zip(caps, fixed, unit, strict=True):
        updated = values.copy()
        for used in range(demand + 1):
            for flow in range(1, min(cap, demand - used) + 1):
                updated[used + flow] = min(
                    updated[used + flow], values[used] + opening + flow * cost
                )
        values = updated
    return values[demand]


def scale_milp(family, index):
    n = (6, 10, 20, 24)[index]
    rng = random.Random(SEED + 100 * family + index)
    v = [variable(f"x{i}", 0, 1, "binary") for i in range(n)]
    rows, costs = [], {}
    if family in (0, 1):
        weights = [rng.randrange(1, 10) for _ in range(n)]
        second = [rng.randrange(1, 10) for _ in range(n)]
        profits = [rng.randrange(1, 16) for _ in range(n)]
        caps = (sum(weights) // 2, sum(second) // 2 if family else 0)
        dp = {(0, 0): 0}
        for a, b, profit in zip(weights, second, profits, strict=True):
            nxt = dict(dp)
            for (u, w), val in dp.items():
                key = u + a, w + (b if family else 0)
                if key[0] <= caps[0] and key[1] <= caps[1]:
                    nxt[key] = max(nxt.get(key, -1), val + profit)
            dp = nxt
        costs = {f"x{i}": -profits[i] for i in range(n)}
        rows = [row("capacity", {f"x{i}": weights[i] for i in range(n)}, "<=", caps[0])]
        if family:
            rows.append(row("capacity2", {f"x{i}": second[i] for i in range(n)}, "<=", caps[1]))
        optimum = -max(dp.values())
    elif family == 2:
        m = max(2, n // 3)
        cover = [sum((1 << j) for j in range(m) if rng.random() < 0.35) for _ in range(n)]
        for j in range(m):
            cover[j] |= 1 << j
        fees = [rng.randrange(1, 11) for _ in range(n)]
        dp = {0: 0}
        for mask, fee in zip(cover, fees, strict=True):
            nxt = dict(dp)
            for covered, value in dp.items():
                nxt[covered | mask] = min(nxt.get(covered | mask, 10**12), value + fee)
            dp = nxt
        for j in range(m):
            rows.append(
                row(f"cover{j}", {f"x{i}": 1 for i in range(n) if cover[i] & (1 << j)}, ">=", 1)
            )
        costs, optimum = {f"x{i}": fees[i] for i in range(n)}, dp[(1 << m) - 1]
    elif family in (3, 5):
        caps = [rng.randrange(1, 4) for _ in range(n)]
        fixed = [rng.randrange(2, 8) for _ in range(n)]
        unit = [rng.randrange(1, 5) for _ in range(n)]
        groups = (
            [list(range(n))]
            if family == 3
            else [list(range(i, min(i + 4, n))) for i in range(0, n, 4)]
        )
        for i in range(n):
            v.append(variable(f"f{i}", 0, caps[i]))
            rows.append(row(f"link{i}", {f"f{i}": 1, f"x{i}": -caps[i]}, "<=", 0))
            costs[f"x{i}"], costs[f"f{i}"] = fixed[i], unit[i]
        optimum = 0
        for j, group in enumerate(groups):
            demand = max(1, sum(caps[i] for i in group) // 2)
            rows.append(row(f"demand{j}", {f"f{i}": 1 for i in group}, "=", demand))
            optimum += capacity_dp(
                [caps[i] for i in group],
                [fixed[i] for i in group],
                [unit[i] for i in group],
                demand,
            )
    else:
        items = n // 2
        weights = [rng.randrange(1, 8) for _ in range(items)]
        first = [rng.randrange(1, 10) for _ in range(items)]
        second = [rng.randrange(1, 10) for _ in range(items)]
        total = sum(weights)
        cap = (3 * total + 4) // 5
        dp = {0: 0}
        for i, (weight, a, b) in enumerate(zip(weights, first, second, strict=True)):
            rows.append(row(f"item{i}", {f"x{2 * i}": 1, f"x{2 * i + 1}": 1}, "=", 1))
            costs[f"x{2 * i}"], costs[f"x{2 * i + 1}"] = a, b
            nxt = {}
            for used, val in dp.items():
                nxt[used] = min(nxt.get(used, 10**12), val + b)
                if used + weight <= cap:
                    nxt[used + weight] = min(nxt.get(used + weight, 10**12), val + a)
            dp = nxt
        rows += [
            row("cap0", {f"x{2 * i}": w for i, w in enumerate(weights)}, "<=", cap),
            row("cap1", {f"x{2 * i + 1}": w for i, w in enumerate(weights)}, "<=", cap),
        ]
        optimum = min(value for used, value in dp.items() if total - used <= cap)
    return model(v, rows, costs, 3), "optimal", optimum + 3


BOUNDARIES = [
    ("free_upper_range_combo", "optimal"),
    ("negative_integer_bounds", "optimal"),
    ("fixed_fractional_integer", "infeasible"),
    ("zero_row_contradiction", "infeasible"),
    ("no_rows_unbounded", "unbounded"),
    ("integer_ray", "unbounded"),
    ("lp_unbounded_mip_infeasible", "infeasible"),
    ("unresolved_unbounded_frontier", "limit"),
    ("node_limit", "limit"),
    ("time_limit", "limit"),
    ("lp_iteration_limit", "limit"),
    ("relative_gap_stop", "limit"),
    ("local_cut_scope", "optimal"),
    ("gmi_mixed_boundary", "optimal"),
    ("stale_basis", "optimal"),
    ("rhs_dual_simplex", "optimal"),
    ("append_row", "optimal"),
    ("append_column", "optimal"),
    ("scaled_kkt", "optimal"),
    ("singular_basis_recovery", "optimal"),
    ("nonfinite_input", "invalid_model"),
    ("malformed_mps", "invalid_model"),
    ("unsupported_mps", "unsupported"),
    ("numeric_overflow", "numerical_failure"),
]


def boundary_input(index):
    """Inputs AND controlled budgets are frozen before any algorithm run."""
    options, action = {}, None
    p = small_lp(5)
    if index == 0:
        p = small_lp(10)
    elif index == 1:
        p = small_milp(2)
    elif index == 2:
        p = model([variable("x", 0.5, 0.5, "integer")], [], {"x": 1})
    elif index == 3:
        p = model([variable("x", 0, 1)], [row("zero", {}, ">=", 1)], {})
    elif index == 4:
        p = model([variable("x", None, None)], [], {"x": -1})
    elif index == 5:
        p = model([variable("x", 0, None, "integer")], [], {"x": -1})
    elif index == 6:
        p = model(
            [variable("x", 0, 1, "integer"), variable("y")],
            [row("half", {"x": 1}, "=", 0.5)],
            {"y": -1},
        )
    elif index == 7:
        p = model([variable("x", 0, 1, "integer"), variable("y")], [], {"y": -1})
        options = {"integer_ray_proof_limit": 0}
    elif index in (8, 9):
        p = small_milp(0)
        options = {"node_limit" if index == 8 else "time_limit": 0}
    elif index == 10:
        options = {"lp_iteration_limit": 0}
    elif index == 11:
        p = model(
            [variable("x", 0, 1, "binary"), variable("y", 0, 1, "binary")],
            [row("d", {"x": 1, "y": 1}, ">=", 0.5)],
            {"x": 1, "y": 1},
        )
        options = {"relative_gap": 1, "cuts": False, "heuristics": True}
    elif index in (12, 13):
        p = small_milp(3 if index == 12 else 4)
        options = {"cuts": True, "heuristics": False}
    elif index in (14, 15, 16, 17, 19):
        p = model([variable("x", 0, 3)], [row("r", {"x": 1}, "<=", 2)], {"x": -1})
        action = {
            14: {"type": "stale_basis", "indices": [999]},
            15: {"type": "rhs", "row": "r", "rhs": 1},
            16: {"type": "append_row", "row": row("new", {"x": 1}, "<=", 1)},
            17: {
                "type": "append_column",
                "variable": variable("y", 0, 2),
                "coefficients": {"r": 1},
                "cost": -2,
            },
            19: {"type": "singular_basis", "duplicate_first": True},
        }[index]
        options = {"presolve": False, "scaling": False}
    elif index == 18:
        p = small_lp(7)
    elif index == 20:
        # JSON cannot encode NaN: the explicit mutation is part of input identity.
        action = {"type": "nonfinite", "target": "objective.x", "value": "NaN"}
    elif index in (21, 22):
        return {
            "format": "mps",
            "text": "NAME bad\nROWS\n L r\nCOLUMNS\n x r\nENDATA\n"
            if index == 21
            else "NAME bad\nQMATRIX\nENDATA\n",
            "options": {},
        }
    elif index == 23:
        p = model([variable("x", 1e308, 1e308)], [], {"x": 1e308})
    return {"format": "json", "model": p, "options": options, "action": action}


def payload_for(entry):
    suite, group, variant_id = entry["suite"], entry["family"], entry["variant"]
    if suite == "lp_small":
        return variant(small_lp(group), variant_id)
    if suite == "milp_small":
        return variant(small_milp(group), variant_id)
    return (scale_lp if suite == "lp_scale" else scale_milp)(group, variant_id)[0]


def digest(payload):
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    ).hexdigest()


def freeze():
    entries = []
    for suite, prefix, count, variants in (
        ("lp_small", "LP", 12, 8),
        ("milp_small", "MI", 12, 8),
        ("lp_scale", "LS", 8, 6),
        ("milp_scale", "MS", 6, 4),
    ):
        for group in range(count):
            for variant_id in range(variants):
                status = "optimal"
                expected = None
                if suite == "lp_small":
                    status = {8: "infeasible", 9: "unbounded"}.get(group, status)
                elif suite == "milp_small" and group == 5:
                    status = "infeasible"
                elif suite in ("lp_scale", "milp_scale"):
                    _, status, expected = (scale_lp if suite == "lp_scale" else scale_milp)(
                        group, variant_id
                    )
                entry = {
                    "id": f"{prefix}{group * variants + variant_id:03}",
                    "suite": suite,
                    "family": group,
                    "variant": variant_id,
                    "expected_status": status,
                    "expected_objective": expected,
                    "options": {"presolve": variant_id != 5, "scaling": variant_id != 6},
                }
                kind = (
                    "fraction_vertices"
                    if suite == "lp_small"
                    else "integer_enumeration_vertices"
                    if suite == "milp_small"
                    else "constructive"
                    if suite == "lp_scale"
                    else "independent_dp"
                )
                if suite == "lp_small" and group == 11:
                    kind = "exact_kkt_no_vertices"
                if status == "infeasible" and suite == "lp_small":
                    kind = "exact_farkas"
                if status == "unbounded":
                    kind = "exact_point_ray"
                entry.update(
                    oracle_kind=kind,
                    truth_source="scripts/prototype/freeze_manifest.py",
                    source_hash=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    expected_terminal_state=status,
                    oracle_operation_cap=2000000,
                    difficulty_group=f"{suite}_family_{group}",
                    seed=SEED,
                )
                payload = payload_for(entry)
                entry.update(
                    model_sha256=digest(payload),
                    variables=len(payload["variables"]),
                    rows=len(payload["constraints"]),
                )
                entries.append(entry)
    scale = [
        e
        for e in entries
        if e["suite"] == "lp_scale"
        and e["expected_status"] == "optimal"
        and 100 <= e["variables"] <= 200
        and 100 <= e["rows"] <= 400
    ]
    assert len(scale) >= 8
    metadata = {
        "program": "SILO-PROTOTYPE-20261023",
        "schema": 2,
        "seed": SEED,
        "recipe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "independent_oracle_sha256": hashlib.sha256(
            (Path(__file__).parent / "oracles.py").read_bytes()
        ).hexdigest(),
        "tolerances": {
            "primal": 1e-7,
            "dual": 1e-7,
            "integrality": 1e-7,
            "pivot": 1e-10,
            "objective_relative": 1e-7,
        },
        "oracle": "raw Fraction vertices; integer enumeration + <=2D vertices; constructive/DP",
        "budgets_seconds": {
            "M1": 600,
            "M2": 1500,
            "M3": 2100,
            "M4": 600,
            "M5": 8400,
            "reserve": 1200,
            "total": 14400,
        },
        "scale_limits": {
            "LP_seconds": 20,
            "MILP_seconds": 60,
            "MILP_nodes": 100000,
            "runs_max": 3,
            "only_stage": "M5",
        },
        "cases": entries,
        "boundaries": [
            {
                "id": f"B{i:02}",
                "name": name,
                "expected_status": status,
                "expected_terminal_state": status,
                "oracle_kind": "exact_or_controlled_boundary",
                "truth_source": "docs/prototype_model_contract.md",
                "source_hash": hashlib.sha256(
                    (ROOT / "docs/prototype_model_contract.md").read_bytes()
                ).hexdigest(),
                "oracle_operation_cap": 10000,
                "difficulty_group": name,
                "seed": SEED,
                "input": boundary_input(i),
                "input_sha256": digest(boundary_input(i)),
            }
            for i, (name, status) in enumerate(BOUNDARIES)
        ],
        "diagnostics": {
            "ids": ["LP000", "LP008", "LP032", "LP056", "MI000", "MI024", "MI072", "MI088"],
            "LP_variants": [
                "cold",
                "rhs_warm",
                "bound_warm",
                "row_warm",
                "column_warm",
                "presolve_off",
                "scaling_off",
                "invalid_basis_fallback",
            ],
            "MILP_variants": "eight combinations cuts x heuristic x best-bound/DFS",
            "calls_max": 64,
        },
    }
    integrations = {
        "finite_cg": {
            "row_lower": [1, 1],
            "row_upper": [None, None],
            "columns": [[1, 0], [0, 1], [1, 1], [2, 0]],
            "costs": [3, 2, 4, 1],
            "initial": [0, 1],
            "round_limit": 20,
            "expected_objective": 2.5,
            "oracle_kind": "fraction_vertices",
        },
        "mip_policy": {
            "model": small_milp(10),
            "node_limit": 1000,
            "oracle_kind": "integer_enumeration_vertices",
        },
    }
    metadata["integrations"] = {
        k: {**v, "input_sha256": digest(v)} for k, v in integrations.items()
    }
    assert len(entries) == 264 and len(metadata["boundaries"]) == 24
    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    if MANIFEST.exists():
        raise RuntimeError(
            "Manifest already frozen; do not replace expected data after implementation."
        )
    MANIFEST.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(
        f"Frozen 192 small + 24 boundary + 72 scale; {len(scale)} large LP scale cases"
    )


if __name__ == "__main__":
    freeze()
