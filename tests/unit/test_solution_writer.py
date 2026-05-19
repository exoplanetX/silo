import json

from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.io.solution_writer import write_solution_json


def test_write_solution_json_is_deterministic(tmp_path) -> None:
    path = tmp_path / "solution.json"
    solution = Solution(
        status=SolverStatus.OPTIMAL,
        objective_value=12.5,
        primal_values={"x": 1.0},
        slack_values={"capacity": 0.0},
        dual_values={"row": 0.5},
        reduced_costs={"x": 0.0},
        basis_status={"x": "basic"},
        message="ok",
    )

    write_solution_json(solution, path)

    assert path.read_text(encoding="utf-8") == (
        "{\n"
        '  "basis_status": {\n'
        '    "x": "basic"\n'
        "  },\n"
        '  "dual_values": {\n'
        '    "row": 0.5\n'
        "  },\n"
        '  "message": "ok",\n'
        '  "objective_value": 12.5,\n'
        '  "primal_values": {\n'
        '    "x": 1.0\n'
        "  },\n"
        '  "reduced_costs": {\n'
        '    "x": 0.0\n'
        "  },\n"
        '  "slack_values": {\n'
        '    "capacity": 0.0\n'
        "  },\n"
        '  "status": "optimal"\n'
        "}\n"
    )
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["status"] == "optimal"
    assert payload["slack_values"] == {"capacity": 0.0}
    assert payload["basis_status"] == {"x": "basic"}
