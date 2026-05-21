import pytest

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


def test_cli_accepts_presolve_command() -> None:
    parser = build_parser()
    args = parser.parse_args(["presolve", "model.json"])
    assert args.command == "presolve"


def test_cli_help_mentions_presolve(capsys) -> None:
    parser = build_parser()
    parser.print_help()

    captured = capsys.readouterr()

    assert "presolve" in captured.out
    assert "--presolve" in captured.out


def test_cli_rejects_unknown_command() -> None:
    parser = build_parser()

    with pytest.raises(SystemExit) as exc_info:
        parser.parse_args(["unknown"])

    assert exc_info.value.code == 2


def test_cli_default_solver_is_tableau() -> None:
    parser = build_parser()
    args = parser.parse_args(["solve", "model.json"])
    assert args.solver == "tableau"


def test_cli_accepts_revised_solver_option() -> None:
    parser = build_parser()
    args = parser.parse_args(["solve", "model.json", "--solver", "revised"])
    assert args.solver == "revised"
