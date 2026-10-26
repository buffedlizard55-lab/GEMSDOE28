# S22C preregistration — multi-scale spatial-context lane (frozen 2026-10-26, before any S22 canary/DTI)

> **Merge rename (PR #63):** this run was labelled “S22” on its branch; three parallel same-prompt sessions (S22-SIGN, S22-AUDIT, S22-MOFR) merged first and own the plain `s22_*` filenames, `knowledge/62–63` S22 slots, and seeds **360–362** (S22-SIGN independently claimed the same seeds from the same base — disclosed seed collision; the shared deterministic splits make the withheld sets identical, 36,596 positives, which S22-AUDIT's own erratum on SIGN independently sums to). This context run is therefore **S22C** (`knowledge/64`/`65`, `evidence/s22c_*`, `scripts/*s22c*`). Preregistration content below is unchanged from its frozen pre-experiment form except file-path updates. Never pool numbers across S22-SIGN/S22-MOFR/S22C.

Session: `G28-S22C-20261026` (branch label `G28-S22-20261026`), branch `arena/f2afeb88-gemsdoe28`. Budget: 3 experiments / 2 hours
(parallel-run protocol §6). This file was written **before** any S22 feature canary, holdout DTI, or
candidate dot was computed. The only computations already run are data restore/hash verification,
the shared `prepare_data.py` cache build, and the Exp-1 byte forensic on already-scored files
(learning only, no dots emitted). Seeds **360, 361, 362** are claimed here (S21 reserved "360+";
a repository search on 2026-10-26 found no prior claim for 360–362; prior decades used include
210s–350s).

## 0. Lane assignment (protocol §1) — disclosed self-assignment

**Irregularity (preserved):** the session prompt says "Your lane is the single method paragraph
below" but contains no identifiable single method paragraph (the same defect Sessions 18–21
recorded). This session therefore **declares its own lane below, labelled a self-assignment**,
because the same prompt orders autonomous completion with no manual input. No external
exclusivity is claimed. If a synchronized registry later shows another live lane with the same
method, this run must be reclassified as a duplicate and stopped.

**S22C lane (single method):** *A gradient-boosted detector whose features are the shared 32-band
per-pixel stack **plus explicit multi-scale spatial context** (Gaussian-pyramid means and
gradient magnitudes at σ = 2 and 5 px of ten physical bands, and structure-tensor coherence of
the LiDAR scarp-step and total-magnetic-gradient fields), with ridge-restricted, catalogue-hygiene
dot emission. No coordinate features, no catalogue-derived features, no H19-5/champion dots or
surface anywhere in training, features, or emission pool.*

## 1. Five candidate hypotheses, ranked before implementation

Ranking rule: expected HOLDOUT-DTI improvement × probability this sandbox (2 CPU cores, 3 GB RAM)
can validate it honestly ÷ implementation cost. "Untried" = no implementation found in `src/`
on 2026-10-26 (grep for pyramid / structure-tensor / U-Net / torch / piercing / ComCat returned
only prose mentions). Local novelty only; no global-novelty claim. All live scores cited are
USER-REPORTED (owner prompt/sites), not organizer receipts.

| Rank | ID | Layers | Physical signature / transform | Why it could find a catalogue-missing fault | Difference from this repo | Non-fault mimic | Cost / data gate |
|---:|---|---|---|---|---|---|---|
| 1 (run now) | **S22-H1 Multi-scale spatial-context HGB (THIS LANE)** | Shared cached 32-band stack (`data/prepared/features.npy`, rebuilt + hash-verified this session) | Gaussian pyramid (σ=2, 5 px means + smoothed gradient magnitudes) of `tmi_hg, iso_grav_anom_hg, cond_surf, det_elev, det_elev_slope, lidar_step_max, lidar_ex_max, lidar_lappos_max, lidar_coh100, lidar_relief`; structure-tensor coherence of `lidar_step_max` and `tmi_hg`; detector = HistGradientBoosting; emission restricted to `ridge_nms` crests of its own surface | Per-pixel habitat is nearly identical on a faulted vs unfaulted lithologic contact (single-band AUCs 0.43–0.58, S21 canary). What separates a young/buried fault the Quaternary catalogue missed is **spatial pattern**: a step/gradient sustained coherently along strike for 100s of metres at a consistent range-front/piedmont position. Context features encode exactly that receptive field; S21's per-pixel PU-HGB (0.0839 vs 0.1062 baseline, HOLDOUT-DTI) had none of it and additionally used raw coordinates, which cannot generalise across quadrants. | No pyramid or structure-tensor feature exists in `src/`; the prepared stack is strictly per-pixel. Handcrafted single-surface lanes (vesselness, ASCP, radlin…) each used one operator hard-thresholded, never context *features* learned jointly with the habitat stack. | Roads, canals, paleo-shorelines, terrace risers, incised drainages — linear context without slip; lithologic contacts sustained along strike. | **Low–medium.** SciPy filters on cached rasters + sampled HGB fits; no new external data. Gateable this session. |
| 2 | **S22-H2 Tiny U-Net patch segmentation** (carried S20-H1) | Same 32-band stack as 2-D patches | Learned encoder–decoder spatial context, Tversky loss (α=0.2, β=0.8) matching the official metric, as in the organizers' reference solution (github.com/drivendataorg/gems-prize-reference-solution) | Highest ceiling: learns the multi-scale linear pattern end-to-end instead of hand-designed context; the 0.33–0.44 public-leaderboard cluster (verified 2026-10-26: #1 = 0.4437) is arithmetically unreachable by re-emission of any owner surface (S20V/S21 inversions) and is consistent with this model class. | No neural network exists in this repo (no torch dependency). | Any linear cultural/geomorphic feature; catalogue mapping-style imitation. | **High.** torch is obtainable from PyPI (allowlisted), and 100 m data are in hand, but an honest 12-cell hide-and-recover gate needs per-cell retraining — not credible on 2 cores / 3 GB inside budget. Ranked #1 for the *next* (GPU) programme, not run here; claiming otherwise would repeat the documented "data gate open ≠ validated" error. |
| 3 | **S22-H3 Signed piedmont break-in-slope concavity** (carried H43-2) | `det_elev` (+ `lidar_relief`) | Downslope profile-curvature sign change (convex range → concave piedmont) localised as a signed lineament | Range-front normal faults sit at the mountain/piedmont slope break even where the scarp itself is buried by alluvium and invisible to step detectors; S20-NCHC diagnosed its NE/SE failures as exactly this missing operator. | `det_local_relief`/`det_gradient` exist, but no signed profile-curvature-along-flow operator. | Alluvial-fan heads, terrace risers, shoreline benches. | **Low.** Cached data only. Ranked below H1 because every prior single-operator standalone surface in this repo (vesselness Δ −0.0125, ASCP Δ −0.0609, …) failed its gate; P(beat baseline alone) is low. Candidate *feature* for H1's successor. |
| 4 | **S22-H4 Displaced piercing markers** (carried S20-H4) | `rtp`/`tmi`, `iso_grav_anom` | Cross-corridor registration: several marker ridges offset by one consistent lateral shift; score the corridor | A concealed fault can offset pre-existing magnetic/density contacts without itself being a gradient ridge — every current potential-field arm scores the contact, not the displacement. | No patch-registration/displacement transform in `src/`. | Intrusive/branching contacts, survey seams. | **Medium–high.** Cached data, but false-match control is the whole problem; not gateable to standard this session. |
| 5 | **S22-H5 Seismicity point-alignment lineaments** (carried S20-H3) | USGS ComCat hypocentres (free, official) | Oriented pair-correlation / Hough accumulation over point hypocentres | Blind active planes can be microseismically illuminated with no scarp and no contact; current stack has only smoothed earthquake *density* (`deq/ieq`), no orientation statistic. | No point-pattern code in `src/`. | Volcanic/geothermal-induced swarms, location-error streaks. | **Data gate CLOSED here:** `earthquake.usgs.gov` is outside this sandbox's bash allowlist, so byte obtainability was **not verified**; per the session prompt it is therefore not proposed as viable this session. Named source for an unrestricted machine: https://earthquake.usgs.gov/fdsnws/event/1/ |

**Selection:** S22-H1 is the only candidate that is (a) unimplemented here, (b) aimed at the
specific diagnosed deficit of the best fresh detector (no receptive field), and (c) testable to
the full gate standard with hash-verified data already restored.

## 2. Frozen S22-H1 method (no post-hoc tuning)

- **Base features:** the shared prepared matrix (32 float32 bands, footprint order,
  `data/prepared/features.npy`, SHA-256 in `features.json`). Used via memmap; never rebuilt privately.
- **Context features (label-free; computed once on the full grid from the same bands):**
  for each of the 10 bands named in the table — NaN/invalid cells nearest-filled **for filtering
  only** (repo convention), values robust-standardised by footprint median/IQR computed on a fixed
  200k sample (RNG 7, unsupervised) — three maps: `gaussian σ=2`, `gaussian σ=5`,
  `|∇ gaussian σ=2|`. Plus structure-tensor coherence
  `((λ1−λ2)/(λ1+λ2+ε))²` (tensor smoothing σ=2, gradient σ=1) of standardised `lidar_step_max`
  and `tmi_hg`. **32 context features**, stored float16 footprint-ordered
  (`data/prepared/context_s22.npy`, git-ignored cache; builder script committed).
  Invalid (non-finite base-band) cells keep NaN context so HGB sees missingness honestly.
- **Arms (all inside Experiment 2, identical splits/samples/emission/hygiene):**
  `lane` = 32 base + 32 context; `control` = 32 base only; `dotted_b2` = S21's baseline
  construction (dotted d2.8 file dots ∩ fold ∩ ¬known ∩ d_visible>2; learning/reference only —
  its dots are never in the lane/control pools).
- **Training per cell:** train region = footprint outside the test quadrant (labels there are
  fully visible by construction of `holdout.make_split`); positives = visible catalogue pixels,
  subsample 25,000 (RNG seed·100+fold); negatives = non-catalogue pixels ≥3 px from any visible
  label in the train region, subsample 75,000. HGB: `max_iter=250, learning_rate=0.06,
  max_leaf_nodes=63, min_samples_leaf=40, l2_regularization=1.0` (S21 settings), `random_state=seed`.
  No coordinates. No catalogue geometry as a feature (S21 v2/v3a canary voids forbid it).
- **Emission per cell (identical for lane/control):** predict the test quadrant; surface →
  `oof_detector.ridge_nms(sigma=1.0)` on the fold crop; pool = ridge ∧ fold ∧ ¬known ∧
  (distance to *visible* catalogue > 2 px); greedy highest-score-first selection with 2.8 px
  minimum spacing to budget `round(37,654 × fold_footprint / total_footprint)`; **pre-registered
  fill rule:** if the spaced ridge pool is exhausted below budget, continue the same greedy pass
  over non-ridge allowed pixels (fill count recorded per cell).
- **Holdout:** shared `gems27.holdout` quadrant component-hide (20 % of 8-connected components per
  quadrant hidden as truth; visible faults masked pixel-exactly via `known`), evaluator
  `gems27.metric.dti_binary` (α=0.2, β=0.8, 300 m triangular kernel) on fold crops — the same
  "gems-segment-pooled-v1" semantics S21 used, on fresh seeds **360–362** × 4 folds = 12 cells.
  Pooled DTI from summed TPw/FPw/FNw; paired Δ vs baseline and vs control; 95 % CI by percentile
  bootstrap over the 12 cells (10,000 draws, RNG 20261026). 12 cells / 4 blocks ⇒ wide CI, reported as such.
- **Canary (protocol §4, before trusting any DTI):** AUC of **each of the 64 features alone**
  separating hidden-truth pixels from 20,000 sampled allowed negatives in cell (360, NW).
  Any AUC > 0.90 ⇒ leakage stop, no candidate, lane closed as void.
- **Uniqueness (protocol §1):** (i) pre-placement Spearman(final lane surface, each registry
  raster) on a fixed 200k footprint sample (RNG 22), |ρ| ≤ 0.90 required; (ii) final dots:
  fraction within 3 px of any single registry raster's dots ≤ 0.70. Registry = distinct dot-sets
  in local `docs/downloads/*-allfinite.tif` + byte-fetched GEMSDOE32 champion
  (SHA-256 `c55bafc4…6fa9`, fetched 2026-10-26) + GEMSDOE36 PINN (`e1589102…a8a`) + dotted/solo
  lineage files. Snapshot-bounded; no global-uniqueness claim.
- **Validator:** shared `submission.verify_geotiff` / `write_geotiff`; primary download is the
  **all-finite** variant (no NaN anywhere, values exactly {0,1}) because the owner previously hit
  the portal error "Predicted values must be in range [0, 1]" (cause undiagnosed; all-finite
  removes every local numeric cause without guaranteeing acceptance). NaN-outside twin + ZIP kept.
- **Promotion gate (all required, else verdict `negative`):** canary pass ∧ pooled HOLDOUT-DTI
  Δ(lane − dotted_b2) > 0 ∧ paired 95 % CI lower bound > 0 ∧ Δ(lane − control) > 0 ∧
  pre-placement + final-dot uniqueness pass ∧ validator hard checks pass on shipped bytes.
  `promote` still does **not** select a weekly slot (separate selector step, protocol §6).
- **Experiments:** (1) forensic re-analysis of scored files, incl. fetched champion/PINN bytes
  (education only, no dots); (2) context build + canary + 12-cell holdout gate (3 arms);
  (3) final full-footprint build (train on all visible labels, same recipe) + validator +
  uniqueness. No fourth experiment; no σ/budget/hyperparameter changes after seeing gate results.

## 3. What would falsify this lane

Pooled Δ(lane − dotted_b2) ≤ 0, or its CI covering 0, or Δ(lane − control) ≤ 0, each falsify
"explicit multi-scale context closes the gap between a fresh tabular detector and the H19-5
ensemble geography at champion budget" — recorded as a negative deliverable, TIF locked
**DO NOT SUBMIT**, and effort redirected to S22-H2 (U-Net) on GPU hardware.
