# Contributing

SILO is a reference solver project. Contributions should make the mathematical structure clearer, better tested, or easier to extend.

## Development Setup

Install the package in editable mode with development dependencies:

```bash
pip install -e ".[dev]"
```

## Before Committing

Run the test suite:

```bash
pytest
```

For local quality checks, use:

```bash
python scripts/check_quality.py
```

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

## Tests

Add small deterministic tests for new algorithms. Prefer known-solution instances and clear status expectations over large benchmark data.

## Generated Files

Do not commit generated outputs, caches, virtual environments, or large datasets. Keep examples and fixtures lightweight.
