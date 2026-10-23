"""M3 frozen MILPs, exact GMI derivation, frontier exits and local inheritance."""

import itertools
import json
import runpy
from fractions import Fraction as F
from math import inf
from pathlib import Path

import pytest

from silo import SolveOptions, solve
from silo.cuts.gmi import derive_gmi
from silo.io import model_from_dict
from silo.lp.tableau_view import AffineCoordinate, GmiTableauRow

ROOT = Path(__file__).resolve().parents[2]
RECIPES = runpy.run_path(str(ROOT / "scripts/prototype/freeze_manifest.py"))
ORACLE = runpy.run_path(str(ROOT / "scripts/prototype/oracles.py"))
MI = [
    e
    for e in json.loads((ROOT / "tests/fixtures/prototype_manifest.json").read_text())["cases"]
    if e["suite"] == "milp_small"
]


@pytest.mark.parametrize("entry", MI, ids=lambda e: e["id"])
def test_frozen_small_milp(entry):
    payload = RECIPES["payload_for"](entry)
    truth = ORACLE["exact_small"](payload, entry["suite"], entry["family"])
    result = solve(model_from_dict(payload), SolveOptions(**entry["options"]))
    assert result.status == truth["status"], result
    if result.status == "optimal":
        assert result.objective_value == pytest.approx(float(truth["objective"]), abs=1e-7)
        assert result.optimality["integer_feasible"]
        assert result.relative_gap == pytest.approx(0)
        assert not result.dual_values
    else:
        assert not result.has_primal_solution


def coordinate(name, index, integer):
    return AffineCoordinate((name,), F(0), tuple(F(int(j == index)) for j in range(2)), integer)


def test_pure_gmi_hand_derivation_and_complete_small_domain():
    row = GmiTableauRow(
        ("basic",),
        F(12, 5),
        (F(1, 5), F(3, 5)),
        (coordinate("z1", 0, True), coordinate("z2", 1, True)),
        True,
        (),
    )
    cut = derive_gmi(row, 2)
    assert cut.coefficients == (F(1, 5), F(4, 15))
    assert cut.lower == F(2, 5)
    for z1, z2 in itertools.product(range(13), repeat=2):
        basic = row.rhs - row.coefficients[0] * z1 - row.coefficients[1] * z2
        if basic >= 0 and basic.denominator == 1:
            assert cut.coefficients[0] * z1 + cut.coefficients[1] * z2 >= cut.lower
    assert 0 < cut.lower  # basic LP point zN=0 is removed


def test_mixed_gmi_continuous_boundary_and_negative_floor():
    row = GmiTableauRow(
        ("basic",),
        F(3, 2),
        (F(1, 4), F(-1, 2)),
        (coordinate("integer", 0, True), coordinate("continuous", 1, False)),
        True,
        (),
    )
    cut = derive_gmi(row, 2)
    assert cut.coefficients == (F(1, 4), F(1, 2))
    assert cut.lower == F(1, 2)
    for zi, basic in itertools.product(range(8), repeat=2):
        zc = 2 * (basic - row.rhs + F(zi, 4))
        if zc >= 0:
            assert cut.coefficients[0] * zi + cut.coefficients[1] * zc >= cut.lower
    negative = GmiTableauRow(
        ("b",),
        F(12, 5),
        (F(-6, 5), F(-6, 5)),
        (coordinate("integer", 0, True), coordinate("continuous", 1, False)),
        True,
        (),
    )
    assert derive_gmi(negative, 2).coefficients == (F(2, 15), F(4, 5))


def mixed_model():
    return model_from_dict(
        RECIPES["model"](
            [RECIPES["variable"]("x", 0, 3, "integer"), RECIPES["variable"]("y", 0, 4)],
            [RECIPES["row"]("d", {"x": 2, "y": 1}, ">=", 3)],
            {"x": 1, "y": 1},
        )
    )


def test_cut_loop_really_removes_mixed_fractional_point_and_strengthens_bound():
    m = mixed_model()
    off = solve(m, SolveOptions(presolve=False, cuts=False, heuristics=False))
    on = solve(m, SolveOptions(presolve=False, cuts=True, heuristics=False))
    assert on.status == off.status == "optimal"
    assert on.objective_value == pytest.approx(2)
    assert off.objective_value == pytest.approx(2)
    assert on.diagnostics["cuts_added"] > 0
    event = on.diagnostics["cut_events"][0]
    assert event["before"] == pytest.approx(1.5)
    assert event["after"] == pytest.approx(2)
    assert event["scope"] == "node_local"
    proof = event["proofs"][0]
    a, b = list(map(F, proof["original_coefficients"])), F(proof["original_lower"])
    assert a[0] * F(3, 2) < b
    # All continuous endpoints for every integer slice preserve the exact cut.
    for x in range(4):
        for y in (max(F(0), 3 - 2 * x), F(4)):
            if 2 * x + y >= 3:
                assert a[0] * x + a[1] * y >= b


def test_local_cuts_follow_ancestors_and_never_cross_siblings():
    variables = [RECIPES["variable"](f"x{i}", 0, 1, "binary") for i in range(6)]
    rows = [
        RECIPES["row"](f"pair{k}", {f"x{2 * k}": 1, f"x{2 * k + 1}": 1}, "<=", 1.5)
        for k in range(3)
    ]
    model = model_from_dict(RECIPES["model"](variables, rows, {f"x{i}": -1 for i in range(6)}))
    result = solve(
        model,
        SolveOptions(
            presolve=False, heuristics=False, cut_round_limit=1, cuts_per_round=1, node_limit=1000
        ),
    )
    assert result.status == "optimal"
    assert result.objective_value == pytest.approx(-3)
    logs = result.diagnostics["node_log"]
    assert any(row["node"] != 0 and row["local_cut_origins"] for row in logs)
    parents = {row["node"]: row["parent"] for row in logs}
    for row in logs:
        ancestors, current = set(), row["node"]
        while current is not None:
            ancestors.add(current)
            current = parents[current]
        assert set(row["local_cut_origins"]) <= ancestors
    assert any(event["node"] != 0 for event in result.diagnostics["cut_events"])


def test_unbounded_relaxation_three_states_and_conservative_frontier():
    bounded_integer = model_from_dict(RECIPES["boundary_input"](6)["model"])
    limited = solve(bounded_integer, SolveOptions(presolve=False, node_limit=1, cuts=False))
    assert limited.status == "limit"
    assert limited.dual_bound == -inf
    assert limited.relative_gap is None
    assert limited.diagnostics["unbounded_state"] == "branchable_unbounded_relaxation"
    full = solve(bounded_integer, SolveOptions(presolve=False, cuts=False))
    assert full.status == "infeasible"
    proven = solve(model_from_dict(RECIPES["boundary_input"](5)["model"]))
    assert proven.status == "unbounded"
    assert proven.witness["kind"] == "integer_point_ray"
    unresolved = solve(
        model_from_dict(RECIPES["boundary_input"](7)["model"]),
        SolveOptions(integer_ray_proof_limit=0),
    )
    assert unresolved.status == "limit"
    assert unresolved.termination_reason == "unresolved_unbounded_relaxation"
    assert unresolved.has_primal_solution
    assert unresolved.dual_bound == -inf
    assert unresolved.relative_gap is unresolved.absolute_gap is None
    assert unresolved.diagnostics["unresolved_nodes"] == 1


def test_node_basis_pseudocost_and_bounded_heuristic_are_used():
    p = RECIPES["model"](
        [RECIPES["variable"]("x", 0, 10, "integer"), RECIPES["variable"]("y")],
        [RECIPES["row"]("cap", {"x": 2, "y": 1}, "<=", 3)],
        {"x": -3, "y": -1},
    )
    r = solve(model_from_dict(p), SolveOptions(presolve=False, scaling=False, cuts=False))
    assert r.status == "optimal"
    assert r.objective_value == pytest.approx(-4)
    assert r.diagnostics["warm_starts"] >= 1
    assert r.diagnostics["dual_pivots"] >= 1
    assert r.diagnostics["pseudocost_updates"] >= 1
    assert 0 < r.diagnostics["heuristic_calls"] <= 2


@pytest.mark.parametrize("index", [8, 9, 10, 11])
def test_fixed_limit_controls_keep_valid_frontier(index):
    payload = RECIPES["boundary_input"](index)
    result = solve(model_from_dict(payload["model"]), SolveOptions(**payload["options"]))
    reason = {8: "node_limit", 9: "time_limit", 10: "lp_iteration_limit", 11: "gap_limit"}[index]
    assert result.status == "limit", result
    assert result.termination_reason == reason
    if index == 11:
        assert result.has_primal_solution
        assert result.dual_bound <= 1 <= result.primal_bound
        assert result.relative_gap == pytest.approx(
            abs(result.primal_bound - result.dual_bound)
            / max(1, abs(result.primal_bound), abs(result.dual_bound))
        )
