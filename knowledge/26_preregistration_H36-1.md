# H36-1 preregistration — the packing-rung re-pack at rung `3.0`, with and without the catalogue-flank prune

Status: **frozen before execution.** Seeds `240–249` are reserved by this file and were never touched
before it was written. No H36 result existed at the time of writing. This file is the protocol; the
runner is `scripts/run_h36_1_holdout.py`, written before the run and not edited afterwards.

---

## 1. What this arm is, in one paragraph

`H34` (`knowledge/21_preregistration_H34.md`, `knowledge/22_h34_result.md`,
`evidence/h34_operating_point.json`) fitted the official metric's two-number operating point to the
three hash-authenticated live scores of the **same** H19-5 surface (0.1922 solid / 0.2477 at `d=1.5` /
0.2600 at `d=2.8`) and concluded that the *optimal packing rung is `3.0`, not the shipped `2.828`* —
worth a predicted `+0.00303` `delta DTI` at `N = 41,333` versus `44,090`. That claim has never been
tested on a spatially-blocked holdout. It is the top entry of `registry/next_hypotheses.json`
`session11_addendum.next_ranked`. This arm tests it, and tests it jointly with the two pruning arms
that H34 *also* re-judged as profitable against the **live** threshold `tau = 0.05499` rather than the
`0.01927` catalogue-proxy threshold.

## 2. A new measurement that changes the arm's meaning (made before this file was written)

`H34` was read, in `registry/next_hypotheses.json`, as "re-thin". That word understates it, and the
difference matters for what the holdout can prove. Measured this session on the full footprint
(`h19_5` surface, `121,131` px, catalogue removed):

| Statement | Measurement |
|---|---|
| the published `0.2600` file `e56ea318af89` **is** `dot_thin(surface, 2.8)` | **exact set equality, 0 px symmetric difference** (44,090 px) |
| `dot_thin(surface, 3.0)` | `41,333` px |
| pixels in rung 3.0 but **not** in the shipped rung | `10,667` |
| pixels in the shipped rung but **not** in rung 3.0 | `13,424` |
| pixels shared | `30,666` (i.e. **58 % of the two sets differ**; `24,091` px change hands) |

So the rung ladder is **not nested**: raising `min_dist` does not merely delete dots, it *re-seeds*
the greedy Poisson-disk packing (lowest raster index per 8-connected component, FIFO) and the whole
cascade re-lays out. `44,090 - 41,333 = 2,757` is therefore *not* "2,757 dots removed"; it is a
24,091-pixel **re-packing**. This is why the arm is worth running even though `H34` predicts only
`+0.003`: a re-pack is a different mechanism from a budget cut, and — unlike a pure thinning — it is
**not reproducible by randomly deleting dots**. The matched-`N` random-drop control in §4 exists to
make exactly that distinction falsifiable.

Floating-point disclosure (this is load-bearing and was checked by hand): `thinning.dot_thin` blocks
offsets whose squared length is **strictly** less than `min_dist**2`, and `math.hypot(2,2)**2`
evaluates to `8.000000000000002`. Calling `dot_thin(s, math.sqrt(8))` therefore blocks the `(2,2)`
offset and returns `41,333`, while `dot_thin(s, 2.8)` does not and returns `44,090`. The rung values
used here are `2.8` and `3.0`, both of which are unambiguous (verified above); no rung in this arm
sits on a `hypot()` knife-edge.

## 3. The hypothesis

**H36-1.** At the live operating point of the `0.2600` submission, the emitted pixel count
`N = 44,090` sits **above** the optimum of the metric's trade between kernel credit `A` and
false-positive mass `0.2 * FPw`. Re-packing the H19-5 surface to rung `3.0` (`N = 41,333`) increases
`DTI`, and the catalogue-flank prunes (`H27-4` blind `d_cat <= 1 px`, `H32-1` mid-segment flank
shadow) remain profitable when applied **on top of** the new rung rather than on the old one.

Physical reading (why a *smaller* emission can be a *better* geological statement): the metric charges
each emitted pixel `0.2` units of false-positive mass but caps its credit at `k(d) <= 1`. The hidden
truth is a sparse 1-px curvilinear network, so at `N = 44,090` the emission already covers ~3.6
emitted pixels per truth pixel; the marginal dot is 2.757/44,090 of the budget earning
`0.03098` credit/px against a break-even of `0.05485`. **Counting fewer, better-spaced dots is a more
honest map of a fault network than a dense raster of the same ridge.** The arm does not claim new
geology; it claims the existing detections are mis-packed.

## 4. Frozen protocol

| Item | Value |
|---|---|
| Script | `scripts/run_h36_1_holdout.py` (new, written before this run) |
| Seeds | **`240–249`** — a fresh, unused decade (verified: no record in `evidence/*.json` mentions any seed `>= 240`; gaps `215–219` and `240–299` were unused, and the 10-seed decade is taken per house convention) |
| Folds | the four spatial quadrants (`NW`, `NE_LidarGapHeavy`, `SW`, `SE`) with the 600 m buffer collar, `holdout.make_split` unchanged |
| Detector | `oof_detector.fit_predict_oof_probabilities` + `ridge_nms(sigma=1.0)` — **unmodified**, so every variant is the same detector and only the emission rule differs |
| Budget | `PRE_THIN_FRAC = 0.0245` — **unmodified** |
| Output | `evidence/h36_1_holdout.json` |
| New source files | `scripts/run_h36_1_holdout.py` only. No file under `src/gems27/` is modified by this arm. |

Variants (all evaluated on identical cells; `g` = hidden truth, `active` = fold `& ~known`):

| Variant | Definition | Why it is in the design |
|---|---|---|
| `base_oof_d280` | `build_oof_dotted_base(..., thin_d=2.8)` | the shipped rung — the reference every delta is measured against |
| `rung30_unpruned` | `build_oof_dotted_base(..., thin_d=3.0)` | the H34 claim in isolation |
| `rung30_blind_r1` | `rung30_unpruned & ~(d_cat <= 1.0)` | the H27-4 prune on the new rung |
| `rung30_flank_mid` | `rung30_unpruned & ~flank_mid` | the H32-1 prune on the new rung |
| `h27_4_blind_r1_d280` | `base_oof_d280 & ~(d_cat <= 1.0)` | the incumbent one-click primary (`8acb75e1f2cc`) |
| `control_random_drop_matched_n` | `base_oof_d280` randomly reduced, **per fold**, to the exact `N` of `rung30_unpruned` | **anti-budget control.** If a re-pack and a coin-flip deletion to the same `N` gain the same, the effect is budget, not packing, and the word "rung" is not earned. RNG namespace `910000 + 10*seed + fold`, disjoint from every holdout-seed namespace (`4242 + fold + 1000*seed`) and from the LOSFO/thermal namespaces; disclosed, not reused for anything else. |
| `control_rung30_protected_only` | `rung30_unpruned & ~tip_or_euler` | **anti-selective control**, inherited from `H35-6`: removes only the *protected* tip / shallow-Euler pixels, i.e. the class the prunes deliberately spare |

`flank_mid` and `tip_or_euler` are the **same** partition used by `scripts/run_h32_1_holdout.py` and
`scripts/build_h32_1_submissions.py` (`build_flank_mid_mask`, copied verbatim into the new runner so
the definition cannot drift).

## 5. Frozen gate, written before the run

Let `G(v)`, `s(v)`, `f(v)` be variant `v`'s mean OOF `delta DTI` versus `base_oof_d280`, its seeds won
out of 10, and its folds improved out of 4. Let `tau_live = 0.054852` (the break-even at the `0.2600`
anchor, `metric.inclusion_threshold(0.2600)`).

**G1 — rung effect.** H36-1's core claim passes iff
`G(rung30_unpruned) > 0`, `s(rung30_unpruned) >= 8`, `f(rung30_unpruned) == 4`.

**G2 — is it packing or merely budget?** The core claim is *upgraded* to "re-packing" and not
downgraded to "budget cut" iff `G(rung30_unpruned) > G(control_random_drop_matched_n)`. If the
control is within `+/-0.0003` of the rung, the result is reported as **budget-only** and the site text
must say so.

**G3 — prunes on the new rung.** A prune variant passes iff `G(v) > 0`, `s(v) >= 8`, `f(v) == 4`, and
its `removed_credit_per_removed_fp < tau_live`. The proxy threshold is **not** used to judge this
(H34's whole point).

**G4 — winner and promotion.** The winner is the member of the candidate set
`{rung30_unpruned, rung30_blind_r1, rung30_flank_mid, h27_4_blind_r1_d280}` with the largest `G(v)`
among those satisfying `s >= 8` and `f == 4`. The winner is promoted to the site's one-click primary
**only if** it also beats the incumbent `h27_4_blind_r1_d280` by `>= +0.0005` mean `delta DTI`
(the seed-to-seed resolution limit recorded in `knowledge/25_preregistration_H35-6...md` §5). Below
that margin the arm is reported as a **tie** and the incumbent stays, because promoting on a gap the
instrument cannot resolve is the exact error `H35-6` was created to fix.

**G5 — anti-selective check.** If `G(control_rung30_protected_only) >= G(winner)`, the selective-prune
reading is unsupported and the evidence file and site must say so, whatever else passes.

**No extension, no re-run on another decade, whatever the outcome.** Ten seeds is the budget for this
question this session.

## 6. What would make this arm wrong

* **The proxy is still a proxy.** The holdout hides published *catalogue* pixels; the live test set is
  expert-labelled faults *outside* the catalogue. A re-pack that helps on catalogue-internal truth
  need not help on off-catalogue truth, because off-catalogue faults are, by construction, the ones
  the surface is worst at. `registry/irregularities.json` already carries `proxy-blind-to-far-field`
  at **high** severity.
* **H34's anchors are owner-reported, not organizer receipts.** The `+0.00303` prediction inherits
  that. The holdout is a different instrument and may simply disagree; a disagreement is a result, not
  a failure, but it must be reported as one.
* **The `4/4 folds` requirement is weak on 10 seeds.** Per-fold seed-to-seed spread was measured at
  `+/-12 %` on the LOSFO harness; a `+0.001` effect can clear `4/4` by luck. G4's `+0.0005` margin is
  the only guard, and it is deliberately conservative.
* **`control_random_drop_matched_n` is a single RNG draw per cell.** It is not averaged over draws, so
  it is itself a noisy comparator. It is used only for the G2 *direction* check, never as a level.

## 7. Disclosure

* Seeds `240–249` are spent here. `215–219` and `250+` remain unused.
* This arm builds **no submission file** on its own. If G1–G5 pass, a separate builder
  (`scripts/build_h36_1_submissions.py`, not written yet) will produce the raster, and it must pass
  `scripts/verify_downloads.py` before the site changes.
* No weekly submission slot is used by this session. The standing rule — *never spend a weekly slot
  on an idea that has not beaten the current holdout best* — is satisfied by construction here: this
  arm only *measures*.
* Never contacts `drivendata.org`. Reads only local, hash-pinned owner mirrors.
