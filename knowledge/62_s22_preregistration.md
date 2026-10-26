# S22 Preregistration — Signed Piedmont Break-in-Slope + Asymmetric Polarity Lane

- **Date (UTC):** 2026-10-26
- **Branch:** `arena/177c1ff2-gemsdoe28` (base: main@2c839d1)
- **Session:** S22-SIGN (H43-2 variant) — single declared lane for this parallel session
- **Reserved fresh seeds (never used in GEMSDOE28 prior sessions 15–21):** `360, 361, 362` (4-fold OOF holdout; 360 also full-fit emission seed) + bootstrap seed `20261026` (block_px=100, n_boot=1000). These are disjoint from S20-NCHC (340–344) and S21-PUHGB (350–352) and from all S19/S20V seeds (240–279, 180–189) per registry audit.
- **Budget:** 3 experiments / 2 h cap. Exp1: surface build + per-feature leakage canary + pre-placement registry novelty. Exp2: SegmentHoldout pooled DTI vs retrained visible-only 32-band+H38 baseline. Exp3: full-fit emission + post-placement novelty + byte-level validation. No tuning after observing holdout.
- **Provenance:** All inputs SHA-256 pinned via `registry/data_manifest.json` + `evidence/data_preparation.json` (prepared/features.npy 32 bands). No DrivenData auth, no new external bytes beyond already-restored local mirrors.

## Hypothesis & Mechanism

**H43-2-SIGN:** Great Basin piedmont range-front faults manifest as *signed* slope-normal profile concavity (∂²z/∂n² > 0 at bedrock→bajada inflection) coincident with *asymmetric* LiDAR scarp polarity (upface_max ≫ downface_max) and along-strike coherence, corroborated by co-aligned magnetic/gravity/conductive-base lineament tubularity. The surface is:

```
S(x) = [σ( κ_signed(x) )]^0.5 * [σ( A_pol(x) )]^0.3 * [ σ( C_sub(x) ) ]^0.2
```

where κ_signed = normalized profile curvature along slope-normal, A_pol = (upface - downface)/255 * coh100/255 with downhill-vs-uphill selectivity, C_sub = multi-scale gradient concordance of rtp/grav/em_cb, σ = robust [0,1] sigmoid via 5–95% quantile. Weights frozen before any holdout; geometric-mean form prevents single-channel domination. B=2 (d_cat >200 m) hygiene enforced from fold-visible faults only.

**Non-fault mimic:** Terrace risers (symmetric), Lahontan shorelines (contour-parallel), GeoDAWN E–W stripes (no topographic step), road cuts (high coh but symmetric).

## Layers (all locally restored)

1. `training_features.tif` (19 bands, 100 m) — specifically `det_elev` (DEM) for curvature, `tmi_hg`/`rtp` for mag, `iso_grav_anom`/`iso_grav_anom_hg` for grav, `depth_to_base_surf`, `cond_surf`, `geod_*` for strain context (not directly scored).
2. `lidar_scarp_features_u8.tif` (12 bands) — `ex_max`, `ex_mean`, `step_max`, `downface_max`, `upface_max`, `cross_max`, `relief`, `coh100`, `strike`, `valid` (>0).
3. `labels.tif` / `existing_faults.tif` for catalogue masking only (distance to known faults d_vis/dist_cat).
4. `geodawn_extensions_u8.tif` / `geodawn_rad_u8.tif` for subsurface corroboration (U8 ranks, not scalar levels).
5. `prepared/features.npy` (32 bands) for leakage canary baseline comparison only — the S22 surface itself is computed deterministically from raw rasters to avoid scalar-level leakage.

## Feature Decomposition for Leakage Canary (must all pass AUC ≤0.90)

Per-protocol, each named physical leg is tested alone via `SegmentHoldout.canary`:

- `f_concavity` = σ(κ_signed)
- `f_polarity` = σ(A_pol)
- `f_coherence` = σ(coh100/255) masked to valid
- `f_mag_tubular` = gradient magnitude of rtp_hg
- `f_grav_tubular` = gradient magnitude of grav
- `f_emcb_tubular` = gradient magnitude of depth_to_base_surf
- `f_combined` = final S(x)

Any AUC >0.90 → fail-closed, log irregularity, no emission.

## Uniqueness Gates

Pre-placement surface and final-dot Spearman vs every registry raster (112 9-site+PR48 published TIFFs) must satisfy |r| ≤0.90 and top-K 3-px support overlap ≤70%. Same thresholds applied post-placement to final binary dots via `shared_novelty.dot_overlap`. Failure → log duplicate, stop, negative verdict.

## Holdout Protocol (gems-segment-pooled-v1)

- 4 quadrants (NW, NE_LidarGapHeavy, SW, SE), 20% whole-component hide per quadrant, 1500 m buffer.
- On each fold: hide whole fault components intersecting the buffer, derive *every* catalogue-based distance strictly from `fold["visible"]`, mask visible faults pixel-exactly, score pooled DTI (α=0.2 β=0.8 300 m triangular) over all 60,988 withheld positives.
- Baseline: retrained visible-only 32-band HistGBM + H38 heatflow/Euler (same seeds, same B=0 hygiene) — the identical comparator that beat S20-NCHC and S21.
- Paired 10-km block bootstrap (583 blocks, 1000 draws, seed 20261026) for 95% CI.
- **Promotion rule (all must hold):** pooled ΔDTI >0 with 95% CI lower bound >0 vs B0, and non-negative per-fold median; otherwise verdict `negative`, `submission_ready:false`, 0 slots spent.

## Emission

Full-footprint fit: compute S(x) everywhere, mask to `footprint & ~labels & (d_cat >2 px)` (B=2 hygiene from full catalogue), select top-K by S(x) such that Poisson-disk thinned (d=2.8) lands at 37,500 ±1% dots (target 37,654 to match champion budget for comparability), emit via `thinning.dot_thin(S>quantile, 2.8)`. Write both `nan` (nodata=NaN outside) and `allfinite` (0 outside, finite [0,1] everywhere) variants via `submission.write_geotiff`, plus `zip_single`. Verify via `verify_geotiff` (grid/crs/shape/transform/range/finiteness). Compute SHA-256, bytes, emitted_px, overlap.

## Run Card Schema

JSON with: session, hypothesis, mechanism, non_fault_mimic, holdout {label dti ci baseline paired_gain}, registry {members max_abs_spearman max_overlap}, raster_sha256, validator {no_nan_inside range_0_1 crs/shape/transform}, submission_name + note ≤140 chars, verdict promote/negative, limitations, provenance hashes.

## Decision Disclosure

S22 is one of several parallel sessions from identical prompt. Seeds 360–362 are unique to this branch; never pool numbers across concurrent lanes. A negative holdout is a deliverable; no slot is spent without superiority.

