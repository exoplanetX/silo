# SILO: Simplex and Integer Linear Optimization

SILO is a Python-first educational optimization solver kernel that currently supports small continuous LPs through dense tableau simplex and revised simplex implementations, plus a JSON-based CLI solve workflow.

## Project Philosophy

SILO starts from a deliberately small Python implementation. The goal is to make solver architecture readable before making it fast. Early phases prioritize clear mathematical conventions, deterministic behavior, and tests that explain the intended solver layers.

The project follows four principles:

- clarity before performance;
- reference implementation before industrial solver;
- Python-first, native-backend-ready;
- modular architecture from LP to MIP and decomposition.

## Current Scope

The current repository contains a working educational LP path:

- Python model objects for LP/MIP-style model representation.
- JSON model reader.
- Dense tableau simplex solver.
- Basis-oriented revised simplex solver.
- Phase I / Phase II support for `<=`, `>=`, and `=` rows.
- Infeasible and unbounded LP status detection.
- CLI solve workflow for JSON LP files.
- CLI presolve diagnostics for inspecting presolve and scaling without solving.
- Solution JSON output with primal values, slacks, reduced costs, and basis status.

The native solver path does not call external solvers.

## Current Limitations

- Continuous LPs only.
- Maximization models only.
- Variables must have lower bound `0`.
- Finite variable upper bounds are not supported yet.
- Integer and binary variables are not solved yet.
- No MIP branch-and-bound yet.
- Presolve is diagnostic-only and is not connected to `silo solve` by default.
- No automatic scaling yet.
- No external solver backend is used by native algorithms.

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

## Quick Start

Solve the production LP example and print deterministic solution JSON:

```bash
silo solve examples/json/production.json
```

Write the same solution JSON to an ignored local output file:

```bash
silo solve examples/json/production.json --output outputs/production_solution.json
```

Select the revised simplex backend explicitly:

```bash
silo solve examples/json/production.json --solver revised
```

Compare the tableau and revised native backends on the same JSON model:

```bash
silo compare examples/json/production.json
```

Inspect presolve and scaling diagnostics without solving the model:

```bash
silo presolve examples/json/production.json
```

Run conservative presolve before solving only when explicitly requested:

```bash
silo solve examples/json/production.json --presolve
```

Presolve recovery examples are available under `examples/json/`, including fixed-variable and repeated-pass cases.

The `outputs/` directory is for local runs and generated files there should not be committed.

## Running Tests

```bash
pytest
```

## Documentation

- [JSON model format](docs/json_model_format.md)
- [CLI solve usage](docs/cli_solve.md)
- [Presolve diagnostics CLI](docs/presolve_cli.md)
- [Backend compare command](docs/backend_compare.md)
- [LP solver scope](docs/lp_solver.md)

## License

SILO is distributed under the Apache License 2.0. See the existing `LICENSE` file for details.
