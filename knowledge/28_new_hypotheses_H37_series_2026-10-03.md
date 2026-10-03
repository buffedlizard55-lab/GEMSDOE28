# New candidate geological hypotheses — H37 series (Session 13, 2026-10-03)

**Purpose.** Per the standing prompt: 3–5 candidate geological hypotheses we have not tried yet, each
naming the specific layer(s) involved, the physical signature being targeted, why it should catch a
fault *missing* from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs
from anything implemented across GEMSDOE → GEMSDOE28. Ranked by expected DTI improvement vs
implementation cost. Every external source below was verified live on 2026-10-03 (links in
`registry/sources.json`, audit in `evidence/session9_external_verification.json`).

**Live context (read 2026-10-03 from `registry/leaderboard_snapshot_2026-10-03.json`, no automated
access):** public leaderboard #1 DARD 0.3195, #15 wbg1 0.2600 (owner anchor), #19 extradr19 0.2449
(owner T-v2 anchor). The validated one-click primary `b531dae0a36f` (H36-1) projects live to
`0.2717–0.2727` from a fresh-seed holdout of `+0.002599` mean ΔDTI on `240–249`. The reachability
frontier (`evidence/reachability_frontier.json`) and the LOSFO measurement
(`evidence/losfo_farfield_diagnostic.json`) both agree: the gap to 0.3195 is a detection gap of
~1,151 px (24.0 % more credit than the entire best submission captures) and only new dots on
genuinely unmapped structure can close it. Adding them is expensive: H35-1
(`evidence/h35_1_thermal_farfield.json`) was refuted below its own matched-count random control.
The pruning family (H31-1, H32-2, H33-1, H34) is also exhausted (`knowledge/22_h34_result.md`).

**Why this series picks three local-only arms.** Every queued addition arm (H33-3 heat-flow
residual, H33-4 drainage neotectonics, H35-2 heat flow × 2 m probe) requires bytes that only the
GitHub Actions runner bridge can fetch — `sciencebase.gov` and `prd-tnm.s3.amazonaws.com` return
TLS handshake failures from this sandbox (`evidence/session9_external_verification.json`). The
three candidates below are designed to use *only* bytes already restored into `data/`, so they can
be validated today. If the runner has landed the heat-flow archive by the next merge, the
preregistered H37-4 (the heat-flow arm in `registry/next_hypotheses.json`) takes the rank-1
queue slot. No candidate below assumes a weekly slot; per the standing instruction, none is
uploaded until its gate passes a fresh-seed OOF holdout.

---

## Ranking table (expected catalogue-proxy ΔDTI is a planning prior, not a prediction)

| Rank | ID | Hypothesis | Expected ΔDTI | Cost | Data gate (verified 2026-10-03) |
|---:|---|---|---|---|---|
| 1 | **H37-1** | Directional (anisotropic) Poisson-disk re-pack of the H19-5 ridge | `+0.0000` to `+0.0020` | Low (one new module + one holdout run) | None external; uses the H19-5 surface, `labels.tif` for the off-catalogue mask, and the `ridge_nms` strike already in `oof_detector.py` |
| 2 | **H37-2** | LiDAR parallel-scarp "multi-strand" addition on the H19-5 ridge | `+0.0000` to `+0.0018` | Low-medium (12 lidar bands × ridge-NMS output, holdout) | None external; all 12 `lidar_scarp_features_u8.tif` bands restored & hash-verified |
| 3 | **H37-3** | Quaternary volcanics polygon-edge directional anisotropic addition | `+0.0000` to `+0.0012` | Low (uses restored `qfaults_v2_in_footprint.json` and `geodawn_extensions_u8.tif`) | None external; `qfaults_v2` is a hash-pinned local file |

Each is gated against `tau_live = 0.054852` (the `0.2600` live break-even) and against the matched-`N`
random-drop control, exactly as in the H36-1 preregistration (`knowledge/26_preregistration_H36-1.md`).

---

## H37-1 — Directional (anisotropic) Poisson-disk re-pack of the H19-5 ridge

- **Layers.** `data/h19_5_nan.tif` (121,131 px of off-catalogue ridge skeleton, restored and
  hash-pinned: SHA-256 `ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d`); local
  strike vector derived from `ridge_nms` (already in `src/gems27/oof_detector.py`); `data/labels.tif`
  for the known-catalogue mask.
- **Physical signature.** A fault is a *1-D* structure embedded in the 2-D grid. The current
  emission packs dots **isotropically** (`dot_thin(min_dist=d)`), so an `rung 3.0` (300 m) pack
  keeps fewer dots on long straight faults than the kernel mass can usefully cover, and more dots
  on tight bends where the kernel overlap is wasted. An anisotropic pack, with along-strike
  spacing `a_∥ ≥ 2.0` px and cross-strike spacing `a_⊥ ≤ 2.0` px, allows more emission budget
  per unit of on-line credit because the linear DTI kernel saturates along strike but does not
  across strike.
- **Why it catches a fault missing from the catalogue.** A directional pack concentrates dots on
  straight ridges (where the linear truth is) and keeps a wider 200–300 m across-strike scatter on
  bends and tips (where the catalogue's tip-extension pixels gain extra `d_end ≤ 300 m` kernel
  coverage). These are exactly the off-catalogue tip-propagation pixels the H32-1 gate now
  protects; the directional pack should *amplify* their yield, not just preserve it.
- **Difference from repo.** Every prior rung arm is *isotropic* (`thinning.dot_thin`,
  `oof_detector.build_oof_dotted_base` with `thin_d ∈ {1.5, 2.8, 3.0, 3.1623}`). The H34 ladder
  study already showed the *isotropic* rung ladder is bounded (`knowledge/22_h34_result.md`); the
  *directional* rung space is genuinely larger and uses no new bytes.
- **Validation plan.** Frozen 4-fold spatial-CV protocol on the existing infrastructure
  (`scripts/run_h36_1_holdout.py` shape); `seeds 250–254` reserved for H37-1. Primary variant:
  `(a_∥, a_⊥) = (3.5, 2.0)`; control: matched-`N` random deletion. Gate identical to
  H36-1's: gain `> 0`, `≥ 8/10` seeds, `4/4` folds, `Δ`vs random-drop `> +0.0003`. **No slot
  before PASS.** No confirmation, no retuning.
- **Obtainability.** In hand; one new function in `src/gems27/thinning.py`, one runner, one holdout.

## H37-2 — LiDAR parallel-scarp "multi-strand" addition on the H19-5 ridge

- **Layers.** `data/lidar_scarp_features_u8.tif` (12 bands, restored, hash-pinned: SHA-256
  `d580bb8bdcdb941e32fefb8b38044bc5bf04e199bf2e83498c3576e6fc465568`); `data/h19_5_nan.tif`;
  `data/labels.tif`; `oof_detector.ridge_nms` for local strike.
- **Physical signature.** The H19-5 emission is a 1-px ridge (a single crest). Real fault zones
  in the Great Basin are 30–250 m wide, with parallel sub-scarps (multiple strands) and
  antithetic-fault step-overs (e.g. Fairview Peak–Dixie Valley 1954 rupture, Bonham et al. 1988;
  and the Landers 1992 rupture, Sowers et al. 1994). `lidar_step_max` records the *maximum
  multi-scale step height* in a 100 m cell, so it remains high *across* a fault zone — even
  inside it. The H19-5 ridge crest sits where the gradient maximum is; a second ridge in
  `lidar_step_max` parallel to it (within 100–200 m, same strike ± 25°) marks an unmapped
  sub-strand. Adding a *capped* set of off-catalogue dots at those secondary crests should
  capture fault-zone mass the 1-px ridge misses.
- **Why it catches a fault missing from the catalogue.** The compilation is single-trace
  (one polyline per mapped fault, not a fault-zone polygon); secondary strands that never
  formed a primary scarp, or that were overprinted by a younger dominant strand, are common
  in range-front step-overs and the catalogue omits them by choice.
- **Difference from repo.** H27-12 / H32-1 family used *raw* lidar bands as classifier features;
  none used `lidar_step_max` parallel-ridge geometry to *add* dots. The H37-2 transform is an
  *add* (not a prune) but bounded (`≤ 600` added dots / fold, ≈ 0.0015 DTI cost in the worst
  case), and any added dot must clear `tau_live` on the LOSFO far-field harness.
- **Validation plan.** Seeds `255–259`. Frozen gate: `ΔDTI > 0` AND `ΔTPw / ΔFPw > 0.054852`
  AND `≥ 8/10` seeds AND `4/4` folds. **No slot before PASS.** No confirmation, no retuning.
- **Obtainability.** In hand; one new transform in `src/gems27/parallel_scarp.py`, one runner.

## H37-3 — Quaternary volcanics polygon-edge directional anisotropic addition

- **Layers.** `data/qfaults_v2_in_footprint.json` (1,252,341 B, hash-pinned: SHA-256
  `4d6efc7bb3659ea2545353fcec574ef085b0acdb189c7590e4420a7c6c57b41c`); `data/derived_sgmc_faults_100m_u8.tif`
  (198,602 B, hash-pinned); `data/geodawn_extensions_u8.tif` (TMI_up150 band 3, 27,132,925 B,
  hash-pinned); `data/h19_5_nan.tif`; `data/labels.tif`.
- **Physical signature.** Quaternary basaltic and rhyolitic vents and flows tend to be localised
  along pre-existing structural weaknesses; a vent/flow polygon edge aligned (within 30°) with
  the local H19-5 strike is an independent geological argument that the structure exists at
  depth. Where the H19-5 ridge misses a polygon edge by `≤ 300 m`, the disagreement is the
  candidate addition.
- **Why it catches a fault missing from the catalogue.** Catalogued Quaternary faults are
  geomorphic; pre-Holocene structures that localised Quaternary volcanism but no longer offset
  the surface (e.g. a caldera ring) are precisely what the catalogue omits by construction.
- **Difference from repo.** H35-5 (queued) used the 21 individual vent *points* for confirmation
  only; H37-3 uses the polygon *edges* as a low-cost addition source. The SGMC gap-filling
  candidate was already LIVE-REFUTED at `0.0360` (16GEMSDOE `aef8f42c`,
  `evidence/live_inversion.json`); H37-3 is bounded (`≤ 400` added dots / fold) and uses the
  TMI_up150 band (which dilcond / H28-3 used *without* the directional gate).
- **Validation plan.** Seeds `260–264`. Frozen gate as H37-2. **No slot before PASS.**
- **Obtainability.** In hand; one transform in `src/gems27/poly_edges.py`, one runner.