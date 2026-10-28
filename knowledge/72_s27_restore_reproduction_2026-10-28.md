# S27 · restore, reproduce, verify — 2026-10-28 UTC

**Branch:** `arena/123dd6aa-gemsdoe28` · **Run card:** [evidence/s27b_run_card.json](../evidence/s27b_run_card.json)

## Decision (read this first)

| Question | Answer |
|---|---|
| New unique TIF generated this session? | **No.** A new raster would bypass the protocol gates (see below). |
| Can the existing S25 TIF be submitted? | **No.** Unique under the 51-file scope, but its holdout score is below a random-placement control. |
| Can the existing S25 TIF be downloaded? | **For research/audit only.** |
| Is a leaderboard score estimate available? | **No.** Holdout values are not calibrated to the leaderboard. |

## What changed in S27 (verified)

1. **Blocker removed: the inputs now restore.** The earlier notes said the data could not be obtained. In this sandbox, `scripts/restore_data.py --group core` and `--group model`, plus `scripts/restore_protocol_assets.py`, all completed. Every file matched its pinned SHA-256. The mirrors are owner-supplied GitHub copies, **not organizer-authenticated**. DrivenData was not contacted. Hashes are in the run card.
2. **Pipeline reproduces.** `scripts/run_s25_pcse.py`, run in a scratch copy, gives the committed values exactly:
   - HOLDOUT-DTI (gems-segment-pooled-v1) 0.0450361, 60,988 withheld positives, 95% CI [0.0380288, 0.0525190]
   - Random-K control 0.0698748, 95% CI [0.0666809, 0.0731446]
   - TIF SHA-256 `c6d722971070f6624a9b2a374c2858db46137f64dcd74805f160ba13f179edef`, identical to the committed file.
3. **Bug fixed.** On rerun the novelty scan included the candidate's own output file, reporting overlap 1.0 and a false duplicate. The script now computes the output name first and skips it. After the fix the scan reproduces the committed novelty values: overlap 0.4437, max |rho| 0.0618, 51 files compared, no duplicate.
4. **Tests.** `pytest`: 664 passed, 5 skipped (up from 662 passed / 7 skipped). `ruff`: clean.

## Exact-file audit (restored inputs)

`scripts/verify_downloads.py` now runs against the restored sample template: 869 checks, **2 failures**, both on archived historical all-finite variants that carry a NaN nodata tag (`s22_archive_h40_vent` and `s22_archive_h41_spring`). Both are archive-only and DO NOT SUBMIT. They are flagged, not rewritten, because their bytes are hash-bound. The S25 PCSE TIFF passes its checks and is registered in the sibling research manifest. Evidence: [evidence/s27b_download_audit.json](../evidence/s27b_download_audit.json).

## Official leaderboard check (replaces the quoted numbers)

Source: [public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/), fetched 2026-10-28.

- **#1 = 0.4544** (xiaofanhu). The prompt's "current high 0.4413" does not appear on the page.
- **#9 = 0.3404**, **#26 = 0.3195** (kpomazi), **#27 = 0.3169**.
- The public board uses the **public** test subset. The Initial Prize Round is scored on a **private** subset, and the Final Round is rescored on an expanded label set. A public rank is not a prize rank.

To reach "beat 0.3195" on the public board, a submission must reach roughly the top 25.

## Metric check against the official page

Source: [problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/). The official definition is DTI(α=0.2, β=0.8) with a triangular kernel of range R = 300 m. The repo's shared evaluator matches on these parameters. The official submission rules allow probabilities in [0,1], and NaN or null outside the bounds. Both are satisfied by the existing file.

## Hypotheses and why nothing new was run

- The preflight gate (`scripts/check_run_preflight.py`) is BLOCKED for four reasons: no assigned method lane, no complete synchronized registry, no frozen same-protocol best, and an expired experiment clock. These are real gaps. The user's protocol paragraph does not name a lane, and I did not invent one.
- Running an untested operator just to produce a new file would be the kind of unvalidated submission the protocol forbids.

## Irregularities flagged for review

1. Holdout values (about 0.05–0.07) are far below public leaderboard values (0.20–0.45). The holdout is not calibrated to the leaderboard.
2. Random-K beats PCSE on the holdout. This is unexplained.
3. Old GEMSDOE submissions were built with the full catalogue visible, so evaluating them on this holdout is not a clean test.
4. The prompt's 0.4413 top score is not on the live board. Its 0.3195 is at #26.
5. GEMSDOE24–36 scores are user-supplied and unverified.

## Next steps

1. Assign a method lane explicitly, and authorize a new session clock in a session record.
2. Diagnose the random-K vs PCSE anomaly before proposing a new operator.
3. Test graded (non-binary) confidence. The official DTI accepts probabilities in [0,1], and FP/FN weighting makes soft confidence a distinct lever from binary dots. Validate on the holdout before any slot.

## Sources

- [Problem description and metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Competition data tab (login required)](https://www.drivendata.org/competitions/306/competition-doe-gems/data/)
- [Reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [EPSG:32611](https://epsg.io/32611)
