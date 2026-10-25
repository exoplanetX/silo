# Sparse basis, eta and session contract

SILO-SPARSE-LP-20261024 / SP1 design v1.0. Dense QR remains the reference.
Sparse numerical LU uses SciPy1.16.3 SuperLU only for linear equations; SILO owns
phases, pivots, pricing, validity, recovery, tree/CG and termination.

## RR02 numerical-policy revision — 2026-10-25

The SP1 equations and frozen input/truth chronology remain historical facts.
RR02 explicitly revises the strict-minimum-tie primal selector using the
[primal stability contract](sparse_primal_stability_contract.md), after R0
observations and its independent mathematical gate. Every positive blocker
limits a row-level window clipped by the original tolerance; nonnegative rows
use64*eps_float64*(1+abs(x_i)), while already tolerated negative deficits remain
covered. This avoids unrelated-large-coordinate inflation. Stable candidates are tried under
the original complete-state gates. Actual rho is separate from nonnegative
progress counting. At most2 private full trials per entering/semantic basis,
including optional preselection same-B refresh, survive generation restarts.
The prior automatic candidate-validation refresh is superseded by bounded
alternative leaving rows. Entering Devex/sticky Bland and forced residual
recovery remain unchanged in the first package. The selector/recovery-policy
version joins the session frame identity. This revision does not relax any
original primal/dual/KKT criterion or assert that capacity acceptance passed.

## Factor interface and numerical invariant

`lp/factorization.py` owns SparseFactor, a private session cache and diagnostics.
Interface: solve_B(rhs), solve_BT(rhs), replace_column(position,column,direction),
refactor(current_B,reason), immutable identity and actual-operation counters.
The adapter hides SuperLU's row/column permutations. No explicit inverse is formed.
Inputs/outputs are in declared basis order; only bounded vectors may be dense.

Every solve is checked against the current actual B or B^T:
`||residual||inf <= 1e-10*(1+||rhs||inf+||abs(B)*abs(solution)||inf)`.
On failure allow at most2 residual corrections, then exactly one current-B
refactor/retry; continued failure returns numerical_failure. Check deadlines
before/after library calls; Python cannot promise to preempt an arbitrary LU.
Initial input-factor nnz and returned L/U nnz obey the factor gate; failed
fill/allocation is recorded and never converted to optimal.

## Eta equations and order

Replace basis position r with entering a, d=B^-1*a, p=d[r]. Define
E=I+(d-e_r)e_r^T, B_new=B*E and B_k=B0*E1*...*Ek.

- E^-1*v: y[r]=v[r]/p; y[i]=v[i]-d[i]*v[r]/p for i!=r.
- E^-T*v: y[i]=v[i] for i!=r; y[r]=(v[r]-sum_{i!=r}d[i]*v[i])/p.
- B_k*x=b: first B0^-1*b, then eta inverses in chronological order.
- B_k^T*y=q: eta transpose inverses in reverse chronological order, then B0^-T.

Mandatory noncommuting example: B0=I, E1=((1,0),(1,1)), E2=((1,1),(0,1)).
B=((1,1),(1,2)); q=(1,0) yields B^-T*q=(2,-1), not the wrong-order (1,-1).
Test multiple RHS, transpose, random short legal chains and current-matrix residuals.

Only commit an eta after B_old*d=a and pivot checks. Chains store the full actual
direction (never truncate small coefficients), bounded by max_factor_updates0..20,
default20. Before update21 rebuild with current B and clear the chain. Pivot
protection uses existing pivot_tolerance and direction scale. Growth gate is
max(||d||inf,1/|p|)>1e8. Chain/pivot/growth/residual/structure/fill causes are
separate actual refactor reasons. max_factor_updates0 disables updates.

## Reference-frame Devex and deterministic fallback

Operative primary source is official COIN-OR CLP, commit
[d4baf2283d816e0fcf4df7bfb01a0b1bc28c87a2](https://github.com/coin-or/Clp/blob/d4baf2283d816e0fcf4df7bfb01a0b1bc28c87a2/src/ClpPrimalColumnSteepest.cpp).
Actual source sections read:539–610 pricing,886–1112 all nonbasic updates,
3714–3831 framework norm and outgoing weight,3906–3928 initialization.
Harris1973 is historical attribution; its full text was not read and is not
claimed as formula-level evidence.

At reset F is the set of then-nonbasic semantic variables and w=1. F stays fixed
through pivots. For primal MAX eligibility use the existing signed improving
reduced-cost test; among eligible columns maximize improving_rc^2/w. Equal
scores tie by ascending stable semantic key. Let q enter, p leave at row r,
d=B^-1*a_q, alpha=d[r], rho=B^-T*e_r, t_j=(a_j^T*rho)/alpha. At an accepted pivot:

`gamma = sum(d[i]^2 for basic_key[i] in F) + int(q in F)`;
`w_p = gamma/alpha^2`;
`w_j = max(0.99*w_j, t_j^2*gamma + int(j in F))` for all unchanged nonbasics.

This is the fixed-reference CLP Devex core, including slack columns, not Dantzig
sorting. Compute all t_j via one BTRAN plus sparse A^T*rho. Partial pricing and
other CLP mode-switch heuristics are excluded. Freeze a SILO engineering positive
weight floor1e-12 (not a claim about CLP's exact floor). Nonfinite gamma/weights
force a reference reset before selection, never an invalid pivot.

Reset F/w on session start, true factor rebuild, rejected pivot, incompatible
basis/coordinate/scale/structure change. For a genuinely appended nonbasic column
with unchanged B/scaling, initialize its w=1 and add its semantic key to F;
unchanged entries remain. Remove deleted nonbasic entries; deleting a basic
variable requires a rebuild. These are explicit project cache policies.

Bland is a project engineering fallback: a repeated basis signature or two
consecutive accepted steps theta<=primal_tolerance triggers sticky Bland through
the current phase (or a fresh cold phase). Enter the smallest eligible semantic
key; ratio ties use the smallest basic semantic key. Record trigger, reset and
exit. This is not a floating-point anti-cycling theorem. Dual retains its existing
deterministic leaving/ratio policy and uses the same factor interface.

## Passive basis and private cache

Version3 passive snapshots bind shape, ordered row/column/basis semantic keys
and actual sparse coefficients in O(nnz) immutable data. They contain no LU,
eta arrays, mutable dictionaries, or dense full-model tuple. Version2 import
is verified and semantically mapped, then newly factorized; bad mappings record
one cold fallback. Never use historical column numbers directly as identity.

The private cache hit validates current B dimensions, ordered row/basis keys,
actual scaled B coefficients, coordinate/side/scale identities and numerical
strategy. A full model SHA change alone does not invalidate unchanged B. A stable
SHA alone never replaces actual coefficient identity. Arbitrary old-row/column
reordering or engine changes invalidate; compatible appended nonbasic columns
are explicitly checked as extensions, not falsely treated as reordering.

| Change | Factor policy | Required fresh work |
|---|---|---|
| RHS, unchanged B/signature | Keep base+eta | Basic values, feasibility, method, dual/termination/KKT |
| Bounds/offset, unchanged B/side/coordinate map | May retain | New RHS/history and original solution; never old primal |
| Objective or dual tolerance, unchanged B | May retain | Dual/reduced costs, stopping and proofs |
| Appended nonbasic, unchanged B/scaling | Retain then real update if pivoting | New column pricing and validity |
| Added row/dimension | Invalidate, map/extend then new LU | All extended-model calculations |
| Changed fixed/free/side/scale/presolve structure | Invalidate | Fresh map/factor or one cold fallback |
| Invalid/stale basis, actual coefficient/key mismatch | No cache hit | Explicit reason and safe recovery |

LPSession uniquely owns the mutable cache. Direct solve has no cross-user global
cache. Node sessions do not share mutable factors; a child may import only its
parent's passive basis and build its own state. Public model is a copy. Editing
an external input/result/snapshot cannot mutate a private factor. SuperLU is not
deepcopied or serialized. Changing numerical limits checks retained state first.

Cache validation has three distinct layers, applied in this order:

1. Algebra identity: engine/dtype, dimensions, ordered row/basic keys, actual
   scaled B coefficients, coordinate directions/row sides/scales. Any mismatch
   invalidates the factor. The frozen library strategy is SuperLU COLAMD with
   its default numerical pivoting, plus residual1e-10/refinement2/growth1e8.
   These policy constants and implementation version join the factor-policy key.
2. Resource/pivot policy: changing pivot_tolerance forces current-B rebase and
   clears eta/pricing state before reuse. A tighter max_factor_nnz below retained
   L/U storage returns resource_limit and releases that cache; zero refuses a
   nonempty factor. Recheck max_sparse_nnz on input/standard before any cache hit.
   If a new max_factor_updates is below retained chain length (including zero),
   rebase current B and clear the chain; otherwise retain within the new ceiling.
   A changed ceiling alone does not pretend old updates were newly performed.
3. Fresh solve/pricing state: primal/dual/objective/complementarity/integrality
   tolerances and objective/RHS are not factor algebra identity. They always
   recompute basic values, feasibility, method, dual/RC, original KKT and proofs.
   A new public solve clears the visited-basis and sticky-Bland history. F/w may
   remain only for a validated unchanged primal Phase-II basis/coordinate frame;
   append compatible nonbasic entries as above. A cold fallback, actual phase
   change, dual-pivot basis change, factor rebuild or incompatible structure
   resets F/w. No stale reduced cost, primal, dual, witness or terminal result
   survives any edit. lp_method changes recompute method feasibility using the
   current B; they never authorize a stale solution or an invalid primal start.

Check all three layers for every SolveOptions change; in particular a looser
dual/objective tolerance does not by itself refactor valid B or grant proof.

## Mechanism and resource evidence

Counters are actual calls: base_factorizations, eta_updates,
refactorizations_by_reason, within_solve_reuses, cross_solve_reuses, cold_fallbacks.
Record A/standard/L/U nnz, factor fill, eta chain length/bytes, residual/refinement
and reset reasons. The stable efficiency denominator is all successful same-size
basis-column replacements, including periodic/safety rebuild pivots. It cannot
be shrunk using an implementation-defined eligible flag. Require the frozen
8 inputs' >=50 pivots and >=70% real updates. Deliberate recovery tests remain
separate from that denominator.
