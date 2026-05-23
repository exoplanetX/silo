# SILO Codex Task: Read-Only Callback Events

Task ID: 20260524-08-01

Slug: callback-events

Date: 2026-05-24

Type: implementation

Phase reference: Phase 6, cut generation and callbacks

Risk level: L1 controlled implementation

Git mode: push-on-success

Expected report: `tasks/reports/20260524-08-01_callback-events_report.md`

## Objective

Add read-only callback event records and hook-order tests using no-op callbacks, without
branch-and-bound integration.

## Context

Phase 6A design is recorded in `notes/18_cut_callback_boundary_design.md`.

Phase 6B added immutable cut candidate dataclasses.

Phase 6C added a deterministic cut pool.

Phase 6D added a no-op separator boundary.

The next approved Phase 6 step is to define callback observation records and no-op
callback dispatch behavior only. This task must not wire callbacks into branch-and-bound.

## Scope Lock

This task solves exactly one primary problem: define and test read-only callback event
records and deterministic no-op callback dispatch.

The implementation must:

- define callback hook identifiers for the Phase 6 design hook points;
- define an immutable callback event record with validation and defensive copies;
- define a callback protocol or equivalent interface;
- define a no-op callback that observes events without mutation;
- define a deterministic event dispatch helper that preserves event order and callback
  order;
- add tests for event validation, read-only observation, no-op behavior, and hook ordering.

## Allowed Changes

- `src/silo/cuts/callbacks.py`
- `src/silo/cuts/__init__.py`
- `tests/unit/test_cut_callbacks.py`
- `tasks/phases/phase_06_cut_callbacks.md`
- `tasks/reports/20260524-08-01_callback-events_report.md`
- this task file

## Forbidden Changes

- Do not modify branch-and-bound search logic.
- Do not modify MIP node ordering, pruning rules, branching rules, or incumbent updates.
- Do not integrate callbacks into branch-and-bound.
- Do not implement cut generation families.
- Do not implement separator behavior beyond existing no-op separator boundaries.
- Do not modify cut candidate, cut-pool, or separator semantics.
- Do not modify LP solvers or presolve.
- Do not modify CLI behavior.
- Do not modify JSON schemas.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not issue or execute another Phase 6 task.

## Stop Conditions

Stop and report instead of proceeding if:

- callback tests require branch-and-bound integration;
- callback tests require changing MIP solve behavior;
- callback tests require public CLI or JSON schema changes;
- callback event records require changing existing cut candidate, cut-pool, or separator
  semantics.

## Required Checks

Run:

```text
git status --short
pytest tests/unit/test_cut_callbacks.py
python scripts/check_quality.py
git diff --check
```

## Acceptance Criteria

- Callback hook identifiers cover the Phase 6 design hook points.
- Callback events are immutable at the dataclass boundary.
- Callback events defensively copy and expose immutable cut-id and diagnostics data.
- Invalid negative ids, negative depths, negative cut counts, blank string fields, and
  nonfinite numeric fields are rejected.
- `NoOpCallback` accepts callback events and returns no mutation or control signal.
- Callback dispatch preserves event order and callback order.
- Public exports from `silo.cuts` include the callback boundary API.
- All required checks pass.
- No branch-and-bound, cut-generation-family, CLI, schema, or example behavior is changed.

## Report Requirements

Create `tasks/reports/20260524-08-01_callback-events_report.md` with:

- task objective;
- files changed;
- implementation summary;
- tests added;
- checks run and results;
- deviations from scope, if any;
- Git status before and after;
- local commit hash, if created;
- push attempted or skipped;
- unresolved issues;
- next recommended atomic task.

## Final Response Requirements

Report:

- generated task path;
- risk classification;
- checks passed or failed;
- local commit hash, if created;
- whether push succeeded or failed.
