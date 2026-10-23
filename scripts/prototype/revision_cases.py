"""Immutable input recipes for the four confirmed 2026-10-24 repair findings.

Inputs and exact target values precede the implementations intended to pass them.
No production solver imports. The old prototype and independent audit stay intact.
"""

import itertools


def mip_case(sense="minimize", small=False, constant=0, heuristics=True, primal=None):
    sign = 1 if sense == "minimize" else -1
    costs = (6e-8, 1e-7) if small else (0.006, 0.01)
    return {
        "payload": {
            "name": "prune",
            "sense": sense,
            "variables": [
                {"name": n, "lower": 0, "upper": 1, "type": "binary"} for n in ("x", "y")
            ],
            "constraints": [{"name": "cover", "coefficients": {"x": 2, "y": 3}, "lower": 3}],
            "objective": {
                "coefficients": dict(zip(("x", "y"), (sign * c for c in costs), strict=True)),
                "constant": constant,
            },
        },
        "options": {
            "presolve": False,
            "cuts": False,
            "heuristics": heuristics,
            "primal_tolerance": (1e-7 if small else 0.01) if primal is None else primal,
            "dual_tolerance": 1e-12,
            "objective_tolerance": 1e-12,
        },
        "expected_status": "optimal",
        "expected_objective": constant + sign * costs[1],
        "expected_point": {"x": 0, "y": 1},
    }


def cg_case(unbounded=False):
    if not unbounded:
        return {
            "name": "cg_cap",
            "rows": [{"name": "cap", "coefficients": {}, "sense": "<=", "rhs": 1e12}],
            "initial": [],
            "pool": [{"name": "x", "cost": -1e-8, "coefficients": {"cap": 1}}],
            "expected_status": "optimal",
            "expected_objective": -10000,
        }
    return {
        "name": "cg_ray",
        "rows": [
            {"name": "r1", "coefficients": {"a": 1, "b": 1}, "sense": "=", "rhs": 1},
            {"name": "r2", "coefficients": {"a": 1, "b": 2}, "sense": "=", "rhs": 2},
        ],
        "initial": ["a", "b"],
        "pool": [
            {"name": "a", "cost": 0, "coefficients": {"r1": 1, "r2": 1}},
            {"name": "b", "cost": -10000000, "coefficients": {"r1": 1, "r2": 2}},
            {"name": "c", "cost": -1, "coefficients": {"r1": -1, "r2": -1}},
        ],
        "expected_status": "unbounded_or_conservative",
        "exact_ray": {"a": 1, "b": 0, "c": 1},
        "exact_anchor": {"a": 0, "b": 1, "c": 0},
    }


def cases():
    records = []
    for i, (sense, small, constant, heuristic) in enumerate(
        itertools.product(
            ("minimize", "maximize"),
            (False, True),
            (0, 100),
            (False, True),
        )
    ):
        records.append(
            {"id": f"F1-{i:02}", "kind": "mip", **mip_case(sense, small, constant, heuristic)}
        )
    for i, sense in enumerate(("minimize", "maximize")):
        records.append({"id": f"F1-strict-{i}", "kind": "mip", **mip_case(sense, primal=1e-12)})
    for i, (unbounded, presolve, scaling) in enumerate(itertools.product((False, True), repeat=3)):
        records.append(
            {
                "id": f"F2-{i:02}",
                "kind": "cg",
                "model": cg_case(unbounded),
                "options": {"presolve": presolve, "scaling": scaling},
            }
        )
    for name, option in (
        ("node", {"node_limit": 0}),
        ("time", {"time_limit": 0}),
        ("pivot", {"lp_iteration_limit": 0}),
        ("gap", {"relative_gap": 1}),
    ):
        entry = mip_case()
        entry["options"].update(option)
        entry["expected_status"] = "limit"
        records.append({"id": "F1-limit-" + name, "kind": "mip_limit", **entry})
    for name, options in (
        ("time", {"time_limit": 0}),
        ("pivot", {"lp_iteration_limit": 0}),
        ("proof", {"proof_operation_limit": 0}),
        ("round", {}),
    ):
        records.append(
            {
                "id": "F2-limit-" + name,
                "kind": "cg_limit",
                "model": cg_case(),
                "options": options,
                "round_limit": 1 if name == "round" else 20,
            }
        )
    return records


def input_contract():
    return {
        "program": "SILO-PROTOTYPE-REVISION-20261024",
        "schema": 1,
        "seed": 20261024,
        "source_audit_commit": "4ca4bab47f2eecb8b60d5e34e767b4dc239fd969",
        "audit_model_json_sha256": (
            "4df0fbec29dc7afd7df66872d395bd5c52"
            "e7f31155c6c28e642050483383ddad"
        ),
        "targeted_cases": cases(),
        "mps": {
            "large_integer": 9007199254740993,
            "equivalent_tokens": [
                "9007199254740993",
                "9007199254740993.0",
                "9007199254740993.000",
                "9.007199254740993e15",
                "90071992547409930e-1",
            ],
            "fields": ["coefficient", "rhs", "lower", "upper"],
            "range_underflow": {
                "rhs_magnitude": "1e-300",
                "width": "0." + "9" * 100 + "e-300",
                "derived_magnitude": "1e-400",
                "row_types": ["L", "G", "E"],
                "range_signs": [-1, 1],
                "expected": "parse_rejection",
            },
        },
        "caps": {
            "targeted_public_calls": 128,
            "new_matrix_rounds": 2,
            "old_matrix_rounds": 2,
            "full_quality_runs": 3,
            "install_retries_per_combination": 1,
            "verification_seconds": 3600,
        },
    }
