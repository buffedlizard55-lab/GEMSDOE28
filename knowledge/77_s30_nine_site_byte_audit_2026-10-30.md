# S30 · 2026-10-30 UTC — nine-site byte audit, why 0.2778 scored, uniqueness, and next steps

**Decision: OK TO DOWNLOAD AND SUBMIT: NO (all nine sites). No new TIF was generated. No weekly slot was used. No holdout experiment was run this session.**

Run card: [evidence/s30_run_card.json](../evidence/s30_run_card.json) · Byte audit: [evidence/nine_site_byte_audit_2026-10-30.json](../evidence/nine_site_byte_audit_2026-10-30.json) · Executive summary: [docs/s30-nine-site-executive-summary.html](../docs/s30-nine-site-executive-summary.html) · Irregularities: [registry/irregularities_s30.json](../registry/irregularities_s30.json)

Labels used below: **ORGANIZER-CONFIRMED** (copied from a submission-page receipt) · **OFFICIAL** (organizer text) · **MEASURED** (computed here from bytes) · **OWNER/USER-REPORTED** (copied from a prompt or owner page, no receipt) · **HYPOTHESIS** (reasoning, not tested).

## 1. What the official rules say (OFFICIAL)

- Single-band GeoTIFF, 100 m, EPSG:32611, float32, values 0–1, outside bounds null or NaN. Source: [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), "Submission format".
- Metric: distance-weighted Tversky index, α = 0.2 (false positives), β = 0.8 (false negatives), triangular kernel with R = 300 m (3 px). Same page, "Performance metric".
- Public and private test sets are chunks of the region. The public test set is "new faults" not in the USGS catalogue. Same page, "Competition structure" and "Datasets".
- Three submissions per week; a single selected submission is scored. [Official rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf), §3.2.
- The official rules contain no uniqueness or overlap rule. The 70% / 3 px rule in this repository is internal.

## 2. Verified facts from bytes (MEASURED)

Repositories fetched from github.com (codeload, main branch) and audited with `scripts/audit_nine_site_bytes.py`.

| Site | Best-claimed file (repo path) | Claimed score | Dots | Format | Max overlap within 3 px vs another site (both directions) |
|---|---|---|---|---|---|
| GEMSDOE24 | docs/downloads/gems24-h25-1-dotted-h19-5-d1-5-…-nan.tif | 0.2477 (reported) | 60,069 | PASS | 1.00 (GEMSDOE25) |
| GEMSDOE25 | docs/downloads/gems25-dotted-h19-5-d2-8-…-nan.tif | 0.2600 (reported) | 44,090 | PASS | 1.00 (GEMSDOE24, GEMSDOE30 — identical to GEMSDOE30) |
| GEMSDOE27 | docs/downloads/gems27-topo-gap-closure-…-nan.tif | 0.2449 (reported) | 61,328 | PASS | 1.00 (GEMSDOE24) |
| GEMSDOE28 | docs/downloads/gems28-h36-1-rung30-blind-r1-…-nan.tif | 0.2710 (reported) | 37,660 | PASS | 1.00 (GEMSDOE24) |
| GEMSDOE30 | docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-…tif | 0.2600 (reported) | 44,090 | PASS | 1.00 (GEMSDOE24, GEMSDOE25 — identical to GEMSDOE25) |
| GEMSDOE31 | docs/downloads/gemsdoe31-h27-4-solo-d28-…-nan.tif | 0.2708 (reported) | 40,199 | PASS | 1.00 (GEMSDOE24) |
| GEMSDOE32 | docs/downloads/gemsdoe32-h33-h33-2-b2-…-zeros.tif | 0.2778 (owner-reported) | 37,654 | PASS | 1.00 (GEMSDOE24, GEMSDOE36) |
| GEMSDOE33 | docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-…tif | 0.2632 (reported) | 41,865 | PASS | 1.00 (GEMSDOE32) |
| GEMSDOE36 | docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-…-zeros.tif | 0.2750 (reported) | 38,854 | PASS | 1.00 (GEMSDOE32) |

- **Format:** all nine are float32, single band, EPSG:32611, 3730×3292 at 100 m with the competition transform, and all in-footprint values are in {0, 1}. None has a value outside [0, 1] inside the footprint. NaN appears only outside the 5,167,373-px footprint, in the "nan" variants.
- **All 36 pairs** exceed the 70% / 3 px rule. Overlap ranges 0.87–1.00. Footprint correlation (phi) ranges 0.52–1.00.
- **Duplicate:** GEMSDOE25 and GEMSDOE30 have identical dot sets inside the footprint (44,090 each; phi = 1.00). Both are claimed at 0.2600.
- **Footprint coverage:** the nine files together place dots within 3 px of 19.6% of the footprint.

## 3. Why 0.2778 is the highest claim — HYPOTHESIS, with what is verified

Verified (MEASURED, GEMSDOE32 raster):

- 37,654 positive pixels; the nearest dot to the USGS catalogue is 223.6 m away (2.24 px). So "0 within 100 m and 0 within 200 m" is correct. 2,171 dots lie within 300 m of a catalogue fault.
- The file is 0/1 float32, and the zeros variant has 0 outside the footprint.

Owner-reported, not verified: the H33-2-B2 rule is "0.2708 base with every dot at distance ≤ 2 px of the catalogue deleted"; the owner audit gives "+0.004870 in 4/4 folds" on a live mirror; no organizer receipt is linked (the owner's page says "already submitted - do not resubmit").

Reasoning (HYPOTHESIS, not tested here):

1. **The public test GT is disjoint from the catalogue by design.** The official text says the scored faults are new faults not in the USGS database. So a dot on a catalogue fault cannot earn a true positive from that catalogue fault, but it still carries a false-positive cost of 0.2 × (1 − k). Deleting catalogue-flank dots therefore reallocates budget without losing true-positive weight. This is consistent with the claimed +0.007 gain (a small gain, as expected from a reallocation rather than a new signal).
2. **Tversky asymmetry.** With β = 0.8 and α = 0.2, one missed GT pixel costs four times one false positive. With a fixed dot budget, the score is set by how many hidden fault pixels fall within 300 m of a dot, not by how clean the dots are.
3. **Why the nine files converge.** They share one base pipeline (dotted ridge-type candidates at about 37–44k dots). Changing the budget or the catalogue flank rule moves only a few percent of the dots. A "new" file from this pipeline is a relabelling, which the overlap matrix confirms.
4. **Why we cannot yet beat 0.2778 with evidence.** The holdout in this repository is not calibrated to the leaderboard. The owner's own page gives the 0.2778 champion HOLDOUT-DTI 0.004515 on its evaluator, so holdout values cannot be read as leaderboard estimates.

## 4. Candidate hypotheses not yet tested (ranked; none run this session)

Ranked by expected information per unit cost. No expected score improvement is asserted.

| Rank | Hypothesis | Layers | Target signature | Why it could catch a catalogue-missing fault | Difference from implemented work | Non-fault mimic | Cost | Data status |
|---|---|---|---|---|---|---|---|---|
| H-S30-1 | Continuous catalogue-distance probability map | labels.tif (catalogue), a ridge-likelihood layer | p(x) = ridge likelihood × f(d_catalogue), f ramps from 0 at 0 px to 1 at ≥5 px; output continuous in [0,1] | Uses the official "new faults" premise directly; avoids binary dot placement | Binary dots are the family; this output is continuous and is not a pruning of dots | Catalogue-misalignment halo (the official page says existing fault data "may be misaligned" from the true surface fault) | Low (hours) | Available in repo (labels.tif, features) |
| H-S30-2 | Depth-to-conductive-base discontinuity (step edges) | Surface conductivity and depth to conductive base (training features) | Lateral step in depth-to-base; window size to be chosen in the preregistration | Basin margins are often fault-bounded | S26-TCB used `cond_surf` and was negative in holdout (see S28 record); this is a step-edge test, not a covariance test | Basin-margin lithology, playa edges | Medium | Available |
| H-S30-3 | Gravity-magnetic joint lineament coherence | RTP, TMI horizontal and vertical derivatives | Coherent lineament across two independent potential fields | Two-field agreement suppresses single-sensor noise | Not verified whether the family used joint field coherence; check before running | Igneous intrusion contacts | Medium | Available |
| H-S30-4 | Scarp (LiDAR) — already tested many times | 1 m DEM descriptors (repo) | Linear scarp | — | Already tested in multiple sessions; not recommended | — | — | Available |

Recommendation: test H-S30-1 first, on the repository's buffered hide-and-recover holdout, with per-feature leakage canaries. Its output is continuous, so it is a different class of file, not a relabelled dot set.

## 5. What is needed, and what is missing

- **A uniqueness decision from the user.** The 70% / 3 px rule is internal. Under the rule, every dot set from this family fails. A new file only passes if it places most of its dots outside the family's 3-px zone.
- **A calibration.** An estimate for the leaderboard needs organizer receipts for several submissions, or a holdout that matches the organizer's scoring. Neither exists here.
- **The file behind the portal error.** The message "Predicted values must be in range [0, 1]" is not matched to any file. No nine-site best file has an in-footprint value outside [0, 1]. The user should report the exact file and variant.
- **The sample file.** The restored `sample_submission.tif` equals `labels == 1` (60,988 pixels). The official sample is "total fault absence". Only its footprint is used.
- **Browser access.** The owner GitHub Pages sites (buffedlizard55-lab.github.io) are not reachable from this sandbox. The pages were read from repository copies.

## 6. Verification log (commands run; no hallucinated numbers)

- `pytest` on this branch: 737 passed, 7 skipped (run before this change).
- Data restore: `bash scripts/download_competition_data.sh` → hash check PASS for training features, labels, sample, and model group (`evidence/restore_audit.json`).
- Nine repositories fetched from codeload.github.com (HTTP 200 for each); TIFs read with rasterio.
- Audit output: `evidence/nine_site_byte_audit_2026-10-30.json` (9 files read, 36/36 pairs flagged).
- Identity check: `np.array_equal` on the footprint dot sets of GEMSDOE25 and GEMSDOE30 → True.
- Catalogue distance of GEMSDOE32 dots: minimum 2.236 px (223.6 m); 0 within 2 px.

## 7. Next steps (ordered)

1. User: confirm whether the internal 70% / 3 px rule applies. If it does, the family cannot yield a unique file, and the next file must be a new hypothesis (H-S30-1).
2. User: report the exact file behind the portal error.
3. Owner: confirm the GEMSDOE25 / GEMSDOE30 duplicate and the sample-file mirror.
4. Next session: run H-S30-1 on the buffered holdout with canaries. Do not spend a weekly slot unless its holdout result beats the same-evaluator family best with a paired CI above zero, and a receipt-based calibration exists.
