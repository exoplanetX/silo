import argparse
import sys
from pathlib import Path

from silo import __version__
from silo.cli.compare import compare_backends, comparison_to_json, write_comparison_json
from silo.cli.mip_solve import mip_solve
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
        choices=["compare", "help", "mip-solve", "presolve", "solve"],
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
        "--lp-solver",
        choices=available_solver_names(),
        help="LP relaxation backend to use. Used only by the mip-solve command.",
    )
    parser.add_argument(
        "--node-limit",
        type=_nonnegative_int,
        default=10_000,
        help="Branch-and-bound node limit. Used only by the mip-solve command.",
    )
    parser.add_argument(
        "--details",
        action="store_true",
        help="Emit MIP summary diagnostics. Used only by the mip-solve command.",
    )
    parser.add_argument(
        "--node-log",
        action="store_true",
        help="Include MIP node-log diagnostics. Requires --details.",
    )
    parser.add_argument(
        "--presolve",
        action="store_true",
        help="Run presolve before solving. Used only by the solve command.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    raw_args = sys.argv[1:] if argv is None else argv
    args = parser.parse_args(raw_args)

    if args.command == "help":
        parser.print_help()
        return 0

    if args.node_log and args.command != "mip-solve":
        parser.error("The --node-log option is only supported by mip-solve --details.")

    if args.command == "solve":
        if not args.path:
            parser.error("The solve command requires a model file path.")
        return _solve(args.path, args.output, args.solver, args.presolve)

    if args.command == "mip-solve":
        if _option_used(raw_args, "--solver"):
            parser.error(
                "The mip-solve command uses --lp-solver; --solver is reserved for "
                "the LP solve command."
            )
        if args.node_log and not args.details:
            parser.error("The mip-solve --node-log option requires --details.")
        if args.presolve:
            parser.error("The mip-solve command does not support --presolve.")
        if not args.path:
            parser.error("The mip-solve command requires a model file path.")
        lp_solver_name = args.lp_solver if args.lp_solver is not None else "tableau"
        return mip_solve(
            args.path,
            args.output,
            lp_solver_name,
            args.node_limit,
            details=args.details,
            node_log=args.node_log,
        )

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


def _nonnegative_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("must be a nonnegative integer") from exc
    if parsed < 0:
        raise argparse.ArgumentTypeError("must be a nonnegative integer")
    return parsed


def _option_used(argv: list[str], option: str) -> bool:
    return any(arg == option or arg.startswith(f"{option}=") for arg in argv)


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
