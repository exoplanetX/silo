from silo.cli.main import build_parser


def test_cli_parser_version_exists() -> None:
    parser = build_parser()
    assert parser.prog == "silo"


def test_cli_default_command_is_help() -> None:
    parser = build_parser()
    args = parser.parse_args([])
    assert args.command == "help"
