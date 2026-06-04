from collections.abc import Sequence
from dataclasses import dataclass
from math import isfinite

TABLEAU_LEAVING_ROW_RATIO_TEST_CANDIDATE_ID = "tableau_leaving_row_ratio_test"
TABLEAU_RATIO_TOLERANCE = 1e-9
TABLEAU_RATIO_TOLERANCE_LABEL = "python_reference_default"

TableauRatioRows = tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class TableauRatioTestParityFixture:
    fixture_id: str
    rows: Sequence[Sequence[float]]
    entering_column: int
    expected_leaving_row: int | None
    tolerance: float = TABLEAU_RATIO_TOLERANCE
    tolerance_label: str = TABLEAU_RATIO_TOLERANCE_LABEL
    message: str = ""

    def __post_init__(self) -> None:
        rows = _normalize_rows(self.rows)
        entering_column = _normalize_index(self.entering_column, "entering column")
        row_width = len(rows[0])
        if entering_column >= row_width - 1:
            raise ValueError("entering column must reference a non-RHS column.")

        expected_leaving_row = _normalize_optional_row_index(
            self.expected_leaving_row,
            len(rows),
        )

        object.__setattr__(
            self,
            "fixture_id",
            _normalize_label(self.fixture_id, "fixture id"),
        )
        object.__setattr__(self, "rows", rows)
        object.__setattr__(self, "entering_column", entering_column)
        object.__setattr__(self, "expected_leaving_row", expected_leaving_row)
        object.__setattr__(self, "tolerance", _normalize_tolerance(self.tolerance))
        object.__setattr__(
            self,
            "tolerance_label",
            _normalize_label(self.tolerance_label, "tolerance label"),
        )
        if not isinstance(self.message, str):
            raise TypeError("message must be a string.")


def _normalize_label(value: str, label: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be a string.")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{label} must not be empty.")
    return normalized


def _normalize_rows(rows: Sequence[Sequence[float]]) -> TableauRatioRows:
    if isinstance(rows, (str, bytes)) or not isinstance(rows, Sequence):
        raise TypeError("rows must be a sequence of row sequences.")
    if not rows:
        raise ValueError("rows must not be empty.")

    normalized_rows: list[tuple[float, ...]] = []
    row_width: int | None = None
    for row_index, row in enumerate(rows):
        if isinstance(row, (str, bytes)) or not isinstance(row, Sequence):
            raise TypeError("each row must be a sequence of numeric values.")
        if not row:
            raise ValueError("rows must not contain empty rows.")

        normalized_row = tuple(
            _normalize_float(value, f"row {row_index} value") for value in row
        )
        if row_width is None:
            row_width = len(normalized_row)
        elif len(normalized_row) != row_width:
            raise ValueError("rows must be rectangular.")
        normalized_rows.append(normalized_row)

    if row_width is None or row_width < 2:
        raise ValueError("rows must include at least one coefficient column and RHS.")

    return tuple(normalized_rows)


def _normalize_float(value: float, label: str) -> float:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be numeric.")
    try:
        normalized = float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(f"{label} must be numeric.") from exc
    if not isfinite(normalized):
        raise ValueError(f"{label} must be finite.")
    return normalized


def _normalize_index(value: int, label: str) -> int:
    if isinstance(value, bool):
        raise TypeError(f"{label} must be an integer.")
    if not isinstance(value, int):
        raise TypeError(f"{label} must be an integer.")
    if value < 0:
        raise ValueError(f"{label} must be nonnegative.")
    return value


def _normalize_optional_row_index(value: int | None, row_count: int) -> int | None:
    if value is None:
        return None
    expected_leaving_row = _normalize_index(value, "expected leaving row")
    if expected_leaving_row >= row_count:
        raise ValueError("expected leaving row must reference an existing row.")
    return expected_leaving_row


def _normalize_tolerance(value: float) -> float:
    tolerance = _normalize_float(value, "tolerance")
    if tolerance < 0.0:
        raise ValueError("tolerance must be nonnegative.")
    return tolerance


TABLEAU_LEAVING_ROW_RATIO_TEST_FIXTURES = (
    TableauRatioTestParityFixture(
        fixture_id="single-eligible-row",
        rows=((2.0, 0.0, 4.0), (0.0, 1.0, 3.0)),
        entering_column=0,
        expected_leaving_row=0,
        message="Only the first row has a pivot coefficient above tolerance.",
    ),
    TableauRatioTestParityFixture(
        fixture_id="unique-minimum-ratio",
        rows=((1.0, 0.0, 5.0), (2.0, 1.0, 4.0), (0.5, 0.0, 3.0)),
        entering_column=0,
        expected_leaving_row=1,
        message="Multiple rows are eligible and row 1 has the unique minimum ratio.",
    ),
    TableauRatioTestParityFixture(
        fixture_id="tie-breaks-by-row-index",
        rows=((1.0, 0.0, 2.0), (2.0, 1.0, 4.0)),
        entering_column=0,
        expected_leaving_row=0,
        message="Equal ratios choose the smaller row index.",
    ),
    TableauRatioTestParityFixture(
        fixture_id="tolerance-boundary-ignored",
        rows=((TABLEAU_RATIO_TOLERANCE, 0.0, 1.0), (2.0, 0.0, 6.0)),
        entering_column=0,
        expected_leaving_row=1,
        message="A pivot coefficient exactly equal to tolerance is ignored.",
    ),
    TableauRatioTestParityFixture(
        fixture_id="nonpositive-pivots-ignored",
        rows=(
            (TABLEAU_RATIO_TOLERANCE / 2.0, 0.0, 1.0),
            (0.0, 0.0, 2.0),
            (-1.0, 0.0, 3.0),
            (3.0, 0.0, 12.0),
        ),
        entering_column=0,
        expected_leaving_row=3,
        message="Below-tolerance, zero, and negative pivot coefficients are ignored.",
    ),
    TableauRatioTestParityFixture(
        fixture_id="no-eligible-row",
        rows=(
            (0.0, 1.0, 2.0),
            (-1.0, 0.0, 3.0),
            (TABLEAU_RATIO_TOLERANCE, 0.0, 4.0),
        ),
        entering_column=0,
        expected_leaving_row=None,
        message="No pivot coefficient is strictly greater than tolerance.",
    ),
    TableauRatioTestParityFixture(
        fixture_id="production-style-tableau",
        rows=((1.0, 2.0, 1.0, 0.0, 8.0), (3.0, 2.0, 0.0, 1.0, 12.0)),
        entering_column=1,
        expected_leaving_row=0,
        message="Small tableau-style rows with slack columns and RHS in the last column.",
    ),
)


def tableau_leaving_row_ratio_test_fixtures() -> tuple[TableauRatioTestParityFixture, ...]:
    return TABLEAU_LEAVING_ROW_RATIO_TEST_FIXTURES


__all__ = [
    "TABLEAU_LEAVING_ROW_RATIO_TEST_CANDIDATE_ID",
    "TABLEAU_LEAVING_ROW_RATIO_TEST_FIXTURES",
    "TABLEAU_RATIO_TOLERANCE",
    "TABLEAU_RATIO_TOLERANCE_LABEL",
    "TableauRatioRows",
    "TableauRatioTestParityFixture",
    "tableau_leaving_row_ratio_test_fixtures",
]
