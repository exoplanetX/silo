def minimum_ratio_test(ratios: dict[str, float]) -> str | None:
    feasible = {name: value for name, value in ratios.items() if value >= 0.0}
    if not feasible:
        return None
    return min(feasible, key=lambda name: (feasible[name], name))
