import importlib
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from silo.cli.solvers import available_solver_names
from silo.interfaces.conformance import (
    PYTHON_REFERENCE_LP_CONFORMANCE_FIXTURES,
    BackendConformanceFixture,
    python_reference_lp_conformance_fixtures,
)
from silo.interfaces.python_reference import PYTHON_REFERENCE_BACKEND_ID

NATIVE_MODULE_PREFIXES = (
    "silo.native",
    "silo.native_backend",
    "silo.backends.native",
    "silo.interfaces.native",
)


def test_python_reference_lp_conformance_fixtures_are_deterministic() -> None:
    fixtures = python_reference_lp_conformance_fixtures()

    assert fixtures == PYTHON_REFERENCE_LP_CONFORMANCE_FIXTURES
    assert tuple(fixture.fixture_id for fixture in fixtures) == (
        "lp-production-optimal",
        "lp-diet-minimize-unsupported",
    )
    assert tuple(fixture.model_path for fixture in fixtures) == (
        "tests/fixtures/lp_small/production.json",
        "tests/fixtures/lp_small/diet.json",
    )
    assert all(fixture.expected_backend_id == PYTHON_REFERENCE_BACKEND_ID for fixture in fixtures)


def test_python_reference_lp_conformance_fixture_expectations_are_passive() -> None:
    production, diet = python_reference_lp_conformance_fixtures()

    assert production.expected_status == "optimal"
    assert production.expected_objective_value == 21.0
    assert production.expected_primal_values == (("x1", 2.0), ("x2", 3.0))
    assert production.tolerance_label == "python_reference_default"

    assert diet.expected_status == "error"
    assert diet.expected_objective_value is None
    assert diet.expected_primal_values == ()
    assert "maximization" in diet.message


def test_conformance_fixture_paths_exist_without_loading_them() -> None:
    repo_root = Path(__file__).resolve().parents[2]

    for fixture in python_reference_lp_conformance_fixtures():
        assert (repo_root / fixture.model_path).is_file()


def test_conformance_fixture_records_are_immutable() -> None:
    fixture = BackendConformanceFixture(
        fixture_id="smoke",
        model_path="tests/fixtures/lp_small/production.json",
        expected_status="optimal",
        expected_primal_values=(("y", 0.0), ("x", 1.0)),
    )

    assert fixture.expected_primal_values == (("x", 1.0), ("y", 0.0))
    with pytest.raises(FrozenInstanceError):
        fixture.fixture_id = "other"
    with pytest.raises(AttributeError):
        fixture.expected_primal_values.append(("z", 2.0))


@pytest.mark.parametrize(
    ("field_name", "value", "match"),
    [
        ("fixture_id", " ", "fixture id must not be empty"),
        ("model_path", " ", "model path must not be empty"),
        ("expected_status", " ", "expected status must not be empty"),
        ("expected_backend_id", " ", "expected backend id must not be empty"),
        ("tolerance_label", " ", "tolerance label must not be empty"),
    ],
)
def test_conformance_fixture_rejects_blank_labels(
    field_name: str,
    value: str,
    match: str,
) -> None:
    kwargs = {
        "fixture_id": "fixture",
        "model_path": "tests/fixtures/lp_small/production.json",
        "expected_status": "optimal",
        "expected_backend_id": PYTHON_REFERENCE_BACKEND_ID,
        "tolerance_label": "python_reference_default",
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError, match=match):
        BackendConformanceFixture(**kwargs)


def test_conformance_fixture_rejects_duplicate_primal_names() -> None:
    with pytest.raises(ValueError, match="expected primal variable names must be unique"):
        BackendConformanceFixture(
            fixture_id="duplicate-primal",
            model_path="tests/fixtures/lp_small/production.json",
            expected_status="optimal",
            expected_primal_values=(("x", 1.0), ("x", 2.0)),
        )


@pytest.mark.parametrize(
    ("field_name", "value", "match"),
    [
        ("expected_objective_value", float("inf"), "expected objective value must be finite"),
        ("expected_primal_values", (("x", float("nan")),), "expected primal value must be finite"),
    ],
)
def test_conformance_fixture_rejects_nonfinite_values(
    field_name: str,
    value: object,
    match: str,
) -> None:
    kwargs = {
        "fixture_id": "nonfinite",
        "model_path": "tests/fixtures/lp_small/production.json",
        "expected_status": "optimal",
    }
    kwargs[field_name] = value

    with pytest.raises(ValueError, match=match):
        BackendConformanceFixture(**kwargs)


def test_conformance_fixture_import_does_not_load_native_modules() -> None:
    _drop_native_modules()

    importlib.import_module("silo.interfaces.conformance")

    assert _loaded_native_modules() == []


def test_conformance_fixture_source_does_not_import_solver_or_native_layers() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "src" / "silo" / "interfaces" / "conformance.py").read_text(
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
        "TableauSimplexSolver",
        "RevisedSimplexSolver",
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
