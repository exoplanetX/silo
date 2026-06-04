# Task: 20260604-13-01 SILO-DOS v0.4 Architecture

## Metadata

- Task ID: `20260604-13-01`
- Slug: `silo-dos-v04-architecture`
- Date: 2026-06-04
- SILO-DOS mode: Mode C principal mode
- Process area: SILO-DOS project operating system
- Task type: architecture design note
- Risk level: L3 strategic design-only
- Git mode: push-on-success
- Expected report: `tasks/reports/20260604-13-01_silo-dos-v04-architecture_report.md`

## Objective

Design SILO-DOS v0.4 as a Project Profile, Technical Route, Experience Map, and
Self-Evolution system.

## Context

Read these repository files before execution:

- `tasks/README.md`
- `AGENTS.md`
- `ROADMAP.md`
- `tasks/reports/20260604-12-01_project-milestone-audit_report.md`
- `tasks/reports/20260604-11-01_phase9-post-defer-audit_report.md`
- recent `tasks/reports/` files as needed for process evidence.

The project milestone audit found that the Python reference-solver milestone is complete
for the current educational/conservative scope, Phase 9 is parked after the native
implementation defer decision, and SILO-DOS process improvement opportunities include
remote sync proof and project-profile migration.

This task is planning/design only. It must not modify solver behavior or the current
local `silo-development-operator` skill.

## Scope Lock

Solve exactly one primary problem: create the SILO-DOS v0.4 architecture design note and
matching execution report.

## Allowed Changes

- `.silo-dos/v04_architecture.md`
- `tasks/codex/20260604-13-01_silo-dos-v04-architecture.md`
- `tasks/reports/20260604-13-01_silo-dos-v04-architecture_report.md`

## Forbidden Changes

- Do not modify solver source code under `src/`.
- Do not modify tests.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify `tasks/phases/`.
- Do not modify existing notes.
- Do not modify existing task files.
- Do not modify the local `silo-development-operator` skill.
- Do not create the full `.silo-dos/` file set beyond `.silo-dos/v04_architecture.md`.
- Do not modify public CLI behavior.
- Do not modify JSON schemas.
- Do not add dependencies.
- Do not modify build or packaging files.
- Do not implement native backend code.
- Do not change solver dispatch or backend selection behavior.
- Do not close Phase 9.
- Do not start Phase 10.
- Do not issue or execute another task.

## Required Design Content

The design note must cover:

- why SILO-DOS is currently too scattered;
- proposed `.silo-dos/` directory structure;
- local mirror vs Research Brain division of responsibility;
- Decision Lookup Chain: local mirror -> Research Brain -> user decision;
- Phase Technical Route / Decision Corridor mechanism;
- Experience Map extraction from historical reports;
- Self-Evolution Loop for process improvements;
- Remote Sync Proof;
- Standing Approval Profile;
- v0.4 non-goals;
- candidate follow-up atomic tasks.

## Required Checks

Run:

```text
git status --short
git branch --show-current
git log --oneline -5
git diff --check
```

Do not run solver tests unless executable files are unexpectedly modified. Do not run
native build commands or native tooling.

## Acceptance Criteria

- `.silo-dos/v04_architecture.md` is created.
- The design covers all required topics.
- No forbidden files or behaviors are changed.
- The matching report is created.
- Required checks pass.
- A local commit is created after checks pass.
- Push is attempted once and the result is recorded.

## Report Requirements

Create `tasks/reports/20260604-13-01_silo-dos-v04-architecture_report.md` with:

- task objective;
- risk level;
- task ID scan result;
- files changed;
- design summary;
- checks run and results;
- deviations from scope, if any;
- git status before and after;
- commit hash;
- push result;
- next recommended atomic task.

## Final Response Requirements

Report:

- task path;
- design note path;
- report path;
- whether checks passed;
- commit hash;
- whether push succeeded;
- whether forbidden changes were avoided;
- next recommended action.

Stop after this one atomic task.
