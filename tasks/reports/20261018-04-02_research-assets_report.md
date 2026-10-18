# Research Asset Preservation and Sync Closure — Execution Report

## Objective / baseline

One user-approved asset-preservation task with two immutable contract revisions. Revision 02 places the existing SciPy application reference under examples; revision 01's backup identity is retained. Primary baseline cd83009, live origin/main bdddf58, 0 1. The five untracked notes are the exact active ingestion artifacts. Git mode push-on-success, including cd83009. Learning delivery not applicable: archival ingestion only.

## Preservation / scope

Verified backup at E:/OneDrive/workspace/codex/silo-solver-backups/20261018-04-01_research-assets: 35 files, 1504344 bytes. Five original notes, five probes, five historical JSON, 16 pinned input files, their manifest and three resfs originals were byte-checked. All originals remain in their initial locations except canonical notes receive link-only edits after this backup. No OneDrive upload proof is claimed.

## Asset delivery / revisions

- Five notes/26..30 are versioned at their existing paths. Only declared local-source/
  result-link replacements were applied; byte comparison against the backed-up originals
  plus that exact replacement list confirms mathematical prose/formulas are unchanged.
- Four synthetic probes are preserved under scripts/research/pricing/probes; the
  fifth, using SciPy/HiGHS as an RMP reference, is under examples/research. All five
  files match original SHA-256 and byte counts; no mathematical source was rewritten.
- A source/provenance manifest records original source/results identities, canonical
  note links, the original session and the fixed input revision. The original input
  manifest preserves URLs, bytes and hashes for all 16 inputs, including source LICENSE.
- The runner changes only the in-memory top-level HERE assignment for the two probes
  that write adjacent files. It preserves the original __file__, asserts the recognized
  assignment shape/count, captures fresh run metadata and refuses output-directory reuse.
- Generated output, reference JSON, cached inputs and ignored historical originals are
  excluded from Git. The local backup preserves these original evidence files without
  publishing the historical discussion archive.
- Five exact archived files are excluded from Ruff style rewriting, while hash checking
  protects their original bytes. The maintained runner and other scripts remain linted.
  Project structure checking also invokes source-asset verification and covers asset links.
- Updated current profile, asset/directory guides and index distinguish current results
  from historical records. Prior contracts/reports, production code and lessons are preserved.
- Revision 01's prepared backup ID remains 20261018-04-01_research-assets. Revision 02
  corrects only application-reference placement to respect the existing external-solver
  boundary; its prose may show the new revision in a prospective backup path, but this
  task reuses and verifies the already-created revision-01 archive, as its revision
  boundary explicitly states. No second backup or second development objective is created.

## Actual verification

- Source verification passed for **5 byte-identical probes** and the pinned input manifest.
  All **16 input files** passed byte-count/hash checks. A missing LICENSE file was fetched
  explicitly from the fixed URL in a temporary fixture and matched the original bytes.
- Fresh theory, signature, frontier and locality outputs matched all four historical JSON
  objects exactly; their generated file SHA-256s also matched the original result hashes.
- Full bounded application execution completed successfully. Recursive comparison found
  exactly **3 differences**, all reference_total_seconds; every other key/value, including
  environment, parameters, numeric results and scope/status information, matched history.
  s2_t90 remains iteration_cap at 200 iterations; s6_t450 remains an explicit state-budget
  exceedance with full_graph_completed false. These are preserved limits, not convergence
  or complete-state-graph evidence. No speedup is inferred from rerun times.
- **9 deliberate failure controls** rejected source corruption, pinned-manifest corruption,
  escaped input paths, corrupt cached data, missing input without fetch, output path escape,
  existing output overwrite, nonpositive timeout and actual execution timeout. The timeout
  retained its failed run manifest. An initial diagnostic reader encountered Windows locale
  decoding noise on the expected existing-directory error; that case was rechecked with
  locale-tolerant capture, retaining the expected exit 1 and untouched marker.
- Structure check passed: **139 contracts, 136 reports, 94 production modules, 438 local
  links**. The counts include the two immutable revisions/handoff reports of this one task.
- Full python scripts/check_quality.py passed: **1364 tests in 8.24s**, followed by Ruff
  passing. Targeted maintained-script Ruff/format also passed. No production source/tests
  changed; the new execution wrapper was verified separately through the probe runs and
  failure controls, rather than counting the existing 1364 tests as wrapper coverage.
- Checked **19 changed/new Markdown documents** for valid UTF-8 and balanced fences.
  Canonical notes contain no .codex/visualizations paths. Existing decision-log contents
  remain an unchanged prefix; new disposition was appended.
- Reverified all 35 backup copies, total **1504344 bytes**, against their manifest. External
  probe/result/input originals and all resfs originals remain unchanged; original note
  bodies are available in backup. Only canonical note link substitutions differ.
- No src/tests/learning/phase records or preexisting contracts/reports changed.
  git diff --check passed; Git noted normal CRLF-to-LF handling for an edited document.
- Verified the exact staged Git blobs for all five original probes. The input manifest's
  CRLF line endings were normalized to LF for portable Git checkouts; its parsed entries
  are unchanged and both original/canonical byte hashes are preserved in provenance.
  Earlier run manifests reference the original manifest hash used at execution time.
- Exported a fresh directory directly from the staged Git index, without the external
  research originals or existing output cache. Its source/structure verification passed,
  and a fresh theory run reproduced the recorded result. This specifically checks that
  staged normalization, relative paths and archived-source hashes survive a new checkout.

Fresh outputs are under ignored outputs/research/pricing/20261018-04-02. Their manifests
record fresh UTC times, interpreter, source/runner/input hashes, exit codes and result
hashes. Original fixed date fields remain historical metadata. Python 3.13.9, NumPy 2.3.5,
SciPy 1.16.3 and pytest 8.4.2 were reused; no dependencies or environment settings changed.

## Old worktree disposition

lp-dual-evidence is clean at bb6baff, which is an ancestor of primary HEAD. The app's
attachment ownership check rejected this chat with "This worktree is owned by another
task." It is retained with its existing owner; no terminal workaround, deletion or
ownership change was attempted. The owning chat can archive it when it no longer needs
the checkout. This restriction does not affect source/asset preservation or GitHub sync.

## Git / Remote Sync Proof

Git mode push-on-success, explicitly requested by the user. Before task: main cd83009,
live/cached origin/main bdddf58, ahead/behind 0 1, and exactly five untracked research
notes (the active ingestion assets). One result commit will include the scoped assets
and this report, subject `chore: preserve research assets and reproduction provenance`,
parent cd83009. Its exact SHA is resolved via this report's Git history after commit.

Before commit: required checks above passed, explicit paths are staged and cached diff
checking is required. Push uses the existing origin/main, normal fast-forward only,
including the previously unpushed cd83009 commit. No global/repository proxy or TLS config
is changed; working command parameters remain invocation-local.

Expected final state after the subsequent push: clean main, local/tracked/live remote
HEAD equal, ahead/behind 0 0, remote_sync_status synchronized_with_origin. Actual push
and post-commit proof are reported in the final execution receipt; these expected fields
do not pretend the not-yet-created commit was already pushed before this report existed.

## Limits / next

This closes research-asset ingestion and the requested repository synchronization.
OneDrive upload was not checked, and ignored backups/results are not part of the GitHub
tree. The separate local backup path remains stated above. Old worktree retirement
remains under its other-chat owner; the ownership constraint is documented.
No solver phase, native path, mathematical claim or dependency policy was advanced.
The separately scoped revised Phase-I cleanup recommendation is unchanged and unexecuted.
