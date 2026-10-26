# S19 — radiometric alteration lineaments (2026-10-26)

## Lane and provenance

The current user message again references "the single method paragraph below" but supplies no
identifiable exclusive method paragraph. Autonomous interpretation, disclosed not concealed:
adopt the repository's own queued next lane — H39-2 radiometric alteration lineaments
(`knowledge/53_s18_result.md` next steps; `registry/next_hypotheses.json` session15_addendum
`next_ranked[0]`), which no prior session executed. Session-scoped ID: `S19-RADLIN`.
No claim of an externally assigned exclusive lane. No competition upload; promotion, if any,
is a separate selector step. Budget: **3 experiments / 2 hours**. Fresh LOSFO seeds **320–324**
(seeds ≤319 are spent or reserved by prior lanes; do not retune on them).

**Frozen method paragraph (before any fit or placement):** From the hash-pinned GeoDAWN
radiometric mirrors, take the extension ratio grid `ThK` (band 1 of
`geodawn_extensions_u8.tif`; valid = value > 0 inside the footprint). Low Th/K is the
potassic-alteration signature: form `f = clip((p95 − ThK)/(p95 − p5), 0, 1)` over valid pixels
(nearest-valid fill only for filtering), smooth at σ=1 px, and take its 1-px ridge by the shared
`oof_detector.ridge_nms`. A ridge pixel earns lineament score
`clip(mx10,0,1) · (0.5 + 0.5·aniso10)` where `mx10`/`aniso10` are the max and
`(max−mean)/max` anisotropy of the four-orientation (0/45/90/135°) ±10 px (1 km half-length)
line means of the smoothed field; score is 0 off-ridge and outside valid radiometry. The bonus
field is the 7×7 maximum of that score (lineament influence within 300 m). Placement is the
shared detector's all-ridge **coverage packing** (`packing.coverage_greedy`) with weight
`prob · (1 + 0.5 · bonus)`, candidates = detector ridge pixels >2 px from the *visible*
catalogue, at a per-cell dot count matched to the recomputed H38-1 baseline (full map:
37,654 dots, the champion's budget, for count comparability only — no champion pixels are
read into placement). Nothing else changes: 32-band cached feature stack, detector,
LOSFO split, evaluator and writer are the shared template tools. K/Th/U raw bands
(`geodawn_rad_u8.tif`) are used only for a validity/quantisation audit of the ratio grid,
not in the score.

**Mechanism.** Hydrothermal alteration along a fluid conduit depletes Th relative to K
(potassic alteration halo). A buried fault that never produced a Quaternary scarp can still
host such a halo, linear at ≥1 km scale, where the surface-rupture catalogue has no trace.
Coverage packing under the official 300 m kernel then spends dots preferentially covering
detector-probability mass that is alteration-corroborated, instead of covering the
probability field blind to alteration.

**Named non-fault mimic.** Felsic lithologic boundaries and playa evaporite K enrichment
produce low-Th/K lineaments with zero fault displacement; GeoDAWN flight-line striping can
manufacture linear ratio artefacts. A lineament is alteration geometry, not proof of a fault
or a geothermal vent.

## Ranked candidate hypotheses (before implementation)

Qualitative expected utility only — no numeric DTI projection is a score. Novelty means
"not executed in this checkout" (checked against `src/gems27/`, `knowledge/` and
`registry/next_hypotheses.json`), not a claim nobody else has studied the process.
All use already-restored, hash-pinned owner mirrors (provenance class: owner mirror,
NOT organizer-authenticated). No new external data is required for ranks 1–4.

| Rank | Hypothesis / layers | Signature and missing-catalogue rationale | Difference from implemented work | Non-fault mimic | Expected benefit / cost |
|---|---|---|---|---|---|
| 1 | **S19-RADLIN**: GeoDAWN `ThK` (+`UTh`) alteration lineaments × detector all-ridge coverage | Low-Th/K ridge, ≥1 km oriented collinearity, as multiplicative coverage weight; alteration haloes outlive/absent scarps along buried conduits | Radiometrics entered only as scalar GBDT bands (S14a radiometric detector: interleaved pass, LOSFO unresolved) or pointwise halo thresholds (H35-1); never as an object lineament weighting coverage placement | Felsic contact; playa K; flight-line striping | Highest in this slate (builds on the twice-replicated all-ridge coverage far-field gain, +0.0052/+0.0059, `knowledge/39`) / medium |
| 2 | Signed shear→dilatation transition corridors; `geod_shearrate`, `geod_dilaterate`, `tmi_hg` | Zero-crossing of dilatation flanked by high \|shear\|, collinear with a TMI horizontal-gradient ridge, as detector extra bands | Kinematic gates used scalar tendencies/thresholds; no signed transition object exists in `src/gems27/` | Distributed ductile strain; interpolation boundary of the geodetic grid | Low–moderate (100 m expression of a km-scale geodetic field is weak) / low |
| 3 | Drainage-chain collinearity; `det_elev`, `det_elev_slope` | Valley-skeleton pixels whose 900 m, 16-direction collinearity vote is high, as extra bands | Terrain work used amplitude/step/curvature descriptors; no drainage-chain object at 100 m | Joint sets; strike valleys; lithologic channels | Low–moderate / medium |
| 4 | Cross-slope radiometric sign reversal; `det_elev` + K/Th/U | Ratio reversal with consistent sign across opposing drainage slopes along a line | Scalar radiometric bands and H39-2-style lineaments proposed; cross-slope sign-consistency never executed; u8 quantisation must be audited first | Felsic contact; transported alluvium; topographic gamma attenuation | Uncertain / medium |
| 5 | Depth-coherent MT conductance-boundary migration + gravity | Lateral migration of a conductance boundary across depth slices with gravity-edge corroboration | Differs from single-depth `cond_surf` scalars, but **not viable now**: no MT slices exist in this checkout and the official source (USGS, DOI [10.5066/P9TWT2LU](https://doi.org/10.5066/P9TWT2LU)) cannot be fetched/byte-verified from this sandbox's allowlisted hosts. Named, gated, not proposed as runnable. | Clay-rich basin margin; lithologic conductor | Unranked benefit / high, data-blocked |

## Frozen experiments and gates

1. **Surface + canary + pre-placement uniqueness (no detector fit).** Build the label-free
   lineament surface from the radiometric mirrors only. Feature-alone leakage canaries on
   LOSFO seed 320 withheld systems (250,000 sampled negatives >6 px from hidden truth,
   fixed RNG): each of (a) lineament score, (b) bonus field, (c) inverted-ThK field alone.
   `max(AUC, 1−AUC) > 0.90` ⇒ leakage, log and STOP. Pre-placement registry check on the
   surface: Spearman(surface, each registry raster) on a fixed 400,000-pixel footprint
   sample, and the fraction of the top-37,654 eligible surface pool (score order,
   ≥2.8 px packing, >2 px from full catalogue for sizing only) within 3 px of each
   registry raster. Spearman >0.90 OR overlap >70% against ANY member ⇒ duplicate,
   log and STOP (no TIFF). Registry scope is declared, not global: every local
   `docs/downloads/*-nan.tif` present at freeze time plus byte-verified forensic copies
   of the nine focus sites' highest-reported artifacts (GEMSDOE24/25/27/28/30/31/32/33/36,
   hashes pinned in `evidence/s18_champion_forensic.json`), fetched for education/forensic
   comparison only and never copied into any shipped raster.
2. **Buffered LOSFO gate, seeds 320–324.** Shared tools only:
   `run_losfo_harness.eval_set` v2 → `metric.dti_binary`, pooled DTI α=0.2, β=0.8,
   300 m triangular kernel; whole fault systems (dilate 3 px) hidden per quadrant fold,
   600 m buffer erased from training labels; every catalogue-derived quantity inside a
   cell (visible mask, distance eligibility) computed only from visible labels; visible
   faults masked pixel-exactly. Baseline per cell = the S18-registered H38-1 recipe
   recomputed on visible-only labels (rung-3.0 dotted base + joint heat-flow/Euler
   corroborated additions). Candidate per cell = coverage packing as frozen above at the
   baseline's per-cell dot count. Gates: pooled paired gain >0.001 AND lower 95% of the
   paired geographic-fold block bootstrap (10,000 draws, 4 blocks) >0 AND ≥3/4 fold
   pooled gains >0 AND ≥4/5 seed pooled gains >0 AND 0 candidate dots on visible
   catalogue AND every cell's hidden-to-visible separation >6 px. No retuning on these
   seeds under any outcome.
3. **Build + validator + final uniqueness (runs regardless; the verdict decides the label).**
   Full-fit detector on all labels; coverage packing to 37,654 dots, >2 px from the full
   catalogue. Write the all-finite TIFF (and NaN-outside variant + single-member ZIP for
   transport parity) through shared `submission.write_geotiff`; independently re-read and
   validate the exact files (single-band float32, template CRS/shape/transform, no NaN
   inside footprint, values in [0,1]). Final uniqueness: fraction of final dots within
   3 px of every registry raster (same declared scope as Exp. 1) and sample Spearman of
   the final binary vs each registry raster. `promote` (to a separate selector only,
   still not slot-approved) requires Exp. 2 gates AND uniqueness AND validator all PASS.
   Any other outcome is `negative`: the download banner must read 🔴 DO NOT SUBMIT.

Every computed number is labelled **HOLDOUT-DTI** (evaluator version, withheld positives,
95% CI). The 0.2477–0.2778 family values are **OWNER-REPORTED** context only; nothing is
**ORGANIZER-CONFIRMED** without a submission-page receipt. The dated public-leaderboard
observation (0.4413, 2026-10-25) is not a receipt and does not identify any raster's owner.

## Why the reported GEMSDOE32 leader improved (byte-verified, conditional)

`evidence/s18_champion_forensic.json`: the `e5eb6e7e-zeros` raster is exactly the solo-r1
dot set minus its 2,545 dots at catalogue distance ≤2 px (zero added, zero reconstruction
difference); solo-r1 is d2.8 minus the ≤1 px ring. For binary predictions
`DTI = TP/(0.2·(TP+FP) + 0.8·|G|)` at fixed truth, removing dots whose lost credit per
removed FP is below `0.2·DTI/(1−0.2·DTI)` raises DTI. The construction proves *emission
hygiene* (pruning), not a new detector; whether those dots earned zero credit on the
private expert labels cannot be measured here, so score causation stays conditional.
Copying or ring-pruning that raster would be a >95% duplicate and is prohibited by the
lane rule. Beating it requires new credit, not fewer of the same dots.
