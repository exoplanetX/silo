# SILO Self-Evolution

## Role Of This File

This file defines how SILO-DOS may improve its own operating process without silently
changing solver behavior, approval gates, phase status, or the local operator skill.

Self-evolution is a controlled process loop. It turns repeated friction into scoped
process improvements only when repository evidence supports the change. It does not
authorize multi-task execution, native implementation, Phase 10 work, solver dispatch
changes, public CLI changes, JSON schema changes, or local skill edits.

## Sources

Primary inputs:

- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/remote_sync_proof.md`
- `.silo-dos/experience_map.md`
- `.silo-dos/standing_approval_profile.md`

Stable repository rules:

- `tasks/README.md`
- `AGENTS.md`
- `ROADMAP.md`
- `tasks/phases/`

## Current Route Assumption

This file is written for the current corridor:

```text
phase9_parked_on_design_bookkeeping_after_native_defer
```

Native implementation remains deferred and unapproved. Phase 9 closure is not approved.
Phase 10 has not started. Self-evolution may refine SILO-DOS process documentation under
`.silo-dos/`, but it must not change these route facts.

## Self-Evolution Loop

Use this loop when process friction recurs:

1. Observe: identify a friction signal in reports, interrupted runs, user corrections,
   sync proof, or task handoffs.
2. Evidence: collect source reports or local mirror files that support the signal.
3. Classify: decide whether the possible improvement is L0, L1, L2, or L3.
4. Choose destination: decide whether the lesson belongs in a report, `.silo-dos`,
   Research Brain, the local skill, or nowhere.
5. Issue one task: create exactly one atomic process task if a repository change is
   justified.
6. Execute only if allowed: use the Standing Approval Profile, Phase Technical Route, and
   Remote Sync Proof gates.
7. Verify: run required checks and inspect forbidden-file boundaries.
8. Record: create the matching report and remote sync proof.
9. Stop: do not continue to a second process or solver task.

The loop is intentionally slow enough to preserve project control.

## Detecting Process Friction

Process friction is an operating problem that consumes user or agent time without
directly advancing solver capability. It can be detected from:

- repeated user corrections;
- repeated interrupted runs;
- repeated Decision Packets for the same kind of task;
- repeated Failure Packets with the same cause;
- repeated Scope Expansion Packets;
- recurring push failures or sync uncertainty;
- duplicate task attempts or task ID confusion;
- stale route assumptions;
- missing decision evidence;
- repeated ambiguity about L0/L1/L2/L3 classification;
- repeated uncertainty about whether a lesson belongs locally or in Research Brain.

Do not treat a single isolated inconvenience as process friction unless it blocks the
current task or crosses a hard approval gate.

## Improvement Candidate Format

Before proposing a process improvement, write or report a candidate in this format:

```text
candidate_id:
friction_signal:
evidence_sources:
affected_workflow:
proposed_destination:
risk_level:
allowed_changes:
forbidden_changes:
auto_action_rule:
approval_required:
checks:
expected_report:
stop_conditions:
success_condition:
no_action_option:
```

Field guidance:

- `candidate_id`: stable short id, such as `SE-YYYYMMDD-01`.
- `friction_signal`: the repeated issue or blocker.
- `evidence_sources`: task reports, `.silo-dos` files, or current user instruction.
- `affected_workflow`: Mode A, Mode B, Mode C, sync-only, phase transition, or local
  mirror maintenance.
- `proposed_destination`: report only, `.silo-dos` file, Research Brain, local skill,
  or no action.
- `risk_level`: L0, L1, L2, or L3.
- `allowed_changes`: exact files or directories.
- `forbidden_changes`: explicit exclusions.
- `auto_action_rule`: whether Mode A can execute or must stop.
- `approval_required`: exact approval gate, if any.
- `checks`: required local commands or tests.
- `expected_report`: matching report path.
- `stop_conditions`: conditions that prevent execution.
- `success_condition`: how the process improvement will be judged useful.
- `no_action_option`: why doing nothing may be safer.

## Destination Rules

### Update `.silo-dos` Local Mirror Files

Update `.silo-dos` when:

- the lesson is stable and repository-local;
- Codex should be able to read it without chat context;
- multiple reports support the pattern;
- the change can be made in one atomic process task;
- the change does not require modifying solver source, tests, examples, roadmap, phase
  files, existing notes, or the local skill;
- the change stays within the current Phase Technical Route.

Good destinations:

- `.silo-dos/project_profile.md` for stable identity, boundaries, and status.
- `.silo-dos/technical_route.md` for current decision corridor and phase movement rules.
- `.silo-dos/decision_log.md` for durable decisions.
- `.silo-dos/remote_sync_proof.md` for synchronization proof rules.
- `.silo-dos/experience_map.md` for high-confidence reusable patterns.
- `.silo-dos/standing_approval_profile.md` for standing auto-execution and hard-stop
  categories.
- `.silo-dos/self_evolution.md` for process-upgrade mechanics.

Do not update `.silo-dos` to record a one-off event, personal preference with no current
repository relevance, or speculative future strategy.

### Export Lessons To Research Brain

Export a lesson to Research Brain when:

- the lesson is strategic, cross-project, or method-style knowledge;
- the lesson concerns the user's long-term preferences rather than a SILO repository
  rule;
- the lesson affects future phase strategy but is not yet locally approved;
- the local mirror should not become a large memory dump;
- a Research Brain note would help future ChatGPT planning before a repository task is
  issued.

Research Brain may propose, but repository-local execution must still follow:

```text
local mirror -> Research Brain -> user decision
```

Exporting a lesson to Research Brain does not approve a repository change.

### Propose Local Skill Changes

Propose a local `silo-development-operator` skill change only when:

- the same process friction recurs across several tasks;
- `.silo-dos` documentation alone is not enough;
- the desired behavior affects how the operator reads files, creates packets, classifies
  risk, or enforces gates;
- the change can be scoped to the local skill in a separate task;
- the user explicitly approves the local skill update task.

Skill changes are at least L3 process-governance work unless a future rule classifies a
very narrow edit differently. They must not be bundled with solver development tasks or
ordinary `.silo-dos` mirror updates.

Examples of possible skill-change candidates:

- teach the operator to read `.silo-dos/` files before scanning broad reports;
- generate Remote Sync Proof blocks automatically;
- stop automatically when `origin/main...HEAD` is not `0 0`;
- produce a standard improvement candidate packet when repeated friction is detected.

Do not modify the local skill inside a `.silo-dos` documentation task.

### Record In Report Only

Record the lesson only in the current report when:

- the issue is narrow to one task;
- evidence is not yet high-confidence;
- a broader issue is discovered but is outside the current scope;
- no repository-level rule needs to change;
- the next action needs user review first.

The report may recommend a future atomic task, but recommendation is not execution
permission.

### Take No Action

Take no action when:

- the friction is isolated and unlikely to recur;
- the cost of adding process rules exceeds the benefit;
- the change would duplicate an existing `.silo-dos` rule;
- the issue is already handled by `tasks/README.md`, `AGENTS.md`, or the standing
  approval profile;
- evidence is missing or ambiguous;
- the improvement would loosen a hard gate;
- the improvement would start a new phase, close a phase, or approve native work without
  explicit user instruction.

Doing nothing should be recorded only if it affects the current task outcome.

## Risk Classification For Process Improvements

### L0 Process Documentation

Examples:

- add a `.silo-dos` local mirror file;
- add a process report;
- add a process audit;
- document a high-confidence recurring pattern;
- define a template without changing how code executes.

Mode A may auto-execute L0 process documentation when Remote Sync Proof is clean and the
allowed files are narrow.

### L1 Process Support

Examples:

- add passive process templates;
- add passive validation for task/report formats;
- add tests for passive process metadata;
- add package boundary smoke tests that do not change solver behavior.

Mode A may execute L1 only if the Standing Approval Profile conditions are satisfied and
acceptance criteria are explicit.

### L2 Process-Behavior Change

Examples:

- change how solver commands are dispatched;
- change public CLI or JSON schemas for process metadata;
- change backend selector behavior;
- change default test or solve behavior.

Mode A must stop before L2 unless the user explicitly approves the exact task.

### L3 Process Governance

Examples:

- update the local `silo-development-operator` skill;
- change `tasks/README.md` task-system rules;
- change phase-transition policy;
- start or close a phase;
- approve native implementation;
- redesign SILO-DOS architecture.

Mode A must stop before L3 unless the user explicitly approves the exact task.

## Required Examples

### Repeated L1 Interruptions

Friction signal:

- Several L1 passive-record tasks require repeated approval language even when they share
  the same passive constraints.

Candidate response:

- If evidence is high-confidence, update `.silo-dos/standing_approval_profile.md` or
  `.silo-dos/experience_map.md` to clarify the eligible L1 categories.
- If the local skill still cannot apply the rule reliably, propose a separate local skill
  update task.

Stop conditions:

- the L1 task touches solver behavior, dispatch, CLI, JSON schemas, native dependencies,
  build files, packaging, phase state, or future-phase work;
- acceptance criteria are missing;
- design evidence is missing.

No-action option:

- keep requiring explicit approval when the apparent L1 category is new or not clearly
  passive.

### Push Failure Patterns

Friction signal:

- Reports repeatedly show `Recv failure: Connection was reset`, SSL read failures, or
  local commits preserved after failed push attempts.

Candidate response:

- Update `.silo-dos/remote_sync_proof.md` when the proof fields or statuses need
  refinement.
- Use sync-only recovery when a task ends with `push_failed`.
- Do not start another development task unless `origin/main...HEAD` is `0 0` or the user
  explicitly approves recovery or continuing.

Stop conditions:

- worktree is dirty;
- branch is not expected;
- local and remote are behind or diverged;
- repeated push retry would occur inside the same task.

No-action option:

- if a later preflight already shows `0 0`, treat the repository as synchronized and do
  not create another process rule.

### Duplicate Task Attempts

Friction signal:

- The same date/task prefix is nearly reused, an untracked malformed task file appears,
  or the user asks to continue after an interrupted run without clear task identity.

Candidate response:

- Use task ID scan before writing a new task.
- Record task-system debt in the report if historical collisions exist.
- Create a new task only with the next available `TT` and `RR = 01` for unrelated work.

Stop conditions:

- an existing `YYYYMMDD-TT-RR` prefix would be reused for a different slug;
- an existing task file would need editing, moving, or deleting without explicit task-file
  maintenance approval;
- the interrupted task state is unclear.

No-action option:

- if no collision or malformed task exists, proceed without adding new process rules.

### Stale Route Assumptions

Friction signal:

- A request assumes a phase has started, closed, or changed state, but `.silo-dos`,
  `ROADMAP.md`, phase files, or decision reports show a different status.

Candidate response:

- Read `.silo-dos/technical_route.md` and `.silo-dos/decision_log.md`.
- If route facts are stale, issue a route-update task only when user instruction and
  source reports support it.
- If route movement crosses L3, stop with a Decision Packet.

Stop conditions:

- Phase 9 closure, Phase 10 planning, native implementation, or phase status changes are
  implied without explicit user approval;
- local mirror and current user instruction conflict;
- decision evidence is missing.

No-action option:

- if the route is still valid, record no change and continue only within the current
  corridor.

### Missing Decision Evidence

Friction signal:

- Codex cannot find the report, note, or decision entry that proves an approval, defer,
  closure, phase start, native candidate, or route change.

Candidate response:

- Stop and ask for user decision or create a decision-audit task if scoped.
- Add a future decision-log maintenance task only after evidence is found.
- Do not infer approval from candidate tasks, design notes, or recommendations.

Stop conditions:

- missing evidence would affect L2/L3 behavior;
- implementation would proceed based on assumption;
- a local mirror entry conflicts with source reports.

No-action option:

- if the missing evidence concerns an optional future candidate, leave the candidate
  unexecuted and record the uncertainty in the report.

## Improvement Candidate Workflow

When an improvement candidate is warranted:

1. Verify Remote Sync Proof is clean before starting.
2. Scan task IDs.
3. Create exactly one task contract under `tasks/codex/`.
4. Keep allowed files narrow.
5. Declare forbidden changes explicitly.
6. Classify risk.
7. Execute only if Mode A and standing approval permit it.
8. Create the matching report.
9. Run required checks.
10. Commit and push if the task Git mode allows it.
11. Stop after one atomic task.

## Non-Goals

Self-evolution does not:

- modify solver source code;
- modify tests;
- modify examples;
- modify `ROADMAP.md`;
- modify `tasks/phases/`;
- modify existing notes;
- modify existing task files;
- modify the local `silo-development-operator` skill;
- start Phase 10;
- close Phase 9;
- implement native backend;
- add dependencies;
- modify build or packaging files;
- change public CLI behavior;
- change JSON schemas;
- change solver dispatch;
- permit multi-task execution.

## Maintenance Rule

Update this file only through a separate atomic process task. Revisit it when:

- `.silo-dos` gains templates or archive rules;
- the local skill is upgraded to v0.4;
- repeated future reports show a new type of friction;
- a process rule proves too broad or too narrow;
- the Phase Technical Route changes;
- Research Brain and local mirror responsibilities are revised by explicit user decision.
