import importlib
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from silo.cli.solvers import available_solver_names
from silo.interfaces.backend import BackendAvailabilityStatus, BackendKind
from silo.interfaces.python_reference import (
    PYTHON_REFERENCE_AVAILABILITY,
    PYTHON_REFERENCE_BACKEND_ID,
    PYTHON_REFERENCE_CAPABILITY,
)
from silo.interfaces.selector import (
    DEFAULT_PYTHON_REFERENCE_REASON,
    NO_FALLBACK_POLICY,
    REQUESTED_PYTHON_REFERENCE_REASON,
    UNSUPPORTED_BACKEND_REASON,
    BackendSelectionDecision,
    BackendSelectionRequest,
    select_backend,
)

NATIVE_MODULE_PREFIXES = (
    "silo.native",
    "silo.native_backend",
    "silo.backends.native",
    "silo.interfaces.native",
)


def test_default_noop_selection_returns_python_reference_records() -> None:
    capability, availability, decision = select_backend()

    assert capability is PYTHON_REFERENCE_CAPABILITY
    assert availability is PYTHON_REFERENCE_AVAILABILITY
    assert decision.selected_backend_id == PYTHON_REFERENCE_BACKEND_ID
    assert decision.selected_kind == BackendKind.PYTHON_REFERENCE
    assert decision.availability_status == BackendAvailabilityStatus.AVAILABLE
    assert decision.fallback_policy == NO_FALLBACK_POLICY
    assert decision.reason == DEFAULT_PYTHON_REFERENCE_REASON
    assert decision.message == PYTHON_REFERENCE_AVAILABILITY.message


def test_explicit_python_reference_request_returns_same_deterministic_records() -> None:
    request = BackendSelectionRequest(
        requested_backend_id=f" {PYTHON_REFERENCE_BACKEND_ID} ",
        fallback_policy=" no_fallback ",
    )
    capability, availability, decision = select_backend(request)

    assert capability is PYTHON_REFERENCE_CAPABILITY
    assert availability is PYTHON_REFERENCE_AVAILABILITY
    assert request.requested_backend_id == PYTHON_REFERENCE_BACKEND_ID
    assert request.fallback_policy == NO_FALLBACK_POLICY
    assert decision.selected_backend_id == PYTHON_REFERENCE_BACKEND_ID
    assert decision.reason == REQUESTED_PYTHON_REFERENCE_REASON


def test_non_python_reference_request_returns_passive_unsupported_decision() -> None:
    capability, availability, decision = select_backend(
        BackendSelectionRequest(requested_backend_id="native-prototype")
    )

    assert capability is None
    assert availability.backend_id == "native-prototype"
    assert availability.kind == BackendKind.NATIVE_EXPERIMENTAL
    assert availability.status == BackendAvailabilityStatus.UNSUPPORTED
    assert availability.reason == UNSUPPORTED_BACKEND_REASON
    assert "does not dispatch" in availability.message
    assert decision.selected_backend_id == "native-prototype"
    assert decision.selected_kind == BackendKind.NATIVE_EXPERIMENTAL
    assert decision.availability_status == BackendAvailabilityStatus.UNSUPPORTED
    assert decision.fallback_policy == NO_FALLBACK_POLICY
    assert decision.reason == UNSUPPORTED_BACKEND_REASON
    assert decision.message == availability.message


def test_selector_request_and_decision_records_are_immutable() -> None:
    request = BackendSelectionRequest(requested_backend_id="python-reference")
    decision = select_backend(request)[2]

    with pytest.raises(FrozenInstanceError):
        request.requested_backend_id = "other"
    with pytest.raises(FrozenInstanceError):
        decision.reason = "other"


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"requested_backend_id": " "}, "requested backend id must not be empty"),
        ({"fallback_policy": " "}, "fallback policy must not be empty"),
    ],
)
def test_selector_request_rejects_blank_labels(
    kwargs: dict[str, str],
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        BackendSelectionRequest(**kwargs)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"selected_backend_id": " "}, "selected backend id must not be empty"),
        ({"fallback_policy": " "}, "fallback policy must not be empty"),
        ({"reason": " "}, "selection reason must not be empty"),
    ],
)
def test_selector_decision_rejects_blank_labels(
    kwargs: dict[str, str],
    match: str,
) -> None:
    base_kwargs = {
        "selected_backend_id": PYTHON_REFERENCE_BACKEND_ID,
        "selected_kind": BackendKind.PYTHON_REFERENCE,
        "availability_status": BackendAvailabilityStatus.AVAILABLE,
        "fallback_policy": NO_FALLBACK_POLICY,
        "reason": DEFAULT_PYTHON_REFERENCE_REASON,
    }
    base_kwargs.update(kwargs)

    with pytest.raises(ValueError, match=match):
        BackendSelectionDecision(**base_kwargs)


def test_selector_rejects_non_request_objects() -> None:
    with pytest.raises(TypeError, match="BackendSelectionRequest"):
        select_backend("python-reference")


def test_selector_import_does_not_load_native_modules() -> None:
    _drop_native_modules()

    importlib.import_module("silo.interfaces.selector")

    assert _loaded_native_modules() == []


def test_selector_source_does_not_import_solver_cli_or_native_layers() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "src" / "silo" / "interfaces" / "selector.py").read_text(
        encoding="utf-8"
    )

    forbidden_patterns = (
        "silo.lp",
        "silo.mip",
        "silo.presolve",
        "silo.cuts",
        "silo.decomposition",
        "silo.uncertainty",
        "silo.cli",
        "silo.native",
        "native_backend",
        "silo.backends.native",
        "silo.interfaces.native",
        "read_json_model",
        "create_solver",
        "available_solver_names",
        "def solve",
        "importlib",
        "os.environ",
        "subprocess",
    )
    for pattern in forbidden_patterns:
        assert pattern not in source


def test_public_cli_solver_choices_remain_unchanged() -> None:
    assert available_solver_names() == ("tableau", "revised")


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
