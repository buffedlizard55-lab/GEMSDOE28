# H36-1 result — the packing-rung re-pack at rung `3.0`, seeds `240–249`

Protocol: `knowledge/26_preregistration_H36-1.md` (written and committed as `aaa659c` **before** any
seed in `240–249` was touched). Runner: `scripts/run_h36_1_holdout.py` (frozen; not edited after the
run). Evidence: `evidence/h36_1_holdout.json`. Runtime 105.0 s on 2 cores.

## 1. Result

Base control (`base_oof_d280`, the shipped rung): mean OOF `DTI` **0.094132**, 48,929 dots/seed.
Deltas are versus that control, on identical cells.

| Variant | ΔDTI | min seed | seeds | folds | Δdots/seed | removed credit per removed FP |
|---|---:|---:|---:|---:|---:|---:|
| `rung30_unpruned` | **+0.000956** | +0.000139 | 10/10 | 4/4 | −2,649 | 0.01231 |
| **`rung30_blind_r1`** (winner) | **+0.002599** | +0.001848 | 10/10 | 4/4 | −4,954 | **0.00984** |
| `rung30_flank_mid` | +0.002188 | +0.001326 | 10/10 | 4/4 | −4,085 | 0.00958 |
| `h27_4_blind_r1_d280` (incumbent) | +0.001715 | +0.001395 | 10/10 | 4/4 | −2,418 | 0.00663 |
| `control_random_drop_matched_n` | **−0.001657** | −0.002531 | **0/10** | **0/4** | −2,649 | 0.03163 |
| `control_rung30_protected_only` | +0.001352 | +0.000658 | 10/10 | 4/4 | −3,518 | 0.01198 |

Per-fold gains for the winner: NW +0.002471, NE_LidarGapHeavy **+0.004814**, SW +0.001098,
SE +0.002011.

**Frozen gate (all five criteria, as written before the run):**

| | Outcome |
|---|---|
| G1 rung effect | **PASS** — `+0.000956`, 10/10 seeds, 4/4 folds |
| G2 re-pack vs budget | **`repack`** — the rung beats the matched-`N` random drop by **+0.002613** (vs a `+0.0003` bar) |
| G3 prunes on the new rung | **PASS** for all three (efficiency 0.00958–0.00984 against `tau_live = 0.054852`) |
| G4 winner / promotion | **`rung30_blind_r1`**, margin over the incumbent **+0.000884** ≥ the `+0.0005` rule ⇒ **PROMOTE** |
| G5 anti-selective control | **not triggered** — the protected-only control scores +0.001352, below the winner |

## 2. What is actually new here

**(a) The rung effect replicates.** H34 predicted, from three owner-reported live scores of one
surface, that the optimum packing rung is `3.0` and not the shipped `2.828`. On a fresh decade of the
independent OOF instrument it is positive in **10/10 seeds and 4/4 folds**. The *direction* of H34 is
confirmed by a different instrument.

**(b) The size is much smaller than H34 predicted, and the reason is informative.** H34 predicted
`+0.00303` at the live operating point; the OOF proxy measures `+0.000956` for the same rule. The two
instruments disagree by ~3×, in the same direction H35-6 warned about: the OOF base sits at `DTI`
0.094 (break-even `tau = 0.0193`) while the live file sits at 0.2600 (`tau = 0.0549`), and a *removal*
is worth strictly more at the higher operating point. So the live projection of the rung step should
be **larger** than the OOF number, not smaller — which is exactly the hybrid convention this repository
already uses. Neither number is wrong; they answer different questions and must not be mixed.

**(c) The anti-budget control is the strongest single result in this file.** Deleting **2,649** dots at
random (the exact count the rung removes) *lowers* the OOF `DTI` by **−0.001657**, in **0/10** seeds and
**0/4** folds. The re-pack at the same count *raises* it by +0.000956. The +0.002613 gap is therefore
**layout, not budget**: the emission was not simply too dense, it was mis-packed. This also falsifies
the natural reading of the H34 model — under that model's `gamma`-invariance assumption, removal is
non-selective, so a coin-flip deletion to the same `N` should have matched the rung. It does not. The
`gamma`-invariance assumption is good to 1.9 % across the three live anchors of the *same* surface, but
it does not survive being tested against a random deletion, because `dot_thin` re-seeds rather than
trims.

**(d) The prunes are worth more on the new rung, as the threshold arithmetic said.** H32-1's
mid-segment flank prune moves from +0.001272 (seeds 180–189, rung 2.828) to +0.002188 on rung 3.0, and
the blind prune from +0.001766 to +0.002599. Removal efficiency *falls* (0.00402 → 0.00958 and
0.00598 → 0.00984) — the pixels being removed on the sparser rung are slightly better — and both stay
far below `tau_live = 0.054852`, so both remain correct.

**(e) The selective-prune reading survives its control.** The anti-selective control (delete only the
*protected* tip/Euler pixels) scores +0.001352 against the winner's +0.002599, so G5 did not fire: on
the new rung the prunes are still selective, not generic mass removal.

## 3. Live projection (a model, not a score)

House hybrid convention — the live-anchored H34 ladder for the geometric step, the measured gate
efficiency for the targeted step, both applied at the `0.2600` anchor (`|G| = 12,225.896`,
`gamma = 0.12653`):

* re-pack 2.828 → 3.0: `A` 4,803.28 → 4,728.40, `N` 44,090 → 41,333, `DTI` 0.260627 → **0.263464** (+0.002834);
* flank prune, 3,673 px at the gate's measured efficiency 0.0098447: `A` → 4,692.24, `N` → 37,660,
  `DTI` → **0.2717–0.2727**.

The range is the honest output. `operating_point.prune_gain` returns 0.27234 as a **first-order**
expansion; recomputing the metric state exactly at `(Δcredit = −e·n, Δmass = −n)` returns 0.2727 if
every removed pixel was pure false-positive mass and 0.2717 if the removed set carried the emission's
average kernel proximity. The ~0.001 spread is the same size as the effects being adjudicated, which
is why `registry/irregularities.json` now carries
`prune-gain-linearisation-overstates-large-prunes` and this file quotes a range rather than a number.

**Do not treat 0.2717–0.2727 as a prediction of a leaderboard move.** The `0.2600` anchor is
owner-reported, H34's anchors are owner-reported, and the OOF instrument measures catalogue-internal
truth while the private test set is expert-labelled faults *outside* the catalogue.

## 4. Artifact

`docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif` — content id
`b531dae0a36f`, **37,660** emitted px, SHA-256 `5556aa1438fd67376b60d5ffc99228ec09dcc11a8408298a743ccb88d6163641`,
1,590,848 bytes. Built by `scripts/build_h36_1_submissions.py`, which asserts all three
full-footprint counts before writing (`121,131` surface → `41,333` rung-3.0 → `37,660` after the
prune) and re-verifies that the shipped `0.2600` file is exactly `dot_thin(surface, 2.8)`
(symmetric difference 0). `scripts/verify_downloads.py` → **PASS, 179 checks, 0 failures**.

Slot change: H36-1 is promoted to the one-click primary; `8acb75e1f2cc` (H27-4 solo), `31e35eee884e`
(H32-1 pre) and `c3aeda1d31a3` (H32-1 post) are demoted one rank each and **retained, not deleted**.
No weekly submission slot is used by this arm: a gate is not a submission.

## 5. Limitations, stated plainly

1. **The proxy is still a proxy.** The holdout hides published catalogue pixels. The private test set
   is expert-labelled faults *absent* from that catalogue, i.e. the population the H19-5 family is
   worst at. `registry/irregularities.json:proxy-blind-to-far-field` (high) still applies in full.
2. **Ten seeds, and 4/4 folds is a weak guard.** Per-fold seed spread was measured at ±12 % on the
   LOSFO harness; the G4 margin (+0.0005) is a deliberate but blunt instrument.
3. **The projection is a model built on owner-reported anchors.** Both the rung step and the prune
   step are extrapolated from them.
4. **The re-pack is not validated off-catalogue.** If the re-packed layout happens to be *better* on
   catalogue-internal truth precisely because catalogue segments are long and smooth, the same gain
   need not appear on shorter, more fragmented expert traces. That is the single largest way this
   result could be wrong, and only a live score can settle it.
5. **The 10,667 px that rung 3.0 adds are new emissions, not re-selected old ones.** They were never
   scored on their own; they are inside the variant that passed, but no claim is made that they are
   individually better than the 13,424 px the re-pack drops.

## 6. Next

The rung sweep is now bounded on both sides (`2.828` → `3.0` improves, `3.1623` drops 6,516 px for no
measured retention gain, and H34 rates it worse). The remaining question this family cannot answer is
whether the gain transfers off-catalogue — that is exactly what `H33-3` (heat-flow residual × 2 m
probe, the top entry of `next_ranked`) is for, and its data gate is the GitHub Actions bridge.
