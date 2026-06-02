import importlib
import sys
from pathlib import Path

from silo.cli.main import build_parser
from silo.cli.solvers import available_solver_names

NATIVE_MODULE_PREFIXES = (
    "silo.native",
    "silo.native_backend",
    "silo.backends.native",
    "silo.interfaces.native",
)

DEFAULT_PYTHON_SOLVER_MODULES = (
    "silo.core.model",
    "silo.modeling.canonical_form",
    "silo.presolve.presolver",
    "silo.lp.simplex.tableau",
    "silo.lp.simplex.revised",
    "silo.mip.branch_and_bound",
    "silo.cuts.cut_pool",
    "silo.decomposition",
    "silo.uncertainty.scenario",
    "silo.cli.main",
)

DEFAULT_SOURCE_PACKAGES = (
    "core",
    "modeling",
    "presolve",
    "lp",
    "mip",
    "cuts",
    "decomposition",
    "uncertainty",
    "cli",
    "io",
)

FORBIDDEN_NATIVE_SOURCE_PATTERNS = (
    "silo.native",
    "from silo import native",
    "silo.native_backend",
    "native_backend",
    "NativeBackend",
    "silo.backends.native",
    "from silo.backends import native",
    "silo.interfaces.native",
)


def test_default_python_solver_imports_do_not_load_native_modules() -> None:
    _drop_native_modules()

    for module_name in DEFAULT_PYTHON_SOLVER_MODULES:
        importlib.import_module(module_name)

    assert _loaded_native_modules() == []


def test_default_solver_sources_do_not_import_native_backend_modules() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    for package in DEFAULT_SOURCE_PACKAGES:
        for path in (repo_root / "src" / "silo" / package).rglob("*.py"):
            text = path.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_NATIVE_SOURCE_PATTERNS:
                assert pattern not in text


def test_public_cli_does_not_expose_native_backend_command() -> None:
    parser = build_parser()
    command_action = next(action for action in parser._actions if action.dest == "command")

    assert "native" not in command_action.choices
    assert "native-solve" not in command_action.choices
    assert "backend" not in command_action.choices
    assert "backend-solve" not in command_action.choices


def test_public_lp_solver_choices_remain_python_reference_solvers() -> None:
    parser = build_parser()
    solver_action = next(action for action in parser._actions if action.dest == "solver")
    lp_solver_action = next(action for action in parser._actions if action.dest == "lp_solver")

    assert available_solver_names() == ("tableau", "revised")
    assert tuple(solver_action.choices) == ("tableau", "revised")
    assert tuple(lp_solver_action.choices) == ("tableau", "revised")


def _drop_native_modules() -> None:
    for module_name in list(sys.modules):
        if _is_native_module(module_name):
            del sys.modules[module_name]


def _loaded_native_modules() -> list[str]:
    return sorted(module_name for module_name in sys.modules if _is_native_module(module_name))


def _is_native_module(module_name: str) -> bool:
    return any(
        module_name == prefix or module_name.startswith(f"{prefix}.")
        for prefix in NATIVE_MODULE_PREFIXES
    )
