# SILO Project Profile

## Role Of This Profile

This file is the repository-local SILO-DOS v0.4 project profile. It summarizes stable
project identity, current milestone status, standing boundaries, and operating rules
that Codex can read before issuing or executing SILO tasks.

This profile is a local mirror. It does not replace:

- `tasks/README.md` as the task-directory and SILO-DOS rule source;
- `AGENTS.md` as the agent-facing solver rule file;
- `ROADMAP.md` as the phase-level status source;
- `tasks/phases/` as long-term phase records;
- `tasks/codex/` as immutable task contracts;
- `tasks/reports/` as execution memory.

If this profile conflicts with a current user instruction, an issued task contract, or a
repository rule file, Codex must stop and resolve the conflict through the usual
SILO-DOS review gate.

## Sources

Primary sources:

- `.silo-dos/v04_architecture.md`
- `tasks/reports/20260604-12-01_project-milestone-audit_report.md`

Supporting sources:

- `tasks/README.md`
- `AGENTS.md`
- `ROADMAP.md`
- recent Phase 9 reports under `tasks/reports/`

## Project Identity

SILO is an educational and conservative optimization solver project. Its current
reference implementation is Python-first. The project emphasizes:

- readable reference algorithms;
- deterministic small tests;
- explicit mathematical conventions;
- conservative phase boundaries;
- one atomic task at a time;
- documented deferred work instead of silent scope expansion.

The current dependency direction is:

```text
core <- modeling <- presolve <- lp <- mip <- cuts/decomposition/uncertainty
```

The `core` package must not depend on LP, MIP, cuts, decomposition, uncertainty, or
native-backend modules.

Native algorithms must not call external solvers. External solvers may appear only in
`interfaces/`, examples, or tests for comparison.

## Current Milestone Status

The current project milestone is:

```text
python_reference_solver_milestone_complete_for_current_educational_scope
```

Interpretation:

- Phase 0 through Phase 8 are complete for their scoped educational/conservative
  milestones.
- Phase 9 remains open and parked on design/bookkeeping after the native implementation
  defer decision.
- Native implementation is not approved.
- Phase 10 has not started.
- No immediate follow-on implementation task is required.

## Phase Status Snapshot

- Phase 0: complete project scaffold.
- Phase 1: complete model core and canonicalization.
- Phase 2: complete educational tableau simplex scope.
- Phase 3: complete enough revised simplex and basis layer for the current LP backend.
- Phase 4: complete conservative presolve, scaling, and numerical diagnostics scope.
- Phase 5: complete minimal branch-and-bound scope.
- Phase 6: complete conservative cut/callback boundary scope.
- Phase 7: complete conservative decomposition boundary scope.
- Phase 8: complete conservative stochastic/robust transformation boundary scope.
- Phase 9: open and parked on design/bookkeeping after native implementation defer.
- Phase 10: not started.

## Parked Phase 9 State

Phase 9 has native-backend planning and passive boundary artifacts:

- conservative native backend boundary design;
- first candidate selection for `tableau_leaving_row_ratio_test`;
- passive backend/interface records;
- candidate-specific parity fixtures;
- candidate-specific unavailable-native diagnostics;
- native build/dependency/generated-artifact policy;
- native implementation decision packet;
- explicit user defer decision;
- post-defer status audit.

The current Phase 9 classification is:

```text
phase9_parked_on_design_bookkeeping_after_native_defer
```

Allowed next strategic directions require explicit user instruction:

- remain parked;
- revise or reject the selected native candidate;
- approve a specific native implementation path through an L3 task;
- prepare Phase 9 closure bookkeeping;
- start Phase 10 planning.

None of these directions should be inferred automatically.

## Native Defer Decision

Native implementation is deferred and unapproved.

The selected candidate, `tableau_leaving_row_ratio_test`, remains Python-reference only
for now. The future approval template in the native decision packet is only a template.
It is not approval.

No task may implement native backend code, add native dependencies, modify build or
packaging files, change solver dispatch, add public CLI controls, or add JSON schema
controls unless a separate explicitly approved task scopes that work.

## Completed Capability Map

SILO currently includes:

- model core and canonicalization;
- tableau simplex;
- revised simplex and basis layer;
- presolve and numerical diagnostics;
- minimal branch-and-bound;
- conservative cut/callback boundary;
- conservative decomposition boundary;
- conservative stochastic/robust transformation boundary;
- native backend planning and passive boundary records.

These capabilities define the current Python reference-solver milestone. They do not
imply production-grade performance or advanced solver features.

## Deliberately Deferred Work

The following work remains deferred:

- advanced MIP features and heuristics;
- real cut families;
- cut materialization into LP relaxations;
- lazy constraints and mutation callbacks;
- production Benders decomposition;
- production column generation;
- branch-and-price;
- broader decomposition integration with LP/MIP solve loops;
- scenario-dependent variables and nonanticipativity constraints;
- broader stochastic and robust transformations;
- public uncertainty CLI or JSON schemas;
- native backend implementation;
- native dependencies, build, packaging, platform support, and native CI behavior;
- solver dispatch to native backend;
- Phase 10 planning or implementation.

## Forbidden Default Changes

Unless an issued task explicitly allows them, Codex must not:

- modify solver source code under `src/`;
- modify tests;
- modify examples;
- modify `ROADMAP.md`;
- modify `tasks/phases/`;
- modify existing notes;
- modify existing task files;
- modify the local `silo-development-operator` skill;
- modify public CLI behavior;
- modify JSON model or solution schemas;
- add dependencies;
- modify build or packaging files;
- implement native backend code;
- change solver dispatch or backend selection behavior;
- close a phase;
- start a new phase;
- continue to a second task.

If completing a task appears to require any forbidden change, Codex must stop and report
through the appropriate SILO-DOS packet.

## Task And Report Directories

Directory roles:

- `tasks/phases/`: long-term phase records and phase-level knowledge.
- `tasks/codex/`: immutable issued Codex task contracts.
- `tasks/reports/`: execution memory for completed or attempted tasks.
- `.silo-dos/`: repository-local mirror for stable operating knowledge.

Task file naming:

```text
tasks/codex/YYYYMMDD-TT-RR_slug.md
```

Report file naming:

```text
tasks/reports/YYYYMMDD-TT-RR_slug_report.md
```

Before creating a new task, scan both `tasks/codex/` and `tasks/reports/` for the
intended date. Use the next available `TT` with `RR = 01` for a new unrelated task.

Existing files under `tasks/codex/` are immutable after creation unless the user
explicitly asks for task-file maintenance.

## Standard Checks

Minimum checks for L0 documentation, report, audit, and bookkeeping tasks:

```text
git status --short
git branch --show-current
git log --oneline -5
git diff --check
```

When staging new files, also prefer:

```text
git diff --cached --check
```

For executable solver changes, use targeted tests relevant to the changed behavior. For
broader or phase-closure work, use the repository quality script when scoped by the task.

Do not run native build commands or native tooling unless an issued task explicitly
approves native build or implementation work.

## Git And Remote Sync

Default task Git mode is `local-commit` unless the task states otherwise. Push only when
the task Git mode is `push-on-success`, the task is `sync-only`, or the user explicitly
requests a push.

When push is attempted, record:

- push output;
- whether push succeeded;
- final working tree status;
- `git rev-list --left-right --count origin/main...HEAD` when useful.

Interpretation:

- `0 0`: local branch and tracked remote are synchronized.
- `0 N`: local branch is ahead by `N` commits.
- `N 0`: local branch is behind and should be synchronized before new work.
- `N M`: local and remote diverged and require explicit recovery.

Push failure is non-fatal. Preserve the local commit, record the failure, and do not
retry repeatedly inside the same task.

## Phase Transition Rules

No phase may start without explicit user approval.

No phase may close without explicit user approval.

Phase planning is separate from phase implementation. A user may approve planning
without approving implementation.

Phase closure is separate from starting the next phase. A closure bookkeeping task must
not issue planning or implementation work for the next phase unless the user explicitly
requests that separate task.

Phase 10 is not started. Any Phase 10 planning task requires explicit user approval.

## Standing Approval Profile

This standing profile guides recommendations but does not override current user
instructions, issued task contracts, `tasks/README.md`, or `AGENTS.md`.

Usually auto-executable in Mode A when scope is clean:

- L0 documentation;
- L0 reports;
- L0 audits;
- L0 bookkeeping;
- task-system cleanup.

Potentially auto-executable only when backed by design notes and explicit acceptance
criteria:

- L1 passive dataclasses;
- L1 protocol records;
- L1 no-op boundaries;
- L1 diagnostic records;
- L1 regression tests.

Always approval-gated:

- L2 solver behavior changes;
- LP/MIP logic changes;
- presolve changes;
- backend behavior changes;
- public CLI changes;
- JSON schema changes;
- solver dispatch changes.

Always approval-gated:

- L3 phase starts;
- L3 phase closures;
- architecture redesign;
- native implementation;
- dependency, build, or packaging changes;
- new solver capability lines.

## Local Mirror Decision Rule

Use this lookup order:

```text
local mirror -> Research Brain -> user decision
```

The local mirror includes `.silo-dos/`, `tasks/README.md`, `AGENTS.md`, `ROADMAP.md`,
`tasks/phases/`, recent `tasks/reports/`, and relevant `notes/`.

If the local mirror lacks a strategic answer, Research Brain may propose a route. If the
route crosses L2/L3 gates or conflicts with repository files, the user must decide.

## Current Recommended Action

No immediate implementation task is required.

Recommended next process action, only when requested:

```text
Create .silo-dos/technical_route.md with the current Phase 9 parked corridor and the
conditions for Phase 9 closure or Phase 10 planning.
```

Do not issue or execute that follow-up automatically.
