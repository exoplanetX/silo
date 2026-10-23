import json
from math import inf, nan

import pytest

from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.io import model_from_dict, model_to_dict, read_json_model


def test_general_json_preserves_bounds_domains_and_objective(tmp_path) -> None:
    payload = {
        "name": "general",
        "sense": "maximize",
        "variables": [
            {"name": "free", "lower": None},
            {"name": "upper", "lower": None, "upper": -2},
            {"name": "fixed", "lower": 3, "upper": 3},
            {"name": "integer", "lower": -4, "type": "integer"},
            {"name": "binary", "upper": 1, "type": "binary"},
        ],
        "objective": {"coefficients": {"free": 2, "integer": -1}, "constant": 7.5},
        "constraints": [
            {"name": "range", "coefficients": {"free": 1}, "lower": -1, "upper": 4},
            {"name": "lower", "lower": 2},
            {"name": "upper", "upper": 5},
            {"name": "free_row", "lower": None, "upper": None},
            {"name": "equality", "lower": 3, "upper": 3},
            {"name": "legacy", "sense": ">=", "rhs": 1},
        ],
    }
    model = model_from_dict(payload)
    assert model.variables[0].bounds.lower == -inf
    assert model.variables[0].bounds.upper == inf
    assert model.variables[1].bounds.upper == -2
    assert model.variables[3].var_type == VariableType.INTEGER
    assert model.variables[4].var_type == VariableType.BINARY
    assert model.objective.sense == OptimizationSense.MAXIMIZE
    assert model.objective.constant == 7.5
    assert [row.row_bounds for row in model.constraints] == [
        (-1, 4), (2, inf), (-inf, 5), (-inf, inf), (3, 3), (1, inf)
    ]
    assert model.constraints[-1].sense == ConstraintSense.GE
    encoded = model_to_dict(model)
    serialized = json.dumps(encoded, allow_nan=False)
    assert model_to_dict(model_from_dict(json.loads(serialized))) == encoded
    assert encoded["constraints"][-1]["sense"] == ">="
    path = tmp_path / "general.json"
    path.write_text(serialized, encoding="utf-8")
    assert model_to_dict(read_json_model(path)) == encoded


def test_legacy_json_defaults_stay_compatible() -> None:
    model = model_from_dict({"variables": [{"name": "x"}], "constraints": [{"name": "r"}]})
    assert model.variables[0].bounds.lower == 0
    assert model.variables[0].bounds.upper == inf
    assert model.objective.sense == OptimizationSense.MINIMIZE
    assert model.constraints[0].row_bounds == (-inf, 0)


@pytest.mark.parametrize(
    "payload",
    [
        {"metadata": {"source": "unknown"}},
        {"variables": [{"name": "x", "unit": "tons"}]},
        {"objective": {"sense": "maximize"}},
        {"constraints": [{"name": "r", "scale": 2}]},
    ],
)
def test_general_json_rejects_unrecognized_metadata(payload) -> None:
    with pytest.raises(ValueError, match="unknown field"):
        model_from_dict(payload)


@pytest.mark.parametrize("value", [inf, -inf, nan, True, "1"])
@pytest.mark.parametrize("location", ["coefficient", "constant", "rhs", "lower"])
def test_general_json_requires_finite_numbers(value, location) -> None:
    payload = {"variables": [{"name": "x"}]}
    if location == "coefficient":
        payload["objective"] = {"coefficients": {"x": value}}
    elif location == "constant":
        payload["objective"] = {"constant": value}
    elif location == "rhs":
        payload["constraints"] = [{"name": "r", "rhs": value}]
    else:
        payload["variables"][0]["lower"] = value
    with pytest.raises(ValueError, match="expected (finite number|number)"):
        model_from_dict(payload)


@pytest.mark.parametrize(
    "row,expected",
    [
        ({"name": "r", "lower": 0, "rhs": 2}, (0, inf)),
        ({"name": "r", "upper": 1, "sense": ">="}, (-inf, 1)),
        ({"name": "r", "lower": -2, "upper": 4, "sense": "=", "rhs": 99}, (-2, 4)),
        ({"name": "r", "lower": None, "upper": None, "sense": "=", "rhs": 99}, (-inf, inf)),
        ({"name": "r", "lower": None, "sense": "<=", "rhs": 2}, (-inf, inf)),
        ({"name": "r", "upper": None, "sense": ">=", "rhs": 2}, (-inf, inf)),
    ],
)
def test_general_json_explicit_interval_sides_take_precedence(row, expected) -> None:
    model = model_from_dict({"constraints": [row]})
    constraint = model.constraints[0]
    assert constraint.row_bounds == expected
    assert constraint.sense.value == row.get("sense", "<=")
    assert constraint.rhs == row.get("rhs", 0)
    encoded = model_to_dict(model)
    assert "sense" not in encoded["constraints"][0]
    assert "rhs" not in encoded["constraints"][0]
    assert model_from_dict(encoded).constraints[0].row_bounds == expected


def test_general_json_rejects_reversed_row_bounds() -> None:
    with pytest.raises(ValueError):
        model_from_dict({"constraints": [{"name": "r", "lower": 2, "upper": 1}]})


@pytest.mark.parametrize("legacy", [{"rhs": inf}, {"rhs": nan}, {"rhs": True}, {"rhs": "1"},
                                   {"sense": "largest"}, {"sense": None}])
def test_general_json_validates_legacy_fields_even_with_explicit_sides(legacy) -> None:
    row = {"name": "r", "lower": -1, "upper": 2, **legacy}
    with pytest.raises(ValueError):
        model_from_dict({"constraints": [row]})


@pytest.mark.parametrize("value", ["NaN", "Infinity", "-Infinity"])
def test_json_reader_rejects_nonstandard_json_numbers(tmp_path, value) -> None:
    path = tmp_path / "bad.json"
    path.write_text('{"objective": {"constant": ' + value + "}}", encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid JSON model file"):
        read_json_model(path)


def test_json_reader_rejects_duplicate_object_fields(tmp_path) -> None:
    path = tmp_path / "duplicate_fields.json"
    path.write_text(
        '{"variables": [{"name": "x"}], "objective": {"coefficients": {"x": 1, "x": 2}}}',
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="Invalid JSON model file"):
        read_json_model(path)
