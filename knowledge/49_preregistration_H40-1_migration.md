# Session 16 — preregistration H40-1 (edge-migration lane), frozen before any fit

**Date:** 2026-10-25 (UTC). **Branch:** `arena/2164512d-gemsdoe28`.
**Budget (prompt):** ≤3 experiments, ≤2 h. Exp 1 = canary/band build, Exp 2 = LOSFO gate,
Exp 3 = candidate build (only if Exp 2 passes). No submission slot is spent by this repo;
promotion/selection is a separate human step.

## 0. Why the 0.2778 file won (verified this session, education only)

Byte-verified 2026-10-25 in this sandbox (SHA-256 `c55bafc4…` = GEMSDOE32 audit pin;
`evidence/s15_champion_forensic.json` reproduced by fetching the file again this session):

`h33-h33-2-b2-…-e5eb6e7e-zeros` (37,654 dots, OWNER-REPORTED 0.2778, **not**
ORGANIZER-CONFIRMED — no receipt exists in any fetched repo) is *exactly*
`solo-r1 8acb75e1` (40,199 dots, OWNER-REPORTED 0.2708) **minus every dot with
d(catalogue) ≤ 2 px** (2,545 removed, 0 added, symmetric difference 0). And `solo-r1` is
exactly `dotted-h19-5-d2-8 e56ea318` (44,090 dots, OWNER-REPORTED 0.2600) minus the
d ≤ 1 px ring (3,891 removed). Owner-reported ladder gain ≈ **+2.76×10⁻⁶ DTI per deleted
flank dot, constant across both rings** — i.e. the group's best score is *emission
hygiene on an unchanged detector surface*, not new detection. A "ring-3" copy would be a
subset of the champion (>95 % of dots within 3 px) and is **prohibited** by the prompt's
uniqueness rule (rank-corr > 0.90 or > 70 % dots within 3 px of one registry raster =
duplicate → stop). Beating 0.2778 honestly therefore requires *new credit at
> τ_live ≈ 0.059 credit/dot* (repo live-inversion bar) from a differently-placed dot set.

## 1. THE LANE (single method paragraph — this session stays inside it)

> **H40-1 edge-migration lane.** From the competition TMI (band 14) and isostatic-gravity
> (band 13) fields only, compute upward continuations at 0/1/2 km (Fourier
> `exp(−|k|h)`, Blakely 1995 — the same verified transform as `depthslice.py`, reused not
> forked), extract the horizontal-gradient ridge at each level, and encode, per pixel,
> (a) the **signed lateral migration** of the ridge between the shallow and 2 km levels
> projected onto the local field-gradient normal (px, smoothed σ=2 along the shallow
> ridge), and (b) a **three-level ridge coherence** `mean_l exp(−d_l/2)`. These 4
> label-free bands are appended to the frozen 32-band stack; the detector is the repo's
> unchanged 4-quadrant HistGBDT (`oof_detector`, 600 m buffer); ranking is by probability
> only (S15 showed persistence-weighted ranking costs −0.0009, so it is NOT used);
> emission is `ridge_nms` → top-budget → `dot_thin(2.8)` with the disclosed build-time
> catalogue exclusion `d_cat > 2 px`. **Named non-fault mimic:** a dipping lithologic
> contact or mafic dike — it migrates identically and has zero Quaternary slip; the lane
> detects *dipping subsurface boundaries*, and fault identity is only ever a candidate.

Differs from H39-1/depthslice (S15, gate FAIL −0.0016): that used HG *magnitudes* and a
persistence *ratio* at a pixel; H40-1 uses ridge *geometry* — where the ridge moves, and
in which signed direction — an observable depthslice never encoded. Differs from H28-1
(static cross-field edge coherence at fixed scales) and from Euler (source fitting).

## 2. Ranked candidate slate (prompt requirement; only #1 is run — the lane)

| # | Hypothesis (layers / signature) | Why a *missing* fault | Mimic | Cost |
|---|---|---|---|---|
| 1 | **H40-1 TMI+gravity ridge migration** (above) | A dipping buried fault juxtaposes magnetic/density rock; its edge migrates with continuation height even with no surface scarp for the catalogue | Dipping contact/dike | Low–med (bands ~2 min) |
| 2 | Paired signed cross-scarp change-points in DEM+radiometric K/Th (GeoDAWN extensions u8, restored) | Degraded scarps show as repeated signed flank steps below single-pixel thresholds | Fan boundary, shoreline | Med |
| 3 | Heat-flow residual × 2 m-probe conjunction at lineaments (ScienceBase 10.5066/P9BZPVUC + GDR 1391) | Alluvium-buried upflow faults vent heat without a trace | Groundwater discharge | Med (data in hand: docs/data heat-flow; probes need GEMSDOE30 mirror fetch) |
| 4 | Drainage-divide asymmetry reversals × magnetic edge (3DEP 1 m DEM tiles) | Concealed normal fault tilts basins without a sharp scarp | Lithologic erosion, capture | High (716 tiles) |
| 5 | MT conductance-boundary depth migration × gravity (USGS 10.5066/P9TWT2LU) | Buried fluid-bearing structure, no Quaternary trace | Clay basin margin | High; obtainability of exact bytes NOT verified → not viable this session |

## 3. Frozen protocol (no changes after Exp 1 starts)

- **Holdout:** LOSFO (`src/gems27/losfo.py`): whole fault systems (8-conn dilation 3 px)
  withheld per quadrant fold, 600 m buffer erased from training labels, visible catalogue
  masked pixel-exactly in evaluation (`active = fold & ~known`). Evaluator = shared
  `run_losfo_harness.eval_set` (pooled DTI α=0.2, β=0.8, 300 m triangular kernel).
  **Seeds 300–304** (checked 2026-10-25: no prior use in evidence/knowledge/registry;
  290–294 consumed by S15). 20 paired cells.
- **Canary (Exp 1):** each migration band alone, AUC vs LOSFO seed-300 withheld systems;
  `max(AUC,1−AUC) > 0.90` = leakage → stop. Also Spearman vs in-stack bands (sample 200k).
- **Gate (Exp 2), all required:** G1 pooled ΔDTI(D1−D0) > 0 AND mean paired ≥ +0.001;
  G2 ≥14/20 cells, ≥4/5 seed means, ≥3/4 fold means positive; G3 pooled credit/dot D1 ≥ D0;
  G4 0 dots on known, pooled |N₁−N₀|/N₀ ≤ 0.10; G5 canary pass.
- **Uniqueness (Exp 3, pre- and post-placement):** Spearman(prob_D1, prob_D0) ≤ 0.90
  (400k sample) AND ≤70 % of final dots within 3 px of *every* registry raster
  (all `docs/downloads/*-nan.tif` + champion e5eb6e7e + GEMSDOE36 9b9ea4e6, education
  copies in /tmp/forensic). Any breach → log duplicate, verdict negative, banner DO NOT SUBMIT.
- **Validator:** `submission.verify_geotiff` all hard checks; the promoted download is the
  **all-finite (zeros-outside)** variant — values exactly {0,1} ⊂ [0,1], no NaN anywhere —
  because the owner already hit the portal error “Predicted values must be in range [0, 1]”
  with a NaN-outside file. Note ≤140 chars, unique name `gems28-h40-1-migration-b1-…`.
- Every number labelled **HOLDOUT-DTI** (evaluator, withheld px, 95 % CI) or
  **OWNER-REPORTED**; projections never written as scores.
