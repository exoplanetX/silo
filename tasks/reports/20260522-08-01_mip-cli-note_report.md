# MIP CLI Exposure Design Note Report

## Summary

Created the MIP CLI exposure design note in `notes/16_mip_cli_exposure_design.md`. The task is design-only: no CLI command, solver implementation, MIP algorithm, JSON model schema, or solution schema was changed.

The note recommends exposing MIP solving first through a separate `silo mip-solve MODEL_PATH` command so that existing LP-oriented `silo solve` behavior remains unambiguous.

## Candidate Commands Considered

- `silo mip-solve MODEL_PATH`
- `silo solve MODEL_PATH --mip`
- `silo solve MODEL_PATH --solver branch-and-bound`
- `silo mip MODEL_PATH`
- `silo mip solve MODEL_PATH`

The note rejects `--solver branch-and-bound` for the first version because `--solver` currently means LP backend selection for `silo solve`, while branch-and-bound is a MIP algorithm that uses LP backends internally.

## Recommended First Command

Recommended planned command:

```bash
silo mip-solve MODEL_PATH
```

Example planned command:

```bash
silo mip-solve examples/mip/binary_knapsack.json
```

This command is not implemented in this task.

## Recommended Flags

Recommended first-version flags:

- `--output` / `-o`
- `--lp-solver tableau|revised`
- `--node-limit N`

The note recommends `--lp-solver` instead of reusing `--solver` so users can distinguish the MIP algorithm from the LP relaxation backend.

## Files Changed

- `notes/16_mip_cli_exposure_design.md`
- `docs/mip_examples.md`
- `docs/cli_solve.md`
- `README.md`
- `ROADMAP.md`
- `tasks/phases/phase_05_branch_and_bound.md`
- `tasks/codex/20260522-08-01_mip-cli-note.md`
- `tasks/reports/20260522-08-01_mip-cli-note_report.md`

## Tests Run

- `python -m pip install -e ".[dev]"`
- `pytest`
- `python scripts/check_quality.py`
- `python -m silo.cli.main --version`
- `python -m silo.cli.main help`
- `python -m silo.cli.main solve examples/json/production.json`
- `python -m silo.cli.main compare examples/json/production.json`
- `silo --help`
- `silo --version`
- `silo solve examples/json/production.json`
- `silo compare examples/json/production.json`
- `git diff --check`

## Results

All required checks passed.

## Notes for Next Task

Phase 5H: implement `silo mip-solve` command.
