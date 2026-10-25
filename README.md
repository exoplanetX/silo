# SILO: Simplex and Integer Linear Optimization

SILO is a Python/NumPy teaching and research prototype for general-form LP and
MILP, with a dense reference engine and an optional sparse LP engine. The local
candidate is **0.3.0a1**. Use `silo.solve()` or
`silo optimize` for the general model pipeline. Local validation and artifact
identities, fixed-run evidence and final acceptance are recorded in the
[sparse program report](tasks/reports/20261024-02-02_sparse-lp-program_report.md).

## Project Philosophy

SILO starts from a deliberately small Python implementation. The goal is to make solver architecture readable before making it fast. Early phases prioritize clear mathematical conventions, deterministic behavior, and tests that explain the intended solver layers.

The project follows four principles:

- clarity before performance;
- reference implementation before industrial solver;
- Python-first, native-backend-ready;
- modular architecture from LP to MIP and decomposition.

## Current Scope

The unified pipeline supports min/max with objective constants, row intervals and
equalities, free/fixed/upper-only variables, negative bounds and continuous,
integer or binary domains. It includes:

- Strict JSON and documented free-MPS input/output.
- Reversible normalization, activity propagation, integer bound rounding and real scaling.
- Native Phase I/II revised primal/dual simplex, dense QR or sparse LU/eta factors,
  and public LP reoptimization with RHS, bounds, row and column edits.
- Original-space primal/KKT checks and exact binary-rational infeasibility/ray evidence.
- Deterministic branch-and-cut, global bounds/gaps, limits, heuristics and verified local GMI cuts.
- Read-only research callbacks and general finite-pool CG with explicit feasibility recovery.
- Optional sparse CSC/LU support through SciPy; optional SciPy/HiGHS optimizer
  comparisons remain isolated in `interfaces/`.

The older tableau/revised classes and `solve`/`mip-solve` CLI commands retain their
documented standard-form domains. Their limits do not define `optimize`'s domain.

The native solver path does not call external solvers.

## Current Limitations

- Dense is the default engine and retains its conservative allocation gate.
  Select sparse explicitly with `SolveOptions(lp_engine="sparse")` or
  `silo optimize model.json --lp-engine sparse`.
- The fixed sparse validation includes up to 2000 variables, 5000 rows and 100000
  nonzeros, plus 12 Netlib LPs. These finite cohorts establish the measured scope;
  actual outcomes and timings belong to the program report. MILP remains a small-instance prototype.
- RR08 binds the existing warm4 five-repeat run: 80 children, 1680 saved solutions,
  median edit-segment speed ratio 3.503361 and 8/8 nonregressing trajectories.
  Same-source warm3/5 each had five cold timeouts; warm4 lacks its auxiliary host trace.
  This records one fixed run and does not establish stability across runs or a unique host cause.
- Sparse factor fill, eta updates, exact proof work, iterations and wall time have
  explicit limits. An unresolved numerical case can return `numerical_failure`.
- Finite pricing pools only for the general CG reference; arbitrary external cut expressions,
  full branch-and-price/Benders, QP/conic/nonlinear models and parallel search remain outside this candidate.
- Exact proof budgets can conservatively skip cuts or retain an unresolved result.
- Research callbacks run cooperatively in the caller process and must return promptly.
- Windows 3.11/3.13 local artifact checks and remote CI have separate validation states.
- Original pricing research remains A/B accepted, C HOLD, D/E not started.

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

Phase 5 starts from the branch-and-bound design note in [notes/15_branch_and_bound_design.md](notes/15_branch_and_bound_design.md) before MIP implementation. MIP CLI exposure follows the design in [notes/16_mip_cli_exposure_design.md](notes/16_mip_cli_exposure_design.md).

## Installation

Use an editable install for development:

```bash
pip install -e ".[dev]"
```

For a normal installation, install a specific locally built wheel with
`python -m pip install /absolute/path/to/silo_solver-0.3.0a1-py3-none-any.whl`.
The dense engine requires NumPy only. Sparse support requires Python 3.11 or newer
and the `sparse` extra, which pins SciPy 1.16.3:

```bash
pip install "silo-solver[sparse] @ file:///absolute/path/to/silo_solver-0.3.0a1-py3-none-any.whl"
```

Use an actual artifact path and the platform's file-URL syntax.
Build, isolated wheel/sdist checks and actual platform status are documented in
[installation](docs/installation.md). No public package upload is implied.

## Quick Start

Run the general pipeline and public research examples:

```bash
silo optimize examples/json/production.json
python -m silo optimize examples/json/production.json --lp-engine sparse
python -m silo optimize model.mps --time-limit 20 --node-limit 100000
python -c "from silo.mip.research_example import run_example; print(run_example())"
python -c "from silo.decomposition.general_master import covering_example; print(covering_example().to_dict())"
```

Use the original standard-form workflows for compatibility examples:

```bash
pip install -e ".[dev]"
pytest
silo solve examples/json/production.json
silo solve examples/json/production.json --solver revised
silo compare examples/json/production.json
silo presolve examples/json/production.json
silo solve examples/json/fixed_var_recovery.json --presolve
silo mip-solve examples/mip/binary_knapsack.json
```

Write the same solution JSON to an ignored local output file:

```bash
silo solve examples/json/production.json --output outputs/production_solution.json
```

Presolve recovery examples are available under `examples/json/`, including fixed-variable and repeated-pass cases.

See [Phase 4 regression checklist](docs/phase4_regression_checklist.md) for the current solve, presolve, and compare behavior matrix.

MIP examples are available under `examples/mip/` and can be run through `silo mip-solve` or the Python `BranchAndBoundSolver` API.

The `outputs/` directory is for local runs and generated files there should not be committed.

## Running Tests

```bash
pytest
```

## Documentation

For development management, start with the [current project snapshot](.silo-dos/project_profile.md),
the [task/report index](tasks/INDEX.md), and the [directory and code entrypoints](docs/development_layout.md).
Preserved pricing research notes and bounded reference probes are indexed in the
[research asset guide](scripts/research/pricing/README.md); they remain outside the solver API.

Start with [development companion learning](learning/README.md) for mathematical
explanations, worked examples, research connections, limitations and exercises.
The first lesson is [L0001: LP duality and optimality verification](learning/lessons/L0001-lp-duality/README.md).
Current API semantics remain in [LP dual reference](docs/lp_duality.md).

| Directory | Purpose |
|---|---|
| `src/`, `tests/`, `examples/` | Solver implementation, deterministic tests and runnable examples |
| [learning/](learning/README.md) | Stable lessons, thematic/chronological catalog, exercises and answers |
| [docs/](docs/README.md) | Current usage, API contracts and solver scope |
| [notes/](notes/README.md) | Design/research exploration and historical decisions |
| [tasks/](tasks/README.md) | Phase plans, immutable task contracts and execution reports |
| `.silo-dos/` | Local project status and development operating rules |

Lesson IDs remain stable while thematic reading order can evolve into a future
course or book. Mathematical development tasks create or update a companion lesson;
see [contribution requirements](CONTRIBUTING.md).

- [JSON model format](docs/json_model_format.md)
- [CLI solve usage](docs/cli_solve.md)
- [Presolve diagnostics CLI](docs/presolve_cli.md)
- [Backend compare command](docs/backend_compare.md)
- [MIP JSON examples](docs/mip_examples.md)
- [MIP solve CLI](docs/mip_solve_cli.md)
- [MIP CLI exposure design](notes/16_mip_cli_exposure_design.md)
- [Phase 4 regression checklist](docs/phase4_regression_checklist.md)
- [LP solver scope](docs/lp_solver.md)

## License

SILO is distributed under the Apache License 2.0. See the existing `LICENSE` file for details.
