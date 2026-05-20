"""Presolve transformations and diagnostics."""

from silo.presolve.diagnostics import PresolveDiagnostics, PresolveStatus, PresolveWarning
from silo.presolve.presolver import Presolver, PresolveResult
from silo.presolve.reductions import ReductionRecord, ReductionType, reduction_data
from silo.presolve.scaling import ScalingDiagnostics, empty_scaling_diagnostics

__all__ = [
    "PresolveDiagnostics",
    "PresolveResult",
    "PresolveStatus",
    "PresolveWarning",
    "Presolver",
    "ReductionRecord",
    "ReductionType",
    "ScalingDiagnostics",
    "empty_scaling_diagnostics",
    "reduction_data",
]
