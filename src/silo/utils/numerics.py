DEFAULT_TOLERANCE = 1e-9


def is_close(a: float, b: float, tolerance: float = DEFAULT_TOLERANCE) -> bool:
    return abs(a - b) <= tolerance
