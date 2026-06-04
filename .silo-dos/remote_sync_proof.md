# SILO Remote Sync Proof

## Role Of This File

This file is the repository-local SILO-DOS v0.4 standard for proving whether a completed
run is synchronized with `origin/main`.

Remote synchronization is a checkable Git state, not a conversational assumption. A task
may create a local commit successfully while `git push` fails because of an HTTPS
connection reset, an SSL read failure, or another transient network problem. SILO-DOS
therefore records both the push command result and the local ahead/behind proof.

This file does not replace `tasks/README.md`, issued task contracts, execution reports,
or current user instructions. It standardizes the end-of-run sync section that reports
should use.

## Sources

Primary local mirror inputs:

- `.silo-dos/v04_architecture.md`
- `.silo-dos/project_profile.md`
- `.silo-dos/technical_route.md`

Recent push-failure evidence:

- `tasks/reports/20260604-15-01_technical-route_report.md`
- `tasks/reports/20260604-12-01_project-milestone-audit_report.md`
- `tasks/reports/20260604-10-01_native-defer-bookkeeping_report.md`
- `tasks/reports/20260604-08-01_phase9-policy-readiness-audit_report.md`
- `tasks/reports/20260524-13-01_phase6-closure-bookkeeping_report.md`

The recurring lesson is that a failed push must not erase or hide the local commit. The
local commit should be preserved, the failure should be recorded in the report, and a
later sync-only recovery can prove whether the branch has become synchronized.

## Required End-Of-Run Fields

Every SILO-DOS task that commits, pushes, or verifies synchronization should record these
fields in its report or final response:

```text
git status --short
git branch --show-current
git log --oneline -5
git rev-list --left-right --count origin/main...HEAD
git push result
remote_sync_status
```

The commands should be interpreted from the current local repository. For normal SILO
development, the intended branch is `main` unless the task explicitly states another
branch.

## Field Meanings

### `git status --short`

Records whether the working tree is clean.

- Empty output means no tracked or untracked working-tree changes are visible.
- Any output means the run is not clean and the next task should not start.

### `git branch --show-current`

Records the active branch. Most SILO-DOS runs expect `main`.

If the branch is not the expected branch, report the branch explicitly and do not infer
that the local commit synchronized to the intended remote branch.

### `git log --oneline -5`

Records the latest local history visible to Codex. This makes the reported commit hash
auditable without depending on chat memory.

### `git rev-list --left-right --count origin/main...HEAD`

Records local ahead/behind state relative to `origin/main`.

Interpretation:

```text
0 0   local HEAD and origin/main are synchronized
N 0   local branch is behind origin/main by N commits
0 N   local branch is ahead of origin/main by N commits
N M   local branch and origin/main have diverged
```

If the intended remote branch is not `origin/main`, the task must name the alternate
comparison explicitly.

### `git push result`

Records whether a push was attempted and what happened.

Use one of these plain outcomes in reports:

```text
not_attempted
succeeded
failed: <brief error>
not_required
```

A failed push is non-fatal for the completed local task, but it blocks starting another
development task until synchronization is recovered or the user explicitly approves a
recovery path.

### `remote_sync_status`

Records the final SILO-DOS sync classification for the run.

Allowed values are:

```text
synchronized_with_origin
local_ahead_origin
push_failed
dirty_worktree
connector_unverified
```

Do not invent additional values in task reports. If a future process task needs more
states, update this file or the relevant task-system rule in a scoped process task.

## Status Definitions

### `synchronized_with_origin`

Use when:

- `git status --short` is clean;
- the branch is the expected branch;
- `git rev-list --left-right --count origin/main...HEAD` is `0 0`;
- the push either succeeded, was not required, or a sync-only check proved that local
  tracking and `HEAD` are already aligned.

This status means Codex may start a later task if the user asks.

### `local_ahead_origin`

Use when:

- `git status --short` is clean;
- the branch is the expected branch;
- `git rev-list --left-right --count origin/main...HEAD` reports `0 N` with `N > 0`;
- no current push failure is being recorded for the task, or push was skipped by task
  Git mode.

This status means the local commit exists but remote synchronization is incomplete.
Codex should not start another development task unless the user explicitly approves
recovery or accepts working ahead of origin.

### `push_failed`

Use when:

- a push was attempted during the run; and
- the push command failed.

The report must preserve the local commit hash, record the error, and state whether the
report was amended to include the failure. Do not retry repeatedly inside the same
development task.

For the task that experienced the failed push, prefer `push_failed` even if a later
inspection might show `0 0`. A separate sync-only recovery can then establish
`synchronized_with_origin`.

### `dirty_worktree`

Use when `git status --short` is not clean after the task, including untracked files,
modified files, unstaged changes, or staged but uncommitted changes.

This status takes priority over push and ahead/behind interpretation. Codex must report
the dirty paths and avoid starting another task.

### `connector_unverified`

Use when local Git proof is incomplete or a task explicitly requires external connector
confirmation that could not be obtained.

Do not downgrade a clean local proof solely because ChatGPT or a remote connector was not
checked. ChatGPT remote connector verification is helpful, but it is not required when
local Git proof is clean and `origin/main...HEAD` reports `0 0`.

## Status Derivation Order

Use this order at the end of a task:

1. If `git status --short` is not clean, set `remote_sync_status` to `dirty_worktree`.
2. If a push was attempted and failed during this task, set `remote_sync_status` to
   `push_failed`.
3. If the worktree is clean and `origin/main...HEAD` reports `0 0`, set
   `remote_sync_status` to `synchronized_with_origin`.
4. If the worktree is clean and `origin/main...HEAD` reports `0 N`, set
   `remote_sync_status` to `local_ahead_origin`.
5. If the worktree is clean but connector-only evidence is required and unavailable, set
   `remote_sync_status` to `connector_unverified`.
6. If `origin/main...HEAD` reports `N 0` or `N M`, stop and report explicit recovery is
   needed. Use `local_ahead_origin` only for the `0 N` case; do not hide behind/diverged
   states.

## Required Workflow Rules

### Do Not Start Another Task Without Sync Proof

After a completed task, do not start another task unless:

- `remote_sync_status` is `synchronized_with_origin`; or
- the user explicitly approves recovery or explicitly approves continuing despite the
  reported sync state.

This protects the repository from stacking unclear local commits after a transient push
failure.

### Preserve Local Commits After Push Failure

If push fails:

- preserve the local commit;
- record the commit hash;
- record the exact push error or a concise error summary;
- amend the report only if the task scope and Git mode allow recording the failure;
- do not retry repeatedly in the same task;
- recommend a sync-only recovery step.

The failed push does not invalidate the task changes. It only means remote
synchronization is unresolved.

### Use Sync-Only Recovery

A sync-only recovery step should run no solver task and should not modify project files
unless recording recovery is explicitly scoped.

Recommended sync-only proof:

```text
git status --short
git branch --show-current
git log --oneline -5
git push
git rev-list --left-right --count origin/main...HEAD
```

If the final ahead/behind proof is `0 0` and the worktree is clean, report
`remote_sync_status: synchronized_with_origin`.

### Local Git Proof Is Primary

Codex local Git proof is the primary source of sync truth for SILO-DOS.

ChatGPT remote connector verification, GitHub UI checks, or external remote inspection
can be useful when available, especially after confusing network failures. They are not
required when local Git proof is clean, the expected branch is active, and
`origin/main...HEAD` reports `0 0`.

## Report Template

Use this compact block in future execution reports:

```text
## Remote Sync Proof

- `git status --short`: <clean or captured output>
- `git branch --show-current`: <branch>
- `git log --oneline -5`: <latest five commits or summary>
- `git rev-list --left-right --count origin/main...HEAD`: <left right>
- `git push result`: <not_attempted | succeeded | failed: reason | not_required>
- `remote_sync_status`: <allowed status>
```

For final responses, include the same information in condensed prose when the user needs
to know whether the completed task reached GitHub.

## Non-Goals

This file does not:

- change Git modes in `tasks/README.md`;
- require remote connector checks for every task;
- authorize repeated push retries inside one task;
- authorize starting another task after a failed push;
- modify solver code, tests, examples, CLI behavior, JSON schemas, build files,
  dependencies, native implementation, roadmap, or phase records;
- start Phase 10.

## Current Application

The current repository route is parked after the Phase 9 native implementation defer
decision. Process documentation tasks such as this file are L0 and may be run under
Mode A when explicitly requested. They do not approve native implementation, Phase 9
closure, or Phase 10 planning.
