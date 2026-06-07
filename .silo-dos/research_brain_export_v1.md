# SILO-DOS Research Brain Export Packet v1

## 1. Export Metadata

- Export id: `SILO-DOS-RB-EXPORT-V1`.
- Project: `SILO solver`.
- Date: 2026-06-07.
- Source repository context: `silo-solver`, local branch `main`, SILO-DOS v0.4 local
  mirror present under `.silo-dos/`.
- Export purpose: compress the current SILO solver milestone, SILO-DOS v0.4 operating
  system, phase decisions, reusable development patterns, phase playbooks, and recovery
  patterns into a structured long-term knowledge package for later Research Brain
  storage.
- Write readiness: review-needed before remote import. The content is structured for
  later writing, but the target Research Brain folder structure, document format, and
  import workflow remain unresolved.
- Local-only statement: this file is a local export packet. It does not itself write to
  Research Brain, Google Drive, external services, or any connector.

Primary source files:

- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/remote_sync_proof.md`
- `.silo-dos/experience_map.md`
- `.silo-dos/standing_approval_profile.md`
- `.silo-dos/self_evolution.md`
- `.silo-dos/local_skill_integration_design.md`
- `.silo-dos/research_brain_bridge.md`
- `tasks/reports/20260604-12-01_project-milestone-audit_report.md`
- `tasks/reports/20260604-11-01_phase9-post-defer-audit_report.md`
- `tasks/reports/20260606-01-01_silo-dos-v04-local-mirror-pilot_report.md`
- `tasks/reports/20260607-01-01_silo-dos-v04-local-skill-integration-design_report.md`
- `tasks/reports/20260607-02-01_silo-dev-operator-v04_report.md`
- `tasks/reports/20260607-03-01_v04-smoke-test_report.md`
- `tasks/reports/20260607-06-01_v04-hard-stop-smoke_report.md`
- `tasks/reports/20260607-07-01_research-brain-bridge_report.md`
- `tasks/README.md`
- `AGENTS.md`
- `ROADMAP.md`
- `tasks/phases/`

## 2. Executive Summary

SILO has reached a stable Python reference-solver milestone for the current
educational/conservative scope.

Phase 0 through Phase 8 are complete. Phase 9 is open but parked on
design/bookkeeping after the native implementation defer decision. Native implementation
is deferred and not approved. Phase 10 has not started.

The current solver milestone includes model core and canonicalization, tableau simplex,
revised simplex and basis handling, conservative presolve and diagnostics, minimal
branch-and-bound, conservative cut/callback boundaries, conservative decomposition
boundaries, conservative stochastic/robust transformation boundaries, and native backend
planning/passive boundary records.

SILO-DOS v0.4 is now represented locally through `.silo-dos/` mirror files and an
upgraded local `silo-development-operator v0.4` skill. The local mirror pilot, v0.4
smoke test, decision-chain smoke test, and hard-stop smoke test show that the local
mirror can act as the primary task-decision source and that unapproved L2/L3 work is
blocked.

The Research Brain Bridge has been designed. It defines:

```text
local .silo-dos mirror -> Research Brain query packet -> user decision
```

and:

```text
local reports / experience_map / decisions -> Research Brain export
Research Brain experience / phase playbooks -> local mirror preload
```

Actual Research Brain writing/import workflow remains future work. This export packet
is the first local package intended for later review and optional import.

## 3. Solver Capability Summary

### Completed Capability Layers

- Model core and canonicalization: user-facing model objects, expression building,
  validation, JSON loading, solution writing, and deterministic canonical conversion.
- Tableau simplex: educational small-LP solver with deterministic pivot behavior,
  Phase I/Phase II workflows, and infeasible/unbounded status handling.
- Revised simplex and basis layer: basis-oriented LP support, feasibility checks,
  reduced costs, warm-start smoke coverage, and comparison against tableau results.
- Presolve and numerical diagnostics: conservative reductions, fixed-variable recovery,
  repeated-pass behavior, original-space slack recovery, coefficient diagnostics,
  checked-in examples, and CLI regression coverage.
- Branch-and-bound: minimal deterministic MIP solver over LP relaxations for small
  binary and bounded integer fixtures, with node logs and opt-in CLI diagnostics.
- Cut/callback boundary: passive cut records, cut pool, no-op separator/callback
  boundaries, optional disabled-by-default integration points, and toy separator
  examples without default branch-and-bound behavior changes.
- Decomposition boundary: master/subproblem records, decomposition logs, passive
  Benders and column-generation structures, no-op and toy fixture drivers, and checked-in
  educational examples.
- Stochastic/robust transformation boundary: finite scenario records, stochastic and
  robust wrappers, uncertainty sets, deterministic naming, tiny deterministic-equivalent
  builder, interval RHS robust counterpart toy transformation, diagnostics, and examples.
- Native backend planning/passive boundary: native boundary design, selected first
  candidate `tableau_leaving_row_ratio_test`, passive backend records, parity fixtures,
  unavailable-native diagnostics, native policy notes, decision packet, defer decision,
  and post-defer audit.

### Deliberately Deferred Solver Work

- Advanced MIP features, heuristics, advanced branching, and production MIP behavior.
- Real cut families and cut materialization into LP relaxations.
- Lazy constraints and mutation callbacks.
- Production Benders decomposition.
- Production column generation.
- Branch-and-price.
- Broader decomposition integration with LP/MIP solve loops.
- Scenario-dependent variables and nonanticipativity constraints.
- Broader stochastic deterministic equivalents and robust counterparts.
- Public uncertainty CLI and JSON schemas.
- Native backend implementation.
- Native dependencies, build, packaging, platform support, and native CI behavior.
- Solver dispatch to native backend.
- Public native CLI or JSON schema controls.
- Phase 10 planning or implementation.

## 4. SILO-DOS v0.4 System Summary

Completed SILO-DOS v0.4 components:

- `.silo-dos/v04_architecture.md`: defines the Project Profile, Technical Route,
  Experience Map, and Self-Evolution concept for repository-local operating memory.
- `.silo-dos/project_profile.md`: records stable project identity, current milestone
  state, forbidden default changes, standard checks, task/report directories, and phase
  transition rules.
- `.silo-dos/technical_route.md`: records the current decision corridor:
  `phase9_parked_on_design_bookkeeping_after_native_defer`.
- `.silo-dos/decision_log.md`: records durable closures, native candidate selection,
  native defer, Phase 9 parked status, and Phase 10 not-started status.
- `.silo-dos/remote_sync_proof.md`: standardizes `git status`, branch, recent log,
  ahead/behind count, push result, and `remote_sync_status`.
- `.silo-dos/experience_map.md`: extracts high-confidence reusable SILO-DOS operating
  patterns.
- `.silo-dos/standing_approval_profile.md`: defines L0/L1 auto-execution corridors and
  L2/L3 hard stops.
- `.silo-dos/self_evolution.md`: defines controlled process-upgrade mechanics and where
  lessons should go.
- `.silo-dos/local_skill_integration_design.md`: designs how the local skill should read
  `.silo-dos/` first and apply the local mirror -> Research Brain -> user decision chain.
- Local `silo-development-operator v0.4`: upgraded outside the repository to use
  `.silo-dos/` as the primary repository-local decision mirror.
- v0.4 smoke test: verified local mirror read order, current project status, standing
  approval boundaries, and Remote Sync Proof.
- v0.4 hard-stop smoke test: verified native implementation, Phase 10 planning, and
  solver dispatch/backend selector behavior changes are blocked without explicit
  approval.
- Research Brain Bridge design: defines query, export, import/preload, degraded mode,
  and safety boundaries.

## 5. Reusable Development Patterns

### PAT-001: Passive Records Plus Validation Tests Are Usually Safe L1

- Pattern id: `PAT-001`.
- Context: Immutable/passive records, adapters, fixtures, diagnostics, or wrappers are
  added with validation tests while no solver calls, dispatch, CLI, schemas, dependencies,
  build files, native code, or default behavior changes occur.
- Evidence source: `.silo-dos/experience_map.md` `EXP-001`; Phase 7, Phase 8, and Phase
  9 passive-record reports.
- Reusable rule: Mode A may execute only when the task is explicitly scoped, backed by
  design evidence or prior audit, has clear acceptance criteria, and stays passive.
- Stop conditions: solver calls, default behavior changes, dispatch changes, CLI/schema
  changes, native dependencies/build/native code, or missing acceptance criteria.
- Confidence: high.
- Transferability: high for future passive metadata, diagnostic, fixture, and no-op
  boundary tasks.
- Recommended Research Brain category: `Risk Patterns / L1 Passive Boundaries`.

### PAT-002: Phase Closure Is Always L3 And Separate From Next Phase Start

- Pattern id: `PAT-002`.
- Context: A task marks a phase complete, changes roadmap or phase-record status, or
  records closure bookkeeping.
- Evidence source: Phase 5, Phase 6, Phase 7, and Phase 8 closure reports; decision log;
  technical route.
- Reusable rule: closure requires explicit user approval for the exact closure task and
  must not start the next phase.
- Stop conditions: missing approval, unresolved closure audit blockers, solver/test/CLI
  changes, or task also starts the next phase.
- Confidence: high.
- Transferability: high for every future phase.
- Recommended Research Brain category: `Phase Playbooks / Closure`.

### PAT-003: Native Implementation Is Always L3

- Pattern id: `PAT-003`.
- Context: A task would implement native code, choose a native implementation form, add
  native dependencies, change build/packaging, change native dispatch, or approve a
  native implementation path.
- Evidence source: Phase 9 readiness, kernel-selection, build-policy, decision-packet,
  defer-bookkeeping, hard-stop smoke, and experience-map reports.
- Reusable rule: Mode A must stop before native implementation or native build/dispatch
  movement unless the user explicitly approves the exact L3 task.
- Stop conditions: any native code, extension module, binary/generated artifact,
  dependency/build/packaging/CI, solver dispatch, CLI, or JSON schema change.
- Confidence: high.
- Transferability: high for all future native/backend acceleration projects.
- Recommended Research Brain category: `Risk Patterns / Native Implementation`.

### PAT-004: Push Failure Requires Sync-Only Recovery And Remote Sync Proof

- Pattern id: `PAT-004`.
- Context: `git push` fails after a local commit due to network reset, SSL read failure,
  or inability to reach GitHub.
- Evidence source: `.silo-dos/remote_sync_proof.md`; repeated push-failure reports;
  v0.4 smoke reports.
- Reusable rule: preserve the local commit, record the failure, do not retry repeatedly
  inside the same task, and require sync-only recovery or clean `origin/main...HEAD =
  0 0` before new work.
- Stop conditions: dirty worktree, behind/diverged branch, local ahead without user
  recovery approval, or repeated push retries inside one task.
- Confidence: high.
- Transferability: high for every Git-backed Codex project.
- Recommended Research Brain category: `Failure Recovery Patterns / Git Sync`.

### PAT-005: Design-Only Planning Does Not Approve Implementation

- Pattern id: `PAT-005`.
- Context: A task creates design notes, planning notes, decision packets, architecture
  notes, technical routes, or Research Brain bridge/export packets.
- Evidence source: Phase 8 design, Phase 9 design, native policy/decision reports,
  SILO-DOS v0.4 architecture, Research Brain bridge.
- Reusable rule: planning may define candidate tasks and gates, but implementation needs
  a later explicit task and approval when L2/L3 work is involved.
- Stop conditions: implementation files, tests, examples, CLI/schema changes,
  dependencies/build changes, or treating a candidate follow-up as permission.
- Confidence: high.
- Transferability: high for phase planning, process tooling, and architecture design.
- Recommended Research Brain category: `Decision Memory / Planning Boundaries`.

### PAT-006: Examples-Only Tasks Can Be L0 If Behavior Is Unchanged

- Pattern id: `PAT-006`.
- Context: Checked-in deterministic examples exercise existing behavior without changing
  solver source, tests, CLI, schemas, roadmap, phase files, or generated outputs.
- Evidence source: `.silo-dos/experience_map.md` `EXP-006`; decomposition and
  uncertainty example reports.
- Reusable rule: examples-only tasks may be L0 when they call existing stable APIs and
  avoid behavior or public-contract changes.
- Stop conditions: source/test changes needed, new CLI/schema support needed, generated
  outputs added, or examples imply phase closure/next-phase start.
- Confidence: high.
- Transferability: medium-high for educational solver repositories.
- Recommended Research Brain category: `Risk Patterns / L0 Examples`.

### PAT-007: Local Mirror Is Execution Authority; Research Brain Is Long-Term Memory

- Pattern id: `PAT-007`.
- Context: Codex must execute from repository-visible rules, while Research Brain stores
  long-term strategy and cross-project experience.
- Evidence source: `.silo-dos/v04_architecture.md`, `research_brain_bridge.md`,
  `local_skill_integration_design.md`, project profile, technical route, experience map.
- Reusable rule: use local mirror first; use Research Brain for strategic suggestions
  only when local mirror is insufficient; ask the user when conflict or L2/L3 movement
  appears.
- Stop conditions: Research Brain conflicts with local mirror, Research Brain proposes
  L2/L3 movement without user approval, or a local mirror file appears stale.
- Confidence: high.
- Transferability: high across future Codex/ChatGPT/GitHub workflows.
- Recommended Research Brain category: `Solver Development OS / Memory Architecture`.

### PAT-008: Standing Approval Applies Only Inside Technical Route And Clean Sync Proof

- Pattern id: `PAT-008`.
- Context: Mode A sees an apparently eligible L0 or L1 task.
- Evidence source: standing approval profile, technical route, remote sync proof, v0.4
  smoke tests.
- Reusable rule: standing approval is valid only when the task is inside the current
  corridor, Remote Sync Proof is clean, task ID scan is complete, and no hard-stop
  category is triggered.
- Stop conditions: dirty worktree, `origin/main...HEAD` not `0 0`, solver behavior,
  dispatch, CLI/schema, dependency/build/native, phase transition, or future-phase work.
- Confidence: high.
- Transferability: high for all SILO-DOS style workflows.
- Recommended Research Brain category: `Risk Patterns / Standing Approval`.

### PAT-009: Broader Issues Belong In Reports Or Improvement Candidates

- Pattern id: `PAT-009`.
- Context: A narrow task discovers adjacent issues, follow-up candidates, missing
  evidence, or possible process friction.
- Evidence source: `tasks/README.md`, `AGENTS.md`, experience map, self-evolution file,
  readiness and milestone audits.
- Reusable rule: record broader issues in the report or self-evolution candidate, but do
  not silently expand the current task.
- Stop conditions: current task cannot be completed without the broader fix, broader fix
  crosses L2/L3, or task becomes multi-objective.
- Confidence: high.
- Transferability: high for all one-task-at-a-time systems.
- Recommended Research Brain category: `Solver Development OS / Scope Control`.

## 6. Decision Memory Export

### DEC-20260524-P5-CLOSURE

- Decision summary: Phase 5 minimal branch-and-bound scope closed after user-approved
  closure bookkeeping.
- Source report/note: `tasks/reports/20260524-02-01_phase5-closure-bookkeeping_report.md`.
- Approved scope: mark Phase 5 complete for the current minimal branch-and-bound scope.
- Forbidden scope: solver/test/example/CLI/schema changes; issuing or starting Phase 6.
- Current status: `closed`.
- Reopening condition: explicit user approval for new Phase 5 or advanced MIP work.
- Store as long-term Research Brain memory: yes.

### DEC-20260524-P6-CLOSURE

- Decision summary: Phase 6 conservative cut/callback boundary closed.
- Source report/note: `tasks/reports/20260524-13-01_phase6-closure-bookkeeping_report.md`.
- Approved scope: mark Phase 6 complete for conservative cut/callback boundary scope.
- Forbidden scope: solver/test/example/CLI/schema changes; issuing or starting Phase 7.
- Current status: `closed`.
- Reopening condition: explicit user approval for real cuts, callbacks,
  branch-and-cut, lazy constraints, or cut materialization.
- Store as long-term Research Brain memory: yes.

### DEC-20260602-P7-CLOSURE

- Decision summary: Phase 7 conservative decomposition boundary closed.
- Source report/note: `tasks/reports/20260602-04-01_phase7-closure-bookkeeping_report.md`.
- Approved scope: mark Phase 7 complete for conservative decomposition boundary scope.
- Forbidden scope: solver/test/example/CLI/schema changes; issuing or starting Phase 8.
- Current status: `closed`.
- Reopening condition: explicit approval for production Benders, production column
  generation, branch-and-price, or solve-loop integration.
- Store as long-term Research Brain memory: yes.

### DEC-20260603-P8-CLOSURE

- Decision summary: Phase 8 conservative stochastic/robust transformation boundary
  closed.
- Source report/note: `tasks/reports/20260603-04-01_phase8-closure-bookkeeping_report.md`.
- Approved scope: mark Phase 8 complete for conservative stochastic/robust
  transformation boundary scope.
- Forbidden scope: solver/test/example/CLI/schema changes; issuing Phase 9 planning or
  implementation.
- Current status: `closed`.
- Reopening condition: explicit approval for broader uncertainty transformations,
  nonanticipativity, public uncertainty CLI/schema, or production uncertainty behavior.
- Store as long-term Research Brain memory: yes.

### DEC-20260604-P9-NATIVE-CANDIDATE

- Decision summary: select `tableau_leaving_row_ratio_test` as the first native kernel
  candidate for later review.
- Source report/note: `notes/22_native_kernel_candidate_selection.md` and
  `tasks/reports/20260604-03-01_native-kernel-selection_report.md`.
- Approved scope: candidate selection only.
- Forbidden scope: native implementation, dispatch, dependencies, build/packaging,
  CLI/schema changes, Phase 9 closure, or Phase 10 start.
- Current status: `active`.
- Reopening condition: explicit user request for design-only candidate revision or
  rejection.
- Store as long-term Research Brain memory: yes.

### DEC-20260604-P9-NATIVE-DEFER

- Decision summary: native implementation deferred for now; selected candidate remains
  Python-reference only.
- Source report/note: `notes/25_native_implementation_defer_decision.md` and
  `tasks/reports/20260604-10-01_native-defer-bookkeeping_report.md`.
- Approved scope: record defer decision and keep Phase 9 open.
- Forbidden scope: native implementation, dependencies, build/packaging, dispatch,
  CLI/schema changes, Phase 9 closure, or Phase 10 start.
- Current status: `deferred`.
- Reopening condition: explicit L3 approval for a specific native implementation task
  with exact scope and no-dispatch boundary unless dispatch is separately approved.
- Store as long-term Research Brain memory: yes.

### DEC-20260604-P9-PARKED

- Decision summary: Phase 9 remains open and parked on design/bookkeeping after native
  defer.
- Source report/note: `tasks/reports/20260604-11-01_phase9-post-defer-audit_report.md`
  and `.silo-dos/technical_route.md`.
- Approved scope: remain parked on design, audit, policy, readiness, or bookkeeping.
- Forbidden scope: native implementation, Phase 9 closure, Phase 10 start, or solver
  behavior changes without separate approval.
- Current status: `parked`.
- Reopening condition: explicit user request to revise/reject candidate, approve native
  implementation path, prepare Phase 9 closure, or start Phase 10 planning.
- Store as long-term Research Brain memory: yes.

### DEC-20260604-P10-NOT-STARTED

- Decision summary: Phase 10 has not started.
- Source report/note: `tasks/reports/20260604-12-01_project-milestone-audit_report.md`,
  `.silo-dos/project_profile.md`, and `.silo-dos/technical_route.md`.
- Approved scope: record Phase 10 not-started state.
- Forbidden scope: Phase 10 planning/implementation, roadmap or phase-file work for
  Phase 10, or inferred approval from Phase 9 parked status.
- Current status: `not_started`.
- Reopening condition: explicit user approval for Phase 10 planning; planning approval
  does not approve implementation.
- Store as long-term Research Brain memory: yes.

## 7. Phase Playbook Export

### General Phase Opening Playbook

1. Confirm current route and Remote Sync Proof.
2. Require explicit user approval for phase start or planning when L3.
3. Create a design/planning note before implementation.
4. Define dependency direction, scope, non-goals, public-contract boundaries, and
   candidate atomic task sequence.
5. Start with passive records or boundary scaffolding when possible.
6. Stop after one atomic task; recommendations are not execution permission.

### Phase Technical Route Playbook

- Record current phase corridor, allowed actions, forbidden actions, decision gates,
  closure conditions, and next-phase conditions.
- Treat the route as a corridor, not a backlog.
- Update only through scoped tasks when route facts change.

### Progression Playbook: Records -> Diagnostics -> Toy Examples -> Audit -> Closure

- Start with immutable/passive records and validation tests.
- Add diagnostic/result records before behavior-changing integrations.
- Add toy fixture-only examples or drivers before production algorithms.
- Run closure-readiness or progress audits before closure.
- Close only after explicit user approval and never start the next phase inside closure.

### L2/L3 Gate Playbook

- Use Decision Packets for solver behavior, dispatch, CLI/schema, native, dependency,
  build, phase, and architecture decisions.
- Approval must name the exact task, allowed files, behavior change, tests, and
  unchanged behavior.
- Planning and candidate selection do not approve implementation.

### Phase Closure Playbook

- Run or read closure-readiness audit.
- Confirm audit recommendation and blockers.
- Require explicit closure approval.
- Limit closure bookkeeping to roadmap/phase/report/task files when scoped.
- Do not issue next-phase work.

### Phase Parking Playbook

- Record the parked reason, current allowed actions, forbidden defaults, and reopening
  conditions.
- Keep parked phases open without implying immediate implementation.
- Do not infer closure or next phase from parking.

### Deferred Implementation Playbook

- Record defer decision in a durable note/report.
- Keep future approval template separate from actual approval.
- Preserve exact reopening condition.
- Ensure follow-up audits do not silently revive implementation.

### Native Backend Phase Playbook

- Native implementation is L3.
- Candidate selection can be design-only, but implementation requires exact approval.
- Build/dependency/generated-artifact policy must precede implementation.
- Default solver dispatch remains Python-only unless a separate dispatch task is
  approved.
- Parity tests and unavailable-native diagnostics should be passive before any native
  kernel exists.

### Uncertainty Transformation Phase Playbook

- Start with scenario and uncertainty records.
- Add wrappers and naming conventions before builders.
- Add tiny deterministic-equivalent or robust counterpart builders only for documented
  fixtures.
- Keep solver integration, CLI/schema exposure, nonanticipativity, and production
  uncertainty behavior deferred until separately approved.

### Decomposition Phase Playbook

- Start with master/subproblem contexts and result records.
- Add iteration logs and passive candidate records before drivers.
- Use no-op and toy fixture drivers before any general solve loop.
- Do not call LP/MIP solvers or implement production Benders/column generation until a
  later explicit task.

### Process-Tooling Phase Playbook

- Treat local skill changes and architecture redesign as L3.
- Build `.silo-dos/` local mirror files one at a time.
- Use smoke tests to prove local mirror usage and hard-stop behavior.
- Keep Research Brain bridge/export/import separate from actual external writes.

## 8. Risk And Gate Patterns

### L0 Safe Work

- Examples: docs, reports, audits, non-phase-state bookkeeping, narrow process mirror
  files, sync-only checks, examples-only tasks with no behavior change.
- Automatic action policy: Mode A may auto-execute when scope is explicit, Remote Sync
  Proof is clean, and no hard-stop condition applies.
- Required approval policy: current user request or task contract must scope the work;
  explicit L2/L3 approval not needed if truly L0.
- Evidence before proceeding: task ID scan, allowed/forbidden files, matching report,
  clean sync proof, lightweight checks.

### L1 Controlled Passive Work

- Examples: passive records, validation tests, diagnostics records, fixture records,
  no-op boundaries, import/package smoke tests.
- Automatic action policy: Mode A may execute only when backed by design evidence,
  acceptance criteria are explicit, and standing approval applies.
- Required approval policy: explicit approval or clear standing approval within route.
- Evidence before proceeding: design note or prior audit, deterministic tests, explicit
  unchanged behavior.

### L2 High-Risk Behavior Work

- Examples: solver behavior, LP/MIP/presolve behavior, solver dispatch, backend selector
  behavior, public CLI, JSON schemas, public API behavior, numerical conventions.
- Automatic action policy: Mode A stops.
- Required approval policy: exact user approval for the specific task.
- Evidence before proceeding: Decision Packet, allowed files, regression proof, behavior
  that must remain unchanged.

### L3 Strategic Work

- Examples: phase start, phase closure, architecture redesign, native implementation,
  native build/dependency strategy, local skill behavior changes, task-system rule
  changes, new solver capability lines.
- Automatic action policy: Mode A stops unless the current user explicitly approves the
  exact task.
- Required approval policy: explicit L3 approval; planning approval does not approve
  implementation.
- Evidence before proceeding: source-linked route facts, approval sentence, scope lock,
  non-goals, report path, Remote Sync Proof.

## 9. Failure And Recovery Patterns

### FAIL-001: GitHub Push Failure / Port 443 Reset

- Symptom: `git push` fails with connection reset, SSL read failure, or cannot connect
  to GitHub port 443.
- Classification: sync failure, not task failure.
- Recovery action: preserve local commit, record failure, avoid repeated retries, use
  sync-only recovery or clean `origin/main...HEAD = 0 0` proof before new work.
- When to stop: after one failed push attempt and report amendment if scoped.
- What to write to report: push error, commit hash, status, branch, log, ahead/behind,
  `remote_sync_status: push_failed`.
- Research Brain should remember: yes.

### FAIL-002: Local Commit Preserved But Not Pushed

- Symptom: worktree clean, local branch ahead of `origin/main`.
- Classification: `local_ahead_origin` unless current task recorded a failed push, then
  `push_failed`.
- Recovery action: run sync-only proof and push if requested.
- When to stop: before starting another development task.
- What to write to report: local commit hash and ahead/behind state.
- Research Brain should remember: yes.

### FAIL-003: Dirty Worktree

- Symptom: `git status --short` shows unrelated modified or untracked files.
- Classification: `dirty_worktree`.
- Recovery action: stop unless the dirty files are exact active task artifacts for an
  approved recovery/continuation.
- When to stop: before issuing a new task.
- What to write to report: dirty paths and recommended recovery.
- Research Brain should remember: yes.

### FAIL-004: Duplicate Task Already Issued Or Executed

- Symptom: intended `YYYYMMDD-TT-RR` prefix already exists in task or report directory.
- Classification: task-system collision risk.
- Recovery action: use next available `TT` for a new unrelated task; do not rename
  immutable historical task files.
- When to stop: if exact identity is ambiguous.
- What to write to report: scan result and selected prefix.
- Research Brain should remember: yes.

### FAIL-005: Codex Stream Disconnection

- Symptom: execution appears interrupted and final response is missing.
- Classification: recovery audit needed.
- Recovery action: inspect `git status`, branch, recent log, and diffs; classify whether
  task completed, partially modified files, local commit exists, or did not start.
- When to stop: after recovery classification unless user approves continuation.
- What to write to report: active task, dirty files, commit/push status, recommended
  action.
- Research Brain should remember: yes.

### FAIL-006: ChatGPT Remote Connector Cannot Verify Latest Commit

- Symptom: local Git proof is clean but a remote connector is unavailable or confusing.
- Classification: connector uncertainty.
- Recovery action: rely on local Git proof when clean; connector verification is helpful
  but not required.
- When to stop: only if local proof is incomplete or task explicitly requires connector
  confirmation.
- What to write to report: local proof and connector status if relevant.
- Research Brain should remember: yes.

### FAIL-007: Stale Local Route Evidence

- Symptom: user request, local mirror, roadmap, phase files, or reports disagree about
  route status.
- Classification: decision conflict.
- Recovery action: stop with Decision Packet; update local mirror only through scoped
  task after source evidence is resolved.
- When to stop: before L2/L3 movement or phase/native decisions.
- What to write to report: conflicting sources and decision needed.
- Research Brain should remember: yes.

### FAIL-008: Missing Decision Evidence

- Symptom: no report/note proves approval, defer, closure, phase start, native
  candidate, or route change.
- Classification: missing evidence.
- Recovery action: stop or create decision-audit task if scoped; do not infer approval.
- When to stop: whenever missing evidence affects L2/L3 behavior.
- What to write to report: missing source and safest next action.
- Research Brain should remember: yes.

## 10. Research Brain Bridge Rules

- Local `.silo-dos/` mirror is the primary repository execution source.
- Research Brain is long-term memory and a cross-project experience center.
- Codex first uses the local mirror, task contracts, reports, and repository rules.
- If the local mirror is insufficient, Codex generates a Research Brain Query Packet.
- If Research Brain is unavailable, stale, conflicting, or inconclusive, Codex asks the
  user.
- After important decisions, milestones, failures, or reusable patterns, SILO-DOS may
  prepare a Research Brain Export Packet.
- Research Brain advice must not override current user instruction, issued task
  contracts, local technical route, decision log, standing approval profile, Remote Sync
  Proof, L2/L3 hard stops, or one-task-at-a-time execution.
- Research Brain cannot silently approve phase start, phase closure, native
  implementation, dependency/build changes, solver dispatch, public CLI, JSON schema,
  solver behavior, local skill edits, or task-system rule changes.
- If Research Brain and local mirror disagree, the user decides. Durable results should
  later be mirrored locally through a scoped task.

## 11. Suggested Research Brain Target Structure

Suggested generic targets:

- `Research Brain / Solver Development OS / SILO-DOS / Experience Maps / SILO Export v1`
- `Research Brain / Solver Development OS / Phase Playbooks / Native Backend`
- `Research Brain / Solver Development OS / Phase Playbooks / Decomposition`
- `Research Brain / Solver Development OS / Phase Playbooks / Stochastic Robust`
- `Research Brain / Solver Development OS / Phase Playbooks / Process Tooling`
- `Research Brain / Solver Development OS / Risk Patterns`
- `Research Brain / Solver Development OS / Failure Recovery Patterns`
- `Research Brain / Solver Development OS / Decision Memory`
- `Research Brain / Solver Development OS / Remote Sync Proof`
- `Research Brain / Solver Development OS / Standing Approval Profiles`

These paths are proposals only. This file does not create, write, or update those
locations.

## 12. Import / Preload Guidance

Use this export later:

- Before starting a new solver project: preload project identity, phase playbooks,
  risk gates, one-task execution, and Remote Sync Proof conventions.
- Before starting a new phase: preload phase-opening playbook, L2/L3 gates, candidate
  task sequence patterns, and non-goals.
- Before approving implementation: preload relevant risk patterns and exact approval
  requirements, especially for native, dispatch, CLI/schema, and algorithmic behavior.
- Before migrating SILO-DOS to another repository: preload `.silo-dos` structure, local
  skill integration, standing approval, and self-evolution rules.
- Before revising standing approval: preload experience patterns, hard-stop smoke
  results, failure history, and route constraints.

Recommended future preload workflow:

1. Read this export packet.
2. Query Research Brain for comparable project and phase lessons.
3. Produce a local preload summary.
4. Compare preload against current repository route.
5. Ask user for any L2/L3 or strategic decision.
6. Update `.silo-dos/` only through a scoped task.

## 13. Open Questions

- What exact Google Drive or Research Brain folder structure should hold these exports?
- Should Research Brain entries be Google Docs, Markdown files, or both?
- Should exports be manual, connector-assisted, or both depending on task risk?
- How often should exports be generated: after milestones, after phase closure, after
  process upgrades, or on a fixed cadence?
- How should stale Research Brain advice be detected and invalidated?
- How should Research Brain experience maps be versioned?
- Should future exports include checksums or commit hashes for source reports?
- Should Research Brain imports produce a local preload file before task issuance?

## 14. Recommended Next Action

This task does not write to Research Brain.

No immediate solver task is required.

The next possible task is a review-only task to decide whether and how to write this
export into Research Brain. Another possible task is a Research Brain Import / Preload
Protocol design task.

Do not issue or execute either automatically.
