from silo.core.bounds import Bounds
from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense, OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.mip.branch_and_bound import BranchAndBoundSolver


def test_single_bounded_integer_variable_solves_optimally() -> None:
    solution = BranchAndBoundSolver().solve(_single_bounded_integer_model())

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == 6.0
    assert solution.primal_values["x"] == 2.0


def test_bounded_integer_allocation_solves_optimally() -> None:
    solution = BranchAndBoundSolver().solve(_bounded_integer_allocation_model())

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == 7.0
    assert solution.primal_values["x"] == 1.0
    assert solution.primal_values["y"] == 2.0


def test_mixed_binary_and_integer_model_solves_optimally() -> None:
    solution = BranchAndBoundSolver().solve(_mixed_binary_integer_model())

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == 11.0
    assert solution.primal_values["b"] == 1.0
    assert solution.primal_values["x"] == 2.0


def test_mixed_continuous_and_integer_model_solves_optimally() -> None:
    solution = BranchAndBoundSolver().solve(_mixed_continuous_integer_model())

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == 11.0
    assert solution.primal_values["x"] == 2.0
    assert solution.primal_values["y"] == 1.0


def test_branching_on_integer_value_greater_than_one() -> None:
    result = BranchAndBoundSolver().solve_with_details(_single_bounded_integer_model())

    assert result.solution.status == SolverStatus.OPTIMAL
    assert result.log[0].branching_variable == "x"
    assert result.nodes_created == 3
    assert [entry.node_id for entry in result.log] == [0, 1, 2]


def test_unbounded_integer_variable_returns_error() -> None:
    model = Model(name="unbounded_integer")
    model.add_variable(Variable(name="x", var_type=VariableType.INTEGER))
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))

    solution = BranchAndBoundSolver().solve(model)

    assert solution.status == SolverStatus.ERROR
    assert "finite upper bound" in solution.message


def test_non_integer_upper_bound_returns_error() -> None:
    model = Model(name="bad_integer_upper")
    model.add_variable(
        Variable(
            name="x",
            bounds=Bounds(lower=0.0, upper=2.5),
            var_type=VariableType.INTEGER,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))

    solution = BranchAndBoundSolver().solve(model)

    assert solution.status == SolverStatus.ERROR
    assert "upper bound must be integer-valued" in solution.message


def test_nonzero_integer_lower_bound_returns_error() -> None:
    model = Model(name="bad_integer_lower")
    model.add_variable(
        Variable(
            name="x",
            bounds=Bounds(lower=1.0, upper=3.0),
            var_type=VariableType.INTEGER,
        )
    )
    model.set_objective(Objective(coefficients={"x": 1.0}, sense=OptimizationSense.MAXIMIZE))

    solution = BranchAndBoundSolver().solve(model)

    assert solution.status == SolverStatus.ERROR
    assert "lower bound must be 0" in solution.message


def test_continuous_finite_upper_bound_returns_error() -> None:
    model = _mixed_continuous_integer_model()
    model.variables[1] = Variable(name="y", bounds=Bounds(lower=0.0, upper=4.0))

    solution = BranchAndBoundSolver().solve(model)

    assert solution.status == SolverStatus.ERROR
    assert "finite upper bounds" in solution.message


def test_revised_simplex_backend_injection_solves_integer_model() -> None:
    solution = BranchAndBoundSolver(lp_solver=RevisedSimplexSolver()).solve(
        _bounded_integer_allocation_model()
    )

    assert solution.status == SolverStatus.OPTIMAL
    assert solution.objective_value == 7.0
    assert solution.primal_values["x"] == 1.0
    assert solution.primal_values["y"] == 2.0


def _single_bounded_integer_model() -> Model:
    model = Model(name="single_integer")
    _add_integer_variable(model, "x", 3.0)
    model.add_constraint(
        Constraint(
            name="row_limit",
            coefficients={"x": 1.0},
            sense=ConstraintSense.LE,
            rhs=2.5,
        )
    )
    model.set_objective(Objective(coefficients={"x": 3.0}, sense=OptimizationSense.MAXIMIZE))
    return model


def _bounded_integer_allocation_model() -> Model:
    model = Model(name="integer_allocation")
    _add_integer_variable(model, "x", 2.0)
    _add_integer_variable(model, "y", 3.0)
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 2.0, "y": 1.0},
            sense=ConstraintSense.LE,
            rhs=4.0,
        )
    )
    model.set_objective(
        Objective(coefficients={"x": 3.0, "y": 2.0}, sense=OptimizationSense.MAXIMIZE)
    )
    return model


def _mixed_binary_integer_model() -> Model:
    model = Model(name="mixed_binary_integer")
    model.add_variable(
        Variable(
            name="b",
            bounds=Bounds(lower=0.0, upper=1.0),
            var_type=VariableType.BINARY,
        )
    )
    _add_integer_variable(model, "x", 3.0)
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"b": 2.0, "x": 1.0},
            sense=ConstraintSense.LE,
            rhs=4.0,
        )
    )
    model.set_objective(
        Objective(coefficients={"b": 5.0, "x": 3.0}, sense=OptimizationSense.MAXIMIZE)
    )
    return model


def _mixed_continuous_integer_model() -> Model:
    model = Model(name="mixed_continuous_integer")
    _add_integer_variable(model, "x", 2.0)
    model.add_variable(Variable(name="y"))
    model.add_constraint(
        Constraint(
            name="capacity",
            coefficients={"x": 1.0, "y": 1.0},
            sense=ConstraintSense.LE,
            rhs=3.0,
        )
    )
    model.set_objective(
        Objective(coefficients={"x": 5.0, "y": 1.0}, sense=OptimizationSense.MAXIMIZE)
    )
    return model


def _add_integer_variable(model: Model, name: str, upper: float) -> None:
    model.add_variable(
        Variable(
            name=name,
            bounds=Bounds(lower=0.0, upper=upper),
            var_type=VariableType.INTEGER,
        )
    )
