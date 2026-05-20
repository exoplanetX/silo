from silo.cli.main import build_parser


def test_cli_parser_version_exists() -> None:
    parser = build_parser()
    assert parser.prog == "silo"


def test_cli_default_command_is_help() -> None:
    parser = build_parser()
    args = parser.parse_args([])
    assert args.command == "help"


def test_cli_accepts_compare_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["compare", "model.json"])
    assert args.command == "compare"


def test_cli_default_solver_is_tableau() -> None:
    parser = build_parser()
    args = parser.parse_args(["solve", "model.json"])
    assert args.solver == "tableau"


def test_cli_accepts_revised_solver_option() -> None:
    parser = build_parser()
    args = parser.parse_args(["solve", "model.json", "--solver", "revised"])
    assert args.solver == "revised"
