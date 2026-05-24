# Codex Task: Audit Phase 6 Completion

## Task Metadata

Task ID: 20260524-11-01
Task slug: phase6-completion-audit
Task type: process-audit
Risk level: L0 safe
Related phase: Phase 6 / Cut Generation and Callbacks
Git mode: push-on-success
Expected report path: tasks/reports/20260524-11-01_phase6-completion-audit_report.md

## Objective

Audit the current Phase 6 cut/callback boundary work and recommend whether Phase 6 is
ready for user-approved closure review or whether one final narrow documentation or
stabilization task is needed.

Do not modify solver source code, tests, examples, CLI behavior, JSON schemas, or
algorithmic behavior.

## Context

Phase 6 has progressed from the conservative cut/callback boundary design note through
immutable cut candidates, deterministic cut-pool lifecycle handling, a no-op separator
boundary, read-only callback events, optional no-op branch-and-bound integration, and a
deterministic toy separator.

The latest completed task, `20260524-10-01_toy-separator`, added a deterministic toy
upper-bound separator for tiny documented fixtures and recommended a Phase 6 completion
audit before closure review.

Relevant inputs:

- `ROADMAP.md`
- `tasks/phases/phase_06_cut_callbacks.md`
- `notes/18_cut_callback_boundary_design.md`
- recent Phase 6 reports under `tasks/reports/`
- current `src/silo/cuts/` implementation inventory
- current Phase 6 test inventory by filename, unless deeper inspection is needed to
  verify audit claims

## Scope Lock

This task is atomic.

Primary objective:

- Produce a Phase 6 completion audit report that maps planned Phase 6 scope to completed
  implementation, tests, integration boundaries, known limitations, and closure-readiness.

Allowed changes:

- `tasks/phases/phase_06_cut_callbacks.md`
- `tasks/reports/20260524-11-01_phase6-completion-audit_report.md`

Supporting allowed change:

- `tasks/codex/20260524-11-01_phase6-completion-audit.md` may be committed as the issued
  task contract for this execution.

Forbidden changes:

- Do not modify solver source code.
- Do not modify tests.
- Do not modify examples.
- Do not modify CLI behavior.
- Do not modify documentation outside `tasks/phases/phase_06_cut_callbacks.md`.
- Do not modify JSON model schemas or solution schemas.
- Do not modify branch-and-bound search logic, node ordering, pruning rules, incumbent
  updates, LP solvers, or presolve.
- Do not mark Phase 6 complete in `ROADMAP.md`.
- Do not start, scope, implement, or issue Phase 7 work.
- Do not modify existing files under `tasks/codex/`.
- Do not add generated output files to git.

## Required Audit Content

The audit report must include:

1. A short Phase 6 scope summary from `ROADMAP.md`,
   `tasks/phases/phase_06_cut_callbacks.md`, and
   `notes/18_cut_callback_boundary_design.md`.
2. A completion map for the Phase 6 sequence from design through deterministic toy
   separator, using task/report IDs where possible.
3. Evidence that the current implementation covers the conservative Phase 6 acceptance
   criteria: cut representation, duplicate handling, cut-pool lifecycle, no-op separator,
   callback event records, no-regression default branch-and-bound behavior, optional no-op
   cut/callback integration, and deterministic toy separator behavior.
4. A limitations section that explicitly preserves out-of-scope items: real cut-family
   algorithms, cut materialization into LP relaxations, lazy constraints, arbitrary
   mutation callbacks, public CLI changes, JSON schema changes, external solver calls,
   performance claims, and Phase 7 decomposition work.
5. A risk/gap assessment that distinguishes blocking gaps from acceptable documented
   limitations.
6. A recommendation with exactly one of these outcomes:
   - `ready_for_user_closure_review`
   - `needs_one_stabilization_task`
7. If recommending `needs_one_stabilization_task`, name exactly one next atomic task and
   explain why it is blocking.
8. If recommending `ready_for_user_closure_review`, state that closing Phase 6 and
   considering Phase 7 still require explicit user approval.

Update `tasks/phases/phase_06_cut_callbacks.md` only with a brief Phase 6H audit note
that records the audit occurred and points to the report. Do not change the roadmap status
or mark Phase 6 complete.

## Stop Conditions

Stop and report instead of proceeding if:

- the audit discovers that assessing Phase 6 completion requires solver behavior changes;
- the audit discovers that assessing Phase 6 completion requires changing tests or
  examples;
- the audit cannot determine the current Phase 6 task sequence from repository files;
- the appropriate next action is a phase transition rather than an audit report;
- unrelated dirty repository changes appear and make the audit scope ambiguous.

## Required Checks

Run at least:

```bash
git status --short
python scripts/check_quality.py
git diff --check
```

Do not run external solvers.

## Acceptance Criteria

This task is complete only if:

1. A report is created at the expected report path.
2. The report maps Phase 6 scope to completed tasks, reports, notes, implementation files,
   and tests where relevant.
3. The report identifies any remaining gaps as either blocking or non-blocking.
4. The report recommends exactly one outcome:
   `ready_for_user_closure_review` or `needs_one_stabilization_task`.
5. `tasks/phases/phase_06_cut_callbacks.md` records only a brief audit note and does not
   mark Phase 6 complete.
6. No solver source code is modified.
7. No tests are modified.
8. No examples or generated output files are modified or added.
9. `python scripts/check_quality.py` passes.
10. `git diff --check` passes.

## Report Requirements

Create:

```text
tasks/reports/20260524-11-01_phase6-completion-audit_report.md
```

The report must include:

```text
Task ID:
Objective:
Risk classification:
Files changed:
Phase 6 scope summary:
Completion evidence map:
Acceptance-criteria assessment:
Limitations and non-goals:
Risk/gap assessment:
Recommendation:
Checks run:
Results:
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
git add tasks/codex/20260524-11-01_phase6-completion-audit.md tasks/phases/phase_06_cut_callbacks.md tasks/reports/20260524-11-01_phase6-completion-audit_report.md
git commit -m "docs(tasks): audit Phase 6 completion"
git push
```

If push fails, preserve the local commit and record the failure in the report and final
response.

## Final Response

When finished, report only:

- whether the Phase 6 completion audit was created;
- the audit recommendation;
- whether the Phase 6 note was updated;
- whether checks passed;
- whether a local commit was created;
- whether push completed or failed;
- the next recommended atomic task.
