# Phase 4: Presolve, Scaling, and Numerical Diagnostics

## Goal

Add conservative presolve and scaling diagnostics while preserving traceability from transformed models back to original models.

## Scope

This phase covers fixed-variable elimination, simple bound tightening, row reduction, empty-row detection, and coefficient-range diagnostics.

The implementation should follow the initial design in `notes/12_presolve_scaling_design.md`. Early tasks should prioritize transformation traceability, original-space solution reconstruction, and diagnostic-only scaling before any aggressive reductions are considered.

Phase 4B starts with immutable presolve result, reduction, and diagnostics dataclasses plus a no-op `Presolver` entry point. Actual reductions and solver integration remain deferred to later tasks.

## Expected Files

- `src/silo/presolve/presolver.py`
- `src/silo/presolve/bound_tightening.py`
- `src/silo/presolve/row_reduction.py`
- `src/silo/presolve/fixed_variable.py`
- `src/silo/presolve/scaling.py`
- `src/silo/presolve/diagnostics.py`
- `src/silo/presolve/reductions.py`
- `tests/unit/test_presolve.py`
- `tests/unit/test_presolve_core.py`
- `tests/unit/test_scaling_diagnostics.py`

## Algorithmic Requirements

Every transformation must be deterministic and reversible enough to reconstruct original-space solution values. Scaling should start as diagnostics unless transformation mapping is fully tested. Presolve should be skipped when a transformation cannot be recorded and reversed clearly.

## Testing Requirements

Add tests for fixed variables, invalid rows, redundant simple rows, tightened-bound diagnostics, core dataclass defaults, no-op behavior, coefficient-range diagnostics, scaling diagnostics defaults, and reconstruction of original variable values.

## Do Not Do

Do not hide convention changes inside presolve. Do not implement aggressive reductions that are hard to explain or test.

## Acceptance Criteria

Presolve can simplify small models safely and report diagnostics without changing solver-facing conventions silently.
