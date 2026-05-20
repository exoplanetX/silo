import pytest

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.lp.simplex.basis import BASIC, NONBASIC_LOWER
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver

VALID_BASIS_STATUSES = {BASIC, NONBASIC_LOWER}


def test_tableau_and_revised_match_on_production_lp() -> None:
    tableau, revised = _solve_both(_production_model())

    _assert_same_optimal_diagnostics(tableau, revised)
    assert tableau.objective_value == pytest.approx(21.0)
    assert tableau.primal_values == {"x1": pytest.approx(2.0), "x2": pytest.approx(3.0)}
    assert tableau.basis_status == revised.basis_status == {"x1": BASIC, "x2": BASIC}
    assert tableau.dual_values == revised.dual_values == {}


def test_tableau_and_revised_match_on_objective_constant_lp() -> None:
    tableau, revised = _solve_both(_single_variable_model())

    _assert_same_optimal_diagnostics(tableau, revised)
    assert tableau.objective_value == pytest.approx(9.0)
    assert tableau.primal_values == {"x": pytest.approx(4.0)}
    assert tableau.basis_status == revised.basis_status == {"x": BASIC}
    assert tableau.dual_values == revised.dual_values == {}


def test_tableau_and_revised_match_on_ge_phase_one_lp() -> None:
    tableau, revised = _solve_both(_ge_model())

    _assert_same_optimal_diagnostics(tableau, revised)
    assert tableau.objective_value == pytest.approx(5.0)
    assert tableau.primal_values == {"x": pytest.approx(5.0)}
    assert tableau.slack_values == {
        "demand": pytest.approx(3.0),
        "capacity": pytest.approx(0.0),
    }
    assert tableau.basis_status == revised.basis_status == {"x": BASIC}
    assert tableau.dual_values == revised.dual_values == {}


def test_tableau_and_revised_match_on_degenerate_equality_lp() -> None:
    model = _degenerate_equality_model()
    tableau, revised = _solve_both(model)

    assert tableau.status == revised.status == SolverStatus.OPTIMAL
    assert tableau.objective_value == revised.objective_value == pytest.approx(4.0)
    assert tableau.slack_values["balance"] == pytest.approx(0.0)
    assert revised.slack_values["balance"] == pytest.approx(0.0)
    _assert_primal_feasible(model, tableau)
    _assert_primal_feasible(model, revised)
    _assert_basis_statuses_are_valid(tableau)
    _assert_basis_statuses_are_valid(revised)
    assert tableau.dual_values == revised.dual_values == {}


def test_tableau_and_revised_match_on_infeasible_lp() -> None:
    tableau, revised = _solve_both(_infeasible_model())

    assert tableau.status == revised.status == SolverStatus.INFEASIBLE
    assert tableau.dual_values == revised.dual_values == {}


def test_tableau_and_revised_match_on_unbounded_lp() -> None:
    tableau, revised = _solve_both(_unbounded_model())

    assert tableau.status == revised.status == SolverStatus.UNBOUNDED
    assert tableau.dual_values == revised.dual_values == {}


def test_public_reduced_cost_signs_match_for_nonbasic_lower_variable() -> None:
    tableau, revised = _solve_both(_reduced_cost_sign_model())

    _assert_same_optimal_diagnostics(tableau, revised)
    assert tableau.objective_value == pytest.approx(1.0)
    assert tableau.primal_values == {"x": pytest.approx(1.0), "y": pytest.approx(0.0)}
    assert tableau.reduced_costs == revised.reduced_costs
    assert tableau.reduced_costs == {"x": pytest.approx(0.0), "y": pytest.approx(-1.0)}
    assert tableau.basis_status == revised.basis_status == {
        "x": BASIC,
        "y": NONBASIC_LOWER,
    }
    assert tableau.dual_values == revised.dual_values == {}


def _solve_both(model: Model) -> tuple[Solution, Solution]:
    return TableauSimplexSolver().solve(model), RevisedSimplexSolver().solve(model)


def _assert_same_optimal_diagnostics(tableau: Solution, revised: Solution) -> None:
    assert tableau.status == revised.status == SolverStatus.OPTIMAL
    assert tableau.objective_value == pytest.approx(revised.objective_value)
    _assert_close_dict(tableau.primal_values, revised.primal_values)
    _assert_close_dict(tableau.slack_values, revised.slack_values)
    _assert_close_dict(tableau.reduced_costs, revised.reduced_costs)
    _assert_basis_statuses_are_valid(tableau)
    _assert_basis_statuses_are_valid(revised)


def _assert_close_dict(actual: dict[str, float], expected: dict[str, float]) -> None:
    assert actual.keys() == expected.keys()
    for key, expected_value in expected.items():
        assert actual[key] == pytest.approx(expected_value)


def _assert_basis_statuses_are_valid(solution: Solution) -> None:
    assert solution.basis_status
    assert set(solution.basis_status.values()) <= VALID_BASIS_STATUSES


def _assert_primal_feasible(model: Model, solution: Solution) -> None:
    assert solution.primal_values.keys() == set(model.variable_names())
    for constraint in model.constraints:
        activity = sum(
            coefficient * solution.primal_values[variable_name]
            for variable_name, coefficient in constraint.coefficients.items()
        )
        if constraint.sense == ConstraintSense.LE:
            assert activity <= constraint.rhs + 1e-9
        elif constraint.sense == ConstraintSense.GE:
            assert activity >= constraint.rhs - 1e-9
        else:
            assert activity == pytest.approx(constraint.rhs)


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
        Objective(coefficients={"x1": 3.0, "x2": 5.0}, sense=OptimizationSense.MAXIMIZE)
    )
    return model


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
        Objective(coefficients={"x": 2.0}, sense=OptimizationSense.MAXIMIZE, constant=1.0)
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


def _infeasible_model() -> Model:
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


def _unbounded_model() -> Model:
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
    return model


def _reduced_cost_sign_model() -> Model:
    model = Model(name="reduced_cost_sign")
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
    return model
