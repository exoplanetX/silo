import json
import sys
from pathlib import Path
from typing import Any

from silo.cli.solvers import create_solver
from silo.core.status import SolverStatus
from silo.io.json_reader import read_json_model
from silo.io.solution_writer import solution_to_dict, solution_to_json, write_solution_json
from silo.mip.branch_and_bound import BranchAndBoundResult, BranchAndBoundSolver


def mip_solve(
    model_path: str,
    output_path: str | None,
    lp_solver_name: str,
    node_limit: int,
    details: bool = False,
    node_log: bool = False,
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
    result = solver.solve_with_details(model)
    solution = result.solution

    try:
        if output_path:
            if details:
                _write_details_json(
                    result,
                    output_path,
                    lp_solver_name,
                    node_limit,
                    include_node_log=node_log,
                )
            else:
                write_solution_json(solution, output_path)
        else:
            if details:
                print(
                    details_to_json(
                        result,
                        lp_solver_name,
                        node_limit,
                        include_node_log=node_log,
                    ),
                    end="",
                )
            else:
                print(solution_to_json(solution), end="")
    except OSError as exc:
        print(f"Error: failed to write solution: {exc}", file=sys.stderr)
        return 1

    return 0 if solution.status == SolverStatus.OPTIMAL else 1


def details_to_dict(
    result: BranchAndBoundResult,
    lp_solver_name: str,
    node_limit: int,
    include_node_log: bool = False,
) -> dict[str, Any]:
    return {
        "solution": solution_to_dict(result.solution),
        "diagnostics": _diagnostics_to_dict(
            result,
            lp_solver_name,
            node_limit,
            include_node_log=include_node_log,
        ),
    }


def details_to_json(
    result: BranchAndBoundResult,
    lp_solver_name: str,
    node_limit: int,
    include_node_log: bool = False,
) -> str:
    return json.dumps(
        details_to_dict(
            result,
            lp_solver_name,
            node_limit,
            include_node_log=include_node_log,
        ),
        indent=2,
        sort_keys=True,
    ) + "\n"


def _diagnostics_to_dict(
    result: BranchAndBoundResult,
    lp_solver_name: str,
    node_limit: int,
    include_node_log: bool = False,
) -> dict[str, Any]:
    diagnostics: dict[str, Any] = {
        "node_count": result.nodes_processed,
        "nodes_processed": result.nodes_processed,
        "nodes_created": result.nodes_created,
        "nodes_pruned": result.nodes_pruned,
        "incumbent_value": result.incumbent_value,
        "best_bound": result.best_bound,
        "relative_gap": _relative_gap(result.best_bound, result.incumbent_value),
        "termination_reason": _termination_reason(result.solution.status),
        "node_limit": node_limit,
        "lp_solver": lp_solver_name,
    }
    if include_node_log:
        diagnostics["node_log"] = [_node_log_entry_to_dict(entry) for entry in result.log]
    return diagnostics


def _node_log_entry_to_dict(entry: Any) -> dict[str, Any]:
    return {
        "node_id": entry.node_id,
        "depth": entry.depth,
        "lp_status": entry.lp_status.value,
        "lp_objective": entry.lp_objective,
        "prune_reason": entry.prune_reason.value,
        "branching_variable": entry.branching_variable,
        "incumbent_value": entry.incumbent_value,
        "message": entry.message,
    }


def _relative_gap(best_bound: float | None, incumbent_value: float | None) -> float | None:
    if best_bound is None or incumbent_value is None:
        return None
    return abs(best_bound - incumbent_value) / max(1.0, abs(incumbent_value))


def _termination_reason(status: SolverStatus) -> str:
    if status == SolverStatus.OPTIMAL:
        return "optimality_proven"
    if status == SolverStatus.INFEASIBLE:
        return "infeasible"
    if status == SolverStatus.UNBOUNDED:
        return "unbounded"
    if status == SolverStatus.ITERATION_LIMIT:
        return "node_limit"
    if status == SolverStatus.NUMERICAL_ISSUE:
        return "numerical_issue"
    return "error"


def _write_details_json(
    result: BranchAndBoundResult,
    path: str | Path,
    lp_solver_name: str,
    node_limit: int,
    include_node_log: bool = False,
) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        details_to_json(
            result,
            lp_solver_name,
            node_limit,
            include_node_log=include_node_log,
        ),
        encoding="utf-8",
    )
