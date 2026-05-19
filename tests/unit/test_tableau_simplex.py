import pytest

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.lp.simplex.pricing import choose_entering_column
from silo.lp.simplex.ratio_test import choose_leaving_row
from silo.lp.simplex.tableau import SimplexTableau, TableauSimplexSolver


def test_tableau_from_model_adds_slack_basis() -> None:
    model = _single_variable_model()

    tableau = SimplexTableau.from_model(model)

    assert tableau.variable_names == ("x", "slack_capacity")
    assert tableau.basis == [1]
    assert tableau.rows == [[1.0, 1.0, 4.0]]
    assert tableau.objective_row == [-2.0, 0.0, 1.0]


def test_tableau_from_model_canonicalizes_phase_one_objective() -> None:
    model = Model(name="phase_one")
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

    tableau = SimplexTableau.from_model(model)

    assert tableau.variable_names == (
        "x",
        "surplus_demand",
        "artificial_demand",
        "slack_capacity",
    )
    assert tableau.basis == [2, 3]
    assert tableau.objective_row == [-1.0, 1.0, 0.0, 0.0, -2.0]


def test_tableau_simplex_solves_single_variable_lp() -> None:
    solution = TableauSimplexSolver().solve(_single_variable_model())

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(9.0)
    assert solution.primal_values == {"x": pytest.approx(4.0)}


def test_tableau_simplex_includes_nonzero_objective_constant() -> None:
    model = Model(name="constant")
    model.add_variable(Variable(name="x"))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=2.0,
        )
    )
    model.set_objective(
        Objective(
            coefficients={"x": 3.0},
            sense=OptimizationSense.MAXIMIZE,
            constant=7.0,
        )
    )

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(13.0)


def test_tableau_simplex_solves_production_lp() -> None:
    model = Model(name="production")
    model.add_variable(Variable(name="x1"))
    model.add_variable(Variable(name="x2"))
    model.add_constraint(
        Constraint(
            name="labor",
            coefficients={"x1": 1.0, "x2": 2.0},
            sense=ConstraintSense.LE,
            rhs=8.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="material",
            coefficients={"x1": 3.0, "x2": 2.0},
            sense=ConstraintSense.LE,
            rhs=12.0,
        )
    )
    model.set_objective(
        Objective(
            coefficients={"x1": 3.0, "x2": 5.0},
            sense=OptimizationSense.MAXIMIZE,
        )
    )

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(21.0)
    assert solution.primal_values == {"x1": pytest.approx(2.0), "x2": pytest.approx(3.0)}


def test_tableau_simplex_detects_unbounded_lp() -> None:
    model = Model(name="unbounded")
    model.add_variable(Variable(name="x"))
    model.add_variable(Variable(name="y"))
    model.add_constraint(
        Constraint(
            name="limit_y",
            coefficients={"y": 1.0},
            sense=ConstraintSense.LE,
            rhs=1.0,
        )
    )
    model.set_objective(
        Objective(
            coefficients={"x": 1.0, "y": 1.0},
            sense=OptimizationSense.MAXIMIZE,
        )
    )

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.UNBOUNDED
    assert "no positive pivot row" in solution.message


def test_choose_leaving_row_breaks_ties_by_row_order() -> None:
    rows = [
        [1.0, 0.0, 2.0],
        [2.0, 1.0, 4.0],
    ]

    assert choose_leaving_row(rows, entering_column=0) == 0


def test_choose_entering_column_uses_tolerance() -> None:
    assert choose_entering_column([-1e-10, -1.0, 0.0]) == 1


def test_tableau_simplex_rejects_minimization() -> None:
    model = _single_variable_model()
    model.set_objective(Objective(coefficients={"x": 2.0}, sense=OptimizationSense.MINIMIZE))

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.ERROR
    assert "maximization" in solution.message


def test_tableau_simplex_solves_ge_row_with_phase_one() -> None:
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

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(5.0)
    assert solution.primal_values == {"x": pytest.approx(5.0)}


def test_tableau_simplex_preserves_objective_constant_after_phase_one() -> None:
    model = Model(name="phase_one_constant")
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
    model.set_objective(
        Objective(
            coefficients={"x": 1.0},
            sense=OptimizationSense.MAXIMIZE,
            constant=10.0,
        )
    )

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(15.0)


def test_tableau_simplex_solves_equality_row_with_phase_one() -> None:
    model = Model(name="eq_row")
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
    assert solution.primal_values["x"] + solution.primal_values["y"] == pytest.approx(4.0)
    assert solution.primal_values["x"] <= 3.0
    assert solution.primal_values["y"] <= 3.0


def test_tableau_simplex_normalizes_negative_rhs_rows() -> None:
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

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(5.0)
    assert solution.primal_values == {"x": pytest.approx(5.0)}


def test_tableau_simplex_detects_phase_one_infeasibility() -> None:
    model = Model(name="infeasible")
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
            rhs=1.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.INFEASIBLE
    assert "Phase I" in solution.message or "infeasibility" in solution.message


def test_tableau_simplex_solves_equality_with_zero_rhs() -> None:
    model = Model(name="zero_rhs_eq")
    model.add_variable(Variable(name="x"))
    model.add_variable(Variable(name="y"))
    model.add_constraint(
        Constraint(
            name="fix_x",
            coefficients={"x": 1.0},
            sense=ConstraintSense.EQ,
            rhs=0.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="capacity_y",
            coefficients={"y": 1.0},
            sense=ConstraintSense.LE,
            rhs=3.0,
        )
    )
    model.set_objective(Objective(coefficients={"y": 1.0}, sense=OptimizationSense.MAXIMIZE))

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(3.0)
    assert solution.primal_values == {"x": pytest.approx(0.0), "y": pytest.approx(3.0)}


def test_tableau_simplex_rejects_finite_upper_bounds() -> None:
    model = Model(name="unsupported")
    model.add_variable(Variable(name="x", bounds=Bounds(lower=0.0, upper=5.0)))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=4.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.ERROR
    assert "finite variable upper bounds" in solution.message


def test_tableau_simplex_rejects_nonzero_lower_bounds() -> None:
    model = Model(name="unsupported")
    model.add_variable(Variable(name="x", bounds=Bounds(lower=1.0)))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=4.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.ERROR
    assert "lower bound 0" in solution.message


def test_tableau_simplex_rejects_integer_variables() -> None:
    model = _single_variable_model()
    model.variables[0] = Variable(name="x", var_type=VariableType.INTEGER)

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.ERROR
    assert "continuous variables" in solution.message


def test_tableau_simplex_rejects_binary_variables() -> None:
    model = _single_variable_model()
    model.variables[0] = Variable(
        name="x",
        bounds=Bounds(lower=0.0, upper=1.0),
        var_type=VariableType.BINARY,
    )

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == SolverStatus.ERROR
    assert "continuous variables" in solution.message


def test_tableau_simplex_returns_iteration_limit_when_limit_is_zero() -> None:
    solution = TableauSimplexSolver(iteration_limit=0).solve(_single_variable_model())

    assert solution.status == SolverStatus.ITERATION_LIMIT


def _single_variable_model() -> Model:
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
    return model
