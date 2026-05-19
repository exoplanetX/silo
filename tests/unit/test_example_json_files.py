from pathlib import Path

import pytest

from silo.core.status import SolverStatus
from silo.io.json_reader import read_json_model
from silo.lp.simplex.tableau import TableauSimplexSolver

EXAMPLE_DIR = Path("examples/json")


@pytest.mark.parametrize("path", sorted(EXAMPLE_DIR.glob("*.json")))
def test_example_json_files_can_be_read(path: Path) -> None:
    model = read_json_model(path)

    assert model.name


@pytest.mark.parametrize(
    ("filename", "expected_status", "expected_objective"),
    [
        ("production.json", SolverStatus.OPTIMAL, 21.0),
        ("ge_row.json", SolverStatus.OPTIMAL, 5.0),
        ("equality_row.json", SolverStatus.OPTIMAL, 4.0),
        ("infeasible.json", SolverStatus.INFEASIBLE, None),
    ],
)
def test_example_json_files_solve_with_tableau(
    filename: str,
    expected_status: SolverStatus,
    expected_objective: float | None,
) -> None:
    model = read_json_model(EXAMPLE_DIR / filename)

    solution = TableauSimplexSolver().solve(model)

    assert solution.status == expected_status
    if expected_objective is not None:
        assert solution.objective_value == pytest.approx(expected_objective)
