import json
from pathlib import Path

from silo.cli.main import main

EXAMPLE_ROOT = Path("examples/json")
EXAMPLE_PRODUCTION_MODEL = EXAMPLE_ROOT / "production.json"
REQUIRED_TOP_LEVEL_FIELDS = {"model_path", "presolve", "reductions", "scaling"}
REQUIRED_PRESOLVE_FIELDS = {
    "status",
    "changed",
    "message",
    "removed_rows",
    "removed_variables",
    "fixed_variables",
    "warnings",
    "notes",
}
REQUIRED_SCALING_FIELDS = {
    "max_abs_coefficient",
    "min_abs_nonzero_coefficient",
    "coefficient_ratio",
    "max_abs_rhs",
    "max_abs_objective",
    "warnings",
}


def test_cli_presolve_prints_diagnostics_json(capsys) -> None:
    exit_code = main(["presolve", str(EXAMPLE_PRODUCTION_MODEL)])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    _assert_presolve_payload_schema(payload)
    assert payload["presolve"]["status"] == "no_change"
    assert payload["scaling"]["max_abs_coefficient"] > 0


def test_cli_presolve_writes_output_file(tmp_path, capsys) -> None:
    output_path = tmp_path / "nested" / "presolve.json"

    exit_code = main(
        [
            "presolve",
            str(EXAMPLE_PRODUCTION_MODEL),
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
    _assert_presolve_payload_schema(payload)


def test_cli_presolve_infeasible_empty_row_returns_success(tmp_path, capsys) -> None:
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

    exit_code = main(["presolve", str(model_path)])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["presolve"]["status"] == "infeasible"
    assert [warning["code"] for warning in payload["presolve"]["warnings"]] == [
        "empty_row_infeasible"
    ]


def test_cli_presolve_unbounded_empty_column_returns_success(tmp_path, capsys) -> None:
    model_path = _write_model(
        tmp_path,
        {
            "name": "empty_column_unbounded",
            "sense": "maximize",
            "variables": [{"name": "x", "lower": 0.0, "upper": None}],
            "objective": {"coefficients": {"x": 1.0}},
        },
    )

    exit_code = main(["presolve", str(model_path)])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["presolve"]["status"] == "unbounded"
    assert [warning["code"] for warning in payload["presolve"]["warnings"]] == [
        "empty_column_unbounded"
    ]


def test_cli_presolve_fixed_variable_reduction(tmp_path, capsys) -> None:
    model_path = _write_model(
        tmp_path,
        {
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
        },
    )

    exit_code = main(["presolve", str(model_path)])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["presolve"]["status"] == "reduced"
    assert payload["presolve"]["fixed_variables"] == ["x"]
    assert [reduction["type"] for reduction in payload["reductions"]] == [
        "fixed_variable"
    ]


def test_cli_presolve_scaling_warning_does_not_change_status(tmp_path, capsys) -> None:
    model_path = _write_model(
        tmp_path,
        {
            "name": "large_range",
            "sense": "maximize",
            "variables": [
                {"name": "x", "lower": 0.0, "upper": None},
                {"name": "y", "lower": 0.0, "upper": None},
            ],
            "objective": {"coefficients": {"x": 0.0, "y": 0.0}},
            "constraints": [
                {
                    "name": "range",
                    "coefficients": {"x": 1.0, "y": 1e9},
                    "sense": "<=",
                    "rhs": 1.0,
                }
            ],
        },
    )

    exit_code = main(["presolve", str(model_path)])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["presolve"]["status"] == "no_change"
    assert payload["presolve"]["warnings"] == []
    assert [warning["code"] for warning in payload["scaling"]["warnings"]] == [
        "large_coefficient_ratio"
    ]


def test_cli_presolve_missing_model_path_returns_error(capsys) -> None:
    exit_code = main(["presolve", "missing-model.json"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Error: model file not found:" in captured.err


def _write_model(tmp_path: Path, payload: dict[str, object]) -> Path:
    model_path = tmp_path / "model.json"
    model_path.write_text(json.dumps(payload), encoding="utf-8")
    return model_path


def _assert_presolve_payload_schema(payload: dict[str, object]) -> None:
    assert set(payload) == REQUIRED_TOP_LEVEL_FIELDS
    assert set(payload["presolve"]) == REQUIRED_PRESOLVE_FIELDS
    assert set(payload["scaling"]) == REQUIRED_SCALING_FIELDS


def _json_stdout(capsys) -> dict[str, object]:
    captured = capsys.readouterr()
    assert captured.err == ""
    return json.loads(captured.out)
