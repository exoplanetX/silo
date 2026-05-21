import pytest

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.lp.simplex.tableau import TableauSimplexSolver
from silo.presolve import Presolver, PresolveStatus, ReductionType


def test_fixed_variable_is_removed_from_returned_model() -> None:
    model = _fixed_x_model()

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.REDUCED
    assert result.changed is True
    assert result.diagnostics.fixed_variables == ("x",)
    assert result.fixed_values == (("x", 2.0),)
    assert [variable.name for variable in result.model.variables] == ["y"]
    assert result.model.constraints[0].coefficients == {"y": 1.0}
    assert result.model.constraints[0].rhs == pytest.approx(3.0)
    assert result.model.objective.coefficients == {"y": 2.0}
    assert result.model.objective.constant == pytest.approx(6.0)
    assert result.reductions[0].reduction_type == ReductionType.FIXED_VARIABLE
    assert result.reductions[0].target == "x"


def test_fixed_variable_presolve_does_not_mutate_original_model() -> None:
    model = _fixed_x_model()

    Presolver().run(model)

    assert [variable.name for variable in model.variables] == ["x", "y"]
    assert model.constraints[0].coefficients == {"x": 1.0, "y": 1.0}
    assert model.constraints[0].rhs == 5.0
    assert model.objective.coefficients == {"x": 3.0, "y": 2.0}
    assert model.objective.constant == 0.0


def test_multiple_fixed_variables_are_eliminated_in_variable_order() -> None:
    model = Model(name="multiple_fixed")
    model.add_variable(Variable(name="x", bounds=Bounds(lower=2.0, upper=2.0)))
    model.add_variable(Variable(name="y"))
    model.add_variable(Variable(name="z", bounds=Bounds(lower=1.0, upper=1.0)))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 1.0, "y": 1.0, "z": 2.0},
            sense=ConstraintSense.LE,
            rhs=10.0,
        )
    )
    model.set_objective(
        Objective(
            coefficients={"x": 3.0, "y": 2.0, "z": 4.0},
            sense=OptimizationSense.MAXIMIZE,
            constant=1.0,
        )
    )

    result = Presolver().run(model)

    assert [variable.name for variable in result.model.variables] == ["y"]
    assert result.diagnostics.fixed_variables == ("x", "z")
    assert [reduction.target for reduction in result.reductions] == ["x", "z"]
    assert result.model.constraints[0].coefficients == {"y": 1.0}
    assert result.model.constraints[0].rhs == pytest.approx(6.0)
    assert result.model.objective.coefficients == {"y": 2.0}
    assert result.model.objective.constant == pytest.approx(11.0)


def test_fixed_variable_absent_from_row_leaves_row_unchanged() -> None:
    model = _fixed_x_model()
    model.add_constraint(
        Constraint(
            name="y_limit",
            coefficients={"y": 2.0},
            sense=ConstraintSense.LE,
            rhs=8.0,
        )
    )

    result = Presolver().run(model)

    assert result.model.constraints[1].name == "y_limit"
    assert result.model.constraints[1].coefficients == {"y": 2.0}
    assert result.model.constraints[1].rhs == 8.0


def test_row_made_empty_by_fixed_variable_is_removed_by_repeated_pass() -> None:
    model = Model(name="row_made_empty")
    model.add_variable(Variable(name="x", bounds=Bounds(lower=2.0, upper=2.0)))
    model.add_constraint(
        Constraint(
            name="fixed_only",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=2.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))

    result = Presolver().run(model)

    assert result.diagnostics.status == PresolveStatus.REDUCED
    assert result.diagnostics.removed_rows == ("fixed_only",)
    assert result.model.constraints == []
    assert [reduction.reduction_type for reduction in result.reductions] == [
        ReductionType.FIXED_VARIABLE,
        ReductionType.EMPTY_ROW,
    ]
    assert [reduction.target for reduction in result.reductions] == [
        "x",
        "fixed_only",
    ]


def test_recover_solution_restores_fixed_variable_values() -> None:
    model = _fixed_x_model()
    result = Presolver().run(model)

    presolved_solution = TableauSimplexSolver().solve(result.model)
    recovered = result.recover_solution(presolved_solution)

    assert recovered.status == SolverStatus.OPTIMAL
    assert recovered.primal_values["x"] == pytest.approx(2.0)
    assert recovered.primal_values["y"] == pytest.approx(3.0)
    assert recovered.objective_value == pytest.approx(12.0)
    assert recovered.basis_status["x"] == "fixed"
    assert recovered.reduced_costs["x"] == 0.0


def test_recover_solution_does_not_double_count_objective() -> None:
    model = _fixed_x_model()
    result = Presolver().run(model)
    presolved_solution = TableauSimplexSolver().solve(result.model)

    recovered = result.recover_solution(presolved_solution)

    assert recovered.objective_value == pytest.approx(12.0)
    assert recovered.objective_value != pytest.approx(18.0)


def test_recover_solution_preserves_non_optimal_status_and_message() -> None:
    result = Presolver().run(_fixed_x_model())
    solution = Solution(
        status=SolverStatus.INFEASIBLE,
        primal_values={"y": 0.0},
        message="presolved infeasible",
    )

    recovered = result.recover_solution(solution)

    assert recovered.status == SolverStatus.INFEASIBLE
    assert recovered.message == "presolved infeasible"
    assert recovered.objective_value is None
    assert recovered.primal_values == {"y": 0.0, "x": 2.0}


def test_recover_solution_does_not_expose_transformed_only_variables() -> None:
    result = Presolver().run(_fixed_x_model())
    solution = Solution(
        status=SolverStatus.OPTIMAL,
        objective_value=12.0,
        primal_values={"y": 3.0, "slack_capacity": 0.0},
        reduced_costs={"y": 0.0, "slack_capacity": 0.0},
        basis_status={"y": "basic", "slack_capacity": "basic"},
    )

    recovered = result.recover_solution(solution)

    assert recovered.primal_values == {"y": 3.0, "x": 2.0}
    assert recovered.reduced_costs == {"y": 0.0, "x": 0.0}
    assert recovered.basis_status == {"y": "basic", "x": "fixed"}


def test_fixed_variable_and_empty_row_reductions_are_combined() -> None:
    model = _fixed_x_model()
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
    assert result.diagnostics.removed_rows == ("empty",)
    assert result.diagnostics.fixed_variables == ("x",)
    assert [reduction.reduction_type for reduction in result.reductions] == [
        ReductionType.EMPTY_ROW,
        ReductionType.FIXED_VARIABLE,
    ]


def _fixed_x_model() -> Model:
    model = Model(name="fixed_x")
    model.add_variable(Variable(name="x", bounds=Bounds(lower=2.0, upper=2.0)))
    model.add_variable(Variable(name="y"))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 1.0, "y": 1.0},
            sense=ConstraintSense.LE,
            rhs=5.0,
        )
    )
    model.set_objective(
        Objective(
            coefficients={"x": 3.0, "y": 2.0},
            sense=OptimizationSense.MAXIMIZE,
        )
    )
    return model
