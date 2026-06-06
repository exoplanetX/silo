# SILO-DOS v0.4 Local Skill Integration Design

## Role Of This Design

This note designs how a future `silo-development-operator` v0.4 local skill should use
the repository-local `.silo-dos/` mirror as its primary project decision source.

This is a design note only. It does not modify the local skill, change task-system
rules, alter solver behavior, close Phase 9, start Phase 10, or approve native backend
implementation.

## Sources

Primary `.silo-dos/` inputs:

- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/remote_sync_proof.md`
- `.silo-dos/experience_map.md`
- `.silo-dos/standing_approval_profile.md`
- `.silo-dos/self_evolution.md`

Supporting repository inputs:

- `tasks/README.md`
- `AGENTS.md`
- `ROADMAP.md`
- `tasks/phases/`
- recent `tasks/reports/`
- `tasks/reports/20260606-01-01_silo-dos-v04-local-mirror-pilot_report.md`

## Purpose

The v0.4 local skill integration should reduce repeated context assembly while
preserving SILO-DOS safety.

The upgraded skill should:

- read `.silo-dos/` first for stable project status, route, approvals, sync proof, and
  process lessons;
- keep issued task contracts and current user instructions authoritative for the current
  run;
- use Research Brain only when local mirror evidence is missing or intentionally
  strategic;
- stop for user decision when evidence conflicts or an L2/L3 gate appears;
- preserve one-task-at-a-time execution;
- preserve task ID scanning, reports, checks, commits, push attempts, and sync proof.

The goal is not more autonomy. The goal is less repeated manual handoff for decisions
that are already stable and repository-visible.

## Current v0.3 Friction

The current v0.3 skill already enforces Mode A, Mode B, Mode C, risk gates, packets, and
one-task-at-a-time execution. Its remaining friction is that it still asks Codex to
assemble the same scattered context on every run:

- `tasks/README.md` for task rules;
- `AGENTS.md` for solver boundaries;
- `ROADMAP.md` and `tasks/phases/` for phase state;
- recent reports for execution memory;
- notes for design boundaries;
- local skill text for Mode A/B/C behavior;
- current chat for high-level decisions;
- Research Brain for longer-horizon route memory.

The `.silo-dos/` mirror now condenses stable project status and process rules into a
small local set. A v0.4 skill should use that mirror to reduce repeated scanning, while
still falling back to original sources for validation and conflict resolution.

## Startup Read Order

A future v0.4 skill should use this startup sequence.

### Step 0: Git Preflight

Before issuing or executing a task, read:

```text
git status --short
git branch --show-current
git log --oneline -5
git rev-list --left-right --count origin/main...HEAD
```

If the worktree is dirty, stop unless the dirty files are the exact active task artifacts
the user asked to recover or continue.

If `origin/main...HEAD` is not `0 0`, stop unless the user explicitly approves recovery
or continuing despite the sync state. Use `.silo-dos/remote_sync_proof.md` to classify
the state.

### Step 1: Current User Instruction

The current user instruction is the most immediate source for:

- requested mode;
- explicit approval;
- exact task file to execute;
- allowed and forbidden changes;
- whether push is requested.

The skill must not infer approval for L2/L3 work from a general preference.

### Step 2: Issued Task Contract

When executing a specific task file, read the task contract before using broader route
context. The task contract defines:

- objective;
- allowed files;
- forbidden files;
- stop conditions;
- checks;
- report path;
- Git mode.

If the task contract conflicts with the current user instruction or local mirror, stop
with a Decision Packet.

### Step 3: Project Profile

Read `.silo-dos/project_profile.md` for stable project identity and current milestone
state:

- SILO is a conservative educational Python reference solver;
- Phase 0 through Phase 8 are complete;
- Phase 9 is open and parked after native implementation defer;
- native implementation is deferred and unapproved;
- Phase 10 has not started;
- no immediate solver implementation task is required by default.

### Step 4: Technical Route

Read `.silo-dos/technical_route.md` for the current decision corridor:

```text
phase9_parked_on_design_bookkeeping_after_native_defer
```

The route decides whether a candidate action is inside the current corridor, requires
approval, or is forbidden by default.

### Step 5: Decision Log

Read `.silo-dos/decision_log.md` for durable decisions:

- Phase 5 through Phase 8 closures;
- Phase 9 native candidate selection;
- native implementation defer decision;
- Phase 9 parked status;
- Phase 10 not-started status.

The skill should use decision ids and source reports when explaining why a gate applies.

### Step 6: Remote Sync Proof

Read `.silo-dos/remote_sync_proof.md` before starting a task and at the end of a task.

The skill should derive one of:

```text
synchronized_with_origin
local_ahead_origin
push_failed
dirty_worktree
connector_unverified
```

The skill should not start another development task after `push_failed`,
`local_ahead_origin`, or `dirty_worktree` unless the user explicitly approves recovery or
continuing.

### Step 7: Standing Approval Profile

Read `.silo-dos/standing_approval_profile.md` to decide whether Mode A may auto-execute
the candidate task.

The standing approval profile is subordinate to:

- current user instruction;
- issued task contract;
- technical route;
- hard L2/L3 gates;
- remote sync proof.

### Step 8: Experience Map

Read `.silo-dos/experience_map.md` for recurring patterns:

- passive records with validation tests are often L1;
- phase closure is always L3;
- native implementation is always L3;
- push failure requires sync-only recovery;
- design-only planning does not approve implementation;
- examples-only work can be L0 when behavior is unchanged;
- broader issues belong in reports.

The experience map helps classification. It never grants approval by itself.

### Step 9: Self-Evolution

Read `.silo-dos/self_evolution.md` when repeated process friction appears. Use it to
decide whether the next action belongs in:

- the current report only;
- a `.silo-dos/` mirror update;
- Research Brain;
- a future local skill edit;
- no action.

### Step 10: Original Repository Sources

Read original sources when needed for validation, conflicts, or missing local mirror
content:

- `tasks/README.md`
- `AGENTS.md`
- `ROADMAP.md`
- `tasks/phases/`
- recent `tasks/reports/`
- relevant `notes/`

The local mirror summarizes stable facts; the original sources remain the underlying
audit trail.

## Mirror File Interaction

The `.silo-dos/` files should interact as a layered local decision system.

### `project_profile`

Defines who the project is and what its current milestone state is. It answers:

- What kind of solver is SILO?
- What phases are complete?
- What phase is open or parked?
- What default changes are forbidden?
- What checks and task directories are standard?

### `technical_route`

Defines what moves are inside the current route corridor. It answers:

- What actions are allowed now?
- Which actions are forbidden by default?
- Which actions require L2 or L3 approval?
- What are Phase 9 closure and Phase 10 planning conditions?

### `decision_log`

Stores durable approvals, closures, deferrals, and parked-state facts. It answers:

- Which decisions are active?
- What source report proves a decision?
- What reopens or supersedes a decision?

### `remote_sync_proof`

Controls whether a new task may start and how a completed task reports GitHub sync. It
answers:

- Is the worktree clean?
- Is local `main` synchronized with `origin/main`?
- Did push succeed or fail?
- Is sync-only recovery required?

### `standing_approval_profile`

Defines what Mode A may execute automatically and what always stops. It answers:

- Which L0 categories are safe?
- Which L1 categories can be executed only with explicit criteria?
- Which L2/L3 categories hard-stop?
- What revokes standing approval?

### `experience_map`

Provides high-confidence patterns from historical reports. It answers:

- Have similar tasks been safe before?
- What stop conditions appeared repeatedly?
- What proof should be required?

### `self_evolution`

Controls process improvement. It answers:

- Is this friction recurring?
- Should the lesson update `.silo-dos/`, Research Brain, the local skill, a report, or
  nothing?
- Is a future process task needed?

## Decision Lookup Chain

The v0.4 skill should use this chain:

```text
local mirror -> Research Brain query packet -> user decision
```

### Local Mirror

The local mirror is the first project decision source. It includes `.silo-dos/` plus the
source repository files that the mirror references.

Use the local mirror when:

- status is explicit;
- route corridor is explicit;
- approval category is explicit;
- no source conflict is visible;
- the current task is inside standing approval.

### Research Brain Query Packet

If local evidence is missing, stale, or too narrow for a strategic question, the skill
should not guess. It should emit a Research Brain Query Packet:

```text
Research Brain Query Packet

Question:
Local mirror evidence:
Missing or stale evidence:
Possible interpretations:
Risk gate:
Decision needed:
Recommended local artifact if resolved:
```

Research Brain may propose route options, but it does not approve repository execution.

### User Decision

Ask the user to decide when:

- local mirror and Research Brain disagree;
- local mirror and current user request disagree;
- L2 or L3 work is involved;
- source evidence is missing for an approval, closure, phase start, native decision, CLI
  change, schema change, dependency change, or solver behavior change.

## Mode A Under v0.4

Mode A remains auto-one.

Startup behavior:

1. Run Remote Sync Proof preflight.
2. Read the current user instruction.
3. Read `.silo-dos/` in the startup order above.
4. Scan task IDs before writing a task.
5. Generate exactly one task.
6. Classify risk.

Execution behavior:

- Auto-execute L0 tasks when the task is narrow, source-linked, and inside the technical
  route.
- Auto-execute L1 only when the standing approval profile permits it and the task has
  explicit acceptance criteria.
- Stop before L2 and L3 tasks.
- Produce a Decision Packet when stopped by a hard gate.
- Stop after one atomic task.

Mode A must not let standing approval override:

- solver behavior changes;
- backend behavior or dispatch;
- CLI or JSON schema changes;
- native implementation;
- dependency/build/packaging changes;
- phase start or closure;
- Phase 10 planning or implementation;
- dirty worktree or unresolved sync state.

## Mode B Under v0.4

Mode B remains review-gated.

The v0.4 skill should use Mode B when:

- the user wants a task prepared for review;
- the route is unclear;
- a medium/high-risk public contract or solver behavior question appears;
- decision packets or staged review gates are required.

Mode B should read the same `.silo-dos/` startup set, but it should stop at predefined
review gates even when a task could be drafted.

Mode B may create:

- a task file for inspection;
- a design note;
- a decision packet;
- an audit report.

Mode B must not silently execute L2/L3 work.

## Mode C Under v0.4

Mode C remains principal planning mode.

The v0.4 skill should use Mode C when:

- the user asks for phase planning;
- the user asks for architecture or process design;
- Research Brain style reasoning is needed;
- the desired output is a design note, route, candidate sequence, non-goals, or review
  gate.

Mode C may create planning artifacts when scoped by a task. It must not execute
implementation. It must not treat a design note as approval for follow-up
implementation.

For `.silo-dos/` work, Mode C should distinguish:

- designing a future skill behavior;
- modifying the local skill;
- executing solver development.

Only the first category is in scope for this design note.

## Risk Classification

v0.4 should confirm the existing risk classes.

### L0

L0 includes narrow documentation, reports, audits, bookkeeping, process mirror files,
and sync-only recovery when no project files are changed.

### L1

L1 includes passive records, validation tests, no-op boundaries, diagnostics records,
fixtures, and passive process support when backed by design evidence and acceptance
criteria.

### L2

L2 includes solver behavior, LP/MIP/presolve behavior, backend behavior, solver dispatch,
public CLI contracts, JSON schemas, public API behavior, and numerical convention
changes.

### L3

L3 includes phase starts, phase closures, architecture redesign, local skill behavior
changes, task-system rule changes, native implementation, dependency/build/packaging
policy, and new solver capability lines.

Local skill integration itself remains L3 until a future rule narrows a specific edit
class.

## Remote Sync Proof Behavior

The v0.4 skill should make Remote Sync Proof a hard preflight.

Before task issuance:

- stop if `git status --short` is not clean, except for explicit recovery/continuation of
  known task artifacts;
- stop if branch is not expected;
- stop if `origin/main...HEAD` is not `0 0`, unless the user explicitly approves
  recovery or continuing.

After task execution:

- record `git status --short`;
- record `git branch --show-current`;
- record `git log --oneline -5`;
- record `git rev-list --left-right --count origin/main...HEAD`;
- record `git push result`;
- record `remote_sync_status`.

If push fails:

- preserve the local commit;
- record the failure in the report when scoped;
- do not retry repeatedly inside the same task;
- require sync-only recovery or clean `0 0` proof before another development task.

## Standing Approval Interaction

Standing approval should reduce repetition, not weaken gates.

Mode A may apply standing approval only when:

- Remote Sync Proof is clean;
- the Technical Route allows the action;
- the task is L0 or eligible L1;
- acceptance criteria are explicit for L1;
- no forbidden file or behavior is touched;
- no L2/L3 hard-stop category appears.

Standing approval is revoked by:

- solver behavior changes;
- solver dispatch or backend selector behavior changes;
- CLI or JSON schema changes;
- dependency/build/packaging changes;
- native implementation;
- phase start or closure;
- Phase 10 work;
- missing task ID scan;
- failing checks;
- stale or conflicting local mirror evidence.

## Packet Behavior

### Decision Packet

Use when:

- task is L2 or L3;
- approval is missing;
- local mirror and Research Brain disagree;
- current user request and local route disagree;
- Phase 9 closure, Phase 10 planning, native implementation, public CLI/schema, or local
  skill behavior is involved.

### Failure Packet

Use when:

- required checks fail;
- push fails and the report cannot record it in scope;
- the worktree becomes dirty outside allowed files;
- task ID collision occurs;
- a required `.silo-dos/` file is missing and the task cannot safely continue.

### Scope Expansion Packet

Use when:

- completing the task requires forbidden files;
- design work would require local skill edits;
- a process task would need solver/test changes;
- a route update would require phase status changes;
- a second atomic task becomes necessary.

## Missing Or Stale `.silo-dos/` Files

The v0.4 skill should handle missing mirror files conservatively.

If a nonessential file is missing:

- read original repository sources;
- proceed only if the task does not depend on the missing file;
- record the gap in the report.

If an essential file is missing:

- stop with a Failure Packet or Decision Packet;
- recommend a narrow `.silo-dos/` maintenance task;
- do not infer approval from older reports alone when L2/L3 gates are involved.

If a file appears stale:

- compare against source reports or current user instruction;
- treat the newest explicit user decision as controlling for the current turn;
- recommend a local mirror update task if the stale fact should become durable;
- do not silently rewrite existing `.silo-dos/` files unless the current task allows it.

Essential files for v0.4 startup are:

- `project_profile`;
- `technical_route`;
- `decision_log`;
- `remote_sync_proof`;
- `standing_approval_profile`.

Experience and self-evolution files are useful but less likely to block every task.

## Avoiding Circular Assumptions

The local mirror should not prove itself.

The v0.4 skill should avoid circularity by:

- linking local mirror facts to reports, notes, roadmap entries, or phase files;
- using source reports for durable decisions when a mirror entry is questioned;
- treating `.silo-dos/` as an execution mirror, not an independent source of authority;
- requiring a task and report for mirror updates;
- stopping when a mirror fact lacks evidence and affects L2/L3 work.

## Research Brain Disagreement

When Research Brain suggests a route that differs from `.silo-dos/`, the local skill
should stop and report:

```text
Decision Packet

Task or question:
Local mirror position:
Research Brain position:
Source evidence:
Risk level:
What would change if accepted:
Recommended option:
Exact approval sentence:
```

The user decides. If the user accepts the Research Brain route, a future task should
mirror the durable decision into `.silo-dos/` or relevant repository files.

## Required Future Local Skill Changes

A later v0.4 skill upgrade task would need to modify the local
`silo-development-operator` skill to:

1. Add `.silo-dos/` startup read order.
2. Add Remote Sync Proof preflight before issuing tasks.
3. Add local mirror consistency checks before relying on standing approval.
4. Add the Research Brain Query Packet.
5. Prefer `.silo-dos/technical_route.md` and `.silo-dos/decision_log.md` for phase and
   strategic status.
6. Use `.silo-dos/standing_approval_profile.md` and `.silo-dos/experience_map.md` for
   L0/L1 classification support.
7. Use `.silo-dos/self_evolution.md` when process friction recurs.
8. Preserve existing Mode A/B/C, risk gates, reports, commits, push rules, and packet
   behavior.

Those changes are not implemented here.

## Migration Plan

Recommended migration sequence:

1. Design local skill integration. This note.
2. Execute a separate L3 task to update `silo-development-operator` to v0.4.
3. Run a smoke test that asks the upgraded skill to issue one L0 process task using the
   local mirror.
4. Run a hard-stop smoke test that confirms the upgraded skill refuses L2/L3 work without
   approval.
5. Run a sync-proof smoke test that confirms task issuance is blocked when
   `origin/main...HEAD` is not `0 0`.
6. Update `.silo-dos/experience_map.md` only if the smoke tests reveal reusable lessons.

Each migration step should be a separate atomic task.

## Non-Goals

This design does not:

- modify the local `silo-development-operator` skill;
- modify `tasks/README.md`;
- modify `AGENTS.md`;
- modify solver source code;
- modify tests;
- modify examples;
- modify `ROADMAP.md`;
- modify phase files;
- modify existing notes;
- modify existing `.silo-dos/` files;
- approve Phase 9 closure;
- start Phase 10;
- approve native implementation;
- change public CLI behavior;
- change JSON schemas;
- add dependencies;
- modify build or packaging files;
- change solver dispatch or backend selection behavior;
- authorize multi-task execution.

## Candidate Follow-Up Atomic Tasks

The following are candidates only. They are not issued or executed by this design note.

1. Update local `silo-development-operator` to v0.4 so it reads `.silo-dos/` first.
   Risk: L3 process-governance.
2. Create a v0.4 smoke-test task for L0 process-task issuance from the local mirror.
   Risk: L0 if it changes only task/report files.
3. Create a v0.4 hard-stop smoke-test task for L2/L3 gates.
   Risk: L0 audit if no skill or solver files are modified.
4. Create a v0.4 sync-proof smoke-test task.
   Risk: L0 or sync-only depending scope.
5. Add `.silo-dos/templates/` for task, report, packet, and Research Brain query packet
   templates.
   Risk: L0 if passive documentation only.

Do not issue or execute these candidates without a separate user request.

## Current Route Preservation

This design preserves the current route facts:

- SILO Python reference solver milestone is complete for the current educational scope.
- Phase 0 through Phase 8 are complete.
- Phase 9 is open and parked on design/bookkeeping after native defer.
- Native implementation is deferred and not approved.
- Phase 10 has not started.
- No immediate solver implementation task is required.
