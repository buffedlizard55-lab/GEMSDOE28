# Repository review — 2026-10-28 UTC

**Reviewed checkout:** `arena/7504de16-gemsdoe28` at `4955e29c7b66503ba2178b25d356d713dc1bc534`

**Review type:** read-only engineering, evidence, and submission-safety review. No geological experiment, holdout, score estimate, TIFF generation, slot selection, or portal submission was performed.

## Executive decision

**NO NEW TIFF. OK TO DOWNLOAD AS A NEW SUBMISSION: NO. OK TO SUBMIT: NO.** There is no fresh candidate artifact and the verifier cannot validate historical downloads without the sample grid and labels. Do not rename, repack, or re-upload an old file to satisfy the uniqueness requirement. This is the appropriate fail-closed outcome; the requested file cannot be responsibly generated under the supplied protocol and current checkout state.

The recorded assigned method lane is `null`; the parallel-run protocol's referenced single-method paragraph is not present as an assignment. The current-session configuration is from an earlier session and records branch `arena/a774f0a0-gemsdoe28`, while this checkout is `arena/7504de16-gemsdoe28`. Its time budget began on 2026-10-27 and has expired. These are provenance/configuration mismatches, not evidence that the source code or historical scores are incorrect.

## What is in good shape

- The project has an unusually extensive provenance-first workflow: pinned owner-repository audits, explicit distinctions between user-reported scores, local HOLDOUT-DTI, geometry diagnostics, and organizer receipts; a JSON-only site generator; a strict submission validator; fail-closed promotion/preflight code; and a large set of synthetic and regression tests.
- The nine-site executive scorecard exists for GEMSDOE24, GEMSDOE25, GEMSDOE27, GEMSDOE28, GEMSDOE30, GEMSDOE31, GEMSDOE32, GEMSDOE33, and GEMSDOE36. Its rows appropriately report no hidden-score estimate and no new upload recommendation. The best listed claim is GEMSDOE32's `0.2778`, but it is classified as **USER-REPORTED / UNVERIFIED**, not ORGANIZER-CONFIRMED.
- The prior pinned overlap audit records that all **72 directional comparisons** among the nine selected historical rasters cross the protocol's `70%` three-pixel proximity threshold. This is a scope-limited comparison among those nine artifacts, not proof about a complete global registry. Each of those historical files therefore fails the requested uniqueness rule; none is recommended.
- The project contains ranked research proposals (PCSE, TCB, MCR, CSD). They remain unimplemented or unvalidated in the latest recorded scientific session; their expected HOLDOUT-DTI improvement is unknown. The documented CSD option depends on original official USGS 3DEP 1 m DEM tiles, which were not obtainable in this runtime. Do not describe a hypothesis as viable or higher scoring before it passes the registered holdout and leakage gates.
- The prior geometry report classifies the calibration-lattice figures as **GEOMETRY-AUDIT, not HOLDOUT-DTI**: for the declared 37,654-dot historical budget it records a duplicate-stop bound, including a 99.8713% footprint coverage by the registered 3-pixel disks. The last recorded inherited-final-dot overlap was 99.6176%. These values come from pinned historical evidence; the corresponding raster/control assets are not present for a fresh replay in this checkout. They are not score estimates and do not establish that every possible smaller or genuinely new prediction is impossible.

## Verification performed in this checkout

- Installed `requirements.txt` into ignored `.venv/`; no dependency payload, training input, or generated raster was added to the repository.
- At the initial checkout review, `.venv/bin/python -m pytest -q` reported **652 passed, 6 skipped, 12 warnings, 9 subtests passed**. After rebasing onto the concurrently merged main review, the suite was rerun at 2026-10-28 11:45 UTC: **655 passed, 6 skipped, 12 warnings, 9 subtests passed**. The skips are data-dependent and are not counted as successful scientific validations. Warnings are Rasterio affine-transform deprecations.
- `.venv/bin/ruff check src scripts tests`: **PASS**.
- Canonical static-site generation plus its active-review overlay, `python -S scripts/build_site.py` and `python -S scripts/build_active_review.py`: **PASS**, no external requests, no tracked working-tree changes after the two-step build.
- `scripts/check_run_preflight.py --config registry/current_session.json`: **BLOCKED**. Failures include no explicit method assignment, no complete synchronized parallel registry, no frozen comparable strict-protocol best, expired run budget, missing prepared feature metadata/array, and missing materialized shared-template assets.
- `scripts/verify_downloads.py`: **FAIL CLOSED** because `data/sample_submission.tif` and `data/labels.tif` are absent. The check did not approve any candidate. The input directory also lacks `training_features.tif`; only manifests/run cards are present in `data/`.
- `git status` is clean after verification. No TIFF was written and no submission slot was used.

The green software checks establish only that available code/tests and the static-site build work; they do not establish current scientific performance, correctness of historical score claims, current leaderboard status, or competition acceptance.

## Findings requiring attention

### High priority: experiment is not authorized or reproducible

1. No assigned single-method lane or assignment source is set in `registry/current_session.json`.
2. The configuration points to an old branch/session and its two-hour wall-clock budget is expired. Do not reuse it as current authorization.
3. A complete synchronized registry and a frozen best evaluated under the exact strict holdout protocol are absent from current-session config.
4. Required local feature cache, sample submission, labels, training raster and materialized shared-template assets are absent. The validator and preflight correctly fail closed.
5. The previously recorded dense-lattice result stops the historical 37,654-dot lane under the literal rule. Do not work around it by moving dots into uncovered cells or omitting the calibration raster. Any policy change must be explicit, shared, versioned, and independently applied to all parallel lanes.

### Score provenance and H33-2 interpretation

The supplied GEMSDOE32 `0.2778` is the largest of the nine user-provided historical claims, not an independently verified organizer receipt. Repository history contains forensic claims that the artifact is a catalogue-adjacent pruning of the H27-4 solo pattern, alongside later records that dispute or limit what is presently verifiable from this checkout. The H33-2 raster and a file-bound organizer receipt are not available here for a fresh byte-level reconstruction. The defensible interpretation is therefore conditional: removing predictions near known catalogue faults could improve a Tversky-style score if those predictions contribute false-positive mass and little weighted true-positive credit, but the claimed score's cause is **unknown**. The `0.2778` must not be attributed causally to pruning without the file/receipt and reproducible scoring evidence.

No calibrated mapping from local holdout performance to hidden leaderboard score is established. Accordingly, the scorecard's numerical estimate is **unavailable** for all nine sites. The prompt's `0.4413` and `0.3195` leaderboard maxima conflict; neither was freshly checked against DrivenData in this checkout and neither is adopted as current.

### Currentness and conflicting historical records

The repository's README and Pages content identify S24 / 2026-10-27 material as the latest review, and older run-card/config records identify multiple different Arena branches. The top-level no-submit decision remains consistent with the current fail-closed checks, but the dashboard's review date, branch provenance and source-feed freshness should be refreshed in a dedicated documentation update. Keep immutable/hash-bound prior evidence intact; add a new dated record instead of editing old run cards. The source feed is not an authenticated current leaderboard or weekly-cap feed.

## Next work, in order

1. Obtain/set the actual single assigned method paragraph and assignment provenance; start a new bounded session clock and registry snapshot. Do not assume an empty lane is consent to choose one.
2. Restore the competition inputs and cached feature stack from authorized pinned sources, materialize the shared template at its pinned hashes, and record whether each source is organizer-authenticated or an owner-supplied mirror. Keep large data out of Git.
3. Resolve the dense calibration-control feasibility issue only through a shared versioned policy decision; do not silently exclude a raster or optimize around its holes.
4. Freeze a comparable buffered whole-segment holdout baseline, visible-only catalogue feature derivation, exact visible-fault mask, pooled DTI metric/kernel and paired uncertainty method before running an experiment. Test each feature alone for leakage first.
5. Only after preflight authorizes work: preregister one candidate, spend no more than the experiment/time cap, and check both the score surface before placement and final dots against the complete registry. Promote only after beating the frozen comparable holdout best with the required uncertainty/spread gates.
6. Run the exact-file validator on any newly generated candidate (inside-footprint finite values in `[0,1]`; single band; exact CRS/shape/transform; hash and registry uniqueness). Keep selector/weekly-cap check and organizer receipt separate from research. Until these steps pass, keep the download button locked.
7. Update the executive page and review-date/source-feed labels from a fresh, reproducible record. Preserve older results as history and label them stale rather than implying they are current.

## Run card

See [`evidence/review_2026-10-28.json`](../evidence/review_2026-10-28.json). It is a negative repository-review deliverable, not a scientific experiment card: no new candidate raster exists, so holdout DTI, confidence interval, raster hash, and candidate validation are null. The prior geometry/overlap values are explicitly labeled GEOMETRY-AUDIT and are not scores.
