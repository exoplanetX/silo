# Task: SILO-DOS v0.4 Local Mirror Smoke Test Repeat

## Metadata

- Task ID: `20260607-04-01`
- Slug: `v04-smoke-test-repeat`
- Date: 2026-06-07
- Mode: Mode A auto-one
- Risk level: L0 safe process audit / smoke test
- Task type: SILO-DOS process audit
- Git mode: `push-on-success`
- Expected report: `tasks/reports/20260607-04-01_v04-smoke-test-repeat_report.md`

## Objective

Verify that the upgraded local `silo-development-operator` v0.4 actually uses
`.silo-dos/` as the primary decision mirror and produces the correct current project
decision without modifying solver functionality.

This repeat smoke test is issued after the prior smoke-test commit is locally visible
and synchronized by Git proof. It must not modify the local skill or any solver files.

## Scope Lock

This is a process audit / smoke test only.

Solve exactly one primary problem:

```text
Confirm v0.4 local mirror decision behavior from the current synchronized repository
state.
```

Do not issue or execute any solver feature task.

## Required Smoke Assertions

Confirm:

- the local skill identifies as v0.4;
- the local skill reads `.silo-dos/` in the designed order;
- the local mirror infers the current project status:
  - Python reference solver milestone complete;
  - Phase 9 open but parked on design/bookkeeping;
  - native implementation deferred and not approved;
  - Phase 10 not started;
  - no immediate solver implementation task required;
- Mode A would not issue solver, native, or Phase 10 work by default;
- Remote Sync Proof is included in the final digest;
- standing approval is recognized but bounded by `technical_route` and
  `remote_sync_proof`.

## Allowed Changes

- Create this matching task file under `tasks/codex/`.
- Create `tasks/reports/20260607-04-01_v04-smoke-test-repeat_report.md`.

## Forbidden Changes

- Do not modify solver source code.
- Do not modify tests.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not modify existing `.silo-dos/` files.
- Do not modify the local `silo-development-operator` skill.
- Do not modify existing notes.
- Do not modify `tasks/README.md`.
- Do not modify `AGENTS.md`.
- Do not start Phase 10.
- Do not close Phase 9.
- Do not implement native backend.
- Do not change CLI behavior.
- Do not change JSON schemas.
- Do not add dependencies.
- Do not modify build or packaging files.
- Do not change solver dispatch or backend selection.
- Do not issue or execute another task.

## Required Inputs

Inspect:

- `C:\Users\xuning\.codex\skills\silo-development-operator\SKILL.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/remote_sync_proof.md`
- `.silo-dos/standing_approval_profile.md`
- `.silo-dos/experience_map.md`
- `.silo-dos/self_evolution.md`
- `.silo-dos/v04_architecture.md`
- `.silo-dos/local_skill_integration_design.md`
- `tasks/README.md`
- `ROADMAP.md`
- recent task reports as needed.

## Required Checks

Run at least:

```text
git status --short
git branch --show-current
git log --oneline -5
git rev-list --left-right --count origin/main...HEAD
git diff --check
```

Before committing, run:

```text
git diff --cached --check
```

Do not run full solver tests because this task must not modify executable files. Do not
run native build commands or native tooling.

## Report Requirements

Create the matching report with:

- task objective;
- risk level;
- task ID scan result;
- files changed;
- local skill verification results;
- `.silo-dos/` files inspected;
- local mirror read-order assessment;
- inferred current project status;
- Mode A default decision;
- standing approval boundary assessment;
- Remote Sync Proof assessment;
- whether any immediate solver/native/Phase 10 task is required;
- checks run and results;
- deviations from scope, if any;
- repository git status before and after;
- remote sync proof;
- local commit hash;
- push result;
- boundary status;
- next recommended action.

## Acceptance Criteria

- The report confirms the local skill identifies as v0.4.
- The report confirms the designed `.silo-dos/` read order is present.
- The report confirms the current status is correctly inferred from the local mirror.
- The report confirms Mode A does not issue solver/native/Phase 10 work by default.
- The report confirms Remote Sync Proof is included in the final digest standard.
- The report confirms standing approval is bounded by Technical Route and Remote Sync
  Proof.
- Only this task file and the matching report are changed in the repository.
- Required checks pass.

## Final Response Requirements

Report only:

- task path;
- report path;
- whether the smoke test completed;
- local skill v0.4 verification;
- current project status inferred;
- whether Mode A would issue solver/native/Phase 10 work by default;
- checks run;
- commit hash;
- whether push succeeded;
- Remote Sync Proof;
- next recommended action.
