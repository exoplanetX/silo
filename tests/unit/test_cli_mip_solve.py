import json
from pathlib import Path

import pytest

from silo.cli.main import main

MIP_EXAMPLE_ROOT = Path("examples/mip")
LP_EXAMPLE_ROOT = Path("examples/json")
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


def test_cli_mip_solve_binary_knapsack_default_backend(capsys) -> None:
    exit_code = main(["mip-solve", str(MIP_EXAMPLE_ROOT / "binary_knapsack.json")])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert set(payload) == REQUIRED_SOLUTION_FIELDS
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(22.0)
    assert payload["primal_values"]["item_2"] == pytest.approx(1.0)
    assert payload["primal_values"]["item_3"] == pytest.approx(1.0)


def test_cli_mip_solve_integer_allocation(capsys) -> None:
    exit_code = main(["mip-solve", str(MIP_EXAMPLE_ROOT / "integer_allocation.json")])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(7.0)


def test_cli_mip_solve_mixed_binary_integer(capsys) -> None:
    exit_code = main(["mip-solve", str(MIP_EXAMPLE_ROOT / "mixed_binary_integer.json")])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(11.0)


def test_cli_mip_solve_mixed_continuous_integer(capsys) -> None:
    exit_code = main(
        ["mip-solve", str(MIP_EXAMPLE_ROOT / "mixed_continuous_integer.json")]
    )

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(11.0)


def test_cli_mip_solve_infeasible_binary_returns_nonzero(capsys) -> None:
    exit_code = main(["mip-solve", str(MIP_EXAMPLE_ROOT / "infeasible_binary.json")])

    payload = _json_stdout(capsys)

    assert exit_code == 1
    assert payload["status"] == "infeasible"


def test_cli_mip_solve_accepts_revised_lp_backend(capsys) -> None:
    exit_code = main(
        [
            "mip-solve",
            str(MIP_EXAMPLE_ROOT / "binary_knapsack.json"),
            "--lp-solver",
            "revised",
        ]
    )

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(22.0)


def test_cli_mip_solve_node_limit_zero_returns_iteration_limit(capsys) -> None:
    exit_code = main(
        [
            "mip-solve",
            str(MIP_EXAMPLE_ROOT / "binary_knapsack.json"),
            "--node-limit",
            "0",
        ]
    )

    payload = _json_stdout(capsys)

    assert exit_code == 1
    assert payload["status"] == "iteration_limit"


def test_cli_mip_solve_writes_solution_json_to_output_file(tmp_path, capsys) -> None:
    output_path = tmp_path / "nested" / "mip_solution.json"

    exit_code = main(
        [
            "mip-solve",
            str(MIP_EXAMPLE_ROOT / "binary_knapsack.json"),
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
    assert payload["objective_value"] == pytest.approx(22.0)


def test_cli_mip_solve_missing_model_path_returns_error(capsys) -> None:
    exit_code = main(["mip-solve", "missing-model.json"])

    captured = capsys.readouterr()

    assert exit_code == 1
    assert captured.out == ""
    assert "Error: model file not found:" in captured.err


def test_cli_mip_solve_rejects_invalid_lp_solver(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "mip-solve",
                str(MIP_EXAMPLE_ROOT / "binary_knapsack.json"),
                "--lp-solver",
                "invalid",
            ]
        )

    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    assert captured.out == ""
    assert "invalid choice" in captured.err


def test_cli_mip_solve_rejects_negative_node_limit(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "mip-solve",
                str(MIP_EXAMPLE_ROOT / "binary_knapsack.json"),
                "--node-limit",
                "-1",
            ]
        )

    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    assert captured.out == ""
    assert "must be a nonnegative integer" in captured.err


def test_cli_mip_solve_rejects_solver_flag(capsys) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "mip-solve",
                str(MIP_EXAMPLE_ROOT / "binary_knapsack.json"),
                "--solver",
                "revised",
            ]
        )

    captured = capsys.readouterr()

    assert exc_info.value.code == 2
    assert captured.out == ""
    assert "--lp-solver" in captured.err


def test_cli_solve_lp_behavior_remains_unchanged(capsys) -> None:
    exit_code = main(["solve", str(LP_EXAMPLE_ROOT / "production.json")])

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(21.0)


def test_cli_solve_mip_example_does_not_route_to_mip(capsys) -> None:
    exit_code = main(["solve", str(MIP_EXAMPLE_ROOT / "binary_knapsack.json")])

    payload = _json_stdout(capsys)

    assert exit_code == 1
    assert payload["status"] != "optimal"
    assert payload["objective_value"] != pytest.approx(22.0)


def _json_stdout(capsys) -> dict[str, object]:
    captured = capsys.readouterr()
    assert captured.err == ""
    return json.loads(captured.out)
