import pytest

from silo.core.enums import ConstraintSense
from silo.mip.branching import (
    branch_on_value,
    choose_branching_variable,
    fractional_part,
    is_integral_value,
)
from silo.mip.relaxation import BranchingConstraint


def test_is_integral_value_accepts_exact_integer() -> None:
    assert is_integral_value(1.0)


def test_is_integral_value_accepts_values_within_tolerance() -> None:
    assert is_integral_value(1.0 + 5e-7)


def test_is_integral_value_rejects_fractional_value() -> None:
    assert not is_integral_value(1.5)


def test_fractional_part() -> None:
    assert fractional_part(2.7) == pytest.approx(0.7)


def test_choose_branching_variable_uses_first_fractional_integer_in_model_order() -> None:
    chosen = choose_branching_variable(
        variable_names=("x", "y", "z"),
        integer_variable_names=("y", "z"),
        values={"x": 0.5, "y": 1.25, "z": 2.5},
    )

    assert chosen == "y"


def test_choose_branching_variable_ignores_continuous_variables() -> None:
    chosen = choose_branching_variable(
        variable_names=("x", "y"),
        integer_variable_names=("y",),
        values={"x": 0.5, "y": 1.0},
    )

    assert chosen is None


def test_choose_branching_variable_raises_for_missing_integer_value() -> None:
    with pytest.raises(ValueError, match="Missing relaxation value"):
        choose_branching_variable(
            variable_names=("x", "y"),
            integer_variable_names=("y",),
            values={"x": 0.0},
        )


def test_branch_on_value_uses_floor_and_ceil() -> None:
    left, right = branch_on_value("x", 2.7)

    assert left == BranchingConstraint("x", ConstraintSense.LE, 2.0)
    assert right == BranchingConstraint("x", ConstraintSense.GE, 3.0)


def test_branch_on_binary_like_value() -> None:
    left, right = branch_on_value("x", 0.4)

    assert left == BranchingConstraint("x", ConstraintSense.LE, 0.0)
    assert right == BranchingConstraint("x", ConstraintSense.GE, 1.0)
