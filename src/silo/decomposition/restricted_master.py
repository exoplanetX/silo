"""MIN restricted masters with cold solves and explicit full-row basis reuse.

Only the caller's current columns are optimized. Nonoptimal backend statuses are
diagnostics, without certified full-master infeasibility or unboundedness claims.
"""

from collections.abc import Mapping
from dataclasses import dataclass, field
from math import inf, isfinite
from types import MappingProxyType

from silo.core.constraint import Constraint
from silo.core.enums import OptimizationSense, VariableType
from silo.core.model import Model
from silo.core.objective import Objective
from silo.core.status import SolverStatus
from silo.core.variable import Variable
from silo.lp.base import LPSolver
from silo.lp.optimality import check_lp_optimality
from silo.lp.simplex.revised import RevisedSimplexSolver
from silo.utils.numerics import DEFAULT_TOLERANCE


@dataclass(frozen=True)
class RestrictedMasterResult:
    """Independent MIN snapshot; mappings are read-only copies, indexed by name.

    Optimal fields describe only the current column set. LE row multipliers are
    nonpositive, GE nonnegative, and reduced costs are c - A.T*pi >= 0.
    """

    status: SolverStatus
    objective_value: float | None = None
    primal_values: Mapping[str, float] = field(default_factory=dict)
    dual_values: Mapping[str, float] = field(default_factory=dict)
    reduced_costs: Mapping[str, float] = field(default_factory=dict)
    message: str = ""

    def __post_init__(self) -> None:
        for name in ("primal_values", "dual_values", "reduced_costs"):
            object.__setattr__(self, name, MappingProxyType(dict(getattr(self, name))))


@dataclass(frozen=True)
class RestrictedMasterReoptimizationResult:
    result: RestrictedMasterResult
    used_warm_start: bool = False
    warm_phase_two_attempted: bool = False
    warm_iterations: int = 0
    cold_solve_count: int = 0
    cold_iterations: int = 0
    fallback_reason: str = ""
    snapshot_available: bool = False
    snapshot_unavailable_reason: str = ""


class RestrictedMasterProblem:
    """Own a full MIN model and explicitly append columns, preserving every row.

    Variables must be continuous with bounds [0, +infinity). Ordinary solve is
    cold. solve_reoptimized explicitly opts into append-only full-row reuse.
    """

    def __init__(self, model: Model) -> None:
        if not isinstance(model, Model):
            raise TypeError("Restricted master input must be a Model.")
        for variable in model.variables:
            _validate_name(variable.name, "Variable name")
        for row in model.constraints:
            _validate_name(row.name, "Row name")
        model.validate()
        if model.objective.sense != OptimizationSense.MINIMIZE:
            raise ValueError("Restricted master requires a minimization model.")
        for variable in model.variables:
            if variable.var_type != VariableType.CONTINUOUS or (
                variable.bounds.lower != 0 or variable.bounds.upper != inf
            ):
                raise ValueError("Restricted master variables require continuous bounds [0, +inf).")
        self._model = _copy_model(model)
        self._basis_snapshot = None

    def add_column(
        self, *, name: str, cost: float, row_coefficients: Mapping[str, float],
    ) -> None:
        """Append one validated column atomically; omitted row coefficients are zero.

        Names match exactly. Zero columns and different names with equal vectors
        are valid. The caller owns feasibility seeding and column selection.
        """
        _validate_name(name, "Column name")
        if name in self._model.variable_names():
            raise ValueError(f"Duplicate variable name: {name}")
        cost = _finite(cost, "Column cost")
        if not isinstance(row_coefficients, Mapping):
            raise TypeError("Row coefficients must be a mapping.")
        row_names = {row.name for row in self._model.constraints}
        coefficients: dict[str, float] = {}
        for row_name, value in row_coefficients.items():
            if row_name not in row_names:
                raise ValueError(f"Unknown row: {row_name!r}")
            coefficients[row_name] = _finite(value, "Column coefficient")

        candidate = _copy_model(self._model)
        candidate.variables.append(Variable(name))
        candidate.objective.coefficients[name] = cost
        for row in candidate.constraints:
            row.coefficients[name] = coefficients.get(row.name, 0.0)
        candidate.validate()
        self._model = candidate

    def solve(self, solver: LPSolver | None = None) -> RestrictedMasterResult:
        """Cold-solve all current columns; verify every optimal native result.

        Internal objective, constant, multipliers and reduced costs are negated.
        A separate reference copy protects verification from backend mutation.
        """
        self._basis_snapshot = None
        native = _copy_model(self._model, negate_objective=True)
        reference = _copy_model(native)
        backend = RevisedSimplexSolver() if solver is None else solver
        solution = backend.solve(native)
        return _publish_result(reference, solution)

    def solve_reoptimized(self, solver: RevisedSimplexSolver | None = None
                          ) -> RestrictedMasterReoptimizationResult:
        """Explicit append-only reuse; the RMP owns and invalidates its cache."""
        backend = RevisedSimplexSolver() if solver is None else solver
        if not isinstance(backend, RevisedSimplexSolver):
            raise TypeError("RMP reoptimization requires a native RevisedSimplexSolver.")
        native = _copy_model(self._model, negate_objective=True)
        reference = _copy_model(native)
        outcome = backend.reoptimize(native, self._basis_snapshot)
        result = _publish_result(reference, outcome.details.solution)
        self._basis_snapshot = outcome.snapshot if result.status == SolverStatus.OPTIMAL else None
        reason = outcome.snapshot_unavailable_reason
        if result.status != SolverStatus.OPTIMAL:
            reason = f"Final RMP {result.status.value}: {result.message}"
        return RestrictedMasterReoptimizationResult(
            result=result, used_warm_start=outcome.used_warm_start
            and result.status == SolverStatus.OPTIMAL,
            warm_phase_two_attempted=outcome.warm_phase_two_attempted,
            warm_iterations=outcome.warm_iterations, cold_solve_count=outcome.cold_solve_count,
            cold_iterations=outcome.cold_iterations, fallback_reason=outcome.fallback_reason,
            snapshot_available=self._basis_snapshot is not None, snapshot_unavailable_reason=reason,
        )


def _publish_result(reference, solution) -> RestrictedMasterResult:
    if solution.status != SolverStatus.OPTIMAL:
        return RestrictedMasterResult(status=solution.status, message=solution.message)
    checked = check_lp_optimality(reference, solution, tolerance=DEFAULT_TOLERANCE)
    if not checked.passed:
        return RestrictedMasterResult(
            status=SolverStatus.NUMERICAL_ISSUE,
            message=f"Restricted master optimality evidence failed: {checked.message}",
        )
    return RestrictedMasterResult(
        status=SolverStatus.OPTIMAL, objective_value=-solution.objective_value,
        primal_values=solution.primal_values,
        dual_values={name: -value for name, value in solution.dual_values.items()},
        reduced_costs={name: -value for name, value in solution.reduced_costs.items()},
        message=f"Restricted master optimal for current columns. {solution.message}",
    )


def _copy_model(model: Model, *, negate_objective: bool = False) -> Model:
    sign = -1.0 if negate_objective else 1.0
    return Model(
        name=model.name,
        # Variable and Bounds are frozen records; their owning list is copied.
        variables=list(model.variables),
        constraints=[
            Constraint(row.name,
                       {name: _finite(value, "Row coefficient")
                        for name, value in row.coefficients.items()},
                       row.sense, _finite(row.rhs, "Row RHS"))
            for row in model.constraints
        ],
        objective=Objective(
            {name: sign * _finite(value, "Objective coefficient")
             for name, value in model.objective.coefficients.items()},
            OptimizationSense.MAXIMIZE if negate_objective else model.objective.sense,
            sign * _finite(model.objective.constant, "Objective constant"),
        ),
    )


def _validate_name(name: str, label: str) -> None:
    if not isinstance(name, str) or not name.strip():
        raise ValueError(f"{label} must be a nonblank string.")


def _finite(value: float, label: str) -> float:
    try:
        numeric = float(value)
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError(f"{label} must be a finite number.") from exc
    if not isfinite(numeric):
        raise ValueError(f"{label} must be finite.")
    return numeric
