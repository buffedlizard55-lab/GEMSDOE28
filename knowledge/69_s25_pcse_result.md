# S25 · 2026-10-28 UTC · PCSE (phase-congruent scarp energy) — result

**Decision: NEGATIVE for leaderboard use.** A unique, format-valid GeoTIFF was generated (so the lane is not a duplicate), but it scores **below a random-placement control** on the shared holdout. **OK to download for review: yes. OK to submit: NO.** No weekly slot was selected or spent. No organizer receipt exists.

## Labels used in this document

- **HOLDOUT-DTI** = computed by the shared evaluator `gems-segment-pooled-v1` on the restored owner-mirror inputs. Not a leaderboard score.
- **ORGANIZER-CONFIRMED** = none exists for S25.
- **USER-REPORTED / UNVERIFIED** = leaderboard and site scores supplied in the request; not reproduced here.

## Experiments (budget: 3 experiments / 2 hours; 2 used, ~45 min)

| # | Experiment | Holdout DTI (HOLDOUT-DTI) | 95% CI | Notes |
|---|---|---|---|---|
| 1 | **PCSE full** (`scripts/run_s25_pcse.py`) | **0.04504** | 0.03803 – 0.05252 | 37,654 dots; 60,988 withheld positives |
| 1c | Random-K control, same folds/seed | 0.06987 | 0.06668 – 0.07314 | seeded uniform draw over eligible cells |
| 1p | Paired PCSE − random-K | **−0.02484** | −0.03241 to −0.01692 | PCSE wins **0 / 4** folds; paired CI excludes 0 on the negative side |
| 2 | Ablation: step-polarity term only (`scripts/run_s25_pcse_ablation.py`) | 0.03734 | 0.03359 – 0.04127 | diagnostic only |
| 2 | Ablation: energy term only | 0.03767 | 0.03068 – 0.04515 | diagnostic only |

Per-fold PCSE − random (from `evidence/s25_pcse_holdout.json`): NW −0.0222, NE_LidarGapHeavy −0.0399, SW −0.0145, SE −0.0286.

Interpretation: neither the step-polarity factor nor the energy factor carries usable fault signal on this holdout; their product is slightly better than either alone but still far below random placement. The *mechanism* in the hypothesis (a consistent cross-scale step) is not supported by this operator on these three layers. This is a **negative result**, and it is recorded as a deliverable.

## Leakage canary (AUC; > 0.90 = leakage until explained)

Full PCSE run: `pcse_surface` 0.579; `det_elev_highpass` 0.397; `tmi_highpass` 0.491; `iso_grav_anom_highpass` 0.543. All below 0.90 and the features carry no catalogue input. Ablation: step-only 0.510; energy-only 0.570. **No leakage flagged.** Low AUC also means no feature is individually discriminative.

## Registry overlap and uniqueness (51 TIFFs in `docs/downloads`)

- Max candidate dots within 3 px of one registry raster: **0.4437** (threshold for duplicate: > 0.70). Pass.
- Max |Spearman| of the pre-placement surface vs any registry raster: **0.0618** (threshold: > 0.90). Pass.
- Duplicate flag: **none**. The file is therefore **unique under the repo's rule**. Uniqueness does not imply skill.
- Source: `evidence/s25_pcse_novelty.json`.

## Submission file (unique, format-valid, NOT recommended)

- File: `docs/downloads/gems28-s25-pcse-scarp-energy-k37654-20261028-4af5ddbb4b50-nan.tif` (+ `.zip`)
- SHA-256 TIF: `c6d722971070f6624a9b2a374c2858db46137f64dcd74805f160ba13f179edef`
- SHA-256 ZIP: `bcda0b0254e5aff28d3aca66c69bd2726788cfa53fcaa2d82182d5e11ca28d74`
- Validator (`submission.verify_geotiff`): **hard checks all pass** — EPSG:32611, shape (3730, 3292), transform (100, 0, 243350, 0, −100, 4508550), float32, single band, 0 non-finite cells inside the 5,167,373-px footprint, values in [0, 1], NaN outside (7,111,787 / 7,111,787), nodata = NaN as in the sample.
- Informational fail (not a hard requirement): a strict whole-array comparison that does not ignore NaN fails any file with NaN outside the footprint, including the official sample. The allfinite fallback was not produced for S25 because it is not the sample-matching format.
- Note (106 characters): `S25 PCSE k37654: unique (max 3px overlap 0.44) but HOLDOUT-DTI 0.045 < random-K 0.070. NOT for submission.`
- Organizer score: **none**. Projection: **none**.

## Bug found and fixed during this run (irregularity)

The training raster `data/training_features.tif` stores its missing-data sentinel as **−3.4028e38** (float32 minimum) in **3,061 footprint cells** per layer (bands 12, 13, 14). The first run treated these as values, which produced overflow and NaN in the surface. The operator now treats |x| ≥ 1e30 as missing. Registry comparison also now uses only jointly finite cells, and Spearman is recomputed on the valid subset rather than subsetting full-array ranks.

## What was restored (no DrivenData access)

- `scripts/restore_data.py --group core` and `--group model` (owner-mirror, SHA-256-pinned, GitHub only). Verified: `training_features.tif` (418,912,844 bytes, sha256 `4371c82e…23bc5`), `labels.tif` (`7ba308cc…4093`), `sample_submission.tif` (`2176d08e…bcc`), `h19_5_nan.tif`, dotted rasters, `lidar_scarp_features_u8.tif`.
- `scripts/restore_protocol_assets.py`: shared template (`data/shared_template`) pinned to GEMSDOE24 `2521cb67…`.
- `scripts/prepare_data.py --force`: builds `data/prepared/features.npy`.
- Status of organizer authenticity: **none**. These are owner mirrors, as `data/manifest.json` states.

## Software verification (this session)

- `pytest -q`: **657 passed, 5 skipped**, 12 warnings. Skips are data-dependent legacy tests. Four S25 tests (`tests/test_s25_pcse.py`) pin the TIF bytes, grid, [0,1] range, note length and NO-submit wording.
- Test-suite note: `tests/test_site.py` and `tests/test_s24_review.py` now re-apply the overlays after any in-repo page rebuild, so the committed pages match CI's clean-diff check.
- `ruff check src scripts tests`: **All checks passed**.

## Answer to the 0.2778 question (what can and cannot be concluded)

- **Cannot verify** that GEMSDOE32's 0.2778 is an organizer score. It is USER-REPORTED / UNVERIFIED.
- The structural mechanism of the file (catalogue-adjacent pruning of the solo surface) is documented in `knowledge/68_s24_repository_review.md`. S25 adds no evidence for or against it.
- **Why PCSE does not beat that family:** PCSE does not use the catalogue at all, while the high-scoring family is built on the H19-5 surface plus catalogue-derived pruning. A catalogue-free detector at 37,654 dots does not reach random-placement DTI on the holdout. Whether catalogue-derived structure explains the family's holdout signal was **not tested** in S25 and is left as an open question.

## Leaderboard anchors (unresolved)

The request lists **0.4413** as the GEMSDOE high score and **0.3195** as the highest score. An earlier repo record notes an **ORGANIZER-PUBLIC** observation of **0.4544** (#1) at approximately 18:50 UTC (see `knowledge/68_s24_result.md`). None of these was re-observed in this session: the sandbox cannot reach drivendata.org, which is outside the allowed host list. Manual review: <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/>

## Manual-review links (not fetched by this session)

- Competition: <https://www.drivendata.org/competitions/306/competition-doe-gems/>
- Problem description: <https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/>
- Submission format PDF: <https://docs.nlr.gov/docs/fy26osti/96647.pdf>
- Reference solution: <https://github.com/drivendataorg/gems-prize-reference-solution>
- Reference CRS: <https://epsg.io/32611>
- Tversky index (the scoring family): <https://en.wikipedia.org/wiki/Tversky_index>

## Next steps (ranked)

1. Run the S25 third experiment only if a **frozen, pre-declared** change is motivated by the ablation: for example, the catalogue-free operator restricted to the H19-5 non-catalogue surface. Do not tune K or the kernel on this holdout.
2. Re-derive the comparator on the same protocol (the S23 registry-feasibility gate still applies). Without a comparable frozen best, no candidate can be claimed to beat any site.
3. Confirm the leaderboard value independently from a DrivenData-hosted page that a human can open. This session cannot reach that host.
