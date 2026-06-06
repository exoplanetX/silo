# Task: SILO Development Operator v0.4 Local Skill Upgrade

## Metadata

- Task ID: `20260607-02-01`
- Slug: `silo-dev-operator-v04`
- Date: 2026-06-07
- Mode: Mode A auto-one with explicit L3 approval
- Risk level: L3 strategic / process-governance
- Task type: local SILO-DOS skill upgrade
- Git mode: `push-on-success`
- Expected report: `tasks/reports/20260607-02-01_silo-dev-operator-v04_report.md`

## Explicit User Approval

The user explicitly approved executing one L3 local skill v0.4 upgrade task.

Approved local non-repository change:

- Update `C:\Users\xuning\.codex\skills\silo-development-operator\SKILL.md`.

Approved repository changes:

- This matching task file under `tasks/codex/`.
- The matching report under `tasks/reports/`.

The local skill file is outside the `silo-solver` repository and must not be committed to
the repository.

## Objective

Upgrade the local `silo-development-operator` skill from v0.3 to v0.4 so that it treats
`.silo-dos/` as the primary repository-local decision mirror.

The upgrade must follow:

- `.silo-dos/local_skill_integration_design.md`
- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/remote_sync_proof.md`
- `.silo-dos/experience_map.md`
- `.silo-dos/standing_approval_profile.md`
- `.silo-dos/self_evolution.md`

## Required v0.4 Behavior

The local skill must state that future SILO-DOS runs should:

- run Git preflight on startup and inspect Remote Sync Proof expectations;
- read `.silo-dos/` files before deciding the next task;
- use `project_profile.md` for project identity, source-of-truth rules, forbidden
  defaults, and standard checks;
- use `technical_route.md` for current allowed corridor, forbidden actions, and phase
  gates;
- use `decision_log.md` for durable strategic decisions;
- use `remote_sync_proof.md` to decide whether a new task may start;
- use `experience_map.md` for reusable decision patterns;
- use `standing_approval_profile.md` for L0/L1 auto-execution rules and L2/L3 hard
  stops;
- use `self_evolution.md` for process-friction detection and improvement candidate
  generation;
- use this decision lookup chain:

```text
local mirror -> Research Brain -> user decision
```

- preserve Mode A / Mode B / Mode C behavior;
- preserve one-task-at-a-time execution;
- preserve task ID scanning;
- preserve immutable task contract and report discipline;
- preserve Decision Packet / Failure Packet / Scope Expansion Packet behavior;
- preserve phase start and phase closure approval gates;
- make Remote Sync Proof mandatory in every End-of-Run Digest.

## Scope Lock

Solve exactly one primary problem:

```text
Upgrade the local operator skill text to v0.4 process behavior.
```

Do not issue or execute any solver feature task.

## Allowed Changes

Repository:

- `tasks/codex/20260607-02-01_silo-dev-operator-v04.md`
- `tasks/reports/20260607-02-01_silo-dev-operator-v04_report.md`

Local non-repository:

- `C:\Users\xuning\.codex\skills\silo-development-operator\SKILL.md`

## Forbidden Changes

- Do not modify solver source code under `src/`.
- Do not modify tests.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not modify existing `.silo-dos/` files.
- Do not modify existing notes.
- Do not modify `tasks/README.md`.
- Do not modify `AGENTS.md`.
- Do not modify public CLI behavior.
- Do not modify JSON model or solution schemas.
- Do not add dependencies.
- Do not modify build or packaging files.
- Do not change solver dispatch or backend selection behavior.
- Do not start Phase 10.
- Do not close Phase 9.
- Do not implement native backend.
- Do not issue or execute a solver feature task.
- Do not execute a second task.

## Required Checks

Run at least:

```text
git status --short
git branch --show-current
git log --oneline -5
git rev-list --left-right --count origin/main...HEAD
git diff --check
```

Verify the local skill file contains:

- `v0.4`
- `.silo-dos`
- `project_profile`
- `technical_route`
- `decision_log`
- `remote_sync_proof`
- `experience_map`
- `standing_approval_profile`
- `self_evolution`
- `local mirror -> Research Brain -> user decision`
- `Remote Sync Proof`

Before committing repository task/report files, run:

```text
git diff --cached --check
```

Do not run full solver tests because no executable repository files may change. Do not
run native build commands or native tooling.

## Report Requirements

Create `tasks/reports/20260607-02-01_silo-dev-operator-v04_report.md` with:

- task objective;
- risk level and explicit approval;
- files changed;
- local skill path updated;
- v0.4 behavior summary;
- `.silo-dos/` read order;
- decision lookup chain;
- standing approval behavior;
- L2/L3 hard-stop behavior;
- remote sync proof behavior;
- checks run and results;
- local skill verification results;
- repository git status before and after;
- remote sync proof;
- local commit hash for repository task/report files;
- push result;
- boundary status;
- next recommended action.

## Acceptance Criteria

- The local skill identifies itself as v0.4.
- The local skill names `.silo-dos/` as the primary repository-local decision mirror.
- The local skill includes the required `.silo-dos/` file roles and read order.
- The local skill includes the decision lookup chain:
  `local mirror -> Research Brain -> user decision`.
- The local skill preserves Mode A / Mode B / Mode C behavior and one-task-at-a-time
  execution.
- The local skill preserves task ID scanning, immutable task contracts, reports, packets,
  phase gates, commit/push rules, and Remote Sync Proof.
- The repository commit includes only this task file and the matching report.
- Required checks pass.

## Stop Conditions

Stop and report if:

- Git preflight is not synchronized and the user has not approved recovery;
- the task ID collides;
- completing the upgrade requires modifying repository files beyond the matching task and
  report;
- completing the upgrade requires solver, test, example, CLI, JSON schema, dependency,
  build, packaging, dispatch, roadmap, phase, `.silo-dos/`, or native implementation
  changes;
- local skill verification fails and the fix would exceed this local skill upgrade;
- required checks fail and the fix is outside scope.

## Final Response Requirements

Report only:

- task path;
- report path;
- local skill path updated;
- whether local skill v0.4 upgrade completed;
- whether repository checks passed;
- local skill verification result;
- repository commit hash;
- whether push succeeded;
- boundary status;
- next recommended action.
