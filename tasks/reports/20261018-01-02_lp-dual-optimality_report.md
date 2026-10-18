# LP Dual Values and Optimality Verification — Execution Report

## Result / scope

Implemented original-row optimal LP dual output in both existing native backends,
fixed-aware presolve recovery and an independent original-input optimality checker.
`silo compare` verifies each optimal primal/dual witness independently. Existing
solution/comparison JSON keys and solver/model capability boundaries are preserved.
MIP final results still expose no node-LP duals. No external solver was added to a
native algorithm, and no phase/native/dependency change occurred.

Risk L2 was explicitly approved by the user's request to begin this precise feature.
This is one atomic task with two immutable contract revisions: revision 02 corrects
the allowed comparison-documentation filename; revision 01 and its handoff report
are retained. No separate second development task was executed.

## Files / implementation

- `src/silo/lp/simplex/tableau.py`: track original-row linear combinations through
  normalization, pivots and redundant-row deletion; compute phase-II c_B^T*T.
- `src/silo/lp/simplex/revised.py`: retain existing B^-T*c_B multipliers; recover
  original row signs/names and zero-fill removed redundant equalities.
- `src/silo/presolve/presolver.py`: lift complete optimal multipliers, zero-fill
  removed feasible rows, reconstruct original reduced costs including fixed variables.
  Preserve small recovered multipliers/residuals rather than rounding away material
  RHS or fixed-bound objective contributions.
- `src/silo/lp/optimality.py`: validate domain, finite complete coordinates, original
  primal feasibility, dual signs, stationarity, three pairwise objective differences
  and complementarity. Return a residual report; no solve or backend helper reuse.
- `src/silo/cli/compare.py`: retain JSON keys, accept nonunique valid duals and reject
  equal-objective results with invalid evidence. Historical dual_values_empty remains
  descriptive for optimal LPs and required for matching nonoptimal statuses.
- `src/silo/core/solution.py`: document dual/reduced-cost semantics only.
- New `tests/unit/test_lp_duality.py`, `test_lp_optimality.py`, and
  `tests/verification/test_dual_oracles.py`; focused updates to existing LP/CLI/parity,
  fixed recovery and JSON regression assertions previously requiring empty duals.
- `docs/lp_duality.md`: bilingual teaching/design note, derivation, runnable hand
  example, fixed-bound correction, checker API, tolerance and cleanup boundary.
- README, LP/compare/baseline docs and dated project_profile/technical_route entries;
  matching new contracts and reports. Research notes and old contracts are untouched.

## Mathematical conventions / learning

For maximization c0+c^T*x: original LE multipliers >=0, GE <=0, EQ free;
rc=c-A^T*y<=0 on ordinary nonnegative unbounded-above variables. For exactly fixed
coordinates x_j=v_j, rc_j has no sign restriction, and the dual bound includes
sum_fixed rc_j*v_j. The objective constant appears exactly once on both sides.
The worked max 2x+7, x<=3 example gives x=3, y=2, rc=0 and P=D=13.

Checker default absolute tolerance is 1e-7; compare uses existing 1e-9. This is a
finite-precision check, not an exact proof or general numerical-robustness guarantee.
Standalone solve returns duals; callers explicitly invoke the checker. Compare invokes
it automatically. Presolve keeps its dependency boundary and does not import LP code.

## Checks / evidence

- Corrected red tests against untouched primary baseline 5cc88cb: 18 failed from
  missing dual/fixed-coordinate evidence. Same tests on initial implementation:
  18 passed in 0.24s. Initial test harness's omitted maximization sense was corrected
  before treating any failure as feature evidence (see revision 01 report).
- Initial broader targeted suite: 410 passed in 1.36s.
- Initial full suite: 1358 passed in 13.91s, Ruff passed.
- After preserving tiny fixed residuals: 82 targeted passed; full suite 1360 passed
  in 8.98s, Ruff passed. Docs' complete Python worked example executed successfully:
  check.passed=True, primal_objective=dual_objective=13.
- Independent review then found tiny row multipliers were still zero-rounded. Both
  backends were corrected; scale 1e9 and 1e10 regression inputs preserve y=1/scale
  and its material objective contribution. Final focused dual/checker/oracle suite:
  **117 passed in 0.64s**, Ruff passed.
- Final `python scripts/check_quality.py`: **1364 passed in 12.59s**, Ruff passed,
  process exit 0. No solver code changed after this final quality run.
- `git diff --check`: no whitespace errors.

Final new-test inventory: 25 dual/recovery checks, 41 checker controls, 51 original
analytical/JSON/warm-start/optional-HiGHS checks, and 2 compare nonuniqueness/corruption
checks: 119 added to the prior 1245 tests. Optional SciPy was present, so both new
marginal comparisons and the earlier optional oracle tests executed.

Environment: reused primary `.venv`, Python 3.13.9, NumPy 2.3.5, pytest 8.4.2,
SciPy 1.16.3. Worktree src was explicitly first on PYTHONPATH, including subprocess
console tests, and primary `.venv/Scripts` first on PATH. No environment/package
changes were required. This is not a fresh locked-environment reproduction.

## Independent services / resolved findings

Read-only theory_architect derived the signs, weak duality, row-transformation map
and fixed-coordinate correction; no experiments or writes. Its initial revised
cleanup provenance concern was refined by a second derivation: if current cleanup's
retained basis is nonsingular, the removed row set is valid and zero-multiplier
extension is sound. A source-row-based cleanup would avoid certain singular outcomes.

Read-only red_team_reviewer identified the small-row-multiplier rounding defect.
Main thread preserved raw multiplier values and added the four focused regressions.
Final review returned **ACCEPT_WITH_BOUNDARIES**, with no remaining fatal/major
findings and no further closure tests requested. The reviewer did not rerun tests;
its earlier test-count references predate the final 1364 run. No reviewer counts substitute
for mathematical or computational evidence; all implementation/tests ran in main.

## Known limitation / next atomic recommendation

Existing revised Phase-I cleanup deletes rows by residual artificial basis slot,
which can differ from artificial source row. A supplied feasible three-row Phase-I
basis for x=1, z=2, z=2 yields a singular reduced basis under current cleanup; the
existing linear solve returns NUMERICAL_ISSUE without optimal dual evidence. The new
regression captures this conservative behavior. Reachability under the current
deterministic pivot rule was not established. No pivot/search/cleanup algorithm was
changed in this task. See docs/lp_duality.md for the complementary-minor argument.

Next recommended atomic task: use artificial-column source-row provenance for robust
revised Phase-I redundant-row cleanup, with the documented constructed-basis case and
independent original-model checks. Recommend GPT-6 Sol / high for the dependency/minor
argument and regression design; routine fixtures may use Sol / medium. General bounds,
minimization and column-generation integration remain later separately scoped work.

## Git / integration / Remote Sync Proof

Primary checkout before work: main at 5cc88cb, origin/main at a4814f4, ahead/behind
`0 1`, with exactly five untracked notes/26..30 files. This known local baseline was
the basis of the user's continuation request; the feature was implemented in a clean
managed detached worktree at 5cc88cb to preserve unrelated notes. No push was requested.

Local commit reference: the commit containing this report, subject
`feat(lp): expose original-row duals and verify optimality`, parent 5cc88cb. Resolve
the exact hash via git log on this report path; the final reply records its hash.
Integrate that single commit into primary main by fast-forward only after confirming
its tracked HEAD is unchanged; verify note hashes and an original-path runtime smoke.
Expected primary state: only those five original untracked notes, main ahead two
(`0 2`), push not_attempted, remote_sync_status dirty_worktree (untracked notes) with
local_ahead_origin. A clean managed worktree is not a claim that primary is clean.
The final chat response records the actual post-commit hash, integration and sync
verification rather than treating these expected states as already observed here.
