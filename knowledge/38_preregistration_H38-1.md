# Preregistration — H38-1 cross-field Euler/gravity/low-relief addition test

**Status before execution: FROZEN PLAN — not yet run.** This document, the exact candidate-builder code, the LOSFO harness extension, the analyzer, tests, a local seed-collision audit, and a single-use seed reservation must be committed and pushed on the session branch before the runner starts. After the freeze, no threshold, candidate, seed, control, or gate may change. The holdout is an internal spatial proxy, not organizer-authenticated truth or a competition score.

## 1. Hypothesis and ranking decision

H38-1 is rank 1 in `knowledge/37_ranked_hypotheses_session14_2026-10-03.md`. It refines the unrun H37-2 cross-field/low-relief concept by adding a fixed, previously generated SI-0 Euler source-depth cluster layer; it is not a claim that Euler contacts are faults. H37-3 showed an informative signal (1.65× its matched-count random control) but failed the live-rate gate: its 5-seed mean was `+0.0005763895` DTI, only 13/20 cells were positive, and pooled credit per added dot was `0.0311573` versus the `0.0548` live break-even. H38-1 asks whether an independent gravity edge and subdued relief make that fixed Euler population more selective.

**Physical target:** a shallow, depth-coherent magnetic contact candidate with a nearby high gravity-gradient response, located in subdued local LiDAR relief. This is a candidate buried density/magnetic contact under a weak surface expression; none of these layers individually or jointly proves faulting, permeability, activity, or geothermal favorability.

**Why a catalogue omission is possible:** the USGS catalogue is a map of interpreted, geologically evidenced surface structures rather than a complete inventory of concealed contacts; the competition page explicitly states that public fault data are incomplete and that experts manually added absent structures. This test therefore measures recovery of held-out *mapped* systems far from the detector-visible catalogue as an upper-bound proxy. Passing does not establish recovery of truly unmapped organizer labels.

## 2. Exact, frozen candidate definition

**Input files and identity**

- Template: `data/sample_submission.tif` (finite footprint; EPSG:32611; 3,730 × 3,292; 100 m cells).
- Gravity: `data/training_features.tif`, 1-based band 18, description beginning `iso_grav_anom_hg`.
- Relief and validity: `data/lidar_scarp_features_u8.tif`, 1-based band 9 `relief` and band 12 `valid`; band 12 is a quantized valid-sample fraction, and `valid > 0` is the frozen usable-cell rule.
- Euler centroids: `evidence/h31_1_euler_clusters.csv`, previously produced from the magnetic TMI band by the recorded SI-0 Euler workflow.
- These local rasters have been restored from hash-pinned owner mirrors. Their hashes establish byte integrity, **not organizer provenance**. No new external data are required for this candidate.

**Candidate rule (no labels, holdout outcomes, or scores are inputs to this builder)**

1. Retain only Euler clusters satisfying `depth_mad_m <= 60 m`, `median_depth_m <= 400 m`, and `n_solutions >= 8`; round the recorded centroid to the nearest grid cell using Python `round`, matching H37-3.
2. Compute the gravity threshold as the linear-interpolated 80th percentile of all finite (`abs(value) < 1e30`) band-18 cells inside the finite template footprint. A centroid is near a gravity edge if its Euclidean distance to any cell at/above that threshold is `<= 2.0` pixels (`200 m`).
3. Compute the relief threshold as the linear-interpolated 50th percentile of band-9 values where the template footprint is true and band-12 `valid > 0`. A centroid passes relief if its band-9 value is `<=` that threshold.
4. The candidate CSV is the ordered subset of Euler rows passing all three tests. No additional interpolation, dilation of relief, direction fitting, candidate merging, model ranking, or post-holdout threshold search is allowed.
5. **Pre-run sufficiency floor:** at least 100 unique candidate centroids in the full grid. If the builder reports fewer than 100, abort before invoking the holdout and do not substitute another threshold. During the holdout, at least 200 total emitted candidate dots are required for promotion; lower support is an underpowered/non-promotable outcome.

The label-free sufficiency audit already completed before this protocol was written: the H37-3 depth rule selects 1,435 of the 6,309 input clusters; the fixed gravity/relief conjunction selects **140** (9.76%). The measured thresholds are gravity `1.460558295249939` and relief `44.0`; the audit reports 5,164,312 finite gravity cells, 3,894,460 LiDAR-valid cells, 569,931 joint-support raster cells, and 140 selected Euler centroids. These are data-support counts, not evidence of score improvement. Frozen artifacts are `evidence/h38_1_sufficiency_audit.json` and `evidence/h38_1_candidate_clusters.csv`; hashes are embedded there and repeated in the pre-run seed claim.

## 3. Spatially blocked holdout, single-use seeds, and controls

**Instrument:** `scripts/run_losfo_harness.py` using the existing leave-fault-system-out (LOSFO) protocol, unchanged defaults: four quadrant folds (`NW`, `NE_LidarGapHeavy`, `SW`, `SE`), 600 m label-erasure buffer, same 2.8-pixel detector/base, five seed assignments, and identical active evaluation cells per arm. A whole mapped fault system is assigned to a held-out fold; the detector never sees its labels or a 600 m buffer around it. This is the repository's appropriate current holdout for an ADD arm; the interleaved holdout contains no far-field truth for this purpose.

**One fresh local range:** seeds `265, 266, 267, 268, 269`, exactly 5 × 4 = 20 paired cells. `evidence/losfo_h37_3_licence.json` uses 260–264. Before reservation, `scripts/audit_holdout_seed_range.py` scans local `evidence/*.json` for these exact seed keys. The audit is explicitly limited to this checkout: it **cannot rule out undocumented owner use, other repositories, or unpublished runs**, so the range is described only as collision-free in the local record, never comprehensively available. Once the single-use claim enters `RUNNING`, all five seeds are spent even if the process errors; do not rerun or repair against the same decade.

For every cell, the exact arms are:

1. `base`: unchanged LOSFO detector ridge pool packed at `d=2.8`.
2. `H38-1`: `base` plus candidate clusters in the active fold that are off the visible catalogue and not in `base`, greedily accepted in the existing raster order only if at least 2.8 pixels from `base` and previously accepted candidate dots.
3. `matched random`: `base` plus the same number of dots, drawn from the same active, off-catalogue, not-in-base pool with the existing deterministic seed `seed * 4 + fold + 1000` and the same 2.8-pixel spacing. This control tests whether the cross-field Euler content is better than merely adding dots.

The frozen runner assertions require no licence/base or licence/catalogue overlap; a same-count random arm; 20 nonempty cells; exact seeds/folds; truth at least 8 pixels from detector-visible known labels; and input/code hashes consistent with the reservation claim. No weekly submission slot is used by this test.

## 4. Frozen measures and decision gates

Let `Δ_i = DTI(base ∪ H38-1)_i − DTI(base)_i` for each of the 20 cells, `R_i = DTI(base ∪ matched-random)_i − DTI(base)_i`, and `e = Σ_i(TP_w(H38-1)_i − TP_w(base)_i) / Σ_i(added H38-1 dots)_i`.

| Gate | Criterion | Threshold |
|---|---|---|
| **C1 — positive and spatially repeatable** | Mean `Δ_i`; positive cells; per-seed and per-fold means | Mean `> 0`, at least 15/20 cells positive, at least 4/5 seed means positive, and at least 3/4 fold means positive. |
| **C2 — live economic bar** | Pooled marginal weighted credit per added dot `e` | `e >= 0.0548`, the fixed incumbent-live-score break-even. Also report the current cell-wise far-field bar, but it cannot replace the live bar. |
| **C3 — content beyond extra dots** | Mean paired `Δ_i − R_i`; positive cells | Mean `> 0` and at least 15/20 cells positive. |
| **C4 — support and integrity** | Candidate count, added-dot count, panel shape, masks, exact file/code hashes | At least 100 preregistered global candidates, at least 200 total accepted additions, exactly 20 unique seed/fold cells, all assertions pass, and the raw record matches the frozen reservation. |
| **C5 — beats the current far-field add-arm best** | Mean H38-1 `Δ_i` versus the H37-3 far-field benchmark `+0.0005763894914862378` | H38-1 mean `Δ_i` must **exceed** `+0.0005763894914862378`. The H37-3 benchmark is from a different seed decade, so this is a conservative point-estimate promotion filter, not a paired or statistically independent superiority test. |

Report unconditionally: cell deltas; per-seed and per-fold means; a two-sided t-based 95% interval across 20 cells (descriptive because seed/fold cells are not fully independent); total/mean added dots; pooled credit per dot; H38-1 versus matched random; and both live/far-field bars. Do not suppress negative cells or round a failed threshold into a pass.

## 5. Pre-committed interpretation and no-slot rule

- **Only C1 ∧ C2 ∧ C3 ∧ C4 ∧ C5:** H38-1 becomes eligible for a separate, fresh-seed confirmation and then an exact-file audit. This result alone does not authorize a weekly slot.
- **C1/C3 pass but C2 or C5 fails:** record a cross-field signal if present, but it does not clear the live value hurdle or the current far-field best; no TIFF promotion, no upload, no slot, no threshold relaxation.
- **C1 or C3 fails:** the H38-1 conjunction is refuted as a candidate-emission rule; no rescue by a narrower subset or alternative thresholds on 265–269.
- **C4 fails or the run is interrupted:** record the failure and burn the range; no rerun on these seeds. Any future test requires a new preregistered range and a new claim.
- A positive internal holdout is not an organizer result. Do not describe mapped LOSFO test systems as confirmed hidden organizer faults or interpret DTI as a public leaderboard score.
- The explicit weekly-slot constraint remains: **no submission slot is spent unless an idea beats the current spatially blocked holdout best**. Even a C1–C5 pass only unlocks confirmation and file review; it does not itself beat an independently verified organizer best or prove live-score gain.

## 6. Existing official-source checks and limits

- DrivenData [problem page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) were manually checked; the former says the known fault set is incomplete and defines the weighted 300 m metric/submission format.
- USGS [Quaternary Faults](https://www.usgs.gov/programs/earthquake-hazards/faults) describes a mapped fault/fold compilation; omission from it is not proof a candidate is a fault.
- Euler-method basis: Reid et al. (1990), [DOI 10.1190/1.1442774](https://doi.org/10.1190/1.1442774). SI=0 encodes an idealized contact source geometry, not a categorical fault label or guaranteed physical depth.
- No new data download is required for H38-1. The local competition and 3DEP-derived layers come from hash-pinned owner mirrors; an official submission download/login is not assumed. The data and owner mirrors are not organizer-authenticated.
- Candidate builder `src/gems27/h38_1.py` and `scripts/build_h38_1_candidate_clusters.py` read no labels, run no holdout, and make no network request. `tests/test_h38_1.py` locks the quantile, validity, distance and Euler-threshold mechanics on synthetic inputs.

## 7. Freeze record

Before the first H38-1 model fit, the protocol-freeze Git commit will be recorded in the result and the following code/input paths will be hash-checked against that committed state. The post-freeze single-use claim and local seed audit are created only after the freeze commit, then committed together as a separate clean reservation commit before the run; they are not part of the code-hash inventory. The holdout wrapper records that reservation commit before starting and burns the range once the claim becomes `RUNNING`.

- This protocol: `knowledge/38_preregistration_H38-1.md`.
- Candidate definition/builder: `src/gems27/h38_1.py`, `scripts/build_h38_1_candidate_clusters.py`.
- LOSFO runner and transitive repository modules: `scripts/run_losfo_harness.py`, `src/gems27/losfo.py`, `src/gems27/oof_detector.py`, `src/gems27/metric.py`, `src/gems27/thinning.py`, `src/gems27/holdout.py`, `src/gems27/grid.py`, `src/gems27/paths.py`, and `src/gems27/packing.py`. The raw run and reservation also record Python, NumPy, SciPy, scikit-learn, and rasterio versions.
- Claim-preparation/audit/wrapper/analyzer and tests: `scripts/audit_holdout_seed_range.py`, `scripts/prepare_h38_1_seed_claim.py`, `scripts/run_h38_1_holdout.py`, `scripts/analyze_h38_1_holdout.py`, `tests/test_h38_1.py`, `tests/test_h38_1_holdout.py`, and `tests/test_seed_range_audit.py`.
- Post-freeze reservation records: `evidence/h38_1_holdout.started.json` (single-use claim) and `evidence/h38_1_seed_audit_pre_run.json` (local-only range scan). These are generated after protocol freeze and committed before the wrapper may start; the claim binds the freeze commit, exact input/code hashes and runtime versions.
- Input/candidate identity: `evidence/h38_1_sufficiency_audit.json`, `evidence/h38_1_candidate_clusters.csv`, and the four source hashes recorded in the sufficiency audit. The single-use claim additionally hashes the LOSFO template, label raster, raw feature/LiDAR rasters, prepared 32-band feature matrix and metadata, Euler-cluster CSV, candidate artifacts, and H37-3 benchmark; the run/analyzer refuse any mismatch.

This section is completed only after the freeze commit is created and pushed, the local seed audit is `PASS_LOCAL_SCAN`, and the exact-claim file reserves 265–269. The run does not start in this document's writing step.
