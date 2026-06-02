# Phase 8: Stochastic and Robust Optimization Extensions

## Goal

Represent stochastic and robust optimization models as explicit transformations into deterministic model objects.

Phase 8A records the uncertainty boundary design in `notes/20_uncertainty_boundary_design.md`; it is planning-only and includes no implementation.

Phase 8B adds immutable finite-scenario records and validation tests for ids, probabilities, metadata, override data, and deterministic ordering; it does not implement stochastic wrappers, robust wrappers, uncertainty sets, deterministic equivalents, examples, CLI behavior, or JSON schemas.

Phase 8C adds uncertainty boundary smoke tests for public exports, lower-layer dependency direction, solver-layer imports, CLI exposure, and `Solution` schema separation; it does not implement new uncertainty behavior.

Phase 8D adds immutable stochastic model wrapper records for a validated base model, finite scenario collection, first-stage declarations, and scenario-dependent declarations; it does not build deterministic equivalents, robust wrappers, uncertainty sets, examples, CLI behavior, or JSON schemas.

Phase 8E adds deterministic naming-convention helpers for scenario variables, scenario constraints, and nonanticipativity constraints; it does not build deterministic equivalents, expose new public package exports, or change solver/CLI/schema behavior.

Phase 8F adds immutable deterministic-equivalent diagnostic/result records for scenario ids, generated dimensions, probability metadata, objective aggregation convention, naming convention, and result pairing; it does not construct deterministic-equivalent models or change the placeholder builder behavior.

Phase 8G adds a tiny deterministic-equivalent builder path for continuous LP fixtures with objective and RHS overrides only; it rejects scenario-dependent variables, does not generate nonanticipativity constraints, does not call solvers, and does not change CLI or JSON schemas.

Phase 8H adds immutable interval and box uncertainty-set records with validation tests for targets, bounds, nominal values, deterministic ordering, metadata, and package-boundary isolation; it does not implement robust model wrappers or robust counterpart transformations.

Phase 8I adds immutable robust model wrapper records that pair a validated base model with an uncertainty set and assumption metadata; it does not implement robust counterpart transformations, solver calls, CLI behavior, or JSON schemas.

Phase 8J adds a toy robust counterpart transformation for interval RHS uncertainty on continuous LP fixtures; it supports only documented RHS worst-case conventions, does not call solvers, does not expose public CLI or JSON schema behavior, and does not close Phase 8.

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
