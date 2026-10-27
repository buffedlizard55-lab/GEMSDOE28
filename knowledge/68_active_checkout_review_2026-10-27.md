# Active-checkout review — 2026-10-27 UTC

**Decision: NEGATIVE. No new TIFF exists. OK to download/submit a new file: NO.** This review was performed on `arena/d955c32f-gemsdoe28`; it does not overwrite or restate the earlier S23 session as if it were run on this branch. The machine-readable audit is [`evidence/active_checkout_review_2026-10-27.json`](../evidence/active_checkout_review_2026-10-27.json).

## Executive answer

The highest result in the supplied nine-site list is GEMSDOE32's `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`, **0.2778 USER-REPORTED / UNVERIFIED**. The pinned forensic record says the 37,654-dot raster exactly reconstructs as the 40,199-dot H27-4 solo raster minus 2,545 predictions within two catalogue pixels, adding no dots. This supports a *plausible emission-pruning / false-positive-mass explanation* for why the owner-reported metric could rise: pruning near known mapped traces can reduce redundant predictions without changing the underlying detector. It does **not** prove that pruning caused 0.2778, that the receipt belongs to those exact bytes, or that the result is organizer-confirmed. The hidden organizer labels and a file-bound receipt are unavailable here. More thinning alone is therefore not a scientifically established route to beating it; a new detector must earn spatially supported credit under a leakage-controlled buffered holdout.

**Can this project currently demonstrate a score above 0.2778? No.** This is an evidence limitation, not a claim that improvement is impossible. Available score numbers are not reliable forecasts of the hidden leaderboard. Every estimated leaderboard score in the nine-site scorecard is deliberately unavailable rather than fabricated.

## Priority-site table

Reported scores below are claims supplied in the task and preserved in the pinned scorecard. They are neither HOLDOUT-DTI measurements nor ORGANIZER-CONFIRMED results. Historical artifact links point to exact owner-repository commits for research/forensics, **not** a download recommendation. The 3-pixel overlap audit compares only the nine selected historical files, not the complete parallel-run registry.

| Site | Highest listed file (historical) | Supplied score | Estimated leaderboard score | Unique vs. the other eight? | New submission decision |
|---|---|---:|---:|---|---|
| GEMSDOE24 | [`gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE24/blob/2521cb676e172c141a4417e4925b73b6a896c1eb/docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif) | 0.2477 USER-REPORTED | Not estimable | No — 100.00% within 3 px of GEMSDOE25 | None; do not submit historical file |
| GEMSDOE25 | [`gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE25/blob/5a60fb475b7171af93cfce795abe6d96c4021ea2/docs/downloads/gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif) | 0.2600 USER-REPORTED | Not estimable | No — 100.00% within 3 px of GEMSDOE24 | None; do not submit historical file |
| GEMSDOE27 | [`gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE27/blob/4d39bbf92edd51fdf47004df5873793a035592e5/docs/downloads/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif) | 0.2449 USER-REPORTED | Not estimable | No — at least 86.72% within 3 px of GEMSDOE32 | None; do not submit historical file |
| GEMSDOE28 | [`gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE28/blob/67dbdf4da84fc92a98dd9644ab816ed18ae36bcc/docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif) | 0.2710 USER-REPORTED | Not estimable | No — 100.00% within 3 px of GEMSDOE24 | None; do not submit historical file |
| GEMSDOE30 | [`gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif`](https://github.com/buffedlizard55-lab/GEMSDOE30/blob/3c3d7255fdbb3a94375eff086522463a8eaca449/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif) | 0.2600 USER-REPORTED | Not estimable | No — 100.00% within 3 px of GEMSDOE24 | None; do not submit historical file |
| GEMSDOE31 | [`gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif`](https://github.com/buffedlizard55-lab/GEMSDOE31/blob/abd9a45cc7adf046d7d3829eb6e8c980943f462d/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif) | 0.2708 USER-REPORTED | Not estimable | No — 100.00% within 3 px of GEMSDOE24; historical format audit failed | None; do not submit historical file |
| GEMSDOE32 | [`gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/1398109a23f04a2ace71c1bd2f527cfba87860b5/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif) | 0.2778 USER-REPORTED | Not estimable | No — 100.00% within 3 px of GEMSDOE24 | None; educational/forensic reference only |
| GEMSDOE33 | [`GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif`](https://github.com/buffedlizard55-lab/GEMSDOE33/blob/122e2240a835c9c84831943ee3489dbb48fd6e85/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif) | 0.2632 USER-REPORTED | Not estimable | No — 99.71% within 3 px of GEMSDOE27 | None; do not submit historical file |
| GEMSDOE36 | [`gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif`](https://github.com/buffedlizard55-lab/GEMSDOE36/blob/61783525af4aa6dcf8da0bc68b06fa38b89ed27a/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif) | 0.2750 USER-REPORTED | Not estimable | No — 97.58% within 3 px of GEMSDOE27 | None; do not submit historical file |

The historical audit found all **72 directional comparisons** across these nine selected files over the 70% proximity threshold; maximum absolute Spearman rank correlation was 1.0. These are **GEOMETRY-AUDIT** findings, not scores. This limited set cannot establish uniqueness against unpublished or newly registered parallel outputs.

## Hypothesis shortlist and gating

The ranked, pre-registered hypotheses are already in [`registry/s23_hypotheses.json`](../registry/s23_hypotheses.json) and [`knowledge/66_s23_preregistration.md`](66_s23_preregistration.md). No experimental claim is made here.

1. **S23-PCSE — Phase-congruent scarp energy**: existing `det_elev`, `tmi`, `iso_grav_anom`; multi-scale oriented odd/even derivative energy and phase/polarity coherence, aimed at weak or partly buried scarps. Mimics: terraces, paleoshorelines, roads, lithologic contacts. Medium cost; highest qualitative priority; expected DTI improvement unknown.
2. **S23-TCB — Texture-covariance boundary**: `rtp`, `tmi_hg`, `cond_surf`; two-sided directional covariance/semivariogram change. Mimics: facies, intrusive contacts, levelling seams, resampling. Medium-high cost; untested; expected improvement unknown.
3. **S23-MCR — Matched conductive residual**: `cond_surf`, `depth_to_base_surf`, `det_elev`, `det_elev_slope`; spatial cross-fit conditional-conductivity residual margins. Mimics: saline aquifers, lacustrine clay, irrigation return, EM-depth variation. Medium cost, high confounding risk; expected improvement unknown.
4. **S23-CSD — Compound-scarp diffusion spectrum**: requires original USGS 3DEP 1 m DEM bytes, which were not obtained in this restricted runtime; not currently viable. Mimics: shorelines, terraces, road cuts and lithologic benches.

The top hypothesis was **not** implemented or evaluated. The fail-closed preflight ran after restoring all nine SHA-256-pinned shared upstream assets and returned **BLOCKED**: no assigned lane/source, no complete synchronized registry, the declared 37,654-dot candidate budget is blocked by the literal overlap control (do not tune around it), no strict comparable frozen baseline, and no prepared cached feature array. Consequently no leakage canary or HOLDOUT-DTI was run. The preflight details are recorded in its reproducible local result and the pinned session files; the historical S23 preflight remains unchanged.

## Repository review and tests

- Shared evaluator, metric, writer, validator, novelty implementation and registry manifest restored from the pinned upstream commit; all nine file hashes match. No private fork was made.
- `.venv/bin/python -m pytest -q`: **642 passed, 6 skipped, 9 subtests passed**, 12 Rasterio pending-deprecation warnings. Six skips explicitly require absent input rasters/tables; they are not passes.
- `.venv/bin/ruff check src scripts tests`: **All checks passed**.
- `python -S scripts/build_site.py`: **built 18 pages**, from JSON only, made no external requests, kept `submission_ready=false` and no research submission download.
- `scripts/check_run_preflight.py`: exit **1 / BLOCKED**, as intended; no candidate or score.

## Irregularities / limitations to keep visible

- Current active branch is `arena/d955c32f-gemsdoe28`, while frozen S23 card/config files name `arena/a774f0a0-gemsdoe28`. They appear to be retained parallel-session provenance. I did not rewrite them because doing so would invalidate their recorded hashes; this review records the active branch separately.
- Prompt leaderboard anchors `0.4413` and `0.3195` conflict. A retained older public leaderboard observation is not a file-bound organizer receipt and is not asserted as current. Current leaderboard state and weekly allowance remain unknown.
- Owner mirrors are not organizer-authenticated. A hash match verifies bytes against the pinned mirror only.
- The nine-site registry audit is selected historical coverage, not a live global registry. No model, canary, holdout, or TIFF was produced in this review.

## Next action sequence

1. Obtain the explicit single method-lane paragraph/assignment and a complete, synchronized registry; do not infer a lane from the broad prompt.
2. Resolve the calibration-control conflict in the shared registry protocol without removing the comparator or placing predictions into its uncovered cells.
3. Restore the template's expected prepared feature cache and a frozen best result evaluated under the exact buffered visible-only whole-segment protocol.
4. Re-run preflight. Only if it passes: execute the preregistered top candidate, per-feature leakage canaries, pooled HOLDOUT-DTI with CI, then pre-placement and final-dot novelty checks and exact-file validation. No score projection may be presented as an observed score.
5. Keep submission selection separate. Check the authenticated weekly allowance at that later point; a software/code pull request is not a competition submission.

**Run card:** See the single JSON record in [`evidence/active_checkout_review_2026-10-27.json`](../evidence/active_checkout_review_2026-10-27.json). It records `verdict: negative`, null HOLDOUT-DTI, no raster hash, validator not run, no submission name, and no slot selected.
