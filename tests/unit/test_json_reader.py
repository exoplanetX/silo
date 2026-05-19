from math import inf

import pytest

from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.io.json_reader import read_json_model


def test_read_json_model_loads_production_fixture() -> None:
    model = read_json_model("tests/fixtures/lp_small/production.json")

    assert model.name == "production"
    assert model.variable_names() == ["x1", "x2"]
    assert model.variables[0].bounds.upper == inf
    assert model.objective.sense == OptimizationSense.MAXIMIZE
    assert model.constraints[0].sense == ConstraintSense.LE


def test_read_json_model_loads_diet_fixture() -> None:
    model = read_json_model("tests/fixtures/lp_small/diet.json")

    assert model.name == "diet"
    assert model.objective.sense == OptimizationSense.MINIMIZE
    assert model.constraints[0].sense == ConstraintSense.GE


def test_read_json_model_loads_knapsack_fixture() -> None:
    model = read_json_model("tests/fixtures/mip_small/knapsack.json")

    assert model.name == "knapsack"
    assert [variable.var_type for variable in model.variables] == [
        VariableType.BINARY,
        VariableType.BINARY,
        VariableType.BINARY,
    ]


def test_read_json_model_rejects_unknown_constraint_variable(tmp_path) -> None:
    path = tmp_path / "unknown_variable.json"
    path.write_text(
        """
        {
          "name": "bad",
          "variables": [{"name": "x"}],
          "constraints": [{"name": "row", "coefficients": {"y": 1.0}}]
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Unknown variable in constraint row: y"):
        read_json_model(path)


def test_read_json_model_rejects_invalid_binary_bounds(tmp_path) -> None:
    path = tmp_path / "bad_binary.json"
    path.write_text(
        """
        {
          "name": "bad",
          "variables": [
            {"name": "z", "lower": 0.0, "upper": 2.0, "type": "binary"}
          ]
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match=r"Binary variable bounds must stay within \[0, 1\]"):
        read_json_model(path)


def test_read_json_model_rejects_duplicate_variable(tmp_path) -> None:
    path = tmp_path / "duplicate.json"
    path.write_text(
        """
        {
          "name": "bad",
          "variables": [{"name": "x"}, {"name": "x"}]
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Duplicate variable name: x"):
        read_json_model(path)


def test_read_json_model_rejects_invalid_enum(tmp_path) -> None:
    path = tmp_path / "invalid_enum.json"
    path.write_text(
        """
        {
          "name": "bad",
          "sense": "largest",
          "variables": [{"name": "x"}]
        }
        """,
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Invalid sense: largest"):
        read_json_model(path)
