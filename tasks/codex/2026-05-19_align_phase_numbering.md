# Codex Task: Align SILO Phase Numbering

## Goal

Make SILO phase numbering consistent across documentation, task files, and code comments/messages.

Use the following canonical phase sequence:

- Phase 0: Project Scaffold
- Phase 1: Model Core and Canonicalization
- Phase 2: Tableau Simplex
- Phase 3: Revised Simplex and Basis Reoptimization
- Phase 4: Presolve, Scaling, and Numerical Diagnostics
- Phase 5: MIP Branch-and-Bound
- Phase 6: Cut Generation and Callbacks
- Phase 7: Decomposition Layer
- Phase 8: Stochastic and Robust Optimization Extensions
- Phase 9: Native Backend

## Scope

1. Keep `ROADMAP.md` as the canonical numbering source.
2. Update `README.md` so its long-term roadmap includes Phase 0 through Phase 9 with the same meanings as `ROADMAP.md`.
3. Rename the phase task files under `tasks/` so filenames match the canonical phase numbers.
4. Update task-file headings to match the canonical phase titles.
5. Add missing task files for the decomposition layer and native backend if they are absent.
6. Update code messages or documentation references that point to the wrong phase number.
7. Leave the ignored source prompt `tasks/createproject.md` unchanged.

## Do Not Do

Do not implement simplex, MIP, cuts, decomposition, stochastic/robust transformations, or native code in this cleanup. Do not change the Apache-2.0 `LICENSE`. Do not commit or push unless explicitly asked.

## Verification

Run:

```bash
pytest
python -m ruff check src tests examples scripts
```

Then search for phase references and confirm that only intentional references remain.
