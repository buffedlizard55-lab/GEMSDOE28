# 48 — Session 15 result (2026-10-25): H39-1 refuted on its frozen gate; champion forensic stands

Preregistration: `knowledge/47` (freeze commit `dae869b`, before seeds 290–294 were touched).
Run card: `evidence/s15_run_card.json`. Experiments used: 3 of 3. No slot spent.

## 1. What was measured

**Experiment 1 — canary (`evidence/s15_canary.json`).** Five label-free depth-slice bands
(TMI HG at 1 km / 2 km upward continuation, persistence ratio, 1 km tilt, gravity HG at 2 km;
FFT transform verified against analytic exp(−|k|h) decay, `tests/test_depthslice.py`).
Single-feature AUC vs LOSFO seed-290 withheld systems: 0.476–0.543 (canary max(AUC,1−AUC)
≤ 0.543 ≪ 0.90 — no leakage; also honestly weak univariate signal). Max |Spearman| vs any
in-stack band 0.79 (tilt vs tmi) — not duplicates of existing bands.

**Experiment 2 — frozen LOSFO gate, seeds 290–294, 20 paired cells
(`evidence/s15_h39_1_losfo_gate.json`; evaluator `run_losfo_harness.py --s15-depthslice`,
pooled DTI α=0.2 β=0.8, 300 m kernel; truth ≥ 800 m from every known pixel).**
**HOLDOUT-DTI** (not an organizer score), 74,557 withheld truth px pooled over cells:

| arm | pooled DTI | credit/dot | dots |
|---|---:|---:|---:|
| D0 (frozen 32-band) | 0.10310 | 0.04674 | 240,376 |
| D1_nw (D0 + 5 bands) | 0.10193 | 0.04612 | 241,222 |
| D1 (D1_nw + persistence ranking, primary) | 0.10150 | 0.04567 | 243,602 |

Primary contrast D1−D0: pooled **−0.00160**, mean paired **−0.00260**,
95% CI **[−0.00739, +0.00208]** (paired bootstrap, 10k), 9/20 cells, 1/5 seed means, 1/4 fold
means (only SE positive). Frozen gate: G1 FAIL, G2 FAIL, G3 FAIL, G4 PASS, G5 PASS →
**gate_passed = false**. The diagnostic splits the blame: the bands alone cost −0.00170 mean
paired (D1_nw) and the persistence ranking costs a further −0.00090. Independent recompute
from stored cells reproduces every number exactly (max DTI recompute error 0.0), and the D0
arm is byte-identical in result to the harness's untouched `losfo` arm.

**Experiment 3 — build (`evidence/s15_candidate_build.json`).** Full-fit analogue at the
champion's budget: `gems28-h39-1-depthslice-persist-b2-20261025-a86b8ed33727-nan.tif`,
37,695 dots, SHA-256 (nan) `a33fe4c2…`. Format validator: **all hard checks PASS** on both
variants (no NaN inside footprint; values exactly {0,1} ⊂ [0,1]; EPSG:32611 / 3730×3292 /
template transform; 0 dots on catalogue; `verify_downloads.py` overall PASS, 0 failures).
Uniqueness vs registry: only **37.2%** of its dots lie within 3 px of the champion
(e5eb6e7e) — a genuinely re-derived dot set — **but** 76.8% / 79.9% lie within 3 px of two
dense unscored detector-ridge research files already in `docs/downloads`
(`1113fba5f6cb`, `52a13184267e`), and Spearman(prob_D1, prob_D0) = 0.977 > 0.90. Under the
protocol's any-single-raster rule, **uniqueness FAILS** and is logged as duplicate drift
against those two rasters (see §3 for why this reading is conservative but binding).

**Verdict: `negative`** (gate FAIL + uniqueness FAIL; validator PASS). The TIF is published
for inspection, banner-marked **🔴 DO NOT SUBMIT** on the site and in its portal note.
The one-click primary (H36-1) is unchanged.

## 2. Interpretation

1. **Deep-persistent magnetic lineaments do not pay at this operating point — on far-field
   mapped truth.** The named mimic (basement lithologic contacts / dike swarms) is the
   likely contaminant: persistence selects exactly the long-wavelength fabric those produce.
   The result is consistent with H32-2's earlier failure of a shallow/deep magnetic ratio,
   reached from the opposite direction (there as a prune, here as positive evidence).
2. **Scope limit, stated so the negative is not over-read:** LOSFO truth is *mapped* fault
   systems (surface-expressed by selection), so a detector optimised for buried faults is
   graded on the population it is not aimed at. That caveat does not rescue the arm: LOSFO is
   the repository's agreed upper-bound instrument, the frozen reading rule binds, and every
   live owner-reported addition experiment in the group (T-v2 −0.0028, GEMSDOE36 conduits
   −0.0028) agrees that novel dots below τ_live ≈ 0.059 credit/dot lose money.
3. **The champion forensic is the session's durable positive result** (`knowledge/47` §1):
   the group's best owner-reported score (0.2778) is emission hygiene — two catalogue-flank
   rings at a near-constant ≈2.76×10⁻⁶ DTI per deleted dot — not new detection. Any future
   lane that wants to beat it must add credit at > 0.059/dot *and* clear a uniqueness bar
   that this session shows is dominated by overlap with dense detector-ridge probes, not
   with the champion itself.

## 3. Irregularities flagged this session (see `registry/irregularities.json`)

* `s15-leaderboard-top-conflict`: owner prompt states both 0.4413 and 0.3195 as the current
  leaderboard top; neither is verifiable from this sandbox (no DrivenData access). Both are
  recorded as conflicting owner snapshots; no number here depends on either.
* `s15-champion-score-no-receipt`: GEMSDOE32's own audit for e5eb6e7e says UNSCORED /
  projected 0.2747; the 0.2778 association exists only in owner lists. Labelled
  OWNER-REPORTED everywhere; the byte-level construction claim, by contrast, verified exact.
* `s15-uniqueness-dense-probes`: the 70%-within-3px rule is failed against two unscored
  research probes whose dot fields blanket the detector ridge network, while passing easily
  (37.2%) against the actual scored champion. Recorded so the selector can judge whether
  "registry" should mean scored/shipped lanes only; this session applied the strict reading.

## 4. Next (fresh preregistration + fresh seeds 295+ required; 290–294 are spent)

Ranked in `knowledge/47` §2: H39-2 radiometric alteration *lineaments* (object-level, not
GBDT pixels), H39-3 drainage-chain collinearity at 100 m, H39-4 artifact-swap. Any of them
must (i) be frozen in `knowledge/` first, (ii) clear the same LOSFO gate shape, and
(iii) pre-check dot overlap against *scored* lanes and the dense probes before spending seeds.
