import importlib
import sys

import pytest

from silo.cli.main import build_parser
from silo.core.solution import Solution
from silo.interfaces.backend import (
    BackendAvailability,
    BackendAvailabilityStatus,
    BackendKind,
)

NATIVE_MODULE_PREFIXES = (
    "silo.native",
    "silo.native_backend",
    "silo.backends.native",
    "silo.interfaces.native",
)


def test_unavailable_native_experimental_diagnostic_record_is_stable() -> None:
    availability = BackendAvailability(
        backend_id="native-prototype",
        kind=BackendKind.NATIVE_EXPERIMENTAL,
        status=BackendAvailabilityStatus.UNAVAILABLE,
        reason="not_installed",
        message="Optional native runtime is not installed.",
    )

    assert availability.backend_id == "native-prototype"
    assert availability.kind == BackendKind.NATIVE_EXPERIMENTAL
    assert availability.status == BackendAvailabilityStatus.UNAVAILABLE
    assert availability.reason == "not_installed"
    assert availability.message == "Optional native runtime is not installed."


def test_unsupported_native_experimental_diagnostic_record_is_stable() -> None:
    availability = BackendAvailability(
        backend_id="native-prototype",
        kind="native_experimental",
        status="unsupported",
        reason="unsupported_problem_family",
        message="The requested problem family is outside native prototype scope.",
    )

    assert availability.kind == BackendKind.NATIVE_EXPERIMENTAL
    assert availability.status == BackendAvailabilityStatus.UNSUPPORTED
    assert availability.reason == "unsupported_problem_family"
    assert availability.message == (
        "The requested problem family is outside native prototype scope."
    )


@pytest.mark.parametrize(
    "status",
    [
        BackendAvailabilityStatus.UNAVAILABLE,
        BackendAvailabilityStatus.UNSUPPORTED,
    ],
)
def test_unavailable_or_unsupported_native_diagnostics_require_reason(
    status: BackendAvailabilityStatus,
) -> None:
    with pytest.raises(ValueError, match="require a reason"):
        BackendAvailability(
            backend_id="native-prototype",
            kind=BackendKind.NATIVE_EXPERIMENTAL,
            status=status,
        )


def test_available_native_experimental_record_is_passive_without_reason() -> None:
    availability = BackendAvailability(
        backend_id="native-prototype",
        kind=BackendKind.NATIVE_EXPERIMENTAL,
        status=BackendAvailabilityStatus.AVAILABLE,
    )

    assert availability.status == BackendAvailabilityStatus.AVAILABLE
    assert availability.reason is None
    assert availability.message == ""


def test_backend_availability_import_does_not_load_native_modules() -> None:
    _drop_native_modules()

    importlib.import_module("silo.interfaces.backend")

    assert _loaded_native_modules() == []


def test_public_cli_has_no_native_backend_selection_commands() -> None:
    parser = build_parser()
    command_action = next(action for action in parser._actions if action.dest == "command")

    assert "native" not in command_action.choices
    assert "native-solve" not in command_action.choices
    assert "backend" not in command_action.choices
    assert "backend-solve" not in command_action.choices


def test_public_solution_schema_has_no_backend_diagnostic_fields() -> None:
    backend_diagnostic_fields = {
        "backend_id",
        "backend_kind",
        "backend_availability",
        "backend_status",
        "fallback_policy",
        "native_diagnostics",
        "native_backend",
    }

    assert backend_diagnostic_fields.isdisjoint(Solution.__dataclass_fields__)


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
