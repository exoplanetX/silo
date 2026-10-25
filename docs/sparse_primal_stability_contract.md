# Sparse primal stability and bounded recovery contract

SILO-SPARSE-LP-20261024 / RR02 / row-window mathematical design GO v1.1, 2026-10-25.
Authority: [RR02](../tasks/codex/20261024-02-02_sparse-lp-program.md).
Original inputs, reference truths, original-space acceptance tolerances, and eight
outcomes stay fixed. This document explicitly revises internal selection policy;
the SP1 freeze and the seven prior failed cohorts remain historical evidence.

## 1. Object and original state machine

The working problem remains max c^T z subject to Az=b, z>=0, with SILO's existing
normalization/restoration. Let x=B^-1 b, lambda=B^-T c_B, r=c-A^T lambda and
d=B^-1 a_q for an eligible improving nonbasic q. A published primal state is bound
to the actual CSC B, ordered semantic basis, generation, b/c, and run/phase token.

| State | Existing invariant | Next operation |
|---|---|---|
| Complete current state | B and BT residual-valid, finite, same generation; x passes original primal gate | Price only fresh r |
| Entering selection | Original reduced-cost test and Devex/sticky Bland | Solve d against current B |
| Leaving selection | Previously strict minimum max(x_i,0)/d_i, safe pivots only in exact ties | RR02 replaces this incomplete selector |
| Private new-basis trial | Old owner untouched; full B/BT/r state generation-coherent | Publish only after original finite/primal gates |
| Published trial | Basis/factor/state committed together, one-use pending | Reprice and rerun all selection on current state |
| Voluntary same-B trial | Old full state still trustworthy | Publish only validated trial; otherwise retain trusted owner |
| Forced residual recovery | Old factor failed its residual evidence | Existing bounded refinement/rebuild; failed recovery cannot restore old owner and continue |
| Termination | Original-space KKT/proof pipeline; rejection is never optimality evidence | Public result with original conventions |

Generation changes invalidate direction, leaving, ratio and uncommitted Devex
weights. Same-B generations do not reset bounded candidate expenditure. Basis
changes reset per-basis local rejection and candidate records. Public solve/edit
boundaries never retain a pending state or recovery objective from another run.

## 2. Two-pass selector

Use the unchanged epsilon_p and current-state allowance
tau=epsilon_p*(1+norm_inf(x)). Define gamma=64*eps_float64, a fixed engineering
selection constant, and row allowance
delta_i=min(tau,max(-x_i,0)+gamma*(1+abs(x_i))).
Every real blocking row P={i:d_i>0} participates, including unsafe pivots.
The common window is theta_bar=min_{i in P}(x_i+delta_i)/d_i. A trustworthy
current state satisfies0<=max(-x_i,0)<=delta_i<=tau, so its headrooms are nonnegative.
An unrelated large coordinate and a candidate's amplified norm cannot enlarge
a nonnegative row's roundoff-level selection margin. Final gates still use the
original public tolerance, not gamma.

Compute equivalent overflow-safe headroom: for x_i<0 use
min(gamma*(1+abs(x_i)),tau+x_i)/d_i; for x_i>=0 use
x_i/d_i+min(tau,gamma*(1+x_i))/d_i. This avoids cancellation of a negative
deficit and avoids overflowing the numerator before a meaningful division.

Second-pass rows satisfy s_i=max(x_i,0)/d_i <= theta_bar and the existing safe
pivot predicate abs(d_i)>pivot_tolerance*(1+norm_inf(d)). Rank by descending
abs(d_i), then the leaving variable's semantic key, then row position. No new
near-equality or instance-dependent threshold is introduced.
Finite direction with an empty positive-blocker set goes to the existing ray
path before optional refresh. Positive h_i overflow to +infinity remains a
nonbinding blocker, never a deleted row. NaN h_i, nonfinite direction/state or
nonfinite delta is numerical failure; it cannot become an empty-blocker ray.

For each ranked row r compute actual rho=x_r/d_r and y=x-rho*d, then y_r=rho.
Full predicted finite/primal checks use epsilon_p*(1+norm_inf(y)), not a clamped
step. Scan cheaply with one O(m) work vector; keep at most two full private
candidate trials. Progress/degeneracy uses max(0,rho), while algebra and recorded
actual pivot observations use rho. A tolerated negative rho does not become a
zero entering coordinate or an assertion of exact nonnegativity.

For rho>=0, window membership bounds every nonleaving positive-d coordinate by
-delta_i>=-tau; nonpositive-d coordinates cannot decrease below their old values.
This is a current-scale bound only. The actual candidate norm can differ, and
rho<0 invalidates the nonpositive-d monotonicity argument. Therefore predicted
and actual-factor complete-state gates are mandatory independent conditions.
The algorithm only claims floating acceptance under unchanged original gates.
In particular, gamma is not an exact forward-error bound or a proof of exact
optimality on all floating inputs. A true tiny blocker below that allowance may
still be crossed within numerical gates; original scaling/KKT and the fixed
independent objective checks remain necessary.

Example: x=(0,1e-8), d=(1e-12,1). The strict-minimum row has unsafe pivot1e-12.
The two-pass window includes row2; its stable pivot produces y=(-1e-20,1e-8),
which passes the original gate. The tiny row still constrains theta_bar.

The initial global-tau proposal was disproved by an unchanged old regression:
x=(0,1e4),d=(1e-8,1e4) allowed rho1 and objective1 for a model whose exact optimum
is0. The row-window bound is instead gamma/1e-8~=1.421e-6 and excludes rho1;
the unsafe genuine blocker remains binding. No acceptance tolerance was changed
and the old wrong-optimal test was not weakened. All12 saved R0 states retain
a stable predicted candidate after the row-window refinement; its independent
mathematical review GO is distinct from actual CAP acceptance.

## 3. Bounded trial and recovery policy

The RR02 conservative budget is at most2 complete private trials per entering
and semantic current basis, including any voluntary same-B full-state trial.
Generation retries do not replenish it. Cheap predicted rejections are counted
separately; no full matrix or all-candidate coordinate history is saved.
Credit is consumed only when the private trial actually begins, using the real
candidate_basis_attempts/same_basis_refresh_attempts start counters. A stage
generation mismatch before construction consumes0. Restarts inside one private
trial still consume1. Cap enforcement precedes every construction; start deltas
are accounted in a finally path even when the trial raises or reaches a limit.

The initial package prioritizes up to2 prediction-pass leaving alternatives and
keeps entering pricing unchanged. Maintain an entering-indexed trial count in
the current semantic basis; do not reset it on factor-generation restarts.

1. Generate a stable ordering inside the common window; lazily check actual
   coordinates with one reusable O(m) vector and the unchanged predicted gate.
2. For each prediction-pass row, compute its own uncommitted Devex/BTRAN update;
   validate generation; consume one full-trial credit and stage the new basis.
   Candidate-specific rejection discards those weights and tries the next row
   if credit remains. Only an accepted candidate publishes weights and basis.
3. After2 private trials, reject the entering column with candidate-budget
   exhaustion. Do not claim that any untried leaving row is infeasible.
4. If there were no prediction-pass rows and no new-basis trial was attempted,
   an unused shared same-B refresh may consume one credit. A validated refresh
   restarts the full state/direction/window/ordering using pending exactly once;
   a rejected refresh leaves the trusted owner and rejects this entering.
5. No voluntary refresh is inserted after a rejected new-basis full trial in
   this initial package. Remaining credit is prioritized for a different
   prediction-pass leaving row. This prevents2 new-basis trials plus a third
   same-B trial. A preselection refresh leaves at most1 subsequent full trial.
6. A generation restart recomputes every selection quantity, retaining spent
   credits and same-basis rejection history. A successful basis change resets
   local trial/rejection state. The original bounded generation-retry ceiling
   still applies; candidate credits are never restored by a retry.

The old round7 voluntary helper remains available only at the bounded
preselection point. Rejected new-basis trials no longer automatically trigger
the old candidate_validation refresh. This is an explicit internal policy
revision, not a change to any primal tolerance or final acceptance gate.

Distinguish no positive blocker (possible improving ray), no stable algebraic
candidate, a candidate-specific full-state rejection, and finite candidate budget
exhaustion. Exhaustion does not prove that untried rows are infeasible. Rejecting
all improving entering columns remains numerical_failure; it never proves an
optimal result. Deadline/resource exits and unexpected programming errors retain
their existing precedence and classification. Actual trial LU/solve/refinement,
accepted/rejected updates, and simultaneous LU memory costs are all recorded.

No new Phase-I/dual/scaling/pricing-control recovery is included in this first package.
If R0 shows the selector insufficient, an independently reviewed finite route
must specify the original b/c restoration and failure semantics before coding.
Any adopted complete feasibility recovery is bounded by2 per public solve and
shares the original deadline, iteration and resource limits; no nested solve,
RHS/bound/objective perturbation, oracle initialization or external optimizer.

The new selector/budget/fallback version joins the private factor/session frame
policy identity. Old numerical/pricing policy frames cannot silently match it.
Existing public-solve freshness, strict algebra/resource validation and node/user
isolation remain. Dual pivots and artificial cleanup keep their original rules.

## 4. R0 evidence and final design gate

Two new diagnostic batches completed under60s each (26.3334261 and26.5895931s),
global diagnostic count2->4/20. Each mode/batch retained at most3 sparse states
per case: 12 states total across2 fixed cases and2 causal modes. This is the
observer's per-batch interpretation of the state-retention limit; the complete
inventory is explicit and no additional state export is planned. No case,
input/truth or acceptance tolerance was changed.

On the eta trajectory, FLOW iteration72 and TRANS iteration47 have no safe
strict-minimum tie row but each has one prediction-pass stable row in the
current-scale window. Their relative backward residuals are around1e-16;
independent same-B LU directions differ by at most floating roundoff (TRANS0).
FLOW later phase2 iteration397 has the same selector gap. On the no-updates
trajectories the gap also appears at FLOW106 and TRANS59, with stable predicted
alternatives. These separate trajectories are not paired causal replications.
They refute eta accumulation as a necessary explanation of this defect class;
they do not prove a unique cause for eventual CAP failure or new-basis acceptance.

All4 public calls started; FLOW's2 calls stopped on bounded prefix capture,
TRANS's2 calls returned the diagnostic time_limit. There were7069 native sparse
LU calls and12 independent same-B LU probes with36 probe linear solves. None is
formal capacity success. Full file/source/option/count/RSS bindings and all12
state summaries are in outputs/sparse_lp_program_20261024/reviews/rr02_r0_evidence.json.

Independent direct sparse LU/BT probes are observations only and cannot feed
solver choices. max_factor_updates=0 is a causal diagnostic, never formal
capacity/update-rate evidence. No oracle point is read by the observer/solver.

Independent theory_architect final mathematical GO has been received, with the
finite/ray/overflow and actual-start credit rules above as binding implementation
and test obligations. The observer's state-retention interpretation remains an
explicit owner accounting choice, not a mathematical-service authorization.
The v1.1 independent refinement gate adds the unchanged wrong-optimal regression,
the negative-deficit boundary and positive-numerator overflow-safe formula.
A design GO does not grant
capacity/SP2 GO. Full48/24/6 and original raw KKT remain the independent joint gate.

## 5. Primary implementation context

Independent derivation above precedes use of the external implementations.
Read for two-pass/recovery context only, without importing or porting code:

- [HiGHS HEkkPrimal.cpp, commit73cac48c5340d775a477087198611862559be250](https://github.com/ERGO-Code/HiGHS/blob/73cac48c5340d775a477087198611862559be250/highs/simplex/HEkkPrimal.cpp): chooseRow1268-1325, solvePhase2 and cleanup. Its own alpha filters and perturbations are not SILO's contract.
- [CLP ClpSimplexPrimal.cpp, commitd4baf2283d816e0fcf4df7bfb01a0b1bc28c87a2](https://github.com/coin-or/Clp/blob/d4baf2283d816e0fcf4df7bfb01a0b1bc28c87a2/src/ClpSimplexPrimal.cpp): introductory numerical feasibility/ratio/recovery discussion, lines15-55. No perturbation behavior is adopted.

Immutable blob SHA and raw-content SHA256 are recorded under the ignored program
outputs in reviews/rr02_primary_source_identity.json. These sources supply context,
not a theorem or a substitute for SILO's actual frozen-model acceptance evidence.
