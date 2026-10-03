# Preregistration — H37-1: metric-aware dot packing (frozen before any seed was spent)

**Session 13 · 2026-10-03. Frozen before the runner was executed. Seeds `250–259` are reserved for this
gate and are not touched by anything else in this session.**

Status of the seed ledger at freeze time: spent `100–214`, `220–239`, `240–249`; free `215–219`,
`250+`. The exploratory passes below used **only** the spent seeds `181` and `185`, so the gate decade
is untouched.

---

## 1. The hypothesis

The pipeline's emission step is content-blind. `gems27.thinning.dot_thin` keeps a pixel iff no
already-kept pixel is closer than `min_dist`, traversing candidates in **ascending raster index** and
seeding a breadth-first cascade at the lowest index of each 8-connected component
(`src/gems27/thinning.py`). The detector's probability never influences which candidates survive; only
their position in memory does.

**H37-1** replaces the packing rule — and *only* the packing rule — with a lazy-greedy **maximum
expected coverage** of the detector's probability field under the official competition kernel
(`k(d) = max(1 - d/300 m, 0)`, `R = 3 px`), at a **matched emission count** and with the **same**
already-validated `H27-4` blind 1-px catalogue-flank prune applied afterwards:

```
gain(x | S) = sum_q p(q) * max(0, k(|x - q|) - C(q)),   C(q) = max_{y in S} k(|y - q|)
```

This is the expected distance-weighted true-positive mass of the official metric under the detector's
own field, so the packing objective and the scoring rule are the same object. `gain` is monotone and
submodular (Nemhauser, Wolsey & Fisher 1978, DOI `10.1007/BF01588971`), so the greedy order carries the
classical `1 - 1/e` guarantee and the lazy evaluation (Minoux 1978, DOI `10.1007/BF01588962`) selects
the same set cheaply. Implementation: `src/gems27/packing.py` (tests: `tests/test_packing.py`,
including a brute-force `(1 - 1/e)` check on a 14×14 instance).

The physical claim is *not* new geology. It is that the existing calibrated surface is being sampled
inefficiently. Under the metric a dot is worth what it covers; the current rule spends dots on
positions chosen by memory order.

## 2. What the exploratory passes measured (spent seeds 181 and 185, 8 cells)

`scripts/explore_packing_h37.py`, `_v2.py`, `_v3.py` → `evidence/_scratch/packing_h37_explore*.json`.
All variants are **count-matched** to the reference emission within each cell (mean N `12,230.125`
unless stated), so these are layout comparisons, not budget comparisons.

| Variant | Field covered | Pool | Budget | Mean ΔDTI vs `base_oof_d280` |
|---|---|---|---:|---:|
| `greedy_prob` | — (probability order + hard spacing) | top-k | matched | **−0.00272** |
| `cover_topk` | detector probability | top-k (same as base) | matched | −0.00024 |
| `cover_allridge` (**`cover_prob`**) | detector probability | **all ridge px** | matched | **+0.00933** |
| `cover_allridge` | detector probability | all ridge px | ×1.5 | **+0.01333** |
| `cover_allridge` | detector probability | all ridge px | ×2.0 | +0.01186 |
| `cover_allridge` | detector probability | all ridge px | ×0.75 | +0.00210 |
| `cover_allridge` | detector probability | all ridge px | ×0.5 | −0.00976 |
| `index_allridge` | — (raster order, same rule as base) | all ridge px | matched | **−0.04731** |
| `cover_binary` | binary ridge set | all ridge px | matched | −0.03561 |
| `cover_smooth` | Gaussian(σ=2) ridge set, binary-derived | all ridge px | ×1.5 | −0.02103 |
| `cover_prob_anywhere` | detector probability | all active px | ×1.5 | +0.01737 |
| `control_random_n` | — (uniform random) | top-k | matched | −0.01799 |
| `control_oldrule_1p5n` | — (raster order, bigger pool) | top-k ×1.5 | ×1.5 | +0.00539 |

Three readings, each falsifiable and each already tested once:

1. **Direction is not "use the probability".** Ranking by probability with the same spacing rule loses.
   Coverage, not ranking, is the active ingredient.
2. **The field must be the detector probability.** Covering the binary ridge set (−0.036) or a
   Gaussian-smoothed binary set (−0.021) is much worse than doing nothing, so this is not a
   geometry-only trick that could be applied to an arbitrary binary surface.
3. **The pool matters.** Coverage on the same top-k pool as the reference is neutral (−0.0002), while
   coverage over the full ridge pool gains. The reference rule collapses (−0.047) on the full pool, so
   the two rules are not interchangeable at a different pool size — the pool and the packer must be
   frozen together.

## 3. Frozen variants (all per cell of the standing 4-quadrant, component-hidden holdout)

Shared, unmodified from `scripts/run_h36_1_holdout.py`: the footprint, the 4-quadrant folds, the OOF
`HistGradientBoostingClassifier` (600 m buffer, `neg_ratio=10`, seed 2026, unchanged), `ridge_nms`
(σ = 1.0), `PRE_THIN_FRAC = 0.0245`, `THIN_D = 2.8` for the reference, and the `build_flank_mid_mask`
partition verbatim.

| Name | Definition | Role |
|---|---|---|
| `base_oof_d280` | `dot_thin(top-k ridge pool, 2.8)` | reference |
| `rung30_blind_r1` | `dot_thin(top-k ridge pool, 3.0) & ~(d_cat <= 1)` | **incumbent** (H36-1 winner) |
| **`cover_prob_r1`** | `packing.coverage_greedy(ridges ∩ active, oof_prob, N_pre(rung30)) & ~(d_cat <= 1)` | **PRIMARY** |
| `cover_prob_1p5n_r1` | same, `n_target = 1.5 × N_pre(rung30)` | dose (report only) |
| `cover_prob_pool3x_r1` | pool = top-`3k` ridge px by probability, otherwise as primary | pool-density probe (report only) |
| `control_random_matched_n` | `n_target = N_pre(rung30)` pixels drawn uniformly from the ridge pool, then the same prune | **content-blind control** |
| `cover_prob_anywhere_r1` | pool = all active px (off-ridge allowed), otherwise as primary | exploratory ceiling (never promotable) |

`N_pre(rung30)` is measured inside the run for each cell, so the primary and the incumbent start from
exactly the same dot count; the difference between them is the layout alone.

## 4. Frozen criteria

* **G1 — direction.** `mean ΔDTI(cover_prob_r1 vs incumbent) > 0` over all 40 cells.
* **G2 — promotion.** `g(cover_prob_r1) − g(incumbent) ≥ +0.0005` where `g(·)` is the mean paired ΔDTI
  against `base_oof_d280` (the same +0.0005 margin H36-1 used).
* **G3 — consistency.** `cover_prob_r1` beats the incumbent in `>= 8/10` per-seed means **and** in
  `4/4` folds.
* **G4 — content control.** `g(cover_prob_r1) − g(control_random_matched_n) >= +0.0005`, i.e. the
  placement carries information that a random subset of the same size does not.
* **G5 — integrity.** In every cell: emission ⊆ active area, zero overlap with known catalogue pixels,
  `> 0` pixels, and `|cover_prob_r1 before the prune| == N_pre(rung30)` exactly (the budget matcher
  worked). Any violation fails the gate regardless of the metric.
* **Report-only, not gates:** the incumbent's own `g` on the fresh decade (instrument reproducibility
  against its `+0.002599` on seeds `240–249`); the dose and pool-density variants; the off-ridge
  variant.

**Decision rule.** All of G1–G5 pass → promote the rule; build the artifact by applying the *same*
packer and the *same* prune to the full-footprint surface, and report the projected live range as a
range, not a point. Any of G1–G5 fails → record the refutation, build nothing, spend no slot, and do
not retune on `250–259`.

## 5. What a pass would NOT establish (written before the result)

1. **It is not far-field evidence.** The standing holdout hides catalogue components interleaved with
   the known catalogue, so **100 % of its truth lies at distance 0 from the published catalogue**
   (`evidence/arm_habitat_decomposition.json`; `registry/irregularities.json:
   interleaved-holdout-has-no-far-field-truth`, severity high). A coverage objective that targets the
   detector's own field is *a priori* favoured by that protocol, because the detector was trained on
   the surrounding catalogue. This is the single most likely way a pass here is wrong.
2. **It is not a live score.** The projection uses owner-reported anchors and the H34 closure
   (`knowledge/22_h34_result.md`) with its own registered linearisation error.
3. **It is not a statement that H19-5 is misplaced.** Only the *selection within* the candidate pool
   changes; the geological content of the pool is unchanged in the matched-N variant.
4. **Ten seeds and four folds still cannot resolve ~0.0005.** The LOSFO far-field harness measured
   ±12 % per-fold spread (`knowledge/20_strategy_after_reachability_frontier.md` §3.2).

## 6. Disclosure

* Explorer scripts are committed (`scripts/explore_packing_h37.py`, `_v2.py`, `_v3.py`) with their
  seeds on the command line; the variant set above was chosen *after* those passes and *before* the
  gate, which is the same select-then-confirm order H35-6 used.
* The exploratory seeds `181`/`185` are inside the already-spent range `100–214`.
* `K_SMOOTH_SIGMA = 2.0`, `PRE_THIN_FRAC = 0.0245`, `THIN_D = 2.8`, kernel radius `3.0 px`, and the
  `1.5×` dose were all fixed by the passes above; none of them is retuned inside the gate.
* No DrivenData access, no hidden truth read, no submission slot used by this gate.
