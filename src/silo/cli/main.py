import argparse

from silo import __version__


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
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "help":
        parser.print_help()
        return 0

    if args.command == "solve":
        if not args.path:
            parser.error("The solve command requires a model file path.")
        print("SILO solve command is not implemented yet.")
        print(f"Requested model file: {args.path}")
        return 0

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
