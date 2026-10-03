# H38-1 result — the GeoDAWN radiometric channels move the emission (gate passed, transfer pending)

**Verdict on the frozen gate.** On the gated fresh decade `280-289`,
`evidence/h38_1_holdout.json`, the radiometric-augmented detector's coverage emission beats the frozen
detector's at matched count by **+0.002869** mean ΔDTI, **9/10 seeds** and **4/4 folds** positive, with
the content-blind control `0.054841` below it — every criterion of `knowledge/37` §4 passes, and both
harness defects found on the way are disclosed and fixed (errata 1 and 2, `knowledge/37` §§7-8).

Independently re-read by `scripts/analyze_h38_1.py` →
`evidence/h38_1_holdout_analysis.json`: every DTI recomputes from the stored `tp`/`fp`/`n_truth`
with max error `0.0`, every count identity holds, and all six stored gate statistics match.

> **This is a candidate, not a submission — and the far-field test has now run.** `knowledge/37` §5
> makes a frozen LOSFO transfer test mandatory first; that test is `knowledge/39` /
> `scripts/run_losfo_rad_farfield.py`, seeds `220-224`. **Result: no transfer licence** — the
> count-matched far-field effect is `+0.000959` with a 95 % interval of `±0.004469` (2/5 seeds, 2/4
> folds, 4/20 cells below `−0.005`), i.e. unresolved and at best neutral, while the run's own
> reproduction guard-rail F4 fired for a reason that turned out to be a mis-calibrated tolerance in the
> preregistration (see `knowledge/41`). **No artifact was built, nothing was re-slotted, and no weekly
> slot was spent.**

## 1. What was added

Six channels, all from hash-pinned local rasters (`registry/data_manifest.json`), all previously
unavailable to the detector:

| channel | source | note |
|---|---|---|
| `rad_K`, `rad_Th`, `rad_U` | `geodawn_rad_u8.tif` bands 1-3 | equivalent uranium/thorium and potassium concentrations, GeoDAWN (USGS + DOE/GTO) airborne survey |
| `ext_ThK`, `ext_UK`, `ext_UTh` | `geodawn_extensions_u8.tif` bands 1-3 | the standard ratio grids used in alteration mapping |

Excluded with measured reasons (frozen in `knowledge/37` §2, re-verified this session): `TMI_up150`
(rank `+0.984`–`+0.998` with in-stack `tmi`), `rad_TC` (rank `+1.000` with the mislabelled training
band 6 `tc`, itself excluded). A full band-identity audit against all eight GeoDAWN channels found
**no other** near-duplicate: every other training band sits at the trend background (`0.90-0.93`)
against every GeoDAWN channel, so the mirror is not smuggling the whole stack into the matrix.

## 2. Gated numbers (seeds 280-289, 40 cells, 297.8 s)

| arm | detector | emission | mean DTI | mean dots |
|---|---|---|---:|---:|
| `base_d280` | D0 | `dot_thin(top-k pool, 2.8)` (shipped reference rule) | 0.09552 | 12,231.2 |
| `cover_r1` | D0 | coverage packing at `n_pre0` + blind `r1` prune (incumbent) | 0.10513 | 11,335.0 |
| `rad_base_d280` | D1 | `dot_thin(top-k pool, 2.8)` | 0.10180 | 12,203.9 |
| **`rad_cover_r1`** | D1 | coverage packing at `n_pre0` + blind `r1` prune | **0.10800** | 11,328.7 |
| `control_random_matched_n` | D0 | uniform random draw at `n_pre0` + blind `r1` | 0.05316 | 11,320.3 |

| criterion | value | verdict |
|---|---|---|
| G1 direction ΔDTI(`rad_cover_r1` − `cover_r1`) | +0.002869 | PASS |
| G2 promotion (≥ +0.0005, ≥ 8/10 seeds, 4/4 folds vs incumbent) | 9/10 seeds, 4/4 folds | PASS |
| G3 do no harm ΔDTI(`rad_base_d280` − `base_d280`) | **+0.006282** (10/10 seeds, 4/4 folds) | PASS |
| G4 content control margin | +0.054841 | PASS |
| G5 integrity (counts, containment, determinism) | 0 violations | PASS |

Count matching held: the primary and the incumbent both emit `n_pre0` from their packers and lose the
same kind of 1-px flank mass to the prune, ending `11,328.7` vs `11,335.0` (max per-cell gap `0.222 %`).

## 3. Two harness defects, disclosed before any re-run

| # | first run | defect | cost | fix |
|---|---|---|---|---|
| 1 | seeds `260-269` | G5(b) compared the **post-prune** mask to the **pre-prune** request | decade spent, metrics void | check the packer's own output (as `run_h37_1_holdout.py` already did); store packer/prune/post-prune counts per cell |
| 2 | seeds `270-279` | `G2_promotion` used the fold split **vs the D0 reference rule** (4/4) instead of **vs the incumbent** (3/4, `NW −0.000703`) | decade spent; result may be cited only as a pilot | store both splits; G2 uses the incumbent-relative one |

Neither defect touched a modelled quantity — the same arms on `270-279` and `280-289` differ only by
decade, and the D0 arms replicate across the three decades (`cover_r1` 0.10370 / 0.10513; `base_d280`
0.09483 / 0.09552). Registered as `h38-1-g5b-checked-post-prune-count` and
`h38-1-g2-fold-statistic-used-base-not-incumbent`. The honest cost is three gate decades for one gate;
the alternative — re-adjudicating a seen decade after changing a check — is the failure mode the
protocol exists to prevent.

## 4. What the gate does and does not say

* **It says** the six radiometric channels change the detector's emission in a way that survives a
  600 m spatially blocked holdout with 9/10 seeds and 4/4 folds, and that the effect is not an artifact
  of the packing objective (G3: the *reference* cascade rule improves by `+0.006282`, more than the
  primary's `+0.002869`) or of dot count (0.22 % gap).
* **It does not say** the channels map *alteration*. K, U and Th respond to bedrock-versus-alluvium,
  elevation and survey-line geometry as much as to hydrothermal alteration; the detector is a
  tree ensemble over 38 bands and the gate cannot attribute the gain to the K-anomaly mechanism. This
  is an information result, not a mechanism result (frozen in `knowledge/37` §6).
* **It does not say** anything about off-catalogue transfer, the live scoring population, or the weekly
  slot. That is the pending LOSFO test (`knowledge/39`).
* It does not reopen the H37-1 question: the incumbent `cover_r1` here is the D0 detector's coverage
  emission, and its `+0.009610` over `base_d280` on this decade is the same proxy-favoured construction
  `knowledge/38` dissects. The comparison that matters is D1-vs-D0 at matched count on the same rule.

## 5. Postscript — status after the far-field run (2026-10-03)

`knowledge/41_h38_1_farfield_result.md` records the transfer test in full. The status of this arm is
therefore: **interleaved gate passed (G1-G5 on seeds 280-289), far-field transfer unresolved, no file
built, no promotion, no slot.** The interleaved gain is real under its own protocol and the F1 interval
is 1.5x its size, so the correct next move is a *larger* far-field decade (>= 10 seeds) if the owner
wants the question settled — not another interleaved gate and not a re-run of the seen decade.

One finding from that run does change the ranking: the **all-ridge coverage packing construction with
the frozen D0 detector** replicated its far-field gain a second time (`+0.005881`, 5/5 seeds, 4/4 folds,
against `+0.005275` on the probe's decade). That construction, not the radiometric detector, is now the
repository's best-supported unshipped arm — and it still needs its own frozen interleaved gate before a
file may be built from it (`registry/next_hypotheses.json:session14_addendum`).
