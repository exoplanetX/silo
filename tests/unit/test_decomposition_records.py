from dataclasses import FrozenInstanceError
from math import inf, nan

import pytest

from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.decomposition import (
    BendersSolver,
    ColumnGenerationSolver,
    MasterProblem,
    MasterProblemContext,
    MasterProblemResult,
    Subproblem,
    SubproblemContext,
    SubproblemResult,
)


def _model(name: str = "toy") -> Model:
    return Model(name=name)


def test_master_problem_context_and_result_are_validated_and_normalized() -> None:
    metadata = {"z": 2, "a": "alpha"}
    problem = MasterProblem(_model(), name=" master ", metadata=metadata)
    metadata["a"] = "changed"

    context = MasterProblemContext(
        problem,
        iteration_id=2,
        incumbent_values={"y": 2, "x": 1},
    )
    result = MasterProblemResult(
        status="optimal",
        objective_value=3,
        primal_values={"y": 2, "x": 1},
        dual_values={"capacity": 0.5},
        reduced_costs={"x": 0},
        message="solved",
    )

    assert problem.name == "master"
    assert problem.metadata == (("a", "alpha"), ("z", 2))
    assert context.iteration_id == 2
    assert context.incumbent_values == (("x", 1.0), ("y", 2.0))
    assert result.status == SolverStatus.OPTIMAL
    assert result.objective_value == 3.0
    assert result.primal_values == (("x", 1.0), ("y", 2.0))
    assert result.dual_values == (("capacity", 0.5),)
    assert result.reduced_costs == (("x", 0.0),)
    assert result.message == "solved"


def test_master_result_from_solution_defensively_copies_solution_mappings() -> None:
    solution = Solution(
        status=SolverStatus.OPTIMAL,
        objective_value=4.0,
        primal_values={"y": 2.0, "x": 1.0},
        dual_values={"row": 0.25},
        reduced_costs={"x": 0.0},
        message="lp solved",
    )

    result = MasterProblemResult.from_solution(solution, metadata={"source": "lp"})
    solution.primal_values["x"] = 99.0

    assert result.status == SolverStatus.OPTIMAL
    assert result.primal_values == (("x", 1.0), ("y", 2.0))
    assert result.dual_values == (("row", 0.25),)
    assert result.metadata == (("source", "lp"),)


def test_master_records_are_immutable_at_dataclass_boundary() -> None:
    problem = MasterProblem(_model())
    context = MasterProblemContext(problem)
    result = MasterProblemResult(status=SolverStatus.NOT_SOLVED)

    with pytest.raises(FrozenInstanceError):
        problem.name = "other"
    with pytest.raises(FrozenInstanceError):
        context.iteration_id = 3
    with pytest.raises(FrozenInstanceError):
        result.message = "changed"


def test_subproblem_context_and_result_are_validated_and_normalized() -> None:
    problem = Subproblem(_model("sub"), name=" worker ", metadata={"role": "pricing"})
    context = SubproblemContext(
        problem,
        iteration_id=1,
        master_values={"theta": 3, "x": 1},
        master_objective=8,
    )
    result = SubproblemResult(
        status="infeasible",
        objective_value=1.5,
        generated_cut_count=2,
        generated_column_count=0,
        message="generated cuts",
    )

    assert problem.name == "worker"
    assert problem.metadata == (("role", "pricing"),)
    assert context.master_values == (("theta", 3.0), ("x", 1.0))
    assert context.master_objective == 8.0
    assert result.status == SolverStatus.INFEASIBLE
    assert result.generated_cut_count == 2
    assert result.generated_column_count == 0


def test_subproblem_records_are_immutable_at_dataclass_boundary() -> None:
    problem = Subproblem(_model())
    context = SubproblemContext(problem)
    result = SubproblemResult(status=SolverStatus.NOT_SOLVED)

    with pytest.raises(FrozenInstanceError):
        problem.name = "other"
    with pytest.raises(FrozenInstanceError):
        context.master_objective = 1.0
    with pytest.raises(FrozenInstanceError):
        result.generated_cut_count = 1


@pytest.mark.parametrize(
    "factory",
    [
        lambda: MasterProblem(_model(), name=" "),
        lambda: Subproblem(_model(), name=" "),
    ],
)
def test_rejects_blank_names(factory: object) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        factory()


@pytest.mark.parametrize(
    "factory",
    [
        lambda: MasterProblemContext(MasterProblem(_model()), iteration_id=-1),
        lambda: SubproblemContext(Subproblem(_model()), iteration_id=-1),
    ],
)
def test_rejects_negative_iteration_ids(factory: object) -> None:
    with pytest.raises(ValueError, match="must be nonnegative"):
        factory()


@pytest.mark.parametrize(
    "factory",
    [
        lambda: MasterProblemResult(status="unknown"),
        lambda: SubproblemResult(status="unknown"),
    ],
)
def test_rejects_invalid_statuses(factory: object) -> None:
    with pytest.raises(ValueError, match="supported SolverStatus"):
        factory()


@pytest.mark.parametrize("value", [inf, -inf, nan])
def test_rejects_nonfinite_master_numeric_values(value: float) -> None:
    problem = MasterProblem(_model())

    with pytest.raises(ValueError, match="finite"):
        MasterProblemContext(problem, incumbent_values={"x": value})
    with pytest.raises(ValueError, match="finite"):
        MasterProblemResult(status=SolverStatus.OPTIMAL, objective_value=value)
    with pytest.raises(ValueError, match="finite"):
        MasterProblemResult(status=SolverStatus.OPTIMAL, primal_values={"x": value})


@pytest.mark.parametrize("value", [inf, -inf, nan])
def test_rejects_nonfinite_subproblem_numeric_values(value: float) -> None:
    problem = Subproblem(_model())

    with pytest.raises(ValueError, match="finite"):
        SubproblemContext(problem, master_values={"x": value})
    with pytest.raises(ValueError, match="finite"):
        SubproblemContext(problem, master_objective=value)
    with pytest.raises(ValueError, match="finite"):
        SubproblemResult(status=SolverStatus.OPTIMAL, objective_value=value)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"generated_cut_count": -1},
        {"generated_column_count": -1},
    ],
)
def test_rejects_negative_subproblem_generated_counts(kwargs: dict[str, int]) -> None:
    with pytest.raises(ValueError, match="must be nonnegative"):
        SubproblemResult(status=SolverStatus.OPTIMAL, **kwargs)


def test_public_exports_and_placeholder_solvers_remain_not_solved() -> None:
    model = _model()

    assert MasterProblem(model)
    assert MasterProblemContext(MasterProblem(model))
    assert MasterProblemResult(status=SolverStatus.NOT_SOLVED)
    assert Subproblem(model)
    assert SubproblemContext(Subproblem(model))
    assert SubproblemResult(status=SolverStatus.NOT_SOLVED)
    assert BendersSolver().solve(model).status == SolverStatus.NOT_SOLVED
    assert ColumnGenerationSolver().solve(model).status == SolverStatus.NOT_SOLVED
