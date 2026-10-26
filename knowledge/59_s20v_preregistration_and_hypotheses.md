# S20V preregistration — Hessian-tubularity lane (frozen 2026-10-26, before any S20 holdout DTI)

> **Merge rename (PR #53):** this run was labelled "S20" on its branch; a concurrent Session 20-H43 run merged first and owns the `s20_*` filenames and seeds 340–344 (interleaved protocol). This vesselness run is therefore **S20V** (`knowledge/59`/`60`, `evidence/s20v_*`). Seed overlap 340–342 across sessions is disclosed; protocols differ (LOSFO here) and numbers must never be pooled. Preregistration content below is unchanged from its frozen pre-experiment form except file-path updates.


Session: `G28-S20-20261026`, branch `arena/6ee1b262-gemsdoe28`. Budget: 3 experiments / 2 hours
(parallel-run protocol §6). This file was written **before** any S20 feature canary, holdout DTI, or
candidate dot was computed. Seeds **340, 341, 342** are claimed here for the S20 LOSFO gate; a
repository-wide search on 2026-10-26 found no prior seed claim for 340–342 (prior LOSFO decades:
210–214, 265–269, 290–294, 300–304, 310–314).

## 0. Lane assignment (protocol §1) — disclosed self-assignment

**Irregularity (preserved, not hidden):** the session prompt says "Your lane is the single method
paragraph below" but contains no identifiable single method paragraph. Sessions 18–19 correctly
refused to invent an external assignment. This session instead **declares its own lane below and
labels it a self-assignment**, because the same prompt also orders autonomous completion with no
manual input. No external exclusivity is claimed. If a coordinating registry later shows another
live lane with the same method, this run must be reclassified as a duplicate and stopped.

**S20 lane (single method):** *Multi-scale Hessian tubularity (Frangi vesselness) of the LiDAR
scarp-step field as a standalone, label-free fault-centreline surface, emitted as catalogue-hygiene
dots.* Everything outside this paragraph (forensic re-analysis of old files for education, site/README
maintenance) is not an experiment in this lane and produces no candidate dots.

## 1. Five candidate hypotheses, ranked before implementation

Ranking rule: expected DTI improvement × probability the available holdout can validate it ÷ cost.
"Untried" means no implementation was found in `src/gems27/` on 2026-10-26 (grep for
hessian/frangi/vessel/phase-congruency/radon/torch/U-Net/drainage returned no module). Local-novelty
only; no global-novelty claim.

| Rank (next programme) | ID | Layers | Physical signature / transform | Why it could find a catalogue-missing fault | Difference from this repo | Non-fault mimic | Cost / data gate |
|---:|---|---|---|---|---|---|---|
| 1 | **S20-H1 U-Net patch segmentation** | Cached 32-band stack (`data/prepared/features.npy`, restored & hash-verified this session) + optionally 1 m DEM derivatives | Learned multi-scale spatial context (encoder–decoder CNN, Tversky loss α=0.2 β=0.8 as in the official reference solution) | Tabular HGB sees one pixel; a CNN integrates scarp/lineament context over 100 m–km, the exact gap every handcrafted band in this repo approximates piecemeal. Blind/buried traces with weak per-pixel but coherent linear expression become detectable. | No neural network exists in this repo (no torch dependency; detector is HistGradientBoosting). The organizers' reference solution is a U-Net, so this is parity with the likely leaderboard method class, not copying any owner submission. | Any linear cultural/geomorphic feature the network associates with faults (roads, channels); also catalogue-style bias (learns to imitate mapping conventions). | **High.** Needs torch (PyPI, allowlisted) + patch training; CPU-only pilot feasible but slow on 2 cores, GPU preferred. Data gate OPEN for 100 m stack; 1 m DEM tiles are listed in restored `data/dem_links.json` (USGS 3DEP, free official) but bulk bytes were **not** downloaded/verified this session. **Not executable to gate standard inside this session's remaining budget — ranked first for the next session, not run here.** |
| 2 (run now) | **S20-H2 Hessian tubularity (THIS LANE)** | `lidar_scarp_features_u8.tif` band `step_max` (+ `valid` mask), restored hash-pinned | Gaussian Hessian eigenstructure at σ∈{1,2,3} px; Frangi vesselness rewards \|λ₂\|≫\|λ₁\| (tubular ridge) and suppresses blobs/plates | A young or partly buried scarp can have a diffuse gradient-magnitude response (what `potential_edges`/`structural_step` measure) yet a coherent second-derivative centreline. The Quaternary catalogue preferentially misses exactly such subdued piedmont scarps. | Repo has gradient magnitudes, directional line integrals (`newinfo`), upward continuation/tilt (`depthslice`), Euler deconvolution — **no Hessian eigenvalue transform anywhere in `src/`**. Used here as a standalone surface, not an HGB feature, so it can pass the ≤0.90/≤70% uniqueness gates that feature-addition arms cannot. | Roads/levees, paleoshorelines, incised drainages, bedding ridges — all tubular step anomalies with no fault slip. | **Low–medium.** Pure SciPy on cached raster; no new external data. Executable and LOSFO-gateable this session. |
| 3 | **S20-H3 Seismicity point-alignment lineaments** | USGS ComCat point catalogue (free official API) — *not* the smoothed `deq/ieq` density bands already in the stack | Anisotropic point-pattern alignment (oriented pair-correlation / Hough accumulation over hypocentres) | Actively creeping/slipping blind faults can microseismically illuminate a plane with no surface scarp and no potential-field contact — invisible to every current layer except as a blurred density. | `deq_n100a15`/`ieq_n100a15` enter the HGB only as smooth densities; no point-pattern or orientation statistic exists in `src/`. | Volcanic swarms, geothermal production-induced seismicity, location-error streaks. | **Medium.** Requires ComCat bytes + magnitude/depth filtering decisions; API host is outside this sandbox's bash allowlist, so obtainability must be re-checked (research fetch or owner machine) before calling it viable. **Not run here.** |
| 4 | **S20-H4 Displaced piercing markers** | Cached `rtp`/`tmi` + `iso_grav_anom` | Cross-corridor registration: multiple marker ridges offset by one consistent lateral shift; score the corridor | A concealed fault can offset pre-existing magnetic/density contacts without itself being a gradient ridge — every current potential-field arm scores the contact, not the displacement. | No patch-registration/displacement transform in `src/` (Session-19 slate rank 1, still unimplemented). | Intrusive/branching lithologic contacts, survey seams. | **Medium–high.** Cached data only, but the estimator needs careful false-match control. **Not run here.** |
| 5 | **S20-H5 Drainage χ / knickpoint neotectonics** | 1 m DEM tiles (USGS 3DEP via restored `dem_links.json`) | Channel steepness/χ disequilibrium + knickpoint alignment across catchments | Actively uplifting fault blocks perturb drainage long before a mappable scarp forms; signal lives in network topology, not in any 100 m pixel value. | No flow-routing code in `src/` (H33-4 proposal, never implemented). 100 m `det_elev` is too coarse; needs the 1 m tiles. | Lithologic knickpoints, base-level fall waves, capture events. | **High.** Tile volume + hydrologic conditioning; bytes not yet restored/verified. **Not run here.** |

**Selection:** S20-H2 is the only candidate that is (a) genuinely unimplemented here, (b) testable to
the full gate standard with hash-verified data already restored, and (c) inside the 3-experiment /
2-hour budget. S20-H1 has higher expected DTI but cannot be honestly gated this session; claiming
otherwise would repeat the "data gate OPEN ≠ data in hand" error this repo has documented before.

## 2. Frozen S20-H2 method (no post-hoc tuning)

- **Input field:** `step_max` band of `data/lidar_scarp_features_u8.tif` (SHA-256 pinned in
  `registry/data_manifest.json`), float32; valid = footprint ∧ (lidar `valid` band > 0) ∧ finite.
  Invalid cells are nearest-filled **for filtering only** (repo convention) and zeroed in the output.
- **Surface:** `src/gems27/vesselness.py::frangi_vesselness`, σ ∈ {1.0, 2.0, 3.0} px, β=0.5,
  c = half the max Frobenius norm over valid cells per scale (standard Frangi default), bright-ridge
  convention (λ₂ < 0 required), max over scales. Output float32 in [0,1], exactly 0 outside valid.
  No labels, catalogue, or scores are read by the transform.
- **Emission recipe (gate cells and final build identical except catalogue scope):**
  ridge = `oof_detector.ridge_nms(V, valid, sigma=1.0)`; pool = ridge ∧ eligible ∧ (distance to
  *visible* catalogue > 2 px); rank pool by V descending (stable); take top-K with
  K = round(0.0245 × eligible-cell count) in gate cells (the repo `PRE_THIN_FRAC`), or budget-search
  K in the final build to land within ±1% of **N = 37,654** dots (champion budget, for comparability
  only — no champion dots are read); dots = `thinning.dot_thin(pool_topK, 2.8)`; re-assert
  dots ∧ catalogue = ∅ and min catalogue distance > 2 px.
- **Control (same splits, same hygiene):** LOSFO OOF HGB detector
  (`oof_detector.fit_predict_oof_probabilities` on buffer-masked labels, exactly as
  `scripts/run_losfo_harness.py`), ridge + same top-K + `dot_thin(2.8)` + same >2 px visible-catalogue
  filter. If lane/control dot counts in a cell differ, drop the lowest-scored dots of the larger arm
  to exact matched-N before scoring (pre-registered; counts recorded per cell).
- **Holdout:** LOSFO (`src/gems27/losfo.py`): fault systems = 8-connected components of catalogue
  dilated 3 px; quadrant-blocked system assignment; 6 px (600 m) buffer erased from training labels;
  truth = held-out systems; visible faults masked pixel-exactly in scoring
  (`metric.dti_binary`, α=0.2, β=0.8, 300 m triangular kernel — the shared evaluator, eval_set v2
  semantics). Seeds **340, 341, 342** × 4 folds = 12 cells. Pooled DTI from summed TPw/FPw/FNw;
  paired ΔDTI per cell; 95% CI by percentile bootstrap over cells (10,000 draws, RNG 20261026) —
  with only 12 cells / 4 geographic blocks this CI is wide and will be reported as such.
- **Canary (protocol §4, before trusting any DTI):** AUC of V alone (and of raw `step_max` alone)
  separating hidden-truth pixels from active background, pooled over seed-340 cells. AUC > 0.90 ⇒
  leakage stop, no candidate. (V is label-free by construction; the canary is still run and recorded.)
- **Uniqueness (protocol §1):** (i) pre-placement: Spearman(V, each registry raster) on a fixed
  400k footprint sample (RNG 20) must satisfy |ρ| ≤ 0.90 for every registry raster; (ii) final dots:
  fraction within 3 px of any single registry raster's dots ≤ 0.70. Registry = all
  `docs/downloads/*-nan.tif` in this repo **plus** byte-verified forensic copies of the GEMSDOE32
  champion (`c55bafc4…`) and GEMSDOE36 (`e1589102…`) rasters. Registry completeness is bounded to this
  snapshot and stated as such; no global-uniqueness claim.
- **Validator:** shared `submission.verify_geotiff` on both variants; primary download is the
  **all-finite** variant (zeros outside footprint, no NaN anywhere, values exactly {0,1}) because the
  owner previously hit the portal error "Predicted values must be in range [0, 1]" — the all-finite
  file removes every local numeric cause (NaN comparisons included) without claiming to have diagnosed
  the portal or to guarantee acceptance. NaN-outside variant retained as the sample-conformant record.
- **Promotion gate (all required, else verdict `negative`):** canary pass ∧ pre-placement pass ∧
  pooled LOSFO ΔDTI (lane − control) > 0 ∧ paired 95% CI lower bound > 0 ∧ final-dot uniqueness pass ∧
  validator hard checks pass on the exact shipped bytes. A `promote` verdict still does **not** select
  a weekly slot (separate selector step, protocol §6).
- **Experiments:** (1) forensic/inversion re-analysis (education; no dots), (2) canary + LOSFO gate,
  (3) candidate build + validator + uniqueness. No fourth experiment; no threshold/σ/budget changes
  after seeing gate results.

## 3. What would falsify this lane

Vesselness credit/dot at or below the matched-N content-blind level, or pooled ΔDTI ≤ 0, or CI
covering 0, each falsify "Hessian tubularity adds far-field fault information beyond the tabular
detector at this budget" — recorded as a negative deliverable with the TIF locked DO NOT SUBMIT.
