> **S22 erratum / historical record:** This report contains superseded uniqueness, protocol and
> score-causation claims. S21 fails the literal any-raster duplicate rule (72.34% overlap), its
> split/full-label negative selection is not the shared whole-segment protocol, and the projected
> leaderboard values are not scores or evidence of superiority. Portal-range cause is unconfirmed.
> See [the current audit](62_s22_audit.md); no file is approved. The original statements below
> are preserved only to show what the earlier run claimed, not endorsed as current facts.

# 61 — Session 21 (S21-PUHGB) result — 2026-10-26

**Verdict: NEGATIVE. New unique TIFF generated and format-validated; automated gates REJECT it for
portal submission. 0 weekly slots spent.** Run card: `evidence/s21_run_card.json`.

## 1. Nine priority sites — best listed submission each (all USER-REPORTED / UNVERIFIED)

No organizer receipt exists in this repo for any row; the dated public-leaderboard top observed
2026-10-26 is 0.4413 (0.3195 was the 2026-10-03 snapshot). Competition/metric facts re-verified
2026-10-26 from the official problem page (faults, not geothermal vents; expert-mapped NEW faults
are the test set; known catalogue pixels are masked; DTI α=0.2 β=0.8, 300 m triangular kernel):
https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/

| Site | Best listed file | Reported | Construction (byte-forensics where stated) |
|---|---|---|---|
| GEMSDOE24 | h25-1-dotted-h19-5-d1-5 | 0.2477 | H19-5 (121,131 px) dotted @1.5px → 60,069 |
| GEMSDOE25 | dotted-h19-5-d2-8 | 0.2600 | H19-5 dotted @2.8px → 44,090 (footprint-identical to GEMSDOE30's file) |
| GEMSDOE27 | topo-gap-closure-t-v2-on-d1-5 | 0.2449 | d1.5 + gap-closure additions → 61,328 (additions lost vs 0.2477 base) |
| GEMSDOE28 | h36-1-rung30-blind-r1 | 0.2710 | rung-3.0 repack + ≤1px ring prune → 37,660 |
| GEMSDOE30 | d28-poisson300m-offcat-44090 | 0.2600 | same 44,090-dot raster family as GEMSDOE25 |
| GEMSDOE31 | h27-4-solo-d28 | 0.2708 | d2.8 − ring≤1px → 40,199 (= GEMSDOE28 solo file) |
| **GEMSDOE32** | **h33-h33-2-b2-…-e5eb6e7e-zeros** | **0.2778** | **solo − ring≤2px → 37,654. Highest listed. LEARNING REFERENCE ONLY — never copy.** |
| GEMSDOE33 | h33d-analog-tip-stepover-r30 | 0.2632 | tip/stepover placement → 41,865 |
| GEMSDOE36 | anderson-geothermal-pinn-38854 | 0.2750 | champion's 37,654 dots + 1,200 extra → 38,854 (extras cost 0.0028) |

## 2. Why 0.2778 won (replicated byte-exactly THIS session, Exp 1)

`scripts/run_s21_lane.py` on hash-verified restored data (`scripts/restore_data.py`, SHA-256 in
`registry/data_manifest.json`): `dot_thin(H19-5, 2.8)` reproduces the dotted file with symmetric
difference **0**; dotted − ring≤1px reproduces solo (40,199) with symdiff **0**; solo − ring≤2px
= **37,654** = champion construction. Mechanism: (a) 300 m kernel → ~2.8 px dot spacing earns
near-line credit at ~1/3 the FP mass of a solid line; (b) dots 100–200 m from catalogue lines are
mostly the detector's blur shadow of *known* faults — known pixels are masked in scoring, so those
dots earn ~nothing while paying 0.2·FP each; deleting all 2,545 of them is pure precision gain
iff their per-dot credit < τ = 0.2·DTI/(1−0.2·DTI) ≈ 0.0588 at DTI 0.2778 (`metric.inclusion_threshold`).
The whole 0.1922→0.2778 ladder is emission hygiene on ONE surface, not new geology. Score→file
association remains UNVERIFIED (champion repo's own audit calls the file UNSCORED).

## 3. Five ranked candidate hypotheses (generated before implementing)

1. **S21-H1 Fresh PU-HGB habitat detector (IMPLEMENTED).** Layers: all 19 GeoDAWN bands + 12
   LiDAR-scarp bands. Signature: multivariate habitat of catalogue faults learned PU-style.
   Why unmapped faults: same habitat, no catalogue geometry features allowed. New vs repo:
   first fully fresh-geography supervised surface in this repo gated end-to-end this way.
2. **S21-H2 U-Net patch segmentation** on 31-band patches (spatial texture: line continuity a
   per-pixel HGB cannot see). Highest expected gain, highest cost (GPU). → next session.
3. **S21-H3 Champion-recipe extension b3/b4** (ring≤3px, 35,483 dots — constructed & counted
   only). Expected +0.001–0.007 MODEL. **Duplicate lane (>90% champion dots): never submittable
   as unique.** Learning reference only.
4. **S21-H4 Soft-probability emission** (p∈(0,1] instead of binary dots; exact-DTI optimal
   shading under `metric.dti_exact`). Cheap to test on any surface; untested here (budget).
5. **S21-H5 Radiometric Th/K alteration lineaments** — needs GeoDAWN radiometric grids from
   USGS ScienceBase item 657e1d85d34e23d3533209f7 (free/official); not in the restored stack.

## 4. S21 experiment log (budget: 3 experiments; voided runs disclosed)

- **Exp 1** forensic replication — PASS (above).
- **Exp 2 v1** VOID: baseline pruned against full labels incl. hidden truth; HGB lacked LiDAR bands.
- **Exp 2 v2** VOID: leakage canary FAIL — ring300 catalogue-density AUC **1.00**
  (`evidence/s21_lane_result_v2_void_canary.json`).
- **Exp 2 v3a** VOID: ring1000 AUC **0.963** (`evidence/s21_v3a_void_log.txt`). Lesson: *any*
  catalogue-density feature separates by construction when positives sit on catalogue lines.
- **Exp 2 v3b (valid)** — 31 bands + coords only; catalogue used only for masking. Canary max
  AUC **0.580 PASS**. HOLDOUT-DTI (quadrant component-hide, seeds 350–352, 12 cells, 35,900
  withheld positives, evaluator `gems27.metric.dti_binary`): S21-HGB **0.0839** [0.082–0.110
  family] vs dotted-b2 baseline **0.1062**; paired Δ **−0.0223, 95% CI [−0.0309, −0.0137]**
  (wholly negative). Fusion with LiDAR ridge worse (0.0727). Surface AUC up to 0.73 (NE/SE)
  shows real habitat signal, but emission-level recovery loses to the H19-5 surface, which
  itself was built with catalogue-proximity structure — hide-and-recover therefore has a
  home-field bias whose size on genuinely new expert faults is unknown. Under the frozen rule
  (no slot without beating holdout), the lane is **negative**.
- **Exp 3** full emission (37,654 dots, 2.8 px greedy, ring≤2 excluded, 0 on-catalogue):
  format validator **PASS** (all-finite {0,1}, EPSG:32611, 3730×3292, template-exact).
  Uniqueness vs scored/champion rasters **PASS** (≤54.7% 3-px overlap vs S20-NCHC; 28.7% vs
  champion; |Spearman| ≤0.089). **Strict any-raster uniqueness FAIL**: 72.3% of dots within 3 px
  of the unscored dense H37-1 probe-union raster (Jaccard 0.029 — proximity to a dense coverage
  packing, not dot copying; same trap as S19B-RADLIN). Honest disposition: **DO NOT SUBMIT**.

## 5. Download table (what to download, estimate, unique?)

| File | Estimated live score (MODEL PROJECTION — not a score) | Unique vs listed sites? | OK to submit? |
|---|---|---|---|
| `gems28-s21-puhgb-20261026-16bbf281ba9b-allfinite.tif` (this session) | ~0.22 [0.20–0.24] via holdout-ratio to 0.2778 anchor | Yes vs all scored rasters (≤55% overlap); NO vs unscored dense probe (72.3%) | **NO — research only (holdout negative)** |
| Champion-recipe b3 (35,483 dots) | ~0.279–0.285 (repo marginal-model family) | **No — 94% champion dots** | **NO — duplicate; no file shipped** |
| GEMSDOE32 champion itself | 0.2778 OWNER-REPORTED | It is the prior submission | **NO — copying prohibited by brief** |

**Bottom line:** no file in existence today is both (a) genuinely unique and (b) evidenced to beat
0.2778. The only evidenced >0.2778 direction (b3 pruning) is a duplicate. Next session: S21-H2
U-Net (needs GPU) or S21-H4 soft emission on the S21 surface (CPU-cheap), pre-registered on fresh
seeds 360+; obtain an organizer receipt for one anchor file to calibrate all projections.
