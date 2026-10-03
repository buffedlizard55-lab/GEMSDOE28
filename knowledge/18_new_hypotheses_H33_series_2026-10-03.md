# New candidate geological hypotheses — H33 series (Session 9, 2026-10-03)

**Purpose.** Per the standing prompt: 3–5 candidate geological hypotheses we have not tried yet,
each naming the specific layer(s), the physical signature targeted, why it should catch a fault
*missing* from the USGS/INGENIOUS catalogue, and how it differs from anything implemented across
GEMSDOE → GEMSDOE28. Ranked by expected DTI improvement vs implementation cost. Every external
source below was verified live on 2026-10-03 (links in `registry/sources.json`, audit in
`evidence/session9_external_verification.json`). The previous rank-1 untried candidate **H32-2 was
executed this session and FAILED its frozen gate** (`knowledge/17_h32_2_result.md`,
`evidence/h32_2_holdout.json`, seeds 190–199 consumed); the next arm uses seeds 200–209.

**Live context.** Public leaderboard read 2026-10-03: #1 DARD 0.3195, #2 0.3128, #3 0.3042,
#4 0.2998, #5 0.2941, …, #15 wbg1 0.2600 (owner anchor), #19 0.2449 (owner T-v2). To pass #1 we
must clear +0.0595 live DTI over `dotted-h19-5-d2-8` — incremental pruning arms (~+0.001 each) are
necessary but cannot get there alone. The H33 series deliberately targets *orthogonal information
channels* (stress kinematics, deep EM structure, heat-flow residuals, drainage neotectonics) and
the *Phase-2 expert-review rescoring rule*, which no submission in this family has exploited.

---

## Ranking table (expected catalogue-proxy ΔDTI is a planning prior, not a prediction)

| Rank | ID | Hypothesis | Expected ΔDTI | Cost | Data gate (verified 2026-10-03) |
|---:|---|---|---|---|---|
| 1 | **H33-1** | Kinematic reactivation favourability gate (slip/dilation tendency × geodetic strain) | +0.0005 to +0.0030 | Medium (~1 session; vector processing + 1 holdout) | USGS ScienceBase `6296974dd34ec53d276bb33d` (DOI 10.5066/P9YL58W6): `Shapefile_Full Study.zip` 34.25 MB listed; byte-verify queued on the runner bridge |
| 2 | **H33-3** | Heat-flow residual × 2 m probe thermal conjunction at candidate intersections | +0.0000 to +0.0025 | Medium (124 MB zip + probes already byte-verified locally) | ScienceBase `6297d2fad34ec53d276c5b28` (DOI 10.5066/P9BZPVUC): zip listed; GDR 2 m probes byte-verified (`evidence/external_layer_inventory.json`) |
| 3 | **H33-5** | Phase-2 discovery budget: capped corroboration-ensemble emission for expert review | Phase-1 cost ≤ −0.002 / Phase-2 +0.005 to +0.030 (speculative) | Low (uses existing layers; bounded-cost arithmetic) | None external; grounded in official rules text |
| 4 | **H33-2** | Multi-depth MT conductance alignment (2–200 km, 5 slices) | +0.0000 to +0.0022 | Medium-high (5 × 3.94 MB GeoTIFFs + reprojection) | ScienceBase `62979746d34ec53d276c113b` (DOI 10.5066/P9TWT2LU): all 5 `gb_conductance_*_tp.tif` listed; byte-verify queued |
| 5 | **H33-4** | Drainage-network neotectonics from 1 m DEMs (offsets, knickpoint alignments, beheaded streams) | +0.0005 to +0.0035 | High (GB-scale DEM tiles + hydrologic toolchain) | Competition `1m_DEM_links.csv` → USGS 3DEP/Theia tiles (free, official); tile fetch cost must be scoped first |

---

## H33-1 — Kinematic reactivation favourability gate

- **Layers.** (external) USGS slip-tendency/dilation-tendency shapefile for Great Basin Quaternary
  faults — Siler 2022, DOI [10.5066/P9YL58W6](https://doi.org/10.5066/P9YL58W6), ScienceBase item
  [6296974dd34ec53d276bb33d](https://www.sciencebase.gov/catalog/item/6296974dd34ec53d276bb33d)
  (attached files verified 2026-10-03: `Shapefile_Full Study.zip` 34.25 MB,
  `Shapefile_INGENIOUS area.zip` 27.35 MB); (local) `training_features.tif` bands `geod_2ndinv`,
  `geod_dilaterate`, `geod_shearrate`; (local) `qfaults_v2_in_footprint.json` for strike
  estimation; candidate dots from the frozen d=2.8 base (`data/dotted_h19_5_d2_8_nan.tif`).
- **Physical signature.** For each off-catalogue candidate dot: (i) estimate the local structural
  strike from the nearest OOF ridge orientation; (ii) interpolate the INGENIOUS slip tendency
  (Ts) and dilation tendency (Td) fields of the nearest catalogued, similarly-oriented segments;
  (iii) gate = high-Ts/Td rank × high local geodetic strain-second-invariant quantile. Prune
  unfavourably oriented low-strain dots; protect high-favourability dots.
- **Why it catches catalogue-missing faults.** The Siler (2022) abstract states the analysis
  exists precisely because "both conditions may make such faults likely to host
  as-yet-undiscovered hydrothermal processes" (verbatim from the DataCite record). The Qfaults
  compilation is geomorphically biased: favourably oriented faults in active E–W extension keep
  accumulating geodetic strain and are the class expert mappers add, even without crisp scarps;
  unfavourably oriented lineaments are likelier relict/non-fault edges (false-positive mass).
- **Difference from repo.** H28-4/SRCOH used shear-rate × seismicity density (holdout-refuted,
  0/4 folds); no arm has used stress-orientation kinematics (Ts/Td) or the Siler product. This is
  a *gate on emission*, not a feature injection (H31-1's failed mode).
- **Validation plan.** Seeds 200–209, frozen 4-fold spatial protocol; primary variant prunes the
  bottom decile of favourability among base dots; direction control prunes the top decile. Gate as
  in `knowledge/16_preregistration_H32-2.md`. **No slot before PASS.**
- **Obtainability.** Listed on the official ScienceBase item page with file sizes (2026-10-03);
  byte-level fetch queued via `fetch-gdr-external-layers.yml` runner bridge (this sandbox cannot
  reach sciencebase.gov; pattern matches the GDR #1391 byte-verification of 2026-10-03).

## H33-3 — Heat-flow residual × 2 m probe thermal conjunction

- **Layers.** (external) DeAngelo et al. 2022 heat-flow maps, DOI
  [10.5066/P9BZPVUC](https://doi.org/10.5066/P9BZPVUC), ScienceBase item
  [6297d2fad34ec53d276c5b28](https://www.sciencebase.gov/catalog/item/6297d2fad34ec53d276c5b28)
  (`heat_flow_maps_and_supporting_data_for_the_Great_Basin_USA.zip`, 124.12 MB, listed 2026-10-03).
  The point coverage carries a **residual** attribute — "the well's departure from estimated
  background heat flow conditions … useful in identifying hydrothermal or groundwater influence"
  (verbatim from the item summary); (local, already byte-verified) GDR #1391
  `2m_temperature_probe_INGENIOUS_regional_data.zip` (5,151 probes in footprint per
  `evidence/external_layer_inventory.json`); local `cond_surf`, `depth_to_base_surf`.
- **Physical signature.** Residual heat-flow outliers (wells whose measured flow exceeds the
  de-convected background trend) collocated within ~1 km of 2 m temperature anomaly clusters and
  of a candidate lineament ⇒ active upflow corridor. Emission: add a capped number of dots at
  three-way conjunctions that are not already dotted; protect existing dots at conjunctions.
- **Why it catches catalogue-missing faults.** The heat-flow product is explicitly built with
  convective influence *removed* — so its residuals mark exactly the hydrothermal upflow the
  compilation ignores; buried, alluvium-mantled faults with no scarp still vent heat and host the
  warm 2 m anomalies.
- **Difference from repo.** H32-4 (untried) targets well/spring geothermometers + radiometric
  K/Th halos — a *fluid-chemistry/alteration* channel; H33-3 is the *conductive-field residual*
  channel with independent 2 m probe confirmation; GEMSDOE26's dilcond (live-refuted 0.1223) used
  only `cond_surf` × dilatation with no heat-flow data at all.
- **Validation plan.** Seeds 200–209 if H33-1 is not yet run; else the next fresh decade. Proxy
  caveat: catalogue truth has weak far-field coverage, so conjunction *add* arms are screened by
  bounded-cost arithmetic (α=0.2 ⇒ cost of an added dot ≤ 0.2 kernel units) before any holdout.

## H33-5 — Phase-2 discovery budget (expert-review-optimised emission)

- **Layers.** No new data. Uses: d=2.8 base dots, Euler SI=0 depth clusters
  (`evidence/h31_1_euler_clusters.csv`), LiDAR scarp bands (`lidar_scarp_features_u8.tif`),
  catalogue distance fields; later H33-1/H33-3 corroboration channels as they land.
- **Physical signature / rule basis.** Official rules (verified 2026-10-03,
  [docs.nlr.gov/docs/fy26osti/96647.pdf](https://docs.nlr.gov/docs/fy26osti/96647.pdf)): Phase 2
  re-scores *the same submission* against an **expanded** label set built by an expert panel
  cross-referencing **every team's submission**; "predictions that helped experts identify
  previously-unmapped faults can score higher here than in the Initial Prize Round" (verbatim from
  the DrivenData problem page). Metric asymmetry: α=0.2 makes false positives cheap, β=0.8 makes
  missed truth expensive. Therefore a small, bounded budget (~1–2 % of emitted dots, ≤ ~600 px) of
  *maximally corroborated novel segments* — dots with ≥ 3 independent indicators (LiDAR scarp +
  shallow Euler cluster + strain/Ts favourability + thermal conjunction) and > 300 m from any
  catalogue pixel — costs at most ≈ 0.2 × 600 kernel units in Phase 1 (≤ ~0.002 DTI at current
  operating points) while creating asymmetric Phase-2 upside if experts confirm any of them.
- **Why it catches catalogue-missing faults.** By construction: emission is restricted to
  off-catalogue pixels with multi-method corroboration; these are precisely the candidates experts
  can verify in the GeoDAWN imagery.
- **Difference from repo.** Every prior arm optimises a Phase-1-style proxy; none has priced the
  Phase-2 rescoring rule. Contrarian by design: it accepts a bounded Phase-1 cost for Phase-2
  optionality — the only structural path to leapfrog the 0.30+ leaderboard cluster, whose members
  plausibly share the same H19-5-family surface.
- **Validation plan.** Not holdout-testable on the catalogue proxy for its Phase-2 claim (stated
  plainly). Phase-1 cost is bounded analytically; the corroboration conjunction quality itself is
  testable on seeds once channels exist. This is a *budget policy*, not a feature; it composes with
  whatever arm wins the screens.

## H33-2 — Multi-depth MT conductance alignment

- **Layers.** (external) Peacock & Bedrosian 2022, DOI
  [10.5066/P9TWT2LU](https://doi.org/10.5066/P9TWT2LU), ScienceBase item
  [62979746d34ec53d276c113b](https://www.sciencebase.gov/catalog/item/62979746d34ec53d276c113b):
  five GeoTIFFs, 3.94 MB each, all listed 2026-10-03 — `gb_conductance_surface_tp.tif` (2–12 km),
  `gb_conductance_middle_crust_tp.tif` (12–20 km), `gb_conductance_lower_crust_tp.tif` (20–50 km),
  `gb_conductance_upper_mantle_tp.tif` (50–90 km), `gb_conductance_mantle_tp.tif` (90–200 km) —
  from 3D ModEM inversion of >800 MT transfer functions; (local) `cond_surf`.
- **Physical signature.** Columnar coherence: conductance-gradient orientation in the shallow
  slice (2–12 km) aligned (|cos| > 0.8) with a candidate lineament over ≥ 3 km, with the anomaly
  *absent or rotated* in the 20–50 km slice ⇒ crustal-scale fluid corridor, not a lithospheric
  terrane boundary. Score dots by shallow-aligned/deep-decoupled rank.
- **Why it catches catalogue-missing faults.** Fault-hosted fluids + clay alteration raise
  mid-crustal conductance along buried structures that never break the surface; the catalogue is
  surface-rupture biased.
- **Difference from repo.** dilcond (live-refuted 0.1223) used only `cond_surf` × dilatation;
  the five-depth column has never entered any arm; H32-2 (magnetic spectral decay) failed this
  session — H33-2 is the EM analogue on a different physical field and depth axis.
- **Validation plan.** Byte-verify on the runner bridge first (availability section of
  `evidence/external_layer_inventory.json` after the next merge-triggered run), then a label-free
  alignment audit before any seed spend.

## H33-4 — Drainage-network neotectonics from 1 m DEMs

- **Layers.** Competition-provided `1m_DEM_links.csv` (owner mirror: `data/dem_links.json`,
  hash-pinned) → USGS 3DEP/Theia 1 m tiles (free, official); derived flow-direction/accumulation
  networks; local `lidar_scarp_features_u8.tif` for contrast.
- **Physical signature.** Linear drainage anomalies: right-angle channel offsets and deflections
  at lineament intersections, beheaded/abandoned channels, aligned knickpoint trains, wind gaps —
  computed from flow-routing on the 1 m DEM, scored along candidate lineaments. Channels integrate
  the most recent deformation and record faulting even where scarp relief has diffused below
  LiDAR-amplitude detection.
- **Why it catches catalogue-missing faults.** Alluvial-basin faults erase scarps fastest but
  keep offsetting active channels; drainage response is the youngest geomorphic recorder and is
  exactly what Quaternary-scarp compilations miss.
- **Difference from repo.** All prior LiDAR work used amplitude features (`lidar_step_max`,
  roughness, openness); no arm has touched flow-network topology.
- **Validation plan.** Scope the tile footprint overlap and download budget first (GB-scale);
  if > 20 GB in-footprint, down-rank and prefer H33-1/H33-3. High expected ceiling, highest cost.

---

## Verification ledger for this note (all accessed 2026-10-03)

| Claim | Source | Method |
|---|---|---|
| Slip/dilation tendency product, abstract quote, file list | DataCite API record for 10.5066/P9YL58W6 + ScienceBase item page | agent read (equivalent of human one-off read) |
| MT conductance product, 5 layer names + depth ranges, file sizes | DataCite API record for 10.5066/P9TWT2LU + ScienceBase item page | agent read |
| Heat-flow product, residual attribute quote, 124.12 MB zip | ScienceBase item page 6297d2fad34ec53d276c5b28 | agent read |
| Phase-2 rescoring rule quotes | DrivenData problem page 967 + official rules PDF 96647 | agent read, full |
| Reid et al. 1990 Euler formulation DOI | Crossref record for 10.1190/1.1442774 | agent read |
| Leaderboard anchors (#1 0.3195, #15 0.2600, #19 0.2449) | DrivenData public leaderboard | one-off agent read; rows do not identify the owner |
| Sandbox cannot reach sciencebase.gov / gdr.openei.org directly | curl exit 35 (TLS) observed this session | runner bridge is the byte-verify path |
