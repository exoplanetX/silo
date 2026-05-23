# Codex Task: Audit Phase 5 Completion

## Task Metadata

Task ID: 20260524-01-01
Task slug: phase5-completion-audit
Task type: process-audit
Related phase: Phase 5 / MIP branch-and-bound
Git mode: local-commit
Expected report path: tasks/reports/20260524-01-01_phase5-completion-audit_report.md

## Objective

Audit the current Phase 5 branch-and-bound work and recommend whether Phase 5 is ready
for user-approved closure or whether one final narrow stabilization task is needed before
considering Phase 6.

Do not modify solver source code, tests, CLI behavior, JSON schemas, examples, or
algorithmic behavior.

## Context

Phase 5 has progressed from branch-and-bound design through MIP relaxation, deterministic
search dataclasses, pure branch-and-bound solving for binary and bounded nonnegative
integer variables, checked-in examples, CLI exposure, CLI regression coverage, opt-in
summary diagnostics, optional node-log diagnostics, and node-log documentation.

The latest completed task, `20260523-08-01_mip-node-log-docs`, documented
`silo mip-solve --details --node-log` stdout and `--output` usage. Its report recommends a
Phase 5 completion audit before considering Phase 6.

Relevant inputs:

- `ROADMAP.md`
- `tasks/phases/phase_05_branch_and_bound.md`
- `notes/15_branch_and_bound_design.md`
- `notes/16_mip_cli_exposure_design.md`
- `notes/17_mip_diagnostics_output_design.md`
- `docs/mip_solve_cli.md`
- recent Phase 5 reports under `tasks/reports/`
- current tests and examples inventory by filename only, unless deeper inspection is needed
  to verify audit claims

## Scope Lock

This task is atomic.

Primary objective:

- Produce a Phase 5 completion audit report that maps planned Phase 5 scope to completed
  implementation, documentation, tests, examples, diagnostics, and known limitations.

Allowed changes:

- `tasks/phases/phase_05_branch_and_bound.md`
- `tasks/reports/20260524-01-01_phase5-completion-audit_report.md`

Supporting allowed change:

- `tasks/codex/20260524-01-01_phase5-completion-audit.md` may be committed as the issued
  task contract for this execution.

Forbidden changes:

- Do not modify solver source code.
- Do not modify tests.
- Do not modify examples.
- Do not modify CLI behavior.
- Do not modify documentation outside `tasks/phases/phase_05_branch_and_bound.md`.
- Do not modify JSON model schemas or solution schemas.
- Do not modify branch-and-bound search logic, node ordering, pruning rules, incumbent
  updates, LP solvers, or presolve.
- Do not mark Phase 5 complete in `ROADMAP.md`.
- Do not start, scope, implement, or issue Phase 6 work.
- Do not modify existing files under `tasks/codex/`.
- Do not add generated output files to git.

## Required Audit Content

The audit report must include:

1. A short Phase 5 scope summary from `ROADMAP.md` and
   `tasks/phases/phase_05_branch_and_bound.md`.
2. A completion map for the Phase 5 sequence from design through node-log documentation,
   using task/report IDs where possible.
3. Evidence that the current implementation covers the Phase 5 acceptance criteria:
   small MIP fixtures, deterministic branch-and-bound behavior, node counts, incumbent
   value, final status, CLI exposure, and diagnostics.
4. A limitations section that explicitly preserves out-of-scope items: cuts, heuristics,
   callbacks, branch-and-cut, MIP presolve, external solver calls, and advanced MIP
   features.
5. A risk/gap assessment that distinguishes blocking gaps from acceptable documented
   limitations.
6. A recommendation with exactly one of these outcomes:
   - `ready_for_user_closure_review`
   - `needs_one_stabilization_task`
7. If recommending `needs_one_stabilization_task`, name exactly one next atomic task and
   explain why it is blocking.
8. If recommending `ready_for_user_closure_review`, state that closing Phase 5 and entering
   Phase 6 still requires explicit user approval.

Update `tasks/phases/phase_05_branch_and_bound.md` only with a brief Phase 5N audit note
that records the audit occurred and points to the report. Do not change the roadmap status
or mark Phase 5 complete.

## Stop Conditions

Stop and report instead of proceeding if:

- the audit discovers that assessing Phase 5 completion requires solver behavior changes;
- the audit discovers that assessing Phase 5 completion requires changing tests or examples;
- the audit cannot determine the current Phase 5 task sequence from repository files;
- the appropriate next action is a phase transition rather than an audit report;
- unrelated dirty repository changes appear and make the audit scope ambiguous.

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

1. A report is created at the expected report path.
2. The report maps Phase 5 scope to completed tasks, reports, notes, docs, examples, and
   tests where relevant.
3. The report identifies any remaining gaps as either blocking or non-blocking.
4. The report recommends exactly one outcome:
   `ready_for_user_closure_review` or `needs_one_stabilization_task`.
5. `tasks/phases/phase_05_branch_and_bound.md` records only a brief audit note and does not
   mark Phase 5 complete.
6. No solver source code is modified.
7. No tests are modified.
8. No examples or generated output files are modified or added.
9. `git diff --check` passes.

## Report Requirements

Create:

```text
tasks/reports/20260524-01-01_phase5-completion-audit_report.md
```

The report must include:

```text
Task ID:
Objective:
Files changed:
Phase 5 scope summary:
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
local-commit
```

After successful audit and checks:

```bash
git add tasks/codex/20260524-01-01_phase5-completion-audit.md tasks/phases/phase_05_branch_and_bound.md tasks/reports/20260524-01-01_phase5-completion-audit_report.md
git commit -m "docs(tasks): audit Phase 5 completion"
```

Do not push unless explicitly instructed by the user.

## Final Response

When finished, report only:

- whether the Phase 5 completion audit was created;
- the audit recommendation;
- whether the Phase 5 note was updated;
- whether checks passed;
- whether a local commit was created;
- whether push was skipped or completed;
- the next recommended atomic task.
