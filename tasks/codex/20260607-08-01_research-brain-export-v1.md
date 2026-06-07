# SILO Codex Task: Research Brain Export Packet v1

## Task Metadata

- Task ID: `20260607-08-01`
- Slug: `research-brain-export-v1`
- Risk level: L3 design-only process-governance export packet, executed as a scoped
  L0-style local documentation change
- Task type: SILO-DOS v0.4 Research Brain export preparation
- Mode: SILO-DOS Mode A auto-one
- Git mode: `push-on-success`
- Expected report: `tasks/reports/20260607-08-01_research-brain-export-v1_report.md`

## Objective

Create a repository-local Research Brain export packet that compresses the current SILO
solver and SILO-DOS v0.4 experience into a structured long-term knowledge package
suitable for later writing into the remote Research Brain.

This task must not write to Google Drive, Research Brain, external services, or any
connector. It only prepares the export packet locally.

## Primary Output

- `.silo-dos/research_brain_export_v1.md`

## Primary Inputs

Read before writing the export packet:

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
- latest `tasks/reports/*research-brain-bridge*_report.md`
- `tasks/README.md`
- `AGENTS.md`
- `ROADMAP.md`
- `tasks/phases/`

## Allowed Changes

- `.silo-dos/research_brain_export_v1.md`
- `tasks/codex/20260607-08-01_research-brain-export-v1.md`
- `tasks/reports/20260607-08-01_research-brain-export-v1_report.md`

## Forbidden Changes

- Do not modify solver source code under `src/`.
- Do not modify tests.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not modify existing `.silo-dos/` files.
- Do not modify existing notes.
- Do not modify the local `silo-development-operator` skill.
- Do not start Phase 10.
- Do not implement native backend.
- Do not change CLI behavior.
- Do not change JSON schemas.
- Do not add dependencies.
- Do not modify build or packaging files.
- Do not change solver dispatch or backend selection behavior.
- Do not write to Google Drive, Research Brain, or external services.
- Do not issue or execute another task.

## Export Packet Requirements

Create `.silo-dos/research_brain_export_v1.md` with these sections:

1. Export Metadata.
2. Executive Summary.
3. Solver Capability Summary.
4. SILO-DOS v0.4 System Summary.
5. Reusable Development Patterns.
6. Decision Memory Export.
7. Phase Playbook Export.
8. Risk And Gate Patterns.
9. Failure And Recovery Patterns.
10. Research Brain Bridge Rules.
11. Suggested Research Brain Target Structure.
12. Import / Preload Guidance.
13. Open Questions.
14. Recommended Next Action.

The packet must clearly state that it is local-only and does not itself write to
Research Brain.

## Required Checks

Run at least:

```text
git status --short
git branch --show-current
git log --oneline -5
git rev-list --left-right --count origin/main...HEAD
git diff --check
git diff --cached --check
```

Do not run full solver tests unless executable files are unexpectedly modified. Do not
run native build commands or native tooling.

## Acceptance Criteria

- Exactly one task is issued and executed.
- The export packet is created locally.
- The export packet includes all required sections.
- The task does not write to Research Brain, Google Drive, or any external service.
- Only allowed files are changed.
- Required checks pass.
- The matching report is created.
- Repository changes are committed locally.
- Push is attempted once.
- Remote Sync Proof is recorded in the final report and final response.

## Stop Conditions

Stop and report if:

- the worktree is dirty before execution with unrelated files;
- `origin/main...HEAD` is not `0 0` before execution;
- required input files are missing;
- execution would require forbidden file changes;
- execution would require an external connector call or external write;
- any required check fails;
- the task would need a second atomic objective.
