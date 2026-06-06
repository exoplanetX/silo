# SILO Codex Task: v0.4 Decision Chain Smoke Test

## Task Metadata

- Task ID: `20260607-05-01`
- Slug: `v04-decision-chain-smoke`
- Risk level: L0 safe process audit / smoke test
- Task type: SILO-DOS v0.4 process audit
- Mode: SILO-DOS Mode A auto-one
- Git mode: `push-on-success`
- Expected report: `tasks/reports/20260607-05-01_v04-decision-chain-smoke_report.md`

## Objective

Verify that the upgraded local `silo-development-operator` v0.4 uses `.silo-dos/` as
the primary decision mirror, follows the local mirror -> Research Brain -> user decision
chain, recognizes the current parked Phase 9 state, and includes Remote Sync Proof in
the End-of-Run Digest.

## Primary Inputs

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
- `AGENTS.md`
- `ROADMAP.md`
- recent matching reports under `tasks/reports/`

## Scope Lock

This is a process audit only. It must not change solver functionality, phase status,
public contracts, local skill behavior, or existing `.silo-dos/` files.

## Allowed Changes

- `tasks/codex/20260607-05-01_v04-decision-chain-smoke.md`
- `tasks/reports/20260607-05-01_v04-decision-chain-smoke_report.md`

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
- Do not modify the local `silo-development-operator` skill.
- Do not start Phase 10.
- Do not close Phase 9.
- Do not implement native backend.
- Do not change CLI behavior.
- Do not change JSON schemas.
- Do not add dependencies.
- Do not modify build or packaging files.
- Do not change solver dispatch or backend selection behavior.
- Do not issue or execute another task.

## Required Verification

The report must answer:

1. Does the local skill identify as `silo-development-operator v0.4`?
2. Does the local skill define `.silo-dos/` as the primary repository-local decision
   mirror?
3. Does the local skill record the designed `.silo-dos/` startup read order?
4. Does the local skill contain the decision lookup chain:
   `local mirror -> Research Brain -> user decision`?
5. Does the local mirror infer the current project status:
   - Python reference solver milestone complete;
   - Phase 9 open but parked on design/bookkeeping;
   - native implementation deferred and not approved;
   - Phase 10 not started;
   - no immediate solver implementation task required?
6. Would Mode A avoid issuing solver, native, or Phase 10 work by default?
7. Is standing approval recognized but bounded by `technical_route` and
   `remote_sync_proof`?
8. Does the End-of-Run Digest include Remote Sync Proof?

## Required Checks

Run at least:

```text
git status --short
git branch --show-current
git log --oneline -5
git rev-list --left-right --count origin/main...HEAD
git diff --check
```

Also run `git diff --cached --check` before committing.

Do not run full solver tests unless executable files are unexpectedly modified. Do not
run native build commands or native tooling.

## Acceptance Criteria

- Exactly one task is issued and executed.
- Only the matching task and report files are changed.
- Local skill v0.4 markers are verified.
- `.silo-dos/` files are used as the primary decision mirror.
- The decision chain is verified.
- The parked Phase 9 status is recognized.
- Mode A default solver/native/Phase 10 hard stops are recognized.
- Remote Sync Proof appears in the final digest.
- Required checks pass.
- Repository task/report files are committed locally.
- Push is attempted once.

## Stop Conditions

Stop and report if:

- the worktree is dirty before execution with unrelated files;
- `origin/main...HEAD` is not `0 0` before execution;
- the local skill lacks required v0.4 markers;
- a required `.silo-dos/` file is missing;
- execution would require forbidden file changes;
- any required check fails;
- the task would need a second atomic objective.
