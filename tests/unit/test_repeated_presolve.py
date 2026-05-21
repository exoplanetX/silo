import pytest

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.lp.simplex.tableau import TableauSimplexSolver
from silo.presolve import Presolver, PresolveStatus, ReductionType


def test_fixed_variable_creates_feasible_empty_equality_row() -> None:
    model = _fixed_x_with_x_eq_2_model()

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.REDUCED
    assert result.changed is True
    assert result.diagnostics.fixed_variables == ("x",)
    assert result.diagnostics.removed_rows == ("x_eq_2",)
    assert [reduction.reduction_type for reduction in result.reductions] == [
        ReductionType.FIXED_VARIABLE,
        ReductionType.EMPTY_ROW,
    ]
    assert [reduction.target for reduction in result.reductions] == ["x", "x_eq_2"]
    assert [variable.name for variable in result.model.variables] == ["y"]
    assert [constraint.name for constraint in result.model.constraints] == ["y_limit"]


def test_fixed_variable_creates_infeasible_empty_row() -> None:
    model = Model(name="fixed_x_infeasible_empty_row")
    model.add_variable(Variable(name="x", bounds=Bounds(lower=2.0, upper=2.0)))
    model.add_variable(Variable(name="y"))
    model.add_constraint(
        Constraint(
            name="x_limit",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=1.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="y_limit",
            coefficients={"y": 1.0},
            sense=ConstraintSense.LE,
            rhs=3.0,
        )
    )
    model.set_objective(Objective(coefficients={"y": 1.0}, sense=OptimizationSense.MAXIMIZE))

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.INFEASIBLE
    assert result.changed is True
    assert result.fixed_values == (("x", 2.0),)
    assert result.diagnostics.fixed_variables == ("x",)
    assert [reduction.reduction_type for reduction in result.reductions] == [
        ReductionType.FIXED_VARIABLE,
    ]
    assert result.reductions[0].target == "x"
    assert "x_limit" in result.message
    assert result.model.constraints[0].name == "x_limit"
    assert result.model.constraints[0].coefficients == {}
    assert result.model.constraints[0].rhs == pytest.approx(-1.0)


def test_multiple_fixed_variables_create_feasible_empty_row() -> None:
    model = Model(name="multiple_fixed_empty_row")
    model.add_variable(Variable(name="x", bounds=Bounds(lower=2.0, upper=2.0)))
    model.add_variable(Variable(name="y"))
    model.add_variable(Variable(name="z", bounds=Bounds(lower=1.0, upper=1.0)))
    model.add_constraint(
        Constraint(
            name="sum_fixed",
            coefficients={"x": 1.0, "z": 1.0},
            sense=ConstraintSense.EQ,
            rhs=3.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="y_limit",
            coefficients={"y": 1.0},
            sense=ConstraintSense.LE,
            rhs=3.0,
        )
    )
    model.set_objective(Objective(coefficients={"y": 1.0}, sense=OptimizationSense.MAXIMIZE))

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.REDUCED
    assert result.diagnostics.fixed_variables == ("x", "z")
    assert result.diagnostics.removed_rows == ("sum_fixed",)
    assert [reduction.reduction_type for reduction in result.reductions] == [
        ReductionType.FIXED_VARIABLE,
        ReductionType.FIXED_VARIABLE,
        ReductionType.EMPTY_ROW,
    ]
    assert [reduction.target for reduction in result.reductions] == [
        "x",
        "z",
        "sum_fixed",
    ]


def test_diagnostic_only_empty_column_warning_does_not_trigger_another_pass() -> None:
    model = Model(name="empty_column_warning_only")
    model.add_variable(Variable(name="y"))
    model.add_variable(Variable(name="x"))
    model.add_constraint(
        Constraint(
            name="y_limit",
            coefficients={"y": 1.0},
            sense=ConstraintSense.LE,
            rhs=3.0,
        )
    )
    model.set_objective(
        Objective(
            coefficients={"y": 1.0, "x": 0.0},
            sense=OptimizationSense.MAXIMIZE,
        )
    )

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.NO_CHANGE
    assert result.changed is False
    assert result.reductions == ()
    assert result.diagnostics.warnings[0].code == "empty_column"
    assert result.diagnostics.warnings[0].source == "x"


def test_recovery_restores_fixed_variables_after_repeated_passes() -> None:
    result = Presolver().run(_fixed_x_with_x_eq_2_model())

    presolved_solution = TableauSimplexSolver().solve(result.model)
    recovered = result.recover_solution(presolved_solution)

    assert recovered.status == SolverStatus.OPTIMAL
    assert recovered.primal_values["x"] == pytest.approx(2.0)
    assert recovered.primal_values["y"] == pytest.approx(3.0)
    assert recovered.objective_value == pytest.approx(3.0)
    assert recovered.basis_status["x"] == "fixed"
    assert recovered.reduced_costs["x"] == 0.0


def _fixed_x_with_x_eq_2_model() -> Model:
    model = Model(name="fixed_x_feasible_empty_row")
    model.add_variable(Variable(name="x", bounds=Bounds(lower=2.0, upper=2.0)))
    model.add_variable(Variable(name="y"))
    model.add_constraint(
        Constraint(
            name="x_eq_2",
            coefficients={"x": 1.0},
            sense=ConstraintSense.EQ,
            rhs=2.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="y_limit",
            coefficients={"y": 1.0},
            sense=ConstraintSense.LE,
            rhs=3.0,
        )
    )
    model.set_objective(Objective(coefficients={"y": 1.0}, sense=OptimizationSense.MAXIMIZE))
    return model
