from silo.utils.numerics import DEFAULT_TOLERANCE


def minimum_ratio_test(ratios: dict[str, float]) -> str | None:
    feasible = {name: value for name, value in ratios.items() if value >= 0.0}
    if not feasible:
        return None
    return min(feasible, key=lambda name: (feasible[name], name))


def choose_leaving_row(
    rows: list[list[float]],
    entering_column: int,
    tolerance: float = DEFAULT_TOLERANCE,
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
