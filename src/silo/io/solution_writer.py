import json
from pathlib import Path
from typing import Any

from silo.core.solution import Solution


def solution_to_dict(solution: Solution) -> dict[str, Any]:
    return {
        "status": solution.status.value,
        "objective_value": solution.objective_value,
        "primal_values": solution.primal_values,
        "slack_values": solution.slack_values,
        "dual_values": solution.dual_values,
        "reduced_costs": solution.reduced_costs,
        "basis_status": solution.basis_status,
        "message": solution.message,
    }


def solution_to_json(solution: Solution) -> str:
    return json.dumps(solution_to_dict(solution), indent=2, sort_keys=True) + "\n"


def write_solution_json(solution: Solution, path: str | Path) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(solution_to_json(solution), encoding="utf-8")
