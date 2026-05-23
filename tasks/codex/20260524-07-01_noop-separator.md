# SILO Codex Task: No-Op Separator Boundary

Task ID: 20260524-07-01

Slug: noop-separator

Date: 2026-05-24

Type: implementation

Phase reference: Phase 6, cut generation and callbacks

Risk level: L1 controlled implementation

Git mode: push-on-success

Expected report: `tasks/reports/20260524-07-01_noop-separator_report.md`

## Objective

Add a no-op separator boundary and separator protocol tests without changing
branch-and-bound behavior.

## Context

Phase 6A design is recorded in `notes/18_cut_callback_boundary_design.md`.

Phase 6B added immutable cut candidate dataclasses.

Phase 6C added a deterministic cut pool with duplicate detection, activation, and
node-local scope clearing.

The next approved Phase 6 step is to define a separator boundary that can return
candidate cuts without mutating model, tree, LP, or cut-pool state. This task must use a
no-op separator only and must not integrate separators into branch-and-bound.

## Scope Lock

This task solves exactly one primary problem: define and test the minimal no-op separator
boundary.

The implementation must:

- define a read-only separator context suitable for later integration;
- define a separator protocol or equivalent interface;
- define a no-op separator that deterministically returns no candidate cuts;
- add a small helper that runs a separator and validates that it returns cut candidates;
- export the separator boundary from `silo.cuts`;
- test protocol conformance, deterministic no-op behavior, context validation, defensive
  context copying, and candidate-return validation.

## Allowed Changes

- `src/silo/cuts/separator.py`
- `src/silo/cuts/__init__.py`
- `tests/unit/test_separator.py`
- `tasks/phases/phase_06_cut_callbacks.md`
- `tasks/reports/20260524-07-01_noop-separator_report.md`
- this task file

## Forbidden Changes

- Do not modify branch-and-bound search logic.
- Do not modify MIP node ordering, pruning rules, branching rules, or incumbent updates.
- Do not integrate separators into branch-and-bound.
- Do not implement real cut families.
- Do not implement callbacks.
- Do not modify the cut-pool implementation except through read-only imports.
- Do not modify LP solvers or presolve.
- Do not modify CLI behavior.
- Do not modify JSON schemas.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not issue or execute another Phase 6 task.

## Stop Conditions

Stop and report instead of proceeding if:

- separator tests require branch-and-bound integration;
- separator tests require a real cut family;
- the boundary would require public CLI or JSON schema changes;
- the boundary would require changing cut candidate or cut-pool semantics.

## Required Checks

Run:

```text
git status --short
pytest tests/unit/test_separator.py
python scripts/check_quality.py
git diff --check
```

## Acceptance Criteria

- `NoOpSeparator` deterministically returns an empty tuple of candidate cuts.
- `SeparatorContext` is immutable at the dataclass boundary and defensively copies
  caller-provided mappings.
- The separator protocol can be satisfied by `NoOpSeparator` and by a small deterministic
  test separator.
- The separator runner rejects non-`CutCandidate` outputs.
- Public exports from `silo.cuts` include the separator boundary API.
- All required checks pass.
- No branch-and-bound, real separator, callback, CLI, schema, or example behavior is
  changed.

## Report Requirements

Create `tasks/reports/20260524-07-01_noop-separator_report.md` with:

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
