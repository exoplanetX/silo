# SILO Task Directory Rules

## 1. Purpose of `tasks/`

The `tasks/` directory manages long-term phase plans, issued Codex task prompts and execution reports. Current status is summarized in [project_profile.md](../.silo-dos/project_profile.md); find historical contracts/reports through [INDEX.md](INDEX.md).

## 2. Folder Roles

```text
tasks/phases/
```

Long-term phase roadmap files. These describe solver-development phases, goals, scope, expected files, testing requirements, and acceptance criteria. They are not one-off Codex commands.

```text
tasks/codex/
```

Issued Codex task prompts. These are the task instructions sent to Codex for execution.

Files under `tasks/codex/` are immutable after creation. Coding agents may read them, but must not edit, rename, delete, or move existing files unless the user explicitly asks for task-file maintenance.

```text
tasks/reports/
```

Execution reports are required for executed tasks under section 6.5. Issuance-only or planning contracts may have no execution report yet. Record actual work, checks and failures here instead of modifying an issued task file.

## 3. Naming Rules

For long-term phase files:

```text
tasks/phases/phase_XX_short-name.md
```

Examples:

```text
tasks/phases/phase_01_model_core.md
tasks/phases/phase_02_tableau_simplex.md
```

For issued Codex task files:

```text
tasks/codex/YYYYMMDD-TT-RR_slug.md
```

Where:

```text
YYYYMMDD = date
TT       = task block number on that date, fixed two digits
RR       = revision number of that task block, fixed two digits
slug     = short kebab-case task label, preferably 1-3 words
```

Examples:

```text
tasks/codex/20260519-01-01_phase-num.md
tasks/codex/20260519-02-01_task-rules.md
tasks/codex/20260519-03-01_model-core.md
tasks/codex/20260519-03-02_model-core.md
```

Meaning:

```text
20260519-03-01_model-core.md
```

means the first version of the third task block issued on 2026-05-19.

### 3.1 Task ID Uniqueness

The `YYYYMMDD-TT-RR` prefix identifies a specific issued task identity. Two different task slugs must not share the same `YYYYMMDD-TT-RR` prefix.

The `RR` component is only for revisions of the same task block. A new unrelated task on the same date must use the next available `TT` value, starting again at `RR = 01`.

Before creating a new task file, Codex must scan existing files under both:

```text
tasks/codex/
tasks/reports/
```

For the intended `YYYYMMDD` date, Codex must identify already used `TT` values and exact `YYYYMMDD-TT-RR` prefixes. If the intended prefix already exists for a different slug, Codex must choose the next available `TT` rather than reusing the prefix.

Existing historical collisions are task-system debt. They must not be repaired by renaming immutable task files unless the user explicitly requests task-file maintenance.

For execution reports:

```text
tasks/reports/YYYYMMDD-TT-RR_slug_report.md
```

Example:

```text
tasks/reports/20260519-02-01_task-rules_report.md
```

## 4. Revision Rule

Do not overwrite an issued Codex task file to revise it.

If a task needs revision, create a new file with an incremented `RR` value.

Example:

```text
tasks/codex/20260519-03-01_model-core.md
tasks/codex/20260519-03-02_model-core.md
```

## 5. Rule Change Rule

If the task system itself needs to change in the future, `tasks/README.md` must be updated first or in the same commit.

No future task-directory restructuring should be done without updating this rule file.

## 6. SILO Development Operating System

The SILO Development Operating System, abbreviated as SILO-DOS, is the operating protocol that governs how solver development knowledge is converted into controlled Codex tasks.

SILO-DOS does not replace the folder roles, naming rules, revision rule, or rule-change rule above. It adds an execution layer on top of the existing `tasks/` convention:

- `tasks/phases/` contains long-term development knowledge.
- `tasks/codex/` contains immutable issued task contracts.
- `tasks/reports/` contains execution memory.
- `tasks/` must not be treated as a general notes folder.

### 6.1 Phase-to-Task Rule

A phase file is not itself a Codex task. A phase file contains goals, scope, expected files, tests, acceptance criteria, and development knowledge for a broader development phase.

A Codex task must be traceable to one of the following:

- a specific phase item;
- an explicit maintenance need;
- a user-approved process task.

Only one atomic Codex task should be issued and executed at a time. If a phase item is too large to complete safely in one step, it must be split into multiple issued task files under `tasks/codex/`.

### 6.2 Atomic Task Rule

Each Codex task must solve exactly one primary problem. A task may include supporting documentation, tests, and reports, but those supporting changes must serve the same primary objective.

Every issued Codex task should include:

- task metadata;
- objective;
- phase reference;
- task type;
- scope lock;
- allowed changes;
- forbidden changes;
- required tests or checks;
- acceptance criteria;
- stop conditions;
- expected report path;
- Git mode.

If any of these fields are missing, Codex should infer the safest narrow interpretation from the task text and record the ambiguity in the execution report.

### 6.3 Scope Lock Rule

Codex must stay within the task objective and the allowed files. The allowed change list is a boundary, not a suggestion.

If Codex discovers a broader issue while executing a task, it should document the issue in the report instead of fixing it within the same task. A broader issue should become a later atomic task unless the user explicitly expands the current task scope.

Codex must not use a small task as an opportunity for unrelated cleanup, refactoring, formatting, solver behavior changes, or documentation rewrites.

### 6.4 Git Mode Rule

Each task should declare one Git mode:

```text
no-git
local-commit
push-on-success
sync-only
```

The modes are:

- `no-git`: modify files only; do not commit or push.
- `local-commit`: commit locally after successful checks; do not push. This is the default mode.
- `push-on-success`: commit locally and attempt one push only after successful checks.
- `sync-only`: do not modify project files; only synchronize already committed local changes with the remote repository.

Push failure is non-fatal. If a push fails, Codex must preserve the local commit, report the failure clearly, and record the failed push in the execution report.

### 6.5 Execution Report Rule

Every executed task must create a report under `tasks/reports/` using the matching task ID and slug:

```text
tasks/reports/YYYYMMDD-TT-RR_slug_report.md
```

The report should include:

- task objective;
- files changed;
- checks or tests run;
- results;
- deviations from scope, if any;
- Git status before and after;
- local commit hash, if created;
- push attempted or skipped;
- unresolved issues;
- next recommended atomic task.

Reports must record execution memory. They must not revise the issued task contract.

### 6.6 One-Step Execution Rule

Codex must stop after completing one atomic task. It must not automatically continue to the next task, phase item, cleanup item, or follow-on implementation unless the user explicitly asks it to continue.

The next recommended atomic task may be recorded in the report, but recommendation is not execution permission.

### 6.7 Responsibility Boundary

The intended responsibility split is:

- The user may set priorities, approve task scope, request pushes, and resolve conflicts.
- ChatGPT or the user may design phase strategy, revise high-level direction, and approve phase transitions.
- Codex executes one task at a time according to issued task contracts and local repository rules.
- GitHub stores synchronized commits and remote collaboration state; it is not the source of task interpretation.

Codex should not depend on a live ChatGPT conversation to interpret task boundaries. It should rely on `tasks/README.md`, phase files, issued task files, prior reports, and explicit user instructions in the current Codex session.

### 6.8 Development Companion Learning

The dedicated `learning/` directory contains reader-oriented explanations, derivations,
research connections, limitations, exercises and solutions. Its stable lesson catalog
supports chronological review and later thematic course/book organization. It remains
outside `tasks/`; task contracts and reports retain their existing roles.

For newly issued tasks concerning models, algorithms, mathematical conventions,
numerical handling or correctness fixes:

- Declare a **Learning delivery** field with the lesson to create or update and include
  its paths in allowed changes. A task may deepen an existing lesson rather than create one.
- Follow `learning/README.md` and `learning/WRITING_GUIDE.md`; provide principle,
  hand-worked example, code/test mapping, research significance and limits, with practice
  and solutions proportionate to the change.
- Record the real verified code baseline and checks. Update `learning/CATALOG.md` for
  new lessons, and link learning outputs/checks in the execution report.

Pure sync, formatting or administrative work may state **Learning delivery: not
applicable**, with a short reason, or update only the affected navigation/metadata.
One learning lesson can accumulate several atomic tasks. Learning work must stay
within the task's scope lock and cannot authorize another algorithm or phase.

This requirement applies prospectively; do not revise old immutable contracts or
historical reports to retrofit it. Teaching material has one canonical body under
`learning/`; current usage and API reference belong under `docs/`, while original
design/research records remain under `notes/`.

## 7. Current Entry, History Index and Baselines

- `.silo-dos/project_profile.md` is the single current-status summary: completed items,
  verified code baselines, active scope and recommendations. Technical gates remain in
  `technical_route.md`; durable decisions remain in `decision_log.md`.
- Keep execution history in reports rather than appending the same chronology to both
  current-status and route files. A historical next-step recommendation is not a pending
  task or approval; cross-check the current summary before issuance.
- `tasks/INDEX.md` is derived navigation, not an approval/status database. It links every
  contract and report, including revisions and known historical identity collisions.
  A report's presence does not establish execution success; an absent report does not
  establish failure. Read the record and its Git history.
- Regenerate the small Markdown navigation index after adding a contract/report:

  ```text
  python scripts/check_project_structure.py --write-index
  python scripts/check_project_structure.py
  ```

- The generated index is versioned documentation. Run outputs, caches, large data and
  binary artifacts remain excluded. `scripts/check_quality.py` checks the index and
  project structure before the existing pytest/Ruff checks.
- `tasks/history_exceptions.json` records only exact historical collisions and early
  record gaps. Do not rename immutable files to hide those exceptions or generalize
  the list to permit new collisions. Any deliberate resolution needs a scoped task
  with evidence and a corresponding exception update.
- New contracts should name the actual starting commit; reports record the baseline
  actually checked. The report's result commit is obtained with
  `git log -1 --format=%H -- tasks/reports/<report-file>` after committing, avoiding a
  self-referential commit hash. Earlier contracts and reports remain unchanged.
- Keep current file paths stable. Any later migration must explicitly include reference
  updates and acceptance checks. Research notes/probes require their own asset-ingestion
  scope; a navigation task does not implicitly promote them into the solver.

Directory responsibilities, actual solver entrypoints, code/process/lesson version
identities and environment guidance are in [development_layout.md](../docs/development_layout.md).
