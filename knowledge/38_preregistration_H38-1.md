# Preregistration — H38-1: radiometric alteration information recovery (frozen before the run)

**Written before `scripts/run_h38_1_holdout.py` is executed.** This document freezes the instrument,
the arms, the decade and the decision rules for the first H38 gate. It spends **no** weekly submission
slot and cannot promote a file by itself.

> **Question.** Does adding the GeoDAWN radiometric channels (K, Th, U) and their standard ratio grids
> (Th/K, U/K, U/Th) to the 32-band detector change the *emission* enough to beat the current one-click
> incumbent on a spatially blocked holdout?

## 1. Why this arm exists

* `training_features.tif` band 6 is labelled `tc - Tilt angle or total curvature - magnetic field
  derivative for edge detection`, but it is **rank-identical to the GeoDAWN radiometric total count**:
  Spearman `+1.000` over the `5,164,300` in-footprint cells where both are finite (measured this
  session, `geodawn_rad_u8.tif` band 4 `TC`). Band 6 is currently **excluded** from the 32-band matrix
  by `scripts/prepare_data.py` (irregularity `tc-band-mislabelled`), so the detector receives **no
  radiometric information whatsoever** — including the one radiometric channel the organisers
  shipped.
* Total count is a lossy combination of K, U and Th; the three channels and the three standard ratios
  are strictly more informative than restoring band 6 alone.
* GeoDAWN is an official USGS + DOE/GTO product (`https://gdr.openei.org/submissions/1591`), the same
  contractor family as the competition's own feature stack (the mirror is literally named
  `gems-geodawn-numerical-features.tif`). Both rasters on disk are hash-pinned
  (`registry/data_manifest.json`: `geodawn_rad`, `geodawn_extensions`).
* Literature for the signature (checked this session): K/eTh as a potassic-alteration indicator
  (`https://www.nature.com/articles/s41598-024-52912-9`,
  `https://www.sciencedirect.com/science/article/abs/pii/S0969804322003967`).

**Honest prior, frozen with the arm.** Univariate AUC against catalogue pixels is weak: K `0.440`,
Th `0.451`, U `0.477`, ThK `0.485`, UK `0.536`, UTh `0.541` (near-fault 0–600 m vs far > 1200 m gives
the same ordering). This is a decisive cheap test of an untested *class* — new physical measurements —
not a predicted win.

## 2. Frozen instrument

* Runner: `scripts/run_h38_1_holdout.py` (new file, committed before the run). It imports
  `gems27.oof_detector`, `gems27.holdout`, `gems27.metric`, `gems27.packing`, `gems27.thinning` and
  contains **no** new modelling logic beyond assembling the extra channels.
* Decade: **seeds 260–269** (fresh hypothesis-gate decade; the ledger on `main` frees `250+`, of which
  `250–259` was consumed by H37-1). The LOSFO probe on `215–219` is a separate namespace and does not
  interact with this gate.
* Detectors, identical apart from the feature matrix:
  * **D0** — `data/prepared/features.npy`, the frozen 32-band matrix, unmodified.
  * **D1** — D0 plus six extra channels appended in row-major footprint order:
    `geodawn_rad` bands 1–3 (`K`, `Th`, `U`) and `geodawn_extensions` bands 1–3 (`ThK`, `UK`, `UTh`),
    read as `float32`, `NaN` outside the footprint and wherever the u8 value is `0` (the rasters'
    no-data marker; inside the footprint all values are `1…255`).
  * **Excluded, with measured reasons (not opinions).** `geodawn_extensions` band 4 `TMI_up150`:
    Spearman `+0.984` with in-stack `tmi` (band 14) — a duplicate. `geodawn_rad` band 4 `TC`:
    rank-identical (`+1.000`) to training band 6 `tc`, i.e. the same channel the repo already excludes;
    including it would test nothing about the disaggregated radiometry.
* Everything else is the frozen H36-1/H37-1 pipeline, unchanged:
  `oof_detector.fit_predict_oof_probabilities` (HistGradientBoostingClassifier, `max_iter=100`,
  `max_leaf_nodes=31`, `lr=0.08`, `l2=5.0`, `neg_ratio=10`, seeds `2026+f`), 600 m training buffer,
  `holdout.make_quadrant_folds` (`NW`, `NE_LidarGapHeavy`, `SW`, `SE`), `ridge_nms(sigma=1.0)`,
  `PRE_THIN_FRAC=0.0245`, `RUNG30=3.0`, `THIN_D_REF=2.8`, and the H27-4 blind 1-px catalogue-flank
  prune `blind_r1 = distance_transform_edt(~known) <= 1.0`.

## 3. Arms (per cell; all masked to `active = fold_mask & ~known`)

| arm | detector | emission rule |
|---|---|---|
| `base_d280` | D0 | `dot_thin(top-k ridge pool, 2.8)` — the shipped reference rule |
| `cover_r1` | D0 | `coverage_greedy(ridges, prob, n_pre)` then `& ~blind_r1` — the H37-1 emission, re-measured here on a fresh decade |
| `rad_base_d280` | D1 | `dot_thin(top-k ridge pool, 2.8)` |
| **`rad_cover_r1`** (PRIMARY) | D1 | `coverage_greedy(ridges, prob, n_pre0)` then `& ~blind_r1`, **matched to the D0 dot count** `n_pre0` so the comparison isolates information, not budget |
| `control_random_matched_n` | D0 | content-blind uniform draw of `n_pre0` ridge pixels, then `& ~blind_r1` |

`n_pre0` = `int(thinning.dot_thin(top_pool(ridge_D0, prob_D0, k), 3.0).sum())` with
`k = round(PRE_THIN_FRAC · fold_pixel_count)`, exactly as in `scripts/run_h37_1_holdout.py`.

## 4. Frozen decision rules

* **G1 — direction.** Mean over the 40 cells of ΔDTI(`rad_cover_r1` − `cover_r1`) **> 0**.
* **G2 — promotion.** The same mean **≥ +0.0005**, with `≥ 8/10` seeds and `4/4` folds positive
  (seed mean across its four folds; fold mean across all seeds).
* **G3 — do no harm (secondary rule).** Mean ΔDTI(`rad_base_d280` − `base_d280`) **≥ −0.0005**: the new
  channels must not wreck the detector under the reference emission rule. This criterion exists so a
  G1/G2 pass cannot be bought by a detector that is merely different; it also catches the opposite
  failure (features that only help through the coverage objective).
* **G4 — content control.** Mean ΔDTI(`rad_cover_r1` − `control_random_matched_n`) **≥ +0.0005**.
* **G5 — integrity.** (a) All six extras are `NaN` outside the footprint and finite on ≥ 99.9 % of
  in-footprint cells (the recorded remainder is the rasters' own zero cells). (b) `rad_cover_r1` is a
  subset of `active`, has **zero** overlap with `known`, is non-empty, and emits exactly `n_pre0`
  pixels (a shortfall means the packer ran out of positive marginal gain and voids that cell's claim).
  (c) Both detectors are deterministic: rerunning one seed's fold reproduces its DTI to `1e-12`.
* **Report-only, not gated.** (i) `cover_r1` vs `base_d280` — an independent-decade replication of the
  H37-1 interleaved gain (the far-field falsification is already settled in `knowledge/33`; the
  interleaved number is quoted only with that caveat). (ii) Per-band AUCs measured this session.
  (iii) The number of D1/dot-count differences caused by the extras changing `ridge_nms` output.

## 5. Pre-committed interpretation

* **G1, G2, G3, G4, G5 pass** → H38-1 is a *candidate only*. The next required step is a frozen LOSFO
  far-field test of the same emission pair (D1 vs D0) on a fresh LOSFO decade before any weekly slot;
  `knowledge/33` is the standing precedent that an interleaved pass does not transfer.
* **G1/G2 fail, G3 passes** → the radiometric channels do not change the emission materially; the arm
  is closed for this decoder, recorded with its numbers, and the hypothesis is reclassified as
  "information present, not exploitable by this detector" rather than refuted as geology.
* **G3 fails** → the channels degrade the detector; the arm is closed outright and the 0.44–0.54
  univariate AUCs are recorded as the explanation.
* **G5(a) or G5(b) fails** → the run is void; the defect is fixed and disclosed *before* any further run
  on `260–269`, and any metric already read from the broken run is reported as void (H33-1 precedent:
  disclose the seed use, do not silently re-run).
* **Multiple comparison discipline.** Exactly one primary comparison (`rad_cover_r1` vs `cover_r1`) is
  declared; all other arms are report-only and may not be promoted by re-ranking this run.

## 6. What this test cannot establish

* It cannot show far-field transfer. The interleaved protocol's hidden truth is catalogue geometry at
  distance 0 from the published catalogue (`evidence/arm_habitat_decomposition.json`), which is why the
  H37-1 interleaved gain did not survive LOSFO.
* It cannot separate "radiometric alteration physics" from "one more terrain/lithology proxy": K, U and
  Th respond to bedrock-versus-alluvium as much as to alteration, and the catalogue prefers basin-margin
  positions. A pass would therefore license the *information*, not the *mechanism*.
* It says nothing about the dose axis, which is measured far-field by
  `evidence/losfo_cover_probe.json` in a separate namespace.

## 7. ERRATUM — G5(b) as written was inconsistent with the arm definition (disclosed 2026-10-03)

The first execution of this protocol (`seeds 260-269`, `evidence/h38_1_holdout_pilot_void.json`,
305 s) produced a valid detector/arm matrix but failed G5(b) on all 40 cells with lines of the form
`primary emitted 10,048 != n_pre0=10,224`. The cause is a **harness defect, not an arm failure**:
the arm definition in §3 appends the H27-4 blind `blind_r1` prune to the packer's output, and the
runner compared the *post-prune* mask to `n_pre0`. No `coverage_greedy` output can survive a
1-px-flank prune unchanged. The H37-1 gate never had this problem because
`scripts/run_h37_1_holdout.py` checks the **packer's own output** (`primary_pre`) against the
requested count and lets the prune be recorded separately.

* Filed as irregularity `h38-1-g5b-checked-post-prune-count`.
* The pilot's DTI matrix is **void for gating** and is kept on disk, unmodified, as the pilot record.
  Its G1/G2/G3/G4 values are not quoted as results anywhere.
* `scripts/run_h38_1_holdout.py` now checks both packers' own output (`primary_pre`,
  `incumbent_pre`) against `n_pre0`, and additionally records, per cell, the packer counts, the
  prune-removed counts and the post-prune counts of the primary and the incumbent, so the
  matched-count claim is auditable without re-deriving it (the pilot exposed that this diagnostic was
  missing).
* The gated run uses a **fresh decade `270-279`**, not `260-269`: the decision statistics of
  `260-269` were already computed and read, so re-checking the same cells after changing a rule —
  even a rule that cannot alter a DTI — is exactly the re-adjudication this repo's protocol forbids.
  `260-269` is spent and disclosed; no result from it may be cited.

## 8. ERRATUM 2 — G2's fold statistic was computed against the wrong reference (disclosed 2026-10-03)

The second execution (seeds `270-279`, `evidence/h38_1_holdout_run2_g5fixed_g2defect.json`, 297.8 s,
`integrity_violations: []`) passed G1-G5 as the runner computed them, but the independent re-reading in
`scripts/analyze_h38_1.py` found that `G2_promotion` used
`summary[PRIMARY]["folds_improved_vs_base"]` — the fold split of `rad_cover_r1` vs the **D0 reference
rule** — whereas §4 G2 specifies the fold split of the primary against the **incumbent**
(`rad_cover_r1 - cover_r1`). The two are different statistics:

| statistic (seeds 270-279) | value |
|---|---|
| mean ΔDTI(primary − incumbent) | **+0.003697** |
| seeds positive vs incumbent | **10/10** (min +0.00117) |
| folds positive vs incumbent | **3/4** (`NW` −0.000703, `NE` +0.006924, `SE` +0.004173, `SW` +0.004395) |
| folds positive vs the D0 reference rule (what the runner reported) | 4/4 |

So under the literal §4 G2 the second run **fails** on one fold, and under the runner's statistic it
passes. Neither ambiguity is acceptable in a gate, and re-adjudicating `270-279` after seeing its
numbers is exactly what the protocol forbids.

* Filed as irregularity `h38-1-g2-fold-statistic-used-base-not-incumbent`.
* `scripts/run_h38_1_holdout.py` now computes and stores **both** splits
  (`folds_improved_vs_base`, `folds_improved_vs_incumbent`) and `G2_promotion` uses the
  incumbent-relative one, as §4 specifies.
* The gated run is a **third** fresh decade, `280-289`. `270-279` is spent and disclosed; its numbers
  are quoted only as a pilot in the erratum table above, never as a gate result.
* Standing cost of the two errata: three decades (`260-269`, `270-279`, `280-289`) for one gate. Every
  run, void or not, is archived on disk. Both defects were in the *harness*, not in the modelled
  quantity: no DTI value changed between runs, and the same-arm replication across the pilot and
  `270-279` (D0 `cover_r1` 0.10372 vs 0.10370, D1 `rad_cover_r1` 0.10740 vs 0.10627) is consistent.
