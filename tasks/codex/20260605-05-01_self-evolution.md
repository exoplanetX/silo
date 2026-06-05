# Task: 20260605-05-01 Self Evolution

## Metadata

- Task ID: `20260605-05-01`
- Slug: `self-evolution`
- Date: 2026-06-05
- SILO-DOS mode: Mode A auto-one
- Risk level: L0 safe documentation/process task
- Git mode: `push-on-success`
- Expected report: `tasks/reports/20260605-05-01_self-evolution_report.md`

## Objective

Create `.silo-dos/self_evolution.md` to define SILO-DOS process-upgrade mechanics.

## Context

Use these primary inputs:

- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/remote_sync_proof.md`
- `.silo-dos/experience_map.md`
- `.silo-dos/standing_approval_profile.md`

The current route remains `phase9_parked_on_design_bookkeeping_after_native_defer`.
This task is process documentation only.

## Required Content

`.silo-dos/self_evolution.md` must define:

- how SILO-DOS detects process friction;
- improvement candidate format;
- when to update `.silo-dos` local mirror files;
- when to export lessons to Research Brain;
- when to propose local skill changes;
- when no action should be taken;
- examples covering repeated L1 interruptions, push failure patterns, duplicate task
  attempts, stale route assumptions, and missing decision evidence.

## Scope Lock

This task creates one local mirror process file. It must not update the local
`silo-development-operator` skill, change repository task rules, alter phase state, or
change solver behavior.

## Allowed Changes

- Add `.silo-dos/self_evolution.md`
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

- `.silo-dos/self_evolution.md` exists.
- The file defines friction detection.
- The file defines an improvement candidate format.
- The file defines when to update `.silo-dos` local mirror files.
- The file defines when to export lessons to Research Brain.
- The file defines when to propose local skill changes.
- The file defines when no action should be taken.
- The required examples are included.
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
- self-evolution file path;
- report path;
- checks run;
- commit hash;
- push result;
- final remote sync proof.

Stop after this one atomic task.
