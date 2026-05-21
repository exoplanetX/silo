# SILO: Simplex and Integer Linear Optimization

SILO is a Python-first educational optimization solver kernel for small LPs. It currently includes dense tableau simplex and revised simplex backends, JSON model input, CLI solve and compare workflows, and a conservative presolve/scaling diagnostics layer.

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
- Dense tableau simplex solver with Phase I / Phase II.
- Basis-oriented revised simplex solver with Phase I / Phase II.
- Phase I / Phase II support for `<=`, `>=`, and `=` rows.
- Infeasible and unbounded LP status detection.
- CLI solve workflow for JSON LP files.
- Backend selection through `--solver tableau` and `--solver revised`.
- Backend comparison through `silo compare`.
- CLI presolve diagnostics for inspecting presolve and scaling without solving.
- Optional solve-time presolve through `silo solve --presolve`.
- Conservative presolve with empty-row diagnostics/removal, empty-column diagnostics, fixed-variable elimination, repeated-pass reductions, original-space slack recovery, and coefficient-range scaling diagnostics.
- Python API branch-and-bound for small binary and bounded nonnegative integer MIPs.
- Solution JSON output with primal values, slacks, reduced costs, and basis status.

The native solver path does not call external solvers.

## Current Limitations

- CLI solve workflows are continuous LP only.
- Maximization models only.
- Variables must have lower bound `0`.
- Native LP backends do not support finite variable upper bounds directly.
- MIP support is Python API only; no MIP CLI yet.
- No cuts, heuristics, callbacks, or branch-and-cut yet.
- Presolve is not enabled by default; solve-time presolve is opt-in.
- No automatic scaling yet.
- No dual values exposed yet.
- No external solver backend is used by native algorithms.
- No industrial performance claims.

## Long-Term Roadmap

- Phase 0: Project scaffold
- Phase 1: Model core and canonicalization
- Phase 2: Tableau simplex
- Phase 3: Revised simplex and basis reoptimization
- Phase 4: Presolve, scaling, and numerical diagnostics
- Phase 5: MIP branch-and-bound design and implementation
- Phase 6: Cut generation and callbacks
- Phase 7: Decomposition layer
- Phase 8: Stochastic and robust optimization extensions
- Phase 9: Native backend

Phase 5 starts from the branch-and-bound design note in [notes/15_branch_and_bound_design.md](notes/15_branch_and_bound_design.md) before MIP implementation. MIP CLI exposure is being designed separately in [notes/16_mip_cli_exposure_design.md](notes/16_mip_cli_exposure_design.md); no MIP CLI command is implemented yet.

## Installation

Use an editable install for development:

```bash
pip install -e ".[dev]"
```

## Quick Start

Run the core development and CLI smoke commands:

```bash
pip install -e ".[dev]"
pytest
silo solve examples/json/production.json
silo solve examples/json/production.json --solver revised
silo compare examples/json/production.json
silo presolve examples/json/production.json
silo solve examples/json/fixed_var_recovery.json --presolve
```

Write the same solution JSON to an ignored local output file:

```bash
silo solve examples/json/production.json --output outputs/production_solution.json
```

Presolve recovery examples are available under `examples/json/`, including fixed-variable and repeated-pass cases.

See [Phase 4 regression checklist](docs/phase4_regression_checklist.md) for the current solve, presolve, and compare behavior matrix.

MIP examples are available under `examples/mip/` and can be run through the Python `BranchAndBoundSolver` API.

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
- [MIP JSON examples](docs/mip_examples.md)
- [MIP CLI exposure design](notes/16_mip_cli_exposure_design.md)
- [Phase 4 regression checklist](docs/phase4_regression_checklist.md)
- [LP solver scope](docs/lp_solver.md)

## License

SILO is distributed under the Apache License 2.0. See the existing `LICENSE` file for details.
