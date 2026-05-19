import json
from pathlib import Path

from silo.core.solution import Solution


def write_solution_json(solution: Solution, path: str | Path) -> None:
    payload = {
        "status": solution.status.value,
        "objective_value": solution.objective_value,
        "primal_values": solution.primal_values,
        "dual_values": solution.dual_values,
        "reduced_costs": solution.reduced_costs,
        "message": solution.message,
    }
    Path(path).write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
