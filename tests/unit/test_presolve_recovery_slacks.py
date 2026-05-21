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
from silo.presolve import PresolveDiagnostics, Presolver, PresolveResult, ScalingDiagnostics


def test_recover_solution_recomputes_original_slacks_for_removed_rows() -> None:
    model = _fixed_x_with_removed_rows_model()
    result = Presolver().run(model)

    presolved_solution = TableauSimplexSolver().solve(result.model)
    recovered = result.recover_solution(presolved_solution)

    assert recovered.status == SolverStatus.OPTIMAL
    assert recovered.primal_values == {"y": pytest.approx(3.0), "x": pytest.approx(2.0)}
    assert recovered.slack_values == {
        "x_le_3": pytest.approx(1.0),
        "x_ge_1": pytest.approx(1.0),
        "x_eq_2": pytest.approx(0.0),
        "y_limit": pytest.approx(0.0),
    }


def test_recover_solution_uses_original_constraint_names_only() -> None:
    model = _fixed_x_with_removed_rows_model()
    result = Presolver().run(model)
    presolved_solution = Solution(
        status=SolverStatus.OPTIMAL,
        objective_value=3.0,
        primal_values={"y": 3.0},
        slack_values={"y_limit": 0.0, "transformed_only": 7.0},
        reduced_costs={"y": 0.0},
        basis_status={"y": "basic"},
    )

    recovered = result.recover_solution(presolved_solution)

    assert set(recovered.slack_values) == {"x_le_3", "x_ge_1", "x_eq_2", "y_limit"}
    assert "transformed_only" not in recovered.slack_values


def test_manual_presolve_result_without_original_model_preserves_solver_slacks() -> None:
    model = Model(name="manual")
    solution = Solution(
        status=SolverStatus.OPTIMAL,
        objective_value=0.0,
        primal_values={},
        slack_values={"solver_row": 1.0},
    )
    result = PresolveResult(
        model=model,
        reductions=(),
        diagnostics=PresolveDiagnostics(),
        scaling=ScalingDiagnostics(),
    )

    recovered = result.recover_solution(solution)

    assert recovered.slack_values == {"solver_row": 1.0}


def _fixed_x_with_removed_rows_model() -> Model:
    model = Model(name="fixed_x_removed_rows")
    model.add_variable(Variable(name="x", bounds=Bounds(lower=2.0, upper=2.0)))
    model.add_variable(Variable(name="y"))
    model.add_constraint(
        Constraint(
            name="x_le_3",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=3.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="x_ge_1",
            coefficients={"x": 1.0},
            sense=ConstraintSense.GE,
            rhs=1.0,
        )
    )
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
