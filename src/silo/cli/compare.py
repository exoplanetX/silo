import json
from pathlib import Path
from typing import Any

from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.io.json_reader import read_json_model
from silo.io.solution_writer import solution_to_dict
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.lp.simplex.tableau import TableauSimplexSolver
from silo.utils.numerics import DEFAULT_TOLERANCE


def compare_backends(model_path: str | Path) -> dict[str, Any]:
    path = Path(model_path)
    model = read_json_model(path)
    tableau_solution = TableauSimplexSolver().solve(model)
    revised_solution = RevisedSimplexSolver().solve(model)

    checks = _comparison_checks(tableau_solution, revised_solution)
    consistent = _is_consistent(tableau_solution, revised_solution, checks)

    return {
        "model_path": path.as_posix(),
        "consistent": consistent,
        "tolerance": DEFAULT_TOLERANCE,
        "checks": checks,
        "tableau": solution_to_dict(tableau_solution),
        "revised": solution_to_dict(revised_solution),
    }


def comparison_to_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_comparison_json(payload: dict[str, Any], path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(comparison_to_json(payload), encoding="utf-8")


def max_abs_diff(left: dict[str, float], right: dict[str, float]) -> float:
    keys = set(left) | set(right)
    if not keys:
        return 0.0
    if set(left) != set(right):
        return float("inf")
    return max(abs(left[key] - right[key]) for key in keys)


def _comparison_checks(left: Solution, right: Solution) -> dict[str, Any]:
    return {
        "status_match": left.status == right.status,
        "objective_match": _objective_match(left, right),
        "primal_max_abs_diff": max_abs_diff(left.primal_values, right.primal_values),
        "slack_max_abs_diff": max_abs_diff(left.slack_values, right.slack_values),
        "reduced_cost_max_abs_diff": max_abs_diff(left.reduced_costs, right.reduced_costs),
        "basis_status_match": left.basis_status == right.basis_status,
        "dual_values_empty": left.dual_values == {} and right.dual_values == {},
    }


def _objective_match(left: Solution, right: Solution) -> bool:
    if left.objective_value is None or right.objective_value is None:
        return left.objective_value is None and right.objective_value is None
    return abs(left.objective_value - right.objective_value) <= DEFAULT_TOLERANCE


def _is_consistent(
    left: Solution,
    right: Solution,
    checks: dict[str, Any],
) -> bool:
    if not checks["status_match"] or not checks["dual_values_empty"]:
        return False
    if left.status == right.status == SolverStatus.OPTIMAL:
        return bool(checks["objective_match"])
    return True
