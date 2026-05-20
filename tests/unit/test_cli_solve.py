import json
from pathlib import Path

import pytest

from silo.cli.main import main

FIXTURE_ROOT = Path("tests/fixtures")
EXAMPLE_ROOT = Path("examples/json")
PRODUCTION_MODEL = FIXTURE_ROOT / "lp_small" / "production.json"
KNAPSACK_MODEL = FIXTURE_ROOT / "mip_small" / "knapsack.json"
EXAMPLE_PRODUCTION_MODEL = EXAMPLE_ROOT / "production.json"
EXAMPLE_GE_MODEL = EXAMPLE_ROOT / "ge_row.json"
EXAMPLE_EQUALITY_MODEL = EXAMPLE_ROOT / "equality_row.json"
EXAMPLE_INFEASIBLE_MODEL = EXAMPLE_ROOT / "infeasible.json"


def test_cli_solve_prints_solution_json_to_stdout(capsys) -> None:
    exit_code = main(["solve", str(PRODUCTION_MODEL)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert captured.err == ""
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(21.0)
    assert payload["primal_values"] == {"x1": pytest.approx(2.0), "x2": pytest.approx(3.0)}
    assert payload["slack_values"] == {"labor": 0.0, "material": 0.0}
    assert payload["reduced_costs"] == {"x1": 0.0, "x2": 0.0}
    assert payload["basis_status"] == {"x1": "basic", "x2": "basic"}
    assert payload["dual_values"] == {}


def test_cli_solve_accepts_explicit_tableau_solver(capsys) -> None:
    exit_code = main(["solve", str(EXAMPLE_PRODUCTION_MODEL), "--solver", "tableau"])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(21.0)


def test_cli_solve_accepts_explicit_revised_solver(capsys) -> None:
    exit_code = main(["solve", str(EXAMPLE_PRODUCTION_MODEL), "--solver", "revised"])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(21.0)
    assert payload["message"] == "Revised simplex solved the LP."


def test_cli_solve_revised_handles_phase_one_ge_example(capsys) -> None:
    exit_code = main(["solve", str(EXAMPLE_GE_MODEL), "--solver", "revised"])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(5.0)
    assert payload["primal_values"] == {"x": pytest.approx(5.0)}


def test_cli_solve_revised_handles_phase_one_equality_example(capsys) -> None:
    exit_code = main(["solve", str(EXAMPLE_EQUALITY_MODEL), "--solver", "revised"])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(4.0)
    assert payload["slack_values"]["balance"] == pytest.approx(0.0)


def test_cli_solve_revised_returns_infeasible_status_and_exit_code(capsys) -> None:
    exit_code = main(["solve", str(EXAMPLE_INFEASIBLE_MODEL), "--solver", "revised"])

    payload = _json_stdout(capsys)

    assert exit_code == 1
    assert payload["status"] == "infeasible"


def test_cli_solve_revised_writes_solution_json_to_output_file(tmp_path, capsys) -> None:
    output_path = tmp_path / "nested" / "revised_solution.json"

    exit_code = main(
        [
            "solve",
            str(EXAMPLE_PRODUCTION_MODEL),
            "--solver",
            "revised",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert output_path.exists()
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(21.0)


def test_cli_solve_rejects_invalid_solver_name(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["solve", str(PRODUCTION_MODEL), "--solver", "unknown"])

    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    assert captured.out == ""
    assert "invalid choice" in captured.err


def test_cli_solve_writes_solution_json_to_output_file(tmp_path, capsys) -> None:
    output_path = tmp_path / "nested" / "solution.json"

    exit_code = main(["solve", str(PRODUCTION_MODEL), "--output", str(output_path)])

    captured = capsys.readouterr()
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert output_path.exists()
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(21.0)
    assert "slack_values" in payload
    assert "reduced_costs" in payload
    assert "basis_status" in payload


def test_cli_solve_missing_model_path_returns_error(capsys) -> None:
    exit_code = main(["solve", "missing-model.json"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Error: model file not found:" in captured.err


def test_cli_solve_unsupported_model_returns_solution_json_with_error(capsys) -> None:
    exit_code = main(["solve", str(KNAPSACK_MODEL)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 1
    assert captured.err == ""
    assert payload["status"] == "error"
    assert "continuous variables" in payload["message"]


def test_cli_solve_unsupported_binary_model_with_revised_solver(capsys) -> None:
    exit_code = main(["solve", str(KNAPSACK_MODEL), "--solver", "revised"])

    payload = _json_stdout(capsys)

    assert exit_code == 1
    assert payload["status"] == "error"
    assert "continuous variables" in payload["message"]


def _json_stdout(capsys) -> dict[str, object]:
    captured = capsys.readouterr()
    assert captured.err == ""
    return json.loads(captured.out)
