# Phase 4: Presolve, Scaling, and Numerical Diagnostics

## Goal

Add conservative presolve and scaling diagnostics while preserving traceability from transformed models back to original models.

## Scope

This phase covers fixed-variable elimination, simple bound tightening, row reduction, empty-row detection, and coefficient-range diagnostics.

The implementation should follow the initial design in `notes/12_presolve_scaling_design.md`. Early tasks should prioritize transformation traceability, original-space solution reconstruction, and diagnostic-only scaling before any aggressive reductions are considered.

Phase 4B starts with immutable presolve result, reduction, and diagnostics dataclasses plus a no-op `Presolver` entry point. Actual reductions and solver integration remain deferred to later tasks.

Phase 4C adds conservative empty-row and empty-column diagnostics. Feasible empty rows may be removed with traceable records, while empty columns remain diagnostic-only except for simple unboundedness detection.

Phase 4D adds fixed-variable elimination with solution recovery. Fixed variables are substituted into constraints and the objective, then restored into recovered original-space solutions.

Phase 4E adds diagnostic-only coefficient-range checks for matrix coefficients, RHS values, and objective coefficients. Automatic scaling remains deferred.

## Expected Files

- `src/silo/presolve/presolver.py`
- `src/silo/presolve/bound_tightening.py`
- `src/silo/presolve/row_reduction.py`
- `src/silo/presolve/fixed_variable.py`
- `src/silo/presolve/scaling.py`
- `src/silo/presolve/diagnostics.py`
- `src/silo/presolve/reductions.py`
- `src/silo/presolve/column_diagnostics.py`
- `tests/unit/test_presolve.py`
- `tests/unit/test_presolve_core.py`
- `tests/unit/test_empty_row_diagnostics.py`
- `tests/unit/test_empty_column_diagnostics.py`
- `tests/unit/test_fixed_variable_presolve.py`
- `tests/unit/test_presolve_scaling_integration.py`
- `tests/unit/test_scaling_diagnostics.py`

## Algorithmic Requirements

Every transformation must be deterministic and reversible enough to reconstruct original-space solution values. Scaling should start as diagnostics unless transformation mapping is fully tested. Presolve should be skipped when a transformation cannot be recorded and reversed clearly.

## Testing Requirements

Add tests for fixed variables, invalid rows, redundant simple rows, tightened-bound diagnostics, core dataclass defaults, no-op behavior, coefficient-range diagnostics, scaling diagnostics defaults, and reconstruction of original variable values.

## Do Not Do

Do not hide convention changes inside presolve. Do not implement aggressive reductions that are hard to explain or test.

## Acceptance Criteria

Presolve can simplify small models safely and report diagnostics without changing solver-facing conventions silently.
