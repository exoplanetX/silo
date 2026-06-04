# SILO Decision Log

## Role Of This Log

This file is the repository-local SILO-DOS v0.4 decision log. It records durable
decisions that should survive chat compaction and repeated task handoffs.

This log is an index and local mirror. It does not replace the source reports, notes,
`ROADMAP.md`, `tasks/phases/`, or issued task contracts. If this file conflicts with a
source report or a current user instruction, Codex must stop and resolve the conflict
through the normal SILO-DOS review gate.

## Sources

Primary local mirror sources:

- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`

Source reports and notes used for the initial entries:

- `tasks/reports/20260524-02-01_phase5-closure-bookkeeping_report.md`
- `tasks/reports/20260524-13-01_phase6-closure-bookkeeping_report.md`
- `tasks/reports/20260602-04-01_phase7-closure-bookkeeping_report.md`
- `tasks/reports/20260603-04-01_phase8-closure-bookkeeping_report.md`
- `notes/22_native_kernel_candidate_selection.md`
- `tasks/reports/20260604-03-01_native-kernel-selection_report.md`
- `notes/25_native_implementation_defer_decision.md`
- `tasks/reports/20260604-10-01_native-defer-bookkeeping_report.md`
- `tasks/reports/20260604-11-01_phase9-post-defer-audit_report.md`
- `tasks/reports/20260604-12-01_project-milestone-audit_report.md`

## Decision Status Legend

- `active`: decision currently governs the project.
- `closed`: phase scope is closed for the recorded milestone.
- `parked`: phase remains open but no immediate task is required.
- `deferred`: implementation or capability line is explicitly not approved for now.
- `not_started`: phase or capability has not begun.

## Decisions

### DEC-20260524-P5-CLOSURE

- Date: 2026-05-24.
- Context: Phase 5 minimal branch-and-bound scope reached closure review and the user
  approved closure bookkeeping.
- Source report/note:
  `tasks/reports/20260524-02-01_phase5-closure-bookkeeping_report.md`.
- Approved scope: mark Phase 5 complete for the current minimal branch-and-bound scope
  by updating `ROADMAP.md`, the Phase 5 phase record, and the matching task/report files.
- Forbidden scope: do not modify solver source code, tests, examples, CLI behavior, JSON
  schemas, or notes; do not issue or start Phase 6.
- Current status: `closed`.
- Reopening condition: reopen Phase 5 only if the user explicitly approves new Phase 5
  work or an advanced MIP task that deliberately revisits branch-and-bound scope.

### DEC-20260524-P6-CLOSURE

- Date: 2026-05-24.
- Context: Phase 6 conservative cut/callback boundary scope reached closure review and
  the user approved closure bookkeeping.
- Source report/note:
  `tasks/reports/20260524-13-01_phase6-closure-bookkeeping_report.md`.
- Approved scope: mark Phase 6 complete for the current conservative cut/callback
  boundary scope by updating `ROADMAP.md`, the Phase 6 phase record, and the matching
  task/report files.
- Forbidden scope: do not modify solver source code, tests, examples, CLI behavior, JSON
  schemas, or notes; do not issue or start Phase 7.
- Current status: `closed`.
- Reopening condition: reopen Phase 6 only if the user explicitly approves new cut,
  callback, branch-and-cut, lazy-constraint, or cut-materialization work.

### DEC-20260602-P7-CLOSURE

- Date: 2026-06-02.
- Context: Phase 7 conservative decomposition boundary scope reached closure review and
  the user approved closure bookkeeping.
- Source report/note:
  `tasks/reports/20260602-04-01_phase7-closure-bookkeeping_report.md`.
- Approved scope: mark Phase 7 complete for the current conservative decomposition
  boundary scope by updating `ROADMAP.md`, the Phase 7 phase record, and the matching
  task/report files.
- Forbidden scope: do not modify solver source code, tests, examples, public CLI
  behavior, or JSON schemas; do not issue or start Phase 8.
- Current status: `closed`.
- Reopening condition: reopen Phase 7 only if the user explicitly approves production
  Benders, production column generation, branch-and-price, decomposition solve-loop
  integration, or related decomposition expansion.

### DEC-20260603-P8-CLOSURE

- Date: 2026-06-03.
- Context: Phase 8 conservative stochastic/robust transformation boundary scope reached
  closure review and the user approved closure bookkeeping.
- Source report/note:
  `tasks/reports/20260603-04-01_phase8-closure-bookkeeping_report.md`.
- Approved scope: mark Phase 8 complete for the current conservative stochastic/robust
  transformation boundary scope by updating `ROADMAP.md`, the Phase 8 phase record, and
  the matching task/report files.
- Forbidden scope: do not modify solver source code, tests, examples, public CLI
  behavior, or JSON schemas; do not issue Phase 9 planning or implementation.
- Current status: `closed`.
- Reopening condition: reopen Phase 8 only if the user explicitly approves broader
  uncertainty transformations, scenario-dependent variables, nonanticipativity, public
  uncertainty CLI/schema work, or production stochastic/robust optimization behavior.

### DEC-20260604-P9-NATIVE-CANDIDATE

- Date: 2026-06-04.
- Context: The user approved a design-only L3 native kernel candidate selection task for
  Phase 9.
- Source report/note:
  `notes/22_native_kernel_candidate_selection.md` and
  `tasks/reports/20260604-03-01_native-kernel-selection_report.md`.
- Approved scope: select exactly one first native-kernel candidate for later review:
  `tableau_leaving_row_ratio_test`, corresponding to Python reference behavior in
  `silo.lp.simplex.ratio_test.choose_leaving_row`.
- Forbidden scope: do not implement native code, approve implementation, change solver
  dispatch, add dependencies, modify build or packaging files, change public CLI or JSON
  schemas, close Phase 9, or start Phase 10.
- Current status: `active`.
- Reopening condition: revise or reject the selected candidate only if the user
  explicitly requests a new design-only candidate review task.

### DEC-20260604-P9-NATIVE-DEFER

- Date: 2026-06-04.
- Context: After the native implementation decision packet recommended deferral, the
  user explicitly chose to defer native implementation for now.
- Source report/note:
  `notes/25_native_implementation_defer_decision.md` and
  `tasks/reports/20260604-10-01_native-defer-bookkeeping_report.md`.
- Approved scope: record that native implementation is deferred and unapproved, while
  keeping Phase 9 open.
- Forbidden scope: do not implement native backend code, add native dependencies, modify
  build or packaging files, change solver dispatch or backend selection, change public
  CLI behavior, change JSON schemas, close Phase 9, or start Phase 10.
- Current status: `deferred`.
- Reopening condition: reopen the native implementation path only if the user explicitly
  approves a specific L3 native implementation task with exact scope, files, build and
  dependency policy, generated-artifact policy, tests, and no-dispatch boundary.

### DEC-20260604-P9-PARKED

- Date: 2026-06-04.
- Context: After the native defer decision, a post-defer audit classified Phase 9 as
  parked on design/bookkeeping.
- Source report/note:
  `tasks/reports/20260604-11-01_phase9-post-defer-audit_report.md` and
  `.silo-dos/technical_route.md`.
- Approved scope: keep Phase 9 open and parked on design, audit, policy, readiness, or
  bookkeeping work.
- Forbidden scope: do not issue native implementation, close Phase 9, start Phase 10, or
  change solver behavior without separate explicit approval.
- Current status: `parked`.
- Reopening condition: move Phase 9 out of parked state only if the user explicitly
  requests one of the corridor actions: revise/reject native candidate, approve a
  specific native implementation path, prepare Phase 9 closure, or start Phase 10
  planning.

### DEC-20260604-P10-NOT-STARTED

- Date: 2026-06-04.
- Context: The project milestone audit and technical route confirm that Phase 10 has not
  started.
- Source report/note:
  `tasks/reports/20260604-12-01_project-milestone-audit_report.md`,
  `.silo-dos/project_profile.md`, and `.silo-dos/technical_route.md`.
- Approved scope: record Phase 10 as not started.
- Forbidden scope: do not issue Phase 10 planning or implementation tasks, modify
  roadmap or phase files for Phase 10, or infer Phase 10 approval from Phase 9 parked
  status.
- Current status: `not_started`.
- Reopening condition: start Phase 10 planning only if the user explicitly approves
  Phase 10 planning. Planning approval does not approve Phase 10 implementation.

## Current Decision Corridor

The current decision corridor is:

```text
phase9_parked_on_design_bookkeeping_after_native_defer
```

Allowed only with explicit user request or approval:

- remain parked with no task;
- create more SILO-DOS v0.4 process mirror files;
- revise or reject the selected native candidate;
- approve a specific native implementation path;
- prepare Phase 9 closure;
- start Phase 10 planning.

Forbidden by default:

- native implementation;
- native dependencies, build, packaging, or generated-artifact work;
- solver dispatch to native backend;
- public CLI or JSON schema changes;
- Phase 9 closure;
- Phase 10 planning or implementation.

## Maintenance Rule

Future durable decisions should be added to this log through a separate atomic task.

Do not edit historical decision entries to reinterpret them unless the user explicitly
requests a decision-log maintenance task. If a decision is superseded, add a new entry
that references the earlier decision and states the superseding condition.
