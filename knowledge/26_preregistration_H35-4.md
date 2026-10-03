# Preregistration — H35-4 buried range-front gravity-bench ADD

**Registered 2026-10-03 (Session 11), before any fitting and before any seed spend.** Seed decade
**240–249** (verified free against every `evidence/*.json` seed ledger; H35-1 used 230–239).

This document is frozen. The runner records its SHA-256 inside the evidence JSON; if the text
changes after the run starts, the hash differs and the run is invalid. No retuning, no
fresh-decade rerun, no TIFF on failure.

---

## 0. Data precondition — satisfied locally, verified from the bytes

| Fact | Value | How verified |
|---|---|---|
| Gravity gradient | `data/training_features.tif` band 18 (`iso_grav_anom_hg`), validity `\|v\| < 1e30` = footprint exactly (42.07%) | hash-pinned restore + label-free descriptive count this session |
| Magnetics (mesa leg) | band 3 (`tmi_hg`), same validity rule | same |
| LiDAR scarp/relief | `data/lidar_scarp_features_u8.tif` bands 3 (`step_max`), 9 (`relief`), 12 (`valid`) — CORRECTED names per `prepare_data.py` assertions | hash-pinned restore; `valid > 0` covers 75.37% of footprint and agrees with `step_max > 0` at 99.97% (label-free check this session), so `step_max = 0` marks invalid terrain in practice |
| Detector | `oof_detector` on LOSFO-masked labels (same instrument as H35-1/LOSFO) | committed code |

**Pre-freeze coverage check (label-free, no truth contact, disclosed).** Before freezing, the
primary bench rule was evaluated on the full grid: bench covers **10.3%** of the footprint
(530,325 px), mesa 0.49%. Non-degenerate, so the primary is frozen as pre-specified; the
fallback (grav ≥ p60 & step ≤ p60 & relief ≤ p60) was specified but not needed and is void.
Cuts are computed by frozen procedure (quantiles over valid footprint pixels), not frozen numbers.

No external fetch is required. No seed is spent anywhere else between this registration and the run.

---

## 1. Physical hypothesis

A range-front normal fault buried under a prograding Holocene fanglomerate apron loses the crisp
scarp the USGS compilation keys on — but the basement density step survives burial untouched:
dense Paleozoic/Mesozoic basement (~2,650–2,750 kg/m³) against unconsolidated basin fill
(~2,000–2,200 kg/m³) keeps a strong isostatic-gravity horizontal gradient along a smooth,
low-relief fan surface. Gravity sees through the apron; the mapper's aerial photo does not.

**Claim.** Off-catalogue dots on gravity benches (strong `grav_hg`, low scarp, low relief) earn
more far-field DTI credit per dot than the live inclusion threshold charges, while equally
far-field ridge dots off-bench do not.

**Why this could find faults the catalogue misses.** Pediment-front and range-front faults
degraded by fanglomerate progradation are omitted from Quaternary scarp maps by construction
(no preserved scarp, no entry), yet remain first-order basement structures with multi-mGal
expression. The bench filter explicitly excludes the opposite failure mode — contour-following
Tertiary basalt/ash-flow mesa rims that fire the LiDAR + magnetic legs of H19-5 with zero
basement step.

**Difference from everything already implemented here.** H32-3 specified the same *layers* as
*suppression* (prune-class) and is closed unrun under the pruning-exhausted rule; H35-4 is its
ADD dual — emit buried-fault candidates instead of suppressing mesa rims. Different gate (LOSFO
+ τ_live), different budget (capped addition), different control (non-bench far-field ridge).
H28-1 computed magnetic-gravity orientation coherence globally without the mesa-vs-bench
decoupling. H35-1 (thermal, FAILED 2/6 this session) shares the harness and the bar but no
physics: heat vs density step, disjoint layers except the ridge skeleton.

---

## 2. Design (frozen)

**Protocol.** Leave-fault-system-out (`src/gems27/losfo.py`), identical `dilate_px=3`,
`buffer_px=6` to H35-1/LOSFO. 10 seeds × 4 folds = 40 paired cells. Empty-hidden cells are
skipped and recorded.

**Control (`base`).** Same d=2.8 masked-detector base as H35-1 (`PRE_THIN_FRAC`, `thin_d=2.8`).

**Bench / mesa (frozen, label-free; `src/gems27/gravity_bench.py`).**
- Valid: training pixels with `|v| < 1e30`; LiDAR pixels with `valid` band > 0. Quantiles over
  valid footprint pixels.
- Bench = lidar-valid & grav-valid & (`grav_hg` ≥ p75) & (`step_max` ≤ p50) & (`relief` ≤ p50).
- Mesa = lidar-valid & grav-valid & tmi-valid & (`step_max` ≥ p90) & (`tmi_hg` ≥ p90) &
  (`grav_hg` ≤ p50), minus bench.
- The mesa mask is a SHARED pre-filter: both arms emit from `sub-threshold & ~mesa`, so the
  gate tests bench-vs-non-bench, not bench-vs-known-junk.

**Eligible addition pool (per cell).** OOF sub-threshold ridge pixels satisfying ALL of: inside
the fold quadrant; NOT in the buffered known set; NOT in the base; below the cell's top-k ridge
cut; ≥ 3 px from buffered known (far-field); ≥ 2.8 px from every base dot; bench (primary) or
non-bench (control); NOT mesa (both).

**Ranker (frozen).** `grav_hg` descending, ties by raster order — in the holdout AND in the
full-map construction, so the gate validates the same ranker the TIFF uses. (H35-1 ranked by
ridge probability in the holdout but had no probability leg on the binary H19-5 full map; H35-4
closes that transfer gap by ranking on gravity everywhere. The ridge still provides the
structural skeleton; gravity orders it.)

**Budget (frozen).** `K = round(0.03 × base_cell_dots)` per cell; emit top-K by ranker, then
`dot_thin(·, 2.8)`. Full-map scale ≈ 1,323 dots. The 3% (vs H35-1's 2%) is a power calculation
from H35-1's MEASURED harness noise (added seed-means SD ≈ 0.024 at ~460 dots/seed → 3% gives
~690 dots/seed, SD ≈ 0.020), disclosed here: sizing on harness variance, not tuning — H35-4's
decade, legs, and ranker are untouched by H35-1's outcome. Worst-case Phase-1 cost at 1,323
zero-credit dots: denominator +264.6 units ≈ **−0.0037 DTI** (analytic bound at 0.2600).

**Variants:**

| Variant | Rule |
|---|---|
| `base` | control, unchanged |
| `h35_4_add` | **primary**: base + budgeted bench dots (grav-ranked) |
| `control_nonbench_ridge` | **direction control**: base + K top-grav non-bench, non-mesa far-field ridge dots (same K, same thinning, same ranker; smaller pools emit all and record) |

**Leakage guards (frozen).** All legs are label-free rasters; all distances recomputed per cell
vs the buffered known set. Runner asserts per cell: added ⊆ far-field, added ∩ known = ∅, min
added-to-base ≥ 2.8 px, hidden-to-known ≥ 6 px, base ⊆ top-k cut. Any violation fails the RUN.

---

## 3. Metrics and promotion gate (frozen, numeric)

Same estimand as H35-1: per-cell added marginal credit/dot `ΔTPw / N_added` (NaN if `N_added =
0`, cell excluded from that seed's mean and recorded). Same threshold: LIVE
`τ_live = metric.inclusion_threshold(0.2600) = 0.05485` (recomputed in-runner). Cell thresholds
reported for context only.

**`h35_4_add` is promoted only if ALL of the following hold:**

1. Mean over seed-means of added marginal credit/dot **> 0.05485**.
2. Seeds with added credit/dot > 0.05485: **≥ 8/10**.
3. Folds with fold-mean added credit/dot > 0.05485: **≥ 3/4**.
4. Direction: pooled added credit/dot **>** pooled control credit/dot.
5. Coverage: **≥ 50%** of non-empty cells emit **≥ 10** added dots.
6. Integrity: criterion-6 asserts hold in every evaluated cell (failures raise before the gate).

**On failure:** record in `knowledge/27`, no retune, no fresh-decade rerun, no TIFF, no slot.
Seeds 240–249 burned either way. A fail here closes the SECOND ridge-filter ADD family and the
program pivots fully to purpose-built channels (H35-2 residual, H35-3 drainage) + H35-5 policy.

**On pass:** build ONE full-map candidate by §4, audit with `scripts/verify_downloads.py`,
register its note (≤ 200 chars), present UNSCORED and not slot-approved (owner's manual call).

---

## 4. Full-map construction on PASS (frozen)

Eligible = H19-5 solid-ridge pixels NOT in `dotted_h19_5_d2_8`; NOT on catalogue; ≥ 3 px from
the full catalogue; bench; NOT mesa; ≥ 2.8 px from every d2.8 dot. Rank by `grav_hg`
descending (same ranker as the holdout), ties by raster order. Emit top **1,323** (3% of
44,090), then `dot_thin(·, 2.8)`. Union with d2.8; single-band float32 NaN/0/1 + allfinite
fallback + single-member zip by a committed script, never by hand.

---

## 5. Expected magnitude, and what a pass does not prove

Bounds at 1,323 dots: zero credit → ≈ −0.0037; 0.10 c/d → ≈ +0.003; 0.20 c/d → ≈ +0.009. The
reachability gap needs ~2,600–3,400 dots at 0.4–0.5 — H35-4 alone cannot close it.

A pass does NOT prove live transfer (LOSFO truth is mapped faults: an **upper bound**), and the
OOF ridge is a stand-in for H19-5 (same caveat as every prior arm; the ranker gap is closed by
design, the skeleton gap is not).

---

## 6. Geological and methodological limitations (stated up front)

1. **The detector may have priced gravity already.** `grav_hg` is one of the 32 GBDT bands, so
   the ridge skeleton already exploits it; the marginal value of an explicit bench filter on
   top is genuinely uncertain — this gate measures exactly that margin.
2. **Bench needs lidar-valid terrain (≤ 75% of footprint).** Buried faults under the
   LiDAR-invalid quarter are invisible to this arm by freeze.
3. **Mesa exclusion is small (0.49%) and one-sided.** It removes the known rim mode but cannot
   enumerate every non-fault gravity gradient (intrusive margins, caldera rings).
4. **Quantile cuts are procedure-frozen, not physics-derived.** p75/p50/p90 are conventional
   levels; the empirical distributions, not fault physics, set them.
5. **LOSFO resolves large effects** (per-fold swings −12%…+20%, `knowledge/20` §2); the 8/10 +
   3/4 + direction structure is the guard, and it is strict by design (a false pass burns a
   weekly slot).
6. **Owner-reported scores are not receipts.** 0.2600/0.3195 are leaderboard/owner readings.
