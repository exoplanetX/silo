from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.variable import Variable
from silo.presolve import Presolver, PresolveStatus, ReductionType
from silo.utils.numerics import DEFAULT_TOLERANCE


def test_feasible_empty_le_row_is_removed_without_mutating_original() -> None:
    model = _model_with_empty_row("empty_le", ConstraintSense.LE, 5.0)

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.REDUCED
    assert result.changed is True
    assert result.diagnostics.removed_rows == ("empty_le",)
    assert [constraint.name for constraint in result.model.constraints] == ["capacity"]
    assert [constraint.name for constraint in model.constraints] == ["empty_le", "capacity"]
    assert result.reductions[0].reduction_type == ReductionType.EMPTY_ROW
    assert result.reductions[0].target == "empty_le"


def test_feasible_empty_ge_row_is_removed() -> None:
    model = _model_with_empty_row("empty_ge", ConstraintSense.GE, -1.0)

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.REDUCED
    assert result.diagnostics.removed_rows == ("empty_ge",)
    assert result.reductions[0].data == (("rhs", -1.0), ("sense", ">="))


def test_feasible_empty_eq_row_is_removed_with_clean_rhs_metadata() -> None:
    model = _model_with_empty_row("empty_eq", ConstraintSense.EQ, DEFAULT_TOLERANCE / 10)

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.REDUCED
    assert result.diagnostics.removed_rows == ("empty_eq",)
    assert result.reductions[0].data == (("rhs", 0.0), ("sense", "="))


def test_infeasible_empty_le_row_returns_infeasible() -> None:
    model = _single_empty_row_model("bad_le", ConstraintSense.LE, -1.0)

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.INFEASIBLE
    assert result.changed is False
    assert result.model is model
    assert "bad_le" in result.message
    assert result.diagnostics.warnings[0].code == "empty_row_infeasible"
    assert result.diagnostics.warnings[0].source == "bad_le"


def test_infeasible_empty_ge_row_returns_infeasible() -> None:
    model = _single_empty_row_model("bad_ge", ConstraintSense.GE, 1.0)

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.INFEASIBLE
    assert result.changed is False
    assert result.diagnostics.warnings[0].source == "bad_ge"


def test_infeasible_empty_eq_row_returns_infeasible() -> None:
    model = _single_empty_row_model("bad_eq", ConstraintSense.EQ, 1.0)

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.INFEASIBLE
    assert result.changed is False
    assert result.diagnostics.warnings[0].source == "bad_eq"


def test_near_zero_coefficient_is_treated_as_empty_row() -> None:
    model = Model(name="near_zero_empty_row")
    model.add_variable(Variable(name="x"))
    model.add_constraint(
        Constraint(
            name="near_zero",
            coefficients={"x": DEFAULT_TOLERANCE / 10},
            sense=ConstraintSense.LE,
            rhs=5.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=3.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.REDUCED
    assert result.diagnostics.removed_rows == ("near_zero",)
    assert [constraint.name for constraint in result.model.constraints] == ["capacity"]


def _model_with_empty_row(name: str, sense: ConstraintSense, rhs: float) -> Model:
    model = Model(name="empty_row")
    model.add_variable(Variable(name="x"))
    model.add_constraint(Constraint(name=name, coefficients={}, sense=sense, rhs=rhs))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=3.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))
    return model


def _single_empty_row_model(name: str, sense: ConstraintSense, rhs: float) -> Model:
    model = Model(name="infeasible_empty_row")
    model.add_constraint(Constraint(name=name, coefficients={}, sense=sense, rhs=rhs))
    return model
