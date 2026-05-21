# Codex Task 20260521-07-01: Recover Original-Space Slacks

## Task Metadata

Task file:

```text
tasks/codex/20260521-07-01_recover-slacks.md
```

Execution report file:

```text
tasks/reports/20260521-07-01_recover-slacks_report.md
```

Recommended local commit message:

```text
Recompute original slacks after presolve
```

## Source Note

This task file was empty when execution began. The task was inferred from the Phase 4J notes in `notes/13_repeated_presolve_design.md` and the previous execution report:

```text
Phase 4J: original-space slack recomputation after presolve recovery.
```

## Goal

Update presolve solution recovery so that recovered solutions report slack values in original model space.

When `silo solve MODEL_PATH --presolve` solves a presolved model, rows removed during presolve do not appear in solver-space slack output. Recovery should recompute slack values from the original model and recovered primal values so solution JSON remains expressed in original constraint names.

## Scope

Implement only original-space slack recomputation after presolve recovery.

Do not add new presolve reductions.
Do not change tableau or revised simplex algorithms.
Do not change solution JSON schema.
Do not change default solve behavior without `--presolve`.

## Expected Behavior

Recovered slack values should follow existing solver conventions:

```text
<= row: rhs - activity
>= row: activity - rhs
= row: rhs - activity
```

Rows removed by presolve should appear in recovered `slack_values`.
Transformed-only solver rows should not leak into recovered `slack_values` when the original model context is available.
Fixed-variable recovery should continue to restore fixed variable primal values, basis status, and zero reduced costs.

## Checks

Run targeted tests, full `pytest`, quality checks, and CLI smoke commands for `solve --presolve`.
