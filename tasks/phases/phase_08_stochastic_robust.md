# Phase 8: Stochastic and Robust Optimization Extensions

## Goal

Represent stochastic and robust optimization models as explicit transformations into deterministic model objects.

Phase 8A records the uncertainty boundary design in `notes/20_uncertainty_boundary_design.md`; it is planning-only and includes no implementation.

Phase 8B adds immutable finite-scenario records and validation tests for ids, probabilities, metadata, override data, and deterministic ordering; it does not implement stochastic wrappers, robust wrappers, uncertainty sets, deterministic equivalents, examples, CLI behavior, or JSON schemas.

## Scope

This phase covers scenario data, stochastic model wrappers, robust model wrappers, uncertainty sets, deterministic equivalents, and small transformation examples.

## Expected Files

- `src/silo/uncertainty/scenario.py`
- `src/silo/uncertainty/stochastic_model.py`
- `src/silo/uncertainty/robust_model.py`
- `src/silo/uncertainty/uncertainty_set.py`
- `src/silo/uncertainty/deterministic_equivalent.py`
- `tests/unit/test_uncertainty.py`

## Algorithmic Requirements

Start with finite-scenario deterministic equivalents. Clearly represent scenario probabilities, replicated variables, and nonanticipativity constraints. Robust counterparts should be implemented only for simple uncertainty sets with documented assumptions.

## Testing Requirements

Add tests for scenario validation, probability checks, deterministic equivalent dimensions, variable naming conventions, and simple robust counterpart construction.

## Do Not Do

Do not create a separate stochastic solver. Do not implement advanced distributionally robust or chance-constrained models without a clear mathematical specification.

## Acceptance Criteria

Small stochastic and robust examples can be transformed into ordinary SILO models and inspected through canonical form.
