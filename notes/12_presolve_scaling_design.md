# Presolve and Scaling Design Note

## 1. Purpose

Presolve and scaling are the next natural layer after the tableau and revised simplex paths. SILO now has two native LP backends, JSON model input, deterministic solution JSON, backend comparison, backend regression tests, and a conservative revised simplex warm-start interface. These components make LP solving visible and testable. Phase 4 should improve the quality of the model that reaches those solvers without hiding how the model changed.

Presolve in SILO should not be treated only as a performance trick. It should serve five purposes. First, it should simplify models when the simplification is mathematically transparent. Second, it should detect simple infeasibility or unboundedness before simplex starts. Third, it should produce numerical diagnostics that warn users and future developers about poorly scaled inputs. Fourth, it should prepare for future MIP and decomposition layers, where repeated LP solves make preprocessing and reconstruction important. Fifth, it should establish a traceable transformation record so every solver-space result can be mapped back to the original model.

The first Phase 4 implementation should therefore be conservative. The goal is not to reduce every possible model. The goal is to define safe transformations, record them explicitly, and preserve original-space solution semantics.

## 2. Current Solver Boundary

The current solver boundary is intentionally narrow. SILO supports small continuous maximization LPs with nonnegative variables. Rows may be `<=`, `>=`, or `=`, and both native LP backends use Phase I / Phase II logic. The tableau backend is the educational dense reference path. The revised backend is the basis-oriented path used for warm starts and future reoptimization. JSON input is available, `silo solve` can choose either backend, and `silo compare` can compare tableau and revised outputs on the same JSON model.

Several features remain unsupported by the solvers: minimization, finite variable upper bounds, nonzero lower bounds, integer and binary variables, presolve, scaling transformations, MIP, and dual values. The model layer can represent some concepts that the solvers do not yet support, such as finite upper bounds or binary variables. Early presolve must respect the solver boundary rather than silently expanding it.

This means Phase 4 should not transform unsupported models into apparently supported models unless the transformation is fully recorded and the public solution can be reconstructed. For example, substituting a fixed variable with `lower == upper` is plausible, but bound shifting for a general nonzero lower bound would change solver conventions and should wait.

## 3. Presolve Philosophy

The first presolve layer should be deterministic, local, readable, and reversible enough for original-space reconstruction. A reduction rule should be skipped if its conditions are unclear, if its effect cannot be explained in a small test, or if its recovery logic is not obvious.

Each presolve pass should satisfy four constraints. It must preserve the mathematical status of the original model. It must record enough information to recover original variables, objective constants, and constraint diagnostics. It must avoid changing public conventions for slacks, reduced costs, status, and solution fields. It must have deterministic output independent of dictionary order or incidental traversal details.

Aggressive reductions are intentionally out of scope. General redundancy detection, row aggregation, dominance rules, probing, and dual reductions can be powerful, but they are hard to explain and test early. SILO should first implement a small set of reductions that make the architecture trustworthy. Traceability is more important than shrinking the model.

## 4. Transformation Traceability

Presolve should eventually return a structured object rather than only a transformed model. A useful conceptual shape is:

```python
@dataclass(frozen=True)
class PresolveResult:
    model: Model
    reductions: tuple[Reduction, ...]
    diagnostics: PresolveDiagnostics
```

Each `Reduction` should describe one transformation and know how to recover the relevant part of an original-space solution. Conceptually:

```python
class Reduction:
    def apply(...): ...
    def recover_solution(...): ...
```

This note does not implement these classes. The design intent is that a reduction log is ordered, immutable, and replayable in reverse. If presolve fixes a variable, the reduction records the variable name, fixed value, objective contribution, and coefficient contributions moved into row right-hand sides. If presolve removes a redundant empty row, the reduction records the row name and why it is satisfied. If presolve detects infeasibility, the result records a diagnostic status without invoking a solver.

The transformation log should also support diagnostics that do not change the model. Coefficient range warnings, duplicate row warnings, near-zero coefficient warnings, and singleton-row observations may be recorded without producing a new solver-space model.

## 5. First Presolve Passes

The first safe passes should be small and test-driven.

Empty row detection should inspect rows with no nonzero coefficients. A row `0 <= rhs` is feasible if `rhs >= 0`; `0 = rhs` is feasible only when `rhs` is numerically zero; `0 >= rhs` is feasible if `rhs <= 0`. Infeasible cases include `0 <= -1`, `0 = 1`, and `0 >= 1`. Feasible empty rows can be removed with a reduction record that marks the original row as redundant. Infeasible empty rows should stop presolve and return an infeasibility diagnostic before simplex.

Empty column detection should inspect variables that appear in no constraints. In the current solver boundary, variables are nonnegative and have no finite upper bound. If an empty column has a positive objective coefficient in a maximization model, the model is unbounded. If its objective coefficient is zero or negative, the variable can be set to zero for an optimum, but removing it requires recording a value for reconstruction. Because future bounds and minimization will complicate this rule, the first implementation may report empty-column diagnostics before removing variables.

Fixed variable substitution is a natural first true transformation. If a variable has `lower == upper`, its value can be substituted into all constraints and the objective. The reduction must record the fixed value, objective constant adjustment, and original variable name. Solution reconstruction restores the fixed variable value. Current simplex solvers do not broadly support nonzero lower bounds, so this reduction should be introduced carefully and tested before being enabled in the default solve path.

Simple bound validation should detect contradictory bounds where the model layer allows them. It should not attempt general bound-shift transformations yet.

Singleton-row bound tightening should initially be diagnostic or limited. A row `a x <= b` with `a > 0` and `x >= 0` implies an upper bound on `x`. Since finite upper bounds are not yet supported by simplex, this observation should not be turned into a solver-facing finite upper bound unless the solver scope changes. It can still be reported as a diagnostic and used later.

Duplicate row detection should start as a warning. Exact duplicate rows can suggest redundancy, but sense, RHS, and numerical tolerance make safe removal less trivial than it first appears. Phase 4 should record duplicates rather than remove them initially.

Coefficient range diagnostics should compute the maximum absolute coefficient, minimum nonzero absolute coefficient, and ratio. They should include constraint matrix coefficients, RHS values, and objective coefficients separately when possible.

## 6. Solution Reconstruction

Public `Solution` objects must stay in original model space. Presolve should not expose transformed variable names or removed-row artifacts to users. If a solver runs on a presolved model, recovery should reconstruct:

- fixed variable values;
- values of variables removed as harmless empty columns;
- objective constants introduced during substitution;
- original-space slack values computed from original constraints;
- original constraint diagnostics for removed redundant rows;
- status explanations for presolve-detected infeasibility or unboundedness.

Slack values should continue to be computed from original constraints using the existing conventions: `rhs - activity` for `<=`, `activity - rhs` for `>=`, and `rhs - activity` for equality residuals. This is safer than trying to carry transformed slacks back through each reduction.

Objective reconstruction should be tested explicitly. If a fixed variable contributes `c_j v` to the objective, that contribution must be preserved in the final original objective value. A recovery check should recompute the original objective from reconstructed primal values and compare it against the reported objective.

## 7. Scaling Diagnostics

Scaling should begin as diagnostics only. Automatic scaling changes the relationship between solver-space and original-space primal values, dual values, reduced costs, feasibility residuals, and objective values. Because SILO does not yet expose dual values and is still establishing its transformation architecture, automatic scaling would create unnecessary risk.

A first diagnostic object might be:

```python
@dataclass(frozen=True)
class ScalingDiagnostics:
    max_abs_coefficient: float
    min_abs_nonzero_coefficient: float | None
    coefficient_ratio: float | None
    warnings: tuple[str, ...]
```

Useful warnings include very large coefficient ratios, near-zero coefficients that are not exactly zero, large RHS values, and large objective coefficient ranges. Diagnostics should be deterministic and should name the affected rows or variables when feasible.

Later, automatic scaling can be considered only after the transformation log supports primal reconstruction, objective reconstruction, reduced-cost interpretation, and dual-value rescaling.

## 8. Numerical Diagnostics

The current dense solvers would benefit from lightweight numerical diagnostics. Phase 4 should start with diagnostics that can be computed cheaply and explained clearly:

- coefficient range and RHS range;
- objective coefficient range;
- near-zero pivot warnings;
- iteration-limit status;
- primal feasibility residual after solve;
- constraint activity residual in original space;
- objective reconstruction residual;
- a simple basis condition proxy for revised simplex, if available through dense NumPy operations.

Exact condition-number tracking is not required in the first implementation. If a condition proxy is added later, it should be optional and reported as a diagnostic, not as a hard failure unless the linear solve actually fails.

## 9. Module Layout

Future Phase 4 files should keep presolve separate from core modeling and LP algorithms:

```text
src/silo/presolve/presolver.py
src/silo/presolve/reductions.py
src/silo/presolve/fixed_variable.py
src/silo/presolve/row_reduction.py
src/silo/presolve/bound_tightening.py
src/silo/presolve/scaling.py
src/silo/presolve/diagnostics.py
tests/unit/test_presolve.py
tests/unit/test_scaling_diagnostics.py
```

`presolver.py` should orchestrate passes and return `PresolveResult`. `reductions.py` should define reduction records and recovery interfaces. `fixed_variable.py` should handle fixed-variable substitution. `row_reduction.py` should handle empty rows and simple row diagnostics. `bound_tightening.py` should hold singleton-row observations and future bound logic. `scaling.py` should compute coefficient and RHS diagnostics. `diagnostics.py` should define immutable diagnostic dataclasses.

The LP solvers should not import presolve directly at first. A higher-level solve wrapper or CLI flag can later decide whether to run presolve before calling tableau or revised simplex.

## 10. Testing Strategy

Future tests should include:

- no-op presolve leaves a supported LP unchanged;
- feasible empty row removal for `<=`, `>=`, and `=`;
- infeasible empty row detection;
- fixed variable substitution in constraints;
- objective constant update after fixed variable substitution;
- solution reconstruction after fixed variable elimination;
- original-space slack values after reconstruction;
- empty-column diagnostics for zero, negative, and positive objective coefficients;
- singleton-row diagnostics without unsupported finite-bound injection;
- coefficient range diagnostics;
- near-zero coefficient diagnostics;
- deterministic order of reductions and warnings;
- tableau and revised comparison still works after presolve is optionally enabled later.

Tests should verify both transformed model content and recovered solution content. A transformation is not complete until its reverse mapping is tested.

## 11. Implementation Phases

Phase 4 should be split into small tasks:

```text
Phase 4A: presolve and scaling design note
Phase 4B: PresolveResult and diagnostics dataclasses
Phase 4C: empty-row and empty-column diagnostics
Phase 4D: fixed-variable elimination with solution reconstruction
Phase 4E: coefficient-range and scaling diagnostics
Phase 4F: optional CLI flag for presolve diagnostics
```

Phase 4B should avoid changing solver behavior. Phase 4C can introduce safe early infeasibility and unboundedness diagnostics behind explicit tests. Phase 4D should be the first transformation that changes a model and therefore must include recovery tests. Phase 4E should keep scaling diagnostic-only. Phase 4F can expose diagnostics through CLI only after the internal APIs are stable.

## 12. Out of Scope for the First Implementation

The first implementation should not include aggressive row aggregation, general redundancy detection, dominance detection, probing, dual reductions, MIP presolve, automatic scaling transformations, basis crash, bound-shifted solver support, finite upper-bound simplex support, dual-value rescaling, external solver comparison, or performance benchmarking.

It should also avoid changing JSON schema, solution JSON schema, tableau simplex behavior, revised simplex behavior, CLI solve behavior, or backend comparison semantics. The first presolve layer should be a traceable preparation and diagnostic layer, not a hidden second solver.
