from dataclasses import dataclass

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense
from silo.core.model import Model
from silo.core.solution import Solution
from silo.presolve.column_diagnostics import inspect_empty_columns
from silo.presolve.diagnostics import PresolveDiagnostics, PresolveStatus, PresolveWarning
from silo.presolve.fixed_variable import FixedValue, eliminate_fixed_variables
from silo.presolve.reductions import ReductionRecord, ReductionType, reduction_data
from silo.presolve.scaling import ScalingDiagnostics, analyze_scaling
from silo.utils.numerics import DEFAULT_TOLERANCE

FIXED_BASIS_STATUS = "fixed"


@dataclass(frozen=True)
class PresolveResult:
    model: Model
    reductions: tuple[ReductionRecord, ...]
    diagnostics: PresolveDiagnostics
    scaling: ScalingDiagnostics
    changed: bool = False
    message: str = ""
    fixed_values: tuple[FixedValue, ...] = ()

    def recover_solution(self, solution: Solution) -> Solution:
        presolved_variable_names = set(self.model.variable_names())
        primal_values = {
            name: value
            for name, value in solution.primal_values.items()
            if name in presolved_variable_names
        }
        reduced_costs = {
            name: value
            for name, value in solution.reduced_costs.items()
            if name in presolved_variable_names
        }
        basis_status = {
            name: status
            for name, status in solution.basis_status.items()
            if name in presolved_variable_names
        }
        for variable_name, fixed_value in self.fixed_values:
            primal_values[variable_name] = fixed_value
            reduced_costs[variable_name] = 0.0
            basis_status[variable_name] = FIXED_BASIS_STATUS

        return Solution(
            status=solution.status,
            objective_value=solution.objective_value,
            primal_values=primal_values,
            slack_values=dict(solution.slack_values),
            dual_values=dict(solution.dual_values),
            reduced_costs=reduced_costs,
            basis_status=basis_status,
            message=solution.message,
        )


@dataclass(frozen=True)
class StructuralPassResult:
    model: Model
    reductions: tuple[ReductionRecord, ...]
    removed_rows: tuple[str, ...]
    fixed_values: tuple[FixedValue, ...]
    fixed_variables: tuple[str, ...]
    changed: bool


class Presolver:
    def __init__(self, max_passes: int | None = None) -> None:
        if max_passes is not None and max_passes < 1:
            raise ValueError("max_passes must be positive.")
        self._max_passes = max_passes

    def run(self, model: Model) -> PresolveResult:
        model.validate()
        scaling = analyze_scaling(model)

        current_model = model
        reductions: list[ReductionRecord] = []
        removed_rows: list[str] = []
        fixed_values: list[FixedValue] = []
        max_passes = self._max_passes or _default_max_passes(model)

        for _ in range(max_passes):
            infeasible_empty_row = _first_infeasible_empty_row(current_model)
            if infeasible_empty_row is not None:
                warning = PresolveWarning(
                    code="empty_row_infeasible",
                    message="Empty row is infeasible.",
                    source=infeasible_empty_row.name,
                )
                return PresolveResult(
                    model=current_model,
                    reductions=tuple(reductions),
                    diagnostics=PresolveDiagnostics(
                        status=PresolveStatus.INFEASIBLE,
                        warnings=(warning,),
                        removed_rows=tuple(removed_rows),
                        fixed_variables=_fixed_variable_names(fixed_values),
                    ),
                    scaling=scaling,
                    changed=bool(reductions),
                    message=f"Empty row is infeasible: {infeasible_empty_row.name}.",
                    fixed_values=tuple(fixed_values),
                )

            column_diagnostics = inspect_empty_columns(current_model)
            if column_diagnostics.unbounded_variable is not None:
                return PresolveResult(
                    model=current_model,
                    reductions=tuple(reductions),
                    diagnostics=PresolveDiagnostics(
                        status=PresolveStatus.UNBOUNDED,
                        warnings=column_diagnostics.warnings,
                        removed_rows=tuple(removed_rows),
                        fixed_variables=_fixed_variable_names(fixed_values),
                    ),
                    scaling=scaling,
                    changed=bool(reductions),
                    message=(
                        "Empty column proves the model is unbounded: "
                        f"{column_diagnostics.unbounded_variable}."
                    ),
                    fixed_values=tuple(fixed_values),
                )

            pass_result = _run_structural_pass(current_model)
            if not pass_result.changed:
                if reductions:
                    return PresolveResult(
                        model=current_model,
                        reductions=tuple(reductions),
                        diagnostics=PresolveDiagnostics(
                            status=PresolveStatus.REDUCED,
                            warnings=column_diagnostics.warnings,
                            removed_rows=tuple(removed_rows),
                            fixed_variables=_fixed_variable_names(fixed_values),
                        ),
                        scaling=scaling,
                        changed=True,
                        message="Applied presolve reductions.",
                        fixed_values=tuple(fixed_values),
                    )

                return PresolveResult(
                    model=current_model,
                    reductions=(),
                    diagnostics=PresolveDiagnostics(
                        status=PresolveStatus.NO_CHANGE,
                        warnings=column_diagnostics.warnings,
                    ),
                    scaling=scaling,
                    changed=False,
                    message="No presolve reductions were applied.",
                )

            current_model = pass_result.model
            reductions.extend(pass_result.reductions)
            removed_rows.extend(pass_result.removed_rows)
            fixed_values.extend(pass_result.fixed_values)

        raise RuntimeError(
            "Repeated presolve exceeded the pass limit; this should be unreachable "
            "for the current structural reductions."
        )

    def apply(self, model: Model) -> Model:
        return self.run(model).model


def _run_structural_pass(model: Model) -> StructuralPassResult:
    reduced_constraints: list[Constraint] = []
    removed_rows: list[str] = []
    empty_row_reductions: list[ReductionRecord] = []
    for constraint in model.constraints:
        if _is_empty_row(constraint):
            removed_rows.append(constraint.name)
            empty_row_reductions.append(
                ReductionRecord(
                    reduction_type=ReductionType.EMPTY_ROW,
                    target=constraint.name,
                    description="Removed feasible empty row.",
                    data=reduction_data(
                        rhs=_clean_near_zero(constraint.rhs),
                        sense=constraint.sense.value,
                    ),
                )
            )
            continue
        reduced_constraints.append(constraint)

    reduced_model = model
    if removed_rows:
        reduced_model = Model(
            name=model.name,
            variables=list(model.variables),
            constraints=reduced_constraints,
            objective=model.objective,
        )

    fixed_elimination = eliminate_fixed_variables(reduced_model)
    reductions = tuple(empty_row_reductions) + fixed_elimination.reductions
    return StructuralPassResult(
        model=fixed_elimination.model,
        reductions=reductions,
        removed_rows=tuple(removed_rows),
        fixed_values=fixed_elimination.fixed_values,
        fixed_variables=fixed_elimination.fixed_variables,
        changed=bool(removed_rows or fixed_elimination.fixed_values),
    )


def _first_infeasible_empty_row(model: Model) -> Constraint | None:
    for constraint in model.constraints:
        if _is_empty_row(constraint) and not _empty_row_is_feasible(constraint):
            return constraint
    return None


def _fixed_variable_names(fixed_values: list[FixedValue]) -> tuple[str, ...]:
    return tuple(name for name, _ in fixed_values)


def _default_max_passes(model: Model) -> int:
    return len(model.variables) + len(model.constraints) + 1


def _is_empty_row(
    constraint: Constraint,
    tolerance: float = DEFAULT_TOLERANCE,
) -> bool:
    return all(abs(coefficient) <= tolerance for coefficient in constraint.coefficients.values())


def _empty_row_is_feasible(
    constraint: Constraint,
    tolerance: float = DEFAULT_TOLERANCE,
) -> bool:
    rhs = constraint.rhs
    if constraint.sense == ConstraintSense.LE:
        return rhs >= -tolerance
    if constraint.sense == ConstraintSense.GE:
        return rhs <= tolerance
    return abs(rhs) <= tolerance


def _clean_near_zero(
    value: float,
    tolerance: float = DEFAULT_TOLERANCE,
) -> float:
    if abs(value) <= tolerance:
        return 0.0
    return value
