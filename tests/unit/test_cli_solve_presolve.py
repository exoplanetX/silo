import json
from pathlib import Path

import pytest

from silo.cli.main import main

EXAMPLE_ROOT = Path("examples/json")
EXAMPLE_PRODUCTION_MODEL = EXAMPLE_ROOT / "production.json"
REQUIRED_SOLUTION_FIELDS = {
    "status",
    "objective_value",
    "primal_values",
    "slack_values",
    "dual_values",
    "reduced_costs",
    "basis_status",
    "message",
}


def test_cli_solve_default_behavior_remains_unchanged(capsys) -> None:
    exit_code = main(["solve", str(EXAMPLE_PRODUCTION_MODEL)])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(21.0)


def test_cli_solve_with_presolve_on_unchanged_model(capsys) -> None:
    exit_code = main(["solve", str(EXAMPLE_PRODUCTION_MODEL), "--presolve"])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert set(payload) == REQUIRED_SOLUTION_FIELDS
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(21.0)
    assert "presolve" not in payload
    assert "scaling" not in payload


def test_cli_solve_with_revised_and_presolve(capsys) -> None:
    exit_code = main(
        ["solve", str(EXAMPLE_PRODUCTION_MODEL), "--solver", "revised", "--presolve"]
    )

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(21.0)


def test_cli_solve_presolve_detects_infeasible_empty_row(tmp_path, capsys) -> None:
    model_path = _write_model(
        tmp_path,
        {
            "name": "bad_empty_row",
            "sense": "maximize",
            "constraints": [
                {
                    "name": "bad",
                    "coefficients": {},
                    "sense": "<=",
                    "rhs": -1.0,
                }
            ],
        },
    )

    exit_code = main(["solve", str(model_path), "--presolve"])

    payload = _json_stdout(capsys)

    assert exit_code == 1
    assert payload["status"] == "infeasible"
    assert "presolve" in payload["message"].lower()


def test_cli_solve_presolve_detects_unbounded_empty_column(tmp_path, capsys) -> None:
    model_path = _write_model(
        tmp_path,
        {
            "name": "empty_column_unbounded",
            "sense": "maximize",
            "variables": [{"name": "x", "lower": 0.0, "upper": None}],
            "objective": {"coefficients": {"x": 1.0}},
        },
    )

    exit_code = main(["solve", str(model_path), "--presolve"])

    payload = _json_stdout(capsys)

    assert exit_code == 1
    assert payload["status"] == "unbounded"
    assert "presolve" in payload["message"].lower()


def test_cli_solve_presolve_recovers_fixed_variable_with_tableau(tmp_path, capsys) -> None:
    model_path = _write_model(tmp_path, _fixed_variable_model_payload())

    exit_code = main(["solve", str(model_path), "--solver", "tableau", "--presolve"])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "optimal"
    assert payload["primal_values"]["x"] == pytest.approx(2.0)
    assert payload["primal_values"]["y"] == pytest.approx(3.0)
    assert payload["objective_value"] == pytest.approx(12.0)
    assert payload["basis_status"]["x"] == "fixed"


def test_cli_solve_presolve_recovers_fixed_variable_with_revised(tmp_path, capsys) -> None:
    model_path = _write_model(tmp_path, _fixed_variable_model_payload())

    exit_code = main(["solve", str(model_path), "--solver", "revised", "--presolve"])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "optimal"
    assert payload["primal_values"]["x"] == pytest.approx(2.0)
    assert payload["primal_values"]["y"] == pytest.approx(3.0)
    assert payload["objective_value"] == pytest.approx(12.0)
    assert payload["basis_status"]["x"] == "fixed"


def test_cli_solve_presolve_writes_recovered_solution_to_output_file(
    tmp_path,
    capsys,
) -> None:
    model_path = _write_model(tmp_path, _fixed_variable_model_payload())
    output_path = tmp_path / "nested" / "solution.json"

    exit_code = main(
        [
            "solve",
            str(model_path),
            "--presolve",
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
    assert set(payload) == REQUIRED_SOLUTION_FIELDS
    assert payload["primal_values"]["x"] == pytest.approx(2.0)
    assert payload["primal_values"]["y"] == pytest.approx(3.0)
    assert payload["basis_status"]["x"] == "fixed"


def _fixed_variable_model_payload() -> dict[str, object]:
    return {
        "name": "fixed_variable",
        "sense": "maximize",
        "variables": [
            {"name": "x", "lower": 2.0, "upper": 2.0},
            {"name": "y", "lower": 0.0, "upper": None},
        ],
        "objective": {"coefficients": {"x": 3.0, "y": 2.0}},
        "constraints": [
            {
                "name": "capacity",
                "coefficients": {"x": 1.0, "y": 1.0},
                "sense": "<=",
                "rhs": 5.0,
            }
        ],
    }


def _write_model(tmp_path: Path, payload: dict[str, object]) -> Path:
    model_path = tmp_path / "model.json"
    model_path.write_text(json.dumps(payload), encoding="utf-8")
    return model_path


def _json_stdout(capsys) -> dict[str, object]:
    captured = capsys.readouterr()
    assert captured.err == ""
    return json.loads(captured.out)
