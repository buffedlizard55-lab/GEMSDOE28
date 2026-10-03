# Preregistration — H38-1 far-field test (frozen before the run)

**Written before `scripts/run_losfo_rad_farfield.py` is executed, and before `evidence/h38_1_holdout.json`
(seeds `270-279`) has been read.** This is the transfer test that `knowledge/37` §5 makes mandatory before
any H38-1 artifact may be built, and it exists because of the standing lesson of this repository:
`knowledge/33` showed that an interleaved-proxy gain of `+0.007289` collapsed to `-0.000037` far field.
The hypothesis set and the gate live in `knowledge/36` and `knowledge/37`.

> **Question.** When the detector never sees a positive label within 600 m of the evaluated truth, does
> adding the six GeoDAWN radiometric channels change the emission's DTI — and in which direction?

## 1. Protocol (identical to the instrument that produced `evidence/losfo_cover_probe.json`)

* `src/gems27/losfo.py`, unchanged: `fault_systems(labels, dilate_px=3)`, `system_table`,
  `assign_systems_to_folds(tab, fold, 4, seed)`, `masked_labels(..., buffer_px=6)`.
* `holdout.make_quadrant_folds`, 600 m (6 px) label buffer, per-cell crop as in the probe.
* Fresh LOSFO decade **seeds 220-224** (the probe used 215-219 and the variants run 215-219; 220-239 are
  unspent). Per-cell truth is every hidden system's pixels inside the fold mask, at ≥ 8 px from every
  known pixel, exactly as the probe measured.
* Two detectors per seed, **same masked labels, same folds, same hyper-parameters**:
  * **D0** — the frozen 32-band matrix (`data/prepared/features.npy`).
  * **D1** — the same matrix plus the six channels `rad_K`, `rad_Th`, `rad_U`, `ext_ThK`, `ext_UK`,
    `ext_UTh`, gathered in row-major footprint order, `NaN` outside the footprint and where the u8
    grids are 0 — byte-for-byte the loader frozen in `knowledge/37` §2.
* `ridge_nms(sigma=1.0)`, `PRE_THIN_FRAC=0.0245`, `RUNG30=3.0`, `THIN_D_REF=2.8`.

## 2. Arms (per cell; all masked to `active = fold_mask & ~known`)

| arm | detector | emission |
|---|---|---|
| `thin_d28_D0` | D0 | `dot_thin(top-k pool_D0, 2.8)` — the shipped reference rule |
| `cover_n_D0` | D0 | `coverage_greedy(ridges_D0, prob_D0, n_pre_D0)` |
| `thin_d28_D1` | D1 | `dot_thin(top-k pool_D1, 2.8)` |
| **`cover_matched_D1`** (PRIMARY) | D1 | `coverage_greedy(ridges_D1, prob_D1, n_pre_D0)` |
| `cover_n_D1` (report-only) | D1 | `coverage_greedy(ridges_D1, prob_D1, n_pre_D1)` |

`n_pre_D0` / `n_pre_D1` are the `dot_thin(pool, 3.0)` counts of each detector's own top-k pool. The
primary is **count-matched to the D0 arm** (`n_pre_D0`), so it isolates *information*, not budget —
the same discipline that `knowledge/38` had to reconstruct for the H37-1 far-field arms.

## 3. Frozen criteria

* **F1 — information transfer (the gate).** Mean over cells of ΔDTI(`cover_matched_D1` − `cover_n_D0`)
  **≥ 0**, and no more than `2/20` cells below `−0.005` (a heavy-tailed loss in a few cells would mean
  the channels mostly hurt).
* **F2 — report-only, reference rule.** Mean ΔDTI(`thin_d28_D1` − `thin_d28_D0`), per-seed and per-fold
  splits, with its own 95 % interval. Recorded whatever it says; it exists because the gate's
  `rad_base_d280` arm (interleaved) improved by `+0.0054`, and this is the far-field counterpart.
* **F3 — integrity.** Every arm emits exactly the count it was asked for (asserted per cell before any
  metric is read); no arm overlaps `known` or leaves `active`; the two detectors' ridge fields and the
  D0 arms are reproducible across a repeated build of one cell.
* **F4 — reproduction.** No cross-run reproduction is possible on a fresh decade; instead the D0 arms
  must land inside the probe's observed per-cell range, and the mean `cover_n_D0` must be within
  `±0.004` of the probe's `cover_n` mean (`0.111635`). Outside that band the run is void and the
  instrument is re-audited before any conclusion.

## 4. Pre-committed interpretation

* **F1 ≥ 0 and F3/F4 pass** → the radiometric channels are far-field *non-negative*: H38-1 may proceed to
  artifact construction with the interleaved gate (`evidence/h38_1_holdout.json`) as its magnitude
  estimate and this run as its transfer licence. It still does not decide a weekly slot: the standing
  rule is that a slot requires beating the current holdout best, and the owner chooses the week.
* **F1 < 0** → the information is proxy-only. No D1-based file may be built or listed; the arm is
  recorded as a far-field regression of size `F1`, exactly as H37-1 was, and the hypotheses set returns
  to `knowledge/36` with H38-4/H38-3 next in the ranking.
* **F4 fails** → void run; fix and re-freeze on a fresh decade before reading any F1 value.
* This run cannot show *why* the channels help or hurt: K, U and Th respond to bedrock-versus-alluvium
  as much as to hydrothermal alteration, and both detectors see the same catalogue. A non-negative F1
  licenses the information, not the alteration mechanism.
