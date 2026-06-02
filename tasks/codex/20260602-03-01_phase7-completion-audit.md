# Codex Task: Phase 7 Completion Audit

## Task Metadata

Task ID: 20260602-03-01
Task slug: phase7-completion-audit
Task type: audit
Risk level: L0 safe
Related phase: Phase 7 / Decomposition Layer
Git mode: push-on-success
Expected report path: tasks/reports/20260602-03-01_phase7-completion-audit_report.md

## Objective

Audit whether the current conservative Phase 7 decomposition boundary scope is complete
enough for user closure review, without closing Phase 7 or starting Phase 8.

## Context

Phase 7A through Phase 7J added:

- the decomposition boundary design note;
- immutable master/subproblem context and result records;
- decomposition method, termination-reason, iteration-log, and run-summary records;
- boundary smoke tests for placeholder Benders and column-generation solvers;
- Benders cut candidate records;
- column candidate records and reduced-cost convention tests;
- a no-op decomposition driver;
- a toy fixture-only Benders driver;
- a toy fixture-only column-generation driver;
- checked-in educational examples for the toy drivers.

The latest report recommends a Phase 7 completion audit before considering Phase 7
closure.

## Scope Lock

This task is atomic.

Primary objective:

- Create a Phase 7 completion audit report and add a brief Phase 7K audit note.

Allowed changes:

- `tasks/phases/phase_07_decomposition.md`
- `tasks/reports/20260602-03-01_phase7-completion-audit_report.md`

Supporting allowed change:

- `tasks/codex/20260602-03-01_phase7-completion-audit.md` may be committed as the issued
  task contract for this execution.

Forbidden changes:

- Do not modify solver source code under `src/`.
- Do not modify tests.
- Do not modify examples.
- Do not modify docs.
- Do not modify `ROADMAP.md`.
- Do not modify public CLI behavior.
- Do not modify JSON model schemas or solution schemas.
- Do not modify LP solver behavior.
- Do not modify MIP solver behavior.
- Do not modify presolve behavior.
- Do not modify cut or callback behavior.
- Do not implement any decomposition behavior.
- Do not close Phase 7.
- Do not mark Phase 7 complete in `ROADMAP.md`.
- Do not start Phase 8.
- Do not issue or execute another task.

## Required Audit

Review:

- `ROADMAP.md`
- `tasks/phases/phase_07_decomposition.md`
- `notes/19_decomposition_boundary_design.md`
- recent Phase 7 task reports under `tasks/reports/`
- current decomposition source, tests, and examples by filename/content inspection as
  needed

The audit report must assess:

- whether every planned conservative Phase 7 item from the design-note candidate sequence
  has a matching completed task/report;
- whether Phase 7 preserved the dependency direction and lower-layer no-import boundary;
- whether public CLI behavior and JSON schemas remained unchanged;
- whether Phase 7 still avoids general Benders, general column generation, branch-and-price,
  LP/MIP solver calls from toy drivers, external solvers, and generated output artifacts;
- whether remaining issues should block user closure review or become future-phase work.

The audit report must include a clear recommendation using one of:

```text
ready_for_user_closure_review
needs_follow_up_before_closure_review
not_ready_for_closure_review
```

## Required Checks

Run at least:

```bash
git status --short
python examples/decomposition/toy_benders.py
python examples/decomposition/toy_column_generation.py
pytest tests/unit/test_decomposition_boundary_smoke.py tests/unit/test_decomposition_records.py tests/unit/test_decomposition_logging.py tests/unit/test_decomposition_benders_cut.py tests/unit/test_decomposition_column_candidate.py tests/unit/test_decomposition_noop_driver.py tests/unit/test_decomposition_toy_benders.py tests/unit/test_decomposition_toy_column_generation.py
python scripts/check_quality.py
git diff --check
```

Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. The audit report exists at the expected path.
2. The report maps Phase 7A through Phase 7J to completed files/reports.
3. The report states whether the conservative Phase 7 boundary is ready for user closure
   review.
4. The report records unresolved issues, if any, without fixing them inside this task.
5. `tasks/phases/phase_07_decomposition.md` receives only a brief Phase 7K audit note.
6. No solver source code is changed.
7. No tests, examples, docs, CLI behavior, JSON schemas, or roadmap status are changed.
8. Required checks pass.

## Report Requirements

Create:

```text
tasks/reports/20260602-03-01_phase7-completion-audit_report.md
```

The report must include:

```text
Task ID:
Objective:
Risk and execution:
Files changed:
Audit summary:
Completed Phase 7 scope:
Boundary preservation:
Checks run:
Results:
Recommendation:
Git status before:
Git status after:
Local commit hash:
Push attempted:
Issues or conflicts:
Next recommended atomic task:
```

## Git Instructions

Git mode:

```text
push-on-success
```

After successful audit and checks:

```bash
git add tasks/codex/20260602-03-01_phase7-completion-audit.md tasks/phases/phase_07_decomposition.md tasks/reports/20260602-03-01_phase7-completion-audit_report.md
git commit -m "docs(decomposition): audit phase 7 completion"
git push
```

If push fails, preserve the local commit and record the failure in the report and final
response.

## Final Response

When finished, report only:

- whether the Phase 7 completion audit was created;
- the audit recommendation;
- whether Phase 7 was not closed and Phase 8 was not started;
- whether checks passed;
- whether a local commit was created;
- whether push completed or failed;
- the next recommended atomic task.
