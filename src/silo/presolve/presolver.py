from dataclasses import dataclass

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense
from silo.core.model import Model
from silo.core.solution import Solution
from silo.presolve.column_diagnostics import inspect_empty_columns
from silo.presolve.diagnostics import PresolveDiagnostics, PresolveStatus, PresolveWarning
from silo.presolve.fixed_variable import FixedValue, eliminate_fixed_variables
from silo.presolve.reductions import ReductionRecord, ReductionType, reduction_data
from silo.presolve.scaling import ScalingDiagnostics, empty_scaling_diagnostics
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


class Presolver:
    def run(self, model: Model) -> PresolveResult:
        model.validate()
        scaling = empty_scaling_diagnostics()

        for constraint in model.constraints:
            if _is_empty_row(constraint) and not _empty_row_is_feasible(constraint):
                warning = PresolveWarning(
                    code="empty_row_infeasible",
                    message="Empty row is infeasible.",
                    source=constraint.name,
                )
                return PresolveResult(
                    model=model,
                    reductions=(),
                    diagnostics=PresolveDiagnostics(
                        status=PresolveStatus.INFEASIBLE,
                        warnings=(warning,),
                    ),
                    scaling=scaling,
                    changed=False,
                    message=f"Empty row is infeasible: {constraint.name}.",
                )

        column_diagnostics = inspect_empty_columns(model)
        if column_diagnostics.unbounded_variable is not None:
            return PresolveResult(
                model=model,
                reductions=(),
                diagnostics=PresolveDiagnostics(
                    status=PresolveStatus.UNBOUNDED,
                    warnings=column_diagnostics.warnings,
                ),
                scaling=scaling,
                changed=False,
                message=(
                    "Empty column proves the model is unbounded: "
                    f"{column_diagnostics.unbounded_variable}."
                ),
            )

        presolved_model = model
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

        if removed_rows:
            presolved_model = Model(
                name=model.name,
                variables=list(model.variables),
                constraints=reduced_constraints,
                objective=model.objective,
            )

        fixed_elimination = eliminate_fixed_variables(presolved_model)
        if removed_rows or fixed_elimination.fixed_values:
            reductions = tuple(empty_row_reductions) + fixed_elimination.reductions
            return PresolveResult(
                model=fixed_elimination.model,
                reductions=reductions,
                diagnostics=PresolveDiagnostics(
                    status=PresolveStatus.REDUCED,
                    warnings=column_diagnostics.warnings,
                    removed_rows=tuple(removed_rows),
                    fixed_variables=fixed_elimination.fixed_variables,
                ),
                scaling=scaling,
                changed=True,
                message="Applied presolve reductions.",
                fixed_values=fixed_elimination.fixed_values,
            )

        return PresolveResult(
            model=model,
            reductions=(),
            diagnostics=PresolveDiagnostics(
                status=PresolveStatus.NO_CHANGE,
                warnings=column_diagnostics.warnings,
            ),
            scaling=scaling,
            changed=False,
            message="No presolve reductions were applied.",
        )

    def apply(self, model: Model) -> Model:
        return self.run(model).model


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
