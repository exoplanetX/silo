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
    python_reference_backend_records,
)

NATIVE_MODULE_PREFIXES = (
    "silo.native",
    "silo.native_backend",
    "silo.backends.native",
    "silo.interfaces.native",
)


def test_python_reference_capability_record_is_deterministic() -> None:
    assert PYTHON_REFERENCE_BACKEND_ID == "python-reference"
    assert PYTHON_REFERENCE_CAPABILITY.backend_id == PYTHON_REFERENCE_BACKEND_ID
    assert PYTHON_REFERENCE_CAPABILITY.kind == BackendKind.PYTHON_REFERENCE
    assert PYTHON_REFERENCE_CAPABILITY.problem_families == (
        "continuous_lp",
        "mixed_integer_linear",
    )
    assert PYTHON_REFERENCE_CAPABILITY.variable_types == (
        "continuous",
        "binary",
        "integer",
    )
    assert PYTHON_REFERENCE_CAPABILITY.constraint_senses == ("<=", ">=", "=")
    assert PYTHON_REFERENCE_CAPABILITY.diagnostics == (
        "status",
        "objective_value",
        "primal_values",
        "slack_values",
        "reduced_costs",
        "basis_status",
        "node_log",
    )
    assert PYTHON_REFERENCE_CAPABILITY.tolerance_label == "python_reference_default"


def test_python_reference_availability_record_is_available() -> None:
    assert PYTHON_REFERENCE_AVAILABILITY.backend_id == PYTHON_REFERENCE_BACKEND_ID
    assert PYTHON_REFERENCE_AVAILABILITY.kind == BackendKind.PYTHON_REFERENCE
    assert PYTHON_REFERENCE_AVAILABILITY.status == BackendAvailabilityStatus.AVAILABLE
    assert PYTHON_REFERENCE_AVAILABILITY.reason is None
    assert "native" in PYTHON_REFERENCE_AVAILABILITY.message


def test_python_reference_records_are_immutable_and_stable() -> None:
    first = python_reference_backend_records()
    second = python_reference_backend_records()

    assert first == second
    assert first == (PYTHON_REFERENCE_CAPABILITY, PYTHON_REFERENCE_AVAILABILITY)
    with pytest.raises(FrozenInstanceError):
        first[0].backend_id = "other"
    with pytest.raises(AttributeError):
        first[0].diagnostics.append("dual_values")


def test_python_reference_adapter_import_does_not_load_native_modules() -> None:
    _drop_native_modules()

    importlib.import_module("silo.interfaces.python_reference")

    assert _loaded_native_modules() == []


def test_python_reference_adapter_source_imports_only_backend_records() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (repo_root / "src" / "silo" / "interfaces" / "python_reference.py").read_text(
        encoding="utf-8"
    )

    assert "from silo.interfaces.backend import" in source
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
        "importlib",
        "os.environ",
        "subprocess",
        "def solve",
        "create_solver",
        "available_solver_names",
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
