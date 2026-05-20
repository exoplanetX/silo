import pytest

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.lp.simplex.basis import Basis
from silo.lp.simplex.revised import RevisedSimplexResult, RevisedSimplexSolver


def test_solve_remains_backward_compatible() -> None:
    solution = RevisedSimplexSolver().solve(_production_model())

    assert isinstance(solution, Solution)
    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(21.0)
    assert solution.primal_values == {"x1": pytest.approx(2.0), "x2": pytest.approx(3.0)}


def test_solve_with_details_returns_final_problem_and_basis() -> None:
    details = RevisedSimplexSolver().solve_with_details(_single_variable_model(rhs=4.0))

    assert isinstance(details, RevisedSimplexResult)
    assert details.solution.status == SolverStatus.OPTIMAL
    assert details.problem is not None
    assert details.basis is not None
    details.basis.validate(
        column_count=len(details.problem.columns),
        row_count=len(details.problem.row_names),
    )


def test_warm_start_with_final_optimal_basis_takes_zero_pivots() -> None:
    solver = RevisedSimplexSolver()
    model = _single_variable_model(rhs=4.0)
    details = solver.solve_with_details(model)

    assert details.basis is not None
    warm_details = solver.solve_with_details(model, basis=details.basis)

    assert warm_details.solution.status == SolverStatus.OPTIMAL
    assert warm_details.used_warm_start is True
    assert warm_details.iterations == 0
    assert warm_details.solution.objective_value == pytest.approx(details.solution.objective_value)
    assert warm_details.solution.primal_values == pytest.approx(details.solution.primal_values)


def test_warm_start_reoptimizes_after_rhs_change_when_basis_remains_optimal() -> None:
    solver = RevisedSimplexSolver()
    first_details = solver.solve_with_details(_single_variable_model(rhs=4.0, constant=0.0))

    assert first_details.basis is not None
    warm_details = solver.solve_with_details(
        _single_variable_model(rhs=5.0, constant=0.0),
        basis=first_details.basis,
    )

    assert warm_details.solution.status == SolverStatus.OPTIMAL
    assert warm_details.used_warm_start is True
    assert warm_details.iterations == 0
    assert warm_details.solution.objective_value == pytest.approx(10.0)
    assert warm_details.solution.primal_values == {"x": pytest.approx(5.0)}


def test_warm_start_rejects_structurally_invalid_basis() -> None:
    details = RevisedSimplexSolver().solve_with_details(
        _single_variable_model(rhs=4.0),
        basis=Basis(basic_columns=(), nonbasic_columns=(0, 1)),
    )

    assert details.solution.status == SolverStatus.ERROR
    assert details.used_warm_start is False
    assert "Invalid warm-start basis" in details.solution.message


def test_warm_start_rejects_primal_infeasible_basis() -> None:
    details = RevisedSimplexSolver().solve_with_details(
        _negative_coefficient_model(),
        basis=Basis(basic_columns=(0,), nonbasic_columns=(1,)),
    )

    assert details.solution.status == SolverStatus.ERROR
    assert details.used_warm_start is False
    assert "not primal feasible" in details.solution.message


def test_warm_start_rejects_artificial_column_model_but_normal_solve_still_works() -> None:
    solver = RevisedSimplexSolver()
    model = _ge_model()

    rejected = solver.solve_with_details(
        model,
        basis=Basis(basic_columns=(0,), nonbasic_columns=(1, 2)),
    )

    assert rejected.solution.status == SolverStatus.ERROR
    assert rejected.used_warm_start is False
    assert "not supported for models requiring artificial variables" in rejected.solution.message

    solution = solver.solve(model)
    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == pytest.approx(5.0)


def test_cold_solve_reports_positive_iteration_count_when_pivoting() -> None:
    details = RevisedSimplexSolver().solve_with_details(_single_variable_model(rhs=4.0))

    assert details.solution.status == SolverStatus.OPTIMAL
    assert details.used_warm_start is False
    assert details.iterations > 0


def _single_variable_model(rhs: float, constant: float = 1.0) -> Model:
    model = Model(name="single")
    model.add_variable(Variable(name="x"))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=rhs,
        )
    )
    model.set_objective(
        Objective(
            coefficients={"x": 2.0},
            sense=OptimizationSense.MAXIMIZE,
            constant=constant,
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
        Objective(coefficients={"x1": 3.0, "x2": 5.0}, sense=OptimizationSense.MAXIMIZE)
    )
    return model


def _negative_coefficient_model() -> Model:
    model = Model(name="negative_coefficient")
    model.add_variable(Variable(name="x"))
    model.add_constraint(
        Constraint(
            name="lower_like_row",
            coefficients={"x": -1.0},
            sense=ConstraintSense.LE,
            rhs=4.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))
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
