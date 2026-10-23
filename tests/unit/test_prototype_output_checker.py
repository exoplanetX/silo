"""Independent checker rejects outputs that a status/objective comparison misses."""

import copy
import runpy
from fractions import Fraction as F
from pathlib import Path

import pytest


@pytest.fixture
def checker(monkeypatch):
    folder = Path(__file__).resolve().parents[2] / "scripts/prototype"
    monkeypatch.syspath_prepend(str(folder))
    return runpy.run_path(str(folder / "validate_results.py"))["validate"]


def instance():
    payload = {
        "sense": "minimize",
        "objective": {"coefficients": {"x": 1}},
        "variables": [{"name": "x", "type": "continuous", "lower": 0, "upper": None}],
        "constraints": [{"name": "r", "coefficients": {"x": 1}, "sense": ">=", "rhs": 1}],
    }
    output = {
        "status": "optimal",
        "termination_reason": "optimal",
        "objective_value": 1,
        "primal_values": {"x": 1},
        "primal_bound": 1,
        "dual_bound": 1,
        "absolute_gap": 0,
        "relative_gap": 0,
        "has_primal_solution": True,
        "row_activities": {"r": 1},
        "dual_values": {"r": 1},
        "reduced_costs": {"x": 0},
        "side_multipliers": {
            "row_lower": {"r": 1},
            "row_upper": {"r": 0},
            "variable_lower": {"x": 0},
            "variable_upper": {"x": 0},
        },
    }
    return payload, output, {"status": "optimal", "objective": F(1)}


def test_valid_raw_kkt(checker):
    assert checker(*instance())["maximum_scaled_stationarity_residual"] == 0


@pytest.mark.parametrize(
    "fault",
    [
        "primal",
        "dual",
        "absent_side",
        "activity",
        "bound",
        "reduced",
        "false_flag",
        "negative_absolute",
        "negative_relative",
        "wrong_relative",
    ],
)
def test_equal_status_and_objective_cannot_hide_invalid_output(checker, fault):
    payload, output, truth = copy.deepcopy(instance())
    if fault == "primal":
        output["primal_values"]["x"] = 0
    elif fault == "dual":
        output["side_multipliers"]["row_lower"]["r"] = 0
    elif fault == "absent_side":
        output["side_multipliers"]["row_upper"]["r"] = 1
    elif fault == "activity":
        output["row_activities"]["r"] = 99
    elif fault == "bound":
        output["dual_bound"] = 2
    elif fault == "reduced":
        output["reduced_costs"]["x"] = 9
    elif fault == "false_flag":
        output["has_primal_solution"] = False
    elif fault == "negative_absolute":
        output["absolute_gap"] = -1
    elif fault == "negative_relative":
        output["relative_gap"] = -1
    else:
        output["relative_gap"] = 0.1
    with pytest.raises(AssertionError):
        checker(payload, output, truth)


def test_limit_without_incumbent_rejects_either_gap(monkeypatch):
    folder = Path(__file__).resolve().parents[2] / "scripts/prototype"
    monkeypatch.syspath_prepend(str(folder))
    check = runpy.run_path(str(folder / "validate_results.py"))["check_gaps"]
    output = {
        "status": "limit",
        "has_primal_solution": False,
        "absolute_gap": None,
        "relative_gap": None,
    }
    check(output)
    for field in ("absolute_gap", "relative_gap"):
        with pytest.raises(AssertionError, match="Gap without incumbent"):
            check({**output, field: 0})
