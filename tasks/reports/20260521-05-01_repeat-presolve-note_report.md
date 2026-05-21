# Repeated-Pass Presolve Design Note Report

## Summary

Created a design-only repeated-pass presolve note for the next Phase 4 step. No presolve, CLI, solver, JSON reader, or solution writer implementation files were changed.

## Files Changed

- `notes/13_repeated_presolve_design.md`
- `docs/lp_solver.md`
- `tasks/phases/phase_04_presolve_scaling.md`

## Main Design Decisions

- Repeated-pass presolve should let existing conservative reductions compose without adding aggressive reductions.
- Scaling diagnostics should initially describe the original submitted model only.
- Structural passes should repeat only when a feasible empty row or fixed variable is removed.
- Diagnostic-only warnings should not trigger another pass.
- A `number_of_variables + number_of_constraints + 1` pass limit is recommended as a safety guard.
- Reduction records should be ordered by pass, then by empty rows in constraint order and fixed variables in variable order.
- Future recovery should eventually apply inverse transformations in reverse reduction order and may need original-space slack recomputation.

## Proposed Implementation Phases

- Phase 4H: repeated-pass presolve design note.
- Phase 4I: repeated-pass presolver loop with empty-row-after-fixed-variable cases.
- Phase 4J: original-space slack recomputation after presolve recovery.
- Phase 4K: repeated-pass CLI regression examples.

## Tests Run

- `python -m pip install -e ".[dev]"`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `python -m silo.cli.main solve examples/json/production.json --presolve`
- `python -m silo.cli.main presolve examples/json/production.json`
- `python -m silo.cli.main compare examples/json/production.json`
- `silo --help`
- `silo --version`
- `silo solve examples/json/production.json --presolve`
- `silo presolve examples/json/production.json`
- `silo compare examples/json/production.json`

## Results

All checks passed. The task is documentation-only and did not change executable behavior.

## Notes for Next Task

Phase 4I: implement repeated-pass presolver loop for empty-row-after-fixed-variable cases.
