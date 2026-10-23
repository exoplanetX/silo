"""Unified general LP/MILP public entry point."""

from time import perf_counter

from silo.core.model import Model
from silo.core.solve_types import SolveOptions, SolveResult
from silo.lp.general import solve_lp_data
from silo.lp.kernel import BasisSnapshot
from silo.modeling.general import linear_data

__all__ = ["solve", "SolveOptions", "SolveResult"]


def solve(
    model: Model,
    options: SolveOptions | None = None,
    *,
    basis: BasisSnapshot | None = None,
    extensions=None,
):
    start = perf_counter()
    options = SolveOptions() if options is None else options
    if not isinstance(options, SolveOptions):
        raise TypeError("options must be SolveOptions.")
    if extensions is not None:
        from silo.mip.research import ResearchExtensions

        if not isinstance(extensions, ResearchExtensions):
            raise TypeError("extensions must be ResearchExtensions.")
    try:
        data = linear_data(model, options.max_dense_cells)
    except (ValueError, TypeError, AttributeError) as exc:
        return SolveResult("invalid_model", str(exc), elapsed_seconds=perf_counter() - start)
    except MemoryError as exc:
        return SolveResult(
            "limit",
            "resource_limit",
            diagnostics={"message": str(exc)},
            elapsed_seconds=perf_counter() - start,
        )
    except (FloatingPointError, OverflowError) as exc:
        return SolveResult(
            "numerical_failure", "input_conversion", diagnostics={"message": str(exc)}
        )
    if data.integer.any():
        from silo.mip.general import solve_milp

        result = solve_milp(model, data, options, start, extensions)
    else:
        if extensions is not None:
            return SolveResult("unsupported", "research_extensions_require_milp")
        result = solve_lp_data(data, options, basis, start + options.time_limit)
    result.elapsed_seconds = perf_counter() - start
    return result
