from dataclasses import dataclass, field


@dataclass(frozen=True)
class SparseMatrix:
    """Coordinate sparse matrix used as an early solver-facing placeholder."""

    rows: tuple[str, ...]
    columns: tuple[str, ...]
    coefficients: dict[tuple[str, str], float] = field(default_factory=dict)

    def get(self, row: str, column: str) -> float:
        return self.coefficients.get((row, column), 0.0)
