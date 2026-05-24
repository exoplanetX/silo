# Codex Task: Phase 6 Closure Bookkeeping

## Task Metadata

Task ID: 20260524-13-01
Task slug: phase6-closure-bookkeeping
Task type: process-bookkeeping
Risk level: L3 strategic
Related phase: Phase 6 / Cut Generation and Callbacks
Git mode: push-on-success
Expected report path: tasks/reports/20260524-13-01_phase6-closure-bookkeeping_report.md

## Objective

Close Phase 6 in project bookkeeping after explicit user approval by updating only the
roadmap status and the Phase 6 phase record.

Do not start Phase 7, issue Phase 7 work, or modify solver behavior.

## Context

The Phase 6 completion audit in
`tasks/reports/20260524-11-01_phase6-completion-audit_report.md` recommended:

```text
ready_for_user_closure_review
```

The audit found no blocking gaps within the conservative Phase 6 cut/callback boundary
scope. It preserved the non-goals: real cut-family algorithms, cut materialization into LP
relaxations, branch-and-cut performance claims, lazy constraints, arbitrary mutation
callbacks, commercial solver callback emulation, external solver calls, parallel tree
search, large benchmarks, automatic MIP presolve, public CLI behavior changes, JSON
schema changes, and Phase 7 decomposition work.

The user has explicitly approved issuing and executing one L3 Phase 6 closure bookkeeping
task, limited to updating `ROADMAP.md`, `tasks/phases/phase_06_cut_callbacks.md`, and the
matching task/report files. Therefore this task is only closure bookkeeping. It must not
implement, scope, issue, or start Phase 7 work.

Relevant files:

- `ROADMAP.md`
- `tasks/phases/phase_06_cut_callbacks.md`
- `tasks/reports/20260524-11-01_phase6-completion-audit_report.md`

## Scope Lock

This task is atomic.

Primary objective:

- Mark Phase 6 as closed/complete for the current conservative cut/callback boundary
  scope in the roadmap and Phase 6 phase record.

Allowed changes:

- `ROADMAP.md`
- `tasks/phases/phase_06_cut_callbacks.md`
- `tasks/reports/20260524-13-01_phase6-closure-bookkeeping_report.md`

Supporting allowed change:

- `tasks/codex/20260524-13-01_phase6-closure-bookkeeping.md` may be committed as the
  issued task contract for this execution.

Forbidden changes:

- Do not modify solver source code.
- Do not modify tests.
- Do not modify examples.
- Do not modify CLI behavior.
- Do not modify JSON model schemas or solution schemas.
- Do not modify docs outside `ROADMAP.md` and
  `tasks/phases/phase_06_cut_callbacks.md`.
- Do not modify notes.
- Do not issue a Phase 7 task.
- Do not create a Phase 7 report.
- Do not modify Phase 7 source, tests, docs, examples, or implementation plans.
- Do not mark Phase 7 as started, active, approved, or in progress.
- Do not change Phase 7 scope or acceptance criteria.
- Do not modify existing files under `tasks/codex/`.
- Do not add generated output files to git.

## Required Bookkeeping Content

Update `ROADMAP.md` only to reflect that Phase 6 is complete for the current conservative
cut/callback boundary scope. The status should make clear that real cut families, cut
materialization into LP relaxations, lazy constraints, mutation callbacks, public
CLI/schema exposure, branch-and-cut performance, and decomposition remain future work.

If needed for roadmap consistency, remove stale wording that says Phase 6 has not been
started. Do not mark Phase 7 as started.

Update `tasks/phases/phase_06_cut_callbacks.md` only with a brief closure note that:

1. records explicit user approval to close Phase 6;
2. points to the completion audit report;
3. states that Phase 6 is closed for the current conservative cut/callback boundary scope;
4. states that Phase 7 was not started by this bookkeeping task.

Do not rewrite the Phase 6 history. Do not expand the Phase 6 scope. Do not edit Phase 7
content.

## Stop Conditions

Stop and report instead of proceeding if:

- closing Phase 6 would require solver behavior changes;
- closing Phase 6 would require test or example changes;
- closing Phase 6 would require modifying Phase 7 scope, implementation, or task files;
- the repository state contains unrelated dirty changes that make the bookkeeping scope
  ambiguous;
- the audit report cannot be found or does not recommend `ready_for_user_closure_review`;
- user approval to close Phase 6 is no longer clear in the active instruction.

## Required Checks

Run at least:

```bash
git status --short
git diff --check
```

Do not run the full solver test suite unless executable files are changed unexpectedly.
Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. `ROADMAP.md` marks Phase 6 complete for the current conservative cut/callback boundary
   scope.
2. `ROADMAP.md` does not mark Phase 7 as started, active, approved, or in progress.
3. `tasks/phases/phase_06_cut_callbacks.md` records a brief closure note with the audit
   report reference and user approval.
4. No solver source code is modified.
5. No tests are modified.
6. No examples are modified.
7. No CLI behavior or JSON schemas are modified.
8. No Phase 7 task is issued or started.
9. A report is created at the expected report path.
10. `git diff --check` passes.

## Report Requirements

Create:

```text
tasks/reports/20260524-13-01_phase6-closure-bookkeeping_report.md
```

The report must include:

```text
Task ID:
Objective:
Risk and approval:
Files changed:
Bookkeeping updates:
Checks run:
Results:
Git status before:
Git status after:
Local commit hash:
Push attempted:
Issues or conflicts:
Next recommended atomic task:
```

The report must explicitly state that Phase 7 was not started and no Phase 7 task was
issued.

## Git Instructions

Git mode:

```text
push-on-success
```

After successful bookkeeping updates and checks:

```bash
git add tasks/codex/20260524-13-01_phase6-closure-bookkeeping.md ROADMAP.md tasks/phases/phase_06_cut_callbacks.md tasks/reports/20260524-13-01_phase6-closure-bookkeeping_report.md
git commit -m "docs(tasks): close Phase 6 bookkeeping"
git push
```

If push fails, preserve the local commit and record the failure in the report and final
response.

## Final Response

When finished, report only:

- whether Phase 6 closure bookkeeping was completed;
- whether `ROADMAP.md` marks Phase 6 complete;
- whether the Phase 6 phase record was updated;
- whether Phase 7 was not started;
- whether checks passed;
- whether a local commit was created;
- whether push completed or failed;
- the next recommended atomic task.
