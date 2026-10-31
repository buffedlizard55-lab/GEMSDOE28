# S31 · 2026-10-31 · unique mid-band candidate, holdout suite, family calibration

**Status in one line:** a new unique GeoTIFF was generated from a frozen rule adjudicated by a
fresh hide-and-recover holdout suite, passed the independent byte gate, and is **OK to download
and submit**. Its score is **NOT ESTABLISHED**; its calibration projection is **NOT ESTIMABLE**
(out of range). No weekly slot was spent.

Artifacts: `docs/candidates/gemsdoe28-s31-midband-random-budgetfill-20261031-zeros.tif`
(SHA-256 `665abda6f0acdac857bb3e3c7433085362408a6393b21c3f26fd5246d3c6774e`),
`docs/s31-executive-summary.html`, `evidence/s31_{seed_audit,holdout,calibration,build,gate,run_card,summary_table}.json`.

## 1. Why this session exists (prompt requirements mapped)

| Requirement | Where satisfied |
|---|---|
| Generate a UNIQUE TIF (never copy) | EXP-2b build; budget ≤ 0.68 per raster enforced during placement (18,494 candidates skipped); independent KD-tree gate re-checked the bytes: max overlap 0.6800 vs 478 registry rasters + all in-repo candidates, zero over 70% |
| Executive summary per site with file/score/uniqueness table | `docs/s31-executive-summary.html` §1 (nine sites: file, USER-REPORTED score, dots, uniqueness verdict, "best to submit?" column) |
| Estimate the score | EXP-2a family calibration (LOO R² 0.555 on 13 USER-REPORTED rows); for the built composition the projection is NOT ESTIMABLE — reported fail-closed, never as a score |
| 3–5 ranked hypotheses, top validated on holdout before any slot | Summary §4 (H-S31-A/B′/C/D/E); EXP-1 adjudicated A, B′, D on 20 fresh-seed splits |
| Explain why 0.2778 is highest and whether it can be beaten | Summary §2 (verified subset/prune mechanism; +0.0288 theoretical FP removal explains the +0.0070 observed) and §5 (association direction) |
| Parallel-run protocol (lane, labels, canary, run card, budget) | Lane registered in `registry/current_session.json`; labels throughout; canary PASS; `evidence/s31_run_card.json`; 3/3 experiments |

## 2. EXP-1 results (HOLDOUT-DTI, seeds 400–404, 20 splits, canary PASS ≤ 0.525)

| Arm | Pooled DTI | Δ vs base | Reading |
|---|---|---|---|
| base (H33-2 as-is) | 0.00189 | — | reference |
| prune3 / prune5 / prune3_strainkeep | 0.00186 / 0.00174 / 0.00180 | −0.00003 / −0.00016 / −0.00009 | prune >3 px ≈ neutral; passes the frozen tolerance, so the build prunes |
| fill_shear / fill_rtp / fill_tmi (far ≥6 px) | 0.00428 / 0.00449 / 0.00468 | +0.0024–0.0028 | all WORSE than matched far random (0.01048) — far geophysical priors are anti-informative here |
| fill_mid_shear (prior, (3,6] px) | 0.01548 | +0.0136 | does NOT beat its random control |
| **fill_mid_random (uniform random, (3,6] px)** | **0.01575** | **+0.0139** | **argmax among buildable arms** |

The decisive finding: **the distance band carries the value, the prior adds none** (canary AUC
0.507 for the shear edge). The frozen rule produced no eligible prior, so the build adopted the
winning control arm's rule — uniform random mid-band placement — as a documented post-hoc
amendment (`evidence/s31_build.json.frozen_rule.post_hoc_amendment`). Known bias, restated:
hidden holdout pieces are catalogue-internal, so this overstates near-catalogue value relative to
genuinely new expert faults. It is used for paired arm ranking only.

## 3. EXP-2a calibration (PROJECTION, never a score)

- Rows: 13 nine-site rasters with USER-REPORTED scores ≥ 0.20; every SHA-256 recomputed from
  local bytes (18 scored rows total; 5 low-score rows excluded from the primary subset).
- Model: score ≈ 0.0580 + 1.809 × frac_mid36 (fraction of dots in (3,6] px of the catalogue).
  LOO R² = 0.555; 4-feature 18-row global model rejected (LOO R² = −1.07).
- Checks: solo field projects 0.2663 vs 0.2708 reported; H33-2 projects 0.2804 vs 0.2778
  reported; the verified prune direction is reproduced (+0.0141 projected vs +0.0070 reported).
- **Irregularity flagged:** the S30 far-fill candidate (`gemsdoe28-s30-catfar65-budgetfill`)
  has frac_mid36 ≈ 0 → projects ≈ 0.058–0.19, far below the 0.2778 parent. The two merged S30
  blocks disagreed on "OK to submit"; this session adds quantitative doubt to the "yes" branch.
  Not adjudicated here (no receipt).
- The S31 composition (frac_mid36 = 0.413) is **outside** the observed family range
  (0.092–0.123) → projection declared NOT ESTIMABLE, fail-closed. Direction only.

## 4. The built file

- Kept: H33-2 dots > 3 px from the catalogue (35,483 = 37,654 − 2,171 shell dots).
- Filled: 17,085 uniformly random cells in the (3,6] px band (reproducible, seed 3101), never on
  the catalogue, never on parent dots, per-raster budget ≤ floor(0.68 × 52,568).
- Gate (independent): validator hard checks pass; no NaN inside; values ∈ {0,1}; max overlap
  0.6800 (`gems24-h24-0-mirror-h19-5-group-best…allfinite`); density rank-corr max 0.875 < 0.90.

## 5. Limitations

- The mid-band bet is unproven on the real scorer: the holdout is catalogue-internal and the
  calibration association is out-of-range here. Both point the same direction; neither is a receipt.
- Uniqueness is measured against the owner's published registry + in-repo candidates only.
- Weekly cap unknown; slot selection is the owner's separate step.
