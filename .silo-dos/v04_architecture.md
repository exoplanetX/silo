# SILO-DOS v0.4 Architecture Design

## Purpose

SILO-DOS v0.4 should turn the current task operating discipline into a repository-visible
project operating layer. The goal is not to make the solver more automatic. The goal is
to make the development memory, technical route, decision boundaries, and process
evolution easier to inspect, reuse, and audit without relying on scattered chat context
or user-local skill text.

The proposed v0.4 system has four cooperating parts:

- Project Profile: stable project identity, standing boundaries, and approval profile.
- Technical Route: phase-level decision corridors and candidate atomic task sequences.
- Experience Map: extracted lessons from historical reports and interrupted runs.
- Self-Evolution Loop: controlled updates to SILO-DOS itself.

This note is design-only. It does not create the full `.silo-dos/` file set, modify the
local `silo-development-operator` skill, change solver code, close Phase 9, start Phase
10, or implement native backend work.

## Why SILO-DOS Is Currently Too Scattered

SILO-DOS works, but its knowledge is distributed across too many surfaces:

- `tasks/README.md` defines folder rules and general SILO-DOS behavior.
- `AGENTS.md` defines solver and task-management rules for coding agents.
- `tasks/phases/` records long-term phase plans and closure notes.
- `tasks/codex/` stores immutable task contracts.
- `tasks/reports/` stores execution memory, checks, push failures, and next-task
  recommendations.
- `notes/` stores design decisions and method boundaries.
- The local `silo-development-operator` skill stores Mode A/B/C, risk gates, and packet
  behavior.
- ChatGPT or Research Brain context may hold higher-level route decisions that are not
  always mirrored locally.

This distribution creates four frictions:

- Context assembly cost: each new run must rediscover which files matter.
- Decision lookup ambiguity: Codex may not know whether to trust local files, Research
  Brain memory, or the current user message when they differ.
- Process drift risk: improvements such as remote sync proof appear in reports but are
  not promoted into a stable project profile.
- Human-time leakage: the user must repeatedly restate stable preferences, phase
  boundaries, and approval patterns.

v0.4 should reduce this scatter by creating a compact repository-local mirror of stable
operating knowledge while preserving the user's authority over strategic decisions.

## Proposed `.silo-dos/` Directory Structure

The proposed full structure is:

```text
.silo-dos/
  project_profile.md
  technical_route.md
  decision_log.md
  experience_map.md
  standing_approval_profile.md
  remote_sync_proof.md
  self_evolution.md
  templates/
    task_contract.md
    execution_report.md
    decision_packet.md
    failure_packet.md
    scope_expansion_packet.md
  archive/
    ...
```

Only this file is created in the present task:

```text
.silo-dos/v04_architecture.md
```

The other files are candidate follow-up artifacts. They should be created one atomic task
at a time after user approval.

## File Roles

### `project_profile.md`

Records stable project identity and operating boundaries:

- repository purpose;
- dependency direction;
- public API and schema caution;
- current phase status;
- standing non-goals;
- current native-backend defer status;
- user-approved process conventions.

It should summarize stable rules, not duplicate every report.

### `technical_route.md`

Records the current phase route and future candidate corridors:

- phase objectives;
- active and parked phases;
- candidate task sequences;
- approval gates;
- non-goals;
- closure criteria;
- conditions for starting the next phase.

It should be a route map, not a task queue.

### `decision_log.md`

Records decisions that should survive chat compaction:

- phase start approvals;
- phase closure approvals;
- native implementation defer/reject/approval decisions;
- CLI/schema/public-contract decisions;
- dependency/build decisions.

It should store durable decisions and references to the source task/report.

### `experience_map.md`

Extracts lessons from historical reports:

- recurring push failures;
- interrupted-run recovery patterns;
- task ID collision avoidance;
- scope-gate examples;
- useful check sets by task type;
- lessons from phase closure and audit runs.

It should turn repeated experience into reusable operational guidance.

### `standing_approval_profile.md`

Records stable approval preferences that do not override explicit task rules:

- L0 docs/audits/bookkeeping are usually auto-executable in Mode A.
- L1 passive records/no-op boundaries/regression tests may be auto-executable only when
  backed by design notes and explicit acceptance criteria.
- L2/L3 execution gates require explicit approval.
- Phase starts, phase closures, native implementation, dependencies, public CLI, JSON
  schema, and solver dispatch changes always require explicit approval.

It should reduce repetition while preserving user control.

### `remote_sync_proof.md`

Defines how a run proves whether GitHub synchronization actually happened:

- record `git status --short`;
- record `git branch --show-current`;
- record `git log --oneline -3`;
- after push, record push output;
- record `git rev-list --left-right --count origin/main...HEAD`;
- treat `0 0` as local tracking sync proof;
- if push fails, preserve the local commit, record the error, and do not retry unless a
  later sync-only task is requested.

It should make sync state explicit even when network connectivity is unstable.

### `self_evolution.md`

Defines how SILO-DOS may improve itself:

- identify process pain in reports;
- classify the improvement risk;
- create a process-only task;
- update the relevant `.silo-dos/` file or local skill only when explicitly scoped;
- record before/after behavior;
- preserve one-task-at-a-time execution.

It should prevent process upgrades from silently changing solver development behavior.

## Local Mirror Vs Research Brain

v0.4 should separate repository-local memory from Research Brain memory.

### Local Mirror

The local mirror is the `.silo-dos/` directory. It should contain stable, auditable
operating knowledge that Codex can read from the repository:

- current profile;
- approved standing boundaries;
- technical route;
- durable decisions;
- lessons extracted from reports;
- templates and check conventions.

The local mirror should be concise and source-linked. It should not become a second copy
of every task report.

### Research Brain

Research Brain is the broader strategic memory held outside the repository. It may keep:

- long-horizon research strategy;
- cross-project user preferences;
- higher-level method taste;
- candidate directions that are not yet repository-approved;
- oral or chat-level reasoning before it becomes a local decision.

Research Brain can propose, but it should not silently override the local repository.

### User

The user remains the final authority for:

- phase starts;
- phase closures;
- native implementation approval;
- dependencies and build changes;
- public CLI and JSON schema changes;
- solver dispatch changes;
- any disagreement between local mirror and Research Brain.

## Decision Lookup Chain

v0.4 should use this lookup chain:

```text
local mirror -> Research Brain -> user decision
```

### Step 1: Local Mirror

Codex first checks repository-visible rules:

- `.silo-dos/` files once created;
- `tasks/README.md`;
- `AGENTS.md`;
- `ROADMAP.md`;
- `tasks/phases/`;
- recent `tasks/reports/`;
- relevant `notes/`.

If the answer is stable and unambiguous, the task follows the local mirror.

### Step 2: Research Brain

If the local mirror lacks the strategic answer, Research Brain may provide:

- candidate direction;
- phase interpretation;
- route alternatives;
- strategic non-goals.

Research Brain input should become local only through an explicit task.

### Step 3: User Decision

If the local mirror and Research Brain conflict, or if the decision crosses L2/L3 gates,
the user decides. Codex must stop with a Decision Packet instead of guessing.

## Phase Technical Route And Decision Corridor

v0.4 should introduce a Phase Technical Route / Decision Corridor mechanism.

### Phase Technical Route

For each active or upcoming phase, the route should state:

- phase goal;
- current status;
- completed artifacts;
- accepted conventions;
- explicit non-goals;
- candidate atomic task sequence;
- risk level for each candidate;
- required approvals;
- closure readiness criteria.

### Decision Corridor

A Decision Corridor is the set of allowed next moves from the current project state. It
is narrower than the whole roadmap.

For example, after the Phase 9 defer decision, the corridor is:

- remain parked;
- revise or reject the native candidate;
- approve a specific native implementation path through an L3 task;
- prepare Phase 9 closure with explicit approval;
- start Phase 10 planning with explicit approval.

It does not include automatic native implementation, automatic Phase 9 closure, or Phase
10 implementation.

## Experience Map Extraction

The Experience Map should be built from historical reports, not from memory alone.

Useful extraction fields include:

- task ID;
- task type;
- risk level;
- files changed;
- checks run;
- push result;
- stop reason;
- scope issue, if any;
- useful next-action rule;
- process lesson.

Examples already visible in reports:

- Push can fail due to network resets; reports should preserve local commits and record
  failure.
- Some completed commits later synchronize successfully, so sync proof should include
  ahead/behind state.
- Phase closure tasks must not start the next phase.
- Native backend work requires decision packets and explicit L3 approval.
- Reports are the right place for broader issues discovered during narrow tasks.

The Experience Map should not rewrite history. It should summarize recurring lessons
with links to source reports.

## Self-Evolution Loop

SILO-DOS should improve through a controlled loop:

1. Observe: reports identify repeated friction, such as push uncertainty or scattered
   project rules.
2. Classify: decide whether the improvement is L0 process documentation, L1 tool support,
   L2 behavior change, or L3 strategic process architecture.
3. Issue: create exactly one process task.
4. Execute: modify only scoped process files.
5. Verify: run lightweight checks and inspect forbidden-file boundaries.
6. Record: create the matching report.
7. Stabilize: promote the lesson into `.silo-dos/` only when useful.

The loop must not silently alter solver behavior, approval gates, or phase status.

## Remote Sync Proof

Remote sync should be treated as a checkable state, not an assumption.

Recommended proof fields:

- branch name;
- latest local commit;
- push command result;
- `git rev-list --left-right --count origin/main...HEAD`;
- final working tree status;
- whether the pushed branch is synchronized.

Interpretation:

- `0 0`: local tracking branch and HEAD are synchronized.
- `0 N`: local branch is ahead by `N` commits; push did not complete or remote tracking
  did not update.
- `N 0`: local branch is behind and should not start new work without sync review.
- `N M`: branches diverged and require explicit recovery.

If push fails, Codex should not retry repeatedly inside the same task. It should record
the failure and preserve the local commit.

## Standing Approval Profile

v0.4 should make standing approval easier to inspect without weakening hard gates.

Suggested profile:

- Auto-acceptable in Mode A when scoped clearly: L0 documentation, reports, audits,
  bookkeeping, and task-system cleanup.
- Auto-acceptable only with explicit acceptance criteria: L1 passive dataclasses,
  protocols, no-op boundaries, diagnostics records, and regression tests.
- Always approval-gated: L2 solver behavior, backend behavior, public CLI, JSON schema,
  presolve, LP/MIP logic, and solver dispatch.
- Always approval-gated: L3 phase start, phase closure, architecture redesign, native
  implementation, dependency/build policy changes, and new solver capability lines.

The standing profile is advisory. Current user instructions and issued task contracts
take precedence.

## v0.4 Non-Goals

v0.4 should not:

- replace `tasks/README.md` as the task directory rule source in the same step;
- rewrite historical task files or reports;
- move phase files out of `tasks/phases/`;
- create a large project-management framework;
- automate multi-task execution;
- remove user approval gates;
- let Research Brain override repository-local decisions silently;
- change solver code, tests, CLI, JSON schemas, dependencies, or dispatch;
- start Phase 10;
- implement native backend work;
- update the local `silo-development-operator` skill without a separate scoped task.

## Candidate Follow-Up Atomic Tasks

The following tasks are candidates only. They are not issued by this design note.

1. Create `.silo-dos/project_profile.md` from stable repository rules and the milestone
   audit.
2. Create `.silo-dos/technical_route.md` with the current Phase 9 parked corridor and
   conditions for Phase 9 closure or Phase 10 planning.
3. Create `.silo-dos/remote_sync_proof.md` and update future report expectations for
   sync status.
4. Create `.silo-dos/experience_map.md` from recent reports, especially push failures,
   phase closures, and native decision gates.
5. Create `.silo-dos/standing_approval_profile.md` from v0.3 user approval patterns.
6. Draft a local skill v0.4 upgrade task that teaches `silo-development-operator` to read
   `.silo-dos/` files before falling back to scattered reports.
7. Add task/report templates under `.silo-dos/templates/` in a separate process task.
8. Audit whether `tasks/README.md` should reference `.silo-dos/` as a local project
   mirror after the first stable files exist.

Each follow-up should remain one atomic task.

## Acceptance Boundary

This architecture note designs SILO-DOS v0.4. It does not implement v0.4 behavior in the
local skill, create the full `.silo-dos/` directory tree, change solver code, close Phase
9, start Phase 10, or approve native implementation.
