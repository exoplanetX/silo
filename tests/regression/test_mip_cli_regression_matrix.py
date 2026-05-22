import json
import os
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
MIP_EXAMPLE_ROOT = Path("examples/mip")
LP_EXAMPLE_ROOT = Path("examples/json")

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
COMPARE_FIELDS = {"model_path", "consistent", "tolerance", "checks", "tableau", "revised"}
DETAILS_FIELDS = {
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
NODE_LOG_FIELDS = {
    "node_id",
    "depth",
    "lp_status",
    "lp_objective",
    "prune_reason",
    "branching_variable",
    "incumbent_value",
    "message",
}

ENTRYPOINTS = [
    pytest.param((sys.executable, "-m", "silo.cli.main"), id="python-module"),
    pytest.param(("silo",), id="console-script"),
]

MIP_OPTIMAL_CASES = [
    pytest.param("binary_knapsack.json", 22.0, id="binary-knapsack"),
    pytest.param("integer_allocation.json", 7.0, id="integer-allocation"),
    pytest.param("mixed_binary_integer.json", 11.0, id="mixed-binary-integer"),
    pytest.param("mixed_continuous_integer.json", 11.0, id="mixed-continuous-integer"),
]


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS)
@pytest.mark.parametrize(("example_name", "expected_objective"), MIP_OPTIMAL_CASES)
def test_mip_solve_example_matrix(
    entrypoint: tuple[str, ...], example_name: str, expected_objective: float
) -> None:
    result = _run_cli(entrypoint, "mip-solve", MIP_EXAMPLE_ROOT / example_name)

    payload = _json_payload(result)

    assert result.returncode == 0
    assert set(payload) == SOLUTION_FIELDS
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(expected_objective)


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS)
def test_mip_solve_revised_backend_for_knapsack(entrypoint: tuple[str, ...]) -> None:
    result = _run_cli(
        entrypoint,
        "mip-solve",
        MIP_EXAMPLE_ROOT / "binary_knapsack.json",
        "--lp-solver",
        "revised",
    )

    payload = _json_payload(result)

    assert result.returncode == 0
    assert set(payload) == SOLUTION_FIELDS
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(22.0)


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS)
def test_mip_solve_details_summary_for_knapsack(entrypoint: tuple[str, ...]) -> None:
    result = _run_cli(
        entrypoint,
        "mip-solve",
        MIP_EXAMPLE_ROOT / "binary_knapsack.json",
        "--details",
    )

    payload = _json_payload(result)
    solution = payload["solution"]
    diagnostics = payload["diagnostics"]

    assert result.returncode == 0
    assert set(payload) == {"solution", "diagnostics"}
    assert set(solution) == SOLUTION_FIELDS
    assert set(diagnostics) == DETAILS_FIELDS
    assert solution["status"] == "optimal"
    assert solution["objective_value"] == pytest.approx(22.0)
    assert diagnostics["node_count"] == diagnostics["nodes_processed"]
    assert diagnostics["termination_reason"] == "optimality_proven"
    assert diagnostics["relative_gap"] == pytest.approx(0.0)
    assert diagnostics["node_limit"] == 10_000
    assert diagnostics["lp_solver"] == "tableau"
    assert "node_log" not in diagnostics


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS)
def test_mip_solve_details_node_log_for_knapsack(entrypoint: tuple[str, ...]) -> None:
    result = _run_cli(
        entrypoint,
        "mip-solve",
        MIP_EXAMPLE_ROOT / "binary_knapsack.json",
        "--details",
        "--node-log",
    )

    payload = _json_payload(result)
    diagnostics = payload["diagnostics"]
    node_log = diagnostics["node_log"]

    assert result.returncode == 0
    assert set(payload) == {"solution", "diagnostics"}
    assert set(payload["solution"]) == SOLUTION_FIELDS
    assert set(diagnostics) == DETAILS_FIELDS | {"node_log"}
    assert diagnostics["termination_reason"] == "optimality_proven"
    assert node_log
    assert set(node_log[0]) == NODE_LOG_FIELDS
    assert isinstance(node_log[0]["lp_status"], str)
    assert isinstance(node_log[0]["prune_reason"], str)
    assert "primal_values" not in node_log[0]
    assert "basis_status" not in node_log[0]


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS)
def test_mip_solve_node_log_requires_details(entrypoint: tuple[str, ...]) -> None:
    result = _run_cli(
        entrypoint,
        "mip-solve",
        MIP_EXAMPLE_ROOT / "binary_knapsack.json",
        "--node-log",
    )

    assert result.returncode == 2
    assert result.stdout == ""
    assert "--node-log" in result.stderr
    assert "--details" in result.stderr


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS)
def test_mip_solve_infeasible_example_returns_nonzero(entrypoint: tuple[str, ...]) -> None:
    result = _run_cli(entrypoint, "mip-solve", MIP_EXAMPLE_ROOT / "infeasible_binary.json")

    payload = _json_payload(result)

    assert result.returncode == 1
    assert set(payload) == SOLUTION_FIELDS
    assert payload["status"] == "infeasible"
    assert payload["objective_value"] is None


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS)
def test_mip_solve_details_infeasible_example_returns_nonzero(
    entrypoint: tuple[str, ...],
) -> None:
    result = _run_cli(
        entrypoint,
        "mip-solve",
        MIP_EXAMPLE_ROOT / "infeasible_binary.json",
        "--details",
    )

    payload = _json_payload(result)

    assert result.returncode == 1
    assert payload["solution"]["status"] == "infeasible"
    assert payload["diagnostics"]["termination_reason"] == "infeasible"
    assert payload["diagnostics"]["relative_gap"] is None


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS)
def test_solve_mip_example_remains_lp_only(entrypoint: tuple[str, ...]) -> None:
    result = _run_cli(entrypoint, "solve", MIP_EXAMPLE_ROOT / "binary_knapsack.json")

    payload = _json_payload(result)

    assert result.returncode == 1
    assert set(payload) == SOLUTION_FIELDS
    assert payload["status"] == "error"
    assert payload["objective_value"] is None


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS)
def test_lp_solve_production_remains_unchanged(entrypoint: tuple[str, ...]) -> None:
    result = _run_cli(entrypoint, "solve", LP_EXAMPLE_ROOT / "production.json")

    payload = _json_payload(result)

    assert result.returncode == 0
    assert set(payload) == SOLUTION_FIELDS
    assert payload["status"] == "optimal"
    assert payload["objective_value"] == pytest.approx(21.0)


@pytest.mark.parametrize("entrypoint", ENTRYPOINTS)
def test_lp_compare_production_remains_unchanged(entrypoint: tuple[str, ...]) -> None:
    result = _run_cli(entrypoint, "compare", LP_EXAMPLE_ROOT / "production.json")

    payload = _json_payload(result)

    assert result.returncode == 0
    assert set(payload) == COMPARE_FIELDS
    assert payload["consistent"] is True
    assert payload["tableau"]["status"] == "optimal"
    assert payload["tableau"]["objective_value"] == pytest.approx(21.0)
    assert payload["revised"]["status"] == "optimal"
    assert payload["revised"]["objective_value"] == pytest.approx(21.0)


def _run_cli(
    entrypoint: Sequence[str],
    command: str,
    model_path: Path,
    *args: str,
) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    src_path = str(REPO_ROOT / "src")
    env["PYTHONPATH"] = (
        src_path if not env.get("PYTHONPATH") else os.pathsep.join([src_path, env["PYTHONPATH"]])
    )
    return subprocess.run(
        [*entrypoint, command, str(model_path), *args],
        cwd=REPO_ROOT,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def _json_payload(result: subprocess.CompletedProcess[str]) -> dict[str, object]:
    assert result.stderr == ""
    return json.loads(result.stdout)
