# Task: 20260606-01-01 SILO-DOS v0.4 Local Mirror Pilot

## Metadata

- Task ID: `20260606-01-01`
- Slug: `silo-dos-v04-local-mirror-pilot`
- Date: 2026-06-06
- SILO-DOS mode: Mode A auto-one
- Risk level: L0 safe process audit
- Git mode: `push-on-success`
- Expected report: `tasks/reports/20260606-01-01_silo-dos-v04-local-mirror-pilot_report.md`

## Objective

Issue and execute exactly one L0 SILO-DOS v0.4 local mirror pilot audit to test whether
the current `.silo-dos/` local mirror can be used as the primary decision source for
SILO-DOS task judgment, without changing solver functionality or expanding the v0.4
design.

## Scope Lock

This is a process audit only. It must inspect the current `.silo-dos/` local mirror and
recent milestone/post-defer reports, then record findings in the matching report.

## Local Mirror Files To Inspect

- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`
- `.silo-dos/decision_log.md`
- `.silo-dos/remote_sync_proof.md`
- `.silo-dos/experience_map.md`
- `.silo-dos/standing_approval_profile.md`
- `.silo-dos/self_evolution.md`

## Audit Questions

The report must answer:

1. What is the current project status according to the `.silo-dos/` local mirror?
2. What actions are currently allowed?
3. What actions are currently forbidden?
4. What tasks would require L2 or L3 approval?
5. What tasks could Mode A auto-execute under standing approval?
6. Does the local mirror agree with recent milestone / post-defer reports?
7. Does the remote sync proof protocol provide enough information for end-of-run status?
8. Is there any immediate next task required?
9. If no immediate task is required, say so explicitly.
10. If a future task is suggested, classify it but do not issue it.

## Allowed Changes

- Add this matching task file under `tasks/codex/`
- Add the matching report file under `tasks/reports/`

## Forbidden Changes

- Do not modify solver source code under `src/`.
- Do not modify tests.
- Do not modify examples.
- Do not modify `ROADMAP.md`.
- Do not modify files under `tasks/phases/`.
- Do not modify existing notes.
- Do not modify any existing `.silo-dos/` file.
- Do not create new `.silo-dos/` design files.
- Do not modify the local `silo-development-operator` skill.
- Do not start Phase 10.
- Do not implement native backend.
- Do not change CLI behavior.
- Do not change JSON schemas.
- Do not add dependencies.
- Do not modify build or packaging files.
- Do not change solver dispatch or backend selection behavior.
- Do not issue or execute another task.

## Required Report Content

The report must include:

- task objective;
- risk level;
- task ID scan result;
- files changed;
- local mirror files inspected;
- inferred current project status;
- allowed actions;
- forbidden actions;
- L0/L1 auto-execution corridor;
- L2/L3 hard-stop gates;
- agreement or disagreement with recent milestone reports;
- remote sync proof assessment;
- whether any immediate next task is required;
- checks run and results;
- deviations from scope, if any;
- git status before and after;
- remote sync proof;
- commit hash;
- push result;
- next recommended action.

## Expected Conclusion

The report should likely conclude:

- SILO reference solver milestone is complete.
- Phase 8 is complete.
- Phase 9 is open but parked on design/bookkeeping after native defer.
- Native implementation is deferred and not approved.
- Phase 10 is not started.
- No immediate solver implementation task is required.
- `.silo-dos/` is usable as a local decision mirror, but local skill v0.4 integration
  remains future work.

## Required Checks

Run at least:

```text
git status --short
git branch --show-current
git log --oneline -5
git rev-list --left-right --count origin/main...HEAD
git diff --check
```

Also run `git diff --cached --check` before commit.

Do not run full solver tests unless executable files are unexpectedly modified. Do not
run native build commands or native tooling.

## Acceptance Criteria

- The matching report answers all audit questions.
- The report compares the local mirror with recent milestone/post-defer reports.
- The report states whether any immediate next task is required.
- Only the matching task and report files are changed.
- Required checks pass.
- A local commit is created after checks pass.
- Push is attempted once if possible.

## Stop Conditions

Stop and report instead of expanding scope if completion would require:

- modifying solver source code, tests, examples, roadmap, phase files, existing notes,
  `.silo-dos` files, or the local skill;
- changing public CLI behavior or JSON schemas;
- adding dependencies;
- modifying build or packaging files;
- changing solver dispatch or backend selector behavior;
- implementing native backend;
- starting Phase 10;
- issuing or executing another task.

## Final Response Requirements

Report only:

- task path;
- report path;
- whether the local mirror pilot audit was completed;
- whether checks passed;
- commit hash;
- whether push succeeded;
- inferred current project status;
- whether any immediate next task is required.

Stop after this one atomic task.
