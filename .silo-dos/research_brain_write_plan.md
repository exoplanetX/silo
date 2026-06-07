# SILO-DOS Research Brain Write Plan

## Role Of This Plan

This file reviews `.silo-dos/research_brain_export_v1.md` and defines a safe plan for
how that export should later be written into the remote Research Brain.

This is a local write plan only. It does not write to Research Brain, Google Drive,
external services, or any connector. It does not approve connector use. It does not
modify the local `silo-development-operator` skill, solver source code, tests, examples,
roadmap, phase files, CLI behavior, JSON schemas, native backend code, build files,
packaging files, solver dispatch, or backend selection.

The governing rule remains:

```text
local .silo-dos mirror -> Research Brain query packet -> user decision
```

Repository-local `.silo-dos/` remains the execution source of truth. Research Brain is a
long-term memory and experience center.

## Sources

Primary sources:

- `.silo-dos/research_brain_export_v1.md`
- `.silo-dos/research_brain_bridge.md`
- `.silo-dos/experience_map.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/self_evolution.md`
- `tasks/reports/20260607-08-01_research-brain-export-v1_report.md`

Supporting stable rules:

- `tasks/README.md`
- `AGENTS.md`

## 1. Write-Readiness Assessment

### Overall Assessment

`.silo-dos/research_brain_export_v1.md` is ready for user review. It is not yet approved
for direct external writing.

The export is well structured for later Research Brain import because it:

- identifies itself as `SILO-DOS-RB-EXPORT-V1`;
- states that it is local-only and review-needed;
- summarizes the current SILO solver milestone;
- records Phase 0 through Phase 8 completion and parked Phase 9 state;
- records native implementation defer status and Phase 10 not-started status;
- exports reusable patterns, decision memory, phase playbooks, risk gates, and failure
  recovery patterns;
- defines Research Brain bridge rules and safety boundaries;
- proposes generic target structures and import/preload guidance.

### Stable Long-Term Knowledge

These parts are stable enough for Research Brain after user review:

- SILO-DOS v0.4 architecture and local mirror model.
- Local mirror vs Research Brain division of responsibility.
- Decision chain: local mirror -> Research Brain query packet -> user decision.
- Risk gate taxonomy: L0, L1, L2, L3.
- Remote Sync Proof and push-failure recovery patterns.
- High-confidence experience-map patterns.
- Phase closure, phase parking, and deferred implementation playbooks.
- Native implementation as an L3 hard stop.
- Design-only planning not implying implementation approval.

### Project-Specific Knowledge To Keep Repo-Local First

These parts should remain primarily repo-local and be exported only as context:

- exact SILO phase status;
- exact task/report ids;
- exact selected native candidate, `tableau_leaving_row_ratio_test`;
- current Phase 9 parked route;
- current Phase 10 not-started state;
- specific `.silo-dos/` file names and repository paths;
- exact local Git sync history and push failure details.

Research Brain may store these as project profile or decision memory, but they should
not become generic rules for every project.

### Items Requiring User Review Before Export

User review is needed for:

- final Research Brain folder/document structure;
- whether Google Docs, Markdown, or both should be used;
- whether import should be manual or connector-assisted;
- how much project-specific task/report detail should be copied;
- whether Research Brain should store exact paths or more abstract references;
- versioning cadence for future exports;
- whether any material should be excluded as too local, too noisy, or not reusable.

### Write-Readiness Conclusion

The export is ready for user review and planning. Direct external writing should not
happen automatically.

## 2. Proposed Research Brain Target Structure

Use a generic structure that separates overview, reusable operating rules, project
decision memory, and phase-specific playbooks:

```text
Research Brain /
  Solver Development OS /
    SILO-DOS /
      Overview
      Experience Maps
      Decision Memory
      Remote Sync Proof
      Standing Approval Profiles
      Research Brain Bridge
      Import Preload Protocols
    Phase Playbooks /
      Native Backend
      Decomposition
      Stochastic Robust
      Process Tooling
      Phase Closure
      Phase Parking
    Risk Patterns /
      L0 Safe Work
      L1 Passive Boundaries
      L2 Behavior Changes
      L3 Strategic Gates
    Failure Recovery Patterns /
      Git Sync
      Dirty Worktree
      Duplicate Task Identity
      Stream Disconnection
      Stale Route Evidence
      Missing Decision Evidence
    Project Profiles /
      SILO
```

Recommended initial targets:

- `Research Brain / Solver Development OS / SILO-DOS / Overview`
- `Research Brain / Solver Development OS / SILO-DOS / Experience Maps`
- `Research Brain / Solver Development OS / SILO-DOS / Decision Memory`
- `Research Brain / Solver Development OS / Phase Playbooks`
- `Research Brain / Solver Development OS / Risk Patterns`
- `Research Brain / Solver Development OS / Failure Recovery Patterns`
- `Research Brain / Solver Development OS / Project Profiles / SILO`

These are proposed target names only. This local plan does not create or modify those
targets.

## 3. Document Split Plan

Recommended split:

```text
one master overview + several focused Research Brain documents
```

This is safer than one large document because future retrieval will usually need one
category at a time: risk gate, phase playbook, failure recovery, or project status. A
master overview should link the focused entries.

### Recommended Documents

1. `SILO-DOS v0.4 Overview`
   - Purpose: explain local mirror, Research Brain bridge, Mode A/B/C, and one-task
     discipline.
   - Source: export sections 1, 2, 4, 10.

2. `SILO Solver Reference Milestone Summary`
   - Purpose: record current solver milestone and deferred work.
   - Source: export sections 2 and 3, project profile, milestone audit.

3. `Experience Map`
   - Purpose: store high-confidence reusable patterns.
   - Source: export section 5 and `.silo-dos/experience_map.md`.

4. `Decision Memory`
   - Purpose: store durable phase and native-defer decisions.
   - Source: export section 6 and `.silo-dos/decision_log.md`.

5. `Phase Playbooks`
   - Purpose: store reusable phase-opening, phase-progress, parking, closure, and
     specific phase playbooks.
   - Source: export section 7.

6. `Risk and Gate Patterns`
   - Purpose: store L0/L1/L2/L3 classification rules and evidence requirements.
   - Source: export section 8 and standing approval profile.

7. `Failure and Recovery Patterns`
   - Purpose: store push failure, dirty worktree, duplicate task, stream disconnection,
     stale route, and missing evidence recovery patterns.
   - Source: export section 9 and remote sync proof.

8. `Research Brain Bridge Protocol`
   - Purpose: store local mirror vs Research Brain responsibilities and query/export
     packet rules.
   - Source: export section 10 and `.silo-dos/research_brain_bridge.md`.

9. `Import / Preload Protocol`
   - Purpose: define how to use Research Brain before a new project, new phase,
     implementation approval, or SILO-DOS migration.
   - Source: export section 12 and bridge preload guidance.

### Optional Master Document

Create `SILO Export v1 Master Overview` only if the user wants a single entry point. It
should be concise and link to the focused entries rather than duplicating all content.

## 4. Format Plan

Recommended format:

```text
both Google Docs style long-form document and Markdown mirror
```

Rationale:

- Google Docs style documents are easier for Research Brain browsing, comments, and
  human review.
- Markdown mirrors preserve repository-style structure, exact headings, and future
  diffability.
- The source-of-truth for execution remains repo-local `.silo-dos/`; Research Brain
  entries are memory/preload artifacts.

Preferred rule:

- Use Google Docs style long-form entries for Research Brain consumption.
- Keep a Markdown mirror or source pointer for versioned traceability.
- Each Research Brain document should include a source reference back to the repository
  file and report id.

## 5. Write Order

Recommended write order:

1. `SILO-DOS v0.4 Overview`.
2. `SILO Solver Reference Milestone Summary`.
3. `Experience Map`.
4. `Decision Memory`.
5. `Phase Playbooks`.
6. `Risk and Gate Patterns`.
7. `Failure and Recovery Patterns`.
8. `Research Brain Bridge Protocol`.
9. `Import / Preload Protocol`.

Reasoning:

- Overview first creates the navigation frame.
- Milestone summary sets project context.
- Experience and decision memory establish durable reusable facts.
- Phase, risk, and failure patterns then become searchable operational knowledge.
- Bridge and preload protocols explain how future use should remain safe.

## 6. Manual Vs Connector-Assisted Workflow

### Manual Workflow

Use this workflow if ChatGPT/Codex cannot directly write to Research Brain:

1. User reviews `.silo-dos/research_brain_export_v1.md`.
2. User reviews this write plan.
3. User decides which target documents to create.
4. Codex or ChatGPT prepares local Markdown or Google Docs-ready drafts in a later
   local-only task if requested.
5. User manually creates Research Brain entries and copies reviewed content.
6. User records completion in a future local report or `.silo-dos/` note only if useful.

Manual workflow safety:

- no connector dependency;
- user controls exact content and destination;
- Research Brain import cannot accidentally bypass local route or approval gates.

### Connector-Assisted Workflow

Use this workflow only if Google Drive / Research Brain access is available later and
the user explicitly approves connector use:

1. Run a new scoped task that explicitly allows connector use.
2. Recheck Remote Sync Proof and local route.
3. Read export packet and this write plan.
4. Create only the user-approved Research Brain documents.
5. Do not modify solver code, phase status, local skill, or public contracts.
6. Record document titles, target paths, connector result, and any failed writes in a
   matching local report.
7. Commit any local task/report artifacts only if scoped.

Connector-assisted workflow safety:

- never infer external-write approval from this plan;
- never write more documents than approved;
- never let Research Brain content override `.silo-dos/` local execution rules.

## 7. Research Brain Entry Schema

Each Research Brain entry should include:

```text
title:
category:
source_repository:
source_report_ids:
source_silo_dos_files:
version:
date:
status:
update_trigger:
related_decisions:
related_phases:
transferability:
scope:
non_goals:
safety_boundaries:
local_source_of_truth:
```

Field guidance:

- `title`: human-readable entry title.
- `category`: overview, experience map, decision memory, phase playbook, risk pattern,
  failure recovery, bridge protocol, or preload protocol.
- `source_repository`: `silo-solver`.
- `source_report_ids`: reports that support the entry.
- `source_silo_dos_files`: local mirror files used.
- `version`: `v1` for this export batch.
- `date`: entry creation date.
- `status`: draft, review-needed, active, superseded, or archived.
- `update_trigger`: event that requires revision.
- `related_decisions`: decision ids such as `DEC-20260604-P9-NATIVE-DEFER`.
- `related_phases`: applicable phase ids.
- `transferability`: project-specific, project-family, or cross-project.
- `scope`: what the entry is meant to guide.
- `non_goals`: what the entry must not be used to approve.
- `safety_boundaries`: hard stops that remain in force.
- `local_source_of_truth`: reminder that `.silo-dos/` and issued task contracts govern
  execution.

## 8. Versioning And Update Policy

### Versioning

Use sequential export versions:

```text
SILO-DOS-RB-EXPORT-V1
SILO-DOS-RB-EXPORT-V2
SILO-DOS-RB-EXPORT-V3
```

Research Brain entries created from this packet should include:

- version: `v1`;
- source file: `.silo-dos/research_brain_export_v1.md`;
- source task/report id: `20260607-08-01_research-brain-export-v1`;
- write-plan id: `20260607-09-01_research-brain-write-plan`.

### Regeneration Triggers

Regenerate or update an export when:

- a phase starts or closes;
- Phase 9 is closed, reopened, or moved out of parked state;
- Phase 10 planning starts;
- native implementation is approved, rejected, or permanently parked;
- local skill behavior changes;
- `.silo-dos/` structure changes;
- standing approval profile changes;
- repeated failures create a new high-confidence recovery pattern;
- Research Brain import/preload workflow is implemented or revised.

### Staleness Avoidance

To avoid stale Research Brain advice:

- every entry must state its source repository and version;
- every entry must link back to source `.silo-dos/` files and reports;
- strategic entries must include update triggers;
- Research Brain advice must be checked against current `.silo-dos/technical_route.md`;
- Research Brain advice must not be used as execution permission.

## 9. Import / Preload Use Cases

Use Research Brain entries later:

- before starting a new solver project, to preload SILO-DOS operating discipline and
  phase playbooks;
- before opening a new phase, to preload route design, non-goals, risk gates, and
  candidate task sequencing;
- before approving L2/L3 work, to preload decision templates, regression expectations,
  and hard-stop patterns;
- before migrating SILO-DOS to another repository, to preload local mirror structure,
  Remote Sync Proof, standing approval, and self-evolution mechanics;
- before revising standing approval, to compare historical safe patterns with current
  route constraints.

Preload should produce a local summary or Decision Packet. It should not directly update
`.silo-dos/` or authorize execution.

## 10. Safety Boundaries

Research Brain advice must not override:

- explicit user instruction;
- issued task contracts;
- `tasks/README.md`;
- `AGENTS.md`;
- `.silo-dos/technical_route.md`;
- `.silo-dos/decision_log.md`;
- `.silo-dos/standing_approval_profile.md`;
- `.silo-dos/remote_sync_proof.md`;
- L2/L3 gates;
- one-task-at-a-time execution;
- allowed and forbidden file lists;
- required checks;
- current local Git sync state.

Research Brain advice must not silently approve:

- phase start;
- phase closure;
- native implementation;
- dependency, build, packaging, or generated-artifact changes;
- solver dispatch or backend selector changes;
- public CLI changes;
- JSON schema changes;
- solver behavior changes;
- local `silo-development-operator` skill edits;
- task-system rule changes;
- Phase 10 planning or implementation.

If Research Brain and the local mirror disagree, Codex must stop and ask the user. If
the user resolves the disagreement, the durable result should be mirrored locally only
through a scoped task.

## 11. Recommended Next Action

Recommended next action:

```text
pause and wait for user review
```

The export is ready for user review. Direct external writing should not happen
automatically.

If the user approves writing to Research Brain later, the safest approach is to create
several focused Research Brain entries plus one overview. The recommended first write is
`SILO-DOS v0.4 Overview`, followed by milestone summary, experience map, decision
memory, phase playbooks, risk/failure patterns, and import/preload protocol.

No immediate solver task is required. No Phase 10 work is approved. Native
implementation remains deferred and unapproved.
