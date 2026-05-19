# SILO Roadmap

## Phase 0: Project Scaffold

Goal: establish the repository layout, packaging configuration, documentation entry points, fixtures, examples, and initial tests.

Core modules: `src/silo/`, `tests/`, `examples/`, `notes/`, `tasks/`, and `scripts/`.

Expected tests: package import, core model construction, CLI parser, and placeholder solver behavior.

Acceptance criteria: editable installation works; `pytest` passes; `silo --help` works; the Apache-2.0 `LICENSE` remains intact.

## Phase 1: Model Core and Canonicalization

Goal: complete the user-facing model objects and convert simple linear models into a solver-ready canonical representation.

Core modules: `core`, `modeling`, and `io`.

Expected tests: expression building, variable and constraint validation, objective conventions, JSON reader, solution writer, and canonical form conversion.

Acceptance criteria: small LP examples can be built through the Python API and loaded from JSON with deterministic canonical output.

## Phase 2: Tableau Simplex

Goal: implement an educational tableau simplex solver for small continuous LPs.

Core modules: `lp.simplex.tableau`, `phase_one`, `phase_two`, `pivot`, `pricing`, and `ratio_test`.

Expected tests: known optimal LPs, infeasible LPs, unbounded LPs, degeneracy smoke cases, and deterministic pivot choices.

Acceptance criteria: the tableau solver returns correct statuses and objective values for small benchmark fixtures.

## Phase 3: Revised Simplex and Basis Reoptimization

Goal: introduce basis-oriented LP solving and prepare the LP layer for repeated solves in MIP and decomposition.

Core modules: `lp.simplex.basis`, revised simplex modules, and numerical utilities.

Expected tests: basis initialization, primal and dual feasibility checks, reduced costs, reoptimization after RHS changes, and comparison with tableau results.

Acceptance criteria: revised simplex solves the same small LPs as tableau simplex and exposes basis information.

## Phase 4: Presolve, Scaling, and Numerical Diagnostics

Goal: add safe preprocessing passes without hiding mathematical conventions.

Core modules: `presolve` and `utils.numerics`.

Expected tests: fixed-variable elimination, bound tightening, redundant row detection, reversible transformations, and scaling diagnostics.

Acceptance criteria: presolve transformations are deterministic, documented, and can reconstruct original-space solutions.

## Phase 5: MIP Branch-and-Bound

Goal: implement a minimal branch-and-bound layer over LP relaxation solves.

Core modules: `mip.branch_and_bound`, `node`, `tree`, `incumbent`, `branching`, and `node_selection`.

Expected tests: binary knapsack, small integer programs, infeasible MIPs, incumbent updates, and deterministic node selection.

Acceptance criteria: pure branch-and-bound solves small MIP fixtures without cuts or heuristics.

## Phase 6: Cut Generation and Callbacks

Goal: separate cut management from the MIP tree and define a conservative callback boundary.

Core modules: `cuts.separator`, `cuts.cut_pool`, and MIP callback integration points.

Expected tests: cut validity checks, duplicate cuts, cut-pool lifecycle, and no-regression tests for branch-and-bound.

Acceptance criteria: cut modules can be enabled experimentally without changing core model conventions.

## Phase 7: Decomposition Layer

Goal: add educational decomposition abstractions for master-subproblem methods.

Core modules: `decomposition.master`, `subproblem`, `benders`, and `column_generation`.

Expected tests: toy Benders examples, subproblem status handling, generated cuts or columns, and deterministic iteration logs.

Acceptance criteria: decomposition examples expose the algorithmic structure without pretending to be industrial implementations.

## Phase 8: Stochastic and Robust Optimization Extensions

Goal: represent uncertainty first as model transformation, not as a separate black-box solver.

Core modules: `uncertainty.scenario`, `stochastic_model`, `robust_model`, `uncertainty_set`, and `deterministic_equivalent`.

Expected tests: scenario expansion, deterministic equivalents, robust counterpart placeholders, and validation of uncertainty sets.

Acceptance criteria: small stochastic and robust examples can be transformed into ordinary model objects.

## Phase 9: Native Backend

Goal: prepare selected solver kernels for a future native implementation while preserving Python reference behavior.

Core modules: `native/`, backend interfaces, and conformance tests.

Expected tests: Python/native parity tests, backend selection, and failure-mode diagnostics.

Acceptance criteria: native work remains optional and does not complicate the Python reference solver.
