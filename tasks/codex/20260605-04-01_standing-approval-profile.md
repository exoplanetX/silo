# Task: 20260605-04-01 Standing Approval Profile

## Metadata

- Task ID: `20260605-04-01`
- Slug: `standing-approval-profile`
- Date: 2026-06-05
- SILO-DOS mode: Mode A auto-one
- Risk level: L0 safe documentation/process task
- Git mode: `push-on-success`
- Expected report: `tasks/reports/20260605-04-01_standing-approval-profile_report.md`

## Objective

Create `.silo-dos/standing_approval_profile.md` from the current SILO-DOS v0.4 local
mirror files.

## Context

Use these primary inputs:

- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/remote_sync_proof.md`
- `.silo-dos/experience_map.md`

The current route remains `phase9_parked_on_design_bookkeeping_after_native_defer`.
This task is process documentation only.

## Required Content

The standing approval profile must define:

- auto-executable L0 categories;
- auto-executable L1 categories, especially passive immutable records, validation tests,
  diagnostic records, fixture records, package boundary smoke tests, and process mirror
  tasks;
- hard-stop L2 categories;
- hard-stop L3 categories;
- conditions that revoke standing approval, including solver behavior changes, solver
  dispatch, backend selector behavior, CLI or JSON schema changes,
  dependency/build/packaging changes, native implementation, phase start/closure, and
  future-phase work;
- how the profile interacts with the Phase Technical Route;
- how the profile interacts with Remote Sync Proof.

## Scope Lock

This task creates one local mirror policy file. It must not update the local
`silo-development-operator` skill or change repository task rules. The profile is
advisory and must not override current user instructions, issued task contracts,
`tasks/README.md`, `AGENTS.md`, the Phase Technical Route, or Remote Sync Proof.

## Allowed Changes

- Add `.silo-dos/standing_approval_profile.md`
- Add this task file under `tasks/codex/`
- Add the matching report under `tasks/reports/`

## Forbidden Changes

- Do not modify solver source code.
- Do not modify tests.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify `tasks/phases/`.
- Do not modify existing notes.
- Do not modify existing task files.
- Do not modify the local `silo-development-operator` skill.
- Do not start Phase 10.
- Do not implement native backend.
- Do not add native dependencies.
- Do not modify build or packaging files.
- Do not change public CLI behavior.
- Do not change JSON schemas.
- Do not change solver dispatch.

## Required Checks

Run:

```text
git status --short
git branch --show-current
git log --oneline -5
git rev-list --left-right --count origin/main...HEAD
git diff --check
git diff --cached --check
```

No solver tests are required because this task does not modify executable code, tests,
examples, public CLI behavior, JSON schemas, native code, dependencies, build files, or
packaging files.

## Acceptance Criteria

- `.silo-dos/standing_approval_profile.md` exists.
- The file defines auto-executable L0 and L1 categories.
- The file defines hard-stop L2 and L3 categories.
- The file defines standing-approval revocation conditions.
- The file explains interaction with the Phase Technical Route.
- The file explains interaction with Remote Sync Proof.
- The matching report is created.
- Required checks pass.
- Only the allowed files are changed.

## Stop Conditions

Stop and report instead of expanding scope if completion would require:

- modifying solver source code, tests, examples, roadmap, phase files, existing notes,
  or the local skill;
- changing task-directory rules;
- changing public CLI or JSON schemas;
- implementing native backend work;
- starting Phase 10;
- running another atomic task.

## Final Response Requirements

Report:

- generated task path;
- standing approval profile path;
- report path;
- checks run;
- commit hash;
- push result;
- final remote sync proof.

Stop after this one atomic task.
