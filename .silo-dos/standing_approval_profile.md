# SILO Standing Approval Profile

## Role Of This Profile

This file is the repository-local SILO-DOS v0.4 standing approval profile. It records
which narrow task categories may usually be auto-executed in Mode A and which categories
must stop for explicit approval.

This profile reduces repeated approval text. It does not create a new permission source.
It cannot override:

- current user instructions;
- issued task contracts under `tasks/codex/`;
- `tasks/README.md`;
- `AGENTS.md`;
- `ROADMAP.md`;
- `tasks/phases/`;
- `.silo-dos/project_profile.md`;
- `.silo-dos/technical_route.md`;
- `.silo-dos/decision_log.md`;
- `.silo-dos/remote_sync_proof.md`;
- `.silo-dos/experience_map.md`.

If a task crosses a hard-stop category, Mode A must stop even when the task resembles a
previously approved task.

## Sources

Primary inputs:

- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/remote_sync_proof.md`
- `.silo-dos/experience_map.md`

Stable source rules:

- `tasks/README.md`
- `AGENTS.md`
- `ROADMAP.md`
- `tasks/phases/`

## Current Route Assumption

This profile is written for the current corridor:

```text
phase9_parked_on_design_bookkeeping_after_native_defer
```

Native implementation is deferred and unapproved. Phase 10 has not started. Phase 9
closure is not approved. The profile must be reevaluated if the Phase Technical Route
changes.

## Approval Levels

### Auto-Executable L0 Categories

Mode A may auto-execute these task categories when scope is narrow, the worktree is clean,
Remote Sync Proof is satisfied, and no revocation condition is triggered:

- documentation-only tasks;
- report-only tasks;
- audit-only tasks;
- bookkeeping tasks that do not change phase state;
- task-system cleanup that does not rewrite task rules;
- `.silo-dos/` process mirror documentation tasks;
- examples-only tasks that add checked-in deterministic examples without solver source,
  test, CLI, schema, roadmap, phase, generated-output, or behavior changes;
- regression or boundary smoke checks that only add or update tests when the task is
  classified L0 by the issued contract and does not touch solver behavior;
- sync-only recovery tasks that modify no project files and only prove or restore remote
  synchronization.

Required L0 conditions:

- one primary objective;
- explicit allowed and forbidden files;
- matching report path;
- no public behavior change;
- no solver behavior change;
- no phase transition;
- no future-phase work;
- required checks are lightweight and appropriate for documentation, reports, examples,
  or sync proof.

### Auto-Executable L1 Categories

Mode A may auto-execute L1 tasks only when the user has explicitly approved the task or
the issued task is clearly within a previously approved L1 route, backed by a design note
or audit, and includes explicit acceptance criteria.

Eligible L1 categories include:

- passive immutable records;
- passive wrapper records;
- passive adapter records;
- passive fixture records;
- passive diagnostic records;
- validation tests for passive records;
- package boundary smoke tests;
- import boundary smoke tests;
- no-op protocol or selector boundaries that do not affect default behavior;
- process mirror support tasks that remain passive, such as templates or validation
  scaffolding, when explicitly scoped and not modifying the local skill.

Required L1 conditions:

- no solver calls unless explicitly approved and still behavior-neutral;
- no change to default solve paths;
- no change to solver dispatch;
- no change to backend selector behavior;
- no public CLI change;
- no JSON model or solution schema change;
- no dependency, build, packaging, or native implementation change;
- deterministic tests or checks cover validation behavior;
- acceptance criteria state what remains unchanged.

If any required L1 condition is missing, Mode A must stop with a Decision Packet or Scope
Expansion Packet instead of executing.

## Hard-Stop L2 Categories

Mode A must stop before executing L2 tasks unless the user explicitly approves the exact
issued task.

Hard-stop L2 categories include:

- solver behavior changes;
- LP algorithm behavior changes;
- MIP search behavior changes;
- branch-and-bound node ordering, pruning, branching, incumbent, or log behavior changes;
- presolve behavior changes;
- cut materialization into relaxations;
- callback behavior that can mutate solve behavior;
- decomposition solve-loop integration with LP or MIP solvers;
- stochastic or robust deterministic-equivalent behavior beyond a scoped toy boundary;
- backend behavior changes;
- solver dispatch changes;
- backend selector behavior changes;
- public CLI contract changes;
- JSON model or solution schema changes;
- public API behavior changes that affect existing users;
- numerical convention changes;
- any change that requires broad regression proof beyond the issued task.

L2 approval must name:

- the exact task file;
- the permitted behavior change;
- files allowed to change;
- tests required to prove no unintended regression;
- behavior that must remain unchanged.

## Hard-Stop L3 Categories

Mode A must stop before executing L3 tasks unless the user explicitly approves the exact
issued task.

Hard-stop L3 categories include:

- phase start;
- phase closure;
- architecture redesign;
- new solver capability lines;
- native implementation;
- native implementation candidate approval;
- native dependency, build, packaging, platform, or generated-artifact policy changes;
- solver dispatch to native backend;
- Phase 9 closure;
- Phase 10 planning;
- Phase 10 implementation;
- local `silo-development-operator` skill behavior changes;
- task-system rule changes in `tasks/README.md`;
- broad project operating policy changes.

L3 approval must be explicit. Planning approval does not approve implementation.
Closure approval does not approve the next phase. Native policy approval does not approve
native implementation.

## Standing Approval Revocation Conditions

Standing approval is revoked if a task includes or requires any of the following:

- solver behavior changes;
- solver dispatch changes;
- backend selector behavior changes;
- public CLI behavior changes;
- JSON model or solution schema changes;
- dependency changes;
- build changes;
- packaging changes;
- native implementation;
- native runtime requirements;
- generated native artifacts;
- phase start;
- phase closure;
- future-phase work;
- roadmap or phase-file changes outside an explicitly approved bookkeeping task;
- existing note rewrites outside an explicitly scoped note task;
- local skill changes;
- task-directory rule changes;
- dirty worktree before execution that is not part of an approved recovery task;
- remote sync status other than `synchronized_with_origin`, unless the user explicitly
  approves recovery or continuing despite the sync state;
- missing task ID scan;
- missing report path;
- missing acceptance criteria for L1 work;
- required checks failing;
- discovery that the task is broader than one atomic objective.

When standing approval is revoked, Codex should stop and report the reason. If useful, it
should provide a Decision Packet, Failure Packet, or Scope Expansion Packet.

## Interaction With Phase Technical Route

The Phase Technical Route defines the current decision corridor. This profile can only
operate inside that corridor.

Current allowed low-risk actions include narrow `.silo-dos/` process documentation,
audits, reports, and other user-requested process refinements. Current forbidden default
actions include native implementation, Phase 9 closure, Phase 10 planning, Phase 10
implementation, solver dispatch changes, public native CLI controls, and native JSON
schema controls.

Use this lookup order:

1. Current user instruction.
2. Issued task contract.
3. `.silo-dos/technical_route.md`.
4. `.silo-dos/decision_log.md`.
5. This standing approval profile.
6. `.silo-dos/experience_map.md`.
7. `tasks/README.md`, `AGENTS.md`, `ROADMAP.md`, `tasks/phases/`, and recent reports.

If the Technical Route says an action requires explicit approval, this profile cannot
make it auto-executable.

## Interaction With Remote Sync Proof

Remote Sync Proof is a gate before and after task execution.

Before starting a new task:

- worktree must be clean;
- branch must be the expected branch;
- `git rev-list --left-right --count origin/main...HEAD` should be `0 0`;
- `remote_sync_status` should be `synchronized_with_origin`, unless the user explicitly
  approves recovery or continuing despite the sync state.

After committing and attempting push:

- record `git status --short`;
- record `git branch --show-current`;
- record `git log --oneline -5`;
- record `git rev-list --left-right --count origin/main...HEAD`;
- record `git push result`;
- record `remote_sync_status`.

If push fails, preserve the local commit, record the failure, and do not start another
development task until sync-only recovery or a clean `0 0` proof exists.

## Decision Packet Triggers

Produce a Decision Packet when:

- a task appears L2 or L3;
- user approval is missing or ambiguous;
- the Technical Route and current user request disagree;
- Research Brain or chat context proposes a move not mirrored locally;
- a task would start Phase 10 or close Phase 9;
- a task would approve, revise, reject, or implement a native path;
- standing approval is revoked by any listed condition.

## Failure Packet Triggers

Produce a Failure Packet when:

- required checks fail;
- a push fails and the task cannot safely amend the report;
- the worktree becomes dirty outside allowed files;
- the intended task ID collides with an existing task/report prefix;
- expected input files are missing.

## Scope Expansion Packet Triggers

Produce a Scope Expansion Packet when completion would require:

- files outside the allowed changes;
- solver source changes for a docs or process task;
- tests for a task that forbids tests;
- roadmap or phase-file changes for a non-phase task;
- public CLI or JSON schema changes;
- native implementation or build changes;
- a second atomic task.

## Non-Goals

This profile does not:

- modify the local `silo-development-operator` skill;
- change `tasks/README.md`;
- approve Phase 9 closure;
- approve Phase 10 planning or implementation;
- approve native implementation;
- approve solver dispatch changes;
- approve public CLI or JSON schema changes;
- remove the one-task-at-a-time rule;
- remove the need for reports, checks, commits, or sync proof.

## Maintenance Rule

Update this profile only through a separate atomic SILO-DOS task. Revisit it when:

- the Phase Technical Route changes;
- a phase starts or closes;
- native implementation is approved, rejected, or permanently parked;
- task-system rules change;
- the local operator skill is upgraded to read `.silo-dos/` directly;
- repeated future reports show that an approval category is too broad or too narrow.
