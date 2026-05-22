import sys
from pathlib import Path

from silo.cli.solvers import create_solver
from silo.core.status import SolverStatus
from silo.io.json_reader import read_json_model
from silo.io.solution_writer import solution_to_json, write_solution_json
from silo.mip.branch_and_bound import BranchAndBoundSolver


def mip_solve(
    model_path: str,
    output_path: str | None,
    lp_solver_name: str,
    node_limit: int,
) -> int:
    path = Path(model_path)
    if not path.exists():
        print(f"Error: model file not found: {path}", file=sys.stderr)
        return 1

    try:
        model = read_json_model(path)
    except ValueError as exc:
        print(f"Error: failed to read model: {exc}", file=sys.stderr)
        return 1

    solver = BranchAndBoundSolver(
        lp_solver=create_solver(lp_solver_name),
        node_limit=node_limit,
    )
    solution = solver.solve(model)

    try:
        if output_path:
            write_solution_json(solution, output_path)
        else:
            print(solution_to_json(solution), end="")
    except OSError as exc:
        print(f"Error: failed to write solution: {exc}", file=sys.stderr)
        return 1

    return 0 if solution.status == SolverStatus.OPTIMAL else 1
