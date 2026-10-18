# Contributing

SILO is a reference solver project. Contributions should make the mathematical structure clearer, better tested, or easier to extend.

## Development Setup

Install the package in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

## Before Committing

After adding task contracts/reports, refresh the derived navigation and run its check:

```bash
python scripts/check_project_structure.py --write-index
python scripts/check_project_structure.py
```

Start development from the [current project snapshot](.silo-dos/project_profile.md).
Use the [task index](tasks/INDEX.md) for history and the
[directory/entrypoint map](docs/development_layout.md) for implementation ownership.

For executable changes, run the relevant tests and required full quality checks:

```bash
pytest
```

For local quality checks, use:

```bash
python scripts/check_quality.py
```

For documentation-only changes, validate affected local links, mathematical examples,
metadata and scope. Execute any new/changed runnable examples. A full solver rerun is
needed when executable behavior changes or an issued task explicitly requires it.

## Development Companion Learning

For work on models, algorithms, mathematical conventions, numerical handling or
correctness fixes, create or update a lesson under [learning/](learning/README.md).
Use the [writing guide](learning/WRITING_GUIDE.md) and [template](learning/templates/lesson.md).
Include a hand-worked example, derivation, code/test mapping, research significance,
limitations and appropriate exercises with solutions. Keep stable lesson IDs and
record the code baseline actually verified; update the catalog when adding a lesson.

Declare the learning delivery path in the task contract and link the delivered lesson
and actual checks from its report. Existing lessons may accumulate multiple tasks.
Pure synchronization, formatting or organization work can record why no new teaching
body is needed. Do not duplicate complete lessons in API docs or rewrite historical
contracts to add the new requirement. Detailed task rules remain in `tasks/README.md`.

## AI/Codex-Assisted Development

AI-assisted development must follow the repository task system.

- `tasks/README.md` is the source of truth for task directory rules and SILO-DOS.
- `AGENTS.md` defines agent-facing solver and workflow rules.
- Long-term phase plans belong under `tasks/phases/`.
- Issued Codex task contracts belong under `tasks/codex/`.
- Execution reports belong under `tasks/reports/`.
- Codex tasks should be atomic, scope-locked, and executed one at a time.
- Do not modify existing issued task files unless the user explicitly requests task-file maintenance.
- Pushes to GitHub should follow the task-declared Git mode or explicit user instruction.

## Module Boundaries

Keep dependencies aligned with the project layering:

```text
core <- modeling <- presolve <- lp <- mip <- cuts/decomposition/uncertainty
```

The `core` package must remain independent of solver implementations. External solver integrations belong only in `interfaces/`, examples, or comparison tests.

The chain above describes development progression. The existing MIP driver imports
passive cut/callback interfaces; cuts stays independent of MIP. See the directory map
for actual import directions and the current placeholder modules.

## Tests

Add small deterministic tests for new algorithms. Prefer known-solution instances and clear status expectations over large benchmark data.

## Generated Files

Do not commit generated outputs, caches, virtual environments, or large datasets. Keep examples and fixtures lightweight.
