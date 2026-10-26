"""Tool tests use hand microcases and never load formal acceptance inputs."""

from copy import deepcopy
from fractions import Fraction

import pytest

from scripts.reliability.check_result import check
from scripts.reliability.exact import equivalent
from scripts.reliability.handwritten import JSON_CASES, MPS_CASES, parsed_json
from scripts.reliability.oracle import solve
from silo.io import model_from_dict, model_to_dict, parse_mps


@pytest.mark.parametrize("field", ["coefficient", "bound"])
def test_sub_tolerance_format_perturbation_is_rejected(field):
    original = {"variables": [{"name": "x", "upper": 2}],
                "objective": {"coefficients": {"x": 1}}}
    changed = deepcopy(original)
    if field == "coefficient":
        changed["objective"]["coefficients"]["x"] += 2**-39
    else:
        changed["variables"][0]["upper"] += 2**-39
    with pytest.raises(AssertionError, match="exact"):
        equivalent(original, changed)


@pytest.mark.parametrize("text,payload", MPS_CASES)
def test_hand_mps_independent_expected(text, payload):
    equivalent(payload, model_to_dict(parse_mps(text)))


@pytest.mark.parametrize("text,payload", JSON_CASES)
def test_hand_json_independent_expected(text, payload):
    equivalent(payload, model_to_dict(model_from_dict(parsed_json(text))))


def test_oracle_microcases_do_not_import_solver():
    p = {"variables": [{"name": "z", "lower": 0, "upper": 3}],
         "objective": {"coefficients": {"z": -1}}}
    assert solve(p)["objective"] == "-3"
    p["constraints"] = [{"name": "conflict", "coefficients": {"z": 1}, "lower": 4}]
    assert solve(p)["status"] == "infeasible"
    p["constraints"] = []
    p["variables"][0]["upper"] = None
    witness = {"anchor": {"z": 0}, "ray": {"z": 1}}
    assert solve(p, witness)["status"] == "unbounded"


def test_independent_kkt_checker_rejects_false_multipliers():
    payload = {"sense": "maximize", "variables": [{"name": "z", "upper": 1}],
               "objective": {"coefficients": {"z": 1}}, "constraints": []}
    result = {"status": "optimal", "primal_values": {"z": 1.0}, "objective_value": 1.0,
              "primal_bound": 1.0, "dual_bound": 1.0, "absolute_gap": 0, "relative_gap": 0,
              "side_multipliers": {"row_lower": {}, "row_upper": {},
                                   "variable_lower": {"z": 0.0}, "variable_upper": {"z": 1.0}}}
    assert check(payload, result, {"status": "optimal", "objective": "1"})
    result["side_multipliers"]["variable_upper"]["z"] = 0
    with pytest.raises(AssertionError):
        check(payload, result, {"status": "optimal", "objective": "1"})


def test_r4_transport_only_accepts_strict_line_end_changes():
    from scripts.reliability.r4_closure import strict_lf

    assert strict_lf(b"one\r\ntwo\n") == b"one\ntwo\n"
    with pytest.raises(ValueError, match="bare CR"):
        strict_lf(b"one\rtwo")


def test_r4_l0016_tail_difference_uses_actual_binary_values():
    delta = Fraction(0.2500000000000001) - Fraction(0.25000000000000006)
    assert delta == Fraction(1, 2**54)
