# S28 — 2026-10-29 checkout review and validation repair

**Branch:** `arena/ff60f579-gemsdoe28`. **Decision: NEGATIVE · no new TIFF · OK TO SUBMIT: NO.** No model experiment, leakage canary, competition request, upload or slot selection occurred. The full normalized standing requirements and historical prompt archive in README were read before implementation. They remain the starting point; this note is not a fabricated verbatim copy of the chat.

## Executive outcome

The requested new high-scoring unique TIFF could **not** be produced within the supplied protocol. The prompt references a single assigned method paragraph but does not contain one. The configured shared registry is incomplete, the frozen same-protocol best is absent, and the old experiment clock has expired. The existing registry feasibility audit also rejects the declared dot budget under the literal overlap rule. We did not invent an exclusive lane, reset authorization, choose a different dot budget, copy/rename an old TIFF, or call a projection a score.

Instead, this session removed reproducible software/data obstacles and repaired two reporting/validation defects:

1. Restored all pinned input groups using the existing GitHub restoration script. Verified hashes, raster grids, band descriptions and the prepared matrix with the existing verifier. Restored all nine shared-template assets without modifying/forking their evaluator or writer. Built the existing cached feature stack with `prepare_data.py`; its source-missingness contract passes. Large rasters and arrays remain ignored. These are **owner mirrors, not organizer-authenticated downloads**.
2. **Fixed a real audit coverage gap:** sibling-manifest S25 research files were previously accepted into the registered set using only their TIFF SHA-256. The archive audit now independently opens those TIFFs and ZIPs: exact CRS/shape/transform, one float32 band, finite footprint probabilities in [0,1], no infinities, explicit outside-footprint convention, no visible-catalogue predictions, exact ZIP member/bytes, note length and non-approval. A matching hash alone is not a format pass. Added synthetic regression cases including NaN, Inf, out-of-range values, shifted grids, wrong CRS, wrong shape/band count, catalogue overlap, malformed manifests, missing/corrupt files, ZIP differences, path traversal and escaping symlinks.
3. **Fixed stale current reporting:** generic `data/current_run_card.json` aliases now publish this checkout's dated decision after the standard offline build. Immutable dated cards still retain the original session bytes. The Pages deployment check now verifies current and historical cards against separate expected hashes; previously it assumed the historical S23 card had to equal every future current card. Prior S27 banners are explicitly historical.
4. Added a prominent current executive summary and dedicated `docs/current-review.html`, including the inherited nine-site file table, unavailable score estimates, non-uniqueness decisions, four ranked untried ideas, and exact future submission steps. No approved-download control is shown.

## Fresh evidence and scope

| Artifact | What it establishes | What it does not establish |
|---|---|---|
| `evidence/s28/input_audit.json` | Pinned owner-mirror hashes, grid/band order and prepared matrix | Original organizer authenticity, license/eligibility or hidden labels |
| `evidence/s28/shared_assets.json` | Nine pinned upstream assets match reviewed SHA-256 | Complete parallel registry or exclusive lane |
| `evidence/s28/preflight.json` | Five remaining protocol failures after successful cache/tool restoration | Permission to run an experiment or select a slot |
| `evidence/s28/download_audit.json` | 880 actual local archive checks; two historical failures | Competition performance or portal acceptance |
| `evidence/s28/site_heads.json` | Fresh GitHub main-branch commit metadata for all nine focus sites | Fresh raster downloads, highest-score ranking or organizer receipts |
| `evidence/s28/official_reference_README.md`, `official_reference_cells.json` | Official reference snapshot, source text, notebook hash and selected cells | Independent certification of our holdout metric or a leaderboard forecast |
| `evidence/s28_validation_run_card.json` | This branch's negative decision and evidence digests | A newly generated TIFF |

The two archive failures are `s22_archive_h40_vent_allfinite_outside_zero` and `s22_archive_h41_spring_allfinite_outside_zero`. The archived all-finite variants carry inconsistent nodata metadata. They are retained byte-identically as historical evidence; they are not approved uploads. S25's newly expanded sibling-manifest checks pass. The overall archive status remains FAIL, not green.

## Parallel correction integrated before PR

While this branch was being verified, PR #79 merged an independent audit of the historical S25 TIFF against the registered calibration control. Its prior local-only uniqueness claim is superseded: `evidence/s28_pcse_lattice_audit.json` reports all candidate dots within 3 pixels of that control. This is geometry evidence, not a HOLDOUT-DTI or a new model experiment. Preserve the parallel run cards (`s28_run_card.json` and `s28_novelty_run_card.json`) and reports separately; this branch uses `s28_validation_run_card.json` and this `74_s28_validation_review` namespace. The canonical current report includes the correction. The original S25 files are unchanged. The result was then independently reproduced in this checkout using the existing hash-pinned shared comparator and validator: `evidence/s28/pcse_lattice_reproduction.json` returns `DUPLICATE_STOP`, max candidate-side 3 px overlap 1.0. This read-only archive audit is not a geological experiment or new pre-placement test. It verifies one sufficient rejecting comparator, not completeness. Command:

```sh
.venv/bin/python scripts/audit_registry_feasibility.py \
  --control data/s28/lattice.tif \
  --candidate docs/downloads/gems28-s25-pcse-scarp-energy-k37654-20261028-4af5ddbb4b50-nan.tif \
  --out evidence/s28/pcse_lattice_reproduction.json
# expected exit 1: DUPLICATE_STOP
```

## Why GEMSDOE32's supplied 0.2778 may have improved

The inherited pinned nine-file forensics (`evidence/s23_scorecard.json`, `evidence/s23_focus_novelty.json`) reconstruct H33-2-B2 from a 40,199-dot H27-4 parent by removing 2,545 catalogue-adjacent dots and adding none, leaving 37,654 dots. This session did not fetch/reconstruct those remote rasters anew. Therefore describe this as **inherited pixel-audit evidence**, not a fresh causal experiment.

The repository DTI uses pooled distance-weighted true/false positives and false negatives, alpha 0.2, beta 0.8, and a triangular 300 m kernel. A redundant prediction can add false-positive mass without additional recovery credit; selective removal can improve a precision/recall tradeoff. Removing an independently useful prediction instead hurts recovery. Sparse emission hygiene is a plausible mechanism, **not proof** that the claimed leaderboard change was caused by geology, pruning or catalogue exclusion. The value 0.2778 remains **USER-REPORTED / UNVERIFIED**, not ORGANIZER-CONFIRMED. No file-bound submission-page receipt exists here. There is no defensible numeric forecast that a new raster would exceed it.

The nine-site executive table uses the highest **supplied historical** claim per site, not a claim to have exhaustively ranked every current file. All nine selected historical files fail the requested mutual geometry novelty rule in the inherited audit. This does not mean every byte is identical. File hash difference is weaker than spatial novelty. Fresh GitHub heads show repository activity but do not synchronize concurrent/private predictions.

## Ranked hypotheses before implementation

Reuse `registry/s26_hypotheses.json`; do not pretend the same slate is newly invented or PCSE is untried. No operator below was implemented in this session. The ordering is qualitative expected complementarity/cost, with **unknown** DTI gain, not an estimated leaderboard score.

1. **TCB: two-sided directional texture-covariance boundary.** Existing `rtp`, `tmi_hg`, `cond_surf`; remove side-specific means and compare directional semivariograms/correlation lengths and anisotropy across a boundary. Potential concealed damage/alteration signal despite weak amplitude edges. Distinct proposed operator from existing gradients, Hessians, context classifiers and graph methods. Mimics: intrusive/depositional contacts, survey leveling and resampling. Medium-high cost. Restored bands available; still not an assigned lane or authorized test.
2. **MCR: spatially cross-fitted conductivity residual margins.** Existing `cond_surf`, `depth_to_base_surf`, `det_elev`, `det_elev_slope`; conditional-quantile residuals against terrain/depth context, then coherent residual margins. Could reveal concealed alteration rather than merely raw conductivity edges or dilation products. Mimics: saline aquifers, lacustrine clay, irrigation return flow and EM-depth variation. Medium cost. Bands available; no numerical forecast or new result.
3. **HFR2M: heat-flow residual × shallow-temperature conjunction.** USGS Great Basin heat-flow residuals plus independent DOE GDR #1391 2 m probes and conductivity/depth context. Buried permeable conduits may have thermal corroboration without mapped scarps. Distinct from a single thermal or geothermometer channel. Mimics: groundwater discharge, warm aquifers and uneven sampling. High cost. Specific sources below; raw official bytes absent and their hosts outside runtime allowlist. **Not viable for the present run.** Historical mirror availability is not a current official-data obtainability check.
4. **DNT: drainage displacement/knickpoint trains.** USGS 3DEP 1 m DEM, compared with existing LiDAR descriptors; routed drainage topology, offsets, wind gaps and aligned knickpoints, not scarp-amplitude scoring. Could preserve displacement evidence after scarp diffusion. Mimics: lithologic resistance, landslides, roads/culverts and artificial channels. Very high cost. Challenge-specific official DEM tiles absent; USGS hosts inaccessible here. **Not viable for the present run.** Restoring a DEM URL list does not restore terrain tiles.

No claim of a proven fault, geothermal vent, productive reservoir or prize eligibility is made. The official reference notebook explicitly targets **geological fault detection**, not labeled geothermal-vent discovery. Fault proximity and geothermal productivity are different scientific endpoints.

## Verified official-source observations and review links

Fetched from the organizer's GitHub organization at commit [`aebe92f7c8a990f0e3443451b7a825d9afd6336b`](https://github.com/drivendataorg/gems-prize-reference-solution/tree/aebe92f7c8a990f0e3443451b7a825d9afd6336b):

- [README](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md) provides both CPU-only and GPU environments; a GPU is faster but not universally required. This corrects the prompt's blanket historical GPU-blocker assumption.
- [Notebook](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/unet-mc-cv-reference-solution.ipynb), cells 0, 5, 6, 16, 19: geological fault detection; features below −1e38 converted to NaN; loading fault labels; Tversky **training loss** alpha 0.2/beta 0.8; single-band GeoTIFF written using label CRS and transform. The notebook's random patch splitting is **not** the required buffered whole-segment holdout, and its training loss is not proof of the hidden distance-tolerant scoring implementation. Its contents are stored with source-cell indices and a complete notebook SHA-256 in the evidence extract.

Retained official links for review, **not freshly fetched/verified in this network-restricted session**:

- [Competition overview/rules](https://www.drivendata.org/competitions/306/competition-doe-gems/), [problem and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/), [data](https://www.drivendata.org/competitions/306/competition-doe-gems/data/), [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/).
- [NLR report](https://docs.nlr.gov/docs/fy26osti/96647.pdf).
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and).
- [USGS heat-flow item / DOI 10.5066/P9BZPVUC](https://www.sciencebase.gov/catalog/item/6297d2fad34ec53d276c5b28), [DOE GDR #1391](https://gdr.openei.org/submissions/1391).
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program), [1 m DEM collection](https://data.usgs.gov/datacatalog/data/USGS:77ae0551-c61e-4979-aedd-d797abdcde0e).

The prompt's conflicting 0.3195/0.4413 leaderboard maxima are not current verified facts. An earlier parallel-session public-board observation remains dated historical evidence, not this session's observation or a file-linked receipt. No scraping, authentication automation or manual credential request was performed.

## Three-pass review

1. **Implement and verify:** restore inputs/shared stack, prepare cache, run existing preflight and exact archive audit; implement missing sibling-manifest inspections and publish the current negative executive summary/card.
2. **Bug/edge-case review:** synthetic matching-hash corrupt-content tests, malformed manifests, shifted grid, range/NaN/Inf, ZIP/path/symlink tests; separate current/historical deployment digests; preserve historical bytes and scientific evidence. Fresh full-suite result after parallel integration: **714 passed, no skips, 34 Rasterio pending-deprecation warnings, 9 subtests passed**. Ruff passes. Initial full-suite failures exposed tests that incorrectly froze the generic current alias to S23; update them to require S28 for generic aliases and S23 for immutable dated aliases, retaining exact-byte assertions and local-link checks.
3. **Requirements recheck:** record software results in `evidence/s28/software_verification.json`; verify offline build reproducibility, canonical aliases, nine rows, honest source/score labels, no approved upload, no new TIFF, no experiment/slot selected. Software passes do not confer scientific validation or promotion.

## Prioritized next-session work and limitations

1. Resolve a single explicit lane and authoritative synchronized registry; this cannot be fabricated from GitHub head timestamps. Keep duplicate thresholds unchanged unless the protocol owner explicitly revises them.
2. Establish a frozen comparable best using the same buffered whole-segment evaluator and visible-only features, then obtain a valid new run budget. Do not reset an expired configuration and call that external authorization.
3. Test TCB only if it is the assigned lane: feature-level canaries first, surface novelty before placement, final-dot novelty afterwards, paired holdout uncertainty against the frozen best. Stop on duplication, leakage, insufficient gain or budget exhaustion. Maximum three experiments/two hours.
4. Resolve the two archival nodata defects with explicitly versioned regenerated artifacts if there is a legitimate future need; never mutate historical hash-bound files in place. Keep old defects visible meanwhile.
5. Only the separate selector may check the authenticated weekly cap and authorize a real upload. Record the exact submission-page receipt and TIFF digest afterwards. The current sandbox cannot access that portal or non-allowlisted official external data.

**Maximize P(Win):** preserve scarce slots and reject unsupported forecasts. **Own the Outcome:** restore what can be restored, repair real audit defects, and communicate the remaining negative outcome plainly. A code PR merge is not a competition submission.
