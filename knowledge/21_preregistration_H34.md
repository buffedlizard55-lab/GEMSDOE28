# Preregistration — H34: packing-ladder rung selection and the operating-point threshold

**Registered 2026-10-03 (Session 10, second arm), before any seed spend.**
Seed decade **220–229** (fresh: 100–159 archived, 160–169 H31-1, 170–179 H32-1 structural,
180–189 H32-1, 190–199 H32-2, 200–209 reserved by `knowledge/19` for H33-1, 210–214 LOSFO).
This document is frozen; the runner records its SHA-256 in the evidence file.

---

## 0. Why this arm exists

Two arithmetic facts, both established in `evidence/h34_operating_point.json` before this
preregistration and independent of any seed:

**Fact 1 — the packing ladder is discrete and is not exhausted.** `thinning.dot_thin` keeps a pixel
iff no already-kept pixel is strictly closer than `min_dist`, so its output changes only when
`min_dist` crosses a distance two integer cells can actually realise (`sqrt(a²+b²)`). There is no
continuum to search, only a ladder of 29 rungs below 8 px. Measuring `N(rung)` on the H19-5 surface
and the credit retention `r(rung)` on the published catalogue (a 1-D curvilinear stand-in for the
hidden fault network) and fitting two unknowns — the solid credit `L` and the truth size `|G|` — to
three hash-authenticated live scores of **that same surface** (0.1922 / 0.2477 / 0.2600) reproduces
all three to a maximum residual of **1.2e-4**, with a closed-form leave-one-out error of at most
**4.5e-4**, and a fitted `|G| = 11,722` that sits 4.1 % below the independent blind-lattice
calibration (12,226). Under that fit the optimum is **rung 3.0 → N = 41,333 px**, i.e. one rung
beyond the shipped `d = 2.8` file (N = 44,090), worth **+0.00283 DTI**. The optimal rung is
**3.0 at every `|G|` in 0.75×–1.25× of the blind-lattice value**.

**Fact 2 — the decision threshold belongs to the artifact, not to the holdout.** Differentiating the
official metric gives the removal rule "drop a pixel class iff its efficiency
`e = |dTPw/dFPw|` is below `tau = 0.2·DTI/(1 − 0.2·DTI)`" (identical to
`metric.inclusion_threshold`). `tau` is monotone in DTI. The catalogue-holdout detector scores
≈ 0.095, so it gates at **tau = 0.0193**; the submission we modify scores 0.2600, so it gates at
**tau = 0.0548** — **2.85× more permissive**. Every prune arm whose measured efficiency falls in
(0.019, 0.055) has been rejected against a threshold that does not apply to the artifact.

Fact 2 is not a licence to excuse a failed arm. It is a scale correction, and it is only usable
because it is stated here, before the run, together with the exact criterion and its direction
control.

---

## 1. Hypothesis

Moving the shipped `d = 2.8` emission one rung out to `min_dist = 3.0` removes 2,757 px
(44,090 → 41,333) that carry **less** credit per unit of false-positive mass than the submission's
own break-even, while the next rung (3.162) removes pixels that carry **more**. Rung 3.0 is therefore
the stopping point, not an arbitrary step.

Direction control: if the effect were simply "thinning is good", rung 3.162 would also pass. It must
not.

---

## 2. Design (frozen)

**Detector.** The repository's frozen 4-fold quadrant out-of-fold protocol, byte-identical to
`scripts/run_h32_1_holdout.py`: `oof_detector.fit_predict_oof_probabilities(foot, labels, fold)`
(model seed 2026, 600 m buffer, `neg_ratio=10`, `HistGradientBoostingClassifier(max_iter=100,
max_leaf_nodes=31, learning_rate=0.08, l2_regularization=5.0)`), then
`ridge_nms(sigma=1.0)`, then `build_oof_dotted_base(..., budget_frac=PRE_THIN_FRAC)`.

**Variants** (all from the same ridge mask and the same budget, only the thinning rung differs):

| variant | `thin_d` |
|---|---|
| `rung_2_828` | 2.8 (the shipped geometry) |
| `rung_3_000` | 3.0 |
| `rung_3_162` | 3.16227766 |

**Seeds.** 220–229 inclusive; 10 seeds × 4 folds = **40 paired cells**. One use only.

**Folds.** `holdout.make_quadrant_folds(footprint)` — NW, NE_LidarGapHeavy, SW, SE — with
`hide_components(..., frac=0.20)` per fold.

---

## 3. Response and analysis (frozen)

For every cell compute `TPw`, `FPw`, `N`, `DTI` per variant with `metric.dti_binary`. Then, per
cell, the **removal efficiency of each rung step**:

    e(a→b) = |TPw(b) − TPw(a)| / |FPw(b) − FPw(a)|

The primary response is `e`, not `ΔDTI`, because `e` is the quantity that transfers across operating
points; `ΔDTI` is reported as a diagnostic and is expected to be negative on this proxy even when the
step is correct (see §5).

Reported per step: mean and median `e` over the 40 cells, `e` per fold, `e` per seed,
`count(e < tau_live)`, and the paired `ΔDTI`.

---

## 4. Promotion gate (frozen, all four must hold)

| # | Criterion | Requirement |
|---|---|---|
| 1 | **Profitability at the live threshold** | mean `e(2.828 → 3.000)` **< 0.0548** (`tau` at the 0.2600 submission) |
| 2 | **Direction control / stopping rule** | mean `e(3.000 → 3.162)` **> 0.0548** |
| 3 | **Consistency** | `e(2.828 → 3.000) < 0.0548` in **≥ 8/10 seeds** and **≥ 3/4 folds** |
| 4 | **Integrity** | `N(3.000) < N(2.828) < N` monotone in all 40 cells; all OOF probabilities finite and in [0, 1]; footprint 5,167,373 px and 60,988 catalogue px as pinned |

Criterion 2 is a **falsification** test, not a formality: if rung 3.162 also clears the threshold the
"optimum" is an artefact and the arm fails.

**On failure:** no confirmation run, no retuning on 220–229, no candidate TIFF, no weekly slot. The
decade is consumed and the result is archived as a closed negative.

**On pass:** the rung-3.0 change is applied to the emission pipeline and carried into the next
candidate build, stacked with the already-validated H32-1 de-jitter. **No weekly submission slot is
spent by this arm alone** — the composite is still an unscored research artifact until the group
decides to spend a slot.

---

## 5. Declared limitation (stated before the run, not after)

The holdout hides **pieces of the published catalogue**, so its truth is catalogue-internal and it
scores ≈ 0.10 while the artifact scores 0.26. The proxy therefore tests the *physical* efficiency
`e` of a rung step against a threshold it does not itself satisfy. Reading the proxy's `ΔDTI` as the
decision variable is the error this arm corrects; reading `e` as the decision variable is still only
valid to the extent that `e` transfers from catalogue-internal truth to genuinely unmapped faults.
That transfer is **assumed, not proven** — the repository's own `proxy-blind-to-far-field`
irregularity records that 100 % of holdout truth lies at distance 0 from the catalogue.

Accordingly the gate uses `e` with **two** independent safeguards: the direction control
(criterion 2), which fails if the rung ordering is an artefact, and the |G|-sensitivity block in
`evidence/h34_operating_point.json`, which shows the winning rung is invariant to a ±25 % change in
the truth size. Even on a pass, the projected live gain is stated as a model projection
(`+0.0028`), never as a measured score.

---

## 6. What this arm does **not** claim

* It does not claim to close the gap to 0.3195. `knowledge/20` §1 shows that gap is a **detection**
  gap of ≈ +1,151 px of credit (+24 %), unreachable by pruning at the current marginal efficiency.
  This arm is worth +0.0028 and is taken because it is free and composes.
* It does not claim the catalogue-geometry retention transfer is exact. The retention curve is
  measured on the catalogue; the fit's 1.2e-4 residual on three live anchors is evidence the
  geometry is right, not proof.
* It does not re-open H32-2 for a slot. §0 Fact 2 re-judges H32-2's archived efficiency (0.0344) as
  profitable at the live threshold, but that is a re-reading of an archived measurement, not a new
  validation; H32-2 stays closed unless it is re-preregistered on its own fresh decade.
