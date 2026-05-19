import pytest

from silo.modeling.expressions import LinearExpression


def test_linear_expression_aggregates_terms() -> None:
    expr = LinearExpression.from_terms([("x", 2.0), ("x", 3.0)])

    assert expr.to_dict() == {"x": 5.0}


def test_linear_expression_adds_expressions_and_constants() -> None:
    expr = LinearExpression({"x": 2.0}, constant=1.0) + LinearExpression(
        {"y": 3.0},
        constant=4.0,
    )

    assert expr.to_dict() == {"x": 2.0, "y": 3.0}
    assert expr.constant == 5.0


def test_linear_expression_subtracts_and_cleans_zero_coefficients() -> None:
    expr = LinearExpression({"x": 2.0, "y": 1.0}, constant=5.0) - LinearExpression(
        {"x": 2.0},
        constant=1.0,
    )

    assert expr.to_dict() == {"y": 1.0}
    assert expr.constant == 4.0


def test_linear_expression_scalar_multiplication() -> None:
    expr = 2 * LinearExpression({"x": 2.0, "y": -1.0}, constant=3.0)

    assert expr.to_dict() == {"x": 4.0, "y": -2.0}
    assert expr.constant == 6.0


def test_linear_expression_coefficient_lookup() -> None:
    expr = LinearExpression({"x": 2.0}, constant=1.0)

    assert expr.coefficient("x") == 2.0
    assert expr.coefficient("missing") == 0.0


def test_linear_expression_rejects_empty_variable_name() -> None:
    with pytest.raises(ValueError, match="Variable name in expression"):
        LinearExpression({"": 1.0})
