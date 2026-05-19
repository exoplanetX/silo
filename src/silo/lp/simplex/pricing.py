from silo.utils.numerics import DEFAULT_TOLERANCE


def choose_entering_variable(
    reduced_costs: dict[str, float],
    tolerance: float = DEFAULT_TOLERANCE,
) -> str | None:
    for name, cost in reduced_costs.items():
        if cost < -tolerance:
            return name
    return None


def choose_entering_column(
    objective_row: list[float],
    tolerance: float = DEFAULT_TOLERANCE,
) -> int | None:
    for index, coefficient in enumerate(objective_row[:-1]):
        if coefficient < -tolerance:
            return index
    return None
