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
REQUIRED_DETAILS_FIELDS = {
    "node_count",
    "nodes_processed",
    "nodes_created",
    "nodes_pruned",
    "incumbent_value",
    "best_bound",
    "relative_gap",
    "termination_reason",
    "node_limit",
    "lp_solver",
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


def test_cli_mip_solve_details_wraps_solution_and_diagnostics(capsys) -> None:
    exit_code = main(
        ["mip-solve", str(MIP_EXAMPLE_ROOT / "binary_knapsack.json"), "--details"]
    )

    payload = _json_stdout(capsys)
    solution = payload["solution"]
    diagnostics = payload["diagnostics"]

    assert exit_code == 0
    assert set(payload) == {"solution", "diagnostics"}
    assert set(solution) == REQUIRED_SOLUTION_FIELDS
    assert set(diagnostics) == REQUIRED_DETAILS_FIELDS
    assert solution["status"] == "optimal"
    assert solution["objective_value"] == pytest.approx(22.0)
    assert diagnostics["node_count"] == diagnostics["nodes_processed"]
    assert diagnostics["node_count"] > 0
    assert diagnostics["nodes_created"] >= diagnostics["nodes_processed"]
    assert diagnostics["incumbent_value"] == pytest.approx(22.0)
    assert diagnostics["best_bound"] == pytest.approx(22.0)
    assert diagnostics["relative_gap"] == pytest.approx(0.0)
    assert diagnostics["termination_reason"] == "optimality_proven"
    assert diagnostics["node_limit"] == 10_000
    assert diagnostics["lp_solver"] == "tableau"
    assert "node_log" not in diagnostics


def test_cli_mip_solve_details_reports_revised_lp_backend(capsys) -> None:
    exit_code = main(
        [
            "mip-solve",
            str(MIP_EXAMPLE_ROOT / "binary_knapsack.json"),
            "--lp-solver",
            "revised",
            "--details",
        ]
    )

    payload = _json_stdout(capsys)

    assert exit_code == 0
    assert payload["diagnostics"]["lp_solver"] == "revised"
    assert payload["diagnostics"]["termination_reason"] == "optimality_proven"


def test_cli_mip_solve_details_infeasible_returns_nonzero(capsys) -> None:
    exit_code = main(
        ["mip-solve", str(MIP_EXAMPLE_ROOT / "infeasible_binary.json"), "--details"]
    )

    payload = _json_stdout(capsys)
    solution = payload["solution"]
    diagnostics = payload["diagnostics"]

    assert exit_code == 1
    assert solution["status"] == "infeasible"
    assert solution["objective_value"] is None
    assert diagnostics["termination_reason"] == "infeasible"
    assert diagnostics["incumbent_value"] is None
    assert diagnostics["relative_gap"] is None


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


def test_cli_mip_solve_details_node_limit_zero_reports_node_limit(capsys) -> None:
    exit_code = main(
        [
            "mip-solve",
            str(MIP_EXAMPLE_ROOT / "binary_knapsack.json"),
            "--node-limit",
            "0",
            "--details",
        ]
    )

    payload = _json_stdout(capsys)
    solution = payload["solution"]
    diagnostics = payload["diagnostics"]

    assert exit_code == 1
    assert solution["status"] == "iteration_limit"
    assert diagnostics["termination_reason"] == "node_limit"
    assert diagnostics["node_limit"] == 0
    assert diagnostics["node_count"] == 0
    assert diagnostics["nodes_processed"] == 0
    assert diagnostics["nodes_created"] == 1


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


def test_cli_mip_solve_details_writes_wrapper_to_output_file(tmp_path, capsys) -> None:
    output_path = tmp_path / "nested" / "mip_details.json"

    exit_code = main(
        [
            "mip-solve",
            str(MIP_EXAMPLE_ROOT / "binary_knapsack.json"),
            "--details",
            "--output",
            str(output_path),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(output_path.read_text(encoding="utf-8"))

    assert exit_code == 0
    assert captured.out == ""
    assert captured.err == ""
    assert set(payload) == {"solution", "diagnostics"}
    assert payload["solution"]["status"] == "optimal"
    assert payload["diagnostics"]["termination_reason"] == "optimality_proven"


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
