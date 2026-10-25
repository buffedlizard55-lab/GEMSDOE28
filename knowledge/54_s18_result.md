# S18-MXTP result — unique TIFF, NEGATIVE performance gate

**Read before the historical README. 2026-10-25. Three experiments used; arm closed.**

## Download and disposition

New output: [`gems28-s18-mxtp-20261025-3e95505c011a-allfinite.tif`](../docs/downloads/gems28-s18-mxtp-20261025-3e95505c011a-allfinite.tif).

- **Download for reproducibility: YES. Submit to competition: NO.** This is a newly generated,
  independently placed research raster, not copied or pruned from a previous submission.
- Name: `GEMSDOE28-S18-MXTP-3e95505c011a`.
- Note: `S18 MXTP: extrapolated TMI/gravity ridges; 11082 dots; holdout rejected; research only; DO NOT SUBMIT.`
- SHA-256: `ce043566a96a1bf0abae366ba706ed6be5907297248b1d14deace8596500b186`.
- Automated exact-file checks: all pass. One float32 band; 3,730 × 3,292; EPSG:32611;
  transform `[100,0,243350,0,-100,4508550]`; whole array finite and in [0,1]; no NaN
  inside footprint; zero catalogue predictions; 11,082 dots. Zeros outside the irregular footprint.
- These are local checks against the pinned owner-mirror template, NOT organizer authentication
  or a guarantee of portal acceptance. The previous portal range error's actual cause is still unknown.
- The official format text says null/NaN outside bounds. The zero-outside-footprint file is a
  compatibility variant; no claim is made that it supersedes the official format or has been accepted.

## Why the reported GEMSDOE32 leader improved

Fresh educational forensic verification, not just reliance on prior notes:
[`evidence/s18_champion_forensic.json`](../evidence/s18_champion_forensic.json).

The `e5eb6e7e-zeros` raster (hash `c55bafc4…`) is exactly solo-r1 minus the ≤200 m
catalogue-distance ring: **2,545 deleted dots; zero added; zero reconstruction difference**.
Solo-r1 is itself d2.8 minus the ≤100 m ring. GEMSDOE30's referenced file has the same
dot set as d2.8; GEMSDOE31's solo equals the local solo; GEMSDOE36's file contains the
GEMSDOE32 dot set plus 1,200 dots. All nine requested sites have pinned source links,
file hashes and measured dot counts in the forensic JSON and the S18 website table.

**Evidence labels:** the user-supplied associations 0.2477, 0.2600, 0.2449, 0.2710,
0.2708, 0.2778, 0.2632 and 0.2750 are *unverified owner-reported context*, not local
measurements, not ORGANIZER-CONFIRMED. No submission-page receipt was obtained.
We retain the claims for audit rather than falsely reclassifying them as authenticated scores.
GEMSDOE32's available audit JSON itself calls its artifact UNSCORED.

**Mathematical explanation, conditional on the reported ladder:** for binary predictions,
`DTI = TP / (0.2*(TP+FP) + 0.8*|G| + epsilon)`. Removing dots with negligible truth
credit reduces FP at little TP cost, raising DTI. The byte-level construction proves pruning;
it does not prove those deleted dots had zero credit on private expert labels. The best-supported
interpretation is **emission hygiene rather than a new detector**. It is not defensible to claim
receipt-linked causation or predict a better organizer score by extrapolating this ladder.

The official metric equations support this algebra:
[DrivenData problem description, performance metric](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/#performance-metric).
A dated public leaderboard observation on 2026-10-25 displayed xiaofanhu first with 0.4413;
it is **not a submission receipt**, does not identify the owner, and does not authenticate any
local raster. The older 0.3195 snapshot is not the current observed leader.

## Frozen method, canary and uniqueness

[`knowledge/52_s18_preregistration.md`](52_s18_preregistration.md) was written before outputs.
The prompt omitted its promised exclusive method paragraph; we autonomously adopted the
repo's recommended next step (knowledge/50–51), and disclose that exclusive lane authorization
was not confirmed. `S18-MXTP` avoids the existing parallel H40 naming collision.

Only cached physical TMI and isostatic gravity columns were used. Shared Fourier continuation
at 1/2/3 km, shared HG ridge NMS, three-height linearity consistency and q0=2q1−q2
produced a new placement pool, not an augmented GBDT re-emitting its old ridges.
No old submission pixels or registry-based avoidance filter entered the candidate.

Experiment 1 feature-alone leakage diagnostics (ROC-AUC, **not DTI**), LOSFO seed 310,
14,681 withheld positives and 250,000 sampled negatives:

| Feature | AUC | max(AUC, 1−AUC) |
|---|---:|---:|
| TMI extrapolated surface | 0.49414 | 0.50586 |
| Gravity extrapolated surface | 0.49661 | 0.50339 |
| Combined maximum | 0.49214 | 0.50786 |

No canary exceeds 0.90. Near-chance AUC is **not evidence of useful discrimination**.

Registry: 167 unique-byte entries acquired; 166 matched submission grids, one explicitly
excluded 32 × 48 format-test fixture. Snapshot covers the nine requested repositories'
`docs/downloads`, `submissions`, `archive/legacy_candidates`, plus pre-run local downloads.
It is not every TIFF ever produced by every parallel session. Commits, aliases, byte hashes,
exclusion and acquisition completeness are retained in
[`evidence/s18_registry_snapshot.json`](../evidence/s18_registry_snapshot.json).

Exact full-footprint Spearman uses midranks, not a random sample. Proximity is the directed
fraction of candidate support/dots ≤3 px from positive registry pixels. No threshold was changed.

| Stage | Max Spearman vs any member | Max overlap ≤3 px |
|---|---:|---:|
| Pre-placement surface, support ≥0.25 | 0.02445 | 37.31% |
| Experiment 2 final dots | 0.00569 | 38.74% |

All comparisons passed the >0.90 / >70% duplicate-stop limits. Full per-member tables are in
[`evidence/s18_stage_result.json`](../evidence/s18_stage_result.json). A new file hash alone
was never accepted as proof of uniqueness.

## Experiment 3 — frozen buffered LOSFO comparison

**HOLDOUT-DTI**, evaluator `scripts/run_losfo_harness.eval_set v2 → src/gems27/metric.dti_binary`,
hash bundle in [`evidence/s18_holdout.json`](../evidence/s18_holdout.json).
Whole fault systems hidden globally with a 600 m buffer; four geographic quadrants;
seeds 310–314; 20 cells; **76,869 pooled withheld-positive pixels**, **45,155 unique**
(withheld samples overlap across seeds). The unique count must be read from the JSON if this
report and a recomputed artifact ever differ; automated regression tests enforce it.

Only visible faults are used in catalogue-based placement masks and baseline training.
Visible pixels are masked exactly; truth-to-visible separation exceeds 6 px in every cell.
Pooled DTI uses α=0.2, β=0.8, 300 m triangular kernel. Confidence intervals are percentile
bootstrap of FOUR geographic fold blocks, keeping all repeated seeds with each sampled fold
(10,000 draws), not a falsely independent 20-cell bootstrap.

| Arm | HOLDOUT-DTI | 95% CI |
|---|---:|---:|
| New S18 extrapolated placement | 0.02038394 | [0.01643786, 0.02472854] |
| Registered prior H38-1 recipe, recomputed on visible-only labels | 0.10823856 | [0.08344478, 0.13182990] |
| Paired pooled gain | −0.08785462 | [−0.11295766, −0.05964173] |

Frozen superiority, fold-spread and seed-spread gates all fail. Integrity gates pass.
**Verdict: negative. No weekly slot. No retuning on these seeds.**
The baseline is the registered prior H38-1 candidate recipe, not an independently certified
universal best: historical promotion records conflict. This limitation cannot rescue a candidate
with a large negative paired result. Neither absolute holdout number predicts the organizer score.
Only four geographic uncertainty blocks, catalogue-selection bias, and mirrored external
heat-flow/Euler inputs limit inference. The budget is now 3/3 experiments; no alternative
hypothesis was run.

## Scientific interpretation and official literature

A potential-field contact is not a fault, and a fault is not proof of a geothermal vent.
USGS explicitly describes HG maxima as indicating **faults, intrusions or lithologic contacts**,
not distinguishing them: [3](https://www.usgs.gov/software/pymaxspots-computing-and-connecting-horizontal-gradient-maxima-potential-field-geophysics).
Grauch & Cordell (1987) document offsets when contacts are nonvertical or sources are close:
[4](https://www.usgs.gov/publications/limitations-determining-density-or-magnetic-boundaries-horizontal-gradient-gravity-or).
Phillips' USGS report lists isolated/vertical/thick contacts and magnetization-direction
assumptions; violating them shifts or duplicates peaks, and reduction to the pole is usually
needed: [1](https://pubs.usgs.gov/of/2002/0098/intro.htm).

S18's raw-TMI ridge geometry is especially vulnerable to these ambiguities. q0 is the extrapolated
**observation-height-zero ridge locus**, NOT a recovered fault-plane/surface intersection.
The test contains no calibrated source-depth or dip inversion. Three-height consistency cannot
eliminate contacts without displacement. This offers a physically grounded explanation of failure,
not a proven causal decomposition of the negative result.

Hermant et al. (2025) Figure 2 documents up to 400 m offsets between USGS and TLS traces,
and its introduction notes faults can be conduits **or barriers**:
[Stanford-hosted proceedings PDF](https://pangea.stanford.edu/ERE/db/GeoConf/papers/SGW/2025/Hermant.pdf).
The abstract/introduction/Figure 2 portion was read this session, not all eight extracted chunks.
It supports catalogue uncertainty and caution, not this candidate's q0 heuristic.

## Review corrections, shared-tool fix and next steps

1. **Shared evaluator fixed once, not forked:** old eval_set applied EDT to empty predictions and
   could award phantom edge credit; truth was not intersected with the active mask. It now delegates
   to the already-tested shared metric. Synthetic regression tests cover both cases. All S18 DTI
   uses v2; historical evidence was not silently rewritten or rerun. This does not prove historical
   results materially changed; their nonempty, active-truth conditions usually avoid the edge case.
2. **Hypothesis rank-2 erratum:** `depth_to_base_surf` denotes the base of a conductive surface,
   not an authenticated basement-thickness model. The frozen proposal's basement-hinge interpretation
   is **not viable as stated**. Do not implement it without a revised physical/provenance hypothesis.
   Ranking 3/4 remain unexecuted proposals; official GDR lists the relevant geodetic and radiometric
   source families, not guaranteed fault-specific signatures.
3. **Access correction:** sandbox batch tools have restricted outbound hosts, but the research fetch
   tool successfully retrieved official public pages and all seven rules-PDF chunks. The frozen
   preregistration overgeneralized this limitation; experiment settings were not changed. No DrivenData
   account, private labels, submission-page allowance, eligibility determination or receipt was accessed.
4. **Official rules vs historical copy:** September rules §§3.2/3.4 state THREE submissions/week;
   historical "four slots" language is not current policy. The authenticated account's remaining cap
   still governs selection. The final-round expert review belongs to the organizer and cannot be
   eliminated by our automated local inspection.
5. **No data-placement blocker now:** all 17 pinned owner-mirror inputs restored and the existing
   32-column feature cache prepared. CPU training ran successfully; GPU is not required for this
   classifier. Large inputs/caches are ignored, not committed.
6. **Next session:** keep this lane closed. A new preregistered, provenance-audited scarp-displacement
   observable with road/shoreline controls is a stronger direction than more HG re-layouts. Require
   an explicit lane, shared synchronized registry, frozen current-best baseline and fresh seed ledger
   before any experiment. No new external dataset is asserted viable here without a byte/coverage audit.

## Reproduce/audit without spending an experiment or slot

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
# Restore input mirrors if absent; this is not an organizer login.
.venv/bin/python scripts/restore_data.py --group all
.venv/bin/python scripts/prepare_data.py
.venv/bin/python scripts/finalize_s18.py   # re-read frozen outputs; no model fit or retuning
.venv/bin/python scripts/check_promotion.py evidence/s18_mxtp_run_card.json  # expected exit 1 (negative)
.venv/bin/python scripts/verify_downloads.py
.venv/bin/python scripts/build_site.py
.venv/bin/pytest -q
```

The frozen experiment scripts deliberately refuse to overwrite existing outputs or rerun started
seeds. Finalization requires restored template/labels but not the ignored S18 intermediate surface; the
published final TIFF and checked-in holdout cells are sufficient for format/result audits.
Do not present recomputation on a changed environment as independent confirmation. Source hashes
and package versions are recorded separately. See the three-pass review in `evidence/s18_review.md`.
