from dataclasses import dataclass
from pathlib import Path

import pytest

from silo.core.status import SolverStatus
from silo.io.json_reader import read_json_model
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.mip.branch_and_bound import BranchAndBoundSolver

EXAMPLES_DIR = Path("examples/mip")


@dataclass(frozen=True)
class MIPExpectation:
    status: SolverStatus
    objective_value: float | None
    primal_values: dict[str, float] | None = None


EXPECTATIONS: dict[str, MIPExpectation] = {
    "binary_choice.json": MIPExpectation(SolverStatus.OPTIMAL, 1.0),
    "binary_knapsack.json": MIPExpectation(
        SolverStatus.OPTIMAL,
        22.0,
        {"item_1": 0.0, "item_2": 1.0, "item_3": 1.0},
    ),
    "infeasible_binary.json": MIPExpectation(SolverStatus.INFEASIBLE, None, {}),
    "integer_allocation.json": MIPExpectation(
        SolverStatus.OPTIMAL,
        7.0,
        {"x": 1.0, "y": 2.0},
    ),
    "mixed_binary_integer.json": MIPExpectation(
        SolverStatus.OPTIMAL,
        11.0,
        {"b": 1.0, "x": 2.0},
    ),
    "mixed_continuous_integer.json": MIPExpectation(
        SolverStatus.OPTIMAL,
        11.0,
        {"x": 2.0, "y": 1.0},
    ),
}

REVISED_BACKEND_EXAMPLES = (
    "binary_knapsack.json",
    "integer_allocation.json",
    "mixed_continuous_integer.json",
)


def test_every_mip_json_example_has_expectation() -> None:
    files = {path.name for path in EXAMPLES_DIR.glob("*.json")}

    assert files == set(EXPECTATIONS)


def test_every_expectation_file_exists() -> None:
    for filename in EXPECTATIONS:
        assert (EXAMPLES_DIR / filename).exists()


@pytest.mark.parametrize("filename", sorted(EXPECTATIONS))
def test_mip_json_example_is_readable(filename: str) -> None:
    model = read_json_model(EXAMPLES_DIR / filename)

    assert model.name


@pytest.mark.parametrize("filename", sorted(EXPECTATIONS))
def test_mip_json_example_solves_with_default_branch_and_bound(filename: str) -> None:
    model = read_json_model(EXAMPLES_DIR / filename)
    expectation = EXPECTATIONS[filename]

    solution = BranchAndBoundSolver().solve(model)

    assert solution.status == expectation.status
    if expectation.objective_value is None:
        assert solution.objective_value is None
    else:
        assert solution.objective_value == pytest.approx(expectation.objective_value)


@pytest.mark.parametrize("filename", REVISED_BACKEND_EXAMPLES)
def test_selected_mip_json_examples_solve_with_revised_lp_backend(filename: str) -> None:
    model = read_json_model(EXAMPLES_DIR / filename)
    expectation = EXPECTATIONS[filename]

    solution = BranchAndBoundSolver(lp_solver=RevisedSimplexSolver()).solve(model)

    assert solution.status == expectation.status
    assert solution.objective_value == pytest.approx(expectation.objective_value)


@pytest.mark.parametrize(
    "filename",
    [
        "binary_knapsack.json",
        "integer_allocation.json",
        "mixed_binary_integer.json",
        "mixed_continuous_integer.json",
    ],
)
def test_mip_json_examples_have_expected_primal_values(filename: str) -> None:
    model = read_json_model(EXAMPLES_DIR / filename)
    expectation = EXPECTATIONS[filename]

    solution = BranchAndBoundSolver().solve(model)

    assert expectation.primal_values is not None
    for variable_name, expected_value in expectation.primal_values.items():
        assert solution.primal_values[variable_name] == pytest.approx(expected_value)


def test_binary_choice_json_has_one_selected_variable() -> None:
    model = read_json_model(EXAMPLES_DIR / "binary_choice.json")

    solution = BranchAndBoundSolver().solve(model)

    assert solution.status == SolverStatus.OPTIMAL
    assert set(solution.primal_values) == {"x", "y"}
    assert sum(solution.primal_values.values()) == pytest.approx(1.0)
    assert set(solution.primal_values.values()) == {0.0, 1.0}


def test_infeasible_mip_json_example_returns_infeasible() -> None:
    model = read_json_model(EXAMPLES_DIR / "infeasible_binary.json")

    solution = BranchAndBoundSolver().solve(model)

    assert solution.status == SolverStatus.INFEASIBLE
    assert solution.objective_value is None
    assert solution.primal_values == {}


def test_mip_json_example_details_smoke() -> None:
    model = read_json_model(EXAMPLES_DIR / "integer_allocation.json")

    details = BranchAndBoundSolver().solve_with_details(model)

    assert details.nodes_processed > 0
    assert details.nodes_created >= 1
    assert details.log
    assert details.solution.status == SolverStatus.OPTIMAL
