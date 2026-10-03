# Preregistration H32-2 — shallow-over-deep magnetic gradient de-screening (intrusive-pluton margin suppression)

**Written 2026-10-03 before any H32-2 holdout run.** This file is the frozen protocol; the runner
records its SHA-256 in the evidence JSON so the exact bytes that governed the run are auditable.

## Falsifiable geological hypothesis

**Hypothesis.** Among the off-catalogue dots emitted by the frozen `d=2.8` operating point, those
sitting on magnetic edges whose source is *deep* (Cenozoic pluton margins, caldera ring complexes,
basement terrane boundaries at source depth z0 ≳ 1.5–3 km) are disproportionately false positives,
whereas dots on magnetic edges whose source is *shallow* (z0 ≲ 300 m brittle contacts under thin
alluvium) carry hidden-fault credit at or above the live inclusion threshold.

**Transform (label-free).** Upward continuation by Δz attenuates wavenumber k by exp(−k·Δz); shallow
sources decay rapidly, deep sources slowly. Define the percentile-normalised attenuation ratio

    G1   = tmi_hg / P99_footprint(tmi_hg)                       (training_features band "tmi_hg")
    G150 = |∇H(TMI_up150)| / P99_footprint(|∇H(TMI_up150)|)     (geodawn_extensions_u8 band 4, u8 units)
    R    = G1 / (G150 + 1e-3)

High R ⇒ the 100 m-scale gradient is strong relative to its 150 m-upward-continued self ⇒ shallow
source. R ≈ 1 ⇒ deep source (both fields see it equally). A constant scale offset between the nT
and uint8 grids shifts R multiplicatively but preserves rank, and all thresholds below are rank
(percentile) thresholds over the dot population, so the decision is invariant to that constant.

**Target.** Same spatially blocked catalogue hide-and-recover proxy as every other arm: paired DTI
against hidden catalogue pixels on 4 quadrant folds. This proxy cannot see the far field; a pass is
a necessary, not sufficient, condition for organizer-label performance.

**Not claimed.** That R is a calibrated depth estimator (it is a rank screen), that uint8
quantisation is lossless (P99 robust scaling and rank thresholds are chosen to be insensitive to
it), or that pluton margins never host faults.

## Difference from prior work in this checkout

* `TMI_up150` (geodawn_extensions_u8 band 4) was only ever appended as an un-ratioed uint8 column
  in the failed H27-12 `+rad`/`+all` detector screens; the upward-continuation attenuation ratio
  against `tmi_hg` has never been computed in this repository.
* H31-1 used Euler *depth estimates* from `tmi` alone (failed screen, closed); H32-2 uses no Euler
  solutions, only the two-grid spectral-decay ratio, and acts as a *pruning* gate on the frozen
  d=2.8 emission rather than a feature injection.
* H28-1 (passed, seeds 140–149) tested multi-scale gradient *orientation coherence*; H32-2 tests
  vertical spectral decay — a physically distinct axis.

## Frozen experiment

* Base and control: identical to H32-1's — the repository's frozen
  `oof_detector.fit_predict_oof_probabilities` + `ridge_nms` + `build_oof_dotted_base(thin_d=2.8)`,
  same hyper-parameters, 4 spatial quadrant folds, 600 m buffer.
* Variants (per cell; quantiles computed label-free over that cell's base d=2.8 dots):
  1. `base_oof_d28` — control.
  2. `h32_2_p05_d28` — remove the bottom 5 % of base dots by R (deepest sources).
  3. `h32_2_p10_d28` — remove the bottom 10 % of base dots by R (**primary variant**).
  4. `control_top_p10_d28` — remove the TOP 10 % of base dots by R (direction control: if the
     hypothesis is true this must lose more credit per removed FP than variant 3).
* Seeds: **190–199** — a fresh decade; 180–189 were consumed by the H32-1 validation
  (`evidence/h32_1_holdout.json`). The session-8 note tentatively reserving 190–199 for H27-16 is
  superseded: H27-16 moves to 200–209 if and when it runs.
* Response: paired DTI difference (variant − base) per cell, identical metric implementation.

## Promotion gate (frozen; no threshold may be tuned afterwards)

Primary variant `h32_2_p10_d28` passes iff ALL of:

1. mean paired ΔDTI ≥ **+0.0010**;
2. improvement in ≥ **3 of 4** folds;
3. improvement in ≥ **8 of 10** seeds;
4. removed credit per removed FP < the OOF inclusion threshold at the run's base mean DTI;
5. direction control: `control_top_p10_d28` removed-credit-per-removed-FP ≥ that of
   `h32_2_p10_d28` (deep dots must be weaker than shallow dots, or the geology is not supported);
6. data checks: R finite on ≥ 95 % of footprint; all OOF probabilities finite and in [0, 1]; zero
   prediction pixels on known catalogue.

**Failure means**: no confirmation run, no retuning on these seeds, no submission candidate; the
hypothesis is recorded as a closed negative result. **Passing means**: eligible for exact-file
build and promotion review against the current holdout best (H32-1, +0.001272) — never an
automatic upload and never a weekly slot without beating that best.

## Run-1 integrity correction (2026-10-03, before any valid evidence existed)

Run 1 on seeds 190–199 was **invalidated by a runner data-check defect**, not by the geology: the
`training_features.tif` bands declare nodata with the float32 sentinel `|v| ≥ 1e30` (7,113,308
cells, essentially the out-of-footprint complement). The P99 robust scaling ingested the sentinel
(`P99 = 3.403e38`), collapsing R to ≈ 1e-37 everywhere and making the percentile prune rank-degenerate
(evidence preserved as `evidence/h32_2_holdout_run1_invalid_2026-10-03.json`). This violates gate
check 6 in spirit (R was numerically finite but structurally garbage). Following the H27-10
precedent (deterministic integrity repair, same seeds, full disclosure), the runner now applies
the repository's frozen validity rule `|value| < 1e30` before scaling; seeds 190–199 are re-run
once with the repaired runner. No gate threshold was altered.
