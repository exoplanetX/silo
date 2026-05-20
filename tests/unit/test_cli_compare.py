import json
from pathlib import Path

import pytest

from silo.cli.compare import compare_backends, max_abs_diff
from silo.cli.main import main

EXAMPLE_ROOT = Path("examples/json")
REQUIRED_TOP_LEVEL_FIELDS = {
    "model_path",
    "consistent",
    "tolerance",
    "checks",
    "tableau",
    "revised",
}
REQUIRED_CHECK_FIELDS = {
    "status_match",
    "objective_match",
    "primal_max_abs_diff",
    "slack_max_abs_diff",
    "reduced_cost_max_abs_diff",
    "basis_status_match",
    "dual_values_empty",
}
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


def test_compare_backends_reports_production_consistency() -> None:
    payload = compare_backends(EXAMPLE_ROOT / "production.json")

    _assert_compare_payload_schema(payload)
    assert payload["consistent"] is True
    assert payload["checks"]["status_match"] is True
    assert payload["checks"]["objective_match"] is True
    assert payload["tableau"]["status"] == "optimal"
    assert payload["revised"]["status"] == "optimal"
    assert payload["tableau"]["objective_value"] == pytest.approx(21.0)
    assert payload["revised"]["objective_value"] == pytest.approx(21.0)


def test_cli_compare_ge_example(capsys) -> None:
    exit_code = main(["compare", str(EXAMPLE_ROOT / "ge_row.json")])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["consistent"] is True
    assert payload["checks"]["status_match"] is True
    assert payload["checks"]["objective_match"] is True
    assert payload["tableau"]["status"] == "optimal"
    assert payload["revised"]["status"] == "optimal"


def test_cli_compare_equality_example_allows_degenerate_primal_differences(capsys) -> None:
    exit_code = main(["compare", str(EXAMPLE_ROOT / "equality_row.json")])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["consistent"] is True
    assert payload["checks"]["status_match"] is True
    assert payload["checks"]["objective_match"] is True
    assert payload["tableau"]["status"] == "optimal"
    assert payload["revised"]["status"] == "optimal"


def test_cli_compare_infeasible_example_is_consistent(capsys) -> None:
    exit_code = main(["compare", str(EXAMPLE_ROOT / "infeasible.json")])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["consistent"] is True
    assert payload["checks"]["status_match"] is True
    assert payload["tableau"]["status"] == "infeasible"
    assert payload["revised"]["status"] == "infeasible"


def test_cli_compare_writes_output_file(tmp_path, capsys) -> None:
    output_path = tmp_path / "nested" / "compare.json"

    exit_code = main(
        ["compare", str(EXAMPLE_ROOT / "production.json"), "--output", str(output_path)]
    )

    captured = capsys.readouterr()
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert output_path.exists()
    _assert_compare_payload_schema(payload)


def test_cli_compare_missing_model_path_returns_error(capsys) -> None:
    exit_code = main(["compare", "missing-model.json"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Error: model file not found:" in captured.err


def test_cli_compare_solution_payloads_use_solve_schema(capsys) -> None:
    exit_code = main(["compare", str(EXAMPLE_ROOT / "production.json")])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert set(payload["tableau"]) == REQUIRED_SOLUTION_FIELDS
    assert set(payload["revised"]) == REQUIRED_SOLUTION_FIELDS


def test_max_abs_diff_reports_infinity_for_mismatched_keys() -> None:
    assert max_abs_diff({"x": 1.0}, {"y": 1.0}) == float("inf")


def _assert_compare_payload_schema(payload: dict[str, object]) -> None:
    assert set(payload) == REQUIRED_TOP_LEVEL_FIELDS
    assert set(payload["checks"]) == REQUIRED_CHECK_FIELDS
    assert set(payload["tableau"]) == REQUIRED_SOLUTION_FIELDS
    assert set(payload["revised"]) == REQUIRED_SOLUTION_FIELDS


def _json_stdout(capsys) -> dict[str, object]:
    captured = capsys.readouterr()
    assert captured.err == ""
    return json.loads(captured.out)
