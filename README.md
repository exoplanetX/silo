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

- Phase 0: Project scaffold
- Phase 1: Model core and canonicalization
- Phase 2: Tableau simplex
- Phase 3: Revised simplex and basis reoptimization
- Phase 4: Presolve, scaling, and numerical diagnostics
- Phase 5: MIP branch-and-bound
- Phase 6: Cut generation and callbacks
- Phase 7: Decomposition layer
- Phase 8: Stochastic and robust optimization extensions
- Phase 9: Native backend

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
