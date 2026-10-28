# S25 — active-checkout repository review (2026-10-28 UTC)

## Outcome

**NO TIFF generated · NOT OK TO DOWNLOAD/SUBMIT · no experiment or slot.** This was a read-only audit on `arena/b74b9587-gemsdoe28` at `4955e29`. The standing S24/S23 evidence remains the source of scientific conclusions; this review did not refresh historical scores or treat them as measured validation.

The requested lane is not unambiguously assigned in the active protocol, the synchronized full registry and strict comparable best are absent, and the ignored feature stack/shared-template dependencies are not present in this checkout. The prior S24 preflight already recorded these fail-closed conditions. Local state confirms `data/` contains only run-card/manifest JSON and `shared_template/` is absent. No TIFF is approved. GEMSDOE32's user-supplied 0.2778 remains **USER-REPORTED / UNVERIFIED**; no prediction of hidden leaderboard score is supported.

## Checks performed

1. Read the README standing brief and S24/S23 disposition first; inspected current branch/status, code/test inventory, run cards, preflight evidence, and submission readiness claims.
2. `python -S scripts/build_site.py`: **exit 0**, deterministic JSON-only build, 19 pages, 43 source records, zero external requests, and `submission_ready: false`. The build rewrote six tracked HTML pages, removing prior active-checkout overlay sections. Those generated changes were restored immediately. This is a workflow hazard: rebuilding the site alone can drop review overlays; run the documented overlay build afterwards or update the build workflow to preserve/regenerate them.
3. `git diff --check`: **pass** before build; final check below. `python -m pytest -q`: **not run** because the runtime Python has no `pytest` installed. `python scripts/check_run_preflight.py`: **not run to completion** because NumPy is absent (`ModuleNotFoundError`). These are environment limitations, not passing test/preflight results. Prior S24 suite results (652 passed, 6 skipped) apply to its different checkout/runtime only and are not re-certified here.
4. `git status` was clean before checks; generated page edits were restored. No code, raster, data or evidence artifact has been modified by this review.

## Review findings / priorities

- **P0 — scientific work remains blocked:** restore hash-pinned cache and shared tools; supply one explicit lane, synchronized registry including parallel artifacts, and a frozen comparator validated under the same protocol. Keep the literal surface and dot novelty checks. Do not sidestep dense-registry overlap by tuning a placement budget.
- **P1 — execution reproducibility:** provision project dependencies in a disposable environment and rerun unit tests, lint, preflight, and required data-dependent tests; record each as pass/fail/blocked. Do not interpret absent-input skips as successful scientific validation.
- **P1 — site build overlay hazard:** `build_site.py` rewrites tracked pages and strips independently injected active-checkout sections. Make the canonical build invoke/compose `build_active_review.py`, or document and test the required build order. Do not commit regenerated pages until the overlay state is restored and reviewed.
- **P2 — score provenance:** keep supplied scores labeled user-reported until a filename/SHA-bound organizer receipt is available; no score estimate is defensible absent a validated transfer calibration.

## Final decision

No new hypothesis was evaluated, no feature canary or HOLDOUT-DTI was produced, and no raster hash or validator result exists for a new submission. **Verdict: negative/blocked; zero experiments; zero slots.** This is not a claim that no higher-scoring model can exist; it is a statement that this checkout cannot responsibly test or certify one under the required gates.
