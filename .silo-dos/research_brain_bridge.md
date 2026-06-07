# SILO-DOS v0.4 Research Brain Bridge

## Role Of This Design

This note defines how SILO-DOS v0.4 should connect the repository-local `.silo-dos/`
mirror with the remote Research Brain as a long-term experience and decision-memory
center.

This is a design-only process-governance note. It does not implement connector logic,
write to Research Brain, modify the local `silo-development-operator` skill, change
solver behavior, change task-system rules, close Phase 9, start Phase 10, or approve
native backend implementation.

## Sources

Primary local mirror inputs:

- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/remote_sync_proof.md`
- `.silo-dos/experience_map.md`
- `.silo-dos/standing_approval_profile.md`
- `.silo-dos/self_evolution.md`
- `.silo-dos/local_skill_integration_design.md`

Recent process evidence:

- `tasks/reports/20260606-01-01_silo-dos-v04-local-mirror-pilot_report.md`
- `tasks/reports/20260607-03-01_v04-smoke-test_report.md`
- `tasks/reports/20260607-06-01_v04-hard-stop-smoke_report.md`

Stable repository rules:

- `tasks/README.md`
- `AGENTS.md`

## Purpose

The bridge has two purposes.

First, it gives Codex and ChatGPT a controlled way to use Research Brain experience when
the local mirror is insufficient for a strategic decision. The bridge should prevent
guesswork while preserving SILO-DOS hard stops.

Second, it defines how useful execution experience should flow back into long-term
memory without turning `.silo-dos/` into a large archive or allowing Research Brain to
override repository-local execution rules.

The target decision chain is:

```text
local .silo-dos mirror -> Research Brain query packet -> user decision
```

The target experience flows are:

```text
local reports / experience_map / decisions -> Research Brain export
Research Brain experience / phase playbooks -> local mirror preload
```

## Role Separation

### Local `.silo-dos/` Mirror

The `.silo-dos/` directory is the repository-local execution mirror. It records the
project state, route corridor, durable decisions, standing approvals, remote sync proof,
experience patterns, and self-evolution rules that Codex can read directly from the
repository.

The local mirror is authoritative for task execution only because it is repository
visible, source-linked, and bounded by `tasks/README.md`, `AGENTS.md`, issued task
contracts, and current user instructions.

The local mirror should contain stable, compact, auditable operating knowledge. It
should not become a complete duplicate of all task reports or Research Brain notes.

### Research Brain

Research Brain is the long-term experience center. It may store cross-project lessons,
phase playbooks, user strategy preferences, failure/recovery patterns, research-method
judgment, and planning knowledge that is broader than one repository.

Research Brain can propose, compare, and recall. It does not approve repository
execution. Its advice becomes executable only when it is consistent with the current
task contract and local mirror, or when the user explicitly resolves the decision and a
future repository task mirrors the durable decision locally.

Research Brain must not be a hard dependency for every SILO task. Most L0/L1 tasks should
continue from `.silo-dos/`, task contracts, reports, and repository rules when those
sources are sufficient.

### User

The user remains the final authority for strategic movement and hard gates. User
decisions are required when local mirror evidence is missing, stale, conflicting, or
insufficient for an L2/L3 decision.

User decisions should later be recorded back into `.silo-dos/` and exported to Research
Brain when they become durable project knowledge.

## Decision Lookup Chain

### Step 1: Local Mirror Lookup

Codex first checks:

1. current user instruction;
2. issued task contract, when one exists;
3. `.silo-dos/project_profile.md`;
4. `.silo-dos/technical_route.md`;
5. `.silo-dos/decision_log.md`;
6. `.silo-dos/remote_sync_proof.md`;
7. `.silo-dos/standing_approval_profile.md`;
8. `.silo-dos/experience_map.md`;
9. `.silo-dos/self_evolution.md`;
10. `.silo-dos/v04_architecture.md`;
11. `.silo-dos/local_skill_integration_design.md`;
12. `tasks/README.md`, `AGENTS.md`, recent reports, and relevant source notes.

If these sources are explicit, current, and source-linked, Codex proceeds inside the
local route and applies the normal SILO-DOS risk gates.

### Step 2: Research Brain Query Packet

If the local mirror is insufficient for a strategic decision, Codex prepares a Research
Brain Query Packet instead of guessing.

The packet is a structured request for experience. It should ask Research Brain for
prior patterns, phase playbooks, comparable decisions, failure modes, and candidate
options. It should not ask Research Brain to approve execution.

### Step 3: User Decision

If Research Brain still cannot resolve the decision, or if Research Brain advice
conflicts with local repository evidence, Codex asks the user.

User decisions should be captured as Decision Packets when they cross L2/L3 boundaries.
After the user decides, a later scoped task may update `.silo-dos/decision_log.md`,
`.silo-dos/technical_route.md`, `.silo-dos/experience_map.md`, or another relevant local
mirror file.

## Research Brain Query Packet

Use this packet when the local mirror lacks enough evidence for a strategic or
experience-based decision.

```text
Research Brain Query Packet

decision_question:
current_phase_or_corridor:
task_objective:
risk_classification:
files_likely_to_change:
local_mirror_lookup_result:
missing_evidence:
requested_research_brain_experience:
candidate_options:
recommended_fallback_if_unavailable:
safety_boundaries:
local_artifact_to_update_if_resolved:
```

Field meanings:

- `decision_question`: the exact decision that local sources cannot resolve.
- `current_phase_or_corridor`: the active phase or route state, such as
  `phase9_parked_on_design_bookkeeping_after_native_defer`.
- `task_objective`: the one primary objective being considered.
- `risk_classification`: L0, L1, L2, or L3, with the reason.
- `files_likely_to_change`: expected repository files, if a later task proceeds.
- `local_mirror_lookup_result`: what `.silo-dos/` and repository sources say.
- `missing_evidence`: what is absent, stale, or conflicting.
- `requested_research_brain_experience`: prior lessons, playbooks, patterns, failures,
  or strategy needed.
- `candidate_options`: bounded options, including a no-action option when appropriate.
- `recommended_fallback_if_unavailable`: what Codex should do if Research Brain cannot
  be reached.
- `safety_boundaries`: rules Research Brain advice cannot override.
- `local_artifact_to_update_if_resolved`: the likely future `.silo-dos/` file or report
  destination if the decision becomes durable.

Recommended fallback when Research Brain is unavailable:

```text
Continue only if the local mirror fully resolves the task inside the approved technical
route. Otherwise stop and ask the user with a Decision Packet.
```

## Research Brain Export Packet

Use this packet when repository-local experience should be promoted to long-term
Research Brain memory.

```text
Research Brain Export Packet

export_subject:
source_repository:
source_files:
phase_or_corridor:
task_ids_or_report_ids:
decision_ids:
experience_patterns:
risk_patterns:
failure_or_recovery_patterns:
milestone_or_phase_lessons:
standing_approval_candidates:
local_boundaries:
recommended_research_brain_tags:
not_for_export:
```

Export sources may include:

- `.silo-dos/experience_map.md`;
- `.silo-dos/decision_log.md`;
- milestone audits;
- phase closure reports;
- phase readiness reports;
- failure packets and recovery reports;
- repeated push failure or sync recovery patterns;
- repeated L2/L3 hard-stop patterns;
- self-evolution candidates.

Export should be selective. It should prefer reusable patterns over raw logs. It should
exclude secrets, credentials, personal local paths where not necessary, large generated
outputs, and one-off task noise.

Research Brain export should preserve the distinction between:

- a repository rule;
- a user preference;
- a one-time task decision;
- a candidate future direction;
- a failure pattern;
- a reusable phase playbook.

Exporting a lesson does not modify the repository and does not approve future execution.

## Research Brain Import / Preload Protocol

Use preload before starting a new phase, opening a new solver project, or entering a
strategic planning task where prior experience matters.

The preload flow is:

```text
Research Brain experience -> preload summary -> local mirror proposal -> user or task
approval -> scoped .silo-dos update
```

Preload should gather:

- phase playbooks;
- known risk patterns;
- standing approval candidates;
- prior project lessons;
- failure and recovery patterns;
- method-specific design traps;
- reproducibility conventions;
- route-selection cautions.

Preload must not directly overwrite `.silo-dos/`. Imported experience should first be
summarized into a local preload proposal or task context. A repository update requires a
separate scoped task unless the current task explicitly allows the target local mirror
file.

Recommended preload packet:

```text
Research Brain Preload Packet

preload_context:
target_project_or_phase:
local_project_state:
user_strategic_goal:
relevant_prior_projects:
phase_playbooks:
known_risk_patterns:
standing_approval_candidates:
failure_recovery_patterns:
recommended_local_mirror_updates:
items_requiring_user_decision:
items_to_ignore_for_this_project:
```

Preload results should be conservative. If Research Brain memory is useful but not yet
approved for SILO, it remains advisory until mirrored locally through an issued task.

## Phase Entry Intelligence Preparation

Every future phase entry should begin with an intelligence preparation step before any
implementation task is issued.

The phase-entry preparation should combine:

- local project state from `.silo-dos/`, `ROADMAP.md`, `tasks/phases/`, reports, and
  notes;
- Research Brain prior experience, including phase playbooks and known failure modes;
- the user's current strategic goals and risk tolerance.

The output should be a phase-entry decision packet or phase technical route proposal,
not immediate implementation.

Recommended contents:

```text
Phase Entry Intelligence Packet

phase_name:
local_current_state:
user_strategic_goal:
research_brain_playbooks_used:
prior_failure_patterns:
candidate_phase_objectives:
non_goals:
risk_gates:
candidate_atomic_task_sequence:
first_safe_task:
decisions_required_before_execution:
local_mirror_files_to_update:
```

For SILO, this is especially important before any future Phase 9 closure, Phase 10
planning, native implementation movement, public CLI/schema expansion, solver dispatch
change, or new capability line.

## Experience Map Extraction

Historical SILO reports should be mined into reusable experience before export or local
mirror update.

Extraction should identify:

- reusable patterns;
- risk patterns;
- decision templates;
- phase templates;
- failure patterns;
- migration lessons;
- check sets by task type;
- approval language that should remain explicit;
- cases where design did not imply implementation.

Recommended extraction fields:

```text
experience_id:
source_reports:
task_type:
risk_level:
route_context:
files_changed:
checks_run:
decision_or_stop_reason:
failure_mode:
recovery_action:
reusable_rule:
transferability:
confidence:
destination:
```

Only high-confidence patterns should be promoted into `.silo-dos/experience_map.md`.
Medium-confidence or cross-project lessons may be better suited for Research Brain.
Low-confidence observations should stay in the task report unless they recur.

## Degraded Mode

Research Brain may be unavailable, incomplete, stale, or outside the current Codex
execution environment. SILO-DOS must remain usable in that state.

In degraded mode:

- the local mirror remains authoritative for repository execution;
- Codex may continue only inside the approved local technical route;
- L0/L1 work may proceed only when `.silo-dos/`, the issued task contract, and Remote
  Sync Proof are sufficient;
- uncertain strategic decisions fall back to a user Decision Packet;
- no L2/L3 movement may proceed based on missing Research Brain access;
- Research Brain import/export is skipped and recorded as unavailable when relevant.

Degraded mode should prefer stopping over inventing strategy.

## Safety Boundaries

Research Brain advice must not override:

- explicit user instruction;
- an issued task contract;
- `tasks/README.md`;
- `AGENTS.md`;
- `.silo-dos/technical_route.md`;
- `.silo-dos/decision_log.md`;
- `.silo-dos/standing_approval_profile.md`;
- `.silo-dos/remote_sync_proof.md`;
- L2 and L3 hard stops;
- one-task-at-a-time execution;
- allowed and forbidden file lists;
- required checks and stop conditions.

Research Brain also must not silently approve:

- phase start;
- phase closure;
- native implementation;
- native dependency, build, packaging, or generated-artifact policy changes;
- solver dispatch or backend selector changes;
- public CLI changes;
- JSON schema changes;
- solver behavior changes;
- local `silo-development-operator` skill edits;
- task-system rule changes.

If Research Brain and the local mirror disagree, Codex should stop and ask the user.
If the user resolves the disagreement, the durable result should be mirrored locally in a
later scoped task.

## Non-Goals

This design does not:

- implement Google Drive or Research Brain connector logic;
- write to Research Brain;
- modify the local `silo-development-operator` skill;
- modify solver source code;
- modify tests;
- modify examples;
- modify `ROADMAP.md`;
- modify `tasks/phases/`;
- modify existing notes;
- modify existing `.silo-dos/` files;
- create templates yet;
- change task-system rules;
- start Phase 10;
- close Phase 9;
- implement native backend;
- change public CLI behavior;
- change JSON schemas;
- add dependencies;
- modify build or packaging files;
- change solver dispatch or backend selection behavior;
- authorize multi-task execution.

## Current Application To SILO

The current route remains:

```text
phase9_parked_on_design_bookkeeping_after_native_defer
```

The Research Brain bridge does not move the route. It only clarifies how future
strategic questions should be escalated when `.silo-dos/` is insufficient.

For current SILO work:

- routine L0 process tasks can still run from local mirror evidence when scoped;
- L2/L3 tasks still require explicit user approval;
- Research Brain can help with phase playbooks or cross-project lessons;
- Research Brain cannot start Phase 10, close Phase 9, or approve native work.

## Maintenance Rule

Update this bridge only through a separate atomic SILO-DOS process task. Revisit it
when:

- a Research Brain connector becomes available and a connector-design task is explicitly
  approved;
- `.silo-dos/templates/` are created;
- the local operator skill changes Research Brain packet behavior;
- repeated reports show that import/export fields are too broad or too narrow;
- the user's Research Brain workflow changes.

Do not treat this design note as permission to implement those follow-up changes.
