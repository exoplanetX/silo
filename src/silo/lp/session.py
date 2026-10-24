"""Public, owned LP session for safe model edits and semantic basis reuse."""

from copy import deepcopy
from dataclasses import replace
from time import perf_counter

from silo.core.bounds import Bounds
from silo.core.solve_types import SolveOptions, SolveResult
from silo.lp.general import solve_lp_data
from silo.modeling.general import linear_data


class LPSession:
    def __init__(self, model, options=None):
        self.options = SolveOptions() if options is None else options
        if not isinstance(self.options, SolveOptions):
            raise TypeError("options must be SolveOptions.")
        self._model = deepcopy(model)
        self._basis = None
        self._factor_state = None
        self._cache_engine = self.options.lp_engine
        self.history = []

    @property
    def model(self):
        return deepcopy(self._model)

    @property
    def basis(self):
        return self._basis

    def solve(self, model=None):
        start = perf_counter()
        candidate = deepcopy(self._model if model is None else model)
        if not isinstance(self.options, SolveOptions):
            raise TypeError("options must be SolveOptions.")
        if self._cache_engine != self.options.lp_engine:
            self._factor_state = None
            self._cache_engine = self.options.lp_engine
        try:
            data = self._data(candidate)
            if data.integer.any():
                raise ValueError("LPSession accepts continuous LPs; use solve for MILP.")
            state = None
            if self.options.lp_engine == "sparse":
                state = {} if self._factor_state is None else self._factor_state
            result = solve_lp_data(
                data,
                self.options,
                self._basis,
                start + self.options.time_limit,
                factor_state=state,
            )
        except ImportError as exc:
            result = SolveResult(
                "unsupported", "sparse_dependency_missing", diagnostics={"message": str(exc)}
            )
        except MemoryError as exc:
            result = SolveResult("limit", "resource_limit", diagnostics={"message": str(exc)})
        self._factor_state = getattr(result, "_factor_state", None)
        if hasattr(result, "_factor_state"):
            del result._factor_state
        result.elapsed_seconds = perf_counter() - start
        self._model, self._basis = candidate, result.basis
        self.history.append(
            {
                "status": result.status,
                "objective": result.objective_value,
                "iterations": result.iterations,
                "elapsed": result.elapsed_seconds,
                "diagnostics": result.diagnostics.copy(),
            }
        )
        return result

    def _data(self, candidate):
        return linear_data(
            candidate,
            self.options.max_dense_cells,
            engine=self.options.lp_engine,
            max_sparse_nnz=self.options.max_sparse_nnz,
        )

    def change_rhs(self, name, rhs):
        row = next((r for r in self._model.constraints if r.name == name), None)
        if row is not None and (row.lower_bound is not None or row.upper_bound is not None):
            raise ValueError("Explicit row intervals require change_row_bounds.")
        self._replace_row(name, rhs=rhs, lower_bound=None, upper_bound=None)

    def change_row_bounds(self, name, lower, upper):
        self._replace_row(
            name,
            lower_bound=-float("inf") if lower is None else lower,
            upper_bound=float("inf") if upper is None else upper,
        )

    def _replace_row(self, name, **changes):
        candidate = self.model
        indices = [i for i, row in enumerate(candidate.constraints) if row.name == name]
        if not indices:
            raise ValueError(f"Unknown row: {name}")
        candidate.constraints[indices[0]] = replace(candidate.constraints[indices[0]], **changes)
        self._data(candidate)
        self._model = candidate

    def change_bounds(self, name, lower, upper):
        candidate = self.model
        indices = [i for i, var in enumerate(candidate.variables) if var.name == name]
        if not indices:
            raise ValueError(f"Unknown variable: {name}")
        candidate.variables[indices[0]] = replace(
            candidate.variables[indices[0]],
            bounds=Bounds(
                -float("inf") if lower is None else lower, float("inf") if upper is None else upper
            ),
        )
        self._data(candidate)
        self._model = candidate

    def append_row(self, row):
        candidate = self.model
        candidate.add_constraint(deepcopy(row))
        self._data(candidate)
        self._model = candidate

    def append_column(self, variable, coefficients, cost=0.0):
        candidate = self.model
        if set(coefficients) - {r.name for r in candidate.constraints}:
            raise ValueError("Appended column contains unknown rows.")
        candidate.add_variable(deepcopy(variable))
        for row in candidate.constraints:
            if row.name in coefficients:
                row.coefficients[variable.name] = coefficients[row.name]
        candidate.objective.coefficients[variable.name] = cost
        self._data(candidate)
        self._model = candidate
