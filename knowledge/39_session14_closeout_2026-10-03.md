# Session 14 close-out — H38-1 support, single-use attempt, analyzer failure

**Run date:** 2026-10-04 UTC (2026-10-03 America/Los_Angeles). **Branch:** `arena/01a10412-gemsdoe28`.
**Outcome:** the frozen LOSFO runner completed all 20 H38-1 cells on seeds 265–269 and wrote a raw artifact; the frozen analyzer then failed while serializing the report. There is no C1–C5 gate decision. The seeds are burned, no rerun or re-analysis is permitted under the preregistration, and no submission TIFF, upload, promotion, or weekly slot was used.

## 1. Frozen scientific work and evidence boundaries

Session 14 first ranked five exact geological rules in `knowledge/37_ranked_hypotheses_session14_2026-10-03.md`, before implementing H38-1. The planning ranges are subjective, risk-adjusted priors with zero included—not holdout or leaderboard predictions. H38-1 combines shallow SI-0 Euler depth-coherent clusters, a nearby independent gravity-gradient edge, and low *valid* LiDAR relief. H38-2 through H38-5 remain queued behind local bytes/schema/coverage checks. The official links and their listing-versus-local-data limitations are recorded in `knowledge/37`, `registry/sources.json`, and `README.md` §3.9c.

The label-free H38-1 candidate builder selected **140 of 1,435** depth-eligible SI-0 clusters (9.76%), with fixed gravity P80 `1.460558295249939` and valid-relief P50 `44.0`. These counts establish support only. They do not establish fault identity, catalogue omission, LOSFO benefit, organizer-label recovery, or a competition score. Candidate CSV SHA-256: `2e5c607affa635418c90a520ef843494a4fb00fb7e7d69f63fb317c73849d369`; sufficiency-audit SHA-256: `91d86b012fcbfa472ff79859623743e1292a077d591427e78bf8627a92250b60`.

The score context remains conditional. `0.2600` is an owner-reported score/file association; repository hashes authenticate local bytes, not an organizer receipt or account association. `0.3195` is the repository's one-off 2026-10-03 observation of an organizer-hosted public leaderboard row, not a verified link to an identity or TIFF and not freshly fetched in this session. The reverse-engineered `~1,151` weighted-credit gap at the 44,090-dot budget makes beating that value mathematically plausible only through materially better off-catalogue detection; this session produced no valid H38-1 performance decision and no evidence that a local candidate can do so.

## 2. Freeze, seed audit, and single-use run chronology

1. **Protocol freeze:** commit `cf1d03627ad3f863d10ff34e5195f126efad51f5` froze the H38-1 definition, builder, analyzer, tests, gates, and runtime/input-hash requirements; it was pushed before seed inspection. The full protocol is `knowledge/38_preregistration_H38-1.md`.
2. **Local audit and reservation:** `scripts/prepare_h38_1_seed_claim.py` returned `RESERVED` and wrote `evidence/h38_1_seed_audit_pre_run.json` plus `evidence/h38_1_holdout.started.json`. The audit reports `PASS_LOCAL_SCAN`, 61 local evidence JSON files scanned, zero references/collisions, and zero unreadable files (audit SHA-256 `413cc522519a394e06d826eacccc11262c0653890659d9e94c550f5c0e91394e`). It is expressly local-only; the Git repository is shallow and the audit cannot rule out other repositories, owner workspaces, or unpublished runs. The reservation artifacts were committed at `eb28c4a` and pushed before execution.
3. **Single invocation:** the wrapper ran once with `GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_h38_1_holdout.py` on `arena/01a10412-gemsdoe28`. Its recorded run commit is `9880ca6d84a3527b2baeaa28b8d2a00be13edcde`. Seeds 265, 266, 267, 268, and 269 each completed; the raw file records 20 cells, the fixed 3-pixel dilation/6-pixel buffer/2.8-pixel spacing, and a minimum 8-pixel far-field separation. The raw file is `evidence/losfo_h38_1_raw.json`, 31,964 bytes, SHA-256 `0375a9e58ed9dc43f6dddecb431644a18e10b39e42219ed491ede530dbf5a4ba`.
4. **Analyzer failure:** `scripts/analyze_h38_1_holdout.py` exited 1 while JSON-serializing its report: `TypeError: Object of type int64 is not JSON serializable`. The wrapper correctly recorded claim status `FAILED`, `runner_exit_code: 0`, `analyzer_exit_code: 1`, `seed_range_burned: true`, and the raw-result hash. No `evidence/h38_1_holdout.json` was written; there is no saved C1–C5 decision. Final claim SHA-256 after the failure detail was added: `1bd9bd5e3e4c2c4861a34f4b1714e7b89e36f73b8dd6f3bb8e819768163a3791`.

This is an **analysis-infrastructure failure, not a scientific pass or refutation**. Although the raw record exists, the frozen rule says an analyzer/run failure burns the decade and forbids rerun or repair against those seeds. The raw per-cell candidate fields are therefore preserved as provenance, not retroactively promoted into a gate result. Do not run the wrapper again, do not process this raw record into a C1–C5 promotion decision, and do not spend a weekly slot. H38-1 is closed as **not evaluable** on this attempt.

After the error, `scripts/analyze_h38_1_holdout.py` received a generic JSON serialization guard for NumPy scalars/arrays, with a synthetic regression test. This post-run correction is for future work only: it was **not** used to generate an H38-1 summary, alter the raw file, or make a decision on seeds 265–269. The frozen analyzer bytes remain identifiable by the claim's code hash and freeze commit.

## 3. Submission file, score, and slot status

The site's first-screen primary remains the previously audited H36-1 GeoTIFF; H38-1 produced no TIFF. `scripts/verify_downloads.py` passed **217/217** local checks with zero failures: the files are single-band float32 on the exact `EPSG:32611`, `3730 × 3292`, 100 m template grid, inside-footprint values are finite and in `[0,1]`, catalogue overlap is zero, and each submission name is unique/content-linked with a note no longer than 200 characters. This local verification does not authenticate the organizer's inputs or guarantee portal acceptance. No DrivenData login, request, upload, score query, or submission was made. No weekly slot was used.

The README and generated site preserve the distinction among owner-reported `0.2600`, the one-off public leaderboard observation `0.3195`, and local research evidence. The site now presents the `FAILED` claim, the support-only boundary, the pre-run audit and the unverified raw artifact; it does not display a fabricated H38-1 gate score.

## 4. Three review passes

### Pass 1 — implement and verify

- Read the complete standing brief in `README.md`; recorded five ranked hypotheses and official-source availability/data gates before implementing H38-1.
- Implemented the label-free candidate builder, frozen LOSFO extension, one-use claim/audit/wrapper, analyzer, and integrity-focused tests. The protocol freeze was committed and pushed before the local seed audit.
- Candidate build returned `READY` with 140 rows. The local seed audit returned `PASS_LOCAL_SCAN`; the reservation was committed/pushed before the single runner invocation.
- Data restoration/preparation was attempted autonomously through the existing hash-pinned owner-mirror path; no DrivenData login or request was made. `evidence/restore_audit.json` reports `PASS: local hashes, grid, band order, and prepared matrix verified`. The prepared 32-feature matrix is `5,167,373 × 32` on `EPSG:32611`; metadata binds it to the template, training features, LiDAR products, and labels. These mirrors are not organizer-authenticated.
- Before the run, the full suite passed **248 tests, 2 skipped**, `ruff check .` passed, submission-file audit passed **217 checks**, and the static site built five pages from JSON with five Session 14 hypotheses and no external requests.
- The runner completed on all five seeds. The analyzer serialization failure was recorded exactly; no gate result was claimed.

### Pass 2 — inspect and fix defects/edge cases

- Before freeze, review found and fixed an input-binding omission: the claim now hashes `data/labels.tif` and both `data/prepared/features.npy` and `data/prepared/features.json`, in addition to the template, raw feature/LiDAR rasters, candidate evidence, and benchmark. Thus the truth raster and exact feature matrix used by the LOSFO fit are bound to the reservation.
- Added per-cell DTI recomputation from weighted TP, FP and truth counts; matched-count/overlap/far-field checks; site integrity handling; raw/audit workflow triggers; and unique submission-name/content-ID validation. Synthetic tests cover malformed results and edge cases.
- Runtime review found the frozen analyzer's NumPy-scalar JSON serialization defect. The range remains burned. A post-failure generic serializer fix is tested only on synthetic data and is not used to derive an H38-1 result. The site renders the claim as failed/unverified and links the preserved raw record.
- Resolved a historical arm-ID collision: this Session 14 H38-1 is the Euler × gravity × low-relief hypothesis, not the parallel directional-thinning experiment. Any future directional revival must receive a distinct later ID and a new protocol.

### Pass 3 — check the whole request and preserve remaining work

- The README still contains the full standing prompt. The ranked geological hypotheses name layers, physical signatures, catalogue-omission rationale, difference from prior rules, planning-only expected ranges, cost, source availability and key confounders.
- `0.2600` is explicitly labeled owner-reported and conditional; `0.3195` is labeled as a dated observation from the organizer-hosted public page without identity/file linkage. No local proxy is called a competition score.
- A valid single-band GeoTIFF remains prominent at site arrival with a unique content-linked name, a ≤200-character note, exact-grid/range/mask audits, and manual submission instructions. H38-1 was not promoted because no valid gate decision exists.
- The pre-run audit's scope limitation, the single-use failure, absent summary, raw hash, and no-rerun rule are recorded in the claim, this close-out, `README.md`, and `registry/irregularities.json`. Remaining work is a *new* preregistered scientific test on a fresh range after a review of the analyzer; never reuse 265–269.
- Final close-out verification after the post-run serializer fix, failed-claim status, and AI-disclosure/site-link updates: **250 passed, 2 skipped** (`.venv/bin/python -m pytest -q`), `.venv/bin/ruff check .` passed, `scripts/verify_downloads.py` passed **217/217** with zero failures, the five-page JSON-only site build reported zero external requests, and `git diff --check` plus JSON parsing checks passed. No holdout wrapper or analyzer was run against the H38-1 raw artifact during this verification.

## 5. Remaining limitations

- There is no valid H38-1 gate result. The raw per-cell artifact does not authorize a scientific conclusion under the frozen protocol after the analyzer failed.
- The seed collision scan covered only the 61 JSON files present in this shallow checkout; it cannot establish global non-use.
- Competition inputs and derived layers are local owner-supplied mirrors, hash-pinned but not organizer-authenticated. Official catalog listings are not local clip/coverage/schema validation.
- The reported `0.2600` score/file association is not backed by an organizer receipt. The `0.3195` public row was not re-fetched this session and is not tied to an owner identity or local file. No GEMSDOE28 artifact has an organizer score.
- GitHub Pages had a previously recorded legacy/workflow configuration irregularity; the repository retains a raw-repository download fallback. Check the current deployment manually before relying on the hosted page.
- Generative AI assisted this work. This close-out adds `AI_DISCLOSURE.md` as a disclosure aid after review found the path referenced by the registry was missing. Include an AI-use statement in the final competition narrative, as required by the official rules; the file is not a substitute for that narrative disclosure.
