import importlib
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from silo.cli.solvers import available_solver_names
from silo.interfaces.parity import (
    BackendParityMatchStatus,
    BackendParityOutcome,
    BackendParityResult,
)

NATIVE_MODULE_PREFIXES = (
    "silo.native",
    "silo.native_backend",
    "silo.backends.native",
    "silo.interfaces.native",
)


def test_backend_parity_result_normalizes_mapping_primal_values() -> None:
    result = BackendParityResult(
        backend_id=" python-reference ",
        status=" optimal ",
        objective_value=21,
        primal_values={"x2": 3, "x1": 2},
        tolerance_label=" default ",
    )

    assert result.backend_id == "python-reference"
    assert result.status == "optimal"
    assert result.objective_value == 21.0
    assert result.primal_values == (("x1", 2.0), ("x2", 3.0))
    assert result.tolerance_label == "default"


def test_backend_parity_result_normalizes_pair_sequence_primal_values() -> None:
    result = BackendParityResult(
        backend_id="candidate",
        status="optimal",
        primal_values=(("y", 0), ("x", 1)),
    )

    assert result.primal_values == (("x", 1.0), ("y", 0.0))
    with pytest.raises(AttributeError):
        result.primal_values.append(("z", 2.0))


def test_parity_outcome_records_matching_pair_passively() -> None:
    reference = BackendParityResult(
        backend_id="python-reference",
        status="optimal",
        objective_value=21.0,
        primal_values={"x1": 2.0, "x2": 3.0},
    )
    candidate = BackendParityResult(
        backend_id="native-prototype",
        status="optimal",
        objective_value=21.0,
        primal_values={"x2": 3.0, "x1": 2.0},
    )
    outcome = BackendParityOutcome(
        fixture_id="lp-production-optimal",
        reference_backend_id=reference.backend_id,
        candidate_backend_id=candidate.backend_id,
        match_status="match",
        reason="recorded_match",
    )

    assert outcome.match_status == BackendParityMatchStatus.MATCH
    assert outcome.reference_backend_id == "python-reference"
    assert outcome.candidate_backend_id == "native-prototype"
    assert outcome.reason == "recorded_match"


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        ("mismatch", "objective_mismatch"),
        (BackendParityMatchStatus.UNSUPPORTED, "unsupported_status"),
    ],
)
def test_parity_outcome_records_nonmatching_or_unsupported_reasons_passively(
    status: BackendParityMatchStatus | str,
    reason: str,
) -> None:
    outcome = BackendParityOutcome(
        fixture_id="fixture",
        reference_backend_id="python-reference",
        candidate_backend_id="native-prototype",
        match_status=status,
        reason=reason,
        message="Recorded without running a comparison.",
    )

    assert outcome.match_status == BackendParityMatchStatus(status)
    assert outcome.reason == reason
    assert "comparison" in outcome.message


def test_backend_parity_records_are_immutable() -> None:
    result = BackendParityResult(backend_id="python-reference", status="optimal")
    outcome = BackendParityOutcome(
        fixture_id="fixture",
        reference_backend_id="python-reference",
        candidate_backend_id="native-prototype",
        match_status=BackendParityMatchStatus.MATCH,
    )

    with pytest.raises(FrozenInstanceError):
        result.backend_id = "other"
    with pytest.raises(FrozenInstanceError):
        outcome.reason = "other"


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"backend_id": " "}, "backend id must not be empty"),
        ({"status": " "}, "result status must not be empty"),
        ({"tolerance_label": " "}, "tolerance label must not be empty"),
    ],
)
def test_backend_parity_result_rejects_blank_labels(
    kwargs: dict[str, str],
    match: str,
) -> None:
    base_kwargs = {"backend_id": "python-reference", "status": "optimal"}
    base_kwargs.update(kwargs)

    with pytest.raises(ValueError, match=match):
        BackendParityResult(**base_kwargs)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"fixture_id": " "}, "fixture id must not be empty"),
        ({"reference_backend_id": " "}, "reference backend id must not be empty"),
        ({"candidate_backend_id": " "}, "candidate backend id must not be empty"),
        ({"tolerance_label": " "}, "tolerance label must not be empty"),
        ({"reason": " "}, "parity reason must not be empty"),
    ],
)
def test_backend_parity_outcome_rejects_blank_labels(
    kwargs: dict[str, str],
    match: str,
) -> None:
    base_kwargs = {
        "fixture_id": "fixture",
        "reference_backend_id": "python-reference",
        "candidate_backend_id": "native-prototype",
        "match_status": BackendParityMatchStatus.MATCH,
    }
    base_kwargs.update(kwargs)

    with pytest.raises(ValueError, match=match):
        BackendParityOutcome(**base_kwargs)


def test_backend_parity_result_rejects_duplicate_primal_names() -> None:
    with pytest.raises(ValueError, match="primal variable names must be unique"):
        BackendParityResult(
            backend_id="python-reference",
            status="optimal",
            primal_values=(("x", 1.0), ("x", 2.0)),
        )


@pytest.mark.parametrize(
    ("field_name", "value", "match"),
    [
        ("objective_value", float("inf"), "objective value must be finite"),
        ("primal_values", (("x", float("nan")),), "primal value must be finite"),
    ],
)
def test_backend_parity_result_rejects_nonfinite_values(
    field_name: str,
    value: object,
    match: str,
) -> None:
    kwargs = {"backend_id": "python-reference", "status": "optimal"}
    kwargs[field_name] = value

    with pytest.raises(ValueError, match=match):
        BackendParityResult(**kwargs)


def test_backend_parity_outcome_rejects_unknown_match_status() -> None:
    with pytest.raises(ValueError, match="match status"):
        BackendParityOutcome(
            fixture_id="fixture",
            reference_backend_id="python-reference",
            candidate_backend_id="native-prototype",
            match_status="unknown",
        )


def test_backend_parity_import_does_not_load_native_modules() -> None:
    _drop_native_modules()

    importlib.import_module("silo.interfaces.parity")

    assert _loaded_native_modules() == []


def test_backend_parity_source_does_not_import_solver_cli_or_native_layers() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "src" / "silo" / "interfaces" / "parity.py").read_text(
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
        "silo.interfaces.selector",
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
