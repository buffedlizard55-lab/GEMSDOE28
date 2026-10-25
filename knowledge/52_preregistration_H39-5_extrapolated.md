# 52 — Preregistration (Session 18, 2026-10-25): H39-5 migration-extrapolated placement

**Frozen before any fit, pool build, or holdout run in this session.** Written after reading
`README.md` (standing prompt + Session 16/17 safety notices), `knowledge/50_s16_result.md`
(recommended next lane, §"What would actually beat 0.2778" item 3) and
`knowledge/51_session17_unique_submission.md` (ranked hypothesis table, H39-5 = rank 1).
This file is the single authorized method paragraph for this parallel run. Budget: **3
experiments**, then stop. No weekly slot is selected by this session; promotion, if any, is
to a separate selector step only.

## Lane (single method paragraph — stay inside it)

H39-5 places dots at **migration-extrapolated surface-trace positions** instead of on the
observed potential-field ridge: for TMI (training band 14) and isostatic gravity (band 13),
compute horizontal-gradient (HG) ridges at 0 / 1 / 2 km upward continuation with the shared
`src/gems27/depthslice.py` + `src/gems27/migration.py` code (extended in the same shared
module, never forked); for every shallow-ridge pixel let **v** = (nearest 2 km ridge pixel −
shallow pixel); the extrapolated position is **shallow − v** (one full migration step up-dip,
the linear extrapolation of ridge position vs. height to −2 km equivalent). Extrapolated
pixels inherit score = migration-coherence × clip(HG₀ / p99(HG₀), 0, 1) per field; the lane
surface is the per-pixel maximum over the two fields. The candidate is the frozen 32-band
detector emission with the weakest **35 %** of its dots dropped and replaced 1-for-1 (matched
count) by top-scoring eligible extrapolated pixels with displacement |**v**| ≥ 2 px, spacing
≥ 2.8 px against retained and accepted dots, never on the visible catalogue and always
> 2 px from it. Nothing else changes: detector, ridge NMS, budget, thinning and evaluator
are the shared template tools.

**Mechanism.** A dipping buried fault's top edge lies down-dip of where its plane, extended
upward, meets the surface. Upward continuation moves the HG ridge further down-dip
(Blakely 1995; migration direction = dip direction, Session 16). The mapped catalogue is
dominated by scarps — structures that already reach the surface — so a concealed dipping
fault under basin fill has neither a scarp for the LiDAR/GBDT ridge to fire on nor a USGS
trace; its only surface expression is up-dip of its potential-field edge. Every prior arm in
this repository (including H39-1 depthslice and H40-1 migration *features*) still emitted
dots **on** a detector ridge; H39-5 is the first arm whose novel dots sit off that ridge
network, which is also the only placement rule with a physical reason to break the dense
probe-blanket uniqueness ceiling measured in Sessions 15–16.

**Named non-fault mimic.** A dipping lithologic contact or mafic dike migrates identically
with zero Quaternary slip; its extrapolated "trace" is a real map line but not a fault.
GeoDAWN flight-line striping can also create false migrating ridges.

## Ranked candidate hypotheses (3–5, per standing prompt; top one is executed)

| Rank | ID | Layers | Signature | Why off-catalogue | Mimic | Cost | Status |
|:--:|---|---|---|---|---|---|---|
| 1 | **H39-5** extrapolated placement | `tmi`, `iso_grav_anom` | shallow − **v** positions (this file) | buried dipping fault's surface projection is up-dip of its edge | dipping contact/dike | Med | **EXECUTED this session** |
| 2 | H39-2 radiometric alteration lineaments | GeoDAWN K/Th/U + ratios | Hessian ridge of low Th/K, ≥1 km collinear | alteration halo along a conduit that never scarpped | felsic lithology boundary; playa K enrichment | Low | not run; local bands pinned |
| 3 | H39-3 drainage-chain collinearity | `det_elev`, slope | valley skeleton × 16-direction 900 m collinearity vote | scarp-less faults deflect drainage across catchments | joint sets; strike valleys | Low | not run |
| 4 | H39-4 artifact-swap shoreline suppression | LiDAR coh/strike, DEM, HG | remove constant-elevation ultra-linear steps with zero potential support, swap 1-for-1 | frees budget from zero-credit cultural dots | Lahontan strandlines; roads/canals | Low–Med | not run |
| — | H39-1 depthslice (reference) | TMI/gravity | persistence-weighted detector bands | — | basement contacts | — | executed S15: gate FAIL, do not re-run |

No numeric ΔDTI is projected for any row: a projection is never a score.

## Experiment 1 — label-free pool + leakage canary + pre-placement uniqueness (no detector)

Build the lane surface from the restored, hash-pinned training raster only (no labels read
by the surface code). Report: displacement-magnitude distribution; eligible-pool size
(|**v**| ≥ 2 px, inside footprint, d_cat > 2 px vs. the *full* catalogue for sizing only);
single-feature AUC of each field surface and the union surface vs. LOSFO seed-310 withheld
systems (negatives sampled > 6 px from hidden truth, same recipe as
`scripts/build_s16_extra.py`). **Canary rule:** max(AUC, 1−AUC) > 0.90 ⇒ leakage, stop.
Pre-placement uniqueness: Spearman(lane surface, each registry binary raster) on a 400 k
footprint sample, and fraction of top-37,654 eligible pool pixels (score order, 2.8 px
thinned) within 3 px of each registry raster. Registry = every `docs/downloads/*-nan.tif`
present at freeze time plus, for education/forensic comparison only, the GEMSDOE32 champion
and GEMSDOE36 rasters byte-verified against their published audit SHA-256 pins
(`c55bafc4…`, `e1589102…`) if fetched; fetched copies are never copied into any shipped
raster and are not committed. If pool Spearman > 0.90 vs. any registry raster, log duplicate
and stop before Experiment 2.

## Experiment 2 — frozen LOSFO gate, seeds 310–314 (fresh; 290–304 are consumed)

Shared evaluator only: `scripts/run_losfo_harness.py:eval_set` imported, `src/gems27/losfo.py`
+ `metric.py`, pooled DTI α = 0.2, β = 0.8, 300 m triangular kernel. Whole fault systems
(dilate 3 px) held out per quadrant fold; 600 m buffer erased from training labels;
catalogue-derived quantities inside a cell (visible-fault mask, d_cat eligibility) computed
**only** from visible (masked) labels; visible faults masked pixel-exactly (`active = fold &
~known`). Per cell: D0 = `build_oof_dotted_base(prob, ridge, fold, known, PRE_THIN_FRAC,
thin_d = 2.8) & active`; D1 = D0 with weakest-35 %-by-probability dots dropped, replaced by
eligible extrapolated pixels (score order; spacing ≥ 2.8 px vs. retained + accepted; d_cat >
2 px vs. visible labels; inside fold) until count matches D0; if the pool is exhausted,
backfill from dropped dots in probability-descending order subject to the same spacing.
Gates (identical structure to Sessions 15–16):
G1 pooled ΔDTI > 0 **and** mean paired ΔDTI ≥ +0.001;
G2 spread: ≥ 14/20 cells, ≥ 4/5 seed means, ≥ 3/4 fold means positive;
G3 pooled credit/dot(D1) ≥ credit/dot(D0);
G4 integrity: 0 D1 dots on visible catalogue; |N(D1) − N(D0)| / N(D0) ≤ 0.10 pooled;
G5 Experiment-1 canary passed.
Report pooled HOLDOUT-DTI for both arms, Δ, paired bootstrap 95 % CI (10,000 draws, seed 42),
withheld-positive count, per-seed/per-fold means, swapped-dot counts. **No retuning on these
seeds under any outcome.**

## Experiment 3 — build + validator + final uniqueness (runs regardless; verdict decides label)

Full-fit detector on all labels; base emission budget-searched to 37,654 dots ± 5 % exactly
as `scripts/build_h40_candidate.py`; then the same frozen 35 % swap against the full
catalogue (d_cat > 2 px). Write NaN-outside and all-finite variants + single-member ZIP via
`src/gems27/submission.py`; validate both with `verify_geotiff` (no NaN inside footprint,
values ⊂ [0, 1], single band, CRS/shape/transform = template). Final uniqueness: fraction of
final dots within 3 px of **every** registry raster (as Exp. 1) and Spearman of the lane
surface vs. each registry binary (Exp. 1 values). **Uniqueness FAIL = Spearman > 0.90 or
> 70 % of dots within 3 px of any one registry raster ⇒ verdict `negative`, banner
🔴 DO NOT SUBMIT.** Verdict `promote` (to selector only, still not slot-approved) requires
gate G1–G5 **and** uniqueness **and** validator all PASS. Any other outcome is `negative`.
The on-site status must state plainly whether the file may be uploaded; a format-valid file
that fails science or uniqueness is inspection-only.

## Score labelling

Every number produced here is **HOLDOUT-DTI** (evaluator and withheld positives stated in the
run card). The 0.2778 / 0.2750 / 0.2708 / 0.2600 family values are **OWNER-REPORTED**; no
organizer submission-page receipt exists in this repository, so nothing is
**ORGANIZER-CONFIRMED**. The 0.4413 vs. 0.3195 leaderboard maxima in circulation conflict
and are not asserted. Why 0.2778 won is already byte-verified (`knowledge/50`, `knowledge/51`
§1: emission hygiene — the champion is the 0.2708 solo file minus the d_cat ≤ 2 px ring);
this session does not re-litigate it and must not copy it (a ring-3 file would be a > 95 %
duplicate).

## Data provenance (obtainability checked at freeze time)

Inputs are the hash-pinned owner mirrors in `registry/data_manifest.json`, restored by
`scripts/download_competition_data.sh` (never contacts DrivenData; mirrors are
integrity-pinned, **not** organizer-authenticated — standing irregularity
`bridge-hashes-not-authenticated`). No new external data is required for H39-5: bands 13/14
of the restored training stack only. Official sources for manual review:
competition https://www.drivendata.org/competitions/306/competition-doe-gems/ ·
rules https://docs.nlr.gov/docs/fy26osti/96647.pdf ·
reference solution https://github.com/drivendataorg/gems-prize-reference-solution ·
USGS GeoDAWN https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and ·
GDR 1391 https://gdr.openei.org/submissions/1391 · CRS https://epsg.io/32611 ·
Blakely (1995) *Potential Theory in Gravity and Magnetic Applications*, Cambridge UP.
