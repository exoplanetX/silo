# Phase 2: Model Core

## Goal

Complete the modeling layer needed to express small linear and mixed-integer models through both Python API and JSON files.

## Scope

This phase should complete the expression system, model validation, canonical form, JSON reader, solution writer, and tests for LP examples.

## Expected Files

- `src/silo/core/model.py`
- `src/silo/core/variable.py`
- `src/silo/core/constraint.py`
- `src/silo/core/objective.py`
- `src/silo/modeling/expressions.py`
- `src/silo/modeling/builder.py`
- `src/silo/modeling/canonical_form.py`
- `src/silo/io/json_reader.py`
- `src/silo/io/solution_writer.py`
- `tests/unit/test_model.py`
- `tests/unit/test_canonical_form.py`

## Algorithmic Requirements

Support linear expressions with deterministic coefficient aggregation. Validate duplicate names, unknown variables in constraints or objectives, invalid bounds, invalid binary bounds, and inconsistent objective conventions. Canonical form should preserve model order and clearly document minimization and maximization conventions.

## Testing Requirements

Add tests for expression arithmetic, model validation errors, JSON round-trip loading, objective sense handling, equality and inequality constraints, and solution writer output.

## Do Not Do

Do not implement simplex inside the modeling layer. Do not let `core` depend on LP, MIP, cuts, decomposition, or uncertainty modules.

## Acceptance Criteria

Small LP examples can be built through the API, loaded from JSON, converted to canonical form, and checked by deterministic tests.
