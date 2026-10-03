# Current untried geological hypotheses — 2026-10-03

**Purpose:** a 3–5 item, evidence-ranked screen for follow-on research, reviewed against the current checkout's prior experiments and code. Expected gains below are uncertain planning priors for a paired catalogue-internal spatial holdout only; they are not observations, leaderboard predictions, or promises. A public leaderboard row is not a link between an owner and a local file. No candidate earns a weekly submission slot without a frozen holdout win, independent confirmation, and an exact-file audit.

## Comparison frame

- **Best comparable prior result:** H28-1 multiscale potential-field edge features + T-v2 graph-gap additions + H27-4 r1 flank-shadow pruning, seeds 140–149; +0.00294884 mean paired DTI versus the prior 32-feature OOF base, positive in 3/4 folds and 9/10 seeds (`evidence/h28_1_edge_holdout.json`). It is catalogue-component hide-and-recover evidence, not organizer-created truth or competition performance.
- **Best same-run control for H31-1:** H28-1's six edge features + the unchanged T-v2/H27-4 stack, refit with the Euler candidate on each fresh draw. Raw DTI means from different seed ranges are not compared.
- **Known completed/failed work not to relabel as untried:** H27-10 annulus reallocation failed its frozen gate on seeds 150–159; H27-12 found radiometric ratios and simple thermal-distance layers near-null on the catalogue proxy; graph connectivity ranking, overlapping step-over geometry, oriented line-integral features, simple well/spring distance and several emission-shape tests are already measured or refuted. Details stay in `knowledge/02_hypotheses_ranked.md`, `knowledge/07_untried_hypotheses.md` (historical Session-5 screen), and `evidence/`.
- **Novelty boundary:** these ideas are genuinely untried in this checkout in the exact transforms described, but the complete sibling-repository methods are unavailable; no global novelty claim is made.

## Ranked screen

| Rank | Hypothesis | Planning prior ΔDTI / cost | Current data/access gate |
|---:|---|---|---|
| 1 | **H31-1: SI-aware magnetic Euler source solutions and shallow clusters aligned to candidate lineaments** | **+0.000 to +0.006**, very uncertain; medium-high CPU/analysis cost | Label-free Euler solutions and the three preregistered feature arrays have been built from the hash-pinned owner-mirror TMI raster. No H31 model fit or holdout has occurred. See `knowledge/12_preregistration_H31-1_euler.md` and `evidence/h31_1_euler_feature_audit.json`. |
| 2 | **H28-3: dilatational-strain × conductivity corridors** | **+0.000 to +0.003**, very uncertain; low-medium cost | Existing owner-mirror raster bands are available locally; official band units/processing and independent bytes are not confirmed. Exact joint transform is untested. |
| 3 | **H28-4: anisotropic seismicity-fabric lineaments** | **+0.000 to +0.002**, very uncertain; low-medium cost | Existing owner-mirror event-density bands are available; smoothing/completeness metadata need primary-source review before feature design. |
| 4 | **H28-5: quality-filtered hydrothermal chemistry gradients** | **+0.000 to +0.003**, very uncertain; medium-high cost | GDR #1391 listing is official, but the owner-mirrored well/spring CSV is not restored in this checkout and raw-package downloadability/schema/licence have not been independently verified here. |
| 5 | **H27-16: paleo-geothermal features + shallow temperature probes + Quaternary-volcanics polygons** | **+0.000 to +0.006**, very uncertain; high access/processing cost | Official GDR #1391 listing and sibling pin reports exist; raw package bytes are absent here. A listing/pin does not prove the files are presently downloadable, have the expected schema/coverage, or have the assumed licence. Do not use until bytes, checksum, schema, coverage and licence are verified. |

## 1. H31-1 — depth-labeled Euler magnetic-source solutions and shallow clusters

**Physical signature.** Solve Euler's homogeneous-field equations in 10 × 10 windows of the owner-mirror `tmi` band; record accepted source x/y, positive-down depth, fitted offset, singular values, residual and depth uncertainty; cluster source solutions; retain SI-0 clusters only when their *Euler-derived source coordinates* align within 200 m of an independently extracted TMI horizontal-gradient ridge. Gradient maxima are an alignment layer, never source locations. Append only fixed cluster-support, shallow-support and normalized depth-context features to the existing H28-1 detector. No Euler point is directly emitted as a submission dot.

**Why it could find faults missing from the catalogue.** A buried susceptibility boundary or fault-related alteration zone can produce a magnetic source edge even where a Quaternary surface trace is absent or covered. Depth-labeled clusters could prioritize coherent, shallow, lineament-aligned contacts that a per-pixel classifier or surface-only scarp map misses. This remains a candidate-generation mechanism: intrusive/lithologic contacts, volcanic edges, remanent magnetization, interpolation artifacts and survey seams are equally plausible explanations.

**How it differs from prior work.** H28-1 added scale-space magnetic/gravity edge-coherence covariates; prior models include magnetic derivatives and use non-maximum suppression on prediction scores. None in this checkout solves and clusters Euler source positions/depths. The only use of gradient ridges here is the post-solution alignment test.

**Structural-index and geometry caveats.** Primary SI=0 approximates a contact of effectively infinite depth extent; a real finite, dipping, segmented fault may require SI=1 or 2. Wrong SI biases depth. Euler does not provide dip. The local SI=1 and SI=2 sensitivity pass on the current mirror produced substantially different cluster centroids from SI=0 (only 41.0% and 30.2% of SI-0 cluster centers respectively had a counterpart within 600 m; median nearest distances 855 m and 1,154 m). These are unlabeled method-sensitivity diagnostics, not evidence that any index is geologically correct. The 100 m grid is not independent 100 m detail: the official GeoDAWN item describes magnetic survey line spacing of 200 m in Area 1 and 400 m in Area 2, with variable terrain clearance.

**Data/access.** The nine local inputs are SHA-256-pinned owner mirrors, not organizer-authenticated. TMI band 14 tags do not include units; no explicit magnetic-source-depth band was found. Four deterministic patches gave positive `tmi_vg` versus FFT-downward-derivative correlations but inconsistent 1.38–1.90 scales; therefore all Euler derivatives are derived from one `tmi` field. The official USGS ScienceBase release page verifies the survey metadata and product listing, not byte identity with this mirror. See `evidence/euler_input_audit.json` and `evidence/h31_1_euler_feature_audit.json`.

**Status.** Protocol revision 2 is committed at `524bf27` before any classifier fit or holdout; it clarifies that source-field units are unverified without changing analysis parameters or gates. Earlier working-copy artifacts cite `d700cfe`/`9eef66b`, but those objects are absent from this checkout's Git history. The initial label-free feature audit matches earlier protocol bytes, but Git cannot prove those bytes were committed before that solve; chronology and the history irregularity are disclosed in `evidence/h31_1_prereg_history_audit.json`. The current label-free build under revision 2 and the current implementation passes all pre-fit sufficiency checks: 80.265% vertical-derivative coverage, 118,089 accepted SI-0 solutions, and 6,309 retained aligned/depth-coherent SI-0 clusters. Median SI-0 depth is 296 m (P10 155 m, P90 614 m), a model output rather than verified geological depth; physical magnetic units remain unauthenticated. No OOF classifier fit, holdout score, promotion decision or candidate TIFF exists. The formal local seed audit passes with 34 evidence JSON files scanned, prior local seeds 100–159, and reserved 160–169/170–179 unused. External/sibling seed use cannot be ruled out. The screen/confirmation gates are seeds 160–169 and (only if earned) 170–179.

## 2. H28-3 — joint dilatational-strain and conductivity corridors

**Layers.** Owner-mirror `geod_2ndinv`, `geod_shearrate`, `geod_dilaterate`, `cond_surf`, with `depth_to_base_surf` only as a fixed geological context layer; inspect embedded names and official processing metadata before use.

**Physical signature.** Short, spatially coincident dilation/strain-gradient and conductive-alteration corridors, tested as a joint geometry rather than independent high-value pixel thresholds.

**Why it could find a missing fault.** A buried, active or fluid-bearing strand can be weakly expressed in surface topography but may produce strain concentration, fluid/clay conductivity, or a co-located subsurface boundary. It might reveal a blind trace omitted from the Quaternary catalogue.

**Difference from prior work.** The existing detectors consume these channels as scalar raster features. No exact in-repo test measures their joint spatial intersection as candidate corridors. This is different from the already tested simple thermal-distance, radiometric and scalar geophysics arms, and from graph-based endpoint links.

**Risks and data gate.** Basin conductivity, clay caps, broad regional strain and source-depth mismatch can create false corridors. The local bands remain owner mirrors; exact units, source processing, spatial coverage and licensing must be checked against primary/official metadata. Planning prior +0.000 to +0.003; low-medium cost. Do not proceed without preregistering a deterministic corridor-width/continuity transform and a same-run H28-1 control.

## 3. H28-4 — anisotropic seismicity-fabric lineaments

**Layers.** Owner-mirror `deq_n100a15`, `ieq_n100a15` and `geod_shearrate`; verify descriptions, input event catalogue, smoothing radius and time window before using.

**Physical signature.** Directional persistence and local orientation of earthquake-density ridges, measured across fixed scales and optionally compared with local shear-rate orientation.

**Why it could find a missing fault.** A linear seismicity fabric may identify a blind active strand without a fresh surface scarp. A mapped surface catalogue can omit faults whose deformation is mostly subsurface.

**Difference from prior work.** The supplied scalar density channels have appeared in the matrix/univariate audit; the directional fabric/anisotropy transform itself has not been tested. It is not the already refuted oriented LiDAR/geophysics line-integral transform: the signal and proposed physical target are seismicity, not terrain or potential-field edges.

**Risks and data gate.** Aseismic faults, completeness gradients, unrelated swarms, smoothing artifacts and sparse events may dominate. Official metadata for the exact competition channels has not been verified in this session; local bytes are owner mirrors. Planning prior +0.000 to +0.002; low-medium cost. Verify the official event/source metadata before specifying scales, then preregister on unused seeds.

## 4. H28-5 — quality-screened hydrothermal chemistry gradients

**Layers.** GDR/INGENIOUS well/spring observations: measured temperature and vetted quartz/chalcedony/cation geothermometers, quality/class fields, and station coordinates. Do not substitute a generic isotropic distance-to-spring raster. Optional 2 m probe data only after the separate H27-16 access gate.

**Physical signature.** De-duplicated, quality-filtered temperature/geothermometer contrasts along short spatial gradients and narrow candidate corridors, with fixed uncertainty and minimum-sample rules.

**Why it could find a missing fault.** Fault permeability can focus hydrothermal upflow and create geochemical/temperature gradients even where the surface trace is missing. Spatial contrast and alignment could be more informative than point proximity alone.

**Difference from prior work.** H27-12 tested simple well/spring distance features and found near-null proxy benefit. The quality-filtered measurement-gradient transform is different, but remains untested; the null result is a warning against generous priors, not a validation.

**Risks and data gate.** Duplicate stations, uncertain geothermometers, sparse/bias sampling, groundwater displacement and non-fault heat sources can mislead. The GDR #1391 listing is official, but a listing alone does not prove the raw binary is downloadable or verify its current schema/licence. The CSV is not in this checkout; acquire and hash-verify actual bytes and metadata before feature code. Planning prior +0.000 to +0.003; medium-high cost.

## 5. H27-16 — independent GDR paleo-geothermal, temperature-probe and volcanics layers

**Layers.** Official GDR #1391 package listings describe paleo-geothermal sinter/tufa/travertine and altered-bedrock vectors, shallow 2 m temperature probes, and Great Basin Quaternary-volcanics polygons.

**Physical signature.** Independent surface alteration, shallow thermal anomalies, and young volcanic-unit/vent patterns that could share structural controls with faults.

**Why it could find a missing fault.** A fault-focused fluid pathway or young structure may leave a thermal/chemical/volcanic signal even where the Quaternary fault catalogue has no mapped trace.

**Difference from prior work.** H27-12 measured simple well/spring distance and radiometric feature groups (near-null proxy gains). This hypothesis concerns three distinct raw source packages and their polygon/measurement geometry, not reusing those distance features. It has not been tested here because the bytes are absent.

**Risks and data gate.** Volcanic contacts can be unrelated to faults; fluids can migrate; probes/sample coverage can be uneven. Official listing/DOI and a sibling-runner hash report are not equivalent to local successful download, checksum match, expected schema, spatial coverage or licence verification. Obtain the actual packages, checksum the exact bytes and review their metadata/licence before preregistering separate layer arms. Planning prior +0.000 to +0.006; high cost and access uncertainty.

## Stop rule and sources

Every hypothesis needs: official/primary source review, exact byte/schema/grid/licence gate, deterministic label-free transform, a preregistered spatial hide-and-recover test against the same-run current-best control, fresh seed ranges, and a predeclared pass/fail gate. Only a screen pass earns a fresh confirmation. A proxy pass is not competition performance. No candidate receives a weekly slot before reproducible holdout superiority, confirmation and exact-file format/range/mask/label-overlap audit.

Manual review sources:

- [USGS ScienceBase GeoDAWN release, Glen & Earney (2024), DOI 10.5066/P93LGLVQ](https://www.sciencebase.gov/catalog/item/657e1d85d34e23d3533209f7) — official survey/release metadata; not authentication of the owner mirror.
- [Reid et al. (1990), Euler deconvolution, DOI 10.1190/1.1442774](https://doi.org/10.1190/1.1442774) — primary method paper; [author-hosted PDF](https://www.reid-geophys.co.uk/wp-content/uploads/2017/11/Reid-et-al-1990.pdf).
- [GDR #1391 listing](https://gdr.openei.org/submissions/1391) — official resource listing; actual package access/schema/coverage/licence still require direct verification.
- [USGS 3DEP catalog](https://data.usgs.gov/datacatalog/data/USGS:77ae0551-c61e-4979-aedd-d797abdcde0e) — official terrain-data context; this does not authenticate the owner-derived LiDAR descriptors.
