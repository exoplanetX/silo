import json
from pathlib import Path

import pytest

from silo.cli.main import main

FIXTURE_ROOT = Path("tests/fixtures")
PRODUCTION_MODEL = FIXTURE_ROOT / "lp_small" / "production.json"
KNAPSACK_MODEL = FIXTURE_ROOT / "mip_small" / "knapsack.json"


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
