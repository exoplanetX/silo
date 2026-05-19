def choose_entering_variable(reduced_costs: dict[str, float]) -> str | None:
    improving = [name for name, cost in reduced_costs.items() if cost < 0.0]
    return min(improving) if improving else None
