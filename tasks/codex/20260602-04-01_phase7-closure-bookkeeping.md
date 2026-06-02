# Codex Task: Phase 7 Closure Bookkeeping

## Task Metadata

Task ID: 20260602-04-01
Task slug: phase7-closure-bookkeeping
Task type: closure-bookkeeping
Risk level: L3 strategic
Related phase: Phase 7 / Decomposition Layer
Git mode: push-on-success
Expected report path: tasks/reports/20260602-04-01_phase7-closure-bookkeeping_report.md

## Objective

Mark Phase 7 complete for the current conservative decomposition boundary scope, without
starting Phase 8 or modifying solver behavior.

## User Approval

The user explicitly approved closing Phase 7 and explicitly did not approve starting
Phase 8.

## Context

The Phase 7 completion audit report:

```text
tasks/reports/20260602-03-01_phase7-completion-audit_report.md
```

recommends:

```text
ready_for_user_closure_review
```

The audit also notes that `ROADMAP.md` still contains a stale Phase 6 sentence saying
Phase 7 has not been started. This closure bookkeeping task may update that stale
bookkeeping text and mark Phase 7 complete for the current conservative decomposition
boundary scope.

## Scope Lock

This task is atomic.

Primary objective:

- Update closure bookkeeping only.

Allowed changes:

- `ROADMAP.md`
- `tasks/phases/phase_07_decomposition.md`
- `tasks/reports/20260602-04-01_phase7-closure-bookkeeping_report.md`

Supporting allowed change:

- `tasks/codex/20260602-04-01_phase7-closure-bookkeeping.md` may be committed as the
  issued task contract for this execution.

Forbidden changes:

- Do not modify solver source code under `src/`.
- Do not modify tests.
- Do not modify examples.
- Do not modify docs outside `ROADMAP.md`.
- Do not modify public CLI behavior.
- Do not modify JSON model schemas or solution schemas.
- Do not modify LP solver behavior.
- Do not modify MIP solver behavior.
- Do not modify presolve behavior.
- Do not modify cut or callback behavior.
- Do not implement any Phase 8 planning or implementation work.
- Do not mark Phase 8 as started, active, approved, or in progress.
- Do not issue or execute a Phase 8 task.
- Do not issue or execute another task.

## Required Bookkeeping

1. Read and confirm that
   `tasks/reports/20260602-03-01_phase7-completion-audit_report.md` recommends
   `ready_for_user_closure_review`.
2. Update `ROADMAP.md` to:
   - remove the stale Phase 6 claim that Phase 7 has not been started;
   - mark Phase 7 complete for the current conservative decomposition boundary scope;
   - avoid marking Phase 8 as started.
3. Update `tasks/phases/phase_07_decomposition.md` with a brief closure note.
4. Create the matching execution report.

## Required Checks

Run at least:

```bash
git status --short
Select-String -Path ROADMAP.md -Pattern "Phase 7 has not been started"
python scripts/check_quality.py
git diff --check
```

Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. The audit recommendation is confirmed as `ready_for_user_closure_review`.
2. Phase 7 is marked complete for the current conservative decomposition boundary scope.
3. Phase 8 is not started, planned, issued, or executed.
4. The stale Phase 6 sentence saying Phase 7 has not been started is removed.
5. No solver source code is changed.
6. No tests are changed.
7. No examples are changed.
8. No CLI behavior or JSON schemas are changed.
9. A report is created at the expected report path.
10. Required checks pass.

## Report Requirements

Create:

```text
tasks/reports/20260602-04-01_phase7-closure-bookkeeping_report.md
```

The report must include:

```text
Task ID:
Objective:
Risk and approval:
Audit recommendation confirmed:
Files changed:
Bookkeeping summary:
Checks run:
Results:
Git status before:
Git status after:
Local commit hash:
Push attempted:
Issues or conflicts:
Next recommended atomic task:
```

The report must explicitly state that Phase 8 was not started and that no solver source
code, tests, examples, CLI behavior, or JSON schemas were modified.

## Git Instructions

Git mode:

```text
push-on-success
```

After successful bookkeeping and checks:

```bash
git add ROADMAP.md tasks/phases/phase_07_decomposition.md tasks/codex/20260602-04-01_phase7-closure-bookkeeping.md tasks/reports/20260602-04-01_phase7-closure-bookkeeping_report.md
git commit -m "docs(decomposition): close phase 7 bookkeeping"
git push
```

If push fails, preserve the local commit and record the failure in the report and final
response.

## Final Response

When finished, report:

- whether Phase 7 was marked complete;
- whether Phase 8 was not started;
- files changed;
- checks run;
- commit hash;
- whether push succeeded.
