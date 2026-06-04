# SILO Experience Map

## Role Of This Map

This file is the repository-local SILO-DOS v0.4 experience map. It extracts reusable
operating patterns from historical task reports and the current `.silo-dos/` local
mirror.

The map is not a substitute for `tasks/README.md`, `AGENTS.md`, `ROADMAP.md`,
`tasks/phases/`, issued task contracts, or current user instructions. It is a compact
memory layer for high-confidence patterns that have appeared repeatedly enough to guide
future SILO-DOS runs.

The map should be conservative. If a pattern is not supported by repository evidence, do
not add it here. If a current task conflicts with a pattern, stop and resolve the conflict
through the normal SILO-DOS review gate.

## Sources

Primary local mirror inputs:

- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/remote_sync_proof.md`

Representative historical evidence:

- `tasks/reports/20260602-06-01_finite-scenarios_report.md`
- `tasks/reports/20260602-08-01_stochastic-wrapper-records_report.md`
- `tasks/reports/20260602-13-01_uncertainty-sets_report.md`
- `tasks/reports/20260602-14-01_robust-wrapper-records_report.md`
- `tasks/reports/20260603-07-01_backend-capability-records_report.md`
- `tasks/reports/20260603-08-01_python-backend-adapter_report.md`
- `tasks/reports/20260603-09-01_backend-conformance-fixtures_report.md`
- `tasks/reports/20260603-11-01_noop-backend-selector_report.md`
- `tasks/reports/20260604-01-01_parity-result-records_report.md`
- `tasks/reports/20260604-04-01_ratio-test-parity-fixtures_report.md`
- `tasks/reports/20260604-06-01_ratio-test-native-diagnostics_report.md`
- `tasks/reports/20260524-02-01_phase5-closure-bookkeeping_report.md`
- `tasks/reports/20260524-13-01_phase6-closure-bookkeeping_report.md`
- `tasks/reports/20260602-04-01_phase7-closure-bookkeeping_report.md`
- `tasks/reports/20260603-04-01_phase8-closure-bookkeeping_report.md`
- `tasks/reports/20260604-03-01_native-kernel-selection_report.md`
- `tasks/reports/20260604-07-01_native-build-policy_report.md`
- `tasks/reports/20260604-09-01_native-decision-packet_report.md`
- `tasks/reports/20260604-10-01_native-defer-bookkeeping_report.md`
- `tasks/reports/20260604-11-01_phase9-post-defer-audit_report.md`
- `tasks/reports/20260604-12-01_project-milestone-audit_report.md`
- `tasks/reports/20260605-02-01_remote-sync-proof_report.md`

## Confidence Legend

- `high`: multiple reports or stable `.silo-dos/` files support the pattern.
- `medium`: one clear report plus aligned project rules support the pattern.
- `low`: not eligible for this map unless later evidence strengthens it.

This initial map includes only `high` confidence patterns.

## Patterns

### EXP-001: Passive Records Plus Validation Tests Are Usually L1

- Pattern id: `EXP-001`.
- Context: A task adds immutable/passive records, passive adapters, passive fixtures, or
  passive diagnostics with validation tests, while avoiding solver calls, solver
  dispatch, public CLI behavior, JSON schemas, native dependencies, build changes, and
  default behavior changes.
- Evidence source:
  - `tasks/reports/20260602-06-01_finite-scenarios_report.md`
  - `tasks/reports/20260602-08-01_stochastic-wrapper-records_report.md`
  - `tasks/reports/20260602-13-01_uncertainty-sets_report.md`
  - `tasks/reports/20260602-14-01_robust-wrapper-records_report.md`
  - `tasks/reports/20260603-07-01_backend-capability-records_report.md`
  - `tasks/reports/20260603-08-01_python-backend-adapter_report.md`
  - `tasks/reports/20260603-09-01_backend-conformance-fixtures_report.md`
  - `tasks/reports/20260603-11-01_noop-backend-selector_report.md`
  - `tasks/reports/20260604-01-01_parity-result-records_report.md`
  - `tasks/reports/20260604-04-01_ratio-test-parity-fixtures_report.md`
  - `tasks/reports/20260604-06-01_ratio-test-native-diagnostics_report.md`
- Auto-action rule: Mode A may auto-execute only when the task is explicitly scoped as
  L1, backed by a design note or prior audit, has clear acceptance criteria, and the
  files and behavior remain passive.
- Stop conditions:
  - solver calls are introduced;
  - default solver behavior changes;
  - solver dispatch or backend selection behavior changes;
  - public CLI or JSON schemas change;
  - native dependencies, build files, packaging, or native code are added;
  - the task lacks explicit acceptance criteria.
- Confidence: high.
- Transferability: Applies to future passive records, metadata, fixtures, diagnostics,
  protocol-like boundaries, and no-op adapters in approved phases.
- Update condition: Revise if a passive-record task later changes public behavior, causes
  unexpected integration risk, or is reclassified by the user as L2/L3.

### EXP-002: Phase Closure Is Always L3 And Separate From Next Phase Start

- Pattern id: `EXP-002`.
- Context: A task marks a phase complete, changes roadmap or phase-record status, or
  records closure bookkeeping.
- Evidence source:
  - `tasks/reports/20260524-02-01_phase5-closure-bookkeeping_report.md`
  - `tasks/reports/20260524-13-01_phase6-closure-bookkeeping_report.md`
  - `tasks/reports/20260602-04-01_phase7-closure-bookkeeping_report.md`
  - `tasks/reports/20260603-04-01_phase8-closure-bookkeeping_report.md`
  - `.silo-dos/decision_log.md`
  - `.silo-dos/technical_route.md`
- Auto-action rule: Do not auto-execute closure in Mode A unless the user explicitly
  approves the exact closure task. Closure bookkeeping must be one atomic task and must
  not issue or start the next phase.
- Stop conditions:
  - user approval is absent or ambiguous;
  - the task also starts the next phase;
  - solver source code, tests, examples, CLI behavior, or JSON schemas would change;
  - the closure audit has unresolved blockers.
- Confidence: high.
- Transferability: Applies to every phase, including possible future Phase 9 closure and
  any later phases.
- Update condition: Revise only if `tasks/README.md` or a user-approved SILO-DOS rule
  changes phase-transition policy.

### EXP-003: Native Implementation Is Always L3

- Pattern id: `EXP-003`.
- Context: A task would implement native backend code, choose a native implementation
  form, add native dependencies, modify build or packaging files, change native dispatch,
  or approve a native implementation path.
- Evidence source:
  - `tasks/reports/20260604-02-01_phase9-readiness-audit_report.md`
  - `tasks/reports/20260604-03-01_native-kernel-selection_report.md`
  - `tasks/reports/20260604-07-01_native-build-policy_report.md`
  - `tasks/reports/20260604-08-01_phase9-policy-readiness-audit_report.md`
  - `tasks/reports/20260604-09-01_native-decision-packet_report.md`
  - `tasks/reports/20260604-10-01_native-defer-bookkeeping_report.md`
  - `.silo-dos/project_profile.md`
  - `.silo-dos/technical_route.md`
  - `.silo-dos/decision_log.md`
- Auto-action rule: Mode A must stop with a Decision Packet before native implementation
  or any native build/dependency/dispatch step. Passive native planning or passive
  metadata does not imply implementation approval.
- Stop conditions:
  - native code, extension modules, binaries, generated artifacts, or compiled outputs
    would be created;
  - dependencies, build files, packaging, CI, solver dispatch, CLI, or JSON schemas would
    change;
  - the approval sentence does not name the exact implementation candidate, files, build
    policy, generated-artifact policy, and no-dispatch boundary.
- Confidence: high.
- Transferability: Applies to Phase 9 and any future native/backend acceleration work.
- Update condition: Revise if the user explicitly approves a new native policy through a
  separate L3 process task.

### EXP-004: Push Failure Requires Sync-Only Recovery

- Pattern id: `EXP-004`.
- Context: `git push` fails after a local commit due to network reset, SSL read failure,
  inability to connect to GitHub, or another remote synchronization error.
- Evidence source:
  - `tasks/reports/20260524-13-01_phase6-closure-bookkeeping_report.md`
  - `tasks/reports/20260604-10-01_native-defer-bookkeeping_report.md`
  - `tasks/reports/20260604-12-01_project-milestone-audit_report.md`
  - `tasks/reports/20260604-15-01_technical-route_report.md`
  - `tasks/reports/20260605-02-01_remote-sync-proof_report.md`
  - `.silo-dos/remote_sync_proof.md`
- Auto-action rule: Preserve the local commit, record the failure in the report when
  scoped, do not retry repeatedly inside the same task, and require sync-only recovery or
  a clean `origin/main...HEAD = 0 0` proof before starting new development work.
- Stop conditions:
  - worktree is dirty after the failed push;
  - `origin/main...HEAD` reports local ahead, behind, or divergence;
  - the user has not explicitly approved recovery or continuing despite the sync state.
- Confidence: high.
- Transferability: Applies to every task with `push-on-success`, explicit push request,
  or sync-only recovery.
- Update condition: Revise if the remote hosting workflow changes or SILO-DOS adopts a
  different remote sync proof standard through a scoped process task.

### EXP-005: Design-Only Planning Does Not Approve Implementation

- Pattern id: `EXP-005`.
- Context: A task creates a design note, planning note, decision packet, technical route,
  native policy, or architecture note.
- Evidence source:
  - `tasks/reports/20260602-05-01_phase8-uncertainty-design_report.md`
  - `tasks/reports/20260603-05-01_phase9-native-backend-design_report.md`
  - `tasks/reports/20260604-03-01_native-kernel-selection_report.md`
  - `tasks/reports/20260604-07-01_native-build-policy_report.md`
  - `tasks/reports/20260604-09-01_native-decision-packet_report.md`
  - `tasks/reports/20260604-13-01_silo-dos-v04-architecture_report.md`
  - `.silo-dos/v04_architecture.md`
  - `.silo-dos/technical_route.md`
- Auto-action rule: Treat planning as planning only. It may define candidate tasks,
  non-goals, and approval gates, but it must not execute implementation unless a later
  issued task explicitly scopes and approves that implementation.
- Stop conditions:
  - the task attempts to create implementation files, tests, examples, CLI behavior, JSON
    schemas, dependencies, build files, or dispatch behavior not allowed by the design
    task;
  - the design crosses L2/L3 gates without explicit approval;
  - a candidate follow-up task is treated as permission to execute.
- Confidence: high.
- Transferability: Applies to phase planning, architecture planning, native/backend
  planning, decomposition/stochastic/robust planning, and SILO-DOS process design.
- Update condition: Revise only if a future task contract explicitly combines design and
  implementation under a user-approved scope.

### EXP-006: Examples-Only Tasks Can Be L0 When Behavior Is Unchanged

- Pattern id: `EXP-006`.
- Context: A task adds checked-in deterministic examples that exercise existing behavior
  without modifying solver source code, tests, public CLI behavior, JSON schemas,
  roadmap, phase records, or generated outputs.
- Evidence source:
  - `tasks/reports/20260602-02-01_decomposition-examples_report.md`
  - `tasks/reports/20260603-01-01_phase8-closure-readiness-audit_report.md`
  - `tasks/reports/20260603-02-01_uncertainty-examples_report.md`
  - `tasks/reports/20260603-03-01_phase8-post-examples-audit_report.md`
- Auto-action rule: Mode A may auto-execute examples-only tasks as L0 when they add only
  examples plus matching task/report files, run deterministic example commands, and leave
  public behavior unchanged.
- Stop conditions:
  - solver source code or tests must change to make the examples pass;
  - examples require new public CLI/schema support;
  - examples create generated outputs or large artifacts;
  - examples imply phase closure or next-phase start without separate approval.
- Confidence: high.
- Transferability: Applies to future educational examples, smoke examples, and scoped
  documentation examples that call existing stable APIs.
- Update condition: Revise if examples begin to serve as public contract changes or need
  dedicated testing policy.

### EXP-007: Research Brain Proposes; `.silo-dos` Executes Locally

- Pattern id: `EXP-007`.
- Context: Long-horizon strategic memory, user preferences, and phase ideas may exist in
  Research Brain or conversation, while Codex must execute from repository-visible rules
  and current user instructions.
- Evidence source:
  - `.silo-dos/v04_architecture.md`
  - `.silo-dos/project_profile.md`
  - `.silo-dos/technical_route.md`
  - `.silo-dos/decision_log.md`
  - `tasks/reports/20260604-13-01_silo-dos-v04-architecture_report.md`
  - `tasks/reports/20260604-14-01_project-profile_report.md`
  - `tasks/reports/20260604-15-01_technical-route_report.md`
- Auto-action rule: Read `.silo-dos/` and repository files first. Use Research Brain for
  strategic suggestions only when the local mirror lacks an answer. If local mirror,
  Research Brain, and user instruction conflict, stop for user decision.
- Stop conditions:
  - Research Brain proposes L2/L3 movement without explicit user approval;
  - a chat recommendation conflicts with an issued task contract or local mirror file;
  - a local mirror file appears stale relative to a current user decision.
- Confidence: high.
- Transferability: Applies to all future SILO-DOS work and to multi-surface task handoff
  between ChatGPT, Codex, and GitHub.
- Update condition: Revise if SILO-DOS v0.4 later changes the local mirror file set or
  gives the local operator skill a new lookup policy.

### EXP-008: L0 Process Mirror Tasks Are Safe When Narrow And Source-Linked

- Pattern id: `EXP-008`.
- Context: A task adds or updates repository-local process documentation under
  `.silo-dos/` without changing solver behavior, task-directory rules, roadmap status,
  phase records, existing notes, tests, examples, public contracts, or the local skill.
- Evidence source:
  - `tasks/reports/20260604-13-01_silo-dos-v04-architecture_report.md`
  - `tasks/reports/20260604-14-01_project-profile_report.md`
  - `tasks/reports/20260604-15-01_technical-route_report.md`
  - `tasks/reports/20260605-01-01_decision-log_report.md`
  - `tasks/reports/20260605-02-01_remote-sync-proof_report.md`
  - `.silo-dos/project_profile.md`
  - `.silo-dos/technical_route.md`
  - `.silo-dos/decision_log.md`
  - `.silo-dos/remote_sync_proof.md`
- Auto-action rule: Mode A may auto-execute a narrow `.silo-dos/` process documentation
  task when it creates exactly one primary mirror artifact, cites stable sources, creates
  the matching task/report, runs documentation checks, commits, and stops.
- Stop conditions:
  - the task changes `tasks/README.md`, `AGENTS.md`, `ROADMAP.md`, phase files, existing
    notes, or the local skill without explicit scope;
  - the task attempts to automate multi-task execution;
  - the task changes phase state, native implementation posture, public contracts, or
    solver behavior.
- Confidence: high.
- Transferability: Applies to future `.silo-dos/standing_approval_profile.md`,
  `.silo-dos/self_evolution.md`, and template tasks when each is scoped separately.
- Update condition: Revise if `.silo-dos/` becomes formally referenced by
  `tasks/README.md` or the local skill is upgraded to v0.4.

### EXP-009: Broader Issues Belong In Reports, Not Scope Expansion

- Pattern id: `EXP-009`.
- Context: While executing a narrow task, Codex discovers a related issue, follow-up
  opportunity, missing design gate, or future task candidate outside the current allowed
  changes.
- Evidence source:
  - `tasks/README.md`
  - `AGENTS.md`
  - `tasks/reports/20260602-12-01_phase8-progress-audit_report.md`
  - `tasks/reports/20260604-05-01_phase9-implementation-readiness-audit_report.md`
  - `tasks/reports/20260604-08-01_phase9-policy-readiness-audit_report.md`
  - `tasks/reports/20260604-12-01_project-milestone-audit_report.md`
- Auto-action rule: Record the broader issue, next recommended atomic task, or decision
  packet in the report. Do not fix or execute the follow-up inside the current task.
- Stop conditions:
  - completing the current task requires the broader fix;
  - the broader fix crosses L2/L3 gates;
  - the current task would become multi-objective.
- Confidence: high.
- Transferability: Applies to all SILO-DOS tasks, especially audits, phase readiness
  checks, process improvements, and implementation tasks that discover adjacent defects.
- Update condition: Revise only if task-system rules change the one-step execution or
  scope-lock policy.

## Use In Future Runs

Before issuing or executing a task, Codex may use this map to recognize common SILO-DOS
patterns. The map can help classify risk and choose an auto-action rule, but it cannot
override:

- the current user instruction;
- the issued task contract;
- `tasks/README.md`;
- `AGENTS.md`;
- `ROADMAP.md`;
- `tasks/phases/`;
- `.silo-dos/project_profile.md`;
- `.silo-dos/technical_route.md`;
- `.silo-dos/decision_log.md`;
- `.silo-dos/remote_sync_proof.md`.

When in doubt, stop with the relevant Decision Packet, Failure Packet, or Scope Expansion
Packet.

## Non-Goals

This map does not:

- approve Phase 10 planning or implementation;
- approve Phase 9 closure;
- approve native implementation;
- authorize solver behavior changes;
- authorize CLI or JSON schema changes;
- authorize dependency, build, packaging, or solver dispatch changes;
- change task-directory rules;
- update the local `silo-development-operator` skill;
- automate more than one task per run;
- rewrite historical reports or task files.

## Maintenance Rule

Future experience patterns should be added through a separate atomic process task. Add a
pattern only when evidence is high confidence, source-linked, and useful for future task
classification or stop conditions. If a pattern is superseded, add a new entry or update
the existing entry through a scoped maintenance task; do not reinterpret history silently.
