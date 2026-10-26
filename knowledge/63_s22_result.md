# Session 22 result — displaced potential-field piercing markers (`S22-DPMR`)

**Date:** 2026-10-26 UTC  
**Frozen preregistration:** [`knowledge/62_s22_preregistration.md`](62_s22_preregistration.md), commit `9b703e5`  
**Implemented runner provenance:** commits `3450ff2`, `c9f2f07`, and import-only startup fix `36742be`  
**Verdict:** `negative` — **OK to download for research: YES; OK to submit: NO; slots spent: 0**

## 1. Executive decision

Session 22 generated a genuinely new, single-band GeoTIFF from displaced magnetic/gravity marker registration. It is not a copy, seed, prune, or perturbation of a prior submission. The exact all-finite file is:

- **Research download:** `docs/downloads/gems28-s22-dpmr-20261026-ecf809d55d2a-allfinite.tif`
- **SHA-256:** `66bbd9f91ecc407e43bbd5018be2b03cfe4aa10fd73613a52d1fddf43bdc8b10`
- **Grid:** EPSG:32611; 3,730 × 3,292; exact sample transform; one `float32` band
- **Values:** exactly `{0,1}`; all 12,279,160 cells finite; 37,654 positive pixels; zero catalogue overlap
- **Portal name:** `GEMSDOE28-S22-DPMR-ecf809d55d2a`
- **Note (97/140):** `S22 DPMR displaced RTP+gravity markers 37654d | HOLDOUT 0.0676 vs 0.1444 | NEGATIVE DO NOT SUBMIT`

The file passed leakage, bounded-registry uniqueness, exact-grid, range, finiteness, footprint, hash, ZIP and archive-registration checks. It nevertheless recovered much less hidden fault mass than either same-protocol comparator:

- candidate **HOLDOUT-DTI 0.067574**, 95% CI **[0.060575, 0.075372]**;
- visible-only B0 **HOLDOUT-DTI 0.144433**, 95% CI **[0.131736, 0.157532]**;
- paired candidate − B0 **−0.076860**, 95% CI **[−0.091128, −0.062776]**, **0/4 folds improved**;
- visible-only champion analogue B1 **HOLDOUT-DTI 0.146082**, 95% CI **[0.133233, 0.159449]**.

Evaluator: shared `gems-segment-pooled-v1`; four spatial quadrants; whole connected fault systems hidden with 1,500 m buffers; visible-only catalogue construction; pixel-exact visible-fault mask; pooled α=0.2, β=0.8, 300 m triangular kernel; **60,988 withheld positive pixels / 3,199 withheld components**; 583 spatial bootstrap blocks and 1,999 resamples. The pinned `evaluate_holdout.py` entry point itself is MTR1-specific, so S22 imported its hash-verified `gems.holdout.SegmentHoldout` authority rather than forking the metric or misusing the MTR1 runner. These are local hide-and-recover measurements, **not organizer scores**.

**Best action:** download S22 only to reproduce the negative result. **Upload nothing from this repository today.**

## 2. Requested executive comparison

No row below has a filename/hash-bound organizer receipt in this repository. Historical values are therefore **USER-REPORTED / UNVERIFIED**, not `ORGANIZER-CONFIRMED`.

| Site | Best listed artifact | Evidence class / value | Construction reading | Submit from GEMSDOE28 now? |
|---|---|---:|---|---|
| GEMSDOE24 | `gems24-h25-1-dotted-h19-5-d1-5-…-989f59505db1-allfinite.tif` | USER-REPORTED / UNVERIFIED `0.2477` | H19-5, 1.5 px spaced emission | **No** — prior artifact, no receipt |
| GEMSDOE25 | `gems25-dotted-h19-5-d2-8-…-e56ea318af89-zeros.tif` | USER-REPORTED / UNVERIFIED `0.2600` | same H19-5 surface, 2.8 px emission | **No** — prior artifact |
| GEMSDOE27 | `gems27-topo-gap-closure-t-v2-on-d1-5-…-5512495c6bd1-allfinite.tif` | USER-REPORTED / UNVERIFIED `0.2449` | d1.5 plus topology additions; reported loss | **No** — prior artifact |
| GEMSDOE28 | `gems28-h36-1-rung30-blind-r1-…-b531dae0a36f-allfinite.tif` | USER-REPORTED / UNVERIFIED `0.2710` | rung-3.0 re-pack plus 1 px ring prune | **No** — historical and not selector-approved |
| GEMSDOE30 | `gemsdoe30-d28-poisson300m-offcat-44090-…-91eae1ca.tif` | USER-REPORTED / UNVERIFIED `0.2600` | same 44,090-dot d2.8 family | **No** — prior artifact |
| GEMSDOE31 | `gemsdoe31-h27-4-solo-d28-…-8acb75e1-allfinite.tif` | USER-REPORTED / UNVERIFIED `0.2708` | d2.8 minus ≤1 px catalogue ring | **No** — prior artifact |
| **GEMSDOE32** | **`gemsdoe32-h33-h33-2-b2-…-e5eb6e7e-zeros.tif`** | **USER-REPORTED / UNVERIFIED `0.2778`** | **37,654-dot d2.8 family minus ≤2 px ring** | **No copying; learning/selector reference only** |
| GEMSDOE33 | `GEMSDOE33-h33d-analog-tip-stepover-r30-…-cb490425926e.tif` | USER-REPORTED / UNVERIFIED `0.2632` | tip/stepover analogue placement | **No** — prior artifact |
| GEMSDOE36 | `gemsdoe36-anderson-geothermal-pinn-38854-…-9b9ea4e6-zeros.tif` | USER-REPORTED / UNVERIFIED `0.2750` | champion family plus 1,200 geothermal dots | **No** — prior artifact |
| **GEMSDOE28 S22** | **`gems28-s22-dpmr-20261026-ecf809d55d2a-allfinite.tif`** | **HOLDOUT-DTI 0.067574 [0.060575, 0.075372]; MODEL PROJECTION 0.1285 [0.1003, 0.1578], NOT A SCORE** | independent RTP/gravity displacement surface | **NO — negative gate** |

The S22 projection is the preregistered `0.2778 × candidate/champion-analogue HOLDOUT-DTI` ratio on identical folds. Its anchor is user-reported and unverified; the output is a model projection, not a score or guarantee.

## 3. Why GEMSDOE32 `h33-h33-2-b2…` reportedly reached 0.2778

Prior byte-level reconstruction reproduced the lineage exactly:

1. H19-5 dense ridge support: 121,131 pixels;
2. deterministic `dot_thin(2.8 px)`: 44,090 dots;
3. remove dots within one pixel of the catalogue: 40,199 dots;
4. remove the remaining two-pixel catalogue ring: 37,654 dots.

The last operation removes **2,545 dots and adds none**. Under the 300 m triangular tolerance kernel, ~2.8-pixel spacing retains broad line coverage while sharply reducing false-positive mass. Catalogue-adjacent detector blur has little marginal hidden-target credit because visible known faults are masked; pruning it can therefore improve the Tversky denominator. At a reported DTI of 0.2778, the inferred break-even marginal credit is roughly 0.0588 per dot, while the deleted ring was estimated far below that threshold. This is a plausible **emission-efficiency mechanism**, not proof of hidden-truth causation.

Important boundary: the champion’s own archived audit calls it unscored and carries a different model projection. No organizer receipt binds `0.2778` to its SHA-256 in this repository. The correct label remains **USER-REPORTED / UNVERIFIED**. Copying or cosmetically repruning it would also violate the current uniqueness requirement.

## 4. Hypotheses ranked before implementation

The full frozen slate, layers, mechanisms, off-catalogue rationale, distinctions, mimics, planning benefit, cost and official-source gates is in `knowledge/62_s22_preregistration.md`. In order:

1. **Selected:** displaced RTP + isostatic-gravity piercing-marker registration — medium CPU, cached bytes, detects buried cross-cutting offset; mimics: intrusive branching, seams, repeated texture.
2. Patch encoder–decoder over all 32 channels — highest upside, but honest buffered four-fold training did not fit the two-hour/two-CPU budget.
3. Signed piedmont break-in-slope × LiDAR scarp polarity — medium cost; mimics: shorelines, terrace/fan risers and roads.
4. Cross-scale shallow magnetic termination — medium cost; mimics: lava-flow contacts, cultural sources and flight-line levelling.
5. Multi-depth MT conductance column — high cost and unavailable bytes in this environment; official USGS source DOI `10.5066/P9TWT2LU` was identified, but the required slices were not falsely claimed present.

Planning ranges in the preregistration were judgements, not scores. H1 was chosen for highest expected information gain per implementable CPU cost.

## 5. Experiment ledger

### Experiment 1 — surface, canaries and pre-placement uniqueness: PASS

The deterministic transform used two band-pass scales, four trial strikes, six ±2–6 px shifts, 9×9 NCC, 3 px opposite-side offsets, and frozen magnetic/gravity fusion. Every feature-alone canary stayed far below the presumed-leakage threshold:

| Feature | Pooled AUC | Worst fold polarity | AUC gate |
|---|---:|---:|---|
| Magnetic displacement | 0.514249 | 0.539256 | PASS |
| Gravity displacement | 0.526023 | 0.559368 | PASS |
| Fused candidate | 0.523830 | 0.535832 | PASS |

Across **190 deduplicated valid-grid rasters** from the nine Git-pinned repositories plus pre-run local TIFFs, the pre-placement maximum `|Spearman|` was **0.331025** and maximum prospective-dot overlap within 3 px was **49.52%**. Both passed the 0.90 / 70% stops.

### Experiment 2 — buffered whole-system holdout: FAIL

| Fold | Withheld positives | S22 HOLDOUT-DTI | B0 visible-only HOLDOUT-DTI | Delta |
|---|---:|---:|---:|---:|
| NW | 10,165 | 0.067056 | 0.149113 | −0.082057 |
| NE_LidarGapHeavy | 12,511 | 0.062545 | 0.172542 | −0.109997 |
| SW | 20,534 | 0.071773 | 0.098698 | −0.026925 |
| SE | 17,778 | 0.066823 | 0.172605 | −0.105783 |
| **Pooled** | **60,988** | **0.067574** | **0.144433** | **−0.076860 [−0.091128, −0.062776]** |

Interpretation: coherent non-zero translation exists in the fields, but the frozen maximum-over-strike/shift statistic is dominated by lithologic/intrusive texture and chance registration rather than mapped-fault-like corridors. Its nearly uniform low fold performance argues against a single geographic failure. The lane is closed; no retuning on this holdout is allowed.

One startup attempt failed before any fit or score because the script path omitted the repository root from `sys.path`. It is explicitly `VOID-INFRASTRUCTURE` in `evidence/s22_dpmr_exp2_void_import.json`; only the import path changed before the clean execution.

### Experiment 3 — frozen emission and exact validation: PASS format/novelty, NEGATIVE overall

Final uniqueness passed: maximum `|Spearman|` **0.334691** and maximum 3 px overlap **50.62%**. The pinned shared writer produced both all-finite and template-NaN variants plus a one-TIFF ZIP. Independent re-read checks passed. After registering all previously omitted historical pairs, the archive-wide audit passed **723/723 checks across 48 TIFFs**, including 30 S22 checks.

A format-valid, unique raster does not override the failed scientific gate.

## 6. Exact artifact disposition

| File | Evidence / estimate class | Unique? | Exact format? | OK to submit? |
|---|---|---|---|---|
| `gems28-s22-dpmr-20261026-ecf809d55d2a-allfinite.tif` | HOLDOUT-DTI 0.067574 [0.060575, 0.075372]; MODEL PROJECTION 0.1285 [0.1003, 0.1578], NOT A SCORE | YES within frozen bounded registry | PASS; whole array finite `[0,1]` | **NO — research only** |
| `gems28-s22-dpmr-20261026-ecf809d55d2a-nan.tif` | same candidate, sample-footprint convention | YES within frozen bounded registry | PASS inside footprint; NaN outside by design | **NO — research only** |
| `gems28-s22-dpmr-20261026-ecf809d55d2a-nan.zip` | byte-identical one-member bundle | same | PASS | **NO — research only** |
| GEMSDOE32 `h33-h33-2-b2…e5eb6e7e` | USER-REPORTED / UNVERIFIED 0.2778 | previous submission family | owner-repository bytes audited elsewhere | **NO — do not copy** |

## 7. Exact future submission instructions

No upload is authorized now. When a future run passes all gates and a separate selector approves a weekly slot:

1. Download the approved **all-finite** `.tif`, not a research-only negative file.
2. Verify its published SHA-256 and run card; require one float32 band, exact sample CRS/shape/transform, and finite values in `[0,1]` everywhere.
3. On the authenticated DrivenData competition page, check the account’s current allowance and choose **New submission → File to submit**.
4. Select the exact `.tif` (or a ZIP containing exactly that one TIFF), paste the registered unique name and ≤140-character note, then submit.
5. Preserve the submission-page receipt, timestamp, file SHA-256 and organizer-returned value. Only then label it `ORGANIZER-CONFIRMED`.

Do **not** perform step 3 for S22. Its paired confidence interval is wholly negative.

## 8. Official/free source availability and boundaries

Manual-review links retained from the frozen preregistration:

- DrivenData problem and metric: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/
- Official open reference implementation: https://github.com/drivendataorg/gems-prize-reference-solution
- USGS GeoDAWN landing page: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and
- DOE GDR INGENIOUS release 1391: https://gdr.openei.org/submissions/1391
- USGS multi-depth MT source: https://doi.org/10.5066/P9TWT2LU

Competition and derived inputs used here are hash-pinned owner mirrors, not organizer-authenticated downloads. The registry is complete only within its declared nine-repository/local scope and cannot see unpublished concurrent work. No DrivenData login, upload, quota query, score query or receipt was used.

## 9. Review and next work

- **Pass 1 — implementation/science:** deterministic transform, focused synthetic tests, leakage canaries, bounded registry, shared holdout and writer.
- **Pass 2 — bug/integrity:** fixed the import-only startup defect; reconciled canonical cache NaN handling with exact schema-3 missingness counts; registered and audited every archived TIFF.
- **Pass 3 — request/claim review:** rechecked evidence labels, projection language, file hashes, `[0,1]`, finiteness, grid, uniqueness, note length, no-slot state, page links and download disposition. Final replay: **555 tests + 9 subtests passed** (7 dependency warnings), repository-wide Ruff passed, the exact-file download audit passed **723/723**, restored-input integrity passed, and two consecutive site builds produced identical hashes for all 20 generated pages/aliases.

The transform should not be tuned on the spent S22 holdout. Highest-upside next work is a fresh preregistered patch encoder–decoder on suitable GPU infrastructure, or the signed piedmont-normal morphology operator on fresh evidence. Either must use a synchronized pre-run registry and a new holdout decision boundary. **Maximize P(Win): reject this lane. Own the Outcome: preserve the negative file and complete evidence rather than spending a slot.**
