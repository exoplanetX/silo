# Sparse program evidence and budget contract

SILO-SPARSE-LP-20261024, SP1 v1.0. Exact fixed IDs/shapes/source hashes and options
are materialized in tests/fixtures/sparse_program_manifest.json, sources.json and
oracles.json. The issued overall and implementation plans govern all thresholds.
No production implementation precedes input/design/truth/baseline freeze and SP1 GO.

## Groups and truth

- 48 tiny LPs in the four prescribed twelve-model families, <=4 variables/8 rows:
  independent actual-binary Fraction vertices/analytic truth, not SILO transforms.
- 24 pressure cases use the declared16 required exact terminal cases,4 numeric
  sets fixed before solving, and4 explicit resource/limit exits. They cannot be
  moved into or counted as the24 capacity/outside required-success models.
- 12 capacity recipes retain their fixed nonfixed variable/effective-row shapes,
  prescribed coupled families and nnz ceilings. All12 optimal within120s/1GiB;
  six fixed IDs disable presolve and must make>=20 effective pivots.
- 12 fixed Netlib IDs, all optimal within120s/1GiB under the same tolerances.
  Save official raw/compressed/decoded/converted files and hashes. An independent
  MPS reader must compare coefficients, all sides/bounds and costs/constant/sense
  on original data; a shared unverified conversion is not independent evidence.
- 8 mechanisms each>=50 pivots, true-update share>=70% on the declared stable
  denominator; separate bad-pivot/basis/transpose/rebuild recovery components.
- 8 edit trajectories, each20 expected-optimal states; RHS/BOUND/ROW/COL each2.
  RHS-02 and COL-02 have>=1000 variables/500 rows. Each state's independent
  truth/proof is frozen, not derived from the new native solver.
- 12 fixed small MIPs and4 CGs use the prescribed IDs and states, including
  actual branching/local cuts and Phase I/II; the old exact1/3 and tiny negative
  reduced-cost contracts remain. No larger search capability is introduced.
- Historical tests/288 fixed cases/192 audit models and saved64 diagnostic results
  retain their original truth/input identities. Saved diagnostics are rechecked,
  never re-solved against an exhausted old ledger.

Raw optimality checks use the existing contribution-scale primal/dual/sign/
complementarity/objective rules and reference objective tolerance
1e-7*(1+abs(reference)). Required-optimal timeout/numerical_failure is a failure,
not a capacity pass. Actual binary values are converted before rational arithmetic.
HiGHS references/readers form one algorithm stream, not many independent solvers.

## Driver and sequencing

Public entry scripts/sparse_program.py has preflight, freeze-inputs, check-inputs,
baseline --engine dense --cohort overlap, run --group tiny/pressure/sp2-smoke/
mechanism/capacity/netlib/mip-cg/historical --engine sparse,
warm --round1 --repetitions5, evaluate --stage SP2/SP3, install-checks
--candidate0.3.0a1 and summary --final. Internal worker options are not product API.
Every run uses a new UUID folder under outputs/sparse_lp_program_20261024.

First commit all recipes/IDs/raw/converted hashes/thresholds, then record native
dense overlap baselines and independent truth. Commit the latter and obtain
independent architecture/evidence design GO before any src/pyproject edits.
SP2 gates48 tiny/24 pressure/4 named small Netlib/2 named capacity smoke cases.
The complete12+12 capacity/outside performance gate remains in SP4 after updates.
SP3 gates math/actual reuse/performance separately. SP4 closes all eight criteria
with a read-only final reviewer who did not implement the system.

## Fair timing and memory

Single thread, fixed machine/versions/parameters; report import and initialization.
For each trajectory/mode/repeat,60s covers import/initial solve and all20 edits.
Time every edit including copying/validation/normalization/factor/reoptimization/
recovery/original check, not only triangular solves. Warm/cold mode order alternates.
Formal8x2x5x20=1600 state solves plus80 initial solves per round; all5 repetitions
remain in evidence. For each i, take median_j(Tcold_ij/Twarm_ij) on the20-state
segment, then median of the8 ratios. Require median>=1.5 and>=6 ratios>=1. Also
publish initial-inclusive totals/amortized ratios; don't broaden the claim.

Measure process OS peak RSS, including native library allocations; ndarray bytes
alone are insufficient. Independently guard wall/memory and distinguish a killed
child from solver-returned limit. Track global dense-allocation boundaries even
when observed RSS is low. Report A/standard/factor nnz/fill and update-chain bytes.

## Append-only accounting and recovery

Time buckets SP1/SP2/SP3/SP4/reserve are1800/3600/10800/10800/1800 seconds;
total28800. All validation/reference/build/install/failures are charged once at
the top-level command. Nested timers are descriptive and do not double-charge.
Keep source/input/script/environment identities, argv/start/end/pid, started/
completed actual calls, output hashes and failure/retry details. Unit-suite calls,
native roots, node/RMP LPs and references have separate counts. No mixed128 cap.

Max full capacity/outside2 rounds; warm2 rounds each5 repeats; quality3 rounds;
diagnostics20 batches each<=60s; each phase initial+2 targeted corrections.
Each of8 installs has<=1 same-SHA purely environmental retry. Before a full batch
reserve enough remaining stage/total time; do not assume all groups can consume
their individual maxima and still repeat. Do not reset on restart.

If a command is live, verify its actual process/tool handle, not a stale intent or
lock. Recover actual completed receipts with unchanged relevant source/input;
do not restart a child only because an observation timed out. Preserve failed,
timed-out and OOM records. Old evidence roots/artifacts remain byte-identical.

## Completion and scope

Require all eight overall criteria and independent technical GO, not only green
tests or correct CSR storage. Local candidate0.3.0a1 has8 source-independent
Windows3.11/3.13 x wheel/sdist x NumPy-dense/SciPy1.16.3-sparse installs. Document
actual platform/NumPy/source/archive/direct_url and no optimizer calls. Current
README/install/learning/workbench provenance points to the new candidate while
historical reports remain. Remote CI/push/public release stay unexecuted.
Original C/D/E and native deferral remain separate; no new research prerequisite.
