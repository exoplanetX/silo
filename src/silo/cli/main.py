import argparse
import sys
from pathlib import Path

from silo import __version__
from silo.cli.compare import compare_backends, comparison_to_json, write_comparison_json
from silo.cli.presolve import presolve_to_dict, presolve_to_json, write_presolve_json
from silo.cli.solvers import available_solver_names, create_solver
from silo.core.model import Model
from silo.core.solution import Solution
from silo.core.status import SolverStatus
from silo.io.json_reader import read_json_model
from silo.io.solution_writer import solution_to_json, write_solution_json
from silo.presolve import Presolver, PresolveStatus


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="silo",
        description="SILO: Simplex and Integer Linear Optimization.",
    )
    parser.add_argument("--version", action="version", version=f"SILO {__version__}")
    parser.add_argument(
        "command",
        nargs="?",
        default="help",
        choices=["compare", "help", "presolve", "solve"],
        help="Command to run.",
    )
    parser.add_argument("path", nargs="?", help="Path to model file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Optional path to write JSON output.",
    )
    parser.add_argument(
        "--solver",
        default="tableau",
        choices=available_solver_names(),
        help="Solver backend to use.",
    )
    parser.add_argument(
        "--presolve",
        action="store_true",
        help="Run presolve before solving. Used only by the solve command.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "help":
        parser.print_help()
        return 0

    if args.command == "solve":
        if not args.path:
            parser.error("The solve command requires a model file path.")
        return _solve(args.path, args.output, args.solver, args.presolve)

    if args.command == "compare":
        if not args.path:
            parser.error("The compare command requires a model file path.")
        return _compare(args.path, args.output)

    if args.command == "presolve":
        if not args.path:
            parser.error("The presolve command requires a model file path.")
        return _presolve(args.path, args.output)

    parser.print_help()
    return 0


def _solve(
    model_path: str,
    output_path: str | None,
    solver_name: str,
    use_presolve: bool = False,
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

    solution = _solve_model(model, solver_name, use_presolve)
    try:
        if output_path:
            write_solution_json(solution, output_path)
        else:
            print(solution_to_json(solution), end="")
    except OSError as exc:
        print(f"Error: failed to write solution: {exc}", file=sys.stderr)
        return 1

    return 0 if solution.status == SolverStatus.OPTIMAL else 1


def _solve_model(model: Model, solver_name: str, use_presolve: bool) -> Solution:
    if not use_presolve:
        return create_solver(solver_name).solve(model)

    presolve_result = Presolver().run(model)
    if presolve_result.diagnostics.status == PresolveStatus.INFEASIBLE:
        return Solution(
            status=SolverStatus.INFEASIBLE,
            message=f"Presolve detected infeasibility: {presolve_result.message}",
        )
    if presolve_result.diagnostics.status == PresolveStatus.UNBOUNDED:
        return Solution(
            status=SolverStatus.UNBOUNDED,
            message=f"Presolve detected unboundedness: {presolve_result.message}",
        )

    solution = create_solver(solver_name).solve(presolve_result.model)
    return presolve_result.recover_solution(solution)


def _compare(model_path: str, output_path: str | None) -> int:
    path = Path(model_path)
    if not path.exists():
        print(f"Error: model file not found: {path}", file=sys.stderr)
        return 1

    try:
        payload = compare_backends(path)
    except ValueError as exc:
        print(f"Error: failed to read model: {exc}", file=sys.stderr)
        return 1

    try:
        if output_path:
            write_comparison_json(payload, output_path)
        else:
            print(comparison_to_json(payload), end="")
    except OSError as exc:
        print(f"Error: failed to write comparison: {exc}", file=sys.stderr)
        return 1

    return 0 if payload["consistent"] else 1


def _presolve(model_path: str, output_path: str | None) -> int:
    path = Path(model_path)
    if not path.exists():
        print(f"Error: model file not found: {path}", file=sys.stderr)
        return 1

    try:
        model = read_json_model(path)
    except ValueError as exc:
        print(f"Error: failed to read model: {exc}", file=sys.stderr)
        return 1

    result = Presolver().run(model)
    payload = presolve_to_dict(path, result)
    try:
        if output_path:
            write_presolve_json(payload, output_path)
        else:
            print(presolve_to_json(payload), end="")
    except OSError as exc:
        print(f"Error: failed to write presolve diagnostics: {exc}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
