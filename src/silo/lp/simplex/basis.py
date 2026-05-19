from dataclasses import dataclass

BASIC = "basic"
NONBASIC_LOWER = "nonbasic_lower"


@dataclass(frozen=True)
class Basis:
    basic_columns: tuple[int, ...]
    nonbasic_columns: tuple[int, ...]

    def validate(self, column_count: int, row_count: int) -> None:
        if len(self.basic_columns) != row_count:
            raise ValueError(
                f"Basis must have one basic column per row: expected {row_count}, "
                f"got {len(self.basic_columns)}."
            )

        _validate_unique(self.basic_columns, "basic")
        _validate_unique(self.nonbasic_columns, "nonbasic")

        basic_set = set(self.basic_columns)
        nonbasic_set = set(self.nonbasic_columns)
        overlap = sorted(basic_set & nonbasic_set)
        if overlap:
            raise ValueError(f"Basis columns overlap between basic and nonbasic sets: {overlap}.")

        expected_columns = set(range(column_count))
        actual_columns = basic_set | nonbasic_set
        missing = sorted(expected_columns - actual_columns)
        if missing:
            raise ValueError(f"Basis is missing columns: {missing}.")

        extra = sorted(actual_columns - expected_columns)
        if extra:
            raise ValueError(f"Basis contains out-of-range columns: {extra}.")

    def is_basic(self, column_index: int) -> bool:
        return column_index in self.basic_columns

    def status_for_column(self, column_index: int) -> str:
        if column_index in self.basic_columns:
            return BASIC
        if column_index in self.nonbasic_columns:
            return NONBASIC_LOWER
        raise ValueError(f"Column is not present in the basis: {column_index}.")

    def pivot(self, leaving_row: int, entering_column: int) -> "Basis":
        if leaving_row < 0 or leaving_row >= len(self.basic_columns):
            raise ValueError(f"Invalid leaving row: {leaving_row}.")
        if entering_column not in self.nonbasic_columns:
            raise ValueError(f"Entering column is not nonbasic: {entering_column}.")

        leaving_column = self.basic_columns[leaving_row]
        new_basic_columns = list(self.basic_columns)
        new_basic_columns[leaving_row] = entering_column
        new_nonbasic_columns = [
            column for column in self.nonbasic_columns if column != entering_column
        ]
        new_nonbasic_columns.append(leaving_column)
        return Basis(
            basic_columns=tuple(new_basic_columns),
            nonbasic_columns=tuple(new_nonbasic_columns),
        )


def _validate_unique(columns: tuple[int, ...], label: str) -> None:
    seen: set[int] = set()
    duplicates: list[int] = []
    for column in columns:
        if column in seen and column not in duplicates:
            duplicates.append(column)
        seen.add(column)
    if duplicates:
        raise ValueError(f"Basis has duplicate {label} columns: {duplicates}.")
