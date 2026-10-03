# LOSFO far-field attribution: the candidate set, not the budget, decides whether H37-1 transfers

**Verdict.** The two far-field measurements of "greedy maximum expected coverage" disagree because they
packed **different candidate sets**. Holding the detector, the folds, the far-field truth and the
emitted count fixed, the rule earns

* **≈ 0** when candidates are restricted to the top-`k` ridge pool (the arm `knowledge/33` tested), and
* **+0.005 to +0.006** when candidates are **all ridge pixels** (the construction the H37-1 gate's
  primary actually used), replicated on 5/5 seeds with the previous probe reproducing to `0.0`.

Evidence: `evidence/losfo_cover_variants.json` (seeds `215–219`, 20 cells, 420.4 s, integrity
violations `[]`), produced by `scripts/run_losfo_cover_variants.py` after the protocol below was
frozen in that file's docstring before the run. This is a measurement, not a promotion gate.

## 1. The two measurements that disagreed

| source | cells | arm as written | candidates | target count | result |
|---|---|---|---|---|---|
| `knowledge/33`, `evidence/losfo_packing_farfield.json` | seeds `210–214`, 20 cells | `packing.coverage_greedy(pool, prob, n_base)` | top-`k` ridge pool | `n_base` = `d=2.8` emission (12,001) | **−0.000037** ± 0.000832, 9/20 cells, 3/5 seeds → FAIL |
| `evidence/losfo_cover_probe.json` (this session) | seeds `215–219`, 20 cells | `packing.coverage_greedy(ridge & active, prob, n_pre)` | all ridge pixels | `n_pre` = `dot_thin(pool, 3.0)` (11,339) | **+0.005275** vs its exact-count twin `thin_d30`, 16/20 cells, 5/5 seeds |

Both arms are "coverage packing"; they differ in the candidate set **and** the count. The follow-up run
below crosses both factors on one detector and one truth set.

## 2. Frozen attribution design (all four combinations, one run)

Same detector per seed (`fit_predict_oof_probabilities` on LOSFO-masked labels), same folds, same
`build_losfo_split` truth, same `active = fold_mask & ~known`, same LOSFO decade `215–219`. Arms:

| arm | candidates | target | mean DTI | credit/dot | ΔDTI vs `base_d28` | cells / seeds / folds up |
|---|---|---|---|---:|---:|---|
| `base_d28` | top-`k` pool | 12,016 (`d=2.8`) | 0.10648 | 0.0487 | — | — |
| `pool_cover_nbase` | top-`k` pool | 12,016 | 0.10730 | 0.0491 | **+0.000819** | 12/20, 3/5, 2/4 |
| `all_cover_nbase` | all ridges | 12,016 | 0.11274 | 0.0520 | **+0.006269** | 16/20, 5/5, 3/4 |
| `pool_cover_npre` | top-`k` pool | 11,339 | 0.10671 | 0.0504 | **+0.000235** | 9/20, 2/5, 2/4 |
| `all_cover_npre` | all ridges | 11,339 | 0.11163 | 0.0531 | **+0.005158** | 16/20, 5/5, 3/4 |

Direct head-to-head contrasts that isolate one factor at a time:

| contrast | isolates | mean ΔDTI | cells / seeds / folds up |
|---|---|---:|---|
| `all_cover_nbase − pool_cover_nbase` | candidate set at the `d=2.8` count | **+0.005450** | 14/20, **5/5**, 3/4 |
| `all_cover_npre − pool_cover_npre` | candidate set at the rung-3.0 count | **+0.004923** | 15/20, **5/5**, 3/4 |
| `pool_cover_nbase − base_d28` | the `knowledge/33` arm | +0.000819 | 12/20, 3/5, 2/4 |

Per-fold, the all-ridge gain is `NW −0.0017`, `NE +0.0055`, `SW +0.0090`, `SE +0.0079` (3/4 folds).

**Integrity and reproduction** (`evidence/losfo_cover_variants_analysis.json`,
`scripts/analyze_cover_variants.py`, pure re-arithmetic on the two stored files — no re-fit).
`integrity_violations: []` (no arm ever emitted a different count from the one it was asked for), and
every stored paired contrast recomputes from the per-cell records with max error `0.0`. The two
independent runs agree **exactly** on their shared arms:

| arm here | arm in the probe | max abs per-cell DTI difference |
|---|---|---|
| `all_cover_npre` | `cover_n` | `0.0` |
| `base_d28` | `thin_d28` | `0.0` |
| `pool_cover_nbase` | `thin_d28` (different arm, diagnostic only) | `6.45e-3` |

The variants runner's stored `reproduction_check` block labels its second line
`max_abs_dti_diff_base_vs_thin_d30` (`2.26e-3`); that line compared two deliberately different arms
(`d=2.8` vs `d=3.0`) and is a spread diagnostic, not a mismatch. The runner now reports arm-matched
pairs explicitly; the corrected arithmetic is in the analysis artifact above.

## 3. What this establishes, and what it does not

**Establishes.**

1. The `knowledge/33` result is real **for the arm it froze**: coverage packing restricted to the top-`k`
   pool at `n_base` is worth ≈ 0 far field. It is not an implementation error.
2. The H37-1 *gate* construction (`coverage_greedy(ridges, prob, n_pre)`, 2.45 %-of-cell pre-thin pool,
   all ridge candidates) **does** improve far-field DTI: `+0.005158` against the shipped raster rule at
   the same count, or `+0.005275` against its exact-count twin, 5/5 seeds, 16/20 cells, 3/4 folds.
3. The earlier inference in `knowledge/33` §3 — "the packing rule's advantage is catalogue
   interpolation" — is **not supported**: the same rule, on truth ≥ 8 px from anything the detector
   saw, moves DTI by ~`+0.005`. What is catalogue-local is the *pool-restricted* variant.
4. Dose, far field, first measurement: raster-order thinning at `d=3.0` versus `d=2.8` on the same pool
   is **−0.000116** (9/20 cells, 1/5 seeds, 2/4 folds) while emitting 677 fewer dots (11,338.9 vs
   12,016) — i.e. the H36-1 re-pack's *dose* axis is far-field neutral, not positive and not harmful.
   This discharges the remedy queued in irregularity `h37-1-farfield-effect-is-zero` ("one more LOSFO run
   on H36-1's dose change") and is what lets the restored one-click primary stand without a far-field
   asterisk: its support remains the live-anchored ladder (`knowledge/27`), and swapping it for the
   H37-1 file costs nothing off-catalogue, it simply buys nothing there either.

**Does not establish.**

1. It does **not** validate the shipped artifact. `scripts/build_h37_1_submissions.py` packs
   `pool_h19 = the H19-5 surface` (121,131 px) with a **full-fit** detector weight, which is a third
   construction: not the gate's all-ridge pool and not `knowledge/33`'s top-`k` pool.
2. The shipped construction **cannot** be tested under LOSFO as it stands: the H19-5 surface is derived
   from the catalogue and `src/gems27/losfo.py` requires catalogue-derived layers to be excluded or
   explicitly audited. Building a LOSFO-consistent re-derivation of that surface is a named next step,
   not something this run did.
3. Twenty cells on five seeds cannot resolve effects below ~`±0.0018` (1 s.e.); the `NW` fold is
   negative in every all-ridge contrast. The claim is a positive mean with 5/5 seeds and 3/4 folds, not
   a certified constant.
4. LOSFO truth is *mapped* fault systems, so every number here is an upper bound on performance against
   genuinely unmapped faults.
5. `all_cover_*` credit/dot is `0.0520–0.0531`, still **below** the live break-even `τ = 0.054852` at
   the `0.26` anchor: the rule improves on the raster cascade far field without by itself clearing the
   live threshold at that anchor's calibration.

## 4. Consequences for the record and the slot

* `docs/downloads/manifest.json` (merged from `main`) demoted H37-1 *because* the far-field test failed.
  That premise is now **contradicted**: the failed arm was not the gated construction. Registered as
  `farfield-arm-did-not-match-gate-construction` (severity medium-high) in
  `registry/irregularities.json`, with the numbers above.
* **Slot order is left unchanged in this session** (H36-1 one-click, H37-1 secondary). Neither promotion
  nor demotion of the *shipped* file is far-field measured, and this session will not re-rank two
  artefacts on a comparison that does not match either of them. The honest statement on the site is
  that the H37-1 **rule** has far-field support in the only construction that can be measured, while the
  **shipped file** remains far-field unknown.
* Named next step (cheap, one session): rebuild the candidate surface itself under LOSFO
  (re-derive the H19-5-style blend with the held-out systems erased, then pack it) so that the shipped
  construction has a far-field number of its own.

## 5. Session consequence

The two facts this run establishes are independent and both matter:

* the **shipped cascade** is not beaten off-catalogue by adding coverage packing to its own pool
  (`+0.000819`), so the site's one-click file stays as merged;
* the **gate's all-ridge coverage rule** does transfer off-catalogue (`+0.005158` at matched count,
  5/5 seeds) but still lands below the live break-even credit density `τ = 0.054852`.

Together that says the far-field ceiling is set by the detector's *credit density per dot*, not by the
packer — which is exactly the reason the session's forward work now moves to adding **new physical
measurements** to the detector (see `knowledge/37_hypotheses_session14.md`) rather than to further
re-arranging the dots it already emits.
