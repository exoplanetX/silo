"""Test raw reference evidence without invoking SILO or an external solver."""

import ast
import copy
import json
import runpy
from collections import Counter
from fractions import Fraction as F
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
EVIDENCE = runpy.run_path(str(ROOT / "scripts/prototype/evidence.py"))


@pytest.fixture(scope="module")
def manifest():
    return EVIDENCE["load_manifest"]()


def _payload(manifest, suite, family, variant=0):
    entry = next(
        e
        for e in manifest["cases"]
        if (e["suite"], e["family"], e["variant"]) == (suite, family, variant)
    )
    return EVIDENCE["raw_payload"](entry)


@pytest.mark.parametrize("variant", range(8))
@pytest.mark.parametrize("family", [8, 9])
def test_small_nonoptimal_lp_uses_actual_fraction_evidence(manifest, variant, family):
    payload = _payload(manifest, "lp_small", family, variant)
    truth = EVIDENCE["constructive_lp_truth"](payload)
    assert truth["oracle_kind"] == (
        "raw_fraction_farkas" if family == 8 else "raw_fraction_point_ray"
    )
    assert EVIDENCE["check_certificate"](payload, truth)


def test_raw_contradiction_removal_changes_status(manifest):
    payload = _payload(manifest, "lp_small", 8)
    payload["constraints"] = [r for r in payload["constraints"] if r["name"] != "b"]
    assert EVIDENCE["constructive_lp_truth"](payload)["status"] == "optimal"


def test_raw_free_variable_bound_removes_unbounded_status(manifest):
    payload = _payload(manifest, "lp_small", 9)
    next(v for v in payload["variables"] if v["name"] == "x")["upper"] = 1
    assert EVIDENCE["constructive_lp_truth"](payload)["status"] == "optimal"


def test_tampered_farkas_and_ray_are_rejected(manifest):
    payload = _payload(manifest, "lp_small", 8)
    truth = EVIDENCE["constructive_lp_truth"](payload)
    name = next(iter(truth["farkas"]["multipliers"]))
    truth["farkas"]["multipliers"][name] = F(-1)
    with pytest.raises(AssertionError):
        EVIDENCE["check_certificate"](payload, truth)
    payload = _payload(manifest, "lp_small", 9)
    truth = EVIDENCE["constructive_lp_truth"](payload)
    truth["ray"] = {n: -value for n, value in truth["ray"].items()}
    with pytest.raises(AssertionError):
        EVIDENCE["check_certificate"](payload, truth)


def test_lp_scale_objective_change_uses_raw_costs_and_constant(manifest):
    payload = _payload(manifest, "lp_scale", 7, 0)
    original = EVIDENCE["constructive_lp_truth"](payload)
    payload["objective"]["coefficients"] = {
        name: value * 3 for name, value in payload["objective"]["coefficients"].items()
    }
    changed = EVIDENCE["constructive_lp_truth"](payload)
    constant = F(str(payload["objective"]["constant"]))
    assert changed["objective"] == constant + 3 * (original["objective"] - constant)


@pytest.mark.parametrize("family", [0, 1])
def test_resource_dp_reads_raw_capacity(manifest, family):
    payload = _payload(manifest, "milp_scale", family)
    payload["constraints"][0]["rhs"] = 0
    truth = EVIDENCE["resource_dp_truth"](payload)
    assert truth["objective"] == 3
    assert not any(truth["point"].values())


def test_cover_dp_reads_raw_costs(manifest):
    payload = _payload(manifest, "milp_scale", 2)
    original = EVIDENCE["cover_dp_truth"](payload)
    payload["objective"]["coefficients"] = {
        name: 2 * value for name, value in payload["objective"]["coefficients"].items()
    }
    changed = EVIDENCE["cover_dp_truth"](payload)
    assert changed["objective"] == 3 + 2 * (original["objective"] - 3)


@pytest.mark.parametrize("family", [3, 5])
def test_flow_dp_reads_raw_group_demand(manifest, family):
    payload = _payload(manifest, "milp_scale", family)
    for row in payload["constraints"]:
        if row["sense"] == "=":
            row["rhs"] = 0
    truth = EVIDENCE["flow_dp_truth"](payload)
    assert truth["objective"] == 3
    assert not any(truth["point"].values())


def test_group_resource_dp_reads_raw_choice_costs(manifest):
    payload = _payload(manifest, "milp_scale", 4)
    original = EVIDENCE["resource_dp_truth"](payload, grouped=True)
    groups = sum(row["sense"] == "=" for row in payload["constraints"])
    payload["objective"]["coefficients"] = {
        name: value + 1 for name, value in payload["objective"]["coefficients"].items()
    }
    changed = EVIDENCE["resource_dp_truth"](payload, grouped=True)
    assert changed["objective"] == original["objective"] + groups


def test_raw_dp_domain_is_checked_instead_of_assuming_family(manifest):
    payload = _payload(manifest, "milp_scale", 3)
    link = next(row for row in payload["constraints"] if row["name"] == "link0")
    link["coefficients"]["f0"] = 2
    with pytest.raises(AssertionError):
        EVIDENCE["flow_dp_truth"](payload)


def test_boundary_controls_have_explicit_reasons_and_exact_witnesses(manifest):
    records = {r["id"]: r for r in EVIDENCE["boundary_evidence"](manifest["boundaries"])}
    assert len(records) == 24 and all(r["oracle_kind"] for r in records.values())
    assert records["B05"]["proof"]["point"] == {"x": F(0)}
    assert records["B05"]["proof"]["ray"] == {"x": F(1)}
    assert records["B05"]["proof"]["integer_compatible"]
    assert records["B07"]["assertions"]["dual_bound"] == "negative_infinity"
    assert records["B07"]["assertions"]["relative_gap"] is None
    assert records["B07"]["assertions"]["absolute_gap"] is None
    assert records["B07"]["mathematical_status"] == "unbounded"
    assert [
        records[f"B{i:02}"]["assertions"]["expected_termination_reason"] for i in range(8, 12)
    ] == ["node_limit", "time_limit", "lp_iteration_limit", "gap_limit"]
    assert records["B11"]["reference_objective"] == 1
    assert records["B11"]["lp_relaxation_proof"]["objective"] == F(1, 2)
    assert all(not record["runtime_assertions_executed"] for record in records.values())


def test_diagnostics_have_64_explicit_single_calls_and_shared_lp_baselines(manifest):
    records = EVIDENCE["diagnostic_evidence"](manifest)
    assert len(records) == 64
    assert Counter(r["case_id"] for r in records) == Counter(
        dict.fromkeys(manifest["diagnostics"]["ids"], 8)
    )
    assert sum(r["planned_native_calls"] for r in records) == 64
    assert sum(r["hidden_setup_solves"] for r in records) == 0
    lp0 = [r for r in records if r["case_id"] == "LP000"]
    assert all(r["original_model_sha256"] != r["diagnostic_base_sha256"] for r in lp0)
    assert len({r["diagnostic_base_sha256"] for r in lp0}) == 1
    assert all(r["shared_cold_call"] == "D-LP000-0" for r in lp0)
    for identifier in ("MI000", "MI024", "MI072", "MI088"):
        combinations = {
            (r["options"]["cuts"], r["options"]["heuristics"], r["options"]["node_strategy"])
            for r in records
            if r["case_id"] == identifier
        }
        assert len(combinations) == 8


def test_complete_static_verification_preserves_frozen_bytes():
    before = EVIDENCE["verify_frozen_sources"]()
    evidence = EVIDENCE["build_evidence"]()
    assert len(evidence["cases"]) == 264
    assert len(evidence["boundaries"]) == 24
    assert len(evidence["diagnostics"]) == 64
    assert evidence["native_solver_calls"] == evidence["files_written"] == 0
    assert EVIDENCE["verify_frozen_sources"]() == before
    json.dumps(EVIDENCE["json_ready"](evidence), allow_nan=False)


def test_evidence_imports_no_production_solver():
    path = ROOT / "scripts/prototype/evidence.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    modules = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    modules += [
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    ]
    assert all(not module.startswith("silo") for module in modules)


def test_certificate_check_rejects_a_damaged_exact_dual(manifest):
    payload = _payload(manifest, "lp_scale", 1)
    truth = EVIDENCE["constructive_lp_truth"](payload)
    damaged = copy.deepcopy(truth)
    name = next(iter(damaged["dual"]["multipliers"]))
    damaged["dual"]["multipliers"][name] += 1
    with pytest.raises(AssertionError):
        EVIDENCE["check_certificate"](payload, damaged)


def test_binary_rhs_rejects_a_decimal_reconstruction_point():
    payload = {
        "sense": "minimize",
        "variables": [{"name": "x", "lower": None, "upper": None, "type": "continuous"}],
        "constraints": [{"name": "r", "coefficients": {"x": 1}, "sense": ">=", "rhs": 0.1}],
        "objective": {"coefficients": {"x": 1}, "constant": 0},
    }
    truth = EVIDENCE["constructive_lp_truth"](payload)
    assert truth["point"]["x"] == truth["objective"] == F(0.1)
    assert truth["point"]["x"] > F(1, 10)
    assert EVIDENCE["q"](2**60 + 1) == F(2**60 + 1)
    assert EVIDENCE["check_certificate"](payload, truth)
    damaged = copy.deepcopy(truth)
    damaged["point"]["x"] = damaged["objective"] = F(1, 10)
    with pytest.raises(AssertionError, match="Infeasible point"):
        EVIDENCE["check_certificate"](payload, damaged)


def test_near_cancellation_farkas_keeps_the_actual_binary_residual():
    upper = 0.3 - 0.2
    payload = {
        "sense": "minimize",
        "variables": [{"name": "x", "lower": None, "upper": None, "type": "continuous"}],
        "constraints": [
            {"name": "lo", "coefficients": {"x": 1}, "sense": ">=", "rhs": 0.1},
            {"name": "hi", "coefficients": {"x": 1}, "sense": "<=", "rhs": upper},
        ],
        "objective": {"coefficients": {}, "constant": 0},
    }
    truth = EVIDENCE["constructive_lp_truth"](payload)
    residual = F(upper) - F(0.1)
    assert residual < 0 and residual != F(str(upper)) - F("0.1")
    assert truth["status"] == "infeasible"
    assert truth["farkas"]["contradiction"] == residual
    assert EVIDENCE["check_certificate"](payload, truth)
