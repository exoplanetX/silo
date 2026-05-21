from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.presolve import Presolver, PresolveStatus


def test_empty_column_with_positive_maximization_objective_is_unbounded() -> None:
    model = _two_variable_model({"x": 1.0}, variable_order=("x", "y"))

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.UNBOUNDED
    assert result.changed is False
    assert result.model is model
    assert "x" in result.message
    assert result.diagnostics.warnings[0].code == "empty_column_unbounded"
    assert result.diagnostics.warnings[0].source == "x"


def test_empty_column_with_zero_objective_gets_warning_only() -> None:
    model = _two_variable_model({"y": 1.0, "x": 0.0}, variable_order=("y", "x"))

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.NO_CHANGE
    assert result.changed is False
    assert result.diagnostics.warnings[0].code == "empty_column"
    assert result.diagnostics.warnings[0].source == "x"


def test_empty_column_with_negative_objective_gets_warning_only() -> None:
    model = _two_variable_model({"y": 1.0, "x": -1.0}, variable_order=("y", "x"))

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.NO_CHANGE
    assert result.changed is False
    assert result.diagnostics.warnings[0].code == "empty_column"
    assert result.diagnostics.warnings[0].source == "x"


def test_nonempty_column_does_not_warn() -> None:
    model = Model(name="nonempty_column")
    model.add_variable(Variable(name="x"))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=1.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.NO_CHANGE
    assert not [
        warning
        for warning in result.diagnostics.warnings
        if warning.code.startswith("empty_column")
    ]


def test_empty_column_warnings_follow_variable_order() -> None:
    model = Model(name="empty_column_order")
    model.add_variable(Variable(name="z"))
    model.add_variable(Variable(name="y"))
    model.add_variable(Variable(name="x"))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=1.0,
        )
    )
    model.set_objective(
        Objective(
            coefficients={"z": 0.0, "y": -1.0, "x": 1.0},
            sense=OptimizationSense.MAXIMIZE,
        )
    )

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.NO_CHANGE
    assert [warning.source for warning in result.diagnostics.warnings] == ["z", "y"]


def _two_variable_model(
    objective_coefficients: dict[str, float],
    variable_order: tuple[str, str],
) -> Model:
    model = Model(name="empty_column")
    for variable_name in variable_order:
        model.add_variable(Variable(name=variable_name))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"y": 1.0},
            sense=ConstraintSense.LE,
            rhs=1.0,
        )
    )
    model.set_objective(
        Objective(
            coefficients=objective_coefficients,
            sense=OptimizationSense.MAXIMIZE,
        )
    )
    return model
