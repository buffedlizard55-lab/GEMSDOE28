# S25 repository review — 2026-10-28 UTC

## Disposition

**NEGATIVE / READ-ONLY REVIEW. No new TIFF; not OK to download or submit; no experiment or slot selected.** This conclusion follows the repository's read-first operating brief and the fresh fail-closed preflight. It is not a judgment that the scientific project is complete or that any prior file is safe to upload.

- [Machine-readable review card](../evidence/s25_repository_review_run_card.json)
- [Exact fresh preflight output](../evidence/s25_preflight.json)
- [Nine-site scorecard and upload guide](../docs/executive-summary.html)
- [Prior S24 repository review](68_s24_repository_review.md) — historical record; its recorded branch is not this active branch.

## Three review passes

### Pass 1 — repository and requirements

Read the README first, inspected the code/tests, site generation and deployment workflows, run cards, focus-site scorecard and data/cache contracts. The executive page has a row for each requested focus site (24, 25, 27, 28, 30, 31, 32, 33, 36), marks all supplied historical scores **USER-REPORTED / UNVERIFIED**, provides no uncalibrated hidden-score estimate, and explicitly labels old TIFF links **DO NOT SUBMIT**. The supplied GEMSDOE32 `0.2778` is therefore not represented as a verified contest score or a reason to reuse its raster.

### Pass 2 — risks, edge cases and evidence freshness

Ran the experiment preflight at `2026-10-28T11:38:07Z`; it exited **1 / BLOCKED**, as intended. The machine-readable output is preserved in `evidence/s25_preflight.json`. It reports missing lane assignment, a complete shared registry, a same-protocol frozen baseline, the cached feature stack/metadata, and all nine pinned shared-template assets; it also reports that the configured wall-clock experiment budget is expired. The registry manifest itself says the external parallel registry is incomplete. These are real blockers, not invitations to bypass the preflight or optimize around the duplicate rule.

No competition site, leaderboard, account allowance, receipt, external source, or DEM was queried in this review. The previously committed source-feed metadata is not a live/current feed. Historical branch-bound S24 evidence is retained but not treated as newly verified on this branch.

### Pass 3 — repeatable verification

- `.venv/bin/python -m pytest -q`: **655 passed, 6 skipped, 12 warnings, 9 subtests passed**. The six skipped cases depend on absent data and do not count as passes.
- `.venv/bin/ruff check src scripts tests`: **PASS**.
- `python -S scripts/build_site.py` followed by `python -S scripts/build_active_review.py`: **PASS**, 19 pages, 43 source records, four untested hypotheses, zero network requests; download remains locked.
- The repository test suite includes internal-link, generated-site, scorecard, and fail-closed safety checks.
- `git diff --check`: **PASS**. The generated pages were rebuilt using both documented build steps; no source changes were needed for this review.

These are software/documentation checks only. No geological experiment, leakage canary, HOLDOUT-DTI, score projection, candidate surface, uniqueness comparison, new TIFF, or organizer validation was performed.

## Current decision and interpretation

The given GEMSDOE32 `0.2778` remains **USER-REPORTED / UNVERIFIED** in this repository. Existing pixel forensics describe the file as a catalogue-adjacent pruning of the H27-4 solo pattern; that suggests a possible precision/false-positive-mass mechanism under a distance-tolerant metric, but it does **not** prove why an organizer score was assigned. The repo has no validated transfer calibration from its catalogue holdout to a hidden-label leaderboard score; an estimate would be unsupported. The prompt's conflicting `0.4413` and `0.3195` claims are not refreshed or verified here.

The repo's historical nine-site comparison reports substantial dot overlap. That comparison is bounded to those nine historical artifacts and is not a complete synchronized registry. Because this review generated no surface or dots, it made no new pre-placement or final-dot novelty claim. The all-registry uniqueness requirement is not met by absence of a comparison.

## Limitations and next actions

1. Do not download or submit any historical TIFF as a new candidate. No TIFF was created or approved in S25.
2. Resolve the registered-budget duplicate stop only through a shared, explicit, versioned protocol decision; do not tune around registry controls or lattice holes.
3. Restore the exact pinned shared template and prepared feature cache, with hashes and missingness checked. Obtain a lane assignment, synchronized complete surface/final-raster registry, and frozen comparator validated under the required buffered visible-only whole-segment protocol.
4. Only after those inputs and a fresh authorized experiment budget are valid, preregister one lane-specific experiment, run per-feature leakage canaries and pre-/post-placement novelty checks, and use the shared evaluator/writer. Label any result HOLDOUT-DTI with evaluator version, withheld-positive count, and spatial 95% CI.
5. Require a strict holdout improvement before a separate selector checks the current authenticated weekly submission allowance. Capture a receipt bound to the exact TIFF bytes before using ORGANIZER-CONFIRMED.
6. Refresh the public source metadata feed through its documented scheduled pipeline when useful; never describe the committed Oct 27 snapshot as live. Obtain DrivenData-only files via the competition's authenticated download process where authorized; this review did not attempt access.

## Official manual-review links

- [Competition overview and rules](https://www.drivendata.org/competitions/306/competition-doe-gems/)
- [Problem description, metric and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition data tab (login required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) — not queried in S25
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [DOE GEMS rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS GeoDAWN data](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE GDR INGENIOUS compilation #1391](https://gdr.openei.org/submissions/1391)
- [USGS 3DEP](https://www.usgs.gov/3d-elevation-program)
- [EPSG:32611](https://epsg.io/32611)
