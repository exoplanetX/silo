import importlib
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from silo.cli.solvers import available_solver_names
from silo.core.solution import Solution
from silo.interfaces.backend import BackendAvailabilityStatus
from silo.interfaces.tableau_ratio_native_diagnostics import (
    TABLEAU_RATIO_NATIVE_BACKEND_ID,
    TABLEAU_RATIO_NATIVE_DIAGNOSTIC_CANDIDATE_ID,
    TABLEAU_RATIO_NATIVE_DIAGNOSTICS,
    TABLEAU_RATIO_NATIVE_TOLERANCE_LABEL,
    TableauRatioNativeDiagnostic,
    tableau_ratio_native_diagnostics,
)

NATIVE_MODULE_PREFIXES = (
    "silo.native",
    "silo.native_backend",
    "silo.backends.native",
    "silo.interfaces.native",
)


def test_tableau_ratio_native_diagnostics_are_deterministic_and_candidate_specific() -> None:
    diagnostics = tableau_ratio_native_diagnostics()

    assert diagnostics is TABLEAU_RATIO_NATIVE_DIAGNOSTICS
    assert TABLEAU_RATIO_NATIVE_BACKEND_ID == "native-ratio-test"
    assert TABLEAU_RATIO_NATIVE_DIAGNOSTIC_CANDIDATE_ID == (
        "tableau_leaving_row_ratio_test"
    )
    assert TABLEAU_RATIO_NATIVE_TOLERANCE_LABEL == "python_reference_default"
    assert tuple(diagnostic.diagnostic_id for diagnostic in diagnostics) == (
        "ratio-test-native-unavailable",
        "ratio-test-native-unsupported",
    )
    assert all(
        diagnostic.candidate_id == TABLEAU_RATIO_NATIVE_DIAGNOSTIC_CANDIDATE_ID
        for diagnostic in diagnostics
    )
    assert all(
        diagnostic.backend_id == TABLEAU_RATIO_NATIVE_BACKEND_ID for diagnostic in diagnostics
    )
    assert all(
        diagnostic.tolerance_label == TABLEAU_RATIO_NATIVE_TOLERANCE_LABEL
        for diagnostic in diagnostics
    )


def test_tableau_ratio_native_diagnostics_record_required_statuses_passively() -> None:
    unavailable, unsupported = TABLEAU_RATIO_NATIVE_DIAGNOSTICS

    assert unavailable.availability_status == BackendAvailabilityStatus.UNAVAILABLE
    assert unavailable.reason == "optional_native_runtime_not_installed"
    assert "not installed" in unavailable.message
    assert unsupported.availability_status == BackendAvailabilityStatus.UNSUPPORTED
    assert unsupported.reason == "native_ratio_test_implementation_not_approved"
    assert "not approved" in unsupported.message


def test_tableau_ratio_native_diagnostic_normalizes_labels_and_status() -> None:
    diagnostic = TableauRatioNativeDiagnostic(
        diagnostic_id=" custom ",
        candidate_id=" tableau_leaving_row_ratio_test ",
        backend_id=" native-ratio-test ",
        availability_status="available",
        tolerance_label=" default ",
        message=" passive record ",
    )

    assert diagnostic.diagnostic_id == "custom"
    assert diagnostic.candidate_id == "tableau_leaving_row_ratio_test"
    assert diagnostic.backend_id == "native-ratio-test"
    assert diagnostic.availability_status == BackendAvailabilityStatus.AVAILABLE
    assert diagnostic.reason is None
    assert diagnostic.tolerance_label == "default"
    assert diagnostic.message == "passive record"


def test_tableau_ratio_native_diagnostic_records_are_immutable() -> None:
    diagnostic = TABLEAU_RATIO_NATIVE_DIAGNOSTICS[0]

    with pytest.raises(FrozenInstanceError):
        diagnostic.reason = "other"


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"diagnostic_id": " "}, "diagnostic id must not be empty"),
        ({"candidate_id": " "}, "candidate id must not be empty"),
        ({"backend_id": " "}, "backend id must not be empty"),
        ({"reason": " "}, "reason must not be empty"),
        ({"tolerance_label": " "}, "tolerance label must not be empty"),
        ({"message": " "}, "message must not be empty"),
    ],
)
def test_tableau_ratio_native_diagnostic_rejects_blank_labels(
    kwargs: dict[str, str],
    match: str,
) -> None:
    base_kwargs = {
        "diagnostic_id": "diagnostic",
        "candidate_id": TABLEAU_RATIO_NATIVE_DIAGNOSTIC_CANDIDATE_ID,
        "backend_id": TABLEAU_RATIO_NATIVE_BACKEND_ID,
        "availability_status": BackendAvailabilityStatus.UNAVAILABLE,
        "reason": "not_installed",
        "message": "Passive diagnostic record.",
    }
    base_kwargs.update(kwargs)

    with pytest.raises(ValueError, match=match):
        TableauRatioNativeDiagnostic(**base_kwargs)


@pytest.mark.parametrize(
    "status",
    [
        BackendAvailabilityStatus.UNAVAILABLE,
        BackendAvailabilityStatus.UNSUPPORTED,
    ],
)
def test_tableau_ratio_native_diagnostic_requires_reason_for_unavailable_or_unsupported(
    status: BackendAvailabilityStatus,
) -> None:
    with pytest.raises(ValueError, match="require a reason"):
        TableauRatioNativeDiagnostic(
            diagnostic_id="diagnostic",
            candidate_id=TABLEAU_RATIO_NATIVE_DIAGNOSTIC_CANDIDATE_ID,
            backend_id=TABLEAU_RATIO_NATIVE_BACKEND_ID,
            availability_status=status,
            message="Passive diagnostic record.",
        )


def test_tableau_ratio_native_diagnostic_rejects_unknown_status() -> None:
    with pytest.raises(ValueError, match="availability status"):
        TableauRatioNativeDiagnostic(
            diagnostic_id="diagnostic",
            candidate_id=TABLEAU_RATIO_NATIVE_DIAGNOSTIC_CANDIDATE_ID,
            backend_id=TABLEAU_RATIO_NATIVE_BACKEND_ID,
            availability_status="missing",
            message="Passive diagnostic record.",
        )


@pytest.mark.parametrize(
    "kwargs",
    [
        {"diagnostic_id": True},
        {"candidate_id": True},
        {"backend_id": True},
        {"reason": True},
        {"tolerance_label": True},
        {"message": True},
        {"availability_status": True},
    ],
)
def test_tableau_ratio_native_diagnostic_rejects_boolean_fields(kwargs: dict[str, object]) -> None:
    base_kwargs = {
        "diagnostic_id": "diagnostic",
        "candidate_id": TABLEAU_RATIO_NATIVE_DIAGNOSTIC_CANDIDATE_ID,
        "backend_id": TABLEAU_RATIO_NATIVE_BACKEND_ID,
        "availability_status": BackendAvailabilityStatus.UNAVAILABLE,
        "reason": "not_installed",
        "message": "Passive diagnostic record.",
    }
    base_kwargs.update(kwargs)

    with pytest.raises(TypeError):
        TableauRatioNativeDiagnostic(**base_kwargs)


def test_tableau_ratio_native_diagnostic_import_does_not_load_native_modules() -> None:
    _drop_native_modules()

    importlib.import_module("silo.interfaces.tableau_ratio_native_diagnostics")

    assert _loaded_native_modules() == []


def test_tableau_ratio_native_diagnostic_source_does_not_import_forbidden_layers() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (
        repo_root / "src" / "silo" / "interfaces" / "tableau_ratio_native_diagnostics.py"
    ).read_text(encoding="utf-8")

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
        "silo.interfaces.selector",
        "select_backend",
        "choose_leaving_row",
        "minimum_ratio_test",
        "read_json_model",
        "create_solver",
        "available_solver_names",
        "def solve",
        "importlib",
        "os.environ",
        "subprocess",
        "platform",
        "Path(",
        "open(",
        "read_text",
    )
    for pattern in forbidden_patterns:
        assert pattern not in source


def test_public_cli_solver_choices_remain_unchanged() -> None:
    assert available_solver_names() == ("tableau", "revised")


def test_public_solution_schema_has_no_ratio_native_diagnostic_fields() -> None:
    backend_diagnostic_fields = {
        "backend_id",
        "backend_kind",
        "backend_availability",
        "backend_status",
        "fallback_policy",
        "native_diagnostics",
        "native_backend",
        "ratio_native_diagnostics",
        "tableau_ratio_native_diagnostics",
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
