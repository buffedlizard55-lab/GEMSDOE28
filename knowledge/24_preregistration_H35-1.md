# Preregistration — H35-1 hydrothermal upflow conjunction ADD

**Registered 2026-10-03 (Session 11), before any fitting and before any seed spend.** Seed decade
**230–239** (verified free against every `evidence/*.json` seed ledger this session; LOSFO used
210–214, H34 used 220–229).

This document is frozen. The runner records its SHA-256 inside the evidence JSON; if the text
changes after the run starts, the hash differs and the run is invalid. No retuning, no fresh-decade
rerun, no TIFF on failure.

---

## 0. Data precondition — satisfied locally, verified from the bytes

| Fact | Value | How verified |
|---|---|---|
| Wells/springs | `data/gdr_wellspring_in_footprint.csv`, 27,092 rows, columns `temp_c`, `geothermquartz_c`, `row`, `col` | hash-pinned restore (`scripts/download_competition_data.sh` this session) + descriptive count |
| Hot cells | temp_c ≥ 60 OR geothermquartz_c ≥ 130 (NaN-safe), deduped on 200 m grid → 491 cells, 403 ≥ 300 m from catalogue | label-free descriptive count this session |
| Radiometrics | `data/geodawn_extensions_u8.tif` bands `ThK`, `UTh` (GeoDAWN mirror) | hash-pinned restore; zeros (57.9%) treated as nodata per `channel_auc.py` convention |
| Euler depth | `evidence/h31_1_euler_clusters.csv`, 6,309 SI=0 clusters, `row`/`col` centroids | label-free build (prior session) |
| Detector | `oof_detector.fit_predict_oof_probabilities` on LOSFO-masked labels (same instrument as `run_losfo_harness.py`) | committed code |

No external fetch is required. No seed is spent anywhere else in this session before the run.

---

## 1. Physical hypothesis

Active fault-hosted hydrothermal upflow destroys the evidence the catalogue is built from:
argillic/sericitic alteration weakens the wall rock, hot fluids erase brittle scarp relief, and
the fault never enters a Quaternary scarp compilation — while its heat (hot wells/springs),
potassium-metasomatic halo (depleted Th/K, elevated U/Th), geophysical ridge (below the emission
cut), and feeder contact at depth (shallow Euler solution) survive. Each leg alone is weak; the
four-way conjunction marks a fault the mappers could not see.

**Claim.** Off-catalogue dots at hydrothermal conjunctions earn more far-field DTI credit per dot
than the live inclusion threshold charges — i.e. adding them raises the 0.2600 submission's live
score — while equally far-field ridge dots *without* thermal conjunction do not.

**Why this could find faults the catalogue misses.** The USGS/INGENIOUS compilation is a
surface-rupture compilation: no preserved scarp, no entry — by construction, not by oversight.
Fault-hosted geothermal conduits (the Brady's / Desert Peak / Dixie Valley / Salt Wells class and
its undiscovered analogues) are exactly the faults whose scarps are erased by their own fluids.
The thermal channel lives in the far field (403/491 deduped hot cells ≥ 300 m from catalogue),
which is the only habitat a shippable addition can occupy.

**Difference from everything already implemented here.** H32-4 proposed the same *layers* as a
corridor screen and was never preregistered; H35-1 is a capped, scored, LOSFO-gated **addition**
— different gate (far-field + live threshold), different budget (2% capped), different control
(no-thermal far-field ridge), frozen leakage guards. dilcond (live-refuted 0.1223) used only
`cond_surf` × dilatation with no well, geothermometer, radiometric, or depth leg. H35-2 is the
same physical family with purpose-built residual data; H35-1 gates the family first, so a fail
here lowers H35-2's prior before its decade is spent.

---

## 2. Design (frozen)

**Protocol.** Leave-fault-system-out (`src/gems27/losfo.py`): 60,988 catalogue px grouped into
fault systems (8-connected components of the catalogue dilated 300 m); per seed, quadrant-blocked
systems held out with a 600 m label buffer erased globally; detector trained on masked labels;
truth = held-out systems ≥ 600 m from every pixel the detector saw as positive. Identical
`dilate_px=3`, `buffer_px=6` to `run_losfo_harness.py`. 10 seeds × 4 folds = 40 paired cells.
Cells with empty hidden truth are skipped and recorded (same as LOSFO).

**Control (`base`).** `oof_detector.build_oof_dotted_base` on the seed's masked detector
(probabilities + ridge NMS, `PRE_THIN_FRAC` budget, `thin_d=2.8`), masked to the fold's active
region (fold quadrant minus buffered known set) — the same base arm LOSFO measured at 0.0465
far-field credit/dot.

**Hot cells (frozen, label-free).** A wellspring row is hot iff `temp_c >= 60` or
`geothermquartz_c >= 130`, NaN-safe (a missing value votes no on its leg). Hot rows are deduped
to 200 m grid cells (`row//2`, `col//2`), one hot cell per occupied cell. Thermal proximity =
within 10 px (1 km) of a hot cell.

**Alteration halo (frozen, label-free).** Valid radiometric coverage = `ThK > 0` (zeros are
nodata). Over valid pixels only: `ThK <= p25` AND `UTh >= p75` (quantiles computed once on the
full grid, no label contact). Dots outside valid coverage are alteration-neutral (bonus 0, never
excluded — the alteration leg must not silently delete 58% of the map).

**Euler bonus (frozen, label-free).** Within 3 px of a rounded SI=0 cluster centroid.

**Eligible addition pool (per cell).** OOF ridge pixels from the seed's masked detector satisfying
ALL of: inside the fold quadrant; NOT in the cell's buffered known set; NOT in the base emission;
below the cell's top-k ridge cut (sub-threshold); ≥ 3 px from the buffered known set (far-field);
within 10 px of a hot cell; ≥ 2.8 px from every base dot (exclusion via
`distance_transform_edt(~base) < 2.8`, matching `dot_thin`'s strict inequality).

**Score (frozen).** `score = ridge_prob × (1 + 0.5·alteration + 0.5·euler)` with binary legs.
Budget `K = round(0.02 × base_cell_dots)`; emit the top-K by score, then `dot_thin(·, 2.8)` for
mutual spacing (final count ≤ K is recorded and used). Ties broken by raster order (deterministic).

**Variants (all evaluated on every non-empty cell):**

| Variant | Rule |
|---|---|
| `base` | control, unchanged |
| `h35_1_add` | **primary**: base + budgeted thermal-conjunction dots |
| `control_farfield_ridge` | **direction control**: base + K top-probability sub-threshold ridge dots that are ≥ 3 px from known, ≥ 2.8 px from base, and NOT within 10 px of a hot cell (same K, same thinning; if the pool is smaller, emit all and record) |

**Leakage guards (frozen).** The CSV's `dist_known_fault_px` column is NEVER read (it is measured
vs the full catalogue including held-out systems). Every distance in every cell is recomputed vs
that cell's buffered known set. Wells, radiometrics, Euler clusters, and the masked detector never
see held-out truth. The runner asserts: added dots ⊆ far-field, added ∩ known = ∅, min
added-to-base distance ≥ 2.8 px, and min hidden-to-known separation ≥ 6 px per cell.

---

## 3. Metrics and promotion gate (frozen, numeric)

Per cell: base DTI/TPw/dots; `h35_1_add` marginal credit `ΔTPw = TPw(base+added) − TPw(base)` and
marginal credit/dot `ΔTPw / N_added` (NaN if `N_added = 0`, cell excluded from that seed's mean and
recorded); same pair for the control; base far-field absolute credit/dot (informative only — it
carries no spacing penalty, so it overstates vs marginal).

The gate threshold is the LIVE inclusion threshold at the submission the arm informs:
`τ_live = metric.inclusion_threshold(0.2600) = 0.05485` (recomputed in-runner, recorded). The cell
threshold (~0.0204) is reported for context and gates nothing (`knowledge/22` §3).

**`h35_1_add` is promoted only if ALL of the following hold:**

1. Mean over seed-means of added marginal credit/dot **> 0.05485**.
2. Seeds with added credit/dot > 0.05485: **≥ 8/10**.
3. Folds with fold-mean added credit/dot > 0.05485: **≥ 3/4**.
4. Direction: pooled added credit/dot **>** pooled control credit/dot (thermal selection beats
   unselected far-field ridge at the same budget and spacing).
5. Coverage: **≥ 50%** of non-empty cells emit **≥ 10** added dots (a gate that fires on a
   handful of dots cannot be interpreted).
6. Integrity: every evaluated cell satisfies min hidden-to-known separation ≥ 6 px, added ⊆
   far-field, added ∩ known = ∅, min added-to-base distance ≥ 2.8 px (asserted in-runner; any
   violation fails the run, not just the gate).

**On failure:** record the result in `knowledge/25`, do not retune, do not rerun on a fresh
decade, do not build a candidate TIFF, spend no slot. Seeds 230–239 are burned either way.

**On pass:** build ONE full-map candidate by the frozen construction below, audit it with
`scripts/verify_downloads.py`, register its note (≤ 200 chars), and present it UNSCORED and not
slot-approved — the slot decision is the human owner's, manual, against the official rules.

---

## 4. Full-map construction on PASS (frozen)

Eligible = H19-5 solid-ridge pixels (`data/post_h19_5_filtered.tif`, the actual emission surface)
satisfying: NOT in `dotted_h19_5_d2_8` (the 0.2600 file); NOT on a catalogue pixel; ≥ 3 px from
the full catalogue; within 10 px of a hot cell; ≥ 2.8 px from every d2.8 dot. Score =
`(1 + 0.5·alteration + 0.5·euler)` (the H19-5 surface is binary, so no probability leg — ties
broken by raster order, deterministic). Emit top **880** (2% of 44,090) by score, then
`dot_thin(·, 2.8)`. Union with the d2.8 dots; write single-band float32 NaN/0/1 + allfinite
fallback + single-member zip by a committed script (not by hand).

---

## 5. Expected magnitude, and what a pass does not prove

At 880 added dots, worst-case Phase-1 cost (zero credit) is denominator +176 units ≈ **−0.0025
DTI** at the 0.2600 operating point — analytic bound, in `knowledge/23`. If the added dots earn
0.10 marginal credit/dot, the gain is ≈ +0.002; at 0.20, ≈ +0.006. The reachability gap needs
~2,600–3,400 dots at 0.4–0.5 — H35-1 alone cannot close it; it opens the ADD ledger and, on a
pass, funds H35-2/H35-3/H35-5.

A pass does NOT prove live transfer: LOSFO truth is still *mapped* faults, so far-field LOSFO
measures an **upper bound** on performance against genuinely unmapped faults (`knowledge/20` §2).
Clearing τ_live on LOSFO is necessary, not sufficient — stated here so no later session upgrades
it silently. The holdout OOF ridge is also a stand-in for the H19-5 surface (same caveat every
prior arm carries; the full-map construction uses H19-5 itself).

---

## 6. Geological and methodological limitations (stated up front)

1. **Hot wells cluster where people already look.** The wellspring record is exploration-biased
   toward known geothermal areas; a conjunction that only re-finds Brady's-adjacent faults still
   clears LOSFO (mapped truth) while adding nothing where mappers never went. The far-field +
   direction-control design mitigates; it does not eliminate.
2. **Radiometric zeros cut the alteration leg to ~42% coverage.** Dots outside GeoDAWN coverage
   are alteration-neutral by freeze, so the arm is effectively thermal×ridge there.
3. **1 km thermal radius is a halo scale, not a derivation.** Upflow halos span 100 m–km; 10 px
   is fixed without tuning and may be too generous (dilution) or too tight (misses).
4. **Quartz-geothermometer ≥ 130 °C and temp_c ≥ 60 °C are literature-conventional cutoffs**
   (H32-4), not fitted. Mixed waters and cold outflow can misclassify both ways.
5. **LOSFO per-fold ratios swing −12%…+20%** (`knowledge/20` §2): with 10 seeds the harness
   resolves large effects, not small ones. The 8/10-seed + 3/4-fold criteria are the guard.
6. **Owner-reported scores are not receipts.** 0.2600/0.3195 are leaderboard/owner readings, not
   organizer links between a score and these bytes.
