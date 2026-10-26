# Session 20 — validation hardening (2026-10-26 UTC)

## Executive decision

**No new TIFF; DO NOT SUBMIT the rejected research downloads.** The existing
[nine-site executive summary](../docs/cross-site-review.html) remains the comparison:
GEMSDOE32 has the highest *user-reported, unverified* value in the supplied list.
No submission-page receipt was obtained in this session. No claim of outperforming it is made.
The ranked four-hypothesis slate remains in `55_session19_cross_site_review.md`;
no assigned lane or valid new scientific experiment was available.

## Pass 1 — implementation

Reviewed README, prior negative results, preflight, promotion gate, website builder,
CI, and tests. Found that preflight verified the cached stack's hash/shape/type but
not finite contents. Added an exhaustive chunked finite check; hashing a NaN-bearing
cache no longer makes it acceptable. Shared evidence JSON parsing now rejects duplicate
keys, NaN/infinity literals, and valid JSON exponents that overflow to infinity.
Both promotion and preflight use this same parser; preflight also uses it for
registry, baseline, and cache metadata. No shared scientific evaluator was changed.

## Pass 2 — regression review

Added synthetic tests for last-cell NaN, positive/negative infinity, ambiguous
nested keys, and overflowing numbers. Full suite exposed a historical evidence
hash binding to the old preflight script. Preserved that exact script as
`evidence/snapshots/pr39_check_run_preflight.py` and pointed only the historical
hash assertion to it. Did not rewrite historical run-card hashes or results.

## Pass 3 — requirements recheck

Rebuilt the site without generated-page drift. Ran the hardened preflight against
the existing configuration; its blocked output is `evidence/session20_preflight.json`.
The old configuration's elapsed-budget failure refers to its historical start time,
not time consumed by this review. Additional actual blockers: absent cache/shared
assets, no lane assignment, no complete registry, no comparable frozen baseline.
No training, feature canary, holdout, surface/dot comparison, or raster validation
was claimed. No weekly submission slot was selected or used.

## Next work, in dependency order

1. Restore hash-pinned shared tools and feature cache using the existing restoration
   scripts. GitHub mirrors verify byte identity, not independent official provenance.
2. Synchronize the complete parallel-run registry; do not silently restrict it to
   scored candidates. Assign one method from the existing ranked slate and freeze it.
3. Establish a same-protocol frozen best, fresh unspent holdout seeds, and a new
   explicit session budget. Run feature-alone canaries before candidate experiments.
4. Emit a unique all-finite [0,1] TIFF only after the preconditions permit research;
   require positive paired holdout improvement, both uniqueness checks, and exact-grid
   validation before a separate selector can consider a slot.

Network access here is restricted to GitHub and package registries. This session
did not freshly verify DrivenData, USGS, GDR, or the rules PDF. Existing source links
are review references, not new source observations. No organizer receipt or
current authenticated submission allowance is available.

Verification: **493 passed, 6 skipped** (input-dependent checks), Ruff PASS,
site build PASS with no generated-page drift, `git diff --check` PASS.

## Concurrent-main reconciliation

During the requested PR merge, main advanced with the independent S19-ASCP run.
Merged it into this working branch and preserved its generated research TIFF and
negative scientific verdict. This review's missing-input observations describe its
original local checkout, not a claim that the concurrent run lacked data. The
S19-ASCP report and website are now the latest scientific result. No evidence was
pooled across runs and neither negative verdict was promoted.

Post-merge verification: **499 passed, 7 skipped**; lint and site rebuild PASS.
