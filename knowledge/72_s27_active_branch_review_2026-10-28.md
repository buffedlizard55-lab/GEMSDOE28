# S27 — active-branch repository review (2026-10-28 UTC)

**Branch:** `arena/265e6e24-gemsdoe28`  
**Disposition:** negative, review-only. No model experiment, candidate surface, new dots, or new TIF was generated. No slot was selected. The current downloadable research TIFF is an older S25 experiment and is explicitly **not OK to submit**.

- Run card: [`evidence/s27_run_card.json`](../evidence/s27_run_card.json)
- Fresh blocked preflight: [`evidence/s27_preflight.json`](../evidence/s27_preflight.json)
- Fresh fail-closed exact-file audit: [`evidence/s27_download_audit.json`](../evidence/s27_download_audit.json)
- Existing ranked four-hypothesis slate: [`registry/s26_hypotheses.json`](../registry/s26_hypotheses.json)
- Nine-site historical scorecard: [`evidence/s23_scorecard.json`](../evidence/s23_scorecard.json)
- Nine-site pairwise geometry: [`evidence/s24_nine_site_overlap.json`](../evidence/s24_nine_site_overlap.json)

## Executive decision

**There is no new TIFF that is approved to download and submit.** Do not submit an archived file under a new name. This conclusion is deliberate: the mandatory experiment gates fail closed, and emitting an unvalidated raster merely to satisfy the request to produce a file would violate the uniqueness and high-score requirements.

The current checkout has no `data/sample_submission.tif`, `data/labels.tif`, prepared feature cache, or materialized pinned shared evaluator/writer. The exact download audit fails for missing sample/labels; the experiment preflight is blocked for the absent lane assignment, synchronized cross-run registry, frozen same-protocol best, cache/shared assets, and expired prior authorization clock. The declared 37,654-dot budget also fails the documented literal any-registry overlap counting bound. These are measured checkout/configuration facts, not assertions that the project can never proceed.

A previous S25 PCSE TIFF is present at [`docs/downloads/gems28-s25-pcse-scarp-energy-k37654-20261028-4af5ddbb4b50-nan.tif`](../docs/downloads/gems28-s25-pcse-scarp-energy-k37654-20261028-4af5ddbb4b50-nan.tif). Its current basic Rasterio inspection confirms one float32 band, shape 3730×3292, EPSG:32611, transform `[100,0,243350,0,-100,4508550]`, 5,167,373 mask cells, finite in-mask values in [0,1], and NaN outside. SHA-256 is `c6d722971070f6624a9b2a374c2858db46137f64dcd74805f160ba13f179edef`. This does not replace the failed exact validator because the sample template and labels are absent. It is research/audit material only.

Its prior result is **HOLDOUT-DTI (gems-segment-pooled-v1)** = 0.0450361, 60,988 withheld positive pixels, 95% CI [0.0380288, 0.0525190]. The same-fold random-K control is **HOLDOUT-DTI (gems-segment-pooled-v1)** = 0.0698748, 95% CI [0.0666809, 0.0731446]; paired candidate-minus-control difference = −0.0248386, 95% CI [−0.0324090, −0.0169181]. This is inherited S25 evidence, not a new S27 result, and it is not a leaderboard score. It is a negative reason not to submit the file.

## Nine requested sites: what is best, and can it be projected?

All supplied scores in this table are **USER-REPORTED / UNVERIFIED**. The source-pinned geometry comparison was performed in prior repository audits over the nine named historical artifacts. It found all 72 directional pair comparisons exceed the specified 70% within-3-pixel threshold; consequently none of these historical files is unique against the other eight under that rule. This is a finite, dated nine-artifact comparison, not a complete synchronized registry of every parallel site. Score estimates are **Unavailable**, not zero: no validated calibration maps this catalogue-based holdout to the hidden leaderboard.

| Site | Highest supplied claim | Historical artifact identified by prior audit | Estimate | Unique vs other eight? | Decision |
|---|---:|---|---|---|---|
| GEMSDOE24 | 0.2477 | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif` | Unavailable | No | Do not submit |
| GEMSDOE25 | 0.2600 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif` | Unavailable | No | Do not submit |
| GEMSDOE27 | 0.2449 | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif` | Unavailable | No | Do not submit |
| GEMSDOE28 | 0.2710 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif` | Unavailable | No | Do not submit |
| GEMSDOE30 | 0.2600 | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | Unavailable | No | Do not submit |
| GEMSDOE31 | 0.2708 | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif` | Unavailable | No | Do not submit |
| GEMSDOE32 | 0.2778 | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | Unavailable | No | Highest supplied claim; do not submit as a new unique method |
| GEMSDOE33 | 0.2632 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | Unavailable | No | Do not submit |
| GEMSDOE36 | 0.2750 | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | Unavailable | No | Do not submit |

Exact filenames and pinned GitHub source commits are recorded in `evidence/s23_scorecard.json` and `evidence/s23_focus_novelty.json`. In this checkout those remote artifacts were not downloaded anew during S27. Links in the executive summary are retained for manual review, not proof of fresh availability or organizer score receipts.

### GEMSDOE32's 0.2778 claim: the strongest defensible explanation

Prior repository forensics describe H33-2-B2 as an emission-pruning variant of the H27-4 solo pattern, rather than an independently trained geological detector: the recorded construction removes 2,545 catalogue-adjacent dots from a 40,199-dot parent to leave 37,654 dots. The exact H33-2 TIF bytes are not present in this checkout, so S27 did not independently reproduce that construction. Treat the geometry description as an inherited historical audit claim and the 0.2778 association as user-supplied, not organizer-confirmed.

The repo's local DTI implementation is distance tolerant: at 100 m per pixel, its 300 m triangular kernel reaches three pixels, and `src/gems27/metric.py` defines `DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw + eps)`. A prediction near already-covered truth may add little TP credit but still contribute FP mass; pruning such a redundant prediction can raise DTI. Conversely, pruning a pixel that uniquely covers a missed fault increases the FN penalty. Thus selective pruning is a plausible explanation of a score increase without new fault discovery, but it is not established as the cause here: exact organizer receipt, hidden labels, and an independently reproduced evaluation are unavailable. There is no defensible numerical forecast above 0.2778 from the available evidence.

## Untried hypotheses already ranked before implementation

The latest repository slate is [`registry/s26_hypotheses.json`](../registry/s26_hypotheses.json). S27 reuses it rather than inventing a new slate or implementing outside the stated lane. Expected DTI gains are unknown for every idea; ordering is qualitative priority, not a numeric forecast.

1. **S26-TCB — two-sided directional texture-covariance boundary** (top actionable candidate). Layers: existing competition `rtp`, `tmi_hg`, `cond_surf`. Target: a cross-boundary directional semivariogram/covariance or anisotropy discontinuity after side-specific mean removal. Rationale: a fault damage/alteration zone may alter spatial texture while broad field amplitudes cancel, potentially exposing a catalogue-missing structure. Difference: the source inventory lists edge/gradient, Hessian/vesselness, texture/context classifiers, and graph methods, but no two-sided directional covariance-change operator. Mimics: depositional facies, intrusive contacts, survey leveling seams, and resampling. Cost: medium-high. No external layer is required, but the local feature cache is absent. Not run.
2. **S26-MCR — spatially cross-fitted conductivity residual margins.** Layers: `cond_surf`, `depth_to_base_surf`, `det_elev`, `det_elev_slope`. Target: spatially blocked conditional-quantile residuals of conductivity given depth/terrain, testing coherent residual margins as possible concealed alteration. Difference: distinct from raw conductivity edges and existing clay-cap/dilation interactions. Mimics: saline groundwater, lacustrine clay, irrigation return flow, and EM investigation-depth changes. Cost: medium. Existing competition bands only; local cache absent. Not run.
3. **S26-HFR2M — heat-flow residual × independent shallow-temperature conjunction.** Layers: USGS Great Basin well heat-flow residuals, DOE GDR #1391 INGENIOUS 2 m temperature probes, plus competition conductivity/depth. Target: spatially supported thermal corroboration, not a vent label. Mimics: warm aquifers, groundwater discharge, and uneven sampling. Cost: high. Specific free/public source links are listed below, but raw bytes are absent and those hosts were not obtainable in this runtime; not viable for this holdout run.
4. **S26-DNT — drainage-network displacement and knickpoint trains.** Layer: challenge-area USGS 3DEP 1 m bare-earth DEM, contrasted with existing LiDAR descriptors. Target: channel offsets, beheaded streams, wind gaps, and aligned knickpoints. Difference: hydrologic network topology, not terrain-amplitude scarp scoring. Mimics: lithologic resistance, landslides, artificial channels, roads/culverts, and DEM artifacts. Cost: very high. Official 3DEP sources are linked below, but challenge-specific tiles are absent and source access was unavailable here; not viable for this holdout run.

Before any authorized candidate test: individual feature leakage canaries first (AUC >0.90 is leakage until resolved); compare surface rank correlation before placement and emitted dots after placement against a complete synchronized registry; then use the shared, buffered whole-segment hide-and-recover evaluator with fold-visible catalogue features only, exact visible-fault masking, pooled DTI (alpha 0.2, beta 0.8, triangular 300 m kernel), plus the shared writer. No private fork, registry-hole optimization, budget changes, or submission slot selection. Promotion belongs to a separate selector.

## Verification passes and irregularities

**Pass 1 — repository review:** confirmed active branch, latest report, user-listed sites, existing hypotheses, archived candidate and historical run-card results. Reproduced the basic raster metadata/range/mask inspection and SHA-256 match for the archived S25 TIFF.

**Pass 2 — gates and edge cases:** fresh `scripts/check_run_preflight.py` returned `BLOCKED` (exit 1); fresh `scripts/verify_downloads.py` returned `FAIL inputs_readable` (exit 1), because `data/sample_submission.tif` and `data/labels.tif` are missing. These are expected safety failures, not successful TIFF authorization. The exact grid/catalogue match therefore remains unverified in this checkout. No holdout or canary was run. Full software suite: 662 passed, 7 skipped, 12 warnings, 9 subtests; all seven skips are data-dependent, not scientific validation. Ruff passed; `git diff --check` passed.

**Pass 3 — original requirements:** no new TIF, score projection, organizer confirmation, holdout result, novelty pass, or upload approval is claimed. The existing S25 TIF remains download-for-research only and `ok_to_submit=false`. The evidence includes prior labeled HOLDOUT-DTI only to prevent its confusion with the current zero-experiment review.

**Irregularities / limits:**

- The prompt gives conflicting leaderboard anchors (0.3195 and 0.4413). Older repository notes contain still other dated public observations. No current DrivenData leaderboard was fetched in S27; all three must remain unverified and time-scoped.
- The 0.2778 H33-2-B2 number is user-reported, not tied here to an organizer receipt. Do not reverse-engineer certainty from the score alone.
- The nine-file geometry registry is historical and incomplete for parallel/private/unpublished outputs. It is sufficient to reject these known files under the requested nine-site comparison, not certify any new candidate.
- S27's preflight config is an earlier session's authorization and its two-hour clock is expired. Resetting it, assigning a method lane, or declaring a complete registry without provenance would falsely authorize experiments.
- Current non-GitHub official source content was not freshly retrieved. The links below are for review; they are not a claim of current availability/content verification.
- Build/test tooling is available through the ignored `.venv`; required large input rasters and shared template assets are absent. No DrivenData login, submission portal, current weekly limit, or receipt is accessible from this checkout.

## Trusted-source links retained for review

- [Competition overview and rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Problem description, metric, and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Official reference solution on GitHub](https://github.com/drivendataorg/gems-prize-reference-solution)
- [Leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — not queried in S27
- [USGS GeoDAWN data](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [USGS Great Basin heat-flow data, ScienceBase DOI 10.5066/P9BZPVUC](https://www.sciencebase.gov/catalog/item/6297d2fad34ec53d276c5b28)
- [DOE GDR INGENIOUS submission 1391](https://gdr.openei.org/submissions/1391)
- [USGS 3DEP program](https://www.usgs.gov/3d-elevation-program) · [1 m DEM collection catalog](https://data.usgs.gov/datacatalog/data/USGS:77ae0551-c61e-4979-aedd-d797abdcde0e)
- [EPSG:32611](https://epsg.io/32611)

## Next work, in order

1. Obtain a new explicit lane assignment and authorized experiment clock; do not edit the stale S23 preflight config to imply approval.
2. Restore inputs and the pinned shared evaluator/writer to ignored data paths from provenance-pinned sources; verify exact hashes and resolve the `labels.tif`/`existing_faults.tif` hash identity before trusting them as distinct products.
3. Build a genuinely synchronized cross-lane registry and the strict frozen comparable best on the same holdout protocol. Resolve the novelty-rule/budget incompatibility via an explicit protocol-level decision, not ad hoc dot placement.
4. Only then run S26-TCB under the three-experiment/two-hour limit, first with per-feature leakage canaries, then buffered whole-segment holdout, and surface/final-dot novelty checks. Stop on failure; do not select a slot in the experiment step.
5. Independently refresh leaderboard and submission instructions through authorized user access; record a file-bound organizer receipt only if the user actually submits and provides the receipt.
