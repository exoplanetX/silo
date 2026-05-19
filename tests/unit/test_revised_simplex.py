import pytest

from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.lp.simplex.basis import BASIC, NONBASIC_LOWER
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver


def test_revised_simplex_solves_single_variable_lp() -> None:
    solution = RevisedSimplexSolver().solve(_single_variable_model())

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(9.0)
    assert solution.primal_values == {"x": pytest.approx(4.0)}
    assert solution.slack_values == {"capacity": pytest.approx(0.0)}
    assert solution.reduced_costs == {"x": pytest.approx(0.0)}
    assert solution.basis_status == {"x": BASIC}
    assert solution.dual_values == {}


def test_revised_simplex_solves_production_lp() -> None:
    solution = RevisedSimplexSolver().solve(_production_model())

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(21.0)
    assert solution.primal_values == {"x1": pytest.approx(2.0), "x2": pytest.approx(3.0)}
    assert solution.slack_values == {
        "labor": pytest.approx(0.0),
        "material": pytest.approx(0.0),
    }
    assert solution.basis_status == {"x1": BASIC, "x2": BASIC}


def test_revised_simplex_matches_tableau_on_supported_lps() -> None:
    for model in (_production_model(), _ge_model(), _equality_model()):
        revised = RevisedSimplexSolver().solve(model)
        tableau = TableauSimplexSolver().solve(model)

        assert revised.status == tableau.status
        assert revised.objective_value == pytest.approx(tableau.objective_value)
        assert revised.primal_values == pytest.approx(tableau.primal_values)
        assert revised.slack_values == pytest.approx(tableau.slack_values)


def test_revised_simplex_reports_reduced_costs_for_nonbasic_original_variables() -> None:
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

    revised = RevisedSimplexSolver().solve(model)
    tableau = TableauSimplexSolver().solve(model)

    assert revised.status == SolverStatus.OPTIMAL
    assert revised.primal_values == {"x": pytest.approx(1.0), "y": pytest.approx(0.0)}
    assert revised.objective_value == pytest.approx(1.0)
    assert revised.reduced_costs == {"x": pytest.approx(0.0), "y": pytest.approx(-1.0)}
    assert revised.reduced_costs == pytest.approx(tableau.reduced_costs)
    assert revised.basis_status == {"x": BASIC, "y": NONBASIC_LOWER}


def test_revised_simplex_detects_unbounded_lp() -> None:
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
        Objective(coefficients={"x": 1.0, "y": 1.0}, sense=OptimizationSense.MAXIMIZE)
    )

    solution = RevisedSimplexSolver().solve(model)

    assert solution.status == SolverStatus.UNBOUNDED
    assert "unbounded" in solution.message


def test_revised_simplex_solves_ge_row_with_phase_one() -> None:
    solution = RevisedSimplexSolver().solve(_ge_model())

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(5.0)
    assert solution.primal_values == {"x": pytest.approx(5.0)}
    assert solution.slack_values == {
        "demand": pytest.approx(3.0),
        "capacity": pytest.approx(0.0),
    }
    assert solution.basis_status == {"x": BASIC}


def test_revised_simplex_solves_equality_row_with_phase_one() -> None:
    solution = RevisedSimplexSolver().solve(_equality_model())

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(7.0)
    assert solution.primal_values == {"x": pytest.approx(3.0), "y": pytest.approx(1.0)}
    assert solution.slack_values == {
        "balance": pytest.approx(0.0),
        "x_capacity": pytest.approx(0.0),
        "y_capacity": pytest.approx(2.0),
    }


def test_revised_simplex_solves_degenerate_equality_row_with_phase_one() -> None:
    solution = RevisedSimplexSolver().solve(_degenerate_equality_model())

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(4.0)
    assert solution.slack_values["balance"] == pytest.approx(0.0)
    assert set(solution.primal_values) == {"x", "y"}
    assert set(solution.reduced_costs) == {"x", "y"}
    assert set(solution.basis_status) == {"x", "y"}


def test_revised_simplex_solves_negative_rhs_with_phase_one() -> None:
    solution = RevisedSimplexSolver().solve(_negative_rhs_model())

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(5.0)
    assert solution.primal_values == {"x": pytest.approx(5.0)}
    assert solution.slack_values == {
        "demand": pytest.approx(3.0),
        "capacity": pytest.approx(0.0),
    }


def test_revised_simplex_detects_phase_one_infeasibility() -> None:
    solution = RevisedSimplexSolver().solve(_infeasible_phase_one_model())

    assert solution.status == SolverStatus.INFEASIBLE
    assert "Phase I" in solution.message
    assert "infeasibility" in solution.message


def test_revised_simplex_detects_unbounded_after_phase_one() -> None:
    solution = RevisedSimplexSolver().solve(_unbounded_after_phase_one_model())

    assert solution.status == SolverStatus.UNBOUNDED
    assert "Phase II" in solution.message
    assert "unbounded" in solution.message


def test_revised_simplex_returns_error_for_unsupported_model_classes() -> None:
    unsupported_models = []

    minimization = _single_variable_model()
    minimization.set_objective(
        Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MINIMIZE)
    )
    unsupported_models.append((minimization, "maximization"))

    finite_upper = _single_variable_model()
    finite_upper.variables[0] = Variable(name="x", bounds=Bounds(lower=0.0, upper=4.0))
    unsupported_models.append((finite_upper, "finite variable upper bounds"))

    nonzero_lower = _single_variable_model()
    nonzero_lower.variables[0] = Variable(name="x", bounds=Bounds(lower=1.0))
    unsupported_models.append((nonzero_lower, "lower bound 0"))

    integer_model = _single_variable_model()
    integer_model.variables[0] = Variable(name="x", var_type=VariableType.INTEGER)
    unsupported_models.append((integer_model, "continuous variables"))

    binary_model = _single_variable_model()
    binary_model.variables[0] = Variable(
        name="x",
        bounds=Bounds(lower=0.0, upper=1.0),
        var_type=VariableType.BINARY,
    )
    unsupported_models.append((binary_model, "continuous variables"))

    for model, expected_message in unsupported_models:
        solution = RevisedSimplexSolver().solve(model)

        assert solution.status == SolverStatus.ERROR
        assert expected_message in solution.message


def test_revised_simplex_returns_iteration_limit_when_limit_is_zero() -> None:
    solution = RevisedSimplexSolver(iteration_limit=0).solve(_single_variable_model())

    assert solution.status == SolverStatus.ITERATION_LIMIT
    assert "Phase II" in solution.message
    assert "iteration limit" in solution.message


def test_revised_simplex_returns_phase_one_iteration_limit_when_limit_is_zero() -> None:
    solution = RevisedSimplexSolver(iteration_limit=0).solve(_ge_model())

    assert solution.status == SolverStatus.ITERATION_LIMIT
    assert "Phase I" in solution.message
    assert "iteration limit" in solution.message


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


def _production_model() -> Model:
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
    return model


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


def _equality_model() -> Model:
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
        Objective(coefficients={"x": 2.0, "y": 1.0}, sense=OptimizationSense.MAXIMIZE)
    )
    return model


def _degenerate_equality_model() -> Model:
    model = Model(name="degenerate_equality")
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
    return model


def _negative_rhs_model() -> Model:
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
    return model


def _infeasible_phase_one_model() -> Model:
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
    return model


def _unbounded_after_phase_one_model() -> Model:
    model = Model(name="unbounded_after_phase_one")
    model.add_variable(Variable(name="x"))
    model.add_constraint(
        Constraint(
            name="demand",
            coefficients={"x": 1.0},
            sense=ConstraintSense.GE,
            rhs=2.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))
    return model
