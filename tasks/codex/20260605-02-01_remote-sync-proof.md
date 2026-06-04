# Task: 20260605-02-01 Remote Sync Proof

## Metadata

- Task ID: `20260605-02-01`
- Slug: `remote-sync-proof`
- Date: 2026-06-05
- SILO-DOS mode: Mode A auto-one
- Risk level: L0 safe documentation/process task
- Git mode: `push-on-success`
- Expected report: `tasks/reports/20260605-02-01_remote-sync-proof_report.md`

## Objective

Create `.silo-dos/remote_sync_proof.md` to standardize how SILO-DOS reports local Git
status, push results, ahead/behind state, and the final remote synchronization status at
the end of a run.

## Context

Use these primary inputs:

- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- recent reports that record push failures, especially reports describing HTTPS
  connection resets, SSL read failures, preserved local commits, and later sync-only
  recovery.

The current Phase 9 route is parked on design/bookkeeping after the native
implementation defer decision. This task is process documentation only.

## Scope Lock

This task creates one SILO-DOS v0.4 local mirror file for remote sync proof. It must not
change solver behavior, phase state, native-backend posture, task-system rules, or the
local operator skill.

## Allowed Changes

- Add `.silo-dos/remote_sync_proof.md`
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

## Required Content

`.silo-dos/remote_sync_proof.md` must define the required end-of-run sync proof fields:

- `git status --short`
- `git branch --show-current`
- `git log --oneline -5`
- `git rev-list --left-right --count origin/main...HEAD`
- `git push result`
- `remote_sync_status`

It must define the allowed `remote_sync_status` values:

- `synchronized_with_origin`
- `local_ahead_origin`
- `push_failed`
- `dirty_worktree`
- `connector_unverified`

It must define these rules:

- Do not start another task unless `remote_sync_status` is `synchronized_with_origin` or
  the user explicitly approves recovery.
- If push fails, preserve the local commit and run sync-only recovery instead of
  continuing to a new development task.
- ChatGPT remote connector verification is helpful but not required when local Git proof
  is clean.
- Codex local Git proof is the primary source of sync truth.

It should include practical status-derivation guidance and an end-of-run report
template.

## Required Checks

Run:

```text
git status --short
git branch --show-current
git log --oneline -5
git diff --check
git diff --cached --check
```

No solver tests are required because this task does not modify executable code, tests,
examples, CLI behavior, JSON schemas, or solver behavior.

## Acceptance Criteria

- `.silo-dos/remote_sync_proof.md` exists.
- The file defines all required proof fields.
- The file defines all allowed `remote_sync_status` values.
- The file documents push-failure handling and sync-only recovery.
- The file states that local Git proof is the primary sync truth.
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
- remote sync proof file path;
- report path;
- checks run;
- commit hash;
- push result;
- final `remote_sync_status` if available.

Stop after this one atomic task.
