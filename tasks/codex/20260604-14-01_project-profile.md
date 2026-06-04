# Task: 20260604-14-01 Project Profile

## Metadata

- Task ID: `20260604-14-01`
- Slug: `project-profile`
- Date: 2026-06-04
- SILO-DOS mode: Mode A auto-one
- Process area: SILO-DOS v0.4 local mirror
- Task type: project profile documentation
- Risk level: L0 safe documentation
- Git mode: push-on-success
- Expected report: `tasks/reports/20260604-14-01_project-profile_report.md`

## Objective

Create `.silo-dos/project_profile.md` from stable repository rules and the project
milestone audit.

## Context

Use these as primary inputs:

- `.silo-dos/v04_architecture.md`
- `tasks/reports/20260604-12-01_project-milestone-audit_report.md`

Also read:

- `tasks/README.md`
- `AGENTS.md`
- `ROADMAP.md`
- recent Phase 9 reports as needed.

The profile is the first materialized SILO-DOS v0.4 local mirror file after the
architecture note. It should record stable project identity and operating boundaries
without replacing `tasks/README.md`, `AGENTS.md`, `ROADMAP.md`, or phase files.

## Scope Lock

Solve exactly one primary problem: add `.silo-dos/project_profile.md` and the matching
task/report files.

## Allowed Changes

- `.silo-dos/project_profile.md`
- `tasks/codex/20260604-14-01_project-profile.md`
- `tasks/reports/20260604-14-01_project-profile_report.md`

## Forbidden Changes

- Do not modify solver source code under `src/`.
- Do not modify tests.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify `tasks/phases/`.
- Do not modify existing notes.
- Do not modify existing task files.
- Do not modify the local `silo-development-operator` skill.
- Do not start Phase 10.
- Do not implement native backend code.
- Do not modify public CLI behavior.
- Do not modify JSON schemas.
- Do not add dependencies.
- Do not modify build or packaging files.
- Do not change solver dispatch or backend selection behavior.
- Do not close Phase 9.
- Do not issue or execute another task.

## Required Profile Content

The profile must record:

- SILO project identity;
- current milestone status;
- completed phases;
- parked Phase 9 state;
- native defer decision;
- forbidden default changes;
- standard checks;
- task/report directories;
- phase transition rules.

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

- `.silo-dos/project_profile.md` is created.
- The profile records all required content.
- No forbidden files or behaviors are changed.
- Required checks pass.
- A matching report is created.
- A local commit is created after checks pass.
- Push is attempted once and the result is recorded.

## Report Requirements

Create `tasks/reports/20260604-14-01_project-profile_report.md` with:

- task objective;
- risk level;
- task ID scan result;
- files changed;
- profile summary;
- checks run and results;
- deviations from scope, if any;
- git status before and after;
- commit hash;
- push result;
- next recommended atomic task.

## Final Response Requirements

Report:

- task path;
- profile path;
- report path;
- whether checks passed;
- commit hash;
- whether push succeeded;
- whether forbidden changes were avoided;
- next recommended action.

Stop after this one atomic task.
