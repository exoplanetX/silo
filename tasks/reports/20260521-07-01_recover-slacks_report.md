# Recover Original-Space Slacks Report

## Summary

Implemented original-space slack recomputation during presolve solution recovery. Recovered solutions now report slack values for the original model constraints after fixed-variable and repeated-pass presolve reductions.

## Task File Note

`tasks/codex/20260521-07-01_recover-slacks.md` was empty when execution began. The implementation followed the Phase 4J direction recorded in the repeated-pass design note and previous report: original-space slack recomputation after presolve recovery.

## Recovery Behavior

`PresolveResult` now keeps an optional `original_model` context. `Presolver.run()` sets this context to the submitted model. During `recover_solution()`, fixed variable primal values are restored first; then slack values are recomputed from the original constraints and recovered primal values when the original model context is available.

Slack conventions match the native solver convention:

```text
<= row: rhs - activity
>= row: activity - rhs
= row: rhs - activity
```

If a manually constructed `PresolveResult` has no original model context, recovery preserves solver-provided slack values for backward compatibility.

## Files Changed

- `src/silo/presolve/presolver.py`
- `tests/unit/test_presolve_recovery_slacks.py`
- `tests/unit/test_repeated_presolve.py`
- `tests/unit/test_cli_solve_presolve.py`
- `tests/unit/test_presolve_core.py`
- `docs/lp_solver.md`
- `docs/cli_solve.md`
- `tasks/phases/phase_04_presolve_scaling.md`
- `tasks/codex/20260521-07-01_recover-slacks.md`
- `tasks/reports/20260521-07-01_recover-slacks_report.md`

## Tests Added

- Recovery recomputes slacks for original rows removed by repeated-pass presolve.
- Recovered slack output uses original constraint names only when original context is available.
- Manual `PresolveResult` without original model context preserves solver-space slacks.
- CLI `solve --presolve` includes slack values for rows removed by presolve.

## Tests Run

```text
pytest tests/unit/test_presolve_recovery_slacks.py tests/unit/test_repeated_presolve.py tests/unit/test_cli_solve_presolve.py tests/unit/test_presolve_core.py tests/unit/test_fixed_variable_presolve.py
python -m pip install -e ".[dev]"
pytest
python scripts/check_quality.py
python -m silo.cli.main --version
python -m silo.cli.main help
python -m silo.cli.main solve examples/json/production.json --presolve
python -m silo.cli.main presolve examples/json/production.json
python -m silo.cli.main compare examples/json/production.json
silo --version
silo --help
silo solve examples/json/production.json --presolve
silo presolve examples/json/production.json
silo compare examples/json/production.json
git diff --check
```

## Results

Targeted tests passed. Editable dev install completed successfully. Full `pytest` passed with 217 tests. `python scripts/check_quality.py` passed. Module and console CLI smoke commands completed successfully. `git diff --check` reported no whitespace issues.

## Notes for Next Task

Consider adding repeated-pass CLI fixture examples in Phase 4K so original-space recovery behavior is covered by small checked-in JSON models.
