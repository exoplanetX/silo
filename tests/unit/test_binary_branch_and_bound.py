from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.mip.branch_and_bound import BranchAndBoundSolver
from silo.mip.logging import PruneReason


def test_binary_choice_model_solves_optimally() -> None:
    solution = BranchAndBoundSolver().solve(_binary_choice_model())

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == 1.0
    assert sum(solution.primal_values.values()) == 1.0
    assert set(solution.primal_values.values()) == {0.0, 1.0}
    assert solution.slack_values == {}
    assert solution.dual_values == {}
    assert solution.reduced_costs == {}
    assert solution.basis_status == {}


def test_binary_knapsack_solves_optimally() -> None:
    solution = BranchAndBoundSolver().solve(_binary_knapsack_model())

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == 22.0
    assert solution.primal_values == {"x1": 0.0, "x2": 1.0, "x3": 1.0}


def test_fractional_relaxation_branches_and_logs_branching_variable() -> None:
    result = BranchAndBoundSolver().solve_with_details(_single_fractional_binary_model())

    assert result.solution.status == SolverStatus.OPTIMAL
    assert result.solution.objective_value == 0.0
    assert result.nodes_processed > 1
    assert result.nodes_created == 3
    assert result.log[0].branching_variable == "x"
    assert result.log[0].prune_reason == PruneReason.NOT_PRUNED


def test_infeasible_binary_mip_returns_infeasible() -> None:
    result = BranchAndBoundSolver().solve_with_details(_infeasible_binary_model())

    assert result.solution.status == SolverStatus.INFEASIBLE
    assert result.solution.objective_value is None
    assert result.solution.primal_values == {}
    assert result.nodes_processed == 1
    assert result.nodes_pruned == 1
    assert result.log[0].prune_reason == PruneReason.LP_INFEASIBLE


def test_unsupported_integer_variable_returns_error() -> None:
    model = Model(name="integer")
    model.add_variable(
        Variable(
            name="x",
            bounds=Bounds(lower=0.0, upper=2.0),
            var_type=VariableType.INTEGER,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))

    solution = BranchAndBoundSolver().solve(model)

    assert solution.status == SolverStatus.ERROR
    assert "general integer variables" in solution.message


def test_unsupported_minimization_returns_error() -> None:
    model = _binary_choice_model()
    model.set_objective(Objective(coefficients={"x": 1.0, "y": 1.0}))

    solution = BranchAndBoundSolver().solve(model)

    assert solution.status == SolverStatus.ERROR
    assert "maximization" in solution.message


def test_node_limit_zero_returns_iteration_limit_without_processing_nodes() -> None:
    result = BranchAndBoundSolver(node_limit=0).solve_with_details(_binary_choice_model())

    assert result.solution.status == SolverStatus.ITERATION_LIMIT
    assert result.solution.objective_value is None
    assert result.nodes_processed == 0
    assert result.nodes_created == 1
    assert result.log == ()
    assert "node limit" in result.solution.message


def test_incumbent_details_match_solution() -> None:
    result = BranchAndBoundSolver().solve_with_details(_binary_choice_model())

    assert result.solution.status == SolverStatus.OPTIMAL
    assert result.incumbent_value == result.solution.objective_value
    assert result.nodes_processed > 0
    assert result.nodes_created >= 1
    assert result.nodes_pruned >= 1


def test_depth_first_child_order_processes_left_child_first() -> None:
    result = BranchAndBoundSolver().solve_with_details(_single_fractional_binary_model())

    assert [entry.node_id for entry in result.log] == [0, 1, 2]
    assert result.log[1].prune_reason == PruneReason.INTEGER_FEASIBLE
    assert result.log[2].prune_reason == PruneReason.LP_INFEASIBLE


def test_bound_dominated_node_is_pruned_after_incumbent_exists() -> None:
    result = BranchAndBoundSolver().solve_with_details(_bound_pruning_model())

    assert result.solution.status == SolverStatus.OPTIMAL
    assert result.solution.objective_value == 1.0
    assert PruneReason.BOUND_DOMINATED in {entry.prune_reason for entry in result.log}


def test_revised_simplex_backend_injection_solves_binary_model() -> None:
    solution = BranchAndBoundSolver(lp_solver=RevisedSimplexSolver()).solve(
        _binary_choice_model()
    )

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == 1.0


def test_lp_error_status_is_returned_as_error() -> None:
    class ErrorSolver:
        def solve(self, model: Model) -> Solution:
            return Solution(status=SolverStatus.ERROR, message=f"bad relaxation: {model.name}")

    result = BranchAndBoundSolver(lp_solver=ErrorSolver()).solve_with_details(
        _binary_choice_model()
    )

    assert result.solution.status == SolverStatus.ERROR
    assert "bad relaxation" in result.solution.message
    assert result.log[0].prune_reason == PruneReason.ERROR


def _binary_choice_model() -> Model:
    model = Model(name="choice")
    _add_binary_variable(model, "x")
    _add_binary_variable(model, "y")
    model.add_constraint(
        Constraint(
            name="choice",
            coefficients={"x": 1.0, "y": 1.0},
            sense=ConstraintSense.LE,
            rhs=1.0,
        )
    )
    model.set_objective(
        Objective(coefficients={"x": 1.0, "y": 1.0}, sense=OptimizationSense.MAXIMIZE)
    )
    return model


def _binary_knapsack_model() -> Model:
    model = Model(name="knapsack")
    for name in ("x1", "x2", "x3"):
        _add_binary_variable(model, name)
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x1": 1.0, "x2": 2.0, "x3": 3.0},
            sense=ConstraintSense.LE,
            rhs=5.0,
        )
    )
    model.set_objective(
        Objective(
            coefficients={"x1": 6.0, "x2": 10.0, "x3": 12.0},
            sense=OptimizationSense.MAXIMIZE,
        )
    )
    return model


def _single_fractional_binary_model() -> Model:
    model = Model(name="single_fractional")
    _add_binary_variable(model, "x")
    model.add_constraint(
        Constraint(
            name="half_capacity",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=0.5,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))
    return model


def _infeasible_binary_model() -> Model:
    model = Model(name="infeasible_binary")
    _add_binary_variable(model, "x")
    model.add_constraint(
        Constraint(
            name="force_one",
            coefficients={"x": 1.0},
            sense=ConstraintSense.GE,
            rhs=1.0,
        )
    )
    model.add_constraint(
        Constraint(
            name="force_zero",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=0.0,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))
    return model


def _bound_pruning_model() -> Model:
    model = Model(name="bound_pruning")
    _add_binary_variable(model, "x")
    _add_binary_variable(model, "y")
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 2.0, "y": 2.0},
            sense=ConstraintSense.LE,
            rhs=3.0,
        )
    )
    model.set_objective(
        Objective(coefficients={"x": 1.0, "y": 1.0}, sense=OptimizationSense.MAXIMIZE)
    )
    return model


def _add_binary_variable(model: Model, name: str) -> None:
    model.add_variable(
        Variable(
            name=name,
            bounds=Bounds(lower=0.0, upper=1.0),
            var_type=VariableType.BINARY,
        )
    )
