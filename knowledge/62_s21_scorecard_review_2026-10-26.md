# GEMSDOE28 executive scorecard and three-pass review — 2026-10-26

## Decision

**No GeoTIFF is approved to submit.** The newest previously generated candidate is available as a research artifact only:

- [Download S21-PUHGB all-finite GeoTIFF](../docs/downloads/gems28-s21-puhgb-20261026-16bbf281ba9b-allfinite.tif)
- **Disposition:** DO NOT SUBMIT. Prior local format validation passed, but the holdout superiority gate failed and 72.3% of final dots were within 3 px of one registry raster, crossing the requested duplicate stop. This is not a new submission recommendation.
- **MODEL PROJECTION, not a score:** 0.2195 (propagated range 0.1969–0.2419). It is the unverified 0.2778 anchor multiplied by a local holdout-DTI ratio; the range propagates a local paired-delta interval and is not a calibrated leaderboard confidence interval or organizer result.
- **HOLDOUT-DTI:** 0.083912 (95% CI [0.067020, 0.103244]); 35,900 pooled withheld positives; evaluator was `gems27.metric.dti_binary` in a quadrant component-hide 20% protocol, seeds 350–352. Paired delta vs dotted-b2 was -0.022298 (95% CI [-0.030924, -0.013741]). This older local protocol is not the strict shared `gems-segment-pooled-v1` requested for a fresh experiment.
- Raster SHA-256: `2bf4737ae0a3b844a160d4041d435e5a7daf92c6ec92f128a0c2c596ba23787c`.
- Name: `GEMSDOE28-S21-PUHGB-20261026-16bbf281ba9b`.
- Note: `S21 PU-HGB 31-band fresh 37654d b2 HOLDOUT 0.0839 vs 0.1062 NEGATIVE DO NOT SUBMIT` (82 characters).

The summary page is built at [docs/cross-site-review.html](../docs/cross-site-review.html); the machine-readable inputs are [the site scorecard](../docs/data/priority_site_review_2026-10-26.json), [the S21-PUHGB run card](../evidence/s21_puhgb_run_card.json), and [the archive audit](../evidence/s21_download_audit.json), and [the fresh S22 preflight](../evidence/s22_preflight.json).

## Nine-site executive table

The site table includes the exact historical artifact name, an immutable commit-pinned download, the value supplied in the owner prompt, and the scope of known novelty evidence. The historical values are **USER-REPORTED / UNVERIFIED**, not estimates independently produced here and not organizer-confirmed receipts. “NOT CERTIFIED” means the complete duplicate rule was not demonstrated; it must not be read as a uniqueness pass.

| Site | Highest value supplied | Historical artifact | Known uniqueness finding |
|---|---:|---|---|
| GEMSDOE24 | 0.2477 | `gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif` | Not certified against the complete registry |
| GEMSDOE25 | 0.2600 | `gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif` | Not unique: exact in-footprint equality with GEMSDOE30 d=2.8 |
| GEMSDOE27 | 0.2449 | `gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif` | Not certified against the complete registry |
| GEMSDOE28 | 0.2710 | `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif` | Not certified for this exact selected H36-1 artifact |
| GEMSDOE30 | 0.2600 | `gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif` | Not unique: exact in-footprint equality with GEMSDOE25 d=2.8 |
| GEMSDOE31 | 0.2708 | `gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif` | Not unique: H27-4 solo raster is reported identical to GEMSDOE28 H27-4 solo |
| GEMSDOE32 | **0.2778** | `gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif` | Not unique: its 37,654 dots are a subset of GEMSDOE28 solo; exceeds 70% stop |
| GEMSDOE33 | 0.2632 | `GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif` | Not certified against the complete registry |
| GEMSDOE36 | 0.2750 | `gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif` | Not unique: 37,654/38,854 dots (96.9%) exactly overlap GEMSDOE32 |

The committed page exposes direct artifact links. The raw source paths and commits are in the JSON scorecard. These are owner repositories, not primary competition evidence; no submission-page receipt was inspected in this review.

## Why 0.2778 may be higher

The archived forensic record says the 37,654-pixel H33-2-B2 set is produced by removing 2,545 catalogue-adjacent points from a 40,199-dot solo set, with no new points. Under a proximity-tolerant Tversky-style score, deleting predictions that provide little withheld-fault credit can reduce false-positive cost while nearby dots retain kernel credit. That is a plausible emission-efficiency explanation, **not proof of hidden-fault recovery or of the 0.2778 score association**. It is also not a distinct geology model. The score-to-file association remains unverified and this raster is a learning reference only; copying it or a near-identical pruning derivative would fail the user's novelty rule.

The competing leaderboard maxima quoted in the request (0.3195 and 0.4413) conflict. The repository records a dated 2026-10-25 public observation of 0.4413, but that is neither a current page check nor a receipt for one of these TIFFs. No leaderboard comparison was used as a score estimate.

## Three review passes

### Pass 1 — implement

Made the nine-site review a data-driven static-page table. Each row now identifies the artifact, owner-reported value (clearly marked unverified), commit-pinned download, and evidence-bounded uniqueness result. Added the S21-PUHGB research-only download, holdout result, conditional model projection, and failed-uniqueness warning at the top of the scorecard. Added references to the latest archive audit and review.

### Pass 2 — challenge assumptions and edge cases

Reviewed the historic duplicate cases and did not label missing comparisons as unique. Treated a score projection as a projection, not a score. Kept the 0.2778 entry non-submittable even though it is the largest supplied value. Confirmed the current archive audit remains failed: **12 of 44 TIFFs are not registered**. That is an audit completeness failure, not proof that the 12 files have invalid raster values. The S21-PUHGB file passes format checks in its historical run card but fails both science and the strict dot-proximity rule. No new experiment was launched. The shared evaluator/writer/validator/registry assets were restored from the pinned GitHub mirror and all nine SHA-256/byte pins now pass. The fresh S22 preflight (`evidence/s22_preflight.json`) still blocks experiments because the explicit lane, complete synchronized registry, comparable frozen baseline, and prepared cached feature array are absent.

### Pass 3 — verification

Rebuilt the static site and ran all tests: **542 passed, 6 skipped, 18 subtests passed**. Ruff passed on modified Python files; `git diff --check` passed. Six skips and seven Rasterio deprecation warnings are retained; no warnings were suppressed. No organizer, competition, or official external-data endpoint was queried in this review. No submission slot was selected.

## Ranked research directions already on record; not authorized for execution here

The earlier S21 prospectus ranks patch-based U-Net segmentation above further dot-emission variants, and lists radiometric alteration signatures as a separate avenue. Those concepts still need frozen lane authorization, compatible cached data, leakage canaries, full pre-placement novelty screening, and strict shared buffered holdouts. Do not call them viable on the current checkout: the required cache and full registry are absent. External data ideas must have obtainable, official free source bytes verified before being called actionable.

## Next steps and limitations

1. Resolve all 12 unregistered-download entries with independently captured exact bytes, SHA-256, grid/range/mask results, provenance, and an explicit research-only or submission-artifact status. Do not manufacture missing score/name/note metadata.
2. Restore and verify the shared cached feature stack; do not rebuild a private substitute under the reuse requirement.
3. Obtain a complete synchronized parallel registry, an explicit lane assignment, and a frozen best evaluated with the same strict protocol before another scientific experiment.
4. Recheck official rules/leaderboard and exact score receipts through a legitimate authenticated process; this repository has no DrivenData login or portal receipt access, and must not automate login or upload.
5. Only a separate selector may decide whether a fully gate-passing candidate can consume a weekly slot. The current result is **no-go**.

Official manual-review links retained in the source ledger: [competition problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), [reference solution](https://github.com/drivendataorg/gems-prize-reference-solution), and [USGS GeoDAWN data page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and). These links were not freshly accessed in this review.
