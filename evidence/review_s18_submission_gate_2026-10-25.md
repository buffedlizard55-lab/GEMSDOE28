# Submission-gate review — 2026-10-25

## Executive decision

**No file is approved for upload. No new TIFF generated. No submission slot used.**
This run is a repository safety review, not an experiment or performance claim.
The requested unique qualifying submission remains incomplete. Generating an arbitrary
raster would not meet the user's scientific or uniqueness requirements.

The supplied protocol says the lane is “the single method paragraph below,” but no
such paragraph is present in this request. The preceding H40-1 migration lane has
already exhausted its experiment budget and failed. We did not select a new lane,
rerun a frozen experiment, fork an evaluator, or recycle an old file as a new one.
`data/` contains only `manifest.json`; training rasters and feature cache are absent.
Their absence does not imply mirrors cannot be restored: the repository provides
`scripts/restore_data.py` for hash-pinned **owner mirrors**, not organizer-authenticated
data. Restore and validate them only for a properly preregistered future method.

## Pass 1 — review and implement

- Read README, previous safety review, historical Session 17 claims, the shared
  promotion gate, CLI, tests, registry, site generator and input-restoration code.
- Found `promotion_gate` returning `submission_ready: true` on self-reported JSON
  alone. This function has no raster/template input and cannot inspect file bytes,
  execute holdout evaluation, authenticate claims, or approve a weekly slot.
- Fixed the shared gate, not a private fork: schema success is now reported separately
  as `evidence_schema_passed`. `submission_ready` and `slot_selected` remain false.
  `verdict: promote` in this schema API still means *eligible for further evidence
  review*, not upload permission. CLI exit zero likewise means schema success only.
- Updated tests to assert schema validity independently of upload readiness. Included
  end-to-end CLI success and injected self-approval-field regression tests.
- Added a leading withdrawal to `knowledge/51_session17_unique_submission.md`.
  Its historical “unique/promote” description contradicts its own reported near-unit
  correlation and excessive probe overlap. Historical text is retained for audit.
- Kept the site's no-approval warning and added a link to this review on every page.
  Existing downloads remain explicitly historical/inspection-only.

## Source refresh and scientific interpretation

Fetched source HTML through GitHub's API for all nine requested owner repositories:
GEMSDOE24/25/27/28/30/31/32/33/36. `s18_owner_site_refresh.json` records file paths,
byte hashes, retrieval outcome and limited score-related excerpts. This verifies
retrieval of **owner-published source text**, not deployed Pages freshness, exact
submission bytes, organizer receipts, or a current score ranking. Some pages have
no matches for the limited search strings; that is not evidence they have no results.

The GEMSDOE32 champion value in the request remains **OWNER-REPORTED**, not
ORGANIZER-CONFIRMED. Existing `s15_champion_forensic.json` reports that its dots
are the solo file with a catalogue-neighborhood ring deleted. This is archived
forensic evidence, **not a byte-level comparison repeated in this run**. Another
historical review disputes availability of the exact score-linked champion TIFF.
That discrepancy is unresolved here; neither record authenticates the competition
score. The defensible mechanism is a *hypothesis*: removing predictions close to
already-mapped faults can reduce weighted false-positive mass without losing much
hidden-fault credit. It does not demonstrate new fault discovery, and the reported
score differences do not prove that causal explanation. Sparse placement can also
change geometric coverage under a distance-tolerant metric. A higher hidden-test
score cannot be promised from this evidence.

Rechecked the official [DrivenData reference repository README](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md)
through GitHub at that commit. It explicitly supports CPU-only environments and says
GPU training is faster; therefore the prompt's inherited “GPU needed” claim is not
a general requirement. This check does not validate this project's training code.

Official links for review, **not freshly retrieved on this restricted network**:
[competition](https://www.drivendata.org/competitions/306/competition-doe-gems/),
[problem](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/),
[leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/),
[rules PDF](https://docs.nlr.gov/docs/fy26osti/96647.pdf),
[USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and),
[GDR 1391](https://gdr.openei.org/submissions/1391).
Neither conflicting leaderboard maximum in the task is asserted current. No organizer
receipt, live weekly cap, new external dataset coverage, or licence was verified.

## Hypotheses and next experiment

The preceding review already contains four ranked future directions with layers,
physical signature, off-catalogue rationale, novelty caveats, named non-fault mimics
and costs: [review_s17](review_s17_submission_safety_2026-10-25.md).
These are **not new hypotheses generated or validated in this run**. Their asserted
novelty requires cross-site code review; external-data directions are not viable
until official byte access, coverage and terms are checked. Repeating them as “new”
would be misleading. No expected DTI improvement is estimable from available evidence.
No candidate validation took place, so no HOLDOUT-DTI score or confidence interval is
reported for this review. See `s18_run_card.json` for explicit null measurements.

Next session's necessary sequence:

1. Establish one method paragraph and freeze a fresh preregistration, split/seed ledger,
   baseline hash and experiment budget. Do not silently reuse exhausted H40-1.
2. Restore pinned inputs/cache; verify source identity, terms, CRS and footprint.
3. Restore the complete registry, including calibration/probe rasters. If a dense
   registry lattice covers every allowable location within the prescribed distance,
   the literal uniqueness gate may be infeasible. Report that blocker; do not quietly
   exempt the lattice or change the user's threshold.
4. Run per-feature leakage canaries before trusting features; apply the shared
   whole-segment buffered visible-only hide-and-recover evaluator. Require a positive
   predeclared paired gate against the frozen best and versioned HOLDOUT-DTI evidence.
5. Check surface novelty before placement and final-dot novelty against every registry
   member. Stop on a duplicate. A schema success cannot substitute for these executions.
6. Only if all gates pass, write a genuinely new TIFF with the shared writer, reread
   exact bytes against the template, hash it, and expose a named one-click download
   with an explicit automated disposition. Leave real-slot promotion to the selector.

## Pass 2 — bugs and edge cases

Initial tests could not run because pytest was absent. Installed repository requirements
in an ignored virtual environment. Full suite then passed; skipped tests require inputs
not present here. The schema tests now exercise malformed evidence as actual failures
of `evidence_schema_passed`, so forcing readiness false does not make negative tests
vacuous. Tests also verify that self-declared readiness/selector fields cannot authorize
upload. Ruff and whitespace checks pass. Site rebuild uses local JSON with no external
requests; no TIFF bytes were changed.

## Pass 3 — reconciliation and limitations

Final local verification: **319 passed, 7 skipped**; full Ruff clean. Rebuilt the six-page
site and checked deterministic regeneration and `git diff --check`. This is software-test
coverage, not HOLDOUT-DTI or proof of geological correctness. The missing lane, data,
complete registry comparison and fresh holdout remain blockers. No new scientific result,
newly viable external-data hypothesis, qualifying TIFF, or competition upload is claimed.
The full prompt is authoritative; the README update is an operational summary, not a
claim to have transcribed this entire repeated message verbatim. Historical verbatim
briefs remain in README. PR creation/merge is tracked separately via GitHub.
