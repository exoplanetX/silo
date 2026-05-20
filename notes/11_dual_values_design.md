# Dual Values Design Note

## 1. Purpose

Dual values are useful solver diagnostics, but they should not be exposed casually. A public dual value is usually interpreted as a shadow price for a user-facing constraint. That interpretation depends on the objective sense, row sense, RHS sign, normalization steps, and the exact convention used by the algorithm. If SILO returns numbers before these mappings are fixed and tested, users may draw the wrong economic or sensitivity conclusion even when the primal solution is correct.

The current LP layer is still intentionally small. The dense tableau solver is an educational reference path, and the revised simplex solver is a readable basis-oriented implementation. Both are now able to solve small continuous maximization LPs with `<=`, `>=`, and `=` rows through Phase I / Phase II logic. The next diagnostic temptation is to expose the simplex multipliers already computed by revised simplex. This note records why that should wait until the row-mapping convention is made explicit.

## 2. Current Status

Both native LP solvers currently return:

```python
dual_values == {}
```

This is deliberate. The public `Solution` object already includes status, objective value, primal values, constraint slacks, reduced costs, and basis status. These fields are reconstructed for original variables and original constraints. Dual values require one more layer: mapping standard-form row multipliers back to the original model rows with a documented sign convention.

The revised simplex implementation computes simplex multipliers internally when evaluating reduced costs. For a basis `B`, it solves:

```text
B^T pi = c_B
```

which is equivalent to `pi^T = c_B^T B^{-1}`. These multipliers are tied to the transformed equality rows used by the standard-form problem, not directly to the model rows as written by the user.

The tableau implementation also has enough information to recover comparable row multipliers, but its internal objective row stores a sign convention that differs from the public reduced-cost convention. That difference is manageable for reduced costs because they are reported only for original variable columns. It is more delicate for row duals because row normalization can change the meaning of each multiplier.

## 3. Candidate Convention

For the standard equality form

```text
maximize c^T x
subject to A x = b
           x >= 0
```

the natural candidate row multiplier is:

```text
pi^T = c_B^T B^{-1}
```

Under this convention, reduced costs are:

```text
reduced_cost_j = c_j - pi^T A_j
```

For a maximization problem with nonnegative variables, optimality requires nonbasic lower-bound variables to have nonpositive reduced costs. This convention is already used by the revised simplex implementation and is now the public convention for both native LP solvers.

The candidate public dual convention should therefore be anchored to the same `pi`. For each transformed equality row, the internal multiplier describes the marginal change in the standard-form objective with respect to that transformed RHS. The public challenge is to translate that multiplier to the original row as the user wrote it.

## 4. Row Normalization Issues

SILO accepts original rows with `<=`, `>=`, and `=` senses. It also normalizes rows with negative right-hand sides. For example:

```text
-x <= -2
```

is transformed into:

```text
x >= 2
```

This multiplication by `-1` changes the sign of the RHS perturbation. A multiplier for the normalized row is not automatically the multiplier for the original row. If the original RHS increases by one unit, the normalized RHS may decrease by one unit after sign flipping. Returning the raw standard-form multiplier would silently reverse the reported shadow price.

The same issue appears when inequalities are converted to equality form. A `<=` row receives a nonnegative slack variable. A `>=` row receives a nonnegative surplus variable and may receive an artificial variable for Phase I. Equality rows receive artificial variables when no natural basis is available. These additional columns help the algorithm, but they are not user-facing constraints. Their presence should not change the interpretation of the final row dual except through the basis selected at optimality.

Degeneracy adds another caution. Multiple optimal bases can produce different dual multipliers when the dual solution is not unique, even if the primal solution and objective value match. Tests should avoid asserting a unique public dual in degenerate examples unless the mathematical dual is unique or the solver's pivot rule deterministically selects the same basis.

## 5. Equality, <=, and >= Row Mapping

The likely public convention should be expressed in terms of the original maximization model:

```text
maximize c^T x
subject to original rows
           x >= 0
```

For an original `<=` row, a positive public dual value should mean that increasing the RHS can increase the optimal maximization objective. For an original `>=` row, the sign convention must be documented carefully because relaxing the row means decreasing its RHS, while increasing the RHS makes the constraint tighter. Equality row multipliers are unrestricted and should represent the marginal value of increasing the equality RHS.

One implementation path is to extend the standard-form row metadata. Each transformed row should record:

```text
original constraint name
original sense
normalization sign, either +1 or -1
transformed sense after normalization
```

After solving, the solver can compute equality-form multipliers for transformed rows and map them back by applying the normalization sign. The row sense then determines how the public value should be interpreted and what sign patterns should be expected at optimum.

The tableau and revised simplex solvers should share this mapping convention. They may compute internal multipliers differently, but public `dual_values` must be identical on small nondegenerate test cases.

## 6. Testing Requirements Before Exposure

Before `dual_values` is populated, tests should check at least:

- shadow-price sign for `<=` rows in nondegenerate maximization examples;
- shadow-price sign for `>=` rows, including cases where the row is binding;
- equality row multipliers;
- negative RHS normalization, especially examples multiplied by `-1`;
- consistency with public reduced costs through `reduced_cost_j = c_j - pi^T A_j`;
- complementary slackness on small LPs;
- parity between tableau and revised simplex on nondegenerate models;
- empty or carefully documented behavior for infeasible and unbounded solves.

The tests should include cases with objective constants, because objective constants should not affect row duals. They should also include at least one model where a nonbasic original variable has a strictly negative reduced cost, ensuring that the multiplier and reduced-cost sign conventions agree.

## 7. Out of Scope for Now

This task does not implement public dual values. It does not add sensitivity ranges, alternative optima reporting, basis inverse exports, warm starts, presolve-aware row recovery, or industrial numerical safeguards. It only records the convention that should guide a later implementation.

Until that later task is completed, returning `dual_values == {}` is safer than returning plausible but under-specified numbers. The immediate priority is to keep primal diagnostics, reduced costs, and basis statuses aligned between tableau and revised simplex while preserving a clean path for future dual reporting.
