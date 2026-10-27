# GEMSDOE28 checkout review — 2026-10-27 UTC

## Decision

**No new TIFF exists. OK to download as a new submission: NO. OK to submit: NO. No weekly slot selected or spent. No geological experiment or new HOLDOUT-DTI was run.** This is an automated, fail-closed disposition, not a request for manual geological inspection.

The S23 scientific stop remains in force: the inherited 37,654-dot lane fails the literal registry overlap rule; there is no explicit method-lane assignment, complete synchronized global registry, or frozen comparable strict-protocol best. The supplied 0.2778 (GEMSDOE32) and competing leaderboard anchors are user-reported claims, not organizer-confirmed receipts. The score cause and prospect of exceeding it are **unknown**. Do not turn a model ratio, a historical local holdout, or file-format validity into a score estimate.

## Pass 1 — inventory and reproduce current authority

- Read the S23 read-first summary and standing requirements in `README.md`, the executive page, `knowledge/66_s23_preregistration.md`, `knowledge/67_s23_result.md`, `registry/s23_hypotheses.json`, the run card and the current S23 evidence.
- Confirmed the nine-site page covers **GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33 and GEMSDOE36**. The highest values shown are explicitly user-reported/unverified, the hidden-score estimate is unavailable, all nine historical bests fail the supplied uniqueness rule, and the page recommends no upload. The page distinguishes format checks from novelty and competition acceptance.
- Confirmed S23's recorded geometry result is `DUPLICATE_STOP`; the preserved report gives a ≥82.3418% overlap lower bound for the 37,654-dot budget and an actual inherited final-dot overlap of 99.6176% against one registered raster. Those are **GEOMETRY-AUDIT** values, not DTI or competition scores. They reject this lane/budget; they do not prove every conceivable smaller budget impossible.
- Confirmed four preregistered hypotheses are ranked in `knowledge/66_s23_preregistration.md`. None was implemented or validated. Their expected DTI improvement is unknown; the 1 m DEM proposal is explicitly unavailable without original official tile bytes.
- No new source-content verification was claimed. The report's official-source ledger documents the scope and freshness limits.

## Pass 2 — independent checkout checks and irregularities

This active checkout is branch `arena/bbe00948-gemsdoe28`, while frozen S23 metadata in `registry/current_session.json` and `knowledge/66_s23_preregistration.md` identifies `arena/a774f0a0-gemsdoe28`. These historical records were not silently edited because their hashes are bound by the frozen run card. This is a **branch-provenance metadata mismatch** to carry forward; it does not establish that any score or raster is wrong.

This checkout has no competition rasters, prepared feature cache, or materialized pinned shared-template files under ignored `data/`. The local, read-only replay commands therefore fail closed:

- `scripts/check_run_preflight.py` → **BLOCKED**; missing lane assignment, complete external registry, comparable best, `data/prepared/features.json`, and all nine materialized shared-template assets.
- `scripts/audit_registry_feasibility.py` → **BLOCKED** because the shared-template assets are not materialized here. This does not reverse the prior pinned S23 geometry finding; it means the geometry replay was not independently reproducible from this checkout alone.
- `scripts/verify_downloads.py` → **FAIL** because `data/sample_submission.tif` and `data/labels.tif` are absent. It approves no file.

The checkout contains prior byte-pinned audit records and historical downloads, but no newly generated TIFF. Do not use those old records to imply current local inputs or a fresh holdout. Existing optional input restoration previously stopped at a GitHub REST rate limit; this review did not repeat that network request or claim the optional inputs were restored.

## Pass 3 — tests and final consistency

Installed repository development requirements into ignored `.venv/` only. No dependency payload or training data was added to Git.

- `.venv/bin/python -m pytest -q` → **641 passed, 6 skipped, 12 warnings, 9 subtests passed**. The six skips are input-dependent tests; missing raster/table inputs remain unavailable. Twelve are Rasterio affine deprecation warnings. This is a software result, not a scientific result.
- `.venv/bin/ruff check src scripts tests` → **PASS** (`All checks passed!`).
- `python -S scripts/build_site.py` → **PASS**, generated 18 static pages from local JSON only, made zero external requests, reports `submission_ready: false`, and has no recommended research download.
- The generated build left the tracked working tree unchanged before this review note was added.
- No run-card claim, historical evidence, TIFF, score, or submission manifest was rewritten.

## User-facing interpretation

The GEMSDOE32 `0.2778` entry is the highest of the supplied focus-site claims, but only as reported in the prompt. Repository forensics documented the construction as the GEMSDOE31 solo dot set minus 2,545 catalogue-adjacent dots. Reduced redundant predictions are a plausible mechanism for an emission-style DTI improvement, not a proven explanation of an organizer score. The site cannot estimate a credible leaderboard score without an organizer-confirmed, file-bound score and a calibrated transfer relationship. The site's literal duplicate rule independently rejects all nine historical bests as new unique files.

No copy, rename, relocation, repackaging, or retagging of a historical raster was used. The portal's earlier `[0,1]` error cause remains unknown. No local TIF has passed all current gates, so the recommendation is unambiguously **DO NOT DOWNLOAD OR SUBMIT A NEW TIFF** (none is offered).

## Next work, gated and ordered

1. Preserve the literal registry rule. Resolve its dense calibration-control conflict in a shared, versioned protocol; do not hide the control or tune predictions into its uncovered cells.
2. Re-materialize and hash-verify the pinned shared tools, official/owner-mirror inputs and cached feature stack in a reproducible workspace. Clearly distinguish owner mirrors from organizer-authenticated data; do not claim source authenticity from matching mirror hashes alone.
3. Obtain a single explicit method paragraph/assignment, a synchronized complete registry, and a frozen comparable baseline evaluated under the strict buffered whole-segment, visible-only, pooled DTI protocol.
4. Only if the novelty/preflight gates permit it, select one preregistered viable hypothesis. Run every feature-alone leakage canary; compare its surface before placement and final dots to every registry raster; report HOLDOUT-DTI with evaluator version, withheld positives and 95% CI. A score estimate remains unavailable absent calibration.
5. A separate selector—not the research run—must check current authenticated weekly allowance and organizer submission receipt. Keep all slots untouched until then.

**Core values:** maximize P(Win) by protecting scarce submission slots from invalid novelty and unsupported projections; own the outcome by keeping negative evidence, blocked checks and provenance mismatches visible.
