# Task: 20260605-03-01 Experience Map

## Metadata

- Task ID: `20260605-03-01`
- Slug: `experience-map`
- Date: 2026-06-05
- SILO-DOS mode: Mode A auto-one
- Risk level: L0 safe documentation/process task
- Git mode: `push-on-success`
- Expected report: `tasks/reports/20260605-03-01_experience-map_report.md`

## Objective

Create `.silo-dos/experience_map.md` from high-confidence reusable patterns in historical
SILO reports.

## Context

Use these primary inputs:

- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/remote_sync_proof.md`
- recent reports under `tasks/reports/`

The current route remains `phase9_parked_on_design_bookkeeping_after_native_defer`.
This task is process documentation only.

## Scope Lock

Extract only high-confidence patterns that are supported by historical reports or current
`.silo-dos/` local mirror files. Do not reinterpret one-off events as durable rules.

## Required Patterns

The experience map must include patterns such as:

- passive records plus validation tests are usually safe L1 when no public behavior
  changes;
- phase closure is always L3;
- native implementation is always L3;
- push failure requires sync-only recovery;
- design-only planning does not imply implementation approval;
- examples-only tasks can be L0 if no source/test/CLI/schema changes are made;
- Research Brain should be long-term memory, while `.silo-dos` is the repo-local
  execution mirror.

For each pattern include:

- pattern id;
- context;
- evidence source;
- auto-action rule;
- stop conditions;
- confidence;
- transferability;
- update condition.

## Allowed Changes

- Add `.silo-dos/experience_map.md`
- Add this task file under `tasks/codex/`
- Add the matching report under `tasks/reports/`

## Forbidden Changes

- Do not modify solver source code.
- Do not modify tests.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify `tasks/phases/`.
- Do not modify existing notes.
- Do not modify existing task files.
- Do not modify the local `silo-development-operator` skill.
- Do not start Phase 10.
- Do not implement native backend.
- Do not add native dependencies.
- Do not modify build or packaging files.
- Do not change public CLI behavior.
- Do not change JSON schemas.
- Do not change solver dispatch.

## Required Checks

Run:

```text
git status --short
git branch --show-current
git log --oneline -5
git rev-list --left-right --count origin/main...HEAD
git diff --check
git diff --cached --check
```

No solver tests are required because this task does not modify executable code, tests,
examples, public CLI behavior, JSON schemas, native code, dependencies, build files, or
packaging files.

## Acceptance Criteria

- `.silo-dos/experience_map.md` exists.
- The file includes high-confidence historical patterns with the required fields.
- The file distinguishes repository-local `.silo-dos` memory from Research Brain memory.
- The file does not authorize Phase 10, native implementation, public contract changes,
  or multi-task automation.
- The matching report is created.
- Required checks pass.
- Only the allowed files are changed.

## Stop Conditions

Stop and report instead of expanding scope if completion would require:

- modifying solver source code, tests, examples, roadmap, phase files, existing notes,
  or the local skill;
- changing task-directory rules;
- changing public CLI or JSON schemas;
- implementing native backend work;
- starting Phase 10;
- running another atomic task.

## Final Response Requirements

Report:

- generated task path;
- experience map path;
- report path;
- checks run;
- commit hash;
- push result;
- final remote sync proof.

Stop after this one atomic task.
