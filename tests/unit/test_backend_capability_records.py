import importlib
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from silo.interfaces.backend import (
    BackendAvailability,
    BackendAvailabilityStatus,
    BackendCapability,
    BackendKind,
)

NATIVE_MODULE_PREFIXES = (
    "silo.native",
    "silo.native_backend",
    "silo.backends.native",
    "silo.interfaces.native",
)


def test_python_reference_capability_record_is_normalized_and_immutable() -> None:
    capability = BackendCapability(
        backend_id=" python-reference ",
        kind="python_reference",
        problem_families=[" lp ", "mip"],
        variable_types=(" continuous ", "binary", "integer"),
        constraint_senses=["<=", ">=", "="],
        diagnostics=(" status ", "objective", "primal_values"),
        tolerance_label=" default ",
    )

    assert capability.backend_id == "python-reference"
    assert capability.kind == BackendKind.PYTHON_REFERENCE
    assert capability.problem_families == ("lp", "mip")
    assert capability.variable_types == ("continuous", "binary", "integer")
    assert capability.constraint_senses == ("<=", ">=", "=")
    assert capability.diagnostics == ("status", "objective", "primal_values")
    assert capability.tolerance_label == "default"

    with pytest.raises(FrozenInstanceError):
        capability.backend_id = "other"
    with pytest.raises(AttributeError):
        capability.problem_families.append("qp")


def test_unavailable_native_experimental_availability_record_is_passive() -> None:
    availability = BackendAvailability(
        backend_id=" native-prototype ",
        kind=BackendKind.NATIVE_EXPERIMENTAL,
        status="unavailable",
        reason="not_installed",
        message="No optional native runtime is installed.",
    )

    assert availability.backend_id == "native-prototype"
    assert availability.kind == BackendKind.NATIVE_EXPERIMENTAL
    assert availability.status == BackendAvailabilityStatus.UNAVAILABLE
    assert availability.reason == "not_installed"
    assert availability.message == "No optional native runtime is installed."


def test_available_backend_does_not_require_reason() -> None:
    availability = BackendAvailability(
        backend_id="python-reference",
        kind="python_reference",
        status=BackendAvailabilityStatus.AVAILABLE,
    )

    assert availability.status == BackendAvailabilityStatus.AVAILABLE
    assert availability.reason is None


def test_blank_backend_id_is_rejected() -> None:
    with pytest.raises(ValueError, match="backend id must not be empty"):
        BackendCapability(backend_id=" ", kind="python_reference")


def test_blank_tuple_values_are_rejected() -> None:
    with pytest.raises(ValueError, match="problem families entry must not be empty"):
        BackendCapability(
            backend_id="python-reference",
            kind="python_reference",
            problem_families=("lp", " "),
        )


def test_duplicate_tuple_values_are_rejected_after_trimming() -> None:
    with pytest.raises(ValueError, match="diagnostics must not contain duplicate entries"):
        BackendCapability(
            backend_id="python-reference",
            kind="python_reference",
            diagnostics=("status", " status "),
        )


def test_tuple_like_fields_reject_plain_strings() -> None:
    with pytest.raises(TypeError, match="problem families must be a sequence of strings"):
        BackendCapability(
            backend_id="python-reference",
            kind="python_reference",
            problem_families="lp",
        )


@pytest.mark.parametrize(
    "status",
    [
        BackendAvailabilityStatus.UNAVAILABLE,
        BackendAvailabilityStatus.UNSUPPORTED,
    ],
)
def test_unavailable_or_unsupported_status_requires_reason(
    status: BackendAvailabilityStatus,
) -> None:
    with pytest.raises(ValueError, match="require a reason"):
        BackendAvailability(
            backend_id="native-prototype",
            kind="native_experimental",
            status=status,
        )


def test_unknown_kind_and_status_are_rejected() -> None:
    with pytest.raises(ValueError, match="backend kind"):
        BackendCapability(backend_id="python-reference", kind="experimental")
    with pytest.raises(ValueError, match="availability status"):
        BackendAvailability(
            backend_id="python-reference",
            kind="python_reference",
            status="missing",
        )


def test_backend_record_import_does_not_load_native_modules() -> None:
    _drop_native_modules()

    importlib.import_module("silo.interfaces.backend")

    assert _loaded_native_modules() == []


def test_backend_record_source_has_no_native_implementation_references() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "src" / "silo" / "interfaces" / "backend.py").read_text(
        encoding="utf-8"
    )

    forbidden_patterns = (
        "silo.native",
        "native_backend",
        "silo.backends.native",
        "silo.interfaces.native",
        "importlib",
        "os.environ",
        "subprocess",
    )

    for pattern in forbidden_patterns:
        assert pattern not in source


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
