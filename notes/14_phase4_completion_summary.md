# Phase 4 Completion Summary

## 1. What Phase 4 Added

Phase 4 moved SILO from a pair of small LP backends into a solver-building project with a visible preprocessing and diagnostic layer. The core addition is a traceable presolve API built around `PresolveResult`, `PresolveDiagnostics`, `ScalingDiagnostics`, and `ReductionRecord`. These objects make preprocessing explicit: the returned result contains the transformed model, deterministic reduction records, status diagnostics, coefficient-range diagnostics, and recovery data.

The implemented presolve rules are intentionally conservative. Empty-row diagnostics detect feasible empty rows, infeasible empty rows, and removable redundant rows. Empty-column diagnostics report variables that do not appear in constraints and can also prove simple unboundedness for a nonconstrained variable with a positive maximization objective coefficient and no finite upper bound. Fixed-variable elimination substitutes variables whose lower and upper bounds are equal, updates constraints and objective constants, records the transformation, and restores fixed values during recovery. The repeated-pass loop composes these existing reductions so that one safe transformation can expose another, such as fixed-variable elimination creating a feasible empty row. Recovery now also recomputes original-space slack values from the original model and recovered primal values.

Phase 4 also added two user-facing CLI paths. `silo presolve MODEL_PATH` reports presolve and scaling diagnostics without solving. `silo solve MODEL_PATH --presolve` explicitly applies conservative presolve before the selected native backend and then recovers the solution in original model space. Checked-in JSON examples and the Phase 4 regression matrix now document these behaviors.

## 2. Presolve Philosophy

The Phase 4 presolve philosophy is conservative, deterministic, traceable, recoverable, and diagnostic-first. Presolve is not treated as a hidden performance layer. It is a small set of mathematically transparent transformations whose effects can be inspected and tested. The public result should explain what changed, why it changed, and how a solver-space result maps back to the submitted model.

This philosophy matters because SILO is an educational reference implementation. It should not conceal convention changes behind polished output. If a reduction changes a variable, row, objective constant, or diagnostic status, that change must be represented in a reduction record or diagnostic object. If a transformation cannot yet be recovered cleanly, it should remain a diagnostic or future task rather than being applied silently.

Diagnostics do not imply structural change. Scaling warnings, empty-column warnings, and coefficient-range warnings can help users and future developers understand a model without changing the model that reaches a solver. This keeps the boundary between model inspection, model transformation, and LP solution behavior clear.

## 3. Public CLI Behavior

The public CLI behavior is now split into three clear workflows.

`silo solve MODEL_PATH` solves a supported JSON LP with the default tableau backend. Users can select a backend explicitly with `--solver tableau` or `--solver revised`. Presolve is not enabled by default, so unsupported features such as nonzero fixed bounds still produce ordinary solver errors unless the user opts into presolve.

`silo solve MODEL_PATH --presolve` applies conservative presolve before solving. If presolve proves infeasibility or unboundedness, the command returns ordinary solution JSON with the corresponding status and does not call a simplex backend. Otherwise, the selected backend solves the presolved model, and recovery restores fixed variables and original-space slack values.

`silo presolve MODEL_PATH` is diagnostic-only. It returns JSON containing the presolve status, change flag, warnings, removed rows, fixed variables, reduction records, and scaling diagnostics. It does not solve the model and does not serialize the full presolved model.

`silo compare MODEL_PATH` remains a backend comparison command. It runs the same raw JSON model through tableau and revised simplex without presolve and reports whether the backend statuses and objective values are consistent under the current comparison convention.

## 4. Current Presolve Capabilities

Current presolve capabilities include feasible empty-row removal, infeasible empty-row detection, empty-column warnings, simple empty-column unboundedness detection, fixed-variable elimination, repeated-pass composition of existing structural reductions, original-space slack recomputation after recovery, and coefficient-range scaling diagnostics.

The repeated-pass loop uses deterministic ordering. Each pass first checks terminal empty-row infeasibility and empty-column unboundedness, then removes feasible empty rows in current constraint order, and then eliminates fixed variables in current variable order. Reduction records follow pass order, so the log reflects the sequence in which transformations were applied. Scaling diagnostics are computed once on the submitted model, not on each transformed intermediate model.

The recovery path restores fixed variables, assigns fixed basis status, sets fixed reduced costs to zero, preserves the solver-space objective value, filters transformed-only variables out of public solution fields, and recomputes slacks from the original model constraints when original model context is available.

## 5. What Remains Out of Scope

Phase 4 does not implement automatic scaling. Scaling remains diagnostic-only because automatic scaling requires careful mapping of primal values, reduced costs, dual values, feasibility residuals, and objective values.

Phase 4 also does not implement singleton-row bound tightening, general redundancy detection, duplicate-row removal, row aggregation, probing, dual reductions, MIP presolve, performance-oriented industrial presolve, or advanced numerical scaling. These are useful solver topics, but they would be premature without a broader transformation and recovery architecture.

The native LP backends still do not expose dual values. They do not support finite upper bounds, nonzero lower bounds, minimization models, integer variables, binary variables, or industrial sparse factorization. Fixed variables are supported only through explicit opt-in presolve.

## 6. Regression and Quality Gates

Phase 4 is protected by unit tests for presolve dataclasses, empty-row diagnostics, empty-column diagnostics, fixed-variable elimination, scaling diagnostics, repeated-pass reductions, and original-space slack recovery. It is also protected by checked-in JSON examples for fixed-variable recovery, repeated-pass empty-row removal, and presolve-detected infeasibility after fixed-variable substitution.

The Phase 4 regression checklist records current CLI behavior for every JSON example under `examples/json/`. The associated regression matrix covers default solve, tableau solve, revised solve, all three solve-with-presolve forms, `silo presolve`, and `silo compare`. The matrix deliberately records that presolve-only fixed-bound examples return `error` without `--presolve`, while solving or diagnosing correctly when presolve is explicitly enabled.

Quality gates remain simple and repeatable: editable installation, full `pytest`, `python scripts/check_quality.py`, CLI smoke tests, and `git diff --check`.

## 7. Readiness for Phase 5

Phase 4 leaves SILO ready to begin Phase 5, but Phase 5 should start with a branch-and-bound design note rather than immediate implementation. The design should define the first supported MIP class, how LP relaxations are created, how unsupported bounds are handled, how branching and node selection remain deterministic, how incumbents and pruning are reported, and how statuses map back to public solution JSON.

The completed Phase 4 work provides useful foundations for Phase 5: deterministic LP backends, a JSON example suite, explicit backend comparison, conservative presolve, recovery discipline, and regression coverage for public CLI behavior. The next step is to design the MIP layer so it uses these foundations without blurring the separation between core modeling, presolve, LP relaxation, and MIP tree search.
