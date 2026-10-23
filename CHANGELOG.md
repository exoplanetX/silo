# Changelog

## 0.2.0a2 - Unreleased local correctness revision

- Removed feasibility tolerances from both MILP objective-bound pruning tests.
- Finite-pool CG now adds every exact negative reduced-cost column and requires
  an original-binary feasible primal/dual pair with equal objectives over the full
  declared pool before optimal termination. Proofs share the existing limits;
  failed proofs retain incumbents without a finite full-pool bound.
- Preserved mathematically integral MPS values across equivalent decimal forms;
  rejected nonzero direct/derived underflow and retained compatible roundtrips.
- Added frozen repair regressions, a repeatable seed20261024 independent audit,
  and isolated Windows Python3.11/3.13 wheel/sdist candidate checks.
- This local candidate preserves the original A/B/C/D/E research status and the
  existing numerical support limits. No public release or remote CI is implied.

## 0.2.0a1 - Unreleased local candidate

- Added the unified general-form LP/MILP API and optimize CLI, strict JSON/free-MPS,
  reversible transformations, original-space recovery and explicit termination reasons.
- Added real scaling, activity propagation, cached QR primal/dual simplex, general
  LP edits/reoptimization and bounded exact original-data proofs.
- Added conservative MIP frontier bounds/gaps/limits, deterministic search,
  bounded heuristics, verified node-local GMI cuts and proof traces.
- Added controlled research strategies and finite-pool general CG with explicit
  Phase I and complete-pricing termination; preserved earlier convex-combination APIs.
- Added an optional SciPy/HiGHS comparison adapter, frozen independent validation,
  source-independent installation checks, prospective CI and four learning units.
- Preserved the separate A/B/C/D/E research status and parked native Phase 9.
  Local artifact/platform results are in the prototype report; no public release date.

## 0.1.0 - Unreleased

- Initialized SILO project scaffold.
- Added Python package structure.
- Added documentation, notes, and task roadmap.
- Added educational tableau/revised LP paths, conservative presolve, and minimal MIP branch-and-bound.
- Added independent small-instance correctness checks and original-row LP dual/optimality evidence.
- Established the development companion learning series with stable lesson identities.
- Consolidated current project navigation, generated task/report index, and structural checks;
  preserved historical contracts and file paths. Version 0.1.0 remains unreleased.
- Preserved pricing research notes/probes with pinned input provenance, portable
  bounded reproduction and a verified local backup of original evidence.
