import pytest

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.lp.simplex.tableau import TableauSimplexSolver


def test_tableau_solution_reports_le_slacks_and_basis_status() -> None:
    model = Model(name="le_slacks")
    model.add_variable(Variable(name="x"))
    model.add_constraint(
        Constraint(
            name="tight_capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=3.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="loose_capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=5.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.primal_values == {"x": pytest.approx(3.0)}
    assert solution.slack_values == {
        "tight_capacity": pytest.approx(0.0),
        "loose_capacity": pytest.approx(2.0),
    }
    assert solution.basis_status == {"x": "basic"}


def test_tableau_solution_reports_ge_and_le_slacks_from_original_rows() -> None:
    model = Model(name="ge_slacks")
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

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.primal_values == {"x": pytest.approx(5.0)}
    assert solution.slack_values == {
        "demand": pytest.approx(3.0),
        "capacity": pytest.approx(0.0),
    }


def test_tableau_solution_reports_equality_residual_slack() -> None:
    model = Model(name="eq_slack")
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

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(4.0)
    assert solution.slack_values["balance"] == pytest.approx(0.0)
    assert set(solution.basis_status) == {"x", "y"}


def test_tableau_solution_reports_reduced_costs_for_original_variables() -> None:
    model = Model(name="reduced_costs")
    model.add_variable(Variable(name="x"))
    model.add_variable(Variable(name="y"))
    model.add_constraint(
        Constraint(
            name="x_capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=1.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="y_capacity",
            coefficients={"y": 1.0},
            sense=ConstraintSense.LE,
            rhs=1.0,
        )
    )
    model.set_objective(
        Objective(coefficients={"x": 1.0, "y": -1.0}, sense=OptimizationSense.MAXIMIZE)
    )

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.primal_values == {"x": pytest.approx(1.0), "y": pytest.approx(0.0)}
    assert solution.objective_value == pytest.approx(1.0)
    assert solution.reduced_costs == {"x": pytest.approx(0.0), "y": pytest.approx(-1.0)}
    assert solution.basis_status == {"x": "basic", "y": "nonbasic"}
    assert solution.dual_values == {}
