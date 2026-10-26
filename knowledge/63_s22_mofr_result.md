# Session 22 (S22-MOFR) result — negative, not submission-ready

**Date:** 2026-10-26
**Lane:** H44-1 — potential-field marker-offset / piercing-point realignment detector
**Preregistration:** [`knowledge/62_s22_mofr_preregistration.md`](62_s22_mofr_preregistration.md)
**Run card (JSON):** [`evidence/s22_mofr_run_card.json`](../evidence/s22_mofr_run_card.json)
**Runner:** [`scripts/run_s22_mofr.py`](../scripts/run_s22_mofr.py) (single-use; refuses rerun once started-markers exist)
**Verdict: NEGATIVE. `submission_ready: false`. Zero weekly submission slots spent.**

## 1. Hypothesis

A fault that offsets a magnetic or gravity marker horizon leaves a detectable **lateral break
in the horizontal-gradient ridge** of that potential-field map — a piercing point — even when the
fault has no mapped surface trace and is therefore absent from the USGS/INGENIOUS catalogue. This
is a different physical mechanism from every prior GEMSDOE28 hypothesis: it does not use elevation,
hillshade, slope, curvature, LiDAR scarp-step, heat flow, or vent/spring proximity. It uses only
two potential-field bands already present in `training_features.tif`:

- `tmi_hg` (total-magnetic-intensity horizontal gradient), band 3
- `iso_grav_anom_hg` (isostatic-gravity-anomaly horizontal gradient), band 18

## 2. Mechanism

1. Run the shared `ridge_nms` non-maximum-suppression skeletonizer independently on each of the
   two horizontal-gradient bands to get thin ridge skeletons.
2. Extract ridge endpoints (skeleton pixels with exactly one 8-connected neighbor).
3. For every pair of endpoints within a bounded search radius, keep the pair only if:
   - the local ridge strike at each endpoint (via the shared `ridge_strike_degrees`) agrees within
     the same ±20° tolerance already used by `newinfo.steppover_links` (reused, not re-derived), and
   - the perpendicular offset and along-strike gap both fall inside preregistered bounds (a gap that
     is too large is more likely a genuine data break than an offset marker; an offset that is too
     large relative to the gap is more likely two unrelated features).
4. Connect kept pairs with a short bridging line segment; this is the emitted dot/line geometry.
5. Two emission variants were compared: `union` (either lane's candidate pairs) and `corroborated`
   (pairs supported by both the TMI and gravity lanes simultaneously). `union` was denser (42,480
   dots) and was chosen because it did not score worse on the pre-registry canaries; the sparser
   `corroborated` variant was also run and recorded but not selected.

This geometry **never reads `labels.tif`**. It is built entirely from the two potential-field bands.

## 3. Named plausible non-fault mimics (honesty requirement)

- Pipeline / transmission-line magnetic noise (produces real horizontal-gradient ridges and breaks)
- Vehicle, structure, or fence-line cultural magnetic anomalies
- Aeromagnetic or gravity survey-line levelling seams (instrument/processing artifacts, not geology)
- Intrusive dike or sill contacts crossing a gradient ridge (a real contact, not a fault)
- Coincidental ridge termination at a survey-boundary edge effect (grid edge, not geology)

## 4. Experiment 1 — leakage canary + pre-placement registry check (PASSED)

Fresh `HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=31, learning_rate=0.08,
l2_regularization=5.0)` trained per fold, same family used by every prior session's canary.

| Feature                              | AUC    | Leakage suspected (>0.90)? |
|---------------------------------------|--------|------------------------------|
| `tmi_hg_abs_raw`                      | 0.5161 | No |
| `iso_grav_anom_hg_abs_raw`            | 0.5378 | No |
| `marker_offset_support_union`         | 0.5048 | No |
| `marker_offset_support_corroborated`  | 0.4992 | No |

All four features are close to chance (0.50); none approach the 0.90 leakage-stop threshold.

Pre-placement registry comparison (on the `support` surface, before any final dot placement) vs
every catalogued/registered raster in the 9-site + local registry: `method_lane_passed: true`
(no correlation or overlap near the 0.90 / 0.70 stop thresholds).

## 5. Experiment 2 — final placement + validation (PASSED format/uniqueness gates)

Chose the `union` variant: 42,480 off-catalogue dots after intersecting with the competition
footprint and excluding any catalogue pixels (`& foot & ~labels`).

- **Registry novelty on the final dots:** max |Spearman rank correlation| **0.0164**; max 3-pixel
  dot overlap **18.9%** against the full registry (every raster from all 9 user-named GEMSDOE
  sites plus this repo's own prior candidates). Both are far under the 0.90 / 0.70 stop thresholds
  — this file is genuinely unique, not a near-duplicate of anything previously produced anywhere
  in this project.
- **File written:** `docs/downloads/gems28-s22-mofr-union-20261026-599452947272-allfinite.tif`
  (826,992 bytes) via the shared `write_submission(outside="zero")` writer — whole array finite,
  values in {0,1}, no NaN anywhere (the format that avoids the DrivenData "[0,1]" range error).
- **Validator:** `check_variants()` → `format_valid: true`;
  `variant_strict_whole_array_no_nan_allowed.pass: true`.

## 6. Experiment 3 — SegmentHoldout vs a freshly retrained baseline (FAILED)

The full-map marker-offset geometry (`bridge_mask`) was computed once — it never reads labels, so
there is no leakage risk in reusing it across folds — and sliced per fold by
`fold["valid"] & ~fold["visible"]`, exactly matching the protocol's blocked-holdout design. It was
compared against a baseline retrained fresh in each of the same 4 folds (the standard comparator
used throughout this project).

| Quantity | Value |
|---|---|
| Candidate HOLDOUT-DTI | **0.033855** [95% CI 0.029998, 0.037495] |
| Baseline HOLDOUT-DTI (same folds, fresh retrain) | **0.143993** |
| Paired gain | **−0.110138** [95% CI −0.123912, −0.097175] |
| Folds where candidate beat baseline | **0 of 4** |

All three promotion gates (positive paired gain, CI excludes zero in the positive direction,
majority of folds improved) **failed**. This is not a marginal miss — the candidate recovers
roughly a quarter of the baseline's DTI.

## 7. Verdict and what it means

**Verdict: negative.** `submission_ready: false`. The file is published for reproducibility
(`docs/downloads/gems28-s22-mofr-union-20261026-599452947272-allfinite.tif`, registered in
`docs/downloads/manifest.json` as `s22_mofr_candidate` with `verdict: "negative"` and
`submission_ready: false`, verified by `scripts/verify_downloads.py`), but it must not be uploaded.

This closes out the fifth (counting Sessions 18's H42-1, 20's S20V vesselness, 20's H43, 21's
PU-HGB, and now 22's marker-offset) independently preregistered, catalogue-blind, physically
motivated hypothesis in a row to lose decisively to the simple retrained-baseline / "dotted"
catalogue-adjacent family (the H19-5 lineage that produces the 0.2778 GEMSDOE32 champion) on the
real spatially-blocked `SegmentHoldout`. The pattern is now strong enough to state plainly: within
this feature stack and this holdout design, further hand-built geological ridge/geometry detectors
are unlikely to close the gap to 0.2778, let alone the public leaderboard's 0.4413. Closing that
gap most plausibly requires either (a) new external data not already encoded in the provided
feature stack (and no such new, sandbox-obtainable source was identified or used this session —
USGS 3DEP/GeoDAWN hosts remain outside this sandbox's network allowlist, so any such path stays
explicitly deferred, not assumed viable), or (b) a materially different modelling approach, such as
a learned dense-segmentation model over the full feature stack rather than a hand-built ridge/edge
geometry fed into a shallow classifier.

## 8. Budget

3 of 3 preregistered experiments used; total wall time 246.18 s (well inside the 2-hour cap).
