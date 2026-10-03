# H33-1 result — kinematic reactivation favourability gate: **REFUTED, 0 of 6 criteria**

**Run 2026-10-03 (Session 10), seeds 200–209, preregistered in
`knowledge/19_preregistration_H33-1.md` before any fitting.**
Evidence: `evidence/h33_1_holdout.json`. Runner: `scripts/run_h33_1_holdout.py`. Score:
`src/gems27/kinematics.py`. Preregistration SHA-256 `a15ccc1b4952cb88…` and clip SHA-256
`2cc92e1d526636fc…` are both recorded inside the evidence file, so the frozen design and the data
it scored against are pinned.

## 0. The data precondition was satisfied first, and it is real

The bridge merged earlier this session produced the clip, so the frozen gate in section 0 of the
preregistration was met before any seed was spent:

| Check | Value |
|---|---|
| `docs/data/sb_slip_tendency_in_footprint.json` | exists, `sha256 2cc92e1d526636fc…` |
| slip / dilation-tendency fields | **`TS`, `TD`, `TS_norm`, `TD_TS`** all present (plus `ShearStres`, `NormalStre`, `Dip`, `DipAz`, `Strike`, `Shmin_Mag`, `SHmax_Mag`, `ShminAZ`, `SHmaxAz`, `APhi`) |
| `n_features_in_bbox` | **84,484 > 0** ✓ |
| segment count / trace points | 84,484 / 473,916 |
| total fault trace in footprint | **17,369 km**, median segment 189 m |
| source CRS → target | NAD83 Albers Equal Area Conic → EPSG:32611 (reprojected by the clip) |
| `Strike` convention | verified geometric azimuth, median abs. difference **4.27°** on 4,000 segments |

The previously-unconfirmed reading of the Siler (2022) release is now **confirmed from the bytes**:
it does carry a per-segment slip tendency and dilation tendency. `TS` is narrowly distributed
(IQR 0.210–0.270, max 0.320) while `TD` is broad (IQR 0.44–0.76), so percentile-ranking `TS`
amplifies small differences — noted as a caveat, not acted on, because the preregistration froze
percentile rank.

## 1. Result

Base `base_oof_d28` mean DTI **0.094633**; inclusion threshold at that DTI **0.019292**;
48,922 base dots per seed; 10 seeds × 4 folds = 40 paired cells; 152 s.

| Variant | mean DTI | ΔDTI | seeds won | folds improved | Δdots/seed | credit per removed FP |
|---|---:|---:|---:|---:|---:|---:|
| `base_oof_d28` | 0.094633 | — | — | — | — | — |
| **`h33_1_prune_p10`** (primary) | 0.091618 | **−0.003014** | **0/10** | **0/4** | −582.4 | **0.12855** |
| `h33_1_prune_p05` (dose) | 0.093018 | −0.001615 | 0/10 | 0/4 | −290.0 | 0.14020 |
| `control_top_p10` (direction) | 0.092426 | −0.002207 | 0/10 | 0/4 | −582.4 | 0.10104 |

**All six frozen promotion criteria failed.**

| # | Criterion | Value | Threshold | |
|---|---|---:|---:|---|
| 1 | mean ΔDTI ≥ +0.0010 | −0.003014 | +0.0010 | **FAIL** |
| 2 | folds improved ≥ 3/4 | 0 | 3 | **FAIL** |
| 3 | seeds won ≥ 8/10 | 0 | 8 | **FAIL** |
| 4 | removed credit/FP < inclusion threshold | 0.12855 | 0.019292 | **FAIL** |
| 5 | direction control worse | 0.10104 | ≥ 0.12855 | **FAIL** |
| 6 | `fav` coverage ≥ 60 % | **11.95 %** | 60 % | **FAIL** |

`gate_passed: false`. Per the preregistration: **record, do not retune, do not re-run on a fresh
decade, build no candidate TIFF, spend no slot.** None of those were done.

## 2. Three things this refutation actually teaches

**(a) The design has a hard coverage ceiling of ~12 %, so it was never a viable arm.** Only 11.95 %
of base dots (minimum fold 9.61 %) had a catalogued segment within 1 km whose strike agreed within
20°. The other 88 % are neutral by construction and can never be pruned. The preregistration set
the 60 % coverage precondition precisely to catch this, and it caught it. The reason is geological
and not fixable by widening a radius: **candidate dots are emitted off-catalogue by design**, so
most of them have no similarly oriented mapped segment nearby. Any arm that transfers an attribute
*from* mapped faults *to* off-catalogue candidates inherits this ceiling. That is a statement about
a whole class of hypotheses, not about one parameterisation.

**(b) The sign of the physics is inverted.** Criterion 5 required the direction control to be
*worse* than the primary. It was better: removing the bottom decile by `fav` discarded **0.12855**
credit per removed FP, while removing the *top* decile discarded only **0.10104**. So the dots this
score called unfavourably oriented were carrying *more* DTI credit than the ones it called
favourable. Low modelled slip/dilation tendency does not mark the false positives in this emission.

**(c) Independent corroboration of the reachability frontier.** Every one of the three arms removed
pixels at **0.101–0.140 credit per FP**, against a break-even inclusion threshold of **0.0193**.
The pruned pixels were worth **5–7× the break-even density**. This is the frontier result
(`knowledge/20`, §1) confirmed by a completely different route: the d=2.8 emission is already
efficient, so *pruning at this operating point destroys credit regardless of which physical
rationale selects the pixels*. Three independent pruning arms — H31-1, H32-2, H33-1 — have now
failed the same way. **Pruning is exhausted as a family.** The only remaining route is addition.

## 3. Implementation defects found and fixed before the result was trusted

Four bugs were fixed between the first invocation and the recorded run. All were caught by
assertions or by an obviously-wrong intermediate, not by inspecting the score:

| Defect | Consequence if missed | How caught |
|---|---|---|
| **Metre/pixel confusion.** The clipped trace is in EPSG:32611 metres; the preregistration's radii are in grid pixels. The first version searched a 10 *metre* radius and densified at 0.5 *metres*. | `fav` coverage **0.0** (nothing ever borrowed) and a 34,864,713-point / ~557 MB trace. The arm would have been "run" against an empty score. | coverage printed as 0.0; trace point count absurd |
| `np.column_stack(np.flatnonzero(mask))` returns shape **(1, 2)** — one row of flat indices, not N `(row, col)` pairs | exactly **one** dot scored instead of 10,757; `fav` silently the wrong length | added `len(dot_rc) == base.sum()` assertion, which fired |
| `fav` is a per-dot vector but was reshaped as a grid; and `prune_by_quantile` mixed flat indices with 2-D indexing | `ValueError` on reshape, then `IndexError` on subscript | raised on the first cell |
| `dot_rc` kept as float for the KD-tree but used directly to index an array | `IndexError: arrays used as indices must be of integer type` | raised on the first cell |

The fixes changed **implementation correctness only**. No frozen constant — the 5 px strike search,
the 10 px segment radius, the 20° tolerance, the 3-neighbour cap, the 10 %/5 % deciles, the neutral
default — was altered at any point, and none was altered in response to an observed score.

**Seed disclosure.** Seed 200 was exercised four times during that debugging, before the recorded
run. Because the harness is deterministic, those invocations returned the same numbers as the
recorded run; no design parameter was changed in response to any of them, and the preregistration
was never edited (its SHA-256 is recorded in the evidence file and matches the frozen text). The
remaining seeds 201–209 were used exactly once. Recorded here and in
`registry/irregularities.json` rather than left implicit.

## 4. Standing effect on the strategy

* H33-1 is **closed**. Do not re-run it on a fresh decade, do not widen its radii, do not re-rank
  by a different tendency field. Seeds 200–209 are spent.
* Add to the do-not-revive list: *attribute transfer from mapped faults to off-catalogue candidates*
  as a pruning signal, for the coverage-ceiling reason in §2(a).
* The frontier conclusion is now over-determined: **the next arm must add dots on unmapped
  structure, validated on LOSFO**, not prune dots on mapped structure, validated on the interleaved
  holdout. See `knowledge/20_strategy_after_reachability_frontier.md`.
