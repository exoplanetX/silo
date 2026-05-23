# SILO Codex Task: Optional No-Op Cut and Callback Integration

Task ID: 20260524-09-01

Slug: bnb-noop-cut-callbacks

Date: 2026-05-24

Type: implementation

Phase reference: Phase 6, cut generation and callbacks

Risk level: L2 high-risk

Review gate: must not execute in SILO-DOS Mode A without explicit user approval.

Git mode: push-on-success

Expected report: `tasks/reports/20260524-09-01_bnb-noop-cut-callbacks_report.md`

## Objective

Integrate optional no-op cut and callback components into branch-and-bound behind default
disabled behavior, with no-regression tests proving default solver behavior remains
unchanged.

## Context

Phase 6A design is recorded in `notes/18_cut_callback_boundary_design.md`.

Phase 6B added immutable cut candidate dataclasses.

Phase 6C added a deterministic cut pool.

Phase 6D added a no-op separator boundary.

Phase 6E added read-only callback event records and no-op callback dispatch.

The next Phase 6 design step is to add optional integration points to branch-and-bound
while preserving default pure branch-and-bound behavior. Because this touches MIP search
control flow, this is an L2 task and requires explicit approval before execution.

## Scope Lock

This task solves exactly one primary problem: add no-op optional cut and callback
integration points to branch-and-bound without changing default behavior.

The implementation must:

- keep `BranchAndBoundSolver()` default behavior unchanged;
- keep node ordering, branching rules, pruning rules, incumbent updates, and CLI output
  unchanged when no cut or callback components are provided;
- accept optional no-op separator and callback components through a narrow constructor
  boundary or internal configuration object;
- dispatch read-only callback events only when callback components are explicitly
  provided;
- allow a no-op separator path to be exercised without adding cuts to LP relaxations;
- add deterministic no-regression tests that compare default behavior with explicitly
  no-op cut/callback components;
- avoid any real cut generation, cut materialization, or branch-and-cut behavior.

## Allowed Changes

- `src/silo/mip/branch_and_bound.py`
- `tests/unit/test_mip_cut_callback_integration.py`
- `tasks/phases/phase_06_cut_callbacks.md`
- `tasks/reports/20260524-09-01_bnb-noop-cut-callbacks_report.md`
- this task file

If a narrowly scoped import/export change is required for the existing cut API, it may
also touch:

- `src/silo/cuts/__init__.py`

## Forbidden Changes

- Do not modify branch-and-bound node ordering.
- Do not modify pruning rules.
- Do not modify branching variable selection.
- Do not modify incumbent comparison or incumbent update rules.
- Do not materialize cuts into LP relaxations.
- Do not implement real cut families.
- Do not implement lazy constraints.
- Do not change LP solver behavior.
- Do not change presolve behavior.
- Do not modify CLI behavior.
- Do not modify JSON schemas.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not issue or execute another Phase 6 task.

## Stop Conditions

Stop and report instead of proceeding if:

- default branch-and-bound behavior changes in any existing MIP test;
- no-op cut/callback tests require changing node ordering, pruning, branching, or
  incumbent logic;
- implementation requires materializing cuts into LP relaxations;
- implementation requires CLI or JSON schema changes;
- implementation requires a broader callback mutation capability.

## Required Checks

Run:

```text
git status --short
pytest tests/unit/test_mip_cut_callback_integration.py
pytest tests/unit/test_binary_branch_and_bound.py tests/unit/test_integer_branch_and_bound.py tests/unit/test_mip_logging.py
python scripts/check_quality.py
git diff --check
```

## Acceptance Criteria

- `BranchAndBoundSolver()` default construction produces the same results and logs as
  before this task.
- Explicit no-op separator and no-op callback components do not change solution status,
  objective value, primal values, node counts, pruning counts, node creation counts, or
  node-log ordering on deterministic fixtures.
- Read-only callback events can be observed in deterministic hook order when callbacks
  are explicitly provided.
- No cuts are materialized into LP relaxations.
- No CLI behavior changes.
- No JSON schema changes.
- All required checks pass.

## Report Requirements

Create `tasks/reports/20260524-09-01_bnb-noop-cut-callbacks_report.md` with:

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

- task path;
- risk classification;
- whether explicit approval was present;
- checks passed or failed;
- local commit hash, if created;
- whether push succeeded or failed.
