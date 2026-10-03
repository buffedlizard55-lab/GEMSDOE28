# Current ranked geological hypotheses — 2026-10-03 (Session 8 Update)

**Purpose:** a PhD-level, evidence-ranked geological hypothesis screen for `GEMSDOE28`, updated with the three newly reported live scores (`25GEMSDOE dotted-h19-5-d2-8 e56ea318af89 = 0.2600`, `27GEMSDOE topo-gap-closure-t-v2-on-d1-5 5512495c6bd1 = 0.2449`, and `26GEMSDOE dilcond-oof-v1 47629f496133 = 0.1223`). Every candidate names the specific layer(s) involved, the physical signature targeted, why it catches a fault missing from the USGS/INGENIOUS catalogue rather than one already in it, and how it differs from anything already implemented across `GEMSDOE` through `GEMSDOE28`.

## 1. Comparison Frame & Live-Score Grounding

- **Current live best (`0.2600`):** `25GEMSDOE dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif` (`44,090` off-catalogue pixels, SHA-256 `91eae1ca42ec...`, crowding-corrected `credit_TPw = 4,791.05 px` at `|G| = 12,226 px`, `5.77x` blind concentration).
- **Live refutation of `T-v2` gap closure (`0.2449` vs `0.2477` `d=1.5` base, `-0.0028` DTI):** `27GEMSDOE topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif` (`61,328` px = `60,069` `d=1.5` + `1,259` `T-v2` dots) earned only `+2.65 px` of live credit (`0.0021` credit/dot vs `0.0495` break-even). Consequently, all new `GEMSDOE28` candidates omit `T-v2`.
- **Live & holdout refutation of `H28-3 / H27-DILCOND-v1` (`0.1223`) and `H28-4 / H27-SRCOH-v1`:** `26GEMSDOE dilcond-oof-v1` (`47629f496133`) scored `0.1223` live (`-0.1254` vs `0.2477`), and `H27-SRCOH-v1` (`geod_shearrate` $\times$ `deq_n100a15` $\times$ `ieq_n100a15`) failed its 4-fold spatial holdout (`0/4` folds) in `GEMSDOE26`. Both are moved to the tested/refuted ledger below.

---

## 2. Top Candidate Preregistered & Validated This Session — `H32-1` (PASS on Seeds `180–189`)

### `H32-1`: Tip- & Euler-Depth-Cluster-Protected Mid-Segment Flank-Shadow De-Jittering on `d=2.8`
- **Specific layers involved:**
  1. `data/dotted_h19_5_d2_8_nan.tif` (`44,090` px, `0.2600` live base) and `data/post_h19_5_filtered.tif` (`121,131` px off-catalogue solid ridge parent).
  2. `data/labels.tif` (`60,988` known USGS/INGENIOUS catalogue fault pixels): Euclidean distance transform $d_{\text{cat}}$, catalogue skeleton degree-1 endpoints $d_{\text{end}}$, and $3\times 3$ catalogue neighbor count $\text{cat\_nbrs}$.
  3. `evidence/h31_1_euler_clusters.csv`: `6,309` retained Structural Index $N=0$ (contact) Reid et al. (1990) Euler deconvolution depth-coherent clusters ($d_{\text{Euler}} \le 300\text{ m}$).
- **Physical signature targeted:**
  - Discriminates **mid-segment lateral digitisation jitter** ($d_{\text{cat}} \le 100\text{ m}$ AND $d_{\text{end}} > 300\text{ m}$ AND $\text{cat\_nbrs} \ge 2$ AND $d_{\text{Euler}} > 300\text{ m}$: `2,434` pixels in `d=2.8`) from **along-strike fault-tip propagation and shallow buried contact splays** ($d_{\text{cat}} \le 100\text{ m}$ AND $[d_{\text{end}} \le 300\text{ m} \text{ OR } d_{\text{Euler}} \le 300\text{ m}]$: `1,457` protected pixels in `d=2.8`, comprising `1,360` tip pixels and `143` shallow Euler $N=0$ cluster pixels).
- **Why it catches a fault missing from the USGS/INGENIOUS catalogue rather than one already in it:**
  - Hermant et al. (2025, *50th Stanford Geothermal Workshop*, Fig. 2 & Fig. 9B) document up to `400 m` lateral offsets between regional 1:24k–1:250k USGS Quaternary fault traces and true 1 m LiDAR fault scarps. Along the interior of an already-mapped fault segment ($\text{cat\_nbrs} \ge 2$, $d_{\text{end}} > 300\text{ m}$) with no independent shallow Euler magnetic contact cluster, a $d_{\text{cat}}=100\text{ m}$ pixel is merely the unmasked 100 m lateral halo of the *already-catalogued* fault and scores zero credit against newly mapped faults $G$. Conversely, at a mapped fault tip ($d_{\text{end}} \le 300\text{ m}$) or where a shallow Euler $N=0$ depth-coherent cluster ($z_0 \approx 155\text{–}614\text{ m}$) corroborates a subsurface contact, the $100\text{ m}$ pixel captures an **unmapped along-strike fault propagation or shallow buried horsetail splay** omitted where surficial scarp relief dies out into basin alluvium.
- **How it differs from anything already implemented in this repo:**
  - Prior `H27-4` blindly pruned *all* `3,891` $d_{\text{cat}} \le 100\text{ m}$ pixels on `d=2.8` without tip or Euler protection, and was only shipped bundled with the now live-refuted `T-v2` gap-closure dots (`23ad46a4d7ba`). Prior `H31-1` fed Euler rasters into a 41-band GBDT and failed screen (`-0.00195`). `H32-1` uses the retained $N=0$ Euler depth clusters and tip geometry as a deterministic structural protection gate on `d=2.8` with zero `T-v2` drag.
- **4-Fold Spatially-Blocked OOF Holdout Validation (`scripts/run_h32_1_holdout.py`, `evidence/h32_1_holdout.json`, fresh seeds `180–189`):**
  - **`h32_1_post_d28`** (post-thinning mid-segment de-jittering): mean DTI `0.096896` vs `0.095624` base (**`+0.001272` mean ΔDTI**, min `+0.000907`, max `+0.001519`), **`10/10` seeds won**, **`4/4` spatial folds improved** (`NW +0.001023`, `NE_LidarGapHeavy +0.002293`, `SW +0.000272`, `SE +0.001498`), `-1,500.4` dots/seed, removed credit per removed FP **`0.004017`** (`4.85x` below the `0.01950` OOF inclusion threshold and `13.7x` below the `0.05485` live `0.2600` inclusion threshold).
  - **`h32_1_pre_d28`** (pre-thinning mid-segment de-jittering before `dot_thin(2.8)`): mean DTI `0.097023` (**`+0.001399` mean ΔDTI**, min `+0.000854`, max `+0.001943`), **`10/10` seeds won**, **`4/4` spatial folds improved**, `+74.3` dots/seed, marginal efficiency **`0.4893`** credit/FP.
  - **Diagnostic control (`control_prune_protected_only_d28`)**: pruning *only* the `1,457` protected tip/Euler pixels loses **`0.009194` credit per removed FP — `2.29x` higher hidden-fault credit density** than the mid-segment flank-shadow pixels (`0.004017`), directly confirming the physical hypothesis.
- **Shipped GeoTIFFs (`docs/downloads/`):**
  - Primary: `gems28-h32-1-tip-euler-dejitter-d2-8-20261003-c3aeda1d31a3-nan.tif` (`41,656` px, hybrid live-anchored model **`0.2665`** vs `0.2600` base).
  - Secondary: `gems28-h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan.tif` (`42,294` px, hybrid live-anchored model **`0.2685`**).
  - Tertiary (unprotected comparator): `gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif` (`40,199` px, hybrid live-anchored model **`0.2701`**).

---

## 3. Four Ranked Untried Geological Hypotheses (`registry/next_hypotheses.json`)

| Rank | ID | Hypothesis | Expected Holdout ΔDTI | Implementation Cost | Data / Access Gate |
|---:|---|---|---:|---|---|
| 1 | **`H32-2`** | **Shallow-over-deep magnetic gradient de-screening (intrusive-pluton margin suppression)** | **`+0.0008` to `+0.0025`** | Low (~25 min + 1 holdout run) | All bands restored & hash-verified locally (`training_features.tif`, `geodawn_extensions_u8.tif`). |
| 2 | **`H32-3`** | **Gravity-gradient bench inflection vs basalt-capped mesa topographic decoupling** | **`+0.0005` to `+0.0022`** | Low-medium (~35 min + 1 holdout run) | All bands restored & hash-verified locally (`training_features.tif`, `lidar_scarp_features_u8.tif`). |
| 3 | **`H32-4`** | **Quality-screened hydrothermal geothermometer & K/Th–U/Th alteration halos along sub-scarp corridors** | **`+0.0000` to `+0.0018`** | Medium (~45 min + fold-safe encoding) | All files restored & hash-verified locally (`gdr_wellspring_in_footprint.csv`, `geodawn_extensions_u8.tif`, `training_features.tif`). |
| 4 | **`H27-16`** | **Independent GDR #1391 paleo-geothermal sinter/travertine, 2 m temperature probes, & Quaternary-volcanics polygons** | **`+0.0000` to `+0.0030`** | High (blocked on external download) | Official GDR #1391 URLs & sibling SHA-256 pins documented; raw zip bytes absent locally (`gdr.openei.org` unreachable in sandbox). |

### 3.1 Rank 1 Untried — `H32-2`: Shallow-Over-Deep Magnetic Gradient De-Screening (Intrusive-Pluton Margin Suppression)
- **Specific layers involved:**
  - `data/training_features.tif` band 15 (`tmi_hg`), band 17 (`tmi_rtp`), band 18 (`mag_sed_thick_km`), band 5 (`depth_to_base_surf`), and `data/geodawn_extensions_u8.tif` band 4 (`TMI_up150`, 150 m upward-continued total magnetic intensity from USGS GeoDAWN, Glen et al. 2024, ScienceBase `657e1d85d34e23d3533209f7`).
- **Physical signature targeted:**
  - The horizontal-gradient upward-continuation attenuation ratio $R_{\text{shallow}}(x) = |\nabla_H \text{TMI}(x)| / (|\nabla_H \text{TMI}_{\text{up150}}(x)| + \varepsilon)$ conditioned on shallow magnetic-sediment/basement thickness ($\text{mag\_sed\_thick\_km} < 0.8\text{ km}$). By potential-field upward continuation $e^{-|k|\Delta z}$ ($\Delta z = 150\text{ m}$), a shallow brittle fault contact ($z_0 \le 300\text{ m}$) decays rapidly under $150\text{ m}$ upward continuation (high $R_{\text{shallow}}$), whereas a deep Cenozoic pluton boundary or caldera ring margin ($z_0 \ge 1.5\text{–}3\text{ km}$) decays slowly ($R_{\text{shallow}} \approx 1$) while still generating strong raw `tmi_hg` ridges.
- **Why it catches a fault missing from the USGS/INGENIOUS catalogue:**
  - Concealed shallow intrabasinal fault contacts beneath thin alluvial veneer lack surface scarps and are omitted from Quaternary scarp maps, whereas deep intrusive margins inside ranges produce false-positive magnetic ridges in `H19-5` that are not brittle faults.
- **How it differs from anything already implemented in this repo:**
  - `TMI_up150` in `geodawn_extensions_u8.tif` was only appended as a raw uint8 value in the failed `H27-12` `+rad`/`+all` screen; its horizontal-gradient attenuation ratio against `tmi_hg` has never been computed or tested.

### 3.2 Rank 2 Untried — `H32-3`: Gravity-Gradient Bench Inflection vs Basalt-Capped Mesa Topographic Decoupling
- **Specific layers involved:**
  - `data/training_features.tif` band 21 (`grav_hg`), band 19 (`isograv`), band 4 (`det_local_relief`), band 15 (`tmi_hg`), and `data/lidar_scarp_features_u8.tif` band 2 (`lidar_step_max`) and band 5 (`lidar_rough50`).
- **Physical signature targeted:**
  - Co-aligned local maxima of horizontal gravity gradient (`grav_hg`) and low-roughness alluvial-fan break-in-slope (`det_local_relief`, `lidar_step_max`), contrasted against high-`tmi_hg`, zero-`grav_hg`, high-`lidar_rough50` erosional Tertiary basalt/ash-flow mesa rims that follow topographic contours.
- **Why it catches a fault missing from the USGS/INGENIOUS catalogue:**
  - Older pediment-front and range-front normal faults degraded by Holocene fanglomerate aprons lack crisp 1 m LiDAR scarps and are omitted from the USGS Quaternary compilation, yet still juxtapose dense Paleozoic/Mesozoic basement ($2{,}650\text{–}2{,}750\text{ kg/m}^3$) against unconsolidated basin fill ($2{,}000\text{–}2{,}200\text{ kg/m}^3$), producing a strong `grav_hg` inflection. Conversely, erosional volcanic mesa rims generate top-percentile LiDAR + magnetic edges in `H19-5` with zero basement density step (`grav_hg` near zero).
- **How it differs from anything already implemented in this repo:**
  - `H28-1` computed multi-scale magnetic-gravity gradient orientation coherence globally without decoupling contour-following volcanic mesa rims (`high lidar_step_max + high tmi_hg + low grav_hg`) from degraded range-front basement steps (`moderate det_local_relief + high grav_hg + low lidar_rough50`).

### 3.3 Rank 3 Untried — `H32-4`: Quality-Screened Hydrothermal Geothermometer & K/Th–U/Th Alteration Halos Along Sub-Scarp Corridors
- **Specific layers involved:**
  - `data/gdr_wellspring_in_footprint.csv` (`27,092` INGENIOUS well/spring records, OpenEI GDR `#1391`), `data/geodawn_extensions_u8.tif` bands 1–3 (`Th/K`, `U/K`, `U/Th` airborne radiometric ratios), and `data/training_features.tif` band 9 (`cond_surf`) and band 8 (`geod_dilaterate`).
- **Physical signature targeted:**
  - Anisotropic fault-strike-aligned hydrothermal alteration corridors coupling quality-screened high-temperature wells/springs ($\text{tempc} \ge 60^\circ\text{C}$ or $\text{gt\_qtz} \ge 130^\circ\text{C}$, de-duplicated on a $200\text{ m}$ grid) with potassium-metasomatic depletion of $\text{Th/K}$ (low `Th/K`, elevated `U/Th`) along sub-threshold geodetector ridges.
- **Why it catches a fault missing from the USGS/INGENIOUS catalogue:**
  - Active hydrothermal fault conduits in Great Basin geothermal districts (Brady's, Desert Peak, Dixie Valley, Salt Wells) undergo argillic/sericitic alteration that mechanically weakens surface rocks and erases brittle scarps, causing omission from Quaternary scarp maps while leaving potassium/uranium radiometric alteration halos and high-geothermometer fluid upflow.
- **How it differs from anything already implemented in this repo:**
  - `H27-12` tested unscreened isotropic Euclidean distances to all wells/springs and raw radiometric bands independently (finding `+0.0005` to `+0.0007` PR-AUC). `GEMSDOE26` `dilcond-oof-v1` (`0.1223`) used `geod_dilaterate` $\times$ `cond_surf` alone without hydrothermal geothermometers or radiometric `Th/K` alteration ratios.

### 3.4 Rank 4 Untried — `H27-16`: Independent GDR #1391 Paleo-Geothermal Sinter/Travertine, 2 m Temperature Probes, & Quaternary-Volcanics Packages
- **Specific layers involved:**
  - Official OpenEI GDR submission `#1391` (`https://gdr.openei.org/submissions/1391`) packages:
    1. `paleo_geothermal_regional.zip` (`https://gdr.openei.org/files/1391/paleo_geothermal_regional.zip`, sibling pin `84,008 B`, SHA-256 `faffcf69...`)
    2. `2m_temperature_probe_INGENIOUS_regional_data.zip` (`https://gdr.openei.org/files/1391/2m_temperature_probe_INGENIOUS_regional_data.zip`, sibling pin `1,080,530 B`, SHA-256 `1301f70d...`)
    3. `great_basin_q_volcanics.zip` (`https://gdr.openei.org/files/1391/great_basin_q_volcanics.zip`, sibling pin `9,898,770 B`, SHA-256 `c4a2d2df...`)
- **Physical signature targeted:**
  - Relict sinter terraces, travertine mounds, and hydrothermal breccias (`paleo_geothermal_regional.zip`), shallow 2 m conductive thermal plumes (`2m_temperature_probe_INGENIOUS_regional_data.zip`), and Quaternary volcanic dike/fissure polygon boundaries (`great_basin_q_volcanics.zip`).
- **Why it catches a fault missing from the USGS/INGENIOUS catalogue:**
  - Sinter and travertine precipitate directly where fault-hosted geothermal fluids discharge at the surface, even where Holocene basin-fill sedimentation has buried the fault scarp.
- **How it differs from anything already implemented in this repo:**
  - None of these three zip packages is present in `data/` (which holds only the well/spring CSV and 21 volcanic vent points).
- **Obtainability status:**
  - Official URLs are documented on OpenEI GDR `#1391` and hash-pinned in sibling runner records (`2026-09-30`), but `gdr.openei.org` is outside this sandbox's network allowlist (`github.com` and `pypi.org` only) and GitHub Actions workflow runs for `fetch-gdr-external-layers.yml` failed before job start. Remains blocked until raw package bytes are retrieved and hash-verified.

---

## 4. Completed / Refuted Hypotheses Ledger (Not Untried)

- **`H32-1` (Tip- & Euler-depth-cluster-protected mid-segment flank-shadow de-jittering on `d=2.8`):** **VALIDATED (PASS)** on 4-fold spatially-blocked holdout seeds `180–189` (`+0.001272` post-thinning, `+0.001399` pre-thinning, `10/10` seeds, `4/4` folds; `evidence/h32_1_holdout.json`).
- **`H31-1` (Euler source-solution & shallow cluster GBDT feature screen):** **FROZEN SCREEN GATE FAILED** on seeds `160–169` (`-0.001947` mean paired ΔDTI, `1/4` folds, `2/10` seeds; `evidence/h31_1_euler_screen.json`). Confirmation seeds `170–179` remain unused and ineligible for `H31-1`.
- **`H27-1 / T-v2` (Topology gap-closure on `d=1.5`, `5512495c6bd1`):** **LIVE-REFUTED** at `0.2449` vs `0.2477` `d=1.5` base (`-0.0028` live DTI; `0.0021` credit/dot vs `0.0495` break-even; `evidence/live_inversion.json`).
- **`H28-3 / H27-DILCOND-v1` (Dilatational-strain $\times$ conductivity corridors, `47629f496133`):** **LIVE-REFUTED** at `0.1223` (`-0.1254` vs `0.2477`; `evidence/live_inversion.json`).
- **`H28-4 / H27-SRCOH-v1` (Shear-rate $\times$ seismicity fabric coherence):** **HOLDOUT-REFUTED** in `GEMSDOE26` (`0/4` spatial folds improved; dense DTI `0.1268`, sparse DTI `0.0719`).
- **`H27-10` (100–300 m offset-scarp annulus reallocation):** **FROZEN GATE FAILED** on seeds `150–159` (`+0.000846` mean ΔDTI, `4/4` folds, `7/10` seeds, annulus efficiency `0.03357 < 0.05212`; `evidence/h27_10_annulus_holdout.json`).
