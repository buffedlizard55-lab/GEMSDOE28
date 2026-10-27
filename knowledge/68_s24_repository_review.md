# S24 — repository review and fail-closed status

**Review time:** 2026-10-27 UTC. **Branch:** `arena/79bafcec-gemsdoe28`.

## Decision — no new TIFF; NOT OK TO DOWNLOAD OR SUBMIT

S24 is a repository, evidence, and software review only. **No geological hypothesis was fitted or evaluated, no feature canary was run, no prediction surface or new raster was made, no leaderboard estimate is supported, and no weekly slot was selected.** No file is approved for upload. Do not use an old TIFF under a new name.

This does not weaken the S23 rejection. It clarifies that the latest checkout also lacks the inputs and shared-template files needed to run the specified pipeline. The automatic preflight at `2026-10-27T18:48:03Z` returned `BLOCKED` (expected exit 1); the exact record is [evidence/s24_preflight.json](../evidence/s24_preflight.json), and the final audit card is [evidence/s24_run_card.json](../evidence/s24_run_card.json).

## What the review verified

### 1. GEMSDOE32's supplied 0.2778 claim

**0.2778 is USER-REPORTED / UNVERIFIED, not HOLDOUT-DTI and not ORGANIZER-CONFIRMED.** The pinned byte-for-byte forensic record in [evidence/s23_focus_novelty.json](../evidence/s23_focus_novelty.json) reconstructs the GEMSDOE32 raster as the GEMSDOE31 solo dot set with 2,545 catalogue-adjacent dots removed (37,654 dots remain; symmetric difference 0 against that reconstruction). Removing predictions that add false-positive cost but little marginal distance-weighted true-positive credit is a plausible explanation for a better DTI without adding a fault detector. This is a metric mechanism, **not proof of why a competition score was assigned**: no file-bound organizer receipt or hidden-truth validation is available.

The independent higher numbers in the owner's prompt (0.3195 and 0.4413) are not refreshed in this review. The repository contains an older public leaderboard observation of 0.4437 at 2026-10-26 22:02 UTC; it is a HISTORICAL PUBLIC OBSERVATION, not a current score or a file-bound receipt. A forecast is not a score. A validated leaderboard estimate is unavailable for every site.

### 2. Nine-site executive recommendation

The generated [executive summary and upload guide](../docs/executive-summary.html) lists the highest supplied historical file for GEMSDOE24, 25, 27, 28, 30, 31, 32, 33, and 36, preserves each result's USER-REPORTED / UNVERIFIED label, reports the estimate as unavailable, and explains why none is unique under the requested threshold. The files are educational forensic references only; none is a new submission recommendation.

| Site | Highest supplied historical claim | Score evidence label | Estimated leaderboard score | Unique vs the other eight | New file / upload decision |
|---|---:|---|---|---|---|
| GEMSDOE24 | 0.2477 | USER-REPORTED / UNVERIFIED | Unavailable | No | None / DO NOT SUBMIT |
| GEMSDOE25 | 0.2600 | USER-REPORTED / UNVERIFIED | Unavailable | No | None / DO NOT SUBMIT |
| GEMSDOE27 | 0.2449 | USER-REPORTED / UNVERIFIED | Unavailable | No | None / DO NOT SUBMIT |
| GEMSDOE28 | 0.2710 | USER-REPORTED / UNVERIFIED | Unavailable | No | None / DO NOT SUBMIT |
| GEMSDOE30 | 0.2600 | USER-REPORTED / UNVERIFIED | Unavailable | No | None / DO NOT SUBMIT |
| GEMSDOE31 | 0.2708 | USER-REPORTED / UNVERIFIED | Unavailable | No | None / DO NOT SUBMIT |
| GEMSDOE32 | 0.2778 | USER-REPORTED / UNVERIFIED | Unavailable | No | None / DO NOT SUBMIT |
| GEMSDOE33 | 0.2632 | USER-REPORTED / UNVERIFIED | Unavailable | No | None / DO NOT SUBMIT |
| GEMSDOE36 | 0.2750 | USER-REPORTED / UNVERIFIED | Unavailable | No | None / DO NOT SUBMIT |

All nine historical bests are pairwise non-unique under the specified 3-pixel / 70% test in the bounded nine-file audit. This is not a complete synchronized global registry. Detailed names, hashes, pinned commits, lower supplied claims, checks and directional overlap values are in [evidence/s23_scorecard.json](../evidence/s23_scorecard.json) and [docs/data/s23_scorecard.csv](../docs/data/s23_scorecard.csv).

### 3. Why no distinct candidate was run

Two independent stop conditions remain, and a fresh current-workspace preflight confirms further missing inputs:

- No explicit single method paragraph/assignment source is present. S23's four ranked hypotheses are a preregistered proposal slate, **not an exclusive lane assignment**.
- The literal novelty rule includes every registry raster. S23's geometry audit found that the registered spacing-five calibration lattice covers 99.871327% of the footprint within 3 pixels. For a 37,654-dot budget, even an unspaced counting bound requires at least 82.341849% proximity overlap; with 2.8-pixel minimum spacing the bound is at least 90.431295%. Those are **GEOMETRY-AUDIT** calculations, not performance scores. The already-existing S22C raster is a measured final-dot duplicate (99.617571% within 3 pixels of that lattice); its low Spearman value does not override the overlap stop. S23 explicitly did not test its unavailable pre-placement surface.
- The present checkout has no `data/prepared/features.npy`, `data/prepared/features.json`, `shared_template/` implementation files, `data/sample_submission.tif`, `data/labels.tif`, or `data/training_features.tif`. The fresh preflight therefore reports the four design/protocol gates plus the missing cache and nine shared assets. Earlier S23 evidence that those assets passed verification describes its earlier runtime, not this checkout.
- A previous optional input-restoration attempt was stopped at a GitHub REST 403 rate limit after nine input hashes were verified; it reports no new optional files restored. The S24 review does not repeat that unchanged restore request. No new official DEM bytes were obtained.

Consequently the inherited lane was not resumed, no dot budget was changed to exploit lattice holes, and no new surface was compared or placed. The prompt's explicit stop/uniqueness rules take precedence over pressure to manufacture a TIFF. This protects the weekly cap and avoids claiming an invalid result.

### 4. Frozen untested hypothesis slate (rank is qualitative; improvement unknown)

These are ranked research proposals already recorded in [knowledge/66_s23_preregistration.md](66_s23_preregistration.md) and [registry/s23_hypotheses.json](../registry/s23_hypotheses.json), not new findings or measured gains.

1. **PCSE — phase-congruent scarp energy.** Cached detrended elevation, TMI and isostatic-gravity layers; oriented cross-profile odd/even derivative energy and cross-scale step-polarity consistency. A concealed or weak step may remain phase-consistent when amplitude-only edge operators are weak. Differs from current scarp amplitude, oriented line-integral and Gaussian-context features. Mimics: terrace risers, paleoshorelines, roads and unfaulted lithologic contacts. Medium implementation cost; expected improvement unknown; no new data required once the cache/protocol is restored.
2. **TCB — texture-covariance boundary.** RTP, TMI horizontal-gradient and surface conductivity; two-sided, mean-removed directional covariance/semivariogram change. Damage or juxtaposition may alter texture even when potential-field amplitudes cancel. No comparable two-sided covariance-change operator is implemented. Mimics: depositional facies, intrusive contacts and survey seams. Medium–high cost; improvement unknown; existing cached layers suffice.
3. **MCR — matched conductive residual.** Surface conductivity conditioned on terrain and depth-to-base; spatially cross-fit conditional quantiles and map coherent residual margins. Could separate a local conductive anomaly from basin-fill/topography associations. Differs from raw conductivity/depth margins already explored. Mimics: saline aquifers, lacustrine clay and variable depth of investigation. Medium cost; improvement unknown; existing cache required.
4. **CSD — compound-scarp diffusion spectrum.** Original USGS 3DEP 1 m profiles at multiple degradation widths; test for repeated displacement steps. Differs from cached 100 m LiDAR maxima, which lose the original profile. Mimics: multiple terraces, shorelines and road cuts. High I/O/CPU cost; not viable in this runtime because original official tile bytes are unavailable here. The specific free official source is [USGS 3DEP](https://www.usgs.gov/3d-elevation-program); a catalog link or owner-mirrored URL list is not proof the required bytes were obtained.

No expected DTI improvement is numerically forecast. The first candidate cannot be validated before the missing shared cache/tools, explicit lane, complete synchronized registry and same-protocol frozen best are restored. A score estimate for the nine existing files would be misleading without hidden-label transfer calibration.

### 5. Source feed freshness reconciliation

The immutable S23 audit snapshot says 10/18 sources were freshly observed at 17:29:17Z. The later committed source-feed file (`docs/data/feed.json`) records 16/18 at 17:51:14Z. At S24 preflight time (18:48:03Z), that later observation was 56m49s old. This is a chronology update, **not a contradiction or a live check**; S23's original snapshot is preserved at `evidence/snapshots/s23_source_feed.json`, and the S24 copy is `evidence/snapshots/s24_source_feed.json`.

The later feed is metadata/availability evidence only: 16 entries returned a response; two requests (`hermant-2025`, `usgs-qfaults`) failed because the configured 2,000,000-byte response limit was exceeded. It does not establish that every response's scientific content, licence, coverage or schema was reviewed. No DrivenData page, current leaderboard, authenticated quota or submission receipt was fetched in S24. The current site displays the later feed timestamp and count; it does not monitor the competition.

### 6. Verification passes and current software state

- **Pass 1 — inspect and verify:** reviewed the read-first README, S23 decision, nine-site scorecard, pinned shared-tool contract, current source feed, exact-file audit and site generator. A standard-library site build succeeds, reports 43 registered source records/four unimplemented hypotheses, makes zero external requests, and leaves submission readiness false.
- **Pass 2 — bugs and edge cases:** reconciled the two dated feed snapshots; distinguished S23's prior cache/template verification from the absent files in the current checkout; confirmed the preflight fails closed; checked that no current or prior TIFF was added or reclassified by this review. The first test run exposed that S23 byte-bound `build_site.py` and `site_s23.py`; their exact pre-S24 bytes are now preserved in `evidence/snapshots/pre_s24_*.py`, and the historical test verifies those snapshots rather than falsely binding old evidence to changed current code. A serialized-run-card byte comparison also caught float/list formatting differences; the site now republishes the exact source JSON bytes. No scientific or format gate was bypassed.
- **Pass 3 — final recheck:** `.venv/bin/python -m pytest -q` → **647 passed, 6 skipped, 12 warnings, 9 subtests passed**. The six skips are data-dependent tests and are not passed. `.venv/bin/ruff check src scripts tests` → **clean**. `python -S scripts/build_site.py` → **built**, 19 documentation pages, zero external requests. `git diff --check` → **clean** after the review changes. The verification record is [evidence/s24_verification.json](../evidence/s24_verification.json).

The site is deterministic static HTML. `ruff` and `pytest` were installed into an ignored local virtual environment; no dependency files or data arrays were added. No new TIFF payload, training dataset or model checkpoint was generated.

## Priority next work and limitations

1. Keep the current literal registry rule. Resolve any protocol conflict by an explicit, shared, versioned registry decision; do not omit the spacing-five control or reinterpret the stop rule locally.
2. Restore the hash-pinned feature cache and all pinned shared template tools through an allowed, rate-limit-safe route. Current workspace preflight must pass before a model run.
3. Obtain a synchronized complete surface/final-raster registry, a specific exclusive lane assignment, and a retrained frozen comparator under the exact buffered visible-only whole-segment protocol. Without those, no candidate can be declared unique or superior.
4. If all prerequisites pass, only then run one preregistered hypothesis: test every feature alone (AUC >0.90 is leakage until resolved), compare the surface pre-placement and final dots against every registry member, and use the shared evaluator/writer for pooled HOLDOUT-DTI with evaluator version, withheld-positive count, and paired spatial 95% CI. Require it to beat the frozen best before a separate slot selector checks the authenticated weekly allowance.
5. Do not estimate a contest score from catalogue-only holdout results without validated transfer calibration. Preserve a filename/SHA-bound organizer receipt before labeling any score ORGANIZER-CONFIRMED.

**Limitations:** no current DrivenData auth/account allowance, official organizer data download/receipt, synchronized parallel registry, explicit external lane, current leaderboard fetch, or original 1 m DEM bytes. Historical score values are user-reported; one old public top-score observation is stale. Exact file format validation cannot compensate for scientific, novelty or organizer-acceptance gates.

### Manual-review sources

- [Competition rules / task overview](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Problem, metric and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition data tab](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [DOE GEMS rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE GDR INGENIOUS compilation 1391](https://gdr.openei.org/submissions/1391)
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program)
- [EPSG:32611](https://epsg.io/32611)
