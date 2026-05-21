# Branch-and-Bound Design Note Report

## Summary

Drafted the Phase 5 branch-and-bound design note. The task remained design-only: no branch-and-bound implementation, MIP node classes, CLI behavior, JSON schema, solver behavior, or presolve behavior was changed.

## Files Changed

- Added `notes/15_branch_and_bound_design.md`.
- Added `tasks/reports/20260522-02-01_bnb-note_report.md`.
- Added the new issued task file `tasks/codex/20260522-02-01_bnb-note.md`.
- Updated `tasks/phases/phase_05_branch_and_bound.md` to link the design note and align expected files/tests.
- Updated `ROADMAP.md` to mark Phase 5 as the next phase with the design note drafted.
- Updated `README.md` with one brief pointer to the Phase 5 design note.

## Main Design Decisions

- The first MIP layer should be small, deterministic, educational, pure branch-and-bound, and LP-relaxation based.
- The LP relaxation builder must respect the current LP solver boundary: continuous maximization LPs, nonnegative variables, and no direct finite upper bounds.
- Binary and bounded integer upper bounds should be converted into explicit linear rows before calling a simplex backend.
- Node selection should initially use deterministic depth-first search.
- Branching should use the first fractional integer variable in original model order.
- MIP-specific diagnostics should live in a future detailed `BranchAndBoundResult` rather than changing the existing `Solution` schema.

## First Supported MIP Class

The design note defines the first supported class as maximization models with linear rows, nonnegative continuous variables without finite upper bounds, binary variables, and bounded nonnegative integer variables. Integer and binary finite bounds are represented in LP relaxations through explicit rows such as `x <= 1` or `x <= U`.

## Implementation Breakdown

The note breaks Phase 5 into:

- Phase 5A: branch-and-bound design note.
- Phase 5B: MIP-to-LP relaxation builder.
- Phase 5C: MIP node, branching constraint, node log, and incumbent dataclasses.
- Phase 5D: pure depth-first branch-and-bound for binary variables.
- Phase 5E: bounded nonnegative integer variables.
- Phase 5F: CLI naming discussion.
- Phase 5G: MIP regression examples and documentation.

## Tests Run

- `python -m pip install -e ".[dev]"`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `python -m silo.cli.main solve examples/json/production.json`
- `python -m silo.cli.main solve examples/json/production.json --presolve`
- `python -m silo.cli.main presolve examples/json/production.json`
- `python -m silo.cli.main compare examples/json/production.json`
- `silo --help`
- `silo --version`
- `silo solve examples/json/production.json`
- `silo solve examples/json/production.json --presolve`
- `silo presolve examples/json/production.json`
- `silo compare examples/json/production.json`
- `git diff --check`

## Results

All checks passed. `pytest` and `python scripts/check_quality.py` each reported 298 passing tests. CLI module and console entry points returned expected help, version, solve, presolve, and compare outputs.

## Notes for Next Task

Phase 5B: implement MIP-to-LP relaxation builder.
