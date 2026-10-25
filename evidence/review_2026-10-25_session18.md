# Repository review — 2026-10-25 (Session 18)

## Executive finding

**Negative / blocked. No submission-ready TIFF exists or was generated in this review.** The user prompt does not specify one exclusive method paragraph as the parallel-run lane; the checked-out `data/` directory contains only `manifest.json`, not the feature stack or prepared cache. The extant run card records no lane and no experiment. Selecting one of the old H39/H40/H38 methods, rebuilding an old raster, or renaming it would violate the lane/uniqueness requirements. No organizer upload or external competition request was made.

## Highest-priority findings and actions

### P0 — site contained a direct contradiction about submission readiness (fixed)

The generated landing page said **NO FILE APPROVED**, while the executive summary's Session 17 one-click block said “Yes, to download,” called H38-1 a unique submission generated this session, and linked a TIFF. The index status table also marked H36-1/H38-1 “OK to download” while separately describing them as unscored/not slot-approved. H38-1's own current check was negative (see its recorded small-sample holdout result in `evidence/holdout_compare_gems28-h38-1_vs-h36-1_2026-10-25.json`), and its 97.5% overlap with a dense probe is above the 70% stop threshold. Those facts do not support a current download/submission recommendation.

**Fix:** the shared HTML generator now renders a single fail-closed “NO APPROVED TIFF — DO NOT SUBMIT” notice on overview and executive summary, removes the historical H36/H38 “OK to download” selection table, and reports that the current run is blocked. Historical files remain available only in explicitly marked audit/inspection panels. Build metadata now reports `submission_ready: false` and `slot_selected: false`; it no longer labels the historical manifest primary as a current `primary_download`. Regression tests prohibit the former affirmative H38 wording.

### P1 — required holdout protocol is not fully satisfied by current shared evaluators (unresolved, disclosed)

- `src/gems27/holdout.py::make_split` calls `hide_components(labels & fm, ...)`. Because the catalogue is clipped to one quadrant **before** connected components are identified, a continuous fault crossing a quadrant boundary can be split into separate pieces. `known = labels & ~hidden` removes only selected pixels; it does not remove a buffer around the withheld piece. This is not whole-fault-segment-with-buffer evaluation.
- `src/gems27/losfo.py` does group dilated fault systems and removes a buffer from the training labels, but its module-level “Known limits” explicitly says feature rasters are **not** re-derived with held-out systems removed. Catalogue-derived feature bands can therefore retain held-out catalogue information unless they are excluded or recomputed from visible faults.
- The task requires whole-segment buffering, visible-fault-only catalogue features, pixel-exact masks, pooled DTI (`alpha=0.2`, `beta=0.8`, 300 m triangular kernel), feature-alone canaries, and withheld-positive counts/95% CI. No evaluator meeting all those conditions was run here. Historical numbers must not be relabeled as compliant HOLDOUT-DTI for the new protocol.

**Action:** do not patch a private fork or spend a slot. The requested shared template repository/path is not present in this checkout. The correct next change is a shared-template repair, reviewed and tested there, followed by rerunning the locked baselines. The absence is recorded, not silently papered over.

### P2 — local science data are absent

`ls data` shows only the tracked `data/manifest.json`; the competition rasters and `data_cache` are absent. The manifest marks its raster records as owner-mirrored, not organizer-authenticated. Running the downloader would restore those mirror bytes, not establish official provenance. We did not attempt a multi-hundred-megabyte restore after establishing that no lane was assigned.

### P3 — historical review and test health

- `python scripts/build_site.py`: PASS; six static pages generated from local records, with no external requests.
- `.venv/bin/python -m pytest -q`: **317 passed, 7 skipped**.
- `.venv/bin/ruff check src scripts tests`: PASS.
- `git diff --check`: PASS.
- Tests passing does not establish source provenance, scientific validation, organizer acceptance, or current submission eligibility.
- GitHub accepted the branch push but warned that existing tracked file `docs/data/sb_slip_tendency_in_footprint.json` is 59.10 MB (above GitHub's recommended 50 MB). The file was not created or modified by this review; it should be evaluated for Git LFS/release/external storage in a separate change, preserving its hash and provenance.

## Ranked hypotheses for a future explicitly assigned lane

These are **design candidates**, not measurements, projected competition scores, or slot recommendations. “Expected improvement” is ordinal judgment based on mechanism and previous negative results; numerical ΔDTI is deliberately not forecast. All candidates remain blocked until the official/shared feature inputs, lane, and evaluator are available. The repository records fuller prior source/provenance limitations in `knowledge/47_parallel_run_audit_2026-10-25.md` and `knowledge/47_s15_hypotheses_and_preregistration_H39-1.md`.

| Rank | Candidate / cost | Specific layers and physical signature | Why it might find an uncatalogued fault | Difference from local work; named mimic | Data/official-source gate |
|---:|---|---|---|---|---|
| 1 | **Paired signed relief–radiometric change points** / medium | `det_elev` plus GeoDAWN K/Th/U or ratios; along-strike detrended, paired cross-structure flank contrasts, requiring coherent sign and persistence rather than raw edge strength | Eroded or covered faults may preserve coupled relief/material boundaries despite lacking a crisp USGS/INGENIOUS trace | Distinct from single-channel edge magnitude and the existing Euler/topology features, but H32 structural-step concepts overlap and require a code-level novelty check. Mimics: alluvial-fan boundary, paleoshoreline, road cut, lithologic contact | Proposed bands are named in the owner stack / GeoDAWN records, but are not present locally. Official GeoDAWN manual-review source: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and . Direct download and current licence/coverage not re-verified here; blocked pending source-byte/schema audit. |
| 2 | **Radiometric alteration lineaments as objects** / low–medium | GeoDAWN Th/K and U/Th ratios; multi-scale Hessian ridge/lineament extraction with a minimum along-strike continuity and independent relief or potential-field orientation agreement | Hydrothermal alteration may persist along a buried permeable structure without a surface fault scarp | Ratio images have appeared as pixel-level model covariates, but lineament extraction and object-level spatial tests are not documented as implemented locally. Mimics: felsic lithology boundaries, playa K enrichment, flight-line striping | Official GeoDAWN source above; ratio rasters in local runtime absent and mirrored derivative provenance is owner-supplied. Not viable until official data access/terms and feature identity are checked. |
| 3 | **Multi-basin drainage asymmetry reversals aligned to an independent edge** / high | USGS 3DEP 1 m DEM where available, drainage divides/channel profiles, plus a magnetic or gravity edge; test coherent basin-scale asymmetry/knickpoint polarity across several catchments | Distributed tilting can warp drainage across a concealed normal fault without a preserved scarp | Different scale/observable from pixel scarp detectors; queued 1 m drainage ideas exist in older hypothesis records, so this is not globally or repository-wide novel absent a full code/registry audit. Mimics: lithology-controlled erosion, stream capture, climatic gradients | Official 3DEP source: https://www.usgs.gov/3d-elevation-program . Owner manifest lists 716 tile links but does not prove current source coverage or obtainability; must verify tile-by-tile before proposing as executable. |
| 4 | **Depth-coherent MT conductance-boundary migration plus gravity corroboration** / high | USGS multi-depth MT conductance slices and gravity; follow boundary migration across depth rather than thresholding absolute conductance | A buried fluid-bearing fault may cut basin cover and have no Quaternary surface trace | Different observable than surface scarp/radiometric ridges; earlier records already queue a related H38-5 “pipe alignment,” so near-duplicate risk is material. Mimic: clay-rich basin margin or evaporitic/saline sediment | Official USGS record cited in prior registry: https://doi.org/10.5066/P9TWT2LU . Exact item, bytes, grid, licence, and coverage were not verified obtainable in this review; explicitly blocked. |

**Selection rule:** do not execute any of the four just because it ranks first. An authorized lane must name one method; then audit every registry raster before placement, run feature-alone AUC canaries, and use the repaired shared holdout evaluator. Stop on any surface correlation above 0.90 or >70% of dots within 3 px of any registry raster. Only a positive paired holdout confidence interval and actual-byte validator can advance to the separate selector.

## Score attribution and scientific interpretation

- `0.2778` for H33-H33-2-B2 is **OWNER-REPORTED** from the prompt/repository-page audit, not **ORGANIZER-CONFIRMED**: no submission-page receipt was found in this checkout. The documented forensic explanation is plausible as an emission-hygiene/pruning mechanism, but it does not prove causal score attribution or justify copying its raster.
- The competing `0.4413` and `0.3195` leaderboard figures are conflicting and not refreshed/receipt-verified in this review.
- Historical local holdout figures from this repository are not competition scores. Because the current holdout protocol has the deficiencies above, they are not upgraded here to compliant metrics for the requested protocol.

## Three-pass review

### Pass 1 — inspect and repair

Reviewed README, source, generated pages, manifests, run cards, evaluator documentation, site tests, and data inventory. Found the contradictory affirmative H38 download recommendation. Replaced it with an explicit blocked/no-TIFF state in the source generator and updated test assertions. No candidate raster, slot, or science claim was created.

### Pass 2 — defect and edge-case pass

Checked each rendered-page role: overview, executive summary, historical candidate panels, and build JSON. Added regression assertions against “Yes, to download,” “OK TO DOWNLOAD,” and “unique submission generated this session.” Examined both component holdout and LOSFO logic. Confirmed the first lacks whole-component-before-quadrant assignment and buffering; LOSFO buffers labels but documents feature-derived leakage limitations. Left shared scientific code untouched because the named shared template is unavailable.

### Pass 3 — request reconciliation and verification

Rebuilt static pages; ran all tests and Ruff; checked whitespace; verified `data/` has only the manifest. No TIF was generated, because the lane and data blockers make any new raster noncompliant rather than useful. The current negative run card remains the machine-readable result; no weekly slot was touched.

## One JSON run card

```json
{
  "hypothesis": "No assigned method lane; current run blocked before experiment",
  "mechanism": "No geological model or raster built; fail-closed repository review only",
  "named_non_fault_process_that_could_mimic_it": "Not applicable to a no-experiment run; future paired relief/radiometric candidate mimics include paleoshorelines, alluvial boundaries, and lithologic contacts",
  "holdout_dti": {
    "label": "HOLDOUT-DTI",
    "evaluator_version": null,
    "withheld_positives": null,
    "ci95": null,
    "result": null
  },
  "registry_correlation_overlap": {
    "result": null,
    "reason": "No candidate surface or final dots generated; no complete registry rasters in local data"
  },
  "raster_sha256": null,
  "validator": {
    "no_nan_inside_footprint": null,
    "values_in_0_1": null,
    "crs_shape_transform_match": null,
    "result": "not applicable; no TIFF generated"
  },
  "submission_name": null,
  "note": "Blocked: no assigned lane or local feature cache; no TIFF generated",
  "verdict": "negative",
  "experiments_run": 0,
  "slot_selected": false,
  "submission_ready": false
}
```

## Remaining work / limitations

1. Specify exactly one method paragraph/lane and the canonical shared-template repository/path.
2. Repair the shared evaluator to preserve whole segments across spatial folds, apply the required buffer, recompute catalogue-derived channels using visible faults only, and verify pixel-exact masks. Add regression fixtures at fold boundaries.
3. Restore/hash-pin competition rasters and template only after lane assignment; distinguish owner mirrors from organizer-authenticated files.
4. Build a full numerical raster registry for GEMSDOE24/25/27/28/30/31/32/33/36; page/tree metadata alone is not enough to calculate the required correlations and 3-px overlaps.
5. Freeze candidate and baseline, perform feature-alone canaries and the compliant paired holdout, and report evaluator version, withheld positives, segment-level uncertainty, and paired 95% CI.
6. Independently validate actual candidate bytes, then stop for the separate selector; do not upload automatically.
