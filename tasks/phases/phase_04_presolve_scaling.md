# Phase 4: Presolve, Scaling, and Numerical Diagnostics

## Goal

Add conservative presolve and scaling diagnostics while preserving traceability from transformed models back to original models.

## Scope

Phase 4 is complete for the current conservative presolve/scaling scope. It covers traceable presolve results, empty-row and empty-column diagnostics, fixed-variable elimination, repeated-pass conservative reductions, original-space solution recovery, diagnostic-only coefficient-range checks, and CLI exposure.

The implementation follows the initial design in `notes/12_presolve_scaling_design.md`, the repeated-pass design in `notes/13_repeated_presolve_design.md`, and the completion summary in `notes/14_phase4_completion_summary.md`.

## Completed Work

Phase 4B added immutable presolve result, reduction, and diagnostics dataclasses plus the initial `Presolver` entry point.

Phase 4C adds conservative empty-row and empty-column diagnostics. Feasible empty rows may be removed with traceable records, while empty columns remain diagnostic-only except for simple unboundedness detection.

Phase 4D adds fixed-variable elimination with solution recovery. Fixed variables are substituted into constraints and the objective, then restored into recovered original-space solutions.

Phase 4E adds diagnostic-only coefficient-range checks for matrix coefficients, RHS values, and objective coefficients. Automatic scaling remains deferred.

Phase 4F exposes presolve diagnostics through `silo presolve`, and Phase 4G adds an explicit `silo solve --presolve` path that applies conservative presolve before solving without changing the default solve workflow.

Phase 4H records the repeated-pass presolve design for cases where one conservative reduction exposes another, such as fixed-variable elimination creating empty rows.

Phase 4I implements the first repeated-pass presolve loop. It composes existing feasible empty-row removal and fixed-variable elimination until no structural change remains, while keeping scaling diagnostics on the original submitted model.

Phase 4J recomputes recovered slack values from the original model constraints after presolve recovery. This keeps `silo solve --presolve` solution JSON in original constraint space when presolve removes rows.

Phase 4K adds checked-in JSON examples and regression coverage for fixed-variable recovery, repeated-pass empty-row removal, original-space slack recovery, and presolve-detected infeasibility.

Phase 4L adds a documented CLI regression checklist that fixes the current solve, presolve, and compare behavior for every checked-in JSON example before Phase 5 begins.

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
- `tests/regression/test_phase4_cli_regression_matrix.py`

## Algorithmic Requirements

Every transformation must be deterministic and reversible enough to reconstruct original-space solution values. Scaling should start as diagnostics unless transformation mapping is fully tested. Presolve should be skipped when a transformation cannot be recorded and reversed clearly.

## Testing Requirements

Maintain deterministic tests for fixed variables, empty-row diagnostics, empty-column diagnostics, repeated-pass behavior, scaling diagnostics, original-space recovery, presolve examples, and the Phase 4 CLI regression matrix.

## Do Not Do

Do not hide convention changes inside presolve. Do not implement aggressive reductions that are hard to explain or test. Automatic scaling, singleton-row bound tightening, general redundancy detection, MIP presolve, dual reductions, probing, and performance-oriented presolve remain future work.

## Acceptance Criteria

Presolve can simplify small models safely, report diagnostics, recover supported transformed solutions in original model space, and preserve public CLI behavior through the regression checklist.
