# H37-3 far-field licence result — REFUTED as a promotable arm, but the mechanism is real and small

**Preregistration:** `knowledge/34_preregistration_H37-3_licence.md`, frozen at commit `0788eec` before
any decision seed was touched. **Run:** `scripts/run_losfo_harness.py --seeds 260-264 --euler-licence
evidence/h31_1_euler_clusters.csv`, exit 0, 5 seeds × 4 folds = **20 paired cells**, ≈13 min. **Evidence:**
`evidence/losfo_h37_3_licence.json`; integrity record `evidence/h37_3_licence_integrity.json`;
analysis `scripts/analyze_h37_3.py`.

## 1. Frozen criteria

| id | criterion | result | verdict |
|---|---|---|---|
| **C1** | mean paired ΔDTI(`base+licence` − `base`) > 0, ≥15/20 cells, ≥4/5 seeds | **+0.000576** ±0.000451, **13/20 cells**, 5/5 seeds | **FAIL** (cells) |
| **C2** | pooled credit per added dot ≥ `τ_live` 0.0548 | **0.031157** (57 % of the bar) | **FAIL** |
| **C3** | mean paired ΔDTI(`licence` − `random_control`) > 0, ≥15/20 cells | **+0.000699** ±0.000452, **16/20 cells** | **PASS** |
| **C4** | integrity | same-seed base arms bit-identical to the pre-patch harness; fresh-decade base arms within the documented LOSFO spread | **PASS** |

Pre-registered interpretation (`knowledge/34` §5): **C1 fails → H37-3 is REFUTED as a promotable arm,
and rank-3 H37-2 becomes the next arm.** That is what is recorded, with the nuance below stated in the
same breath rather than buried.

## 2. What the numbers actually say

* **The licence carries a real far-field signal.** `C3` passed with 16/20 cells: dots placed by the
  depth-coherence licence earned **0.0312** credit each against **0.0189** for the same number of dots
  placed at random inside the *same* off-catalogue eligible region — a **1.65×** ratio. This is the first
  positive-signal far-field result in the repository: a per-cluster statistic built from SI-0 Euler
  depth *dispersion* does place dots better than chance off the catalogue.
* **It is far too small to pay.** 0.0312 credit/dot is 57 % of the live break-even 0.0548. Mechanically,
  adding the arm's 296 dots/cell-equivalent to the shipped `0.2600` file is **not** neutral-to-positive
  but *negative*: projected live DTI 0.260627 → **0.260294** (−0.000333 at 296 dots; −0.001317 at
  four times that; −0.006271 at the arm's full 5,916-dot scale). The far-field break-even at this
  operating point is lower (0.0211, which the licence clears by 1.48×), which is exactly why the live
  bar is the one that decides.
* **C1 failed only on the spread requirement**, not on the sign: the mean is positive, all five seeds
  are positive (+0.000588, +0.000275, +0.000660, +0.000307, +0.001051), and 13/20 cells are positive.
  The pre-registered threshold (15/20) was chosen to prevent promoting a one-fold artefact, and one fold
  **is** negative: `NE_LidarGapHeavy` −0.000390 against `NW` +0.001186, `SE` +0.000893, `SW` +0.000617.
  That fold is the repository's known hardest quadrant (dense LiDAR-gap heavy terrain), so the honest
  reading is "real but fold-fragile and below the bar", not "zero".
* **Integrity is clean.** The patched harness (licence enabled) reproduces the pre-patch harness's base
  arms on the identical spent-seed panel (seed 181, 4/4 cells, both detectors, all four aggregate
  statistics equal to the last bit: `losfo` DTI 0.10818811971962443, `leaky` 0.09997855786881087), and
  the fresh-decade base arms sit within the documented LOSFO seed-to-seed spread (+3.5 % / +7.0 % against
  −12 %…+20 %). The run's own assertions (`licence ∩ base = ∅`, `licence ∩ known = ∅`,
  control ∩ base = ∅) held in all 20 cells.

## 3. Decision taken

* H37-3 is **not promoted, no slot, no build**. It is recorded as `refuted_as_promotable` with the
  positive mechanism note attached, because a future arm could reuse the statistic at a *lower* rate:
  the marginal credit of the 1,435-candidate licence is real, and the loss here is a *rate* problem
  (0.031 < 0.055), not a *placement* problem.
* **Rank-3 H37-2 (concealed-fault conjunction) becomes the next arm** per the preregistration. Note for
  its design: it must be evaluated on the LOSFO harness from the start, and its licence rate must be
  sized so that the expected credit per dot clears 0.0548 — the H37-3 lesson is that a 300-dot-per-cell
  licence at 1.65× random is still a loser.
* Seed ledger: **260–264 are spent by this test; 265–269 remain free.** The arm did not touch 210–214.
* `knowledge/31_hypotheses_session13.md`'s ranked table is updated: H37-3 → *tested, refuted as
  promotable (mechanism positive, 1.65× random, 0.031/dot vs 0.0548 bar)*; H37-2 → next.

## 4. Reusable artefact and its limits

* `scripts/run_losfo_harness.py --euler-licence <csv>` is now a general **positive-licence tester**: it
  takes any point set, applies the frozen spacing and exclusions, and reports paired ΔDTI against both
  a raster-cascade base and a same-count content-blind control, at matched count, on the same far-field
  truth. H37-2 can be evaluated with it by supplying a different candidate point set.
* Limits, unchanged from the preregistration: the harness packs the detector's ridge pool, not the
  shipped H19-5 surface; LOSFO's 600 m buffer is a hard far-field protocol; and the licence's three
  thresholds were frozen before the run, so this is a test of *that* rule at *that* rate — a lower-rate
  variant is a new preregistration, not a re-threshold of this one.

*No-hallucination statement: every number above is read from `evidence/losfo_h37_3_licence.json`,
`evidence/h37_3_licence_integrity.json`, `scripts/analyze_h37_3.py` output, or the committed constants
of `knowledge/34`; the live-DTI projections use the repository's own metric constants
(`N` = 44,090, `|G|` = 12,226, 0.260627) and the standard first-order form
`ΔDTI = ΔN·(c − 0.2·DTI)/D`.*
