# Session 17 repository review — submission safety and lane closure

**Date:** 2026-10-25 UTC. **Scope:** documentation/site review only. No new hypothesis experiment, holdout fit, raster generation, submission-slot selection, or organizer upload was performed.

## Decision

**No current TIFF is approved for competition upload.** The only method lane present for the immediately preceding run is H40-1 continuation-height ridge migration (the frozen method paragraph in `knowledge/49_preregistration_H40-1_migration.md`). It already consumed its three-experiment budget. Its LOSFO spread gate and strict uniqueness gate failed; its 2026-10-25 raster is explicitly inspection-only. The older H36-1/H38-1 files are historical and do not satisfy the present request for a newly generated unique artifact. We must not relabel, copy, alter, or submit a failed or old file as a new unique submission.

This decision follows the owner’s duplicate-stop protocol and “Maximize P(Win)”: a format-valid raster that fails the scientific or uniqueness gate cannot be promoted. “Own the Outcome” required correcting a misleading site message discovered in review; it did not justify bypassing failed gates.

## High-score review — evidence boundary

The user’s list ranks the GEMSDOE32 `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` value `0.2778` highest among the named owner sites. That value remains **OWNER-REPORTED**, not **ORGANIZER-CONFIRMED**: the cross-site audit found no submission-page receipt or locally available score-linked TIFF for that artifact. The owner page’s prose describes catalogue-proximity pruning of a prior dotted base. The repo’s forensic record shows the same broad emission-hygiene lesson for earlier family artifacts, but it does not independently establish the exact 0.2778 TIFF’s construction or causally explain its score. A public score requires an organizer receipt and exact file association.

The prompt’s current-leader maxima `0.3195` and `0.4413` conflict. The available leaderboard evidence is a one-off 2026-10-03 observation, not a fresh verification. Neither value is asserted as current here. No external competition page was queried, no upload was attempted, and no organizer result was obtained.

Manual-review links: [GEMSDOE32 report](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html), [official leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), [competition overview](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [USGS GeoDAWN survey](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [GDR submission 1391](https://gdr.openei.org/submissions/1391), [USGS 3DEP catalog](https://data.usgs.gov/datacatalog/data/USGS:77ae0551-c61e-4979-aedd-d797abdcde0e), and [USGS multi-depth MT release](https://www.sciencebase.gov/catalog/item/62979746d34ec53d276c113b). These links are for review; direct current-page/data availability was not rechecked from this network-restricted run.

## Four future hypotheses, ranked qualitatively (not authorized for this lane)

The rankings are design priorities, **not numeric DTI projections**. No expected score gain is honestly estimable from the present evidence. The current checkout’s `data/` directory has only `manifest.json`; the prior H40-1 outputs and evidence are archived in the repository, but this does not restore the inputs for another model run. These directions are not proven globally novel across the owner’s other repositories; they are candidates for a future lane only after source-code and registry audits.

| Rank | Layers and target signature | Why potentially off-catalogue | Distinction from existing local work | Named non-fault mimic | Cost / obtainability gate |
|---:|---|---|---|---|---|
| 1 | GeoDAWN elevation and radiometric K/Th/U: paired, signed cross-scarp change points coherent along strike | Eroded or subtle fault scarps can retain a paired material/relief transition even when no crisp line or mapped trace remains | Tests joint signed flank contrasts; not simply static edge magnitude, edge coherence, Euler depth clusters, or catalogue-distance pruning. Existing structural-step code overlaps conceptually, so exact feature-level novelty must be established before preregistration | Paleoshoreline, alluvial-fan boundary, road/rail grade | Medium. Uses competition/GeoDAWN layers; pinned input rasters are absent from this checkout. Official GeoDAWN landing page is linked above; actual layer identity and data terms must be verified before use |
| 2 | USGS 3DEP 1 m DEM plus TMI/gravity edge orientation: multi-basin drainage-divide asymmetry reversals aligned across a candidate structure | Distributed tilting around a concealed normal fault may deflect drainage without a sharp preserved scarp | Hydrologic network response across basins, unlike local DEM derivatives/scarp detectors and unlike H40-1 subsurface edge migration | Lithology-controlled erosion or stream capture | High. The official 3DEP catalog is linked above, but tile coverage/downloadability for the footprint was not verified this turn; unavailable until enumerated and hash-pinned |
| 3 | USGS Great Basin heat-flow residual + GDR 1391 2 m temperature probes: spatially coherent thermal residual intersecting a geophysical lineament | Conductive heat anomalies above buried permeable faults can occur without mapped surface rupture | Not the previously tested surface vent/wellspring point-process conjunction (H35-1); this is a measured subsurface thermal field plus a depth-probe residual. H35-2/H33-3 is queued but locally unrun | Groundwater recharge/discharge, lithologic thermal-conductivity contrast | Medium–high. Official ScienceBase DOI `10.5066/P9BZPVUC` and GDR 1391 are named in existing provenance records; exact co-registered derivative/probe availability needs a fresh audit before fitting |
| 4 | USGS multi-depth MT conductance slices + gravity: depth-coherent lateral conductance-boundary migration | A buried fluid-bearing structure can persist beneath conductive basin fill and lack a surface scarp | Tests boundary migration with depth, distinct from absolute surface conductivity and from an existing queued MT pipe-alignment hypothesis; local novelty is therefore especially uncertain | Clay-rich basin margin, evaporite or saline sediment | High. Official USGS ScienceBase item is linked above. Earlier repo evidence records byte-verification of five rasters, but current direct availability and licence were not rechecked; treat as blocked pending revalidation |

No direction above was fitted this turn. A new assigned lane must choose exactly one; apply the feature-alone AUC canary first, then the shared hide-and-recover evaluator with whole-segment buffering, visible-only catalogue features, pixel-exact visible-fault masks, pooled DTI (α=0.2, β=0.8; 300 m triangular kernel), paired 95% CI, and pre-/post-placement registry correlation and 3 px overlap tests. Do not spend a weekly slot without a positive predeclared gate and selector decision.

## Defect found and repaired

The top-level notice correctly warned that H40-1 failed, but then suggested that a user submitting “anything” use the historical H36-1 all-finite TIFF. That could be mistaken for current authorization even though H36-1 is an old reference, is unscored, and has no current selector approval. The executive summary also called an unapproved old file the suggested TIFF. This was inconsistent with the stated gate and user’s request to make it obvious whether download/submission is allowed.

The shared generator now states **NO FILE APPROVED**, labels H40-1 and H36-1 as inspection-only, distinguishes format compatibility from scientific/selector approval, and changes the executive-summary checklist to say not to select a current file. The discrepancy is logged as `submission-ui-mixed-disposition-2026-10-25` in `registry/irregularities.json`. The legacy downloads remain in place for audit; they are not deleted or silently re-pointed.

## Three review passes

### Pass 1 — implement and verify

- Updated `scripts/build_site.py`, then rebuilt all six pages; the build used local JSON only and reported `external_requests: 0`.
- Corrected the current status, historical artifact description, executive summary, and manual checklist.
- Added regression assertions in `tests/test_site.py` to require the explicit no-approval message and reject the former “if you submit anything” recommendation.
- Recomputed SHA-256 for both existing H40-1 variants with Python’s standard library: NaN-outside `2b32f81dcb734c51fe7b67da5b58123668ee6d614abe119a6d0dfbd23ccd7c0f`; all-finite `93abd1dbd2b06961eeafb25dbb428848d15d3c5e36ab9505d165f150fc9e9316`. These match `evidence/s16_run_card.json`. They are pre-existing failed artifacts; none was regenerated.

### Pass 2 — bugs, assumptions, and edge cases

- Full test suite after adding the new assertions: **317 passed, 7 skipped**. The first run revealed one overly exact test-string expectation; it was corrected to test the actual message, and the full suite then passed.
- The first full-repo Ruff invocation found three unused-variable findings in `scripts/build_unique_submission.py` and `scripts/evaluate_unique_holdout.py`. Removed the dead `order` calculation and `pooled_cand_n` assignment, and renamed the unused loop key `_fid`; these changes do not affect candidate ordering or holdout calculations. Full-repository Ruff now passes, with the complete test suite rerun after the fixes.
- `git diff --check`: pass. All site pages contain the no-approval status; Overview and Executive Summary no longer recommend the older TIFF.
- Edge case retained: “all-finite” means values meet the strict range validator; it does not fix a failed holdout, duplicate placement, input provenance, or missing selector approval.

### Pass 3 — original request reconciliation

- **New unique submission TIFF:** not produced. H40-1 already used all 3/3 experiments and failed G2 spread and uniqueness; creating a fourth arm or changing the raster would violate the protocol. Existing H40-1 TIFFs are not promoted, and old H36-1/H38-1 files are not represented as new submissions.
- **HOLDOUT-DTI evidence (existing Session 16 run only):** LOSFO evaluator, seeds 300–304, 81,101 withheld truth pixels, pooled ΔDTI `+0.001261`, paired 95% CI `[-0.003369, +0.006334]`; G2 spread failed (9/20 cells, 1/4 fold means). Single-feature AUCs were 0.489–0.535 (no canary breach), but this cannot rescue the failed gate.
- **Uniqueness (existing H40-1 run):** the recorded surface correlation is Spearman(prob_D1, prob_D0) = `0.9903`; it is not explicitly a per-registry surface comparison, and the run card does not retain that required per-registry pre-placement table. Final-dot overlap is measured: `91.27%` lie within 3 px of registry probe `52a13184267e`, exceeding `70%`. That alone establishes a duplicate-stop failure; the missing surface-vs-registry comparison is also a reporting gap.
- **Raster validator (existing H40-1 bytes):** sidecar/run card reports single-band float32, no NaN inside footprint, values `{0,1}` in `[0,1]`, CRS `EPSG:32611`, shape `3730×3292`, 100 m transform matching the template. SHA-256s were independently recomputed above. Format passes do not make the file upload-eligible.
- **Site instruction:** a user can now tell immediately: no file is approved. Submission is manual-only; no human-inspector gate is used in place of the automated research gates, and no DrivenData upload or score query was attempted.

## Remaining limitations / next work

1. No qualifying TIFF exists. Do not represent any file as ready until a future preregistered candidate clears the science, uniqueness, and actual-byte gates and a separate selector approves it.
2. Current checkout has no training rasters or prepared feature cache; only `data/manifest.json`. Owner mirrors remain unauthenticated. Revalidate official source access, licence, schema, and coverage before any new run.
3. The user’s stated `0.2778` score and two competing leaderboard maxima are not receipt-verified here. A submission-page receipt is required for organizer confirmation.
4. Exact raw H33-2 TIFF/code is absent, so the 0.2778 causal explanation remains bounded by the owner-page prose and prior family forensics.
5. `evaluate_holdout.py` and `submission_writer.py` are not the local filenames; the shared repo uses `run_losfo_harness.py`/`holdout.py` and `submission.py`. Do not fork tools; any evaluator defect must be fixed once in the shared template after its exact path/specification is established.
6. The official site, current leaderboard, competition cap, and external dataset endpoints were not accessed in this run. Manual-review links are supplied above. No automated login, fetching, scraping, submission, or monitoring is performed.
7. Full-repo lint still reports three older issues outside this change; see Pass 2. No fix was made to frozen model scripts.
