# Phase 0: Project Scaffold

## Goal

Establish the SILO repository as a lightweight Python package with a clear solver-oriented directory structure, documentation entry points, examples, fixtures, and smoke tests.

## Scope

This phase creates the package skeleton only. It should define stable module boundaries and placeholders, not full algorithms.

## Expected Files

- `pyproject.toml`
- `README.md`
- `ROADMAP.md`
- `AGENTS.md`
- `src/silo/`
- `tests/`
- `examples/`
- `notes/`
- `scripts/`

## Algorithmic Requirements

No full simplex, MIP, cut generation, decomposition, stochastic, or robust optimization implementation is required. Placeholder solver classes may return `SolverStatus.NOT_SOLVED`.

## Testing Requirements

Tests must verify imports, core model construction, duplicate-name validation, canonical-form placeholder output, tableau-simplex placeholder status, and CLI parser behavior.

## Do Not Do

Do not introduce large data, generated outputs, native code, external solver dependency, or premature performance-oriented abstractions.

## Acceptance Criteria

The project installs in editable mode, `pytest` passes, `silo --help` works after installation, and the Apache-2.0 `LICENSE` remains unchanged.
