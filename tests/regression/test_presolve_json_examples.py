import json
from pathlib import Path

import pytest

from silo.cli.main import main
from silo.io.json_reader import read_json_model

EXAMPLE_ROOT = Path("examples/json")
PRESOLVE_EXAMPLES = (
    "fixed_var_recovery.json",
    "repeated_empty_row.json",
    "presolve_infeasible_after_fixed.json",
)


@pytest.mark.parametrize("example_name", PRESOLVE_EXAMPLES)
def test_presolve_json_examples_can_be_read(example_name: str) -> None:
    model = read_json_model(EXAMPLE_ROOT / example_name)

    assert model.name


@pytest.mark.parametrize("solver_name", ("tableau", "revised"))
def test_fixed_var_recovery_solves_with_presolve(capsys, solver_name: str) -> None:
    exit_code = main(
        [
            "solve",
            str(EXAMPLE_ROOT / "fixed_var_recovery.json"),
            "--solver",
            solver_name,
            "--presolve",
        ]
    )

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(12.0)
    assert payload["primal_values"]["x"] == pytest.approx(2.0)
    assert payload["primal_values"]["y"] == pytest.approx(3.0)
    assert payload["basis_status"]["x"] == "fixed"
    assert payload["slack_values"]["capacity"] == pytest.approx(0.0)
    assert payload["slack_values"]["y_limit"] == pytest.approx(0.0)


@pytest.mark.parametrize("solver_name", ("tableau", "revised"))
def test_repeated_empty_row_solves_with_presolve(capsys, solver_name: str) -> None:
    exit_code = main(
        [
            "solve",
            str(EXAMPLE_ROOT / "repeated_empty_row.json"),
            "--solver",
            solver_name,
            "--presolve",
        ]
    )

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(3.0)
    assert payload["primal_values"]["x"] == pytest.approx(2.0)
    assert payload["primal_values"]["y"] == pytest.approx(3.0)
    assert payload["basis_status"]["x"] == "fixed"
    assert payload["slack_values"]["x_eq_2"] == pytest.approx(0.0)
    assert payload["slack_values"]["y_limit"] == pytest.approx(0.0)


def test_repeated_empty_row_presolve_reports_reduction_order(capsys) -> None:
    exit_code = main(["presolve", str(EXAMPLE_ROOT / "repeated_empty_row.json")])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["presolve"]["status"] == "reduced"
    assert payload["presolve"]["fixed_variables"] == ["x"]
    assert [(reduction["type"], reduction["target"]) for reduction in payload["reductions"]] == [
        ("fixed_variable", "x"),
        ("empty_row", "x_eq_2"),
    ]


def test_presolve_infeasible_after_fixed_solve_reports_infeasible(capsys) -> None:
    exit_code = main(
        [
            "solve",
            str(EXAMPLE_ROOT / "presolve_infeasible_after_fixed.json"),
            "--presolve",
        ]
    )

    payload = _json_stdout(capsys)

    assert exit_code == 1
    assert payload["status"] == "infeasible"
    assert "presolve" in payload["message"].lower()
    assert "empty row" in payload["message"].lower()


def test_presolve_infeasible_after_fixed_diagnostics(capsys) -> None:
    exit_code = main(
        ["presolve", str(EXAMPLE_ROOT / "presolve_infeasible_after_fixed.json")]
    )

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["presolve"]["status"] == "infeasible"
    assert [(reduction["type"], reduction["target"]) for reduction in payload["reductions"]] == [
        ("fixed_variable", "x"),
    ]
    assert [warning["code"] for warning in payload["presolve"]["warnings"]] == [
        "empty_row_infeasible"
    ]


def test_default_solve_without_presolve_still_rejects_fixed_bounds(capsys) -> None:
    exit_code = main(["solve", str(EXAMPLE_ROOT / "fixed_var_recovery.json")])

    payload = _json_stdout(capsys)

    assert exit_code == 1
    assert payload["status"] == "error"


def _json_stdout(capsys) -> dict[str, object]:
    captured = capsys.readouterr()
    assert captured.err == ""
    return json.loads(captured.out)
