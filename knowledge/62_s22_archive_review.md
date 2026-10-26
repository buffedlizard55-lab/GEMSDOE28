# Session 22 — archive review, preflight, and decision (2026-10-26)

## Decision at a glance

- **Submission: NO.** No repository file is approved for DrivenData. No account, login, score page, upload route, or weekly slot was accessed or selected.
- **Research download: YES, optional, for the existing S21-PUHGB artifact only.** The [S21 result page](../docs/session21-result.html) links to `gems28-s21-puhgb-20261026-16bbf281ba9b-allfinite.tif` and labels it **RESEARCH ONLY / DO NOT SUBMIT**. Its negative holdout and strict any-raster uniqueness failure remain controlling; a local format pass is not a score or portal-acceptance pass. This review did not generate a TIFF.
- **Archive audit: PASS, local checks only.** `evidence/archive_audit_2026-10-26.json` reports **890 checks, 0 failures; all 46 of 46 registered download TIFFs were covered**. This says nothing about organizer authentication, geological correctness, score, or portal acceptance.
- **Next experiment: BLOCKED.** `evidence/session22_preflight.json` records `experiment_allowed: false`. No scientific experiment, holdout score, score estimate, slot choice, or upload occurred.

## Archive audit and site correction

The audit re-read the manifest and local TIFF bytes against the restored, hash-pinned sample template. It checked registered-file presence, SHA-256 and byte count, single-band float32 encoding, template CRS/shape/affine, [0,1] range, footprint/nodata behavior, candidate/name registration, ZIP membership and TIFF references, and alias deduplication. It also covered the six historical NaN/all-finite pairs. For the H40-1 and H41-1 all-finite variants, the arrays are finite everywhere and zero outside the footprint while a NaN nodata tag remains; the audit records that metadata/pixel distinction rather than treating it as a hidden pixel failure.

The result is a **local archive-integrity PASS**, not an independent authentication of owner-supplied files. The audit used no external requests. Nine shared evaluator/writer/validator/registry assets were separately verified against `registry/protocol_assets.json` (manifest SHA-256 `b4e23ba97cb72e89a78bcfda7d4b3076ea2076141ba1f648801083b79e500d79`); the exact pinned [GEMSDOE24 source archive](https://codeload.github.com/buffedlizard55-lab/GEMSDOE24/tar.gz/bddb55fca2c16e2b6f03c98d28751d8ff8cc7e5e) at commit `bddb55fca2c16e2b6f03c98d28751d8ff8cc7e5e` was used to restore those files. The pinned labels and sample template also verify by SHA-256.

The old S21 banner claiming that “12 of 44 TIFFs” were unregistered is superseded by this 46/46 audit and has been removed from the generated site. The homepage and cross-site page now put the local audit and the negative S21 disposition before historical result cards. Historical S19 remains available as a dated result with its own run card; it is not the current run.

## Current experiment preflight

The preflight is **BLOCKED** by all four of these missing prerequisites:

1. No explicit assigned method lane or assignment source.
2. No complete shared parallel-run registry.
3. No frozen current-best result evaluated under the same strict protocol.
4. No cached feature metadata/stack at `data/prepared/features.json` / `data/prepared/features.npy`.

The ranked proposal list below is not lane authority. A prior hypothesis, a local proposal, or historical seeds do not authorize a run. The shared-tool pins pass, but that does not clear the other blockers. `registry/current_session.json` records this as archive-review-only, with no lane. Restore or rebuild of the feature stack was not attempted.

## Nine-site score claims and the 0.2778 explanation

The site-family values below remain **owner-reported / unverified**. This repository has no submission-page receipt binding those values to the exact filenames and hashes. These are not presented as organizer-confirmed scores.

| Site | Highest cited owner-reported value |
|---|---:|
| GEMSDOE24 | 0.2477 |
| GEMSDOE25 | 0.2600 |
| GEMSDOE27 | 0.2449 |
| GEMSDOE28 | 0.2710 |
| GEMSDOE30 | 0.2600 |
| GEMSDOE31 | 0.2708 |
| GEMSDOE32 | **0.2778** |
| GEMSDOE33 | 0.2632 |
| GEMSDOE36 | 0.2750 |

The **0.2778** GEMSDOE32 claim is the highest in this nine-site family, not a verified association between an organizer score and a particular file. Local byte-forensics reproduced the reported construction: the 37,654-dot raster is the prior solo raster after removing 2,545 catalogue-near dots, with no dots added. That supports a plausible emission-efficiency explanation—less low-credit false-positive mass while retaining spaced-dot kernel coverage—but does **not** prove score causation, hidden-fault discovery, or the exact score-to-hash association. Do not copy or slightly re-prune that historical raster as a new submission.

Keep two separate dated public-leaderboard observations separate from the site claims: **0.3195** was the 2026-10-03 snapshot; **0.4413** was recorded on 2026-10-26. Neither is the GEMSDOE32 0.2778 claim, and an old observation should not be described as a current site score. The detailed comparison and byte-forensic explanation are also on the [nine-site scorecard](../docs/cross-site-review.html) and in [Session 21's result record](61_s21_result.md).

## Ranked untried research leads — none approved or currently runnable

This is a **planning rank**, based on the expected-gain ranges and cost notes already in the repository's proposal records. Those ranges are uncalibrated hypotheses, not measured HOLDOUT-DTI gains; the underlying proposal estimates are not necessarily comparable. No new utility model or score estimate was fitted. There is no honest scalar expected-utility calculation without calibrated probabilities and a same-protocol baseline. All five leads remain blocked by the current preflight; none is being called viable.

### 1. H43-2 — signed piedmont break-in-slope, scarp polarity, and subsurface concordance

- **Layers:** `dem_100m`, `lidar_scarp_desc_100m`, `isostatic_grav` / `grav_hg`, `tmi_hg` / `rtp_tilt`, and `depth_to_base_surf`.
- **Proposed physical signature:** signed slope-normal profile concavity at mountain-front-to-bajada inflections, asymmetric LiDAR upface/downface polarity, and subsurface nematic concordance.
- **Why it could find unmapped faults / what is new:** the proposal targets degraded Quaternary piedmont scarps and range-front step faults missed by aerial-photo compilation while retaining intrabasinal geophysical tracking. It is a direct asymmetric-polarity correction to the symmetric Hessian upslope shift diagnosed in H43-1, not another scalar elevation-level detector.
- **Non-fault mimic/control:** fluvial terrace risers and Lake Lahontan paleoshorelines; the proposed control is contour-parallel elevation constancy (`|dz/ds| ≈ 0`).
- **Proposal-only utility and cost:** `+0.010 to +0.025 HOLDOUT-DTI` over the proposal's B0 comparator, about 25 minutes of compute. This is an uncalibrated prior projection, not a measured gain; the required current comparable baseline is absent.
- **Source/data gate:** no new external layer is listed; the proposal uses local feature-stack layers. The cached stack is absent in this workspace, so the layers are not currently available for a compliant run.

### 2. H43-4 — transtensional stepover/releasing-bend Coulomb-dilation bridge

- **Layers:** geodetic strain-rate invariant, earthquake density, `sb_heatflow_100m`, visible-only fold fault endpoints, and gravity/magnetic gradients (`grav_hg` / `tmi_hg`).
- **Proposed physical signature:** solve anisotropic Coulomb-dilation fields strictly between visible-only fold fault tips, weighted by geodetic strain, microseismicity, and geophysical bridge alignment.
- **Why it could find unmapped faults / what is new:** it targets segmented accommodation zones and horsetail splays where displacement partitions across sub-resolution fractures. It is a fold-isolated physical boundary-value bridge, unlike Session 18's straight-line tip extrapolation.
- **Non-fault mimic/control:** broad regional strain highs; suppress them unless localized gravity/magnetic transfer gradients support a bridge. The proposal also bans the precomputed full-catalogue slip-tendency surface.
- **Proposal-only utility and cost:** `+0.003 to +0.008 HOLDOUT-DTI`, about 20 minutes. Uncalibrated proposal range, not a result.
- **Source/data gate:** the proposal cites Faulds & Hinz (2015), [OSTI open-access paper](https://www.osti.gov/servlets/purl/1724082), as rationale. This is a literature source, not a fresh availability check for data. The required local feature cache is missing; no run is authorized.

### 3. H33-3 — heat-flow residual × 2 m temperature-probe × lineament conjunction

- **Layers:** USGS ScienceBase heat-flow well residuals (measured minus de-convected background), GDR #1391 2 m temperature probes, candidate lineaments, and local `cond_surf` / `depth_to_base_surf` context.
- **Proposed physical signature:** emit only where a residual heat-flow well, a nearby 2 m temperature-anomaly cluster, and a candidate lineament jointly indicate an upflow corridor; protect existing dots there.
- **Why it could find unmapped faults / what is new:** the proposal targets concealed, alluvium-mantled structures whose upflow warms the shallow layer, a conductive-field residual channel with independent probe corroboration—not the fluid-chemistry/geothermometer and K/Th halo approach, and not `cond_surf × dilatation` alone.
- **Non-fault mimic/control:** uneven well coverage and groundwater discharge unrelated to faults; require the lineament-conjunction leg before emission.
- **Proposal-only utility and cost:** `[0, +0.0025] HOLDOUT-DTI`, medium cost; the original proposal notes a 130,154,244-byte heat-flow archive plus probe ingestion. Range and cost are estimates only.
- **Free source and actual availability evidence:** [USGS ScienceBase heat-flow item, DOI 10.5066/P9BZPVUC](https://www.sciencebase.gov/catalog/item/6297d2fad34ec53d276c5b28); [GDR #1391 2 m probe ZIP](https://gdr.openei.org/files/1391/2m_temperature_probe_INGENIOUS_regional_data.zip). The repository's historical `evidence/external_layer_inventory.json` records HTTP 200 and pin-matched bytes on **2026-10-03** for the 130,154,244-byte heat-flow ZIP and 1,080,530-byte probe ZIP. This is **not a fresh current availability check**. The raw ZIPs are not present in the current `data/` tree (a derived heat-flow CSV/JSON is tracked under `docs/data/`); the feature cache is absent. Therefore this is not currently viable.

### 4. H33-2 — five-depth magnetotelluric conductance alignment

- **Layers:** USGS 3-D ModEM conductance slices at 2–12 km, 12–20 km, 20–50 km, 50–90 km, and 90–200 km, plus `cond_surf` context.
- **Proposed physical signature:** shallow conductance-gradient orientation aligns with a candidate lineament for at least 3 km, while the anomaly is absent or rotated at 20–50 km—a proposed crustal-fluid corridor rather than a shallow-only or lithospheric-fabric signal.
- **Why it could find unmapped faults / what is new:** fault-hosted fluids and alteration may increase mid-crustal conductance along buried structures lacking a surface rupture. This is the five-depth column test, not the previously used `cond_surf × dilatation` interaction.
- **Non-fault mimic/control:** regional fabric and coarse MT cells; the proposal requires deep decoupling and cautions that structures under roughly 5 km may be smoothed.
- **Proposal-only utility and cost:** `[0, +0.0022] HOLDOUT-DTI`, medium-high cost for five reprojections, alignment, and label-free checks. Uncalibrated prior range.
- **Free official source and actual availability evidence:** [USGS ScienceBase conductance item, DOI 10.5066/P9TWT2LU](https://www.sciencebase.gov/catalog/item/62979746d34ec53d276c113b). `evidence/external_layer_inventory.json` records all five listed files as HTTP 200 / pin-matched on **2026-10-03** (about 4.13 MB each). That is a historical availability check only, not a fresh one; the raw five rasters are absent from the current workspace. The feature cache is also absent. Not currently viable.

### 5. S21-H2 — U-Net patch segmentation on 31-band patches

- **Layers:** 31-band spatial patches from the S21 feature stack; no newly verified external data layer is part of this proposal.
- **Proposed physical signature:** learned multi-scale spatial context and line continuity across patches, which a per-pixel HGB classifier cannot represent directly.
- **Why it could find unmapped faults / what is new:** a coherent, weak per-pixel trace could be detectable as a line in neighborhood context. This differs from the repository's tabular per-pixel HGB detector.
- **Non-fault mimic/control:** roads, channels, other linear geomorphology, and learned bias toward the existing catalogue's mapping style; spatial holdouts and leakage controls would be essential.
- **Proposal-only utility and cost:** qualitatively described as the highest-ceiling lead, but there is **no numerical gain projection** in the record. High cost; GPU is preferred. No GPU availability was verified in this review.
- **Data/source gate:** the feature metadata/stack required by the preflight is absent. A high ceiling is not a viability finding or lane assignment.

**Ordering note:** H43-2 and H43-4 rank highest on the explicit gain/cost claims in their proposal cards. H33-3 and H33-2 carry external-ingest cost and only old availability evidence. U-Net remains last in this planning order because its gain is unquantified, compute demand is high, and the local feature stack is absent—not because its scientific ceiling is claimed to be low. A fresh official-source check, complete inputs, explicit lane assignment, shared registry, frozen comparator, and preregistration are required before any one of these can be considered runnable.

## Provenance and exact records

- Archive audit: `evidence/archive_audit_2026-10-26.json` — PASS, 890 checks, 0 failures, 46/46 TIFFs.
- Blocked preflight: `evidence/session22_preflight.json` — four blockers above; `experiment_allowed: false`.
- Current review card: `evidence/session22_review_run_card.json` — archive review only; no experiment, score, TIFF, or slot decision.
- Current lane/session record: `registry/current_session.json` — archive-review-only, `lane: null`.
- Shared pins: `registry/protocol_assets.json`; restored shared tool files verify successfully.
- Score context and 0.2778 construction: `knowledge/61_s21_result.md`, `docs/cross-site-review.html`.

No manual geological inspection was used as a release gate. The negative S21 disposition follows recorded automated holdout and strict-uniqueness evidence; the archive PASS is not a scientific or submission gate. All future candidates must use the pinned shared evaluator/writer, not a private fork.
