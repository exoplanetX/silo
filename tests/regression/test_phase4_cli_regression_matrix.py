import json
from pathlib import Path
from typing import NamedTuple

import pytest

from silo.cli.main import main

EXAMPLE_ROOT = Path("examples/json")
SOLUTION_FIELDS = {
    "status",
    "objective_value",
    "primal_values",
    "slack_values",
    "dual_values",
    "reduced_costs",
    "basis_status",
    "message",
}
PRESOLVE_FIELDS = {"model_path", "presolve", "reductions", "scaling"}
COMPARE_FIELDS = {"model_path", "consistent", "tolerance", "checks", "tableau", "revised"}


class SolveExpectation(NamedTuple):
    exit_code: int
    status: str


class PresolveExpectation(NamedTuple):
    exit_code: int
    status: str


class CompareExpectation(NamedTuple):
    exit_code: int
    consistent: bool
    tableau_status: str
    revised_status: str


class ExampleExpectation(NamedTuple):
    solve: SolveExpectation
    solve_tableau: SolveExpectation
    solve_revised: SolveExpectation
    solve_presolve: SolveExpectation
    solve_tableau_presolve: SolveExpectation
    solve_revised_presolve: SolveExpectation
    presolve: PresolveExpectation
    compare: CompareExpectation


OPTIMAL = SolveExpectation(0, "optimal")
INFEASIBLE = SolveExpectation(1, "infeasible")
ERROR = SolveExpectation(1, "error")
NO_CHANGE = PresolveExpectation(0, "no_change")
REDUCED = PresolveExpectation(0, "reduced")
PRESOLVE_INFEASIBLE = PresolveExpectation(0, "infeasible")
OPTIMAL_COMPARE = CompareExpectation(0, True, "optimal", "optimal")
INFEASIBLE_COMPARE = CompareExpectation(0, True, "infeasible", "infeasible")
ERROR_COMPARE = CompareExpectation(0, True, "error", "error")

EXAMPLE_EXPECTATIONS = {
    "equality_row.json": ExampleExpectation(
        solve=OPTIMAL,
        solve_tableau=OPTIMAL,
        solve_revised=OPTIMAL,
        solve_presolve=OPTIMAL,
        solve_tableau_presolve=OPTIMAL,
        solve_revised_presolve=OPTIMAL,
        presolve=NO_CHANGE,
        compare=OPTIMAL_COMPARE,
    ),
    "fixed_var_recovery.json": ExampleExpectation(
        solve=ERROR,
        solve_tableau=ERROR,
        solve_revised=ERROR,
        solve_presolve=OPTIMAL,
        solve_tableau_presolve=OPTIMAL,
        solve_revised_presolve=OPTIMAL,
        presolve=REDUCED,
        compare=ERROR_COMPARE,
    ),
    "ge_row.json": ExampleExpectation(
        solve=OPTIMAL,
        solve_tableau=OPTIMAL,
        solve_revised=OPTIMAL,
        solve_presolve=OPTIMAL,
        solve_tableau_presolve=OPTIMAL,
        solve_revised_presolve=OPTIMAL,
        presolve=NO_CHANGE,
        compare=OPTIMAL_COMPARE,
    ),
    "infeasible.json": ExampleExpectation(
        solve=INFEASIBLE,
        solve_tableau=INFEASIBLE,
        solve_revised=INFEASIBLE,
        solve_presolve=INFEASIBLE,
        solve_tableau_presolve=INFEASIBLE,
        solve_revised_presolve=INFEASIBLE,
        presolve=NO_CHANGE,
        compare=INFEASIBLE_COMPARE,
    ),
    "presolve_infeasible_after_fixed.json": ExampleExpectation(
        solve=ERROR,
        solve_tableau=ERROR,
        solve_revised=ERROR,
        solve_presolve=INFEASIBLE,
        solve_tableau_presolve=INFEASIBLE,
        solve_revised_presolve=INFEASIBLE,
        presolve=PRESOLVE_INFEASIBLE,
        compare=ERROR_COMPARE,
    ),
    "production.json": ExampleExpectation(
        solve=OPTIMAL,
        solve_tableau=OPTIMAL,
        solve_revised=OPTIMAL,
        solve_presolve=OPTIMAL,
        solve_tableau_presolve=OPTIMAL,
        solve_revised_presolve=OPTIMAL,
        presolve=NO_CHANGE,
        compare=OPTIMAL_COMPARE,
    ),
    "repeated_empty_row.json": ExampleExpectation(
        solve=ERROR,
        solve_tableau=ERROR,
        solve_revised=ERROR,
        solve_presolve=OPTIMAL,
        solve_tableau_presolve=OPTIMAL,
        solve_revised_presolve=OPTIMAL,
        presolve=REDUCED,
        compare=ERROR_COMPARE,
    ),
}


@pytest.mark.parametrize("example_name", sorted(EXAMPLE_EXPECTATIONS))
def test_every_expected_example_exists(example_name: str) -> None:
    assert (EXAMPLE_ROOT / example_name).exists()


def test_every_json_example_has_phase4_expectations() -> None:
    example_names = {path.name for path in EXAMPLE_ROOT.glob("*.json")}

    assert example_names == set(EXAMPLE_EXPECTATIONS)


@pytest.mark.parametrize(
    ("command_name", "args", "expectation_key"),
    [
        ("solve", ["solve"], "solve"),
        ("solve_tableau", ["solve", "--solver", "tableau"], "solve_tableau"),
        ("solve_revised", ["solve", "--solver", "revised"], "solve_revised"),
        ("solve_presolve", ["solve", "--presolve"], "solve_presolve"),
        (
            "solve_tableau_presolve",
            ["solve", "--solver", "tableau", "--presolve"],
            "solve_tableau_presolve",
        ),
        (
            "solve_revised_presolve",
            ["solve", "--solver", "revised", "--presolve"],
            "solve_revised_presolve",
        ),
    ],
)
@pytest.mark.parametrize("example_name", sorted(EXAMPLE_EXPECTATIONS))
def test_phase4_solve_matrix(
    capsys,
    example_name: str,
    command_name: str,
    args: list[str],
    expectation_key: str,
) -> None:
    expectation = getattr(EXAMPLE_EXPECTATIONS[example_name], expectation_key)
    exit_code = main([args[0], str(EXAMPLE_ROOT / example_name), *args[1:]])

    payload = _json_stdout(capsys)

    assert command_name
    assert exit_code == expectation.exit_code
    assert set(payload) == SOLUTION_FIELDS
    assert payload["status"] == expectation.status


@pytest.mark.parametrize("example_name", sorted(EXAMPLE_EXPECTATIONS))
def test_phase4_presolve_matrix(capsys, example_name: str) -> None:
    expectation = EXAMPLE_EXPECTATIONS[example_name].presolve

    exit_code = main(["presolve", str(EXAMPLE_ROOT / example_name)])

    payload = _json_stdout(capsys)

    assert exit_code == expectation.exit_code
    assert set(payload) == PRESOLVE_FIELDS
    assert payload["presolve"]["status"] == expectation.status


@pytest.mark.parametrize("example_name", sorted(EXAMPLE_EXPECTATIONS))
def test_phase4_compare_matrix(capsys, example_name: str) -> None:
    expectation = EXAMPLE_EXPECTATIONS[example_name].compare

    exit_code = main(["compare", str(EXAMPLE_ROOT / example_name)])

    payload = _json_stdout(capsys)

    assert exit_code == expectation.exit_code
    assert set(payload) == COMPARE_FIELDS
    assert payload["consistent"] is expectation.consistent
    assert payload["tableau"]["status"] == expectation.tableau_status
    assert payload["revised"]["status"] == expectation.revised_status


def _json_stdout(capsys) -> dict[str, object]:
    captured = capsys.readouterr()
    assert captured.err == ""
    return json.loads(captured.out)
