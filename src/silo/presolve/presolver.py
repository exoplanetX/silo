from dataclasses import dataclass

from silo.core.model import Model
from silo.presolve.diagnostics import PresolveDiagnostics, PresolveStatus
from silo.presolve.reductions import ReductionRecord
from silo.presolve.scaling import ScalingDiagnostics, empty_scaling_diagnostics


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
        return PresolveResult(
            model=model,
            reductions=(),
            diagnostics=PresolveDiagnostics(status=PresolveStatus.NO_CHANGE),
            scaling=empty_scaling_diagnostics(),
            changed=False,
            message="No presolve reductions were applied.",
        )

    def apply(self, model: Model) -> Model:
        return model
