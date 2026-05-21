from dataclasses import dataclass

from silo.core.constraint import Constraint
from silo.core.enums import ConstraintSense
from silo.core.model import Model
from silo.presolve.column_diagnostics import inspect_empty_columns
from silo.presolve.diagnostics import PresolveDiagnostics, PresolveStatus, PresolveWarning
from silo.presolve.reductions import ReductionRecord, ReductionType, reduction_data
from silo.presolve.scaling import ScalingDiagnostics, empty_scaling_diagnostics
from silo.utils.numerics import DEFAULT_TOLERANCE


@dataclass(frozen=True)
class PresolveResult:
    model: Model
    reductions: tuple[ReductionRecord, ...]
    diagnostics: PresolveDiagnostics
    scaling: ScalingDiagnostics
    changed: bool = False
    message: str = ""


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

        reduced_constraints: list[Constraint] = []
        removed_rows: list[str] = []
        reductions: list[ReductionRecord] = []
        for constraint in model.constraints:
            if _is_empty_row(constraint):
                removed_rows.append(constraint.name)
                reductions.append(
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
            reduced_model = Model(
                name=model.name,
                variables=list(model.variables),
                constraints=reduced_constraints,
                objective=model.objective,
            )
            return PresolveResult(
                model=reduced_model,
                reductions=tuple(reductions),
                diagnostics=PresolveDiagnostics(
                    status=PresolveStatus.REDUCED,
                    warnings=column_diagnostics.warnings,
                    removed_rows=tuple(removed_rows),
                ),
                scaling=scaling,
                changed=True,
                message="Removed feasible empty rows.",
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
