"""Presolve transformations and diagnostics."""

from silo.presolve.diagnostics import PresolveDiagnostics, PresolveStatus, PresolveWarning
from silo.presolve.fixed_variable import FixedVariableElimination, eliminate_fixed_variables
from silo.presolve.presolver import Presolver, PresolveResult
from silo.presolve.reductions import ReductionRecord, ReductionType, reduction_data
from silo.presolve.scaling import ScalingDiagnostics, empty_scaling_diagnostics

__all__ = [
    "FixedVariableElimination",
    "PresolveDiagnostics",
    "PresolveResult",
    "PresolveStatus",
    "PresolveWarning",
    "Presolver",
    "ReductionRecord",
    "ReductionType",
    "ScalingDiagnostics",
    "eliminate_fixed_variables",
    "empty_scaling_diagnostics",
    "reduction_data",
]
