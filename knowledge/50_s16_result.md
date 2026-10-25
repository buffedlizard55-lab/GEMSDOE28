# Session 16 result — H40-1 edge-migration lane: NEGATIVE (gate + uniqueness)

**Date:** 2026-10-25. **Lane/preregistration:** `knowledge/49_preregistration_H40-1_migration.md`
(frozen before any fit). **Experiments used:** 3/3. **Slot spent:** none.

## Why 0.2778 won (re-verified this session, not copied)

Fetched `gemsdoe32-h33-h33-2-b2-…-e5eb6e7e-zeros.tif` again this session; SHA-256
`c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9` matches GEMSDOE32's
audit pin. Byte forensic (S15, reproduced inputs): champion = `solo-r1` (OWNER-REPORTED
0.2708) minus the d_cat ≤ 2 px ring (2,545 dots, 0 added); `solo-r1` = `d2-8`
(OWNER-REPORTED 0.2600) minus the d_cat ≤ 1 px ring. Constant ≈ +2.76×10⁻⁶ DTI per
deleted flank dot ⇒ the best score in the family is **emission hygiene, not detection**.
A ring-3 prune would be >95 % within 3 px of the champion — a duplicate under the
prompt's rule — so it was not built. All scores here are OWNER-REPORTED; none is
ORGANIZER-CONFIRMED (no receipt exists in any fetched repo). The prompt's 0.4413 and
0.3195 leaderboard maxima still conflict and neither was verified this session.

## Experiment 1 — canary (`evidence/s16_canary.json`) PASS

4 label-free migration bands (TMI/gravity × signed-migration/coherence). Single-feature
AUC vs LOSFO seed-300 withheld systems: 0.489–0.535 (max(AUC,1−AUC) ≤ 0.535 ≪ 0.90 —
no leakage; honestly weak univariate signal, like S15). Max |Spearman| vs in-stack
bands 0.42 — not surface duplicates at band level.

## Experiment 2 — frozen LOSFO gate, seeds 300–304 (`evidence/s16_h40_losfo_gate.json`) FAIL

HOLDOUT-DTI (evaluator: shared `run_losfo_harness.eval_set`; α=0.2, β=0.8, 300 m
triangular kernel, pooled; 81,101 withheld truth px over 20 cells):

| arm | pooled DTI | credit/dot | dots |
|---|---:|---:|---:|
| D0 (32-band) | 0.095387 | 0.04544 | 239,192 |
| D1 (+4 migration bands) | 0.096648 | 0.04608 | 238,921 |

Pooled Δ **+0.001261**, mean paired **+0.001163**, 95 % CI **[−0.00337, +0.00633]**,
9/20 cells, seed means {300:+0.0002, 301:+0.0030, 302:+0.0125, 303:−0.0107, 304:+0.0009},
fold means only SW positive (+0.0095). Gate: G1 PASS, **G2 FAIL**, G3 PASS, G4 PASS,
G5 PASS → `gate_passed=false`. The mean is carried by one fold/seed pair; the frozen
spread rule correctly rejects it. No retuning was done or is permitted on these seeds.

## Experiment 3 — build + uniqueness (`evidence/s16_candidate_build.json`) FAIL

`gems28-h40-1-migration-b1-20261025-5f2efa891ce7-nan.tif`, 37,694 dots. Format validator:
**all hard checks PASS** on both variants (no NaN inside footprint; values exactly
{0,1} ⊂ [0,1]; EPSG:32611 / 3730×3292 / template transform; 0 dots on catalogue).
Uniqueness: Spearman(prob_D1, prob_D0) = **0.990 > 0.90**; **91.3 %** of dots within
3 px of the dense probe `52a13184267e` (89.5 % vs `1113fba5f6cb`) — duplicate drift
under the strict any-registry-raster rule → logged, stop. (Vs the *scored* champion it
is 41.3 % — the binding constraint is again the dense unscored probe blanket, the same
irregularity S15 recorded; the selector, not this session, may re-define "registry".)

**Verdict: `negative`.** TIF published inspection-only, banner **🔴 DO NOT SUBMIT**;
one-click primary (H36-1) unchanged. If the operator submits anything manually, the
primary's **all-finite** variant is the range-safe file (no NaN anywhere; strict
whole-array [0,1] PASS) — the NaN-outside variant is the plausible cause of the
owner's earlier “Predicted values must be in range [0, 1]” portal error.

## What would actually beat 0.2778 (PhD-level read of all evidence)

1. The remaining catalogue-flank rings are worth ≈ +0.006/ring *if* the owner-reported
   ladder extrapolates — but every such file is a >90 % duplicate of the champion and
   cannot be claimed as a unique submission.
2. Every genuinely new-information addition tested by this group (H39-1 depthslice,
   H40-1 migration, T-v2, GEMSDOE36 conduits) lands below τ_live ≈ 0.059 credit/dot on
   far-field truth. The detector ridge network itself is the uniqueness ceiling:
   re-derived detectors re-emit the same ridge pixels (Spearman 0.98–0.99).
3. The untested lever with a physical reason to place dots *off* the standard ridge is
   the migration-**extrapolated** surface trace (shift deep ridges back along the dip
   direction to their zero-height position) — H40-1 encoded migration as features but
   still emitted on the GBDT ridge. That is the recommended next preregistration,
   on fresh seeds ≥310, with the extrapolated-placement pool checked for uniqueness
   *before* any detector is trained.
