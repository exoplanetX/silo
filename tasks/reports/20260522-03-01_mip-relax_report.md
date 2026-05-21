# MIP Relaxation Builder Report

## Summary

Implemented the Phase 5B MIP-to-LP relaxation builder. The change adds an internal Python API that converts the first supported MIP class into a continuous LP model accepted by existing SILO LP backends. No branch-and-bound search loop, CLI behavior, JSON schema, solution schema, tableau simplex behavior, revised simplex behavior, or presolve behavior was changed.

## Files Changed

- Added `src/silo/mip/relaxation.py`.
- Updated `src/silo/mip/__init__.py` to export the relaxation API.
- Added `tests/unit/test_mip_relaxation.py`.
- Updated `docs/lp_solver.md` with the MIP relaxation boundary.
- Updated `tasks/phases/phase_05_branch_and_bound.md` to mark Phase 5B relaxation-builder scope.
- Added `tasks/codex/20260522-03-01_mip-relax.md`.
- Added `tasks/reports/20260522-03-01_mip-relax_report.md`.

## Main Implementation Decisions

- `build_lp_relaxation()` returns a `MIPRelaxation` dataclass containing the generated LP model, generated bound row names, and generated branching row names.
- Binary variables are relaxed to continuous variables with explicit `x <= 1` rows.
- Bounded nonnegative integer variables are relaxed to continuous variables with explicit `x <= U` rows.
- Local `BranchingConstraint` records are appended as deterministic generated rows.
- Generated rows use the reserved `__mip_` prefix, and user constraints using that prefix are rejected to avoid collisions.
- The original model is copied into a relaxation model and is not mutated.

## Supported Scope

The builder supports maximization models with continuous nonnegative variables without finite upper bounds, binary variables with `[0, 1]` bounds, and bounded nonnegative integer variables. It rejects minimization, nonzero lower bounds, finite upper bounds on continuous variables, malformed binary bounds, unbounded integer variables, branching constraints on unknown variables, branching constraints on continuous variables, invalid branching senses, and reserved-prefix row names.

## Tests Added

Added 14 deterministic unit tests covering binary relaxation, bounded integer relaxation, original-model immutability, objective and constraint preservation, branching-row generation, standard-form compatibility, and unsupported-case rejection.

## Tests Run

- `pytest tests/unit/test_mip_relaxation.py`
- `pytest`
- `python scripts/check_quality.py`
- `python -m pip install -e ".[dev]"`
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

All checks passed. The full test suite reports 312 passing tests. `python scripts/check_quality.py` also reports 312 passing tests and all checks passed. Module and console CLI smoke commands returned expected help, version, solve, presolve, and compare outputs.

## Notes for Next Task

Phase 5C: add MIP node, branching constraint, node log, and incumbent dataclasses.
