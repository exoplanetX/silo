# SILO Development Rules for AI Coding Agents

1. Keep the dependency direction clean:
   core <- modeling <- presolve <- lp <- mip <- cuts/decomposition/uncertainty

2. The `core` package must not depend on LP, MIP, cuts, decomposition, or uncertainty modules.

3. Native algorithms must not call external solvers.

4. External solvers may only be used in `interfaces/`, examples, or tests for comparison.

5. Prefer clarity, correctness, and deterministic tests over performance in early phases.

6. Do not introduce large datasets, generated outputs, or binary files into git.

7. Every algorithmic module must include small deterministic tests.

8. Keep public APIs minimal and documented.

9. Do not silently change mathematical conventions. Record conventions in notes and docs.

10. Avoid premature optimization. First implement a readable reference version.

## Task Management Rules

- `tasks/README.md` is the source of truth for task directory rules and the SILO Development Operating System (SILO-DOS). AI coding agents must read `tasks/README.md` before issuing or executing task files.
- Long-term development knowledge belongs under `tasks/phases/`.
- Issued Codex task contracts belong under `tasks/codex/`.
- Execution memory belongs under `tasks/reports/`.
- Files under `tasks/codex/` are immutable after creation. Coding agents may read them, but must not edit, rename, delete, or move existing files under `tasks/codex/` unless the user explicitly asks for task-file maintenance.
- Each Codex task must be atomic and solve exactly one primary problem.
- Each task must obey its scope lock, allowed changes, forbidden changes, stop conditions, required checks, acceptance criteria, expected report path, and Git mode.
- Codex must stop after one atomic task. It must not automatically continue to the next task, enter a new phase, or expand task scope without explicit user instruction.
- Default Git mode is `local-commit` unless the issued task states otherwise.
- Codex must not push to GitHub unless the task Git mode is `push-on-success`, the task is `sync-only`, or the user explicitly requests a push.
- Push failure is non-fatal. If push fails, Codex must preserve the local commit and record the failure in the execution report.
- If Codex discovers a broader issue, it should document the issue in the report instead of fixing it inside the current task.
- If a task needs revision, create a new `tasks/codex/YYYYMMDD-TT-RR_slug.md` file with an incremented revision number.
- Before creating a new task file, Codex must scan existing `tasks/codex/` and `tasks/reports/` filenames for the same date. It must not reuse an existing `YYYYMMDD-TT-RR` prefix for a different slug.
- Use `RR` only for revisions of the same task block. Use the next available `TT` for a new unrelated task on the same date.
- Treat historical task ID collisions as reportable task-system debt, not as permission to rename immutable task files.
- If the task naming, folder rules, or SILO-DOS rules need to change, update `tasks/README.md` first or in the same commit.
- Responsibility boundary: the user sets priorities and approves scope; ChatGPT or the user may design phase strategy and approve phase transitions; Codex executes one issued task at a time from local repository rules; GitHub stores synchronized commits and remote collaboration state, but is not the source of task interpretation.
