# Session 21 — independent validation review (2026-10-26)

## Executive decision

**DO NOT SUBMIT. No new TIFF generated, no experiment executed, no slot selected.**
The nine-site comparison remains [the existing executive scorecard](../docs/cross-site-review.html).
The listed GEMSDOE32 result is user-reported, not an organizer-confirmed receipt. There is no defensible leaderboard estimate for a new candidate in this session.

## Pass 1 — restore and reproduce

Read the standing README brief, prior-session results and next steps. Restored the four core competition mirror files (training stack, labels, existing faults, sample submission) through GitHub, checking registered SHA-256 and size. Restored all nine pinned shared-tool/registry assets using `restore_protocol_assets.py`. These are owner mirrors, not independent organizer authentication. Large inputs remain ignored, not committed. Installed dependencies in `.venv`.

Ran the independent archive audit against the restored grid. Found an actual coverage defect: the filename-only path was hardcoded to S18 and did not independently validate S19's filename-only TIFF. Replaced it with discovery of every filename-style manifest entry. Negative verdicts must still have `submission_ready: false`; schema discovery does not imply promotion.

## Pass 2 — challenge the green result

Added six synthetic regression cases for arbitrary future-session entries: valid file, last-cell out-of-range value, missing file, incorrect hash, overlength note and contradictory approval. Then checked whether every TIFF in the download directory was represented by a manifest record. **12 of 44 files were unregistered**, including S20-H43 and older research artifacts. Added an explicit coverage gate rather than silently claiming those files passed. The real audit now reports **FAIL: `all_tifs_registered_for_audit`** (488 checks). All other recorded checks pass. This is a coverage failure, not evidence the 12 files have invalid values. See [exact audit](../evidence/s21_download_audit.json) for their names.

## Pass 3 — protocol and user requirements

Re-ran preflight using a fresh UTC session configuration without overwriting historical registry settings. Shared assets now pass. Remaining blockers: missing assigned method paragraph, incomplete shared parallel registry, absent frozen same-protocol best, absent cached feature metadata/stack. No private evaluator fork, synthetic candidate, random perturbation, fabricated CI or fabricated score was introduced. No fresh official leaderboard/USGS/PDF observation was possible through the restricted host allowlist. Existing official reference links remain review links, not new verification.

No changes were made to the other eight repositories. This PR only governs GEMSDOE28. No claim of completing the requested cross-repository rollout or unique high-scoring TIFF is made.

## Ranked scientific work, not experiments or numerical predictions

The existing five-candidate slate is [knowledge/59](59_s20v_preregistration_and_hypotheses.md); vesselness was subsequently tried and rejected. The four remaining next-programme candidates below are **previously proposed, not newly discovered hypotheses**. Ordering is qualitative expected utility, not an estimated DTI gain. Local source review cannot establish novelty across all parallel repositories.

| Priority | Layers / physical signature | Missing-fault rationale and distinction | Non-fault mimic | Cost / feasibility |
|---|---|---|---|---|
| 1 | Cached 32-band stack; patch encoder-decoder spatial segmentation | Context may identify weak coherent scarps missed by pixelwise HGB; no trained CNN in the reviewed local pipeline | Roads, channels, mapping style | High; cache restoration and buffered training/validation required; no GPU verified |
| 2 | RTP/TMI and isostatic gravity; cross-corridor marker-displacement registration | Targets displacement of contacts, not contact gradient strength, potentially exposing concealed cross-cutting faults | Intrusive branching and survey seams | Medium–high; mirror layers available, cache prerequisite unmet |
| 3 | USGS ComCat hypocentres; oriented point-pair alignment | Illuminates blind active planes rather than smoothed earthquake density | Induced swarms and location-error streaks | Medium; official https://earthquake.usgs.gov/fdsnws/event/1/ outside allowed hosts, obtainability NOT verified; deferred |
| 4 | USGS 3DEP DEM; cross-catchment aligned knickpoints/chi disequilibrium | Network-scale uplift signal rather than local scarp morphology | Lithologic knickpoints, base-level changes | High; official https://www.usgs.gov/3d-elevation-program outside allowed hosts, tile obtainability NOT verified; deferred |

## Next session, dependency order

1. Register the 12 unmatched archive TIFFs with independently verified hashes, names, notes and provenance, or explicitly move their publication out of the submission archive. Do not invent metadata just to turn the audit green.
2. Restore the pinned prepared cache and derived inputs; do not rebuild privately. Synchronize the complete concurrent registry and obtain an explicit method lane; declare a frozen comparable baseline and fresh held-out segments.
3. Test feature-alone leakage canaries, surface uniqueness, then at most three experiments. Stop immediately on lane drift. Only emit and recommend a new file if paired holdout improvement, final-dot uniqueness and exact-grid/range validation all pass.
4. Separate selector checks current portal allowance. Bind any organizer receipt to the exact raster hash before calling a result ORGANIZER-CONFIRMED.

Core values: Maximize P(Win) by refusing unsupported promotion; Own the Outcome by fixing audit coverage rather than accepting a misleading green check.

Final verification: **541 passed, 5 skipped, 9 subtests passed**; targeted Ruff PASS, site rebuild PASS, `git diff --check` PASS. The five skipped tests retain their existing input/environment conditions. [JSON run card](../evidence/s21_run_card.json).
