# H37-1 result — the frozen gate PASSED (seeds 250–259), and what it does and does not prove

Preregistration: `knowledge/29_preregistration_H37-1.md` (committed as `424401b`, **before** any seed in
`250–259` was touched). Runner: `scripts/run_h37_1_holdout.py` (unmodified after the freeze).
Evidence: `evidence/h37_1_holdout.json` (40 cells, 442.6 s). Artifact:
`evidence/h37_1_artifact.json`, `docs/downloads/gems28-h37-1-coverprob-h19-5-r1-20261003-0bbddf41eb6d-nan.tif`.

## 1. Result

The arm replaces the **content-blind** packing rule (`dot_thin`: ascending raster index, first-come-
first-served, evidence never read) with a **lazy-greedy maximum expected coverage** of the detector's
probability field under the official kernel, at a matched dot count, followed by the unchanged H27-4
blind 1-px catalogue-flank prune.

| Variant (40 cells, fresh seeds 250–259) | mean OOF DTI | ΔDTI vs `d=2.8` ref | ΔDTI vs incumbent | seeds | folds | mean dots/cell |
|---|---:|---:|---:|---:|---:|---:|
| `base_oof_d280` (reference) | 0.098186 | — | — | — | — | 12,229 |
| `rung30_blind_r1` (H36-1 incumbent) | 0.100860 | +0.002675 | — | — | 4/4 | 11,003 |
| **`cover_prob_r1` (PRIMARY)** | **0.105475** | **+0.007289** | **+0.004614** | **10/10** | **4/4** | 11,339 |
| `cover_prob_1p5n_r1` (dose, report-only) | 0.108626 | +0.010440 | +0.007765 | 10/10 | 3/4 | 16,989 |
| `cover_prob_pool3x_r1` (pool probe) | 0.105522 | +0.007336 | +0.004661 | 10/10 | 4/4 | 11,339 |
| `control_random_matched_n` (content-blind) | 0.053502 | −0.044684 | −0.047359 | 0/10 | 0/4 | 11,322 |
| `cover_prob_anywhere_r1` (off-ridge ceiling) | 0.107171 | +0.008985 | +0.006310 | 10/10 | 3/4 | 11,452 |

Frozen criteria, all passed:

| Criterion | Requirement | Observed |
|---|---|---|
| G1 direction | > 0 | +0.004614 |
| G2 promotion margin | ≥ +0.0005 | **+0.004614** |
| G3 consistency | ≥ 8/10 seeds and 4/4 folds | 10/10, 4/4 |
| G4 content control | ≥ +0.0005 over the matched-N random subset | **+0.051973** |
| G5 integrity | emission ⊆ active, no catalogue overlap, N > 0, budget matcher exact | 0 violations (40/40 cells) |

## 2. Three things this measurement establishes

1. **The emission step was leaving real, measurable value on the table.** The primary changes nothing
   but *which* of the candidate pixels survive at the same count (+3.05 % dots, because the coverage
   layout also puts 336 fewer dots in the catalogue-flank ring) and moves the proxy by +4.58 %
   relative. The content-blind control at the same count degenerates to −0.0447, so placement — not
   budget, not the surface, not the detector — carries this effect.
2. **The instrument is reproducible across decades.** The H36-1 incumbent, re-run unmodified on a
   fresh decade, returned **+0.002675** against its own **+0.002599** on seeds 240–249. A 7.6e-5
   difference on a different seed decade is the strongest reproducibility check this programme has
   published, and it means the +0.004614 margin is measured on an instrument that is not drifting.
3. **The ingredient is specifically "cover the detector's probability field".** Ranking by probability
   with the same spacing rule loses (−0.0027); covering the *binary* ridge set loses badly (−0.0356);
   covering a Gaussian-smoothed binary set also loses (−0.0210); raster-order packing of the full pool
   collapses to −0.0473. Only the continuous detector field, covered greedily at the official 3-px
   kernel scale, produces the gain. That is a falsifiable statement about *why*, and every rival
   explanation has been run.

## 3. Why the pool probe matters more than the primary for the artifact

The gate's primary was allowed to choose from every ridge pixel (208,300/cell, ~16 % of the footprint).
The shipped surface — the H19-5 blend — is only **2.34 %** of the footprint. The pool probe
`cover_prob_pool3x_r1`, restricted to the top-`3k` pool (2.45 % density), measured **+0.004661** over
the incumbent, 10/10 seeds, 4/4 folds: statistically indistinguishable from the primary. So the
transfer to the shipped surface rests on a *measured* pool density, not on an extrapolation from a
richer pool. That is why the artifact uses the H19-5 pool at 41,333 px pre-prune — the exact
rung-3.0 budget — and not the union pool.

The union-pool emission (H19-5 + the detector's own ridges) is written as a **probe only**
(`gems28-h37-1-probe-union-pool-r1-…`, 38,545 px). It is expected to look better on the internal proxy
because the proxy's truth *is* catalogue geometry, and it is exactly the kind of emission a live score
has already punished once (26GEMSDOE `dilcond-oof-v1`, a pure detector-product emission, scored
0.1223). Shipping it as the primary would be trading a validated geological surface for a proxy
artefact.

## 4. Artifact and projection (a model, not a score)

`docs/downloads/gems28-h37-1-coverprob-h19-5-r1-20261003-0bbddf41eb6d-nan.tif` — 37,447 px (37,660
incumbent), SHA-256 `4557311baedb4e66…`, single-band float32, EPSG:32611, exact template grid, zero
catalogue overlap, values in {0,1}. `scripts/verify_downloads.py` → **PASS, 208 checks, 0 failures**.

| Transfer assumption | Modelled live range |
|---|---|
| relative transfer (same relative OOF gain on the anchor) | 0.2841–0.2852 |
| credit transfer (Eq. 1 at \|G\| = 12,225.896, γ = 0.12653; +6.89 % credit, +3.05 % mass) | 0.2757–0.2895 |
| half-transfer (conservative) | 0.2779–0.2789 |

**House verdict: MODELLED 0.278–0.286 against the incumbent's modelled 0.2717–0.2727.** Both anchors
are owner-reported, and the closure's own linearisation error is registered
(`prune-gain-linearisation-overstates-large-prunes`).

## 5. Stated plainly: what a pass here does NOT establish

1. **The proxy favours this arm by construction.** The standing holdout hides catalogue components
   interleaved with the known catalogue, so 100 % of its truth lies at distance 0 from the published
   catalogue (`evidence/arm_habitat_decomposition.json`; `registry/irregularities.json:
   interleaved-holdout-has-no-far-field-truth`). An objective that maximises coverage of a detector
   *trained on that catalogue* is the strongest possible candidate for a proxy artefact. The gate is
   necessary and it was passed on fresh seeds with a devastating content-blind control — but it is not
   far-field evidence, and this session did **not** run the LOSFO far-field instrument on it.
2. **The 4/4 fold criterion is a weak guard.** Per-fold LOSFO spread was measured at ±12 %
   (`knowledge/20` §3.2). One fold (SW) supplies most of the gain in every variant.
3. **The dose variant is not promotable.** 1.5× budget gains more on the proxy (+0.0104) but loses
   4/4 folds (3/4), so it is recorded and not shipped: the live anchors themselves show the operating
   point moving *down* in N (121k → 60k → 44k → 41k), i.e. the live curve disagrees with the proxy
   about the direction of the optimal budget.
4. **No slot was spent, no upload occurred.** A gate is not a submission, and nothing here contacts
   DrivenData.

## 6. What follows (ranked, with costs)

`knowledge/31_hypotheses_session13.md` carries the four *geological* candidates this session generated
and ranked. The immediate engineering follow-up is a **LOSFO far-field run of the same rule** — it is
the only instrument in the repository that can falsify the proxy-artefact explanation, and it is the
gating instrument the Session-10 review already required for any arm that moves dots.
