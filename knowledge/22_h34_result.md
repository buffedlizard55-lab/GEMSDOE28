# H34 result — the packing-rung arm FAILED its direction control; the threshold framework was confirmed

**Status: CLOSED. Gate FAIL on criterion 2.** Preregistration `knowledge/21_preregistration_H34.md`
(SHA-256 recorded in the evidence file). Evidence `evidence/h34_holdout.json`, seeds 220–229,
40 paired cells (10 seeds × 4 spatially blocked folds), 198 s. No rung change is promoted, no
candidate TIFF is built, no weekly slot is spent. Seeds 220–229 are consumed.

**What did survive, and it is the more valuable result:** the run measures the proxy's own
break-even directly, and the threshold arithmetic is confirmed to ~1 %. That is a *general*
correction to how every future arm is judged, not a property of this one arm.

---

## 1. The gate outcome

| # | Criterion | Requirement | Observed | Verdict |
|---|---|---|---|---|
| 1 | profitability at the live threshold | mean `e(2.828→3.000)` < 0.0548 | **0.01914** | PASS |
| 2 | direction control: next rung must NOT clear it | mean `e(3.000→3.162)` > 0.0548 | **0.02814** | **FAIL** |
| 3a | consistency over seeds | ≥ 8/10 | 10/10 | PASS |
| 3b | consistency over folds | ≥ 3/4 | 4/4 | PASS |
| 4a | monotone emission counts, all cells | yes | yes (40/40) | PASS |
| 4b | OOF probabilities in [0, 1] | yes | yes | PASS |
| 4c | grid pinned (5,167,373 px / 60,988 catalogue px) | yes | yes | PASS |
| | **overall** | | | **FAIL** |

Measured step detail (means over the 40 cells):

| step | Δ emitted | Δ TPw | Δ FPw | `e` | proxy ΔDTI |
|---|---:|---:|---:|---:|---:|
| rung 2.828 → 3.000 | −602.3 | −11.40 | −593.64 | **0.01914** | **−0.000031** |
| rung 3.000 → 3.162 | −1,109.5 | −30.64 | −1,091.25 | **0.02814** | −0.002270 |
| rung 2.828 → 3.162 | −1,711.8 | −42.04 | −1,684.89 | 0.02497 | −0.002301 |

---

## 2. Why the arm failed, and what it means

Criterion 1 passed and criterion 2 failed. Those two together say something specific: **the proxy
agrees that rung 3.0 is not harmful, but it does not agree that 3.0 is where to stop.** Both measured
steps (0.0191 and 0.0281) sit below the live threshold `tau_live = 0.0548`, so under the proxy's own
efficiency ladder you could keep thinning well past rung 3.162 — which is false, since at infinite
spacing DTI goes to zero. The preregistration required the proxy to locate the stopping rung, and it
cannot.

**Why the proxy cannot locate it (diagnosed, quantified).** Removal efficiency scales with the
emission's credit per dot, because `e` is the ratio of credit lost to mass shed and both scale with
how densely the emission covers truth. The proxy detector earns `420.5 / 10,711 = 0.0393` credit per
dot; the H19-5 surface earns `4,791 / 44,090 = 0.1087`, **2.77x more**. The proxy's efficiency ladder
is therefore systematically flatter and lower than the live surface's by roughly that factor: it
measures 0.0191 where the live model gives 0.0272 (ratio 1.4) and 0.0281 where the live model gives
0.0659 (ratio 2.3). A proxy that covers ~20 % of its truth cannot reproduce the marginal cost of
*uncovering* truth on a surface that covers ~39 % of its own. This is the same
`proxy-blind-to-far-field` limitation the repository already records, showing up a second time as a
scale error rather than a sign error.

So the arm closes on its own terms. What the run does *not* do is contradict the rung-3.0 step
itself: both independent estimates put that step's efficiency below `tau_live`, and the corrected
live-anchored model (§3) independently reproduces the stopping rule the proxy missed.

---

## 2b. A modelling error found and fixed while writing this up

Building the test for `src/gems27/operating_point.py` exposed a real bug in the model, and fixing it
changed every number above. It is recorded here because the original figures were reported in
`knowledge/21` §0 and are now superseded.

**The bug.** The model closed the metric with `FP = N - A`, i.e. every emitted pixel not earning
credit is charged full false-positive mass. That is not the metric. The correct closure is
`FP = N - Atilde` where `Atilde = sum over emitted pixels of k(d(p, truth))` is the credit counted
from the *emission* side. The two differ by the crowding excess `Atilde - A`, which the inversion
measures as 0.18x, 0.43x and 1.46x of `A` on the three anchors — a factor-of-eight range.

**The fix, and why it works.** `gamma = Atilde / N` computes to **0.12569 / 0.12576 / 0.12811** on the
three live anchors — constant to 1.9 %. That is exactly what non-selective thinning predicts
(`thinning.dot_thin` discards on-truth and off-truth dots at the same rate, which H32-1's own
evidence confirmed independently: 11.6 % on-catalogue before thinning, 11.7 % after), and it means
`gamma` is **measured, not fitted**. The corrected model is therefore

    DTI = A / (0.8*|G| + 0.2*(1 - gamma)*N + 0.2*A)

**A second error, found the same way.** The retention `r(v)` is measured by thinning the catalogue,
whose dot-to-truth density is 1:1. The H19-5 surface runs ~10 dots per truth pixel, so thinning costs
it proportionally less. Scaling the *loss* by a single density scale `s`,

    A(v) = credit_solid * (1 - s*(1 - r(v)))

reproduces the two non-trivial anchors with implied `s` of **0.8149** and **0.8441** — agreeing to
3.5 %, which is the honest statement of how well one number describes both rungs.

**Result: model A is essentially parameter-free.** `credit_solid = 6,188.80` (inverted credit of a
hash-authenticated 0.1922 score), `|G| = 12,225.9` (blind-lattice calibration) and `gamma` are all
measured; only `s` is fitted. Three anchors, two degrees of freedom, max residual **1.08e-3**:

| anchor | N | gamma | live score | model A | residual |
|---|---:|---:|---:|---:|---:|
| h19-5 solid | 121,131 | 0.12569 | 0.1922 | 0.192201 | +7.6e-07 |
| dotted-h19-5-d1-5 | 60,069 | 0.12576 | 0.2477 | 0.246618 | −1.08e-03 |
| dotted-h19-5-d2-8 | 44,090 | 0.12811 | 0.2600 | 0.260627 | +6.3e-04 |

It also reproduces the inversion's independently-measured `fp_mass` of 38,440.9 as 38,441.6 (0.002 %)
and the truth size without distortion. **Model B, the two-parameter fit used in `knowledge/21` §0, is
rejected**: it fits the anchors to 3.2e-4 but recovers `|G| = 9,698`, **20.7 % below** the blind
lattice, because two free parameters cannot separate the crowding term from the density mismatch.

**What model A says about the rung.** Best rung is **3.0 → N = 41,333**, DTI 0.26346 against 0.26043
at the current rung 2.828, i.e. **+0.00303** (revised up from the +0.00283 in `knowledge/21`). The
winning rung is 3.0 at every `s` in 0.79–0.87, and the step efficiencies are:

| step | `e` | `tau` at the step | worth it | ΔDTI |
|---|---:|---:|---|---:|
| 2.828 → 3.000 | **0.02716** | 0.05495 | **yes** | +0.00394 |
| 3.000 → 3.162 | **0.06592** | 0.05562 | **no** | −0.00145 |

That is the direction control passing at the live operating point: the step to rung 3.0 is
profitable and the next one is not. **This does not overturn the gate verdict** — the gate was
preregistered on the *proxy-measured* efficiency, and §2 records why the proxy cannot supply it. It
does mean the specific rung-3.0 recommendation is supported by two independent lines of evidence
(model A on live anchors; the proxy on 40 cells) that agree on the step and disagree only on where
to stop.

## 3. The result that generalises: the threshold framework is confirmed to ~1 %

Differentiating the official metric gives the removal rule

    drop a pixel class iff  e = |dTPw/dFPw|  <  tau = 0.2*DTI/(1 - 0.2*DTI)

(`metric.inclusion_threshold`; identical derivation re-checked in `src/gems27/operating_point.py`).
This run measures the crossing point directly on 40 independent cells:

> The proxy's base control scores 0.094506, so `tau_proxy = 0.019265`. The measured efficiency of the
> 2.828 → 3.000 step is **0.01914**, and the measured proxy ΔDTI is **−0.000031** — zero to five
> decimal places, at an efficiency within **0.7 %** of the predicted break-even.

The second step is the sign check: `e = 0.0281 > tau_proxy`, and ΔDTI is **−0.00227**, negative as
required. Both signs and the crossing magnitude come out right on data the framework never saw.

**Consequence for every future arm.** `tau` is monotone in DTI. The catalogue-holdout proxy scores
≈ 0.095 → `tau = 0.0193`. The LOSFO far-field harness scores ≈ 0.100 → `tau = 0.0204`. The submission
those harnesses are meant to inform scores 0.2600 → `tau = 0.0548`, i.e. **2.85× more permissive**.
So:

* a **removal** whose proxy-measured efficiency lies in **(0.019, 0.055)** is profitable on the
  0.2600 submission even though every proxy in this repository scores it ≤ 0;
* an **addition** obeys the mirror rule and must *earn* more than `tau`.

Two concrete re-readings follow, both recorded as re-readings of archived measurements and **not**
promoted (see §4):

* **H32-2** (deep magnetic-gradient de-screening, `evidence/h32_2_holdout.json`): archived
  `e = 0.034350`, judged `KEEP` against `tau_proxy = 0.0193` (0/10 seeds). Against `tau_live` it
  flips to `PRUNE`, worth **+0.0047** modelled DTI at a 10 % prune. Its archived proxy ΔDTI of
  −0.003767 with 0/10 seeds is exactly what `e >> tau_proxy` predicts, so the sign is not in dispute —
  only the threshold is.
* **H33-1 (checked after the fact, and it does not survive either).** The parallel session ran the
  preregistered H33-1 prune on seeds 200–209 (`evidence/h33_1_holdout.json`) and refuted it: 0 of 6
  criteria, mean ΔDTI `−0.003014`, 0/10 seeds, 0/4 folds. Its measured removal efficiency is
  **`e = 0.12855`** — not merely above `tau_proxy = 0.0193`, but **2.3× above `tau_live = 0.0548`**.
  So the threshold correction does **not** rescue H33-1, and its refutation is stronger than it
  looked: it fails at the proxy threshold and at the live threshold. Two of its criteria are
  independently damning — the direction control went the *wrong* way (the naive `control_top_p10`
  prune has `e = 0.10104`, i.e. removing the top 10 % by probability destroys **less** credit per
  unit of mass than the kinematically-targeted prune does), and kinematic favourability covers only
  **11.95 %** of the emission against a required 60 %. H33-1 is closed on its own evidence.
* **LOSFO far-field additions** (`evidence/losfo_farfield_diagnostic.json`): measured far-field
  credit/dot **0.0465**. Against the cell threshold (0.0204) that clears; against `tau_live = 0.0548`
  it does **not**. Base-quality far-field dots therefore do not pay for themselves on the live
  submission. `knowledge/20` §3 proposes gating additions against "the inclusion threshold at the
  cell DTI"; this measurement says that gate must use the **live** threshold, or it will admit dots
  that lower the score. This is a correction to the standing plan, recorded for whoever runs it.

---

## 4. What is explicitly not claimed

* **No rung change is promoted.** The preregistration is binding: no confirmation run on 220–229, no
  retuning, no TIFF, no slot.
* **H32-2 stays closed.** §3 re-judges its archived efficiency, but that is a re-reading, not a new
  validation. It is re-openable only on its own fresh decade with its own preregistered gate.
* **`e` transfer is assumed, not proven.** The proxy's truth is catalogue-internal; 100 % of it lies
  at distance 0 from the published catalogue (`proxy-blind-to-far-field`). That the τ *arithmetic* is
  confirmed to 1 % does not prove the *efficiency measured on catalogue truth* equals the efficiency
  against genuinely unmapped faults. Both safeguards required by §5 of the preregistration are
  reported: the direction control fired, and the |G|-sensitivity block
  (`evidence/h34_operating_point.json.truth_size_sensitivity`) shows the winning rung is invariant to
  ±25 % in the truth size — which is why the failure is attributed to the efficiency-transfer
  assumption and not to the fit.
* **The live-anchored fit is a model.** It reproduces three hash-authenticated live scores of the
  H19-5 surface to a maximum residual of 1.2e-4 with two parameters (closed-form leave-one-out error
  ≤ 4.5e-4; fitted |G| = 11,722 against an independent blind-lattice 12,226, −4.1 %), which is
  evidence the geometry is right, not proof. Its `+0.00283` projection for rung 3.0 is stated as a
  model projection and is not promoted.

---

## 5. Next steps (in the order they should be taken)

1. **Do not re-run this arm on 220–229.** If the stopping rung is worth resolving, preregister a new
   arm on 230–239 whose variants span rungs 3.0 → 6.0 and whose gate requires the *crossing* rung
   (where `e` first exceeds `tau_live`) to be identified in ≥ 3/4 folds, with the live-anchored
   model's prediction of that rung recorded **before** the run.
2. **Re-gate the LOSFO addition arms against `tau_live`, not the cell threshold** (§3). This is a
   one-line change to the gate definition and it changes the admission decision at the measured
   far-field quality of 0.0465.
3. **H33-1 is already run and refuted — do not re-spend its decade.** The parallel session executed
   it on seeds 200–209 (`evidence/h33_1_holdout.json`, `knowledge/21_result_H33-1_refuted_2026-10-03.md`):
   0 of 6 criteria, and §3 records that its efficiency `0.12855` fails the *live* threshold by 2.3×,
   not just the proxy one. Its data precondition is satisfied (84,484 records, SHA-256 matched) — the
   hypothesis itself is what failed, not the data. **The pruning family is now exhausted**: H32-2,
   H33-1 and H34 have all been measured and all fail, and `knowledge/20` §1 shows the gap to 0.3195
   is a detection gap no prune can close. Future effort belongs on addition arms (H33-3, H33-4,
   H33-5), gated against `tau_live` on the LOSFO far-field truth set.
4. **Keep taking free pruning gains** while the addition arms are built: H32-1's de-jitter remains
   the holdout-best and the primary download.
5. **Re-verify any future use of `OperatingPoint` against `tests/test_operating_point.py`.** The
   `FP = N - A` closure bug survived a full review cycle because nothing compared the model against
   `metric.dti_binary` on synthetic data. That test now exists (14 assertions, including a guard
   that the naive closure is *not* the metric on all three anchors).
