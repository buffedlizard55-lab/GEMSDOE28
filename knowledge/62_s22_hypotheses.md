# S22 Ranked Geological Hypotheses — 2026-10-26 (Pass 1)

**Branch:** `arena/177c1ff2-gemsdoe28` · **Date:** 2026-10-26 UTC
**Context:** S20-NCHC (H43-1) proved swath-level uniqueness (53% max overlap vs 91% prior) and won the Walker Lane SW quadrant (+0.0134 HOLDOUT-DTI) but lost pooled (-0.0132). Its fold diagnostics isolate the missing operator: symmetric Hessian tubularity of |∇z| peaks *upslope* of true piedmont break-in-slope scarps, causing systematic misses in NE/SE Basin-and-Range range-front folds. S21-PUHGB (pure ML habitat without physics) lost pooled -0.0223. The synthesis is signed concavity + polarity.

**Evaluator:** `gems-segment-pooled-v1` (quadrant LOSFO, 20% whole-component hide + 1500 m buffer, catalogue-derived features only from `fold["visible"]`, pixel-exact masks, α=0.2 β=0.8 300 m triangular DTI, 4-quadrant pooled + 583×10 km block bootstrap).

## Ranked Hypotheses (Expected HOLDOUT-DTI vs Cost)

### 1. H43-2 — Signed Piedmont Break-in-Slope Concavity + Asymmetric LiDAR Polarity + Subsurface Concordance Hybrid [SELECTED LANE]
- **Layers:** `det_elev` (DEM 100 m) + `lidar_scarp_features_u8.tif` (12-band LiDAR scarp descriptors, bands upface_max/downface_max/coh100/valid) + `training_features.tif` (`tmi_hg`, `rtp_tilt`, `iso_grav_anom_hg`, `depth_to_base_surf`, `geod_2ndinv`) — all already restored & hash-pinned (`registry/data_manifest.json`), no new download.
- **Physical signature:** Mountain→piedmont break-in-slope is a *signed* slope-normal profile concavity event: ∂²z/∂n² > 0 where steep bedrock slope collapses to gentle bajada. Asymmetric LiDAR polarity selects uphill-facing scarps (upface_max ≫ downface_max) with along-strike coherence >100 m, rejecting symmetric terrace risers and symmetric channels. Subsurface concordance requires co-aligned magnetic/gravity/conductive-base lineament tubularity within 300–1000 m to reject fluvial terrace artefacts.
- **Why it catches a fault missing from USGS/INGENIOUS:** USGS Qfaults v2 compilation is aerial-photo/scarp-height biased: subtle 0.5–3 m piedmont scarps degraded by Holocene alluviation are systematically missed, especially on Basin-and-Range range-front steps where the morphological signature is *signed concavity* not symmetric ridge strength. Intrabasinal blind faults have no scarp at all but retain magnetic/gravity/conductive-base steps — the hybrid keeps both.
- **Non-fault mimic:** Fluvial terrace risers (symmetric up=down, high concavity but no subsurface lineament), Lake Lahontan paleoshorelines (contour-parallel, constant elevation), GeoDAWN E–W flight-line stripes (azimuth 90°, no topographic step), road cuts (high coherence but symmetric).
- **Differs from repo:** S19-ASCP used symmetric Hessian vesselness of |∇z| (peak upslope of true scarp); S20-NCHC used nematic tubularity but *without* signed concavity, losing NE/SE. No prior emission uses ∂²z/∂n² polarity. Pure ML lanes (S21-PUHGB) ignore physics.
- **Expected HOLDOUT-DTI:** +0.010 to +0.025 vs S20-NCHC baseline (+0.008 to +0.020 vs 32-band H38) — highest leverage because it directly repairs folded -0.029/-0.038 NE/SE losses while preserving SW win. **Cost:** Low (25 min CPU, ~1 GB RAM, no GPU).

### 2. H43-3 — 3D Euler Deconvolution SI=0 Contact Depth-Coherence
- **Layers:** `tmi`, `rtp`, `tmi_hg`, `iso_grav_anom`, `iso_grav_anom_hg` + DEM for topographic correction.
- **Signature:** Euler homogeneity solutions (Reid et al. 1990, Geophysics) SI=0 fault-contact cluster with shallow depth (<500 m) and along-strike coherence >1 km.
- **Why missing:** Resolves dipping intrabasinal faults beneath 200–1500 m Plio-Quaternary fill with zero surface scarp.
- **Mimic:** Steep-topography helicopter drape artefacts, N≥1.5 pluton margins.
- **Differs:** Inverts dip/offset vs 2D ridge maxima. **Expected:** +0.005 to +0.012. **Cost:** Medium (35 min, Euler windowing).

### 3. H43-4 — Transtensional Stepover Coulomb Dilation Bridge
- **Layers:** `geod_shearrate`, `geod_dilaterate`, `geod_2ndinv`, `ieq_n100a15` + visible-only fault tips + gravity/magnetic bridge gradients.
- **Signature:** Solves anisotropic Coulomb dilation between visible-only fold fault tips weighted by strain rate, microseismicity, geophysical bridge alignment.
- **Why missing:** Accommodation zones/horsetail splays partition displacement across sub-resolution fractures (Faulds & Hinz 2015).
- **Mimic:** Broad strain highs lacking localized bridge gradients.
- **Differs:** Fold-isolated BVP vs S18 straight-line extrapolation. **Expected:** +0.003 to +0.008. **Cost:** Low-Med (20 min).

### 4. H43-5 — Radiometric K/Th Adularia-Illite × Silica Disequilibrium Alteration Fusion
- **Layers:** `geodawn_rad_u8.tif` (Th/K, U/Th, U/K, total count) + `geodawn_extensions_u8.tif` + `gdr_wellspring_in_footprint.csv` (quartz/chalcedony geothermometer disequilibrium plumes) + `gdr_volcanic_vents_in_footprint.csv`.
- **Signature:** K-metasomatic Th/K lows + U/Th redox cross-gradients coincident with 1.5 km Gaussian plumes of Tqtz–Tmeas >15°C, filtered to exclude closed-playa smectite basins.
- **Why missing:** Hydrothermal alteration halos extend 1–3 km beyond surface fault trace, marking blind geothermal conduits invisible to scarp mappers.
- **Mimic:** Lithologic contacts (shale vs carbonate Th/K contrast), playa smectite interiors.
- **Differs:** No prior lane uses fluid-chemistry vectors; H27-12 well/spring alone added ~0. **Expected:** +0.004 to +0.010. **Cost:** Medium (20 min, CSV ingest).

### 5. H43-6 — Multi-Scale Hessian Vesselness Retuning with Flight-Line Anisotropy Filter
- **Layers:** DEM + `lidar_scarp_features_u8` + training_features magnetic/gravity bands.
- **Signature:** Multi-scale Frangi vesselness (σ=150/400/1000 m) with explicit E–W flight-line suppression (90° azimuth power) and strike coherence gating.
- **Why missing:** S20V vesselness failed pooled -0.0125 but used only DEM|∇z|, ignoring LiDAR step asymmetry; retuning with LiDAR + magnetic concordance fixes upslope bias.
- **Mimic:** Road embankments, lava flow fronts.
- **Differs:** Adds flight-line deconfounder and LiDAR step gating vs S20V. **Expected:** +0.002 to +0.006. **Cost:** Low (15 min).

**Ranking rationale:** H43-2 is the only hypothesis that simultaneously (a) explains S20-NCHC's exact fold asymmetry, (b) requires zero new downloads, (c) is level-invariant (no scalar elevation level leakage), and (d) has a clear negative control (symmetric concavity without polarity kills terrace mimics). It is therefore the lane for S22.
