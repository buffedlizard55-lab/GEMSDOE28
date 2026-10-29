# S28 — current evidence review, 2026-10-29 UTC

Branch: `arena/cc67fd6a-gemsdoe28`. No scientific experiment, new TIFF, feature canary or weekly slot. **OK TO SUBMIT: NO.** The requested high-performing unique submission remains unfulfilled; no score estimate can honestly be supplied.

## Pass 1 — inventory, restoration and fresh checks

Read README and prior-session follow-ups. Installed dependencies in ignored `.venv/`; the system Python is externally managed and was not modified. Initial tests: 664 passed, seven skipped. Restored all four core files, the model group and nine pinned shared-template assets through existing restoration scripts. Ran existing `prepare_data.py`: 32-band cache SHA-256 `83ed2704ee2de03cf8b1c8f2966fcf71813501df97c1c35400e6c0415393f6dc`. The restoration logs and `evidence/s28_preflight.json` document this. These are owner GitHub mirrors, not organizer-authenticated downloads.

Fresh nine-site inventory pinned each repository's main commit and checked selected raster Git blob identities. Sources, line-numbered page excerpts, file hashes, full raster inventories and format checks are in `evidence/s28_priority_repository_audit.json`. This covers the requested historical identities, not every currently available candidate or every concurrent lane.

Added a comparison-only wrapper around the **pinned shared novelty comparator**. It places no dots and changes no predictions. Its nine leaders are selected from the user's supplied historical results, not a new slot selection. Every leader fails the literal final-dot rule against another leader. Full-footprint raw rank correlations, sampled kernel sensitivity correlations and exact directional 3 px overlap are distinguished in `evidence/s28_priority_novelty.json`. The original continuous surfaces are unavailable, so none of these checks is represented as a pre-placement surface check.

Fresh pixel-set forensics reproduce:

- GEMSDOE25 = GEMSDOE30 inside the footprint.
- GEMSDOE28 solo = GEMSDOE31 solo inside the footprint.
- GEMSDOE32 = GEMSDOE28 solo minus dots at catalogue distance <=2 px: 37,654 surviving dots, 2,545 removed, no additions.

These facts do not prove the reported leaderboard-score mechanism. A plausible explanation is reduced false-positive cost near known faults; test by rebuilding the catalogue-dependent operator inside every buffered hidden-segment fold. Never evaluate a full-catalogue-dependent archived raster as though it had not seen hidden segments.

## Pass 2 — bugs and conflicting assumptions

1. Historical `allfinite` filenames in GEMSDOE31 have metadata that the inventory classifies as NaN variants. Selecting by that label was ambiguous. The wrapper now requires exactly one explicitly named `-nan.tif` or `-nanoutside.tif` artifact and fails closed if selection is ambiguous. A regression test covers the case. Historical bytes remain untouched.
2. New standalone review pages were assumed by a legacy test to contain the S23 banner. Updated that test to assert the S28 negative decision on the new page **without skipping its local-link and duplicate-ID checks**.
3. Multiple older generated panels call themselves current and some report absent data. Added an S28 top panel explicitly superseding those checkout-state notices, an updated latest-review link and a standalone nine-site summary. Historical records remain identifiable and are not rewritten as current observations.
4. The exact-file audit still has two failures in 869 checks: archive-only H40/H41 all-finite variants with NaN nodata tags. Flagged, not rewritten or approved. A format-valid research TIFF is not a skilled submission.
5. README assertions in historical-review tests were brittle to a new leading session. They now assert that the historical section remains present; the new tests separately require S28 at the beginning.

## Pass 3 — end-to-end build, link and evidence coherence

A root-route regression caught the updated latest-review link changing only the `docs/` route. Fixed the builder to update both route forms. Ran the complete offline build (`build_site.py` then `build_active_review.py`) and full suite again: **671 passed, five skipped, 12 warnings, nine subtests passed**. Skips are not passes. Ruff clean; `git diff --check` clean. The S28 overlay is wired into the existing build chain and the workflow path filters. The builder is idempotent, escapes source text and cannot publish a promotion card. Tests check hashes, all nine comparisons, exact-file selection ambiguity, decision flags, generated entrypoint ordering and local links.

## Ranked scientific work and remaining barriers

Reuse the existing **four untried** proposals in `registry/s26_hypotheses.json`: directional texture-covariance boundaries (TCB), cross-fitted conductivity residual margins (MCR), heat-flow/2 m probe conjunction, drainage-network displacement/knickpoint trains. The current executive page provides layers, transforms, missing-fault rationale, differences, mimics, implementation cost and data limitations. Ranking is qualitative expected complementarity/cost, not a DTI projection. No new scientific novelty is claimed for re-listing them.

TCB remains the highest actionable existing-data proposal but **was not validated**. Fresh preflight after restoration retains five blockers:

- no supplied single-method paragraph/assignment provenance;
- no complete synchronized parallel registry;
- declared emission budget blocked by the literal overlap rule (dense calibration lattice);
- no frozen comparable current-best result under the requested strict evaluator;
- expired configured session clock (the configuration belongs to an older branch).

Resetting a timestamp would not resolve the other gates. Do not delete the dense calibration control, tune dot locations around its holes, silently reinterpret the rule, or generate a renamed archive merely to satisfy a download request. Negative audits do not authorize a submission.

The top-candidate experiment, per-feature AUC canaries, strict paired improvement gate and new TIFF cannot be completed under those unresolved prerequisites. No external heat-flow/probe or 3DEP hypothesis is called viable without official byte/coverage checks. Non-GitHub official hosts are outside this runtime's outbound allowlist. DrivenData authentication, submission receipt and remaining weekly allowance are unavailable here. No portal interaction occurred.

## Verified source scope and irregularities

- [Official reference README at pinned commit](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md), freshly fetched through GitHub. Line excerpts and SHA-256: `evidence/s28_official_reference_check.json`. It explicitly offers CPU-only operation; the inherited claim that GPU is required is too strong. GPU accelerates training.
- [Official task/metric/format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) and [leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) are review links, **not freshly fetched in S28**. The inherited prior-branch board observation must not become a new receipt. Prompt anchors 0.3195 and 0.4413 conflict; S28 makes no current-top claim.
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and), [USGS 3DEP](https://www.usgs.gov/3d-elevation-program), [GDR INGENIOUS](https://gdr.openei.org/submissions/1391): official source links, no fresh retrieval/availability claim.
- All nine historical score values remain **USER-REPORTED / UNVERIFIED**. None is ORGANIZER-CONFIRMED. Estimated leaderboard scores are null rather than invented.
- Existing S25 HOLDOUT-DTI is historical, not newly reproduced here: evaluator gems-segment-pooled-v1, 60,988 withheld positives, 0.0450361 (95% CI 0.0380288–0.0525190), below random-K HOLDOUT-DTI 0.0698748 (95% CI 0.0666809–0.0731446). Neither number forecasts hidden-test performance.

## Next session, in order

1. Resolve the missing method-lane paragraph and synchronized registry contract, including the dense-control conflict, without relaxing user rules unilaterally.
2. Freeze the shared strict same-fold baseline and valid run configuration; preserve budgets and prior spent experiments.
3. Investigate the S25 random-K advantage before investing in another geological operator. Establish whether gains reflect actual recovery versus placement geometry.
4. If authorized by all gates, test TCB's single-feature leakage canaries and then its paired whole-segment holdout once. Stop on duplicates or a failed gate; only write a new submission after passing evidence exists.
5. Keep selection/upload separate and retain the actual organizer receipt. Code PR merge does not select a weekly slot.
