# Repeated-Pass Presolve Design Note

## 1. Purpose

Repeated-pass presolve is needed because one safe reduction can expose another safe reduction. A single pass is conservative and easy to reason about, but it can stop before reaching a clearly simpler equivalent model. For example, if `x` is fixed at `2` and a constraint is `x - 2 = 0`, fixed-variable substitution turns the row into `0 = 0`. The row is then a feasible empty row and can be removed without changing the feasible region. Under the current single-pass design, fixed-variable elimination runs after empty-row detection, so this newly empty row is intentionally left in the presolved model.

The goal of repeated-pass presolve is not to add aggressive industrial presolve. The goal is to let already-approved conservative reductions compose safely. SILO's presolve philosophy should remain deterministic, traceable, and recoverable. Every structural transformation must be recorded, every public diagnostic should be stable across runs, and any solution returned by a solver on the final presolved model must be recoverable in original model space.

Repeated passes are especially important now that `silo solve --presolve` exists. A user who explicitly opts into presolve expects safe reductions to be applied consistently, not only when they happen to be visible in the original model. The first repeated-pass implementation should therefore focus on the narrow cases already supported by the presolve layer: empty rows, empty columns, fixed variables, and scaling diagnostics.

## 2. Current Presolve Boundary

The current presolve layer supports empty-row detection and feasible empty-row removal, infeasible empty-row detection, empty-column diagnostics, simple empty-column unboundedness detection, fixed-variable elimination, fixed-variable solution recovery, and coefficient-range scaling diagnostics. The CLI exposes these capabilities through `silo presolve MODEL_PATH`, and `silo solve MODEL_PATH --presolve` can solve the current presolved model and recover fixed variables.

The current behavior is intentionally single-pass. `Presolver.run()` validates the model, computes scaling diagnostics on the submitted model, checks for infeasible empty rows, checks for unbounded empty columns, removes feasible empty rows, and eliminates fixed variables. It does not loop back after fixed-variable elimination. This keeps the initial behavior simple and avoids hidden interactions among transformations while the public result objects and recovery path are still young.

That boundary is useful, but it should now be made explicit in the next design step. Repeated-pass presolve should not change the meaning of existing reductions. It should only re-run the conservative structural checks after a structural change has created a new opportunity.

## 3. Why a Single Pass Is Not Enough

The simplest motivating case is a fixed variable creating a feasible empty row. Suppose `x = 2` and the model contains `x + y <= 5`. Fixed-variable elimination updates the row to `y <= 3`, which is the intended reduced row. If instead the model contains `x - 2 = 0`, substitution creates `0 = 0`. The row is now redundant and should be removed by the existing feasible empty-row logic.

Fixed substitution can also create an infeasible empty row. If `x = 2` and a row is `x <= 1`, substitution creates `0 <= -1`. A repeated pass can detect this as presolve infeasibility and stop before a solver sees a degenerate unsupported model.

Removing one row may reveal an empty column. A variable may appear only in a feasible empty row or in rows that become empty after fixed-variable substitution. Once those rows are removed, the variable may no longer appear in any constraint. Empty-column diagnostics and simple unboundedness detection should then be reconsidered.

Fixed-variable elimination may also remove variables and update the objective. After that change, empty-column diagnostics should operate on the reduced variable set. Multiple fixed variables can cascade when one pass simplifies rows and leaves a smaller model for the next pass. Not all of these interactions should be implemented immediately, but the loop design should be able to support them without changing public conventions later.

## 4. Pass Ordering

The first repeated-pass implementation should use a deterministic order:

```text
1. validate model
2. scaling diagnostics on original model
3. empty-row infeasibility check
4. empty-column unboundedness check
5. feasible empty-row removal
6. fixed-variable elimination
7. repeat structural passes if the model changed
8. stop when no structural change occurs
```

Scaling diagnostics should be computed on the original input model only in the first implementation. This is the clearest user-facing interpretation: scaling diagnostics describe what the user submitted, not the sequence of intermediate transformed models. Recomputing scaling after each pass could be useful later for debugging, but it would require a more complex report structure and could confuse the simple CLI payload.

The structural pass should be applied to the current working model. Empty-row infeasibility and empty-column unboundedness are terminal checks. Feasible empty-row removal and fixed-variable elimination are structural reductions. A diagnostic-only empty-column warning should not cause another pass.

## 5. Termination and Change Detection

The loop should terminate when a complete structural pass applies no structural reduction. Structural reductions include removing a feasible empty row and removing a fixed variable. Warnings, notes, scaling diagnostics, and other diagnostic-only findings do not count as changes.

Because the first repeated-pass reductions strictly decrease either row count or variable count, infinite loops should not occur. Still, the implementation should include a safety guard. A reasonable initial limit is:

```text
max_passes = number_of_variables + number_of_constraints + 1
```

This bound is easy to explain: each successful pass should remove at least one row or one variable, and the extra one allows the final no-change pass. If the limit is reached, the presolver should return a clear diagnostic rather than silently continuing. The current `PresolveStatus` set does not include a dedicated numerical or iteration-limit status, so the first implementation can either add a warning/note with `NO_CHANGE` or introduce a narrowly documented presolve warning such as `presolve_pass_limit`. A status expansion should be a separate decision.

Change detection should be explicit. Each pass should return the working model, the reductions applied in that pass, the fixed values discovered in that pass, and a boolean `changed`. The outer loop should append reductions and fixed values in order.

## 6. Reduction Ordering and Traceability

Reduction records must remain deterministic. The ordering rule should be:

```text
pass order first, then within each pass:
  empty-row reductions in current constraint order
  fixed-variable reductions in current variable order
```

The complete reduction log should preserve the exact order in which transformations were applied. This matters for auditability and for future recovery. Even though fixed-variable recovery can currently be implemented by storing fixed values directly, future reductions may require inverse transformations to be applied in reverse order. The log should therefore be a faithful transformation trace, not merely a grouped summary.

Each reduction record should remain small. Empty-row records should store the original row sense and cleaned RHS at the time of removal. Fixed-variable records should store the fixed value, objective coefficient, and objective contribution. Large nested row snapshots should be avoided unless a future recovery operation requires them.

Diagnostics should also be deterministic. Removed-row tuples should follow reduction order. Fixed-variable tuples should follow the order of fixed-variable reductions. Warnings should follow the pass and scan order that generated them. If a warning is diagnostic-only and repeated across passes, the first implementation should avoid duplicate warnings when possible, or clearly document why duplicates appear.

## 7. Solution Recovery Through Multiple Reductions

`PresolveResult.recover_solution()` should eventually recover through all reductions in reverse order. Current fixed-variable recovery restores fixed variable primal values, adds basis status `"fixed"`, and adds zero reduced costs for fixed variables. This is sufficient for fixed-variable elimination because the objective constant in the presolved model already includes fixed-variable contributions.

With repeated passes, recovery must preserve original-space primal values, fixed variable values, objective value, basis status for fixed variables, reduced costs for fixed variables, and dual-value placeholders. The recovered objective should not be recomputed unless a future reduction requires it. The current approach of preserving solver-space objective value remains correct for fixed-variable substitution because the presolved objective already contains the fixed contribution.

Slack values need more care. At present, recovery preserves solver-produced slack values. Once rows can be removed across multiple passes, this may be insufficient because removed original rows will not appear in the solver-space model. The next recovery design should consider recomputing slack values from the original model and recovered primal values. That would also make recovery more robust when future row reductions are added.

The repeated-pass result should retain enough original-model context for recovery. A simple path is to store the original model in `PresolveResult` or in a dedicated recovery context. If that is considered too large for the public object, a private recovery context can be introduced while keeping the public result fields stable.

## 8. Status Priority Across Passes

Status priority should be:

```text
INFEASIBLE empty row > UNBOUNDED empty column > REDUCED > NO_CHANGE
```

Across passes, terminal statuses stop the loop immediately. If any pass detects infeasibility, presolve returns `INFEASIBLE` and does not call later reductions. If any pass detects unboundedness, presolve returns `UNBOUNDED`. If at least one structural reduction occurred and no terminal status occurred, the final status is `REDUCED`. If no structural reduction occurred and only warnings exist, the final status remains `NO_CHANGE`.

This priority matches the existing conservative behavior and gives `silo solve --presolve` a clear status mapping. Terminal presolve statuses produce ordinary solution JSON with `infeasible` or `unbounded` status and exit code `1`. Nonterminal statuses continue to the selected backend.

## 9. Interaction with CLI Solve and Presolve Diagnostics

`silo presolve MODEL_PATH` should show the final repeated-pass result. The JSON payload should continue to include `model_path`, `presolve`, `reductions`, and `scaling`. The `reductions` array should list all reductions in pass order. The command should not serialize the full presolved model in the first repeated-pass implementation unless a separate task adds that feature.

`silo solve MODEL_PATH --presolve` should solve the final presolved model and recover the original-space solution. If repeated passes prove infeasibility or unboundedness, the solve command should return ordinary solution JSON without invoking a simplex backend.

The default `silo solve MODEL_PATH` command should remain unchanged. Repeated-pass presolve is an opt-in solve path and a diagnostic command path, not a default behavior change.

## 10. Testing Strategy

Future tests should cover fixed-variable substitution that creates a feasible empty row, fixed-variable substitution that creates an infeasible empty row, fixed-variable removal followed by empty-column warning, multiple fixed variables across passes, reduction order across passes, and the fact that diagnostics-only warnings do not trigger another pass.

Tests should also cover the max-pass guard, recovered solutions with all original fixed variables restored, recovered objectives that are not double counted, `silo solve --presolve` on repeated-pass examples, and `silo presolve` reduction order. Regression tests should ensure ordinary `silo solve` remains unchanged and that `silo presolve` still returns exit code `0` when diagnostics are produced.

## 11. Proposed Implementation Phases

The future work should be split into small tasks:

```text
Phase 4H: repeated-pass presolve design note
Phase 4I: repeated-pass presolver loop with empty-row-after-fixed-variable cases
Phase 4J: original-space slack recomputation after presolve recovery
Phase 4K: repeated-pass CLI regression examples
```

Phase 4I should implement only the loop and the already-supported structural reductions. Phase 4J should improve recovery rather than adding new reductions. Phase 4K should lock the behavior through CLI fixtures and examples.

## 12. Out of Scope for the First Implementation

The first repeated-pass implementation should not include general row redundancy detection, row aggregation, duplicate-row removal, singleton-row bound tightening, automatic scaling, MIP presolve, dual reductions, probing, basis crash, or performance-focused presolve. These are valuable industrial-solver topics, but they are outside SILO's current readable reference path.

The first implementation should also avoid changing JSON model format, solution JSON schema, tableau simplex internals, revised simplex internals, and default solve behavior. The narrow goal is to make existing conservative reductions compose predictably.
