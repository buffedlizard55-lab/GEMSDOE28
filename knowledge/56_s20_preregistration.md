# Session 20 Preregistration — Ranked Untried Geological Hypotheses & Locked Lane `S20-NCHC` (`H43-1`)

- **Date (UTC):** `2026-10-26`
- **Branch:** `arena/3a8a5bef-gemsdoe28` (base commit `10c26af3dc4d45292189734b0b696c7afb24ffb1`)
- **Assigned single lane:** `S20-NCHC` (`H43-1`: *Multi-Scale Nematic Cross-Modal Lineament Concordance & Hydrothermal Clay-Cap Margin Corridor with 300 m Submodular Kernel Allocation*)
- **Reserved fresh seeds (never previously used in `GEMSDOE28` or sibling PRs):** classifier/subsample seeds `340, 341, 342, 343, 344` (`340` for 4-fold OOF holdout; `340–344` ensemble for full-fit emission); spatial-block bootstrap seed `20261034` (`n_boot = 1000`, `block_px = 100` = `10 km`).
- **Experiment budget:** Strictly capped at **3 experiments** and **2 hours** wall-clock (`Experiment 1`: feature extraction + single-feature leakage canary + 4-fold OOF surface + pre-placement registry uniqueness gate; `Experiment 2`: `SegmentHoldout` `gems-segment-pooled-v1` hide-and-recover evaluation against paired baselines; `Experiment 3`: 5-seed full-fit GeoTIFF emission via shared `submission_writer.py` + post-placement 112/120-raster registry uniqueness gate + automated byte/promotion verification).
- **Pre-run commitment:** Written and frozen **before** extracting `S20-NCHC` features, touching `labels.tif` in any model fit, or running `SegmentHoldout`. No hyperparameter, feature weight, threshold, or budget constant may be tuned after observing holdout DTI.

---

## 1. Forensic Diagnosis Motivating Session 20

1. **Why unsupervised single-mechanism physics lanes failed `SegmentHoldout`:**
   - `S18-MXTP` (`3e95505c011a`, extrapolated TMI/gravity ridges) achieved `HOLDOUT-DTI = 0.020384` (`gems-segment-pooled-v1`, 60,988 withheld positives, 95% CI `[0.017609, 0.023442]`).
   - Parallel PR #48 `S19-ASCP` (`dc717c1ab13b`, LiDAR antislope paired-curvature scarps) achieved `HOLDOUT-DTI = 0.080806` (`[0.068055, 0.093334]`) vs the retrained visible-only 32-band H38 baseline `0.141694` (`[0.128368, 0.154587]`).
   - *Physical reason:* Across the `5,167,373`-pixel (`51,674 km²`) Great Basin / Walker Lane study area, non-fault geological boundaries (welded-tuff mesa rims, pluton aureoles, Lake Lahontan wave-cut shorelines, GeoDAWN E–W micro-leveling stripes, and variable helicopter terrain-clearance drape anomalies documented by Glen & Earney, 2024, DOI `10.5066/P93LGLVQ`) vastly outnumber concealed faults in any single physical channel.
2. **Why pixel-wise 32-band GBDT lanes collided (`>90%` 3-px overlap) with local registry probe `52a13184267e`:**
   - `gems28-h37-1-probe-union-pool-r1-20261003-52a13184267e-allfinite.tif` (`38,545` px) equals `prob_order_pack` on `h19_5 | ridge_nms(oof_detector_32band, sigma=1.0)`.
   - The 32-band `oof_detector` relies heavily on **0th-order regional scalar levels** (`det_elev`, `iso_grav_anom`, `rtp`, `tmi`, `depth_to_base_surf`, `cond_surf`), memorizing quadrant elevation/gravity contours and collapsing to the identical `sigma=1.0` ridge network (`91.3%` 3-px overlap in `H40-1`).
3. **Why both gates can be satisfied simultaneously without touching any historical raster:**
   - Removing raw 0th-order scalar level bands and representing every pixel strictly through **translation- and level-invariant multi-scale Hessian/Frangi tubular lineament operators, 4-modality nematic strike concordance, GeoDAWN E–W flight-line artifact suppression, and hydrothermal clay-cap/alteration/geothermometry coupling**, combined with **submodular 300 m triangular-kernel coverage (`gems27.packing.coverage_greedy`)** on fold-calibrated corridor probabilities (`B=2` `d_visible > 2.0 px` strictly from `fold["visible"]`), targets genuine concealed structural corridors while structurally diverging from both `H19-5` (`e5eb6e7e`) and `52a13184267e`.

---

## 2. Five Ranked Untried Candidate Geological Hypotheses

All expected DTI deltas below are **pre-experiment planning judgments, never scores or projections**.

### Rank 1 (LOCKED SESSION LANE) — `H43-1` / `S20-NCHC`: Multi-Scale Nematic Cross-Modal Lineament Concordance & Hydrothermal Clay-Cap Margin Corridor with 300 m Submodular Allocation
- **Layers (100% locally restored & SHA-256 verified against `registry/data_manifest.json`; zero catalogue layers):**
  - Cached `prepared/features.npy` (`sha256: 83ed2704ee2de03cf8b1c8f2966fcf71813501df97c1c35400e6c0415393f6dc`) derived from `training_features.tif` and `lidar_scarp_features_u8.tif` (using derivative/strain/LiDAR channels directly and computing multi-scale Hessian/gradient operators from `rtp`, `iso_grav_anom`, `depth_to_base_surf`, `cond_surf`, `det_elev` while **dropping** raw 0th-order scalar levels from classifier training).
  - `geodawn_extensions_u8.tif` (`sha256: 2224604a...`, USGS GeoDAWN DOI `10.5066/P93LGLVQ`, CC0 1.0): `ThK` (`Th/K`), `UK` (`U/K`), `UTh` (`U/Th`), `TMI_up150`.
  - `gdr_wellspring_in_footprint.csv` (`sha256: 4eb7d85e...`, INGENIOUS DOE GDR #1391 DOI `10.15121/1881483`, CC-BY-4.0): strictly physical columns `row`, `col`, `temp_c`, `geothermquartz_c`, `geothermchalc_c` (`dist_known_fault_px` explicitly banned and tested).
  - `docs/data/sb_heat_flow_in_footprint.json` (`sha256: d2340b7d...`, DeAngelo et al. 2022, USGS DOI `10.5066/P9BZPVUC`, public domain): `hf_resid`.
- **Physical signature:**
  1. *Multi-scale Frangi–Hessian tubular ridgeness* ($\sigma \in \{1.5, 4.0, 10.0\}\text{ px} = \{150\text{ m}, 400\text{ m}, 1\text{ km}\}$) and double-angle strike directors $d_m = (\cos 2\theta_m, \sin 2\theta_m)$ on four physical boundary fields: magnetic gradient $\|\nabla G_\sigma(\text{rtp})\|$, isostatic-gravity density step $\|\nabla G_\sigma(\text{iso\_grav\_anom})\|$, conductive-base interface step $\|\nabla G_\sigma(\text{depth\_to\_base\_surf})\|$, and detrended piedmont scarp slope $\|\nabla G_\sigma(\text{det\_elev})\|$ (+ 1 m LiDAR scarp coherence with explicit `lidar_valid` coverage indicator).
  2. *4-Modality nematic scalar order parameter* $S_{\text{nematic},\sigma}(x) = \|\sum_m w_{m,\sigma}(x) d_{m,\sigma}(x)\| / (\epsilon + \sum_m w_{m,\sigma}(x))$ at $400\text{ m}$ and $1\text{ km}$, plus *top-two cross-modal harmonic ridgeness* $\sqrt{w_{(1)}(x)\,w_{(2)}(x)}$ (preserving blind sub-playa faults where surface scarp $w_{\text{topo}} = 0$ but `mag`+`grav` or `grav`+`em` co-align) and *GeoDAWN E–W flight-line artifact diagnostic* $A_{\text{ew}}(x) = \mathcal{T}_{\text{mag},1.5}(x)\max(0, -\cos 2\theta_{\text{mag},1.5}(x))^2$.
  3. *Hydrothermal conduit & alteration margin observables*: lateral clay-cap boundary gradient $\|\nabla G_4(\text{cond\_surf})\|$, upward-continuation magnetic shallow-source differential $|\text{rtp}_{\text{norm}} - \text{TMI\_up150}_{\text{norm}}|$ gradient, radiometric K-metasomatism ($-\text{Th/K}$ local contrast) & redox cross-gradient $\|\nabla G_3(\text{U/Th})\|$ (`rad_valid` masked), and $1.5\text{ km}$ Gaussian plumes of silica thermal disequilibrium $\max(0, T_{\text{quartz}} - T_{\text{meas}})$, measured thermal anomaly $\max(0, T_{\text{meas}} - 25^\circ\text{C})$, and conductive heat-flow residual $\max(0, \text{hf\_resid})$.
  4. *Fold-calibrated PU-GBM + submodular 300 m DTI coverage*: `HistGradientBoostingClassifier` fit strictly on `fold["train"]` (`fold["visible"]` positives vs random negatives), monotonically bin-calibrated inside `fold["train"]` to empirical corridor fault density $\hat{p}(x)$, masked by fold-local `d_visible > 2.0 px`, and allocated via `gems27.packing.coverage_greedy(radius_px=3.0)` over the top-6% corridor (`f_budget = 0.0095`, `~49,090` full-map dots).
- **Why USGS/INGENIOUS catalogues miss these faults:** Late Quaternary surface-rupture mapping misses concealed faults beneath active Holocene alluvial fans, Lake Lahontan lacustrine basins, and diffuse Walker Lane stepovers/relay ramps (`~75%` of Great Basin geothermal systems are blind or lack prominent surface scarps; Faulds & Hinz, 2015).
- **Non-fault geological & survey mimics:** (a) GeoDAWN E–W flight-line micro-leveling stripes ($200\text{–}400\text{ m}$ spacing, azimuth $90^\circ$) and steep-terrain helicopter drape anomalies (Glen & Earney, 2024); (b) Lake Lahontan wave-cut shorelines and road/canal embankments (1-modality geomorphic steps); (c) curved pluton aureoles and flat-lying welded-tuff mesa rims (high $|\lambda_2/\lambda_1|$, non-linear perimeter); (d) lateral down-gradient warm groundwater outflow plumes in piedmont gravels without structural lineament support.
- **How it differs from repo:** Eliminates all raw 0th-order scalar level bands and `H19-5` reuse; introduces 2D Frangi–Hessian eigen-tubularity, 4-modality nematic order parameter $S_{\text{nematic}}$, GeoDAWN E–W stripe diagnostic, clay-cap margin + silica-disequilibrium + K-metasomatic feature fusion, and full-corridor Minoux submodular 300 m kernel allocation instead of `ridge_nms(sigma=1.0)` + `dot_thin`.
- **Expected DTI delta (planning judgment, NOT a score) × cost:** `+0.015` to `+0.035` `HOLDOUT-DTI` over retrained 32-band `GEMSDOE28` baseline (`0.1417`) × Low–Medium cost (~35 min CPU, `< 500 MB` RAM, zero external downloads).

### Rank 2 — `H43-2`: Continuum Strain-Resolved Andersonian Slip & Dilation Tendency on Geophysical Hessian Directors
- **Layers:** `geod_shearrate`, `geod_dilaterate`, `geod_2ndinv` (`training_features.tif`) + geophysical Hessian strike $\theta(x)$ from `rtp` and `iso_grav_anom`.
- **Physical signature:** Resolve continuum geodetic extension/shear orientation onto each pixel's geophysical lineament strike $\theta(x)$ to score NNE-striking normal-dilation segments and NW/ENE Walker Lane dextral/sinistral conjugate shears everywhere in the footprint (100% spatial coverage).
- **Why off-catalogue:** Intrabasinal accommodation zones and blind relay faults lack Quaternary scarps but sit in optimal transtensional dilation orientations.
- **Non-fault mimics:** NNE-aligned basaltic dike swarms or longitudinal eolian dunes parallel to regional $S_{H\max}$.
- **Differs from repo:** `H33-1` (`kinematics.py`) borrowed `TS`/`TD` from mapped Quaternary fault traces within 1 km (failing on 88% of off-catalogue pixels and risking near-catalogue bias); continuum geophysical-director resolution has never been tested in `GEMSDOE28`.
- **Expected DTI delta (planning judgment) × cost:** `+0.003` to `+0.010` `HOLDOUT-DTI` × Low cost (~25 min); ranked #2 because long-wavelength (~25 km) GPS strain smoothing limits standalone spatial sharpness without `H43-1`'s multi-modal fusion.

### Rank 3 — `H43-3`: Terrain-Clearance De-Draped Magnetic Vertical-Continuation Differential & Tilt-Contact Ratio
- **Layers:** `rtp`, `tmi_hg`, `tmi_vg`, `det_elev`, `det_elev_slope` (`training_features.tif`) + `TMI_up150` (`geodawn_extensions_u8.tif`).
- **Physical signature:** Locally orthogonalize short-wavelength magnetic gradients against topographic slope/Laplacian (removing variable helicopter drape over volcanic ridges per Glen & Earney, 2024), then extract Salem et al. (2007) tilt-angle horizontal gradient peaks paired with shallow-minus-150m upward-continued magnetic decay.
- **Why off-catalogue:** Shallowly buried (`50–300 m`) Tertiary volcanic fault blocks beneath piedmont alluvium produce sharp de-draped tilt zero-crossings with zero surface scarp.
- **Non-fault mimics:** Paleochannels filled with magnetic basaltic cobbles and reversely magnetized lava-flow lobe margins.
- **Differs from repo:** `H39-1` used FFT upward continuation without terrain-drape orthogonalization inside the duplicate 32-band `oof_detector`; `S18-MXTP` extrapolated raw TMI/gravity ridges unsupervised (`0.0204`).
- **Expected DTI delta (planning judgment) × cost:** `+0.002` to `+0.009` `HOLDOUT-DTI` × Low–Medium cost (~30 min); magnetic-only misses non-magnetic Paleozoic carbonate/siliciclastic faults.

### Rank 4 — `H43-4`: Multi-Depth 3D ModEM Magnetotelluric Crustal Conductance Column Decoupling (`2–200 km`)
- **Layers:** Official USGS ScienceBase release `62979746d34ec53d276c113b` (Peacock et al., 2022, DOI `10.5066/P9TWT2LU`, CC0 public domain: 5 depth-slice GeoTIFFs `2–12`, `12–20`, `20–50`, `50–90`, `90–200 km`) + `cond_surf`.
- **Physical signature:** Subvertical upper-crustal (`2–12 km`) conductance gradients decoupled from lower-crustal (`20–50 km`) terrane boundaries identify active brittle-crust hydrothermal fluid pathways (Peacock & Bedrosian, 2022).
- **Why off-catalogue:** Deep blind geothermal fault-valve conduits capped by ductile smectite clay often lack surface fault scarps.
- **Non-fault mimics:** Paleozoic graphitic/pyritic black shales (Roberts Mountains allochthon) and hypersaline playa brines.
- **Differs from repo:** Untried `H33-2` in `registry/next_hypotheses.json`.
- **Official source obtainability check:** Official USGS DOI `10.5066/P9TWT2LU` (`www.sciencebase.gov`) is free public-domain data, **but `www.sciencebase.gov` is outside this sandbox's outbound network allowlist** and the 5 GeoTIFF slices are absent from `registry/data_manifest.json` and sibling mirrors. Marked **blocked on external ingest in this environment** (not viable for immediate execution).

### Rank 5 — `H43-5`: 1 m USGS 3DEP LiDAR Hydrologic Drainage-Network Deflection & Knickpoint Alignment
- **Layers:** Competition-listed `1m_DEM_links.csv` (`data/dem_links.json`, official USGS 3DEP 1 m DEM tiles on `prd-tnm.s3.amazonaws.com`, public domain).
- **Physical signature:** Aligned channel deflections, beheaded fan channels, and knickpoint trains across degraded alluvial-fan fault traces.
- **Why off-catalogue:** Active piedmont sedimentation erases small vertical scarps while preserving channel-network deflections.
- **Non-fault mimics:** Resistant bedrock ribs, Lahontan beach bars, and road/canal culverts.
- **Differs from repo:** Untried `H33-4`; existing `lidar_scarp_features_u8.tif` measures local slope/curvature amplitude only, not flow-routing topology.
- **Official source obtainability check:** Tile URLs on `prd-tnm.s3.amazonaws.com` are free official USGS 3DEP assets, **but outside this sandbox's outbound network allowlist** and multi-GB in volume. Marked **blocked on external ingest in this environment**.

---

## 3. Frozen Mathematical Specification of `S20-NCHC` (`H43-1`)

### 3.1 Exact 28-Feature Level-Invariant Stack (`s20_nchc_features.npy`)
Every feature is computed purely from label-free physical layers; outside the `5,167,373`-pixel competition footprint all features are `0.0`, and inside the footprint all features are finite `float32` (no `NaN`/`Inf`). Zero raw regional scalar level bands (`det_elev`, `rtp`, `tmi`, `iso_grav_anom`, `depth_to_base_surf`, `cond_surf`) are included:

1. `mag_tubular_150m`, `mag_tubular_400m`, `mag_tubular_1000m`: Frangi–Hessian scale-normalized tubular ridgeness of $\|\nabla G_\sigma(\text{rtp})\|$ at $\sigma \in \{1.5, 4.0, 10.0\}\text{ px}$ ($\beta_F = 0.5$), robust-scaled on `[P5, P99]` in-footprint.
2. `grav_tubular_400m`, `grav_tubular_1000m`: Frangi–Hessian tubular ridgeness of $\|\nabla G_\sigma(\text{iso\_grav\_anom})\|$ at $\sigma \in \{4.0, 10.0\}\text{ px}$.
3. `em_cb_tubular_400m`, `em_cb_tubular_1000m`: Frangi–Hessian tubular ridgeness of $\|\nabla G_\sigma(\text{depth\_to\_base\_surf})\|$ at $\sigma \in \{4.0, 10.0\}\text{ px}$.
4. `topo_tubular_150m`, `topo_tubular_400m`, `topo_tubular_1000m`: Frangi–Hessian tubular ridgeness of $\|\nabla G_\sigma(\text{det\_elev})\|$ at $\sigma \in \{1.5, 4.0, 10.0\}\text{ px}$.
5. `nematic_order_400m`, `nematic_order_1000m`: 4-modality (`mag`, `grav`, `em_cb`, `topo`) amplitude-weighted double-angle nematic order parameter $S_{\text{nematic},\sigma} = \|\sum_m w_{m,\sigma} d_{m,\sigma}\| / (10^{-6} + \sum_m w_{m,\sigma}) \in [0, 1]$.
6. `top2_harmonic_400m`, `top2_harmonic_1000m`: Geometric mean $\sqrt{w_{(1),\sigma}\, w_{(2),\sigma}}$ of the two strongest modalities at each pixel (retaining full sensitivity on sub-playa blind faults where `topo` ridgeness is zero).
7. `geodawn_ew_stripe_150m`: Explicit GeoDAWN E–W flight-line artifact diagnostic $\mathcal{T}_{\text{mag},1.5}\cdot \max(0, -\cos 2\theta_{\text{mag},1.5})^2$ (allowing trees to discount uncorroborated E–W micro-leveling stripes).
8. `mag_up150_step_300m`: Shallow-source vertical attenuation gradient $\|\nabla G_3(\text{zscore}(\text{rtp}) - \text{zscore}(\text{TMI\_up150}))\|$ (`TMI_up150 > 0` masked).
9. `claycap_margin_400m`: Smectite clay-cap lateral margin gradient $\|\nabla G_4(\text{cond\_surf})\|$.
10. `rad_k_metasom_local`: Local potassic alteration contrast $G_{20}(\text{ThK}) - G_2(\text{ThK})$ over valid radiometric coverage (`ThK > 0`; `0.0` where invalid).
11. `rad_uth_redox_step_300m`: Cross-strike redox mobilization gradient $\|\nabla G_3(\text{UTh})\|$ over valid coverage (`UTh > 0`), plus `rad_valid_flag` (`float32` `{0, 1}`).
12. `hydro_qtz_diseq_1500m`, `hydro_temp_anom_1500m`, `hydro_hf_resid_1500m`: $1.5\text{ km}$ ($\sigma = 15\text{ px}$) Gaussian-smoothed point-source thermal anomalies from `gdr_wellspring_in_footprint.csv` ($\max(0, T_{\text{qtz}} - T_{\text{meas}})$ and $\max(0, T_{\text{meas}} - 25^\circ\text{C})$, `dist_known_fault_px` NEVER read) and `sb_heat_flow_in_footprint.json` ($\max(0, \text{hf\_resid})$).
13. `strain_2ndinv_grad_1000m`, `strain_dilate_norm`, `seis_ieq_norm`: Tectonic strain-rate gradient $\|\nabla G_{10}(\text{geod\_2ndinv})\|$, robust-scaled dilatation rate `geod_dilaterate`, and robust-scaled earthquake density `ieq_n100a15`.
14. `lidar_scarp_composite`, `lidar_valid_flag`: Composite 1 m LiDAR scarp prominence $\text{robust}(\text{lidar\_step\_max})\cdot(0.5 + 0.5\,\text{lidar\_coh100}/255)$ on valid 3DEP swaths (`lidar_valid > 0`) plus explicit `lidar_valid_flag` (`{0, 1}`).

### 3.2 Fold-Isolated Training, Calibration & Submodular 300 m Allocation
- **Evaluator:** Shared `gems.holdout.SegmentHoldout` (`gems-segment-pooled-v1`, 4 geographic quadrants, `buffer_m = 1500.0` whole-component + quadrant buffer, `60,988` withheld positives across the 4 folds, pooled $\alpha = 0.2, \beta = 0.8$, $R = 300\text{ m}$ triangular kernel).
- **Classifier:** `sklearn.ensemble.HistGradientBoostingClassifier(loss="log_loss", learning_rate=0.05, max_iter=300, max_leaf_nodes=63, max_depth=6, min_samples_leaf=100, l2_regularization=5.0, random_state=seed)`.
- **Fold training isolation:** On fold $f$, positive rows are `fold["train"] & fold["visible"]`; negative rows are up to `250,000` uniformly subsampled (`seed + f`) rows from `fold["train"] & ~fold["visible"]` (with `sample_weight` weighting negatives by `N_neg_train / n_neg_sampled` so predicted probabilities are calibrated directly to true prior corridor fault density on `fold["train"]`!).
- **Fold-local `B=2` off-catalogue hygiene:** On fold $f$, `allowed_f = fold["eval_mask"] & (distance_transform_edt(~fold["visible"]) > 2.0)` — strictly derived from `fold["visible"]`, NEVER from full `labels.tif`.
- **Submodular 300 m kernel allocation:** Over candidate corridor pixels `cand_f = allowed_f & (prob_f >= quantile(prob_f[allowed_f], 0.94))` with weight `w_f = np.where(cand_f, prob_f, 0.0)`, run `gems27.packing.coverage_greedy(cand_f, w_f, n_target=int(round(0.0095 * fold["eval_mask"].sum())), radius_px=3.0)` and emit binary `1.0` on selected pixels (`0.0` elsewhere).

### 3.3 Promotion Gate Criteria (All Must Pass — Fail-Closed)
1. **Single-feature leakage canary:** Every one of the 28 features satisfies `max(AUC, 1 - AUC) <= 0.90` on `SegmentHoldout.canary` (both pooled and per-fold).
2. **Pre-placement & post-placement registry uniqueness:** Against **all 112 unique published 9-site + PR #48 rasters** (`GEMSDOE24`, `25`, `27`, `28`, `30`, `31`, `32`, `33`, `36`, and `PR #48`), `max |Spearman| <= 0.90` AND `max within_3px <= 0.70` (with prospective 120-raster audit including historic calibration controls reported alongside via `gems.novelty.compare_prospective_registry`).
3. **Holdout superiority (`HOLDOUT-DTI`):** Positive pooled `HOLDOUT-DTI` gain with **95% spatial-block paired bootstrap CI lower bound strictly `> 0.0`** (`block_px = 100` = `10 km`, `n_boot = 1000`, `seed = 20261034`) against the retrained visible-only `GEMSDOE28` H38 baseline (`B0_32band_h38_vis`), AND also reported head-to-head against the visible-only `H19-5` `d=2.8` `B=2` champion-analog (`B1_champion_analog_vis`).
4. **Byte-level submission validation:** Shared `submission_writer.py` (`outside="zero"`, `nodata=None`) + `scripts/verify_downloads.py` + `scripts/check_promotion.py` all pass (`count=1`, `dtype=float32`, `EPSG:32611`, `3730 × 3292`, all `12,279,160` cells finite in `[0.0, 1.0]`, zero full-catalogue overlap, `slot_selected: false`).
