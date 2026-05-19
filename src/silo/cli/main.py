import argparse
import sys
from pathlib import Path

from silo import __version__
from silo.core.status import SolverStatus
from silo.io.json_reader import read_json_model
from silo.io.solution_writer import solution_to_json, write_solution_json
from silo.lp.simplex.tableau import TableauSimplexSolver


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
        choices=["help", "solve"],
        help="Command to run.",
    )
    parser.add_argument("path", nargs="?", help="Path to model file.")
    parser.add_argument(
        "-o",
        "--output",
        help="Optional path to write solution JSON.",
    )
    parser.add_argument(
        "--solver",
        default="tableau",
        choices=["tableau"],
        help="Solver backend to use.",
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
        return _solve(args.path, args.output)

    parser.print_help()
    return 0


def _solve(model_path: str, output_path: str | None) -> int:
    path = Path(model_path)
    if not path.exists():
        print(f"Error: model file not found: {path}", file=sys.stderr)
        return 1

    try:
        model = read_json_model(path)
    except ValueError as exc:
        print(f"Error: failed to read model: {exc}", file=sys.stderr)
        return 1

    solution = TableauSimplexSolver().solve(model)
    try:
        if output_path:
            write_solution_json(solution, output_path)
        else:
            print(solution_to_json(solution), end="")
    except OSError as exc:
        print(f"Error: failed to write solution: {exc}", file=sys.stderr)
        return 1

    return 0 if solution.status == SolverStatus.OPTIMAL else 1


if __name__ == "__main__":
    raise SystemExit(main())
