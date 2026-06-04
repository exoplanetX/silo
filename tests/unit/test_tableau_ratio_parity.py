import importlib
import sys
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from silo.cli.solvers import available_solver_names
from silo.interfaces.tableau_ratio_parity import (
    TABLEAU_LEAVING_ROW_RATIO_TEST_CANDIDATE_ID,
    TABLEAU_LEAVING_ROW_RATIO_TEST_FIXTURES,
    TABLEAU_RATIO_TOLERANCE,
    TABLEAU_RATIO_TOLERANCE_LABEL,
    TableauRatioRows,
    TableauRatioTestParityFixture,
    tableau_leaving_row_ratio_test_fixtures,
)

NATIVE_MODULE_PREFIXES = (
    "silo.native",
    "silo.native_backend",
    "silo.backends.native",
    "silo.interfaces.native",
)


def test_tableau_ratio_fixture_set_is_deterministic_and_candidate_specific() -> None:
    fixtures = tableau_leaving_row_ratio_test_fixtures()

    assert fixtures is TABLEAU_LEAVING_ROW_RATIO_TEST_FIXTURES
    assert TABLEAU_LEAVING_ROW_RATIO_TEST_CANDIDATE_ID == "tableau_leaving_row_ratio_test"
    assert TABLEAU_RATIO_TOLERANCE == 1e-9
    assert TABLEAU_RATIO_TOLERANCE_LABEL == "python_reference_default"
    assert tuple(fixture.fixture_id for fixture in fixtures) == (
        "single-eligible-row",
        "unique-minimum-ratio",
        "tie-breaks-by-row-index",
        "tolerance-boundary-ignored",
        "nonpositive-pivots-ignored",
        "no-eligible-row",
        "production-style-tableau",
    )
    assert all(fixture.tolerance_label == TABLEAU_RATIO_TOLERANCE_LABEL for fixture in fixtures)


def test_tableau_ratio_fixtures_record_expected_reference_results_passively() -> None:
    expected_results = {
        "single-eligible-row": 0,
        "unique-minimum-ratio": 1,
        "tie-breaks-by-row-index": 0,
        "tolerance-boundary-ignored": 1,
        "nonpositive-pivots-ignored": 3,
        "no-eligible-row": None,
        "production-style-tableau": 0,
    }

    for fixture in TABLEAU_LEAVING_ROW_RATIO_TEST_FIXTURES:
        assert fixture.expected_leaving_row == expected_results[fixture.fixture_id]
        assert _local_expected_leaving_row(
            fixture.rows,
            fixture.entering_column,
            fixture.tolerance,
        ) == fixture.expected_leaving_row


def test_tableau_ratio_fixture_normalizes_rows_and_labels() -> None:
    fixture = TableauRatioTestParityFixture(
        fixture_id=" custom ",
        rows=[[1, 0, 2], [2, 0, 5]],
        entering_column=0,
        expected_leaving_row=0,
        tolerance=1,
        tolerance_label=" default ",
    )

    assert fixture.fixture_id == "custom"
    assert fixture.rows == ((1.0, 0.0, 2.0), (2.0, 0.0, 5.0))
    assert fixture.entering_column == 0
    assert fixture.expected_leaving_row == 0
    assert fixture.tolerance == 1.0
    assert fixture.tolerance_label == "default"


def test_tableau_ratio_fixture_records_are_immutable() -> None:
    fixture = TABLEAU_LEAVING_ROW_RATIO_TEST_FIXTURES[0]

    with pytest.raises(FrozenInstanceError):
        fixture.fixture_id = "other"
    with pytest.raises(AttributeError):
        fixture.rows.append((1.0, 2.0, 3.0))
    with pytest.raises(TypeError):
        fixture.rows[0][0] = 99.0


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"fixture_id": " "}, "fixture id must not be empty"),
        ({"tolerance_label": " "}, "tolerance label must not be empty"),
    ],
)
def test_tableau_ratio_fixture_rejects_blank_labels(
    kwargs: dict[str, str],
    match: str,
) -> None:
    base_kwargs = {
        "fixture_id": "fixture",
        "rows": ((1.0, 2.0),),
        "entering_column": 0,
        "expected_leaving_row": 0,
    }
    base_kwargs.update(kwargs)

    with pytest.raises(ValueError, match=match):
        TableauRatioTestParityFixture(**base_kwargs)


@pytest.mark.parametrize(
    ("rows", "match"),
    [
        ((), "rows must not be empty"),
        (((1.0, 2.0), (3.0,)), "rows must be rectangular"),
        (((1.0,),), "at least one coefficient column and RHS"),
        (((float("inf"), 1.0),), "row 0 value must be finite"),
    ],
)
def test_tableau_ratio_fixture_rejects_invalid_rows(
    rows: object,
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        TableauRatioTestParityFixture(
            fixture_id="fixture",
            rows=rows,
            entering_column=0,
            expected_leaving_row=0,
        )


@pytest.mark.parametrize(
    "rows",
    [
        "not rows",
        (("not numeric", 1.0),),
        ((True, 1.0),),
    ],
)
def test_tableau_ratio_fixture_rejects_nonnumeric_or_bool_rows(rows: object) -> None:
    with pytest.raises(TypeError):
        TableauRatioTestParityFixture(
            fixture_id="fixture",
            rows=rows,
            entering_column=0,
            expected_leaving_row=0,
        )


@pytest.mark.parametrize(
    ("entering_column", "match"),
    [
        (-1, "entering column must be nonnegative"),
        (1, "entering column must reference a non-RHS column"),
        (2, "entering column must reference a non-RHS column"),
    ],
)
def test_tableau_ratio_fixture_rejects_invalid_entering_column(
    entering_column: int,
    match: str,
) -> None:
    with pytest.raises(ValueError, match=match):
        TableauRatioTestParityFixture(
            fixture_id="fixture",
            rows=((1.0, 2.0),),
            entering_column=entering_column,
            expected_leaving_row=0,
        )


@pytest.mark.parametrize("value", [True, 0.0, "0"])
def test_tableau_ratio_fixture_rejects_noninteger_entering_column(value: object) -> None:
    with pytest.raises(TypeError, match="entering column must be an integer"):
        TableauRatioTestParityFixture(
            fixture_id="fixture",
            rows=((1.0, 2.0),),
            entering_column=value,
            expected_leaving_row=0,
        )


@pytest.mark.parametrize("value", [True, 0.0, "0"])
def test_tableau_ratio_fixture_rejects_noninteger_expected_row(value: object) -> None:
    with pytest.raises(TypeError, match="expected leaving row must be an integer"):
        TableauRatioTestParityFixture(
            fixture_id="fixture",
            rows=((1.0, 2.0),),
            entering_column=0,
            expected_leaving_row=value,
        )


def test_tableau_ratio_fixture_rejects_expected_row_outside_rows() -> None:
    with pytest.raises(ValueError, match="expected leaving row must reference an existing row"):
        TableauRatioTestParityFixture(
            fixture_id="fixture",
            rows=((1.0, 2.0),),
            entering_column=0,
            expected_leaving_row=1,
        )


@pytest.mark.parametrize(
    ("tolerance", "error_type", "match"),
    [
        (True, TypeError, "tolerance must be numeric"),
        (-1e-9, ValueError, "tolerance must be nonnegative"),
        (float("nan"), ValueError, "tolerance must be finite"),
    ],
)
def test_tableau_ratio_fixture_rejects_invalid_tolerance(
    tolerance: object,
    error_type: type[Exception],
    match: str,
) -> None:
    with pytest.raises(error_type, match=match):
        TableauRatioTestParityFixture(
            fixture_id="fixture",
            rows=((1.0, 2.0),),
            entering_column=0,
            expected_leaving_row=0,
            tolerance=tolerance,
        )


def test_tableau_ratio_fixture_import_does_not_load_native_modules() -> None:
    _drop_native_modules()

    importlib.import_module("silo.interfaces.tableau_ratio_parity")

    assert _loaded_native_modules() == []


def test_tableau_ratio_fixture_source_does_not_import_solver_cli_or_native_layers() -> None:
    repo_root = Path(__file__).resolve().parents[2]
    source = (
        repo_root / "src" / "silo" / "interfaces" / "tableau_ratio_parity.py"
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
        "choose_leaving_row",
        "minimum_ratio_test",
        "read_json_model",
        "create_solver",
        "available_solver_names",
        "def solve",
        "importlib",
        "os.environ",
        "subprocess",
        "Path(",
        "open(",
        "read_text",
    )
    for pattern in forbidden_patterns:
        assert pattern not in source


def test_public_cli_solver_choices_remain_unchanged() -> None:
    assert available_solver_names() == ("tableau", "revised")


def _local_expected_leaving_row(
    rows: TableauRatioRows,
    entering_column: int,
    tolerance: float,
) -> int | None:
    best_row: int | None = None
    best_ratio: float | None = None
    for row_index, row in enumerate(rows):
        pivot_coefficient = row[entering_column]
        if pivot_coefficient <= tolerance:
            continue
        ratio = row[-1] / pivot_coefficient
        if best_ratio is None or (ratio, row_index) < (best_ratio, best_row):
            best_ratio = ratio
            best_row = row_index
    return best_row


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
