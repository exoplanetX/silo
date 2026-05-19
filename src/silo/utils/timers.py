from collections.abc import Iterator
from contextlib import contextmanager
from time import perf_counter


@contextmanager
def timer() -> Iterator[dict[str, float]]:
    state = {"elapsed": 0.0}
    start = perf_counter()
    try:
        yield state
    finally:
        state["elapsed"] = perf_counter() - start
