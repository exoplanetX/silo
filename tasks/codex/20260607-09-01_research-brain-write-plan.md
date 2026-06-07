# SILO Codex Task: Research Brain Export Review and Write Plan

## Task Metadata

- Task ID: `20260607-09-01`
- Slug: `research-brain-write-plan`
- Risk level: L3 design-only process-governance plan, executed as a scoped local
  documentation/process task
- Task type: SILO-DOS v0.4 Research Brain write-plan design
- Mode: SILO-DOS Mode A auto-one
- Git mode: `push-on-success`
- Expected report: `tasks/reports/20260607-09-01_research-brain-write-plan_report.md`

## Objective

Review `.silo-dos/research_brain_export_v1.md` and design a safe write plan for how
this export should later be written into the remote Research Brain.

This task must not write to Google Drive, Research Brain, external services, or any
connector. It only creates a local review/write plan.

## Primary Output

- `.silo-dos/research_brain_write_plan.md`

## Primary Inputs

- `.silo-dos/research_brain_export_v1.md`
- `.silo-dos/research_brain_bridge.md`
- `.silo-dos/experience_map.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/self_evolution.md`
- `tasks/reports/20260607-08-01_research-brain-export-v1_report.md`

## Allowed Changes

- `.silo-dos/research_brain_write_plan.md`
- `tasks/codex/20260607-09-01_research-brain-write-plan.md`
- `tasks/reports/20260607-09-01_research-brain-write-plan_report.md`

## Forbidden Changes

- Do not write to Google Drive.
- Do not write to Research Brain.
- Do not use external services or connectors.
- Do not modify solver source code.
- Do not modify tests.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify `tasks/phases/`.
- Do not modify existing `.silo-dos/` files except adding the new write-plan file.
- Do not modify existing notes.
- Do not modify the local `silo-development-operator` skill.
- Do not start Phase 10.
- Do not implement native backend.
- Do not change CLI behavior.
- Do not change JSON schemas.
- Do not add dependencies.
- Do not modify build or packaging files.
- Do not change solver dispatch or backend selection behavior.
- Do not issue or execute another task.

## Write Plan Requirements

The write plan must cover:

1. Write-readiness assessment.
2. Proposed Research Brain target structure.
3. Document split plan.
4. Format plan.
5. Write order.
6. Manual vs connector-assisted workflow.
7. Research Brain entry schema.
8. Versioning and update policy.
9. Import / preload use cases.
10. Safety boundaries.
11. Recommended next action.

Expected conclusion:

- `research_brain_export_v1.md` is ready for user review.
- Direct external writing should not happen automatically.
- The safest next step is for the user to review and approve a write plan.
- If approved, documents should be created in Research Brain as several focused entries
  plus one overview.
- Repo-local `.silo-dos/` remains the execution source of truth.

## Required Checks

Run at least:

```text
git status --short
git branch --show-current
git log --oneline -5
git rev-list --left-right --count origin/main...HEAD
git diff --check
git diff --cached --check
```

Do not run full solver tests unless executable files are unexpectedly modified. Do not
run native build commands or native tooling.

## Acceptance Criteria

- Exactly one task is issued and executed.
- The local write plan is created.
- The write plan includes all required sections.
- No external write or connector call is made.
- Only allowed files are changed.
- Required checks pass.
- The matching report is created.
- Repository changes are committed locally.
- Push is attempted once.
- Remote Sync Proof is recorded in the final report and final response.

## Stop Conditions

Stop and report if:

- the worktree is dirty before execution with unrelated files;
- `origin/main...HEAD` is not `0 0` before execution;
- required input files are missing;
- execution would require forbidden file changes;
- execution would require an external connector call or external write;
- any required check fails;
- the task would need a second atomic objective.
