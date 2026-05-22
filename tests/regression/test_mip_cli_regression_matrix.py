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
def test_mip_solve_infeasible_example_returns_nonzero(entrypoint: tuple[str, ...]) -> None:
    result = _run_cli(entrypoint, "mip-solve", MIP_EXAMPLE_ROOT / "infeasible_binary.json")

    payload = _json_payload(result)

    assert result.returncode == 1
    assert set(payload) == SOLUTION_FIELDS
    assert payload["status"] == "infeasible"
    assert payload["objective_value"] is None


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
