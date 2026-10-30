# S30 — repository review, hypotheses, and submission gate — 2026-10-30 UTC

**Branch:** `arena/6aaf0523-gemsdoe28`

**Decision:** **NO NEW TIFF · NO FILE APPROVED · OK TO DOWNLOAD AND SUBMIT: NO · NO WEEKLY SLOT SELECTED**

This is the current checkout’s review, not a geological experiment. I did not copy, rename, or re-label an older raster as a new submission. I did not query DrivenData or upload anything. A prior S29 research GeoTIFF exists in the repository, but its internal holdout was negative; it remains research-only.

## Executive summary

The user-supplied `0.2778` for GEMSDOE32 is the largest historical claim among the nine selected sites, but it is **USER-REPORTED / UNVERIFIED**, not an organizer receipt, not a local HOLDOUT-DTI, and not a calibrated estimate of a new file’s hidden score. A prior pixel-forensic record finds that the 37,654-dot GEMSDOE32 artifact is exactly the GEMSDOE31 H27-4 solo placement after removing 2,545 dots within two pixels of the mapped catalogue, with no additions. This makes a selective-pruning/coverage-efficiency explanation plausible. It does **not** show that those removed pixels were false positives on the hidden labels or prove why the reported score changed. In the metric implementation (`src/gems27/metric.py`), false negatives receive the larger weight (beta 0.8 vs. alpha 0.2); pruning can therefore help only if the loss in weighted true-positive coverage is outweighed by the reduction in false-positive mass. The hidden evaluation is unavailable here, so causation and a numerical forecast are not identifiable.

**There is no defensible numerical leaderboard-score estimate for any row.** The 0.3195 and 0.4413 leaderboard anchors in the prompt conflict, and this checkout did not fetch the current leaderboard. Do not convert a holdout DTI to a projected leaderboard score. The historical claim column below is not an estimate.

## Nine-site executive table

“Historical claim” reproduces the prompt; each is **USER-REPORTED / UNVERIFIED**. The audit snapshot/file links point to pinned owner-repository mirrors, not authenticated competition downloads or score receipts. The inherited exact geometry audit evaluated 72 ordered pairs among these nine selected rasters; every selected raster exceeded the requested 70% within-3-pixel overlap rule against at least one other selected raster. This is **not** a complete synchronized registry audit. The Spearman value shown is for the peer that maximized the displayed overlap; it is not claimed to be the maximum correlation against every possible registry member.

| Site | Historical artifact snapshot (audit/learning only) | Supplied claim | Leaderboard estimate | Unique among the other eight? | File to download for S30 / submit? |
|---|---|---:|---|---|---|
| GEMSDOE24 | [`gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/f4d5a5ef3f3cf6cbe5a24ee0b29c6d592910d308/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif) | 0.2477 · USER-REPORTED / UNVERIFIED | Unavailable | **No** · 100.00% within 3 px of GEMSDOE25 | **None · NO** |
| GEMSDOE25 | [`gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/889d93dcde5bbc5812b2d68c5de830a8d8dc61a1/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif) | 0.2600 · USER-REPORTED / UNVERIFIED | Unavailable | **No** · 100.00% within 3 px of GEMSDOE24 | **None · NO** |
| GEMSDOE27 | [`gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/378151fa3a0d3c5bb58fec6b88dbf461df193a4e/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif) | 0.2449 · USER-REPORTED / UNVERIFIED | Unavailable | **No** · 98.02% within 3 px of GEMSDOE24; displayed-peer Spearman 0.9896 | **None · NO** |
| GEMSDOE28 | [`gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/b500c9af13c8917085f83264d6ccb763a2cd1f6f/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif) | 0.2710 · USER-REPORTED / UNVERIFIED | Unavailable | **No** · 100.00% within 3 px of GEMSDOE24 | **None · NO** |
| GEMSDOE30 | [`gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif`](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/7b12a5a7368e263d465784165fc02b6d8f35453d/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) | 0.2600 · USER-REPORTED / UNVERIFIED | Unavailable | **No** · 100.00% within 3 px of GEMSDOE24 | **None · NO** |
| GEMSDOE31 | [`gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/4d3bc5c8db9fb5f7dfa3d21e0d696ffe40005e52/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif) | 0.2708 · USER-REPORTED / UNVERIFIED | Unavailable | **No** · 100.00% within 3 px of GEMSDOE24 | **None · NO** |
| GEMSDOE32 | [`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/148a9148e77456ad1acc7d1735d38ed1e558cc03/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) | 0.2778 · USER-REPORTED / UNVERIFIED | Unavailable | **No** · 100.00% within 3 px of GEMSDOE24 | **None · NO** |
| GEMSDOE33 | [`GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif`](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/3eaf85efb49f364b84f8be04e8b084b12d0303b9/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) | 0.2632 · USER-REPORTED / UNVERIFIED | Unavailable | **No** · 99.71% within 3 px of GEMSDOE27 | **None · NO** |
| GEMSDOE36 | [`gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/e280188adbbe762e6b7ac6f3b8e105e8e7915026/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) | 0.2750 · USER-REPORTED / UNVERIFIED | Unavailable | **No** · 97.58% within 3 px of GEMSDOE27 | **None · NO** |

The exact row-level hashes, format flags, overlap values and source URLs are recorded in [`evidence/s30_scorecard.json`](../evidence/s30_scorecard.json), derived from [`evidence/s28_focus_novelty.json`](../evidence/s28_focus_novelty.json), an inherited audit observed 2026-10-29. GEMSDOE31’s selected all-finite mirror failed two inherited format checks (`outside_footprint_is_nan`, `masked_read_in_0_1`); a historical claim is not proof that this exact mirror variant earned that score.

## Why the GEMSDOE32 claim may be higher

The inherited forensic comparison (`evidence/s15_champion_forensic.json`) reports:

- The GEMSDOE32 / `e5eb6e7e` 37,654-dot set equals the GEMSDOE31 H27-4 solo set minus exactly 2,545 dots whose catalogue distance is at most 2 pixels; there are no added dots.
- The historical user-reported values differ by +0.0070 (0.2708 to 0.2778). This is a comparison of claims, not an organizer-confirmed experiment.
- At 100 m cells, the competition distance-tolerant score uses a 300 m triangular kernel and the local metric source defines `DTI = TPw / (TPw + 0.2 FPw + 0.8 FNw)`. A plausible mechanism is removal of redundant/low-marginal-credit points while retaining useful kernel coverage. However, false-negative mass has the larger coefficient, so pruning is beneficial only if its change in weighted FP/TP/coverage improves the ratio. The hidden truth is unavailable; the causal explanation is **not proven**.
- The GEMSDOE32 dot set is not a novel strategy under the requested uniqueness rule relative to the other eight selected site rasters. The inherited audit records 100% within 3 px of GEMSDOE24.

No score extrapolation is made. The prior catalogue-based holdout is not the hidden organizer test, the user-reported live scores have no file-bound receipt, and this checkout has no validated calibration from holdout DTI to leaderboard DTI.

## Ranked hypotheses for a properly authorized future run

The slate below contains exact operators not found as complete implemented/tested holdout methods in the inspected local inventory. “Rank” is a qualitative hypothesis-priority ordering, not a measured DTI ordering. **Every expected DTI delta is unknown.** The single assigned method paragraph referenced by the parallel-run instruction is absent, so none is selected or authorized in S30. The first proposal needs only the competition feature stack in principle; that stack is absent here. The external-data proposals are explicitly marked not viable until raw bytes, coverage and provenance can be verified.

| Rank | Hypothesis | Layers and physical signature | Why it could find a catalogue-missing fault | Difference from inspected repo work | Non-fault mimic | Expected DTI / cost / source gate |
|---:|---|---|---|---|---|---|
| 1 | **MCR — conductivity residual margins** | `cond_surf`, `depth_to_base_surf`, `det_elev`, `det_elev_slope`; spatially cross-fit a conditional-quantile conductivity baseline, then detect coherent residual margins. | Fluid alteration in a concealed damage zone could produce a conductivity contrast that is unusual for local basin-depth and terrain context even without a mapped surface trace. | Distinct from raw-conductivity ranking, existing clay-cap margins/interactions and structural-step edges; no exact cross-fitted conditional-quantile residual operator was found. | Saline groundwater, lacustrine clay, irrigation return flow and changing EM investigation depth. | DTI change unknown; highest qualitative actionability. Medium cost; no new external data in principle, but feature cache/shared tools are absent. Official input entry point: [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/). |
| 2 | **HFR2M — independent heat-flow × 2 m probe conjunction** | USGS Great Basin conductive heat-flow residuals + DOE GDR #1391 2 m temperature probes + competition `cond_surf`/`depth_to_base_surf`; require supported co-location with an independent structural corridor. | A buried fluid conduit may create shallow thermal expression without a mapped scarp; two independent thermal sources reduce reliance on one noisy sample type. | Different from the repo’s separate heat-flow/Euler, thermal-site distance and well/spring plume work. Exact combination must be checked against all merged parallel work before implementation. | Groundwater discharge, warm aquifers, uneven well/probe sampling and non-tectonic circulation. | DTI change unknown; high cost. Specific official sources: [USGS ScienceBase heat-flow item](https://www.sciencebase.gov/catalog/item/6297d2fad34ec53d276c5b28) and [DOE GDR #1391](https://gdr.openei.org/submissions/1391). The bytes are not in this checkout; those hosts were not reachable under this runtime’s allowlist. Prior evidence of a past runner fetch is not a current check. **Not viable now.** |
| 3 | **RUDP — lithology-conditioned U/Th transport dipoles** | Official GeoDAWN K/eU/eTh radiometry + official lithology/SGMC units + independent potential-field corridor; measure signed, paired cross-corridor residual dipoles after conditioning on local lithology. | Hydrothermal redox/fluid transport could redistribute U/Th asymmetrically around a concealed permeable structure missed by a surface-fault catalogue. | Unlike scalar radiometric ratios or Th/K lineament scores, the hypothesized signal is an ordered lithology-conditioned residual dipole. No exact match was found in the inspected inventory; global novelty is not established. | Groundwater redox fronts, sediment sorting, lithologic contacts, radon disequilibrium and survey seams. | DTI change unknown; medium-high cost. Official links: [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [GeoDAWN ScienceBase item](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7), [USGS SGMC Nevada](https://mrdata.usgs.gov/geology/state/shp/NV.zip) and [California](https://mrdata.usgs.gov/geology/state/shp/CA.zip). SGMC sibling-runner pins are historical; exact bytes/product coverage were not re-fetched or re-verified in S30. **Not viable now.** |
| 4 | **DNT — drainage displacement and knickpoint-train topology** | Challenge-linked USGS 3DEP 1 m bare-earth DEM tiles + independent competition potential-field lineaments; target channel offsets, beheaded reaches, wind gaps and aligned knickpoint trains crossing a corridor. | Channel-network geometry may preserve displacement evidence after a low-relief scarp is diffused or buried; this is potential fault evidence, not direct geothermal evidence. | Existing LiDAR features emphasize pixelwise step, roughness, openness and relief. No flow-routing/channel-topology implementation was found in the inspected local code inventory. | Lithologic resistance, landslides, stream capture, artificial channels, roads/culverts and DEM artifacts. | DTI change unknown; very high cost. Official sources: [USGS 3DEP](https://www.usgs.gov/3d-elevation-program) and [1 m DEM catalog record](https://data.usgs.gov/datacatalog/data/USGS:77ae0551-c61e-4979-aedd-d797abdcde0e). No challenge-specific tile manifest/bytes are present or freshly obtainable here. **Not viable now.** |

These ideas are planning proposals. An official landing page or a prior data-fetch record does not prove current access, correct footprint, license, or complete coverage. Before any experiment, verify the exact source files and metadata; otherwise keep the candidate blocked.

## Why no experiment or fresh TIFF was run

The automated preflight was actually run at `2026-10-30T22:52:57Z` and failed closed (`evidence/s30_preflight.json`). It records:

1. No explicit assigned method lane or assignment source.
2. No complete synchronized parallel-run registry; the repository records a prior geometry result that warns the literal overlap rule blocks the declared budget. Do not tune around the lattice/control holes.
3. No frozen, same-protocol HOLDOUT-DTI comparator.
4. The inherited two-hour clock began at `2026-10-27T17:12:00Z`; the preflight observed 279,657 seconds elapsed, exceeding 7,200 seconds. It was not reset.
5. `data/prepared/features.npy` and its metadata are absent.
6. All nine pinned shared-template assets are absent, including `evaluate_holdout.py`, `submission_writer.py`, the evaluator/metric/validator and shared registry.
7. `data/sample_submission.tif` and `data/labels.tif` are absent. The exact-file audit (`evidence/s30_download_audit.json`) failed before examining any candidate.

The inherited `registry/current_session.json` is an S23 configuration on branch `arena/a774f0a0-gemsdoe28`, with `lane: null`, missing registry/baseline fields and an expired timer. It was not rewritten to make this S30 session look authorized. The absence of these prerequisites, plus the absent lane, means there is no valid HOLDOUT-DTI to report and no legitimate basis to emit a new submission file. S30 used zero experiments and zero slots.

### Existing S29 research TIFF: inspect, do not submit

`docs/candidates/gems29-s29-hole-k20000-20261029-b68117a828cc-nan.tif` already exists. This review did not generate or copy it. A read-only local Rasterio inspection found SHA-256 `bcc92b8d8c5d81e095b9f4a7b73e2578e22fccf6fddb98c08a170c4089816cb3`; one float32 band; CRS EPSG:32611; shape 3730 × 3292; transform `(100, 0, 243350, 0, -100, 4508550)`; 20,000 one-valued cells; and finite values in [0,1]. Its finite/NaN counts match the **repository’s copied grid constants**, but the current official sample template is absent, so this is not a fresh exact-template check. Prior S29 evidence states it passed its hard validator and the 87-reference novelty gate (max 68% of dots within 3 px), but HOLDOUT-DTI was **0.02951796** (95% CI **0.02335114–0.03597472**, 60,988 withheld positives, evaluator `gems-segment-pooled-v1`), below its matched random-K HOLDOUT-DTI **0.03962040** and below the historical comparable best **0.0553736**. It is negative and **NOT OK TO DOWNLOAD AND SUBMIT**. See [`evidence/s30_archived_candidate_inspection.json`](../evidence/s30_archived_candidate_inspection.json) and [`evidence/s29_candidate_run_card.json`](../evidence/s29_candidate_run_card.json).

### The earlier “Predicted values must be in range [0, 1]” error

The exact organizer-side cause is not known. Historical local forensics (`evidence/range_validator_forensics_2026-10-03.json`) found 2,344,929 NaNs inside the owner-mirrored template footprint in one predecessor, which could fail an elementwise range check; its all-finite alternative had 625,805 positive predictions outside the mirrored footprint. This is a strong local explanation of why those two predecessor files were unsafe, **not a replay of the portal validator or proof of the portal’s internal implementation**. A new candidate would need all footprint cells finite and in [0,1], one float32 band, exact template CRS/shape/transform, and a correct outside-mask convention, verified with the pinned shared writer/validator against the exact sample template. S30 could not perform that final check because the template and labels are absent.

## Automated submission instructions (no human geological inspection)

The project’s scientific inspection is machine-validated; no human inspector is a substitute for the required holdout. A future file must be promoted only after all gates pass, then a separate selector may authorize it within the account’s verified weekly allowance. For an authorized file only:

1. Use the exact approved `.tif` (or a `.zip` containing only that one GeoTIFF). Do not choose a historical research artifact.
2. Before publishing a download button, run the pinned shared writer and validator on the exact file and sample template: one float32 band; CRS, dimensions and geotransform equal the template; every footprint prediction finite and in `[0,1]`; no infinities; outside-footprint mask follows the competition format; record SHA-256.
3. Run feature-alone leakage canaries (AUC > 0.90 blocks reliance until disproven), then buffered whole-segment hide-and-recover. Derive catalogue-dependent features from visible faults only, mask visible fault pixels exactly, pool HOLDOUT-DTI with alpha 0.2, beta 0.8 and the 300 m triangular kernel, and report evaluator version, withheld-positive count and 95% CI.
4. Apply surface correlation/overlap before placement and final-dot overlap afterward against the complete synchronized registry. Stop if absolute rank-correlation exceeds 0.90 or over 70% of candidate dots are within 3 px of any registry raster. A negative result stays negative; it must not be renamed to look unique.
5. Only after a positive same-protocol holdout, novelty, format and separate selector decision may the page display an enabled one-click TIFF download, unique submission name and note no longer than 140 characters.
6. In the DrivenData New submission form, select that exact file, enter the short note, and submit. This project has no DrivenData login/receipt in this checkout. An organizer receipt bound to the raster SHA-256 is the only basis to label a score `ORGANIZER-CONFIRMED`.

**S30 page state:** button disabled; no current file/name; no submission estimate; **OK TO DOWNLOAD AND SUBMIT: NO**. The static executive summary is [`docs/s30-review.html`](../docs/s30-review.html), linked from the site entry pages.

## Official-source links and verification status

The URLs below are included for manual review. They were supplied in the prompt or already recorded in repository source ledgers. **Non-GitHub official hosts were not contacted in this S30 runtime** because they are outside its outbound network allowlist. Their inclusion is not a claim of a fresh 2026-10-30 availability check.

- [DrivenData competition problem and format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/)
- [DrivenData data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/) — the competition data were previously documented as login-gated; no credentials or data were accessed here.
- [DrivenData leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — not freshly checked in S30.
- [Official DOE/NLR competition rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Official DrivenData reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN data description](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE GDR/INGENIOUS submission #1391](https://gdr.openei.org/submissions/1391)
- [USGS Great Basin heat-flow ScienceBase item](https://www.sciencebase.gov/catalog/item/6297d2fad34ec53d276c5b28)
- [USGS 3DEP program](https://www.usgs.gov/3d-elevation-program) and [1 m DEM catalog record](https://data.usgs.gov/datacatalog/data/USGS:77ae0551-c61e-4979-aedd-d797abdcde0e)
- [EPSG:32611](https://epsg.io/32611)

## Three-pass review and software verification

- **Pass 1 — inspect and implement:** reviewed branch/status, README and historical decisions, current-session manifest, shared-template pin, input/cache presence, existing S29 candidate bytes, nine-site score/geometry evidence, static site builders, and submission/download workflow. Added S30 scorecard/run card, blocked preflight and exact-file audit, archived-artifact inspection, research summary and public fail-closed decision panel.
- **Pass 2 — review for bugs/assumptions:** kept all historical scores explicitly unverified; checked all nine rows and all 72 inherited pairwise comparisons; corrected GEMSDOE32 explanation to distinguish exact pixel reconstruction from unproven score causation; retained the DTI false-negative weight; marked the official leaderboard and non-GitHub source availability unverified; prevented a disabled download from linking to a TIFF; left S23/S29 historical configuration untouched.
- **Pass 3 — re-check against the request:** verified the exact active branch, valid JSON/≤140-character note, no new raster/name/slot, false submit flag, explicit holdout/validator `NOT RUN` fields, all four ranked hypotheses with physical signal/difference/mimic/cost/source gate, nine-site table, submission guide, current fail-closed page, and the exact reason new scientific testing was blocked. Fresh pytest/Ruff/site-build checks are recorded in [`evidence/s30_verification.json`](../evidence/s30_verification.json); the feature cache and template-dependent exact file audit remain blocked, not counted as passes.

### Remaining work, in order

1. Resolve the assigned single method lane and synchronized registry in the parallel-run coordination; do not infer or reset them.
2. Establish a fresh, explicit experiment authorization and an in-budget start time; freeze a same-protocol HOLDOUT-DTI comparator before touching a slot.
3. Restore the exact competition inputs and prepared feature stack plus hash-pinned shared evaluator/writer assets; verify every SHA-256 and provenance. Owner mirrors are not organizer-authenticated.
4. Rerun fail-closed preflight. If it passes, choose one preregistered local-data hypothesis and test its surface-only novelty and individual-feature leakage canaries before the shared holdout. Do not run any external-data proposal until the exact free official files, license, grid and coverage are verified obtainable.
5. Require a positive paired holdout against the frozen best, exact final novelty gate and exact template validator before a separate weekly selector. Only then expose a download and pursue a receipt-bound live score.

The historical public-feed workflow, code, and research inventory remain useful, but none can turn the current blocked state into submission approval. Maximize P(Win) and Own the Outcome mean preserving a trustworthy negative result rather than shipping an unvalidated TIFF.
