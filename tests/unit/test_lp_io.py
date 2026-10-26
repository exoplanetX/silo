"""Development hand examples only; the frozen acceptance corpus is not collected."""

import math

import pytest

from scripts.reliability.exact import equivalent
from scripts.reliability.handwritten import INVALID_LP, LP_CASES
from silo.io import model_from_dict, model_to_dict, model_to_lp, parse_lp, read_lp_model
from silo.io.lp import write_lp_model


@pytest.mark.parametrize("text,payload", LP_CASES)
def test_handwritten_lp_semantics(text, payload):
    model = parse_lp(text)
    equivalent(payload, model_to_dict(model))
    rewritten = model_to_lp(model)
    equivalent(payload, model_to_dict(parse_lp(rewritten)), lp=True)
    assert model_to_lp(parse_lp(rewritten)) == rewritten


@pytest.mark.parametrize("text", INVALID_LP)
def test_declared_rejections(text):
    with pytest.raises(ValueError):
        parse_lp(text)


def test_interval_name_collisions_and_zero_columns(tmp_path):
    payload = {"variables": [{"name": "x"}, {"name": "band__lower", "upper": 2}],
               "objective": {}, "constraints": [
                   {"name": "band", "coefficients": {"x": 1}, "lower": 1, "upper": 3},
                   {"name": "band__lower_1", "coefficients": {"x": 1}, "upper": 4}]}
    model = model_from_dict(payload)
    text = model_to_lp(model)
    assert "band__lower_2:" in text
    equivalent(payload, model_to_dict(parse_lp(text)), lp=True)
    path = tmp_path / "model.lp"
    write_lp_model(model, path)
    equivalent(payload, model_to_dict(read_lp_model(path)), lp=True)


def test_free_row_zero_variables_and_invalid_names_rejected_before_write(tmp_path):
    for payload in ({}, {"variables": [{"name": "x"}], "constraints": [
            {"name": "r", "lower": None, "upper": None}]},
            {"variables": [{"name": "bad name"}]}, {"variables": [{"name": "sos"}]}):
        path = tmp_path / "untouched.lp"
        path.write_text("original", encoding="utf-8")
        with pytest.raises(ValueError):
            write_lp_model(model_from_dict(payload), path)
        assert path.read_text(encoding="utf-8") == "original"


@pytest.mark.parametrize("value", [math.nextafter(0, 1), 0.1, 1e308, -0.0, 2**53])
def test_numeric_export_preserves_actual_float(value):
    payload = {"variables": [{"name": "x", "lower": value, "upper": value}],
               "objective": {"coefficients": {"x": value}, "constant": value}}
    equivalent(payload, model_to_dict(parse_lp(model_to_lp(model_from_dict(payload)))))


def test_decimal_terms_combine_before_conversion_and_keep_cancelled_variable():
    result = model_to_dict(parse_lp("Min\n .1 x + .2 x - .3 x\nST\nEnd"))
    assert result["variables"][0]["name"] == "x"
    assert result["objective"]["coefficients"]["x"] == 0


def test_interval_named_obj_does_not_destabilize_objective_label():
    payload = {"variables": [{"name": "x"}], "constraints": [
        {"name": "obj", "coefficients": {"x": 1}, "lower": 0, "upper": 2}]}
    text = model_to_lp(model_from_dict(payload))
    assert " obj: " in text
    assert model_to_lp(parse_lp(text)) == text


@pytest.mark.parametrize("token", ["1e1000000000", "1e-1000000000", "1e9999999999999999999"])
def test_exponent_limits_checked_before_large_rational_allocation(token):
    with pytest.raises(ValueError):
        parse_lp(f"Min\n {token} x\nST\nEnd")
