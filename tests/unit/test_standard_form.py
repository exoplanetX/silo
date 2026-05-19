import pytest

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.lp.simplex.standard_form import (
    COLUMN_ARTIFICIAL,
    COLUMN_ORIGINAL,
    COLUMN_SLACK,
    COLUMN_SURPLUS,
    build_standard_form,
)


def test_build_standard_form_for_simple_le_lp() -> None:
    model = Model(name="single")
    model.add_variable(Variable(name="x"))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=4.0,
        )
    )
    model.set_objective(
        Objective(
            coefficients={"x": 2.0},
            sense=OptimizationSense.MAXIMIZE,
            constant=1.0,
        )
    )

    problem = build_standard_form(model)

    assert [column.name for column in problem.columns] == ["x", "slack_capacity"]
    assert [column.role for column in problem.columns] == [COLUMN_ORIGINAL, COLUMN_SLACK]
    assert problem.row_names == ("capacity",)
    assert problem.matrix == ((1.0, 1.0),)
    assert problem.rhs == (4.0,)
    assert problem.initial_basis.basic_columns == (1,)
    assert problem.initial_basis.nonbasic_columns == (0,)
    assert problem.artificial_columns == ()
    assert problem.objective_coefficients == (2.0, 0.0)
    assert problem.objective_constant == 1.0
    assert problem.original_variable_count == 1


def test_build_standard_form_for_ge_row_adds_surplus_and_artificial() -> None:
    problem = build_standard_form(_ge_model())

    assert [column.name for column in problem.columns] == [
        "x",
        "surplus_demand",
        "artificial_demand",
        "slack_capacity",
    ]
    assert [column.role for column in problem.columns] == [
        COLUMN_ORIGINAL,
        COLUMN_SURPLUS,
        COLUMN_ARTIFICIAL,
        COLUMN_SLACK,
    ]
    assert problem.matrix == (
        (1.0, -1.0, 1.0, 0.0),
        (1.0, 0.0, 0.0, 1.0),
    )
    assert problem.rhs == (2.0, 5.0)
    assert problem.initial_basis.basic_columns == (2, 3)
    assert problem.initial_basis.nonbasic_columns == (0, 1)
    assert problem.artificial_columns == (2,)
    assert problem.columns[2].source_constraint == "demand"


def test_build_standard_form_for_equality_row_adds_artificial() -> None:
    model = Model(name="equality")
    model.add_variable(Variable(name="x"))
    model.add_variable(Variable(name="y"))
    model.add_constraint(
        Constraint(
            name="balance",
            coefficients={"x": 1.0, "y": 1.0},
            sense=ConstraintSense.EQ,
            rhs=4.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="x_capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=3.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="y_capacity",
            coefficients={"y": 1.0},
            sense=ConstraintSense.LE,
            rhs=3.0,
        )
    )
    model.set_objective(
        Objective(coefficients={"x": 1.0, "y": 1.0}, sense=OptimizationSense.MAXIMIZE)
    )

    problem = build_standard_form(model)

    assert [column.name for column in problem.columns] == [
        "x",
        "y",
        "artificial_balance",
        "slack_x_capacity",
        "slack_y_capacity",
    ]
    assert problem.matrix == (
        (1.0, 1.0, 1.0, 0.0, 0.0),
        (1.0, 0.0, 0.0, 1.0, 0.0),
        (0.0, 1.0, 0.0, 0.0, 1.0),
    )
    assert problem.initial_basis.basic_columns == (2, 3, 4)
    assert problem.artificial_columns == (2,)
    assert problem.objective_coefficients == (1.0, 1.0, 0.0, 0.0, 0.0)


def test_build_standard_form_normalizes_negative_rhs() -> None:
    model = Model(name="negative_rhs")
    model.add_variable(Variable(name="x"))
    model.add_constraint(
        Constraint(
            name="demand",
            coefficients={"x": -1.0},
            sense=ConstraintSense.LE,
            rhs=-2.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=5.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))

    problem = build_standard_form(model)

    assert [column.name for column in problem.columns] == [
        "x",
        "surplus_demand",
        "artificial_demand",
        "slack_capacity",
    ]
    assert problem.matrix[0] == (1.0, -1.0, 1.0, 0.0)
    assert problem.rhs[0] == 2.0
    assert problem.initial_basis.basic_columns == (2, 3)
    assert problem.artificial_columns == (2,)


def test_build_standard_form_rejects_finite_upper_bound() -> None:
    model = _ge_model()
    model.variables[0] = Variable(name="x", bounds=Bounds(lower=0.0, upper=5.0))

    with pytest.raises(ValueError, match="finite variable upper bounds"):
        build_standard_form(model)


def test_build_standard_form_rejects_nonzero_lower_bound() -> None:
    model = _ge_model()
    model.variables[0] = Variable(name="x", bounds=Bounds(lower=1.0))

    with pytest.raises(ValueError, match="lower bound 0"):
        build_standard_form(model)


def test_build_standard_form_rejects_integer_variables() -> None:
    model = _ge_model()
    model.variables[0] = Variable(name="x", var_type=VariableType.INTEGER)

    with pytest.raises(ValueError, match="continuous variables"):
        build_standard_form(model)


def test_build_standard_form_rejects_binary_variables() -> None:
    model = _ge_model()
    model.variables[0] = Variable(
        name="x",
        bounds=Bounds(lower=0.0, upper=1.0),
        var_type=VariableType.BINARY,
    )

    with pytest.raises(ValueError, match="continuous variables"):
        build_standard_form(model)


def test_build_standard_form_rejects_minimization() -> None:
    model = _ge_model()
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MINIMIZE))

    with pytest.raises(ValueError, match="maximization"):
        build_standard_form(model)


def _ge_model() -> Model:
    model = Model(name="ge_row")
    model.add_variable(Variable(name="x"))
    model.add_constraint(
        Constraint(
            name="demand",
            coefficients={"x": 1.0},
            sense=ConstraintSense.GE,
            rhs=2.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=5.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))
    return model
