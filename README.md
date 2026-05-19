# SILO: Simplex and Integer Linear Optimization

A minimal solver kernel for learning LP simplex, MIP search, and extensible mathematical programming solver architecture.

## Project Philosophy

SILO starts from a deliberately small Python implementation. The goal is to make solver architecture readable before making it fast. Early phases prioritize clear mathematical conventions, deterministic behavior, and tests that explain the intended solver layers.

The project follows four principles:

- clarity before performance;
- reference implementation before industrial solver;
- Python-first, native-backend-ready;
- modular architecture from LP to MIP and decomposition.

## Current Scope

The current repository is a project scaffold. It defines the package layout, core model objects, canonicalization entry points, a placeholder tableau-simplex solver, a minimal command-line interface, examples, fixtures, and tests.

The next implementation phases will complete the model core, canonical form conversion, JSON input/output, tableau simplex, revised simplex, presolve, scaling, and branch-and-bound modules.

## Long-Term Roadmap

- Phase 1: Python modeling and canonical form
- Phase 2: tableau simplex
- Phase 3: revised simplex and basis handling
- Phase 4: presolve and scaling
- Phase 5: branch-and-bound for MIP
- Phase 6: cuts and callbacks
- Phase 7: stochastic and robust model transformations
- Phase 8: native backend

## Installation

Use an editable install for development:

```bash
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest
```

## CLI Placeholder

```bash
silo --help
```

The `solve` command is present only as a stable interface placeholder.

## License

SILO is distributed under the Apache License 2.0. See the existing `LICENSE` file for details.
