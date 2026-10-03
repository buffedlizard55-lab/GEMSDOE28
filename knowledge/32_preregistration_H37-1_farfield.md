# Preregistration — H37-1 far-field falsification test (LOSFO packing diagnostic)

**Written before the run.** This document freezes the instrument, the arms, the decade and the
decision rules for a **diagnostic falsification test of the already-built H37-1 artifact**. It cannot
promote a new arm and it spends no weekly submission slot. Its only job is to answer one question:

> Does the H37-1 packing advantage survive when *no* hidden truth lies within the detector's buffer?

## 1. Why this test exists

H37-1 passed its frozen interleaved gate on fresh seeds 250–259 (`knowledge/30`,
`evidence/h37_1_holdout.json`): the maximum-coverage packing rule earned **+0.007289** mean OOF ΔDTI
against the same-run `d=2.8` reference, **+0.004614** over the H36-1 incumbent, 4/4 folds and 10/10
seeds, while the content-blind matched-`N` control scored **−0.044684**.

The standing caveat, registered as `h37-1-is-proxy-favoured-by-construction` in
`registry/irregularities.json`, is that the interleaved protocol hides catalogue components *in place*:
`evidence/arm_habitat_decomposition.json` measured that **100 %** of its hidden truth lies at distance
**0 px** from the published catalogue. An objective that maximises coverage of a detector field trained
on that same catalogue is therefore a priori favoured by the protocol, and the +0.007289 could be
catalogue interpolation rather than a transferable emission improvement.

`src/gems27/losfo.py` provides the only instrument in this repository whose truth is genuinely far
field: held-out **whole fault systems** are removed from the training labels together with a
**600 m (6 px) buffer**, so every evaluated pixel of truth is ≥ 6 px from any positive label the
detector saw. The stored run (`evidence/losfo_farfield_diagnostic.json`, seeds 210–214) measured the
base cascade at **credit/dot 0.046499**, below the live break-even τ = 0.054852 — i.e. at that
operating point added dots do not pay — and its habitat check confirmed a minimum truth-to-known
distance of 8 px with 90 % of dots ≥ 300 m from known.

## 2. Frozen instrument

* Script: `scripts/run_losfo_harness.py` with the additive `--packing-variants` switch. The base arms
  (`losfo`, `leaky`) are computed by the unmodified code path; the switch only *adds* arms.
* Decade: **seeds 210–214**, the harness's dedicated LOSFO decade (already spent by the stored
  diagnostic; this test therefore consumes no hypothesis-gate decade and no free seed).
* Detector: `oof_detector.fit_predict_oof_probabilities` + `ridge_nms(sigma=1.0)`, `PRE_THIN_FRAC`
  0.0245, `thin_d = 2.8`, LOSFO buffer 600 m, fold structure from `holdout.make_quadrant_folds`.
* Per seed and fold (20 cells), the four arms draw from **one identical candidate pool** — the top
  budget fraction of `ridge & active` by detector score, exactly the pool the base arm packs. The
  script asserts that thinning that pool reproduces the base arm byte-for-byte
  (`thinning.dot_thin(pool, 2.8) & active == base`), so any difference between arms is *ordering or
  objective only*, never pool membership.
* Matched dots: every variant is truncated at `n_base = int(base.sum())` for its own cell.

## 3. Arms (per detector: `losfo` = honest, `leaky` = control)

| arm | rule |
|---|---|
| `base` | shipped cascade: `thinning.dot_thin` in raster order (the existing reference) |
| `prob_order` | same spacing rule, candidates visited by descending detector score |
| `random_order` | same spacing rule, seeded random visit order (content-blind control) |
| `max_coverage` | `packing.coverage_greedy(pool, prob, n_base)` — H37-1's rule, the arm under test |

`leaky` repeats all four with a field trained on the unmasked catalogue, so the contrast
`losfo vs leaky` measures how much of the packing gain is catalogue-adjacent.

## 4. Frozen decision rules

* **F1 — the falsification test.** Under `losfo`, mean paired ΔDTI(`max_coverage` − `base`) **> 0**.
  If this fails, the proxy-artefact explanation stands for H37-1.
* **F2 — content, not merely non-raster order.** Under `losfo`,
  mean ΔDTI(`max_coverage` − `random_order`) **≥ +0.0005**. If F1 holds but F2 fails, the honest
  description is "any non-raster order helps", not "evidence-weighted coverage helps".
* **F3 — spread.** `max_coverage` improves over `base` in **≥ 15 of 20** cells and in **≥ 4 of 5**
  seeds (seed mean over its four folds).
* **F4 — report-only contrast.** The same three quantities under `leaky`, plus the dose context
  (the stored run's credit/dot 0.046499 vs τ_live 0.054852). No criterion attaches to F4; it is
  recorded so the two fields can be compared and so future arms can cite it.
* **F5 — integrity.** (a) The unmodified arms must reproduce the stored diagnostic to numerical
  tolerance: `losfo` mean DTI 0.09973627, `sum_tp` 11160.553996, `credit_per_dot` 0.04649901 and
  `leaky` mean DTI 0.10154756, `sum_tp` 11291.302992 on the same decade. (b) Every arm is a subset of
  its pool and of `active`, with zero overlap with the `known` catalogue pixels. (c) All arms are
  deterministic (the control has an explicit seeded order).

## 5. Pre-committed interpretation

* **F1 fails** → the +0.007289 interleaved gain does not transfer off the catalogue. The H37-1
  artifact stays *built and audited* but is **demoted** in the manifest to the conservative slot, the
  site and README carry the far-field number next to the interleaved one, and the arm's status becomes
  "catalogue-local, not far-field validated".
* **F1 passes and F2 fails** → H37-1's rule is real but weaker than advertised; the honest claim is
  that evidence-weighted packing beats the raster cascade far field, without a claim that the
  *coverage objective* (rather than any sensible order) is the active ingredient.
* **F1 and F2 pass** → the packing rule's advantage is not explained by catalogue interpolation; the
  H37-1 promotion stands and the far-field number is quoted alongside the interleaved one in
  `knowledge/30`, the README and the site.
* **F5(a) fails** → the extended script has changed the base path; the run is void, the diff is
  reverted, and the test is re-frozen before any further run.

## 6. What this test cannot establish

* It cannot show that H37-1's *shipped* emission (the H19-5 pool + full-fit detector field) is
  far-field optimal: the harness's pool is the detector's own ridge set, not the H19-5 surface, and
  the honest field is out-of-fold while the shipped weight field is full-fit on all labels.
* It cannot certify the live score. The stored LOSFO credit/dot (0.046499) is below the live
  break-even, and a far-field packing gain at a `d=2.8` budget does not by itself prove that a
  different budget would transfer.
* It says nothing about the dose axis (1.5×N), which the interleaved gate already recorded as
  fold-fragile (3/4) and which is deliberately **not** re-run here.

*No hallucination statement: every number above is quoted from a committed artifact in this
repository — `evidence/h37_1_holdout.json`, `evidence/losfo_farfield_diagnostic.json`,
`evidence/arm_habitat_decomposition.json`, `registry/irregularities.json` — and none was fetched from
a network source. The two 1978 packing references cited in `src/gems27/packing.py` remain
manual-review links (sandbox egress to DOI hosts fails).*
