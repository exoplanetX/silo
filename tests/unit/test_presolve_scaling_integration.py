from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.presolve import Presolver, PresolveStatus


def test_no_change_result_includes_scaling_diagnostics() -> None:
    model = _base_model()

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.NO_CHANGE
    assert result.scaling.max_abs_coefficient == 10.0
    assert result.scaling.min_abs_nonzero_coefficient == 2.0
    assert result.scaling.coefficient_ratio == 5.0


def test_reduced_result_includes_scaling_diagnostics() -> None:
    model = _base_model()
    model.constraints.insert(
        0,
        Constraint(
            name="empty",
            coefficients={},
            sense=ConstraintSense.LE,
            rhs=5.0,
        ),
    )

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.REDUCED
    assert result.scaling.max_abs_coefficient == 10.0


def test_infeasible_result_includes_scaling_diagnostics() -> None:
    model = _base_model()
    model.constraints.insert(
        0,
        Constraint(
            name="bad_empty",
            coefficients={},
            sense=ConstraintSense.LE,
            rhs=-1.0,
        ),
    )

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.INFEASIBLE
    assert result.scaling.max_abs_coefficient == 10.0
    assert result.scaling.max_abs_rhs == 8.0


def test_unbounded_empty_column_result_includes_scaling_diagnostics() -> None:
    model = Model(name="unbounded_scaling")
    model.add_variable(Variable(name="x"))
    model.add_variable(Variable(name="y"))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"y": 2.0},
            sense=ConstraintSense.LE,
            rhs=4.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.UNBOUNDED
    assert result.scaling.max_abs_coefficient == 2.0
    assert result.scaling.max_abs_rhs == 4.0


def test_scaling_warnings_do_not_change_status() -> None:
    model = Model(name="large_ratio")
    model.add_variable(Variable(name="x"))
    model.add_variable(Variable(name="y"))
    model.add_constraint(
        Constraint(
            name="range",
            coefficients={"x": 1.0, "y": 1e9},
            sense=ConstraintSense.LE,
            rhs=1.0,
        )
    )
    model.set_objective(
        Objective(
            coefficients={"x": 0.0, "y": 0.0},
            sense=OptimizationSense.MAXIMIZE,
        )
    )

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.NO_CHANGE
    assert result.changed is False
    assert [warning.code for warning in result.scaling.warnings] == [
        "large_coefficient_ratio"
    ]
    assert result.diagnostics.warnings == ()


def _base_model() -> Model:
    model = Model(name="scaling_integration")
    model.add_variable(Variable(name="x"))
    model.add_variable(Variable(name="y"))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 2.0, "y": 10.0},
            sense=ConstraintSense.LE,
            rhs=8.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))
    return model
