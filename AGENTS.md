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

- Long-term phase plans belong under `tasks/phases/`.
- Issued Codex task prompts belong under `tasks/codex/`.
- Optional execution reports belong under `tasks/reports/`.
- Files under `tasks/codex/` are immutable after creation. Coding agents may read them, but must not edit, rename, delete, or move existing files under `tasks/codex/` unless the user explicitly asks for task-file maintenance.
- If a task needs revision, create a new `tasks/codex/YYYYMMDD-TT-RR_slug.md` file with an incremented revision number.
- If an execution report is needed, create it under `tasks/reports/` instead of modifying the issued task file.
- If the task naming or folder rules need to change, update `tasks/README.md` first or in the same commit.
