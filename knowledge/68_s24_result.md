# S24 result — 2026-10-27 UTC

**Decision: NO NEW FILE APPROVED · OK TO DOWNLOAD: NO · OK TO SUBMIT: NO**

This is an automated decision (no human inspector). S24 generated **no new TIFF**, ran **zero holdout experiments** and selected **no weekly slot**. The only computation was a geometry audit of existing files (`GEOMETRY-AUDIT`, not `HOLDOUT-DTI`, not an organizer score).

> **Current policy / separate-session note:** this geometry audit is from a concurrent S24 run, not the active repository-review run. Its A/B/C alternatives and its then-recorded recommendation are analysis only; they do **not** change the user's standing instruction to compare every registry raster and stop on a duplicate. No comparator is excluded and no search/tuning around lattice holes is authorized. The active checkout's disposition and card are [here](68_s24_repository_review.md) and [here](../evidence/s24_repository_review_run_card.json). The public leaderboard values below are that session's `ORGANIZER-PUBLIC` observation, not a file-bound receipt or score estimate, and were not refreshed by this checkout.

Machine-readable record: [`evidence/s24_run_card.json`](../evidence/s24_run_card.json) · overlap evidence: [`evidence/s24_nine_site_overlap.json`](../evidence/s24_nine_site_overlap.json) · reproduce: `python scripts/audit_s24_nine_site_overlap.py`

---

## 1. Why no unique file can be approved right now (the blocker is a rule conflict)

The protocol's lane rule says a raster is a duplicate if **more than 70 % of its dots lie within 3 px of one registry raster's dots**. The registry includes the calibration lattice `13gems_20261001_r13-lattice-s5_v2_nan-outside.tif` (GitHub pin `GEMSDOE24@07345ea`, sha256 `b4570b40…`).

Verified numbers (re-computed this session, not copied):

| Check | Result | Source |
|---|---|---|
| Lattice 3 px coverage of the 5,167,373-cell footprint | **99.87 %** (206,895 lattice dots) | `evidence/s23_registry_feasibility.json` (re-derived here) |
| Cells not within 3 px of any lattice dot | **6,649** | same |
| Dots a 37,654-dot file would need outside the lattice to pass (≥30 %) | **11,297** — impossible (only 6,649 cells exist) | counting bound |
| Each of the nine historical best files vs the lattice | **99.91–99.92 %** overlap | `s24_nine_site_overlap.json` |

So the rule as written **cannot be passed by any dense file without placing dots deliberately into the 6,649 uncovered cells**. The repo's own module (`src/gems27/registry_feasibility.py`) forbids that tuning: *"a duplicate lane must stop, not tune."* Every historical file in the nine sites is therefore a duplicate under this rule, and so would be any new file of comparable budget. The lattice is a space-filling **calibration control**, not a submission, which is why it does not discriminate well.

Against the **nine real historical submissions only** (lattice excluded), the rule is satisfiable in principle: each file covers only **15.1–18.5 %** of the footprint within 3 px, and the union of all nine covers **19.6 %**. Hence the user must decide which comparator set counts. See section 5.

## 2. Nine-site re-verification (line by line, from pinned GitHub bytes)

All nine best files were re-fetched through `gh api` at the commit recorded in `docs/data/s23_scorecard.json` and hashed (`evidence/s24_nine_site_overlap.json`).

| Site | Best file (what the scorecard pins) | Dots in footprint | Dots on catalogue | Dots ≤2 px of catalogue | Median catalogue distance (px) | User-reported claim |
|---|---|---:|---:|---:|---:|---:|
| GEMSDOE24 | gems24-h25-1-dotted-h19-5-d1-5-…-allfinite.tif | 60,069 | 0 | 8,769 | 14.9 | 0.2477 |
| GEMSDOE25 | gems25-dotted-h19-5-d2-8-…-zeros.tif | 44,090 | 0 | 6,436 | 15.0 | 0.2600 |
| GEMSDOE27 | gems27-topo-gap-closure-t-v2-on-d1-5-…-allfinite.tif | 61,328 | 0 | 8,875 | 14.1 | 0.2449 |
| GEMSDOE28 | gems28-h36-1-rung30-blind-r1-…-allfinite.tif | 37,660 | 0 | 2,353 | 17.7 | 0.2710 |
| GEMSDOE30 | gemsdoe30-d28-poisson300m-offcat-44090-…tif | 44,090 | 0 | 6,436 | 15.0 | 0.2600 |
| GEMSDOE31 | gemsdoe31-h27-4-solo-d28-…-allfinite.tif | 40,199 | 0 | 2,545 | 17.7 | 0.2708 |
| **GEMSDOE32** | gemsdoe32-h33-h33-2-b2-…-zeros.tif | **37,654** | 0 | **0** | **19.6** | **0.2778** |
| GEMSDOE33 | GEMSDOE33-h33d-analog-tip-stepover-r30-…tif | 41,865 | 0 | 3,894 | 16.6 | 0.2632 |
| GEMSDOE36 | gemsdoe36-anderson-geothermal-pinn-38854-…-zeros.tif | 38,854 | 0 | 0 | 19.2 | 0.2750 |

Verified exact set relations (boolean arithmetic on the fetched bytes):
- **GEMSDOE32 ⊂ GEMSDOE31**, with exactly **2,545** GEMSDOE31 dots removed. Those 2,545 are exactly GEMSDOE31's dots within 2 px of the catalogue.
- **GEMSDOE32 ⊂ GEMSDOE36**, with **1,200** extra dots in GEMSDOE36.
- **GEMSDOE25 and GEMSDOE30 have identical dot sets** (both 44,090 dots; overlap 1.0).
- All **72 directional pairs** of the nine exceed the 70 % overlap rule (max 1.0 = GEMSDOE24→GEMSDOE25 etc.). This matches the S23 audit.

No pairwise sha256 or dot-set equality exists between any of the nine except the GEMSDOE25/30 pair (their raw file hashes differ, only dot sets match).

## 3. Why did GEMSDOE32 (0.2778, user-reported) score highest? — answer and confidence

**Verified structure:** GEMSDOE32 is GEMSDOE31's emission with its catalogue-adjacent dots (≤2 px) deleted. It has **zero** dots within 2 px of the catalogue, and its median catalogue distance is the largest of the nine (19.6 px).

**Mechanism (metric-based reasoning, not measured against hidden labels):** Under the official DTI (`https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/`, fetched 2026-10-27), each dot adds credit `k(d)` to TP only where the hidden truth lies within 3 px, and adds FP cost `(1 − k)` otherwise. Removing a set of dots raises DTI exactly when their marginal efficiency `dTP/dFP` is below the threshold `0.2·DTI/(1−0.2·DTI)`. The repo's `metric.inclusion_threshold` gives **0.0588** at DTI 0.2778 (0.0573 at 0.2708). A catalogue-adjacent dot is plausibly low-efficiency, because new (hidden) faults are less likely to sit exactly on mapped ones. Deleting 2,545 such dots therefore plausibly raises DTI. This is a **hypothesis consistent with the arithmetic**, not a measured fact.

**Confidence and limits:**
- The 0.2778 value is **USER-REPORTED / UNVERIFIED**. No organizer receipt binds it to this file.
- The hidden-truth efficiency of those 2,545 dots is **unknown**. The local holdout cannot test it, because its truth is catalogue-internal (flagged in `src/gems27/holdout.py`).
- Whether the organizer masks catalogue pixels is **not stated in the official text** (fetched page). All nine files have zero dots on catalogue, which suggests the owners assumed masking. This is flagged as an irregularity (section 6).

**Can we beat 0.2778?** Unknown. The only way to beat it is a method whose extra dots clear the same efficiency bar on the hidden truth. Nothing validated does that, and no holdout run in S24 tested it. Projecting a score would be a fabrication, so none is given.

## 4. Official public leaderboard (fetched 2026-10-27, approx. 18:50 UTC)

Source: <https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/> (public "best DW-Tversky" column, top 50 shown).

- **#1 = 0.4544** (xiaofanhu), **#2 = 0.3916**, **#25 = 0.3195** (kpomazi), **#50 = 0.2857**.
- The user's **0.4413** does not appear on this page. The repo's **0.4437** (2026-10-26) is stale.
- The user's "0.3195 is the highest right now" is **incorrect**: it is rank #25.
- A 0.2778 score, if real, would sit **below rank 50** on the public board.

This is an **ORGANIZER-PUBLIC leaderboard observation**, not a submission receipt. Private-set scores can differ.

## 5. Comparator-rule conflict (historical options; no alternative adopted here)

This section records options considered in that concurrent session; it is not a request for a manual choice and does not authorize a local protocol change. The active instruction requires every registry raster to be checked and duplicates to stop. The literal rule therefore remains controlling here; any change would require an explicit shared, versioned protocol decision. The calibration-lattice calculation is documented as GEOMETRY-AUDIT, not an excuse to omit a comparator or tune holes.

- **A. Keep the literal rule, lattice included.** Result: no dense file can ever be approved. Expected output: none.
- **B. Exclude the calibration lattice (it is a control, not a submission) and compare against real submissions only.** Result: the nine real files cover 15–18 % each, so a new file with ≥30 % of its dots outside every one of them is geometrically possible. It must still pass a pre-registered holdout (≤3 experiments, ≤2 h) before any slot selection.
- **C. Use the exact-copy rule only.** Result: any new byte-distinct file is "unique". Risk: a near-copy with a relabel would pass. Not recommended.

The prior session recorded B as its research recommendation. **That recommendation is not adopted on the active branch and has no operational effect**; no alternative comparator set is in force.

## 6. Irregularities flagged for review

1. **Lattice control makes the rule non-discriminating:** 99.87 % coverage, and every historical file scores 99.9 % against it. See section 1.
2. **Comparator/rule conflict** (section 5).
3. **Leaderboard anchors conflict:** 0.4413 (prompt) vs 0.4437 (repo, 2026-10-26) vs 0.4544 (live page, 2026-10-27). The "0.3195 highest" claim is rank #25.
4. **Masking assumption unverified against official text.** The local metric and the owner files assume catalogue pixels are masked. The official page does not say so.
5. **User-reported scores have no organizer receipts.** They are not verified and carry no estimated leaderboard value.
6. **Portal error cause unknown.** The "Predicted values must be in range [0, 1]" message is not reproduced here. The official sample uses NaN outside the footprint; the writer in `src/gems27/submission.py` follows that, and the zeros/allfinite variants are fallbacks.
7. **Site not rebuilt.** `docs/index.html` still shows the S23 decision and the 0.4437 observation. Rebuilding would touch a 1,448-line generator and was not done in S24.
8. **Historical format audit** (S23: 2 legacy nodata-tag failures) was not re-run in S24.

## 7. Score-estimate table (for the executive summary)

| Site | What to download | Estimated leaderboard score | Unique vs the other eight? | OK to download and submit? |
|---|---|---|---|---|
| GEMSDOE24 | pinned best file (section 2) | **Not estimable** (user claim 0.2477, unverified) | No (72/72 pairs >70 %) | **NO** |
| GEMSDOE25 | pinned best file | **Not estimable** (0.2600, unverified) | No (identical dots to GEMSDOE30) | **NO** |
| GEMSDOE27 | pinned best file | **Not estimable** (0.2449, unverified) | No | **NO** |
| GEMSDOE28 | pinned best file (h36-1) | **Not estimable** (0.2710, unverified) | No | **NO** |
| GEMSDOE30 | pinned best file | **Not estimable** (0.2600, unverified) | No (identical dots to GEMSDOE25) | **NO** |
| GEMSDOE31 | pinned best file | **Not estimable** (0.2708, unverified) | No | **NO** |
| GEMSDOE32 | pinned best file (highest claim) | **Not estimable** (0.2778, unverified) | No | **NO** |
| GEMSDOE33 | pinned best file | **Not estimable** (0.2632, unverified) | No | **NO** |
| GEMSDOE36 | pinned best file | **Not estimable** (0.2750, unverified) | No | **NO** |
| **New S24 file** | **none generated** | — | — | **NO** (blocked by the rule, section 5) |

"Not estimable" is deliberate: no validated calibration maps holdout DTI to the hidden score, and no organizer receipt exists.

## 8. Next work, in priority order

1. Keep the active literal all-registry stop in force. Any protocol change must be explicit, shared, versioned, and authorized; do not exclude the lattice or tune around its holes.
2. Only after an explicit shared, versioned rule change is authorized, the assigned lane and all preflight gates pass: preregister one mechanism with a hard budget and holdout gate. Candidate families already ranked in `registry/s23_hypotheses.json` (PCSE, TCB, MCR, CSD) remain unimplemented.
3. Verify the masking convention against the official rules PDF (`https://docs.nlr.gov/docs/fy26osti/96647.pdf`) and the competition rules page, then record the result.
4. Rebuild the site so the official 0.4544 observation and the S24 decision are shown at the top.
5. Re-run the S23 format audit once a file is chosen.

## 9. Verification performed

- Inputs restored from the hash-pinned owner mirrors (`scripts/restore_data.py --group core`): training features 418,912,844 bytes, sha256 `4371c82e…`; labels and existing faults 425,830 bytes, sha256 `7ba308cc…`; sample submission 1,599,597 bytes, sha256 `2176d08e…`. All matched the pins in `registry/data_manifest.json`.
- `pytest`: 642 passed, 5 skipped (documented skips), plus the 3 new S24 tests (645 total passing, 5 skipped). `ruff check src scripts tests`: clean.
- Official metric re-derived from the fetched worked example: 3.00 / (3.00 + 0.2·1.89 + 0.8·2.00) = 0.6027, matching the published 0.60 to rounding.
- All numeric claims above come from the scripts and evidence files named in each section. Anything not measured is labelled.
