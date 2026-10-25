# Current review — G28-A51, 2026-10-25

## Executive decision

**NOT READY TO SUBMIT. No new TIFF was generated, no geological hypothesis was run, and no competition slot was selected.** This review does not complete the user's unique-submission requirement. It resolves the data/cache blocker, establishes read-only reuse of the discovered shared tools, and removes an unsafe recommendation to submit a historical duplicate. Negative results are deliverables, but must not be presented as a successful new submission.

Read the current notice, requirement summary and retained historical prompts in `README.md` at the start of subsequent work. The latest full verbatim request was not available in the retained conversation; its summary is not falsely labeled a verbatim transcript. Core values: **Maximize P(Win)** by requiring real information gain rather than a new filename; **Own the Outcome** by testing the advertised download and withdrawing unsupported clearance without waiting for a human inspector.

## 1. What was actually executed

These are **software/integrity/raster-audit measurements**, not competition scores or geological HOLDOUT-DTI experiments.

1. Inspected the branch, standing brief, current site generator, previous S15/S16 cards, legacy component holdout, LOSFO code, writer, source feed, workflows and tests.
2. Installed the existing Python requirements in ignored `.venv/`. Baseline tests with restored data: 322 passed, two optional geospatial-library skips. A skipped check is not a pass.
3. Ran the existing `scripts/restore_data.py --group all`. All 17 entries match `registry/data_manifest.json` by byte count and SHA-256. Training features, labels, sample grid, LiDAR descriptors, GeoDAWN caches and auxiliary tables now exist in ignored `data/`.
4. Ran the existing `scripts/prepare_data.py`, without changing feature design. It produced the existing 32-band float32 feature cache. Ran `scripts/verify_restored_inputs.py` independently. See [`current_input_audit.json`](../evidence/current_input_audit.json); cache SHA-256 is recorded there. This is reproduction of the established cache, not a new hypothesis/feature stack. The large cache is not committed.
5. Pinned all nine requested owner repositories at observed commits, downloaded 28 high-score-identity raster variants, checked their Git blob identities, calculated SHA-256 values, and re-read their grids/ranges. See [`priority_repository_audit.json`](../evidence/priority_repository_audit.json). This is the priority subset, **not** an assertion of complete global or parallel-run coverage.
6. Located actual `scripts/evaluate_holdout.py` and `scripts/submission_writer.py` in GEMSDOE24 at `bddb55fca2c16e2b6f03c98d28751d8ff8cc7e5e`. Pinned those entry points and their shared holdout/metric/novelty/writer libraries in [`protocol_assets.json`](../registry/protocol_assets.json). Source stays read-only under ignored `data/shared_template/`, is hash-verified before import, and is restored by `scripts/restore_protocol_assets.py`. **No evaluator or writer code was copied into a new private fork.** The entry point is a frozen MTR1-specific scientific runner; it is not a lane assignment for this session.
7. Ran `scripts/audit_shared_template.py` on synthetic fixtures. Whole cross-quadrant components were absent from visible faults, training and validation were disjoint, deliberate and inverted label leaks were flagged, and the legacy metric's components matched the pinned shared metric on all fixture cases. See [`shared_template_contract.json`](../evidence/shared_template_contract.json). These software tests do **not** establish expert fault-segment identity, scientific generalization or an improved current-best holdout.
8. Ran `scripts/audit_existing_submissions.py`. It reads existing bytes and calls the pinned shared novelty comparator. It never trains, places new dots or writes a TIFF. The advertised historical primary passes two format validators but fails the duplicate rule. Full raw-footprint Spearman and all-dot directional overlap are separate from the separately labeled kernel-sample diagnostic. See [`current_submission_audit.json`](../evidence/current_submission_audit.json).
9. Ran the current preflight. It correctly blocks on missing lane, missing complete parallel-run registry and missing frozen same-protocol best. The cache and shared tools pass integrity checks. See [`current_preflight.json`](../evidence/current_preflight.json).

## 2. Why the reported GEMSDOE32 result plausibly leads the family

### Directly verified from the downloaded raster bytes

The source identities and exact calculations are in the priority and current-submission audits.

- GEMSDOE25's D2.8 raster has **44,090** positive footprint cells.
- GEMSDOE28 solo has **40,199**.
- GEMSDOE32's named champion has **37,654**.
- The champion equals solo minus its **2,545** dots at Euclidean catalogue distance ≤2 pixels, pixel-exactly. It introduces **zero** new dots. Equivalently it equals D2.8 after the same ≤2-pixel exclusion.
- GEMSDOE36 contains every champion dot plus **1,200** others.
- GEMSDOE25 and GEMSDOE30 have identical footprint predictions. GEMSDOE28 solo and GEMSDOE31 solo do too. Different byte hashes can represent the same scored prediction, including NaN/zero-outside packaging changes.
- The currently advertised H36-1 primary has **95.472650%** of its dots within 3 pixels of the champion and **100%** within 3 pixels of several other priority/local references. Either threshold violation suffices to reject it as a new lane. Its original pre-placement continuous surface was not available; no surrogate surface or backdated pre-placement check was fabricated.

These counts and correlations are **RASTER AUDIT** statistics, not DTI scores. The educational reconstruction was in memory only; no champion-derived TIFF was emitted.

### Mechanism, with the correct epistemic boundary

For the stipulated triangular distance kernel and alpha=0.2, beta=0.8:

\[
S=\frac{TP_w}{TP_w+0.2FP_w+0.8FN_w}
 =\frac{TP_w}{0.2TP_w+0.2FP_w+0.8|G|}.
\]

At fixed truth, an addition improves the ratio only when

\[
\frac{\Delta TP_w}{\Delta FP_w}>\frac{0.2S}{1-0.2S}.
\]

Removing predictions with a smaller lost-credit/removed-FP ratio can therefore help. Spaced predictions can retain much of a line's triangular-kernel coverage while avoiding redundant prediction mass; catalogue-flank predictions can be particularly inefficient when they reproduce already mapped expression rather than new target faults. This is a defensible explanation of **emission efficiency**, not evidence of newly discovered faults or vents.

The hidden organizer truth and a receipt bound to the champion bytes are unavailable. We cannot measure its true TP/FP changes or prove that pruning caused the user-reported competition outcome. We do not label the supplied `0.2778` claim ORGANIZER-CONFIRMED, even where an owner README uses that wording for an owner-reported receipt. A source author's label is not an independently inspected submission-page receipt.

**Can we exceed it?** Unknown. This review has no new HOLDOUT-DTI, withheld-positive count or confidence interval, and no prediction that can honestly be claimed to beat it. Historical catalogue-trained final TIFFs are not valid paired OOF baselines for a new strict holdout. Neither a mean-only improvement nor another pruning ring is an acceptable substitute for a new, nonduplicate method.

## 3. Four ranked hypotheses, before any geological implementation

The full layer/signature/off-catalogue rationale/difference/confounder/cost/availability slate is machine-readable in [`current_review.json`](../evidence/current_review.json) and rendered first on the Research page.

| Rank | Proposal | Key new statistic | Expected benefit (qualitative only) | Cost / availability |
|---|---|---|---|---|
| 1 | **G28-A51-A: displaced potential-field piercing markers** | Consistent offset of multiple RTP/TMI/gravity marker ridges across a corridor, rather than assigning the marker edge itself as a fault | Highest information potential in this slate; entirely unmeasured | Medium/high; cached fields available |
| 2 | **G28-A51-B: lithology-conditioned U/Th transport dipoles** | Odd-symmetric cross-corridor U/Th residual morphology, conditioned on Th/K and tested against quantization/missingness | Moderate, physically ambiguous; unmeasured | Medium; cached radiometry/ratios available, not absolute chemical calibration |
| 3 | **G28-A51-C: paired-geothermometer cooling corridors** | Multi-site directional structure in paired reservoir-estimate/observed-temperature differences, not a max-temperature halo | Low/moderate, strongly limited by site sampling | Medium; cached GDR table has paired values; deduplicate sites before analysis |
| 4 | **G28-A51-D: opposite-flank flexural curvature pairs** | Ordered signed curvature/relief lobes on both sides of a corridor, not generic curvature/gradient magnitude | Lowest priority because nontectonic landforms are common; unmeasured | Medium for coarse/cache diagnostic; high-resolution 3DEP confirmation not obtained |

These are **hypotheses**, not literature-verified geothermal signatures, globally unique methods or score projections. Current local source review did not find the named transforms; a complete peer-source/method registry is still needed to establish cross-site novelty. Specific non-fault mimics are listed for every proposal. No scalar strain or potential-field layer is treated as sufficient to recover fault dip, slip or permeability uniquely.

The top proposal is **not** an assigned parallel-run lane. The prompt references a single method paragraph, but none is identifiable. Choosing one anyway would violate the lane constraint. No top-candidate validation was run and no slot is eligible. Once an explicit lane and registry are present, test only that method under the common protocol, not the whole slate or a three-arm parameter search.

All coarse proposals use existing restored data for an internal diagnostic. For high-resolution confirmation the official free source is the [USGS 3DEP 1 m DEM collection](https://data.usgs.gov/datacatalog/data/USGS:77ae0551-c61e-4979-aedd-d797abdcde0e). Its tile bytes/coverage were not obtained here; no high-resolution method is marked viable on an unverified URL alone.

## 4. New safety behavior

- The current Overview and Executive Summary no longer suggest submitting the old primary. They explicitly lock the submission download and link the machine-readable negative card.
- Old overview/checklists/slot labels are retained in a separately labeled, collapsed **historical archive**. They are not current authorization. Archived TIFF buttons explicitly say **DO NOT SUBMIT**.
- All current pages use a common readiness banner computed from the evidence gate, not a hardcoded self-declared `submission_ready` field. Even a complete schema is only promotion eligibility; it does not select a slot, check the live cap, authenticate evidence or authorize upload.
- The shared evidence gate now rejects inverted leakage, negative near-perfect rank duplicates, whitespace/non-string scientific identifiers and missing final-dot overlap. Pre-placement surface correlation does not require inventing dot overlap before dots exist.
- The existing local shared writer rejects non-real/text predictions, self-overwriting the template, wrong extensions and invalid interior probabilities. It atomically publishes only after an independent disk re-read. Numeric nodata sentinels, wrong shapes, NaN inside and wrong drivers fail closed. ZIP packaging cannot overwrite its source TIFF. New notes are capped at the stricter **140 characters**. This hardens the existing shared writer; it does not replace the pinned upstream evaluator with a private fork.
- A JSON evidence schema cannot prove independent training or that a self-declared registry includes unseen parallel runs. The site and CLI state this limit. Actual numerical outputs remain hash-bound and source-linked; no human sign-off is treated as substitute evidence.
- Existing source-feed observations retain their original timestamps. A stale/unavailable observation is never called a live score or cap. The browser labels old observations stale rather than polling the competition.

## 5. Official source audit and access limitations

Freshly inspected official GitHub sources:

- [Official reference notebook, pinned commit](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/unet-mc-cv-reference-solution.ipynb): cell 0 describes **fault detection**; cell 16 uses a Tversky training loss with alpha=0.2, beta=0.8. This is not the hidden competition evaluator or a receipt.
- [Official README, same commit](https://github.com/drivendataorg/gems-prize-reference-solution/blob/aebe92f7c8a990f0e3443451b7a825d9afd6336b/README.md): CPU-only environments are supported. A GPU is faster, not a prerequisite for all training or these audits. The older “GPU needed” blanket statement is not adopted.
- [`official_reference_audit.json`](../evidence/official_reference_audit.json) records the exact bytes, sources and claim boundaries.

Official review links **not freshly retrieved in this runtime**:

- [Competition problem / metric / format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [Competition leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Rules PDF provided by the user](https://docs.nlr.gov/docs/fy26osti/96647.pdf)
- [USGS GeoDAWN](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE GDR #1391](https://gdr.openei.org/submissions/1391)

Network policy permits GitHub and package registries, not these official hosts. GitHub repository access works; no GitHub credentials are needed from the user. No DrivenData account was accessed and no login-walled file or receipt was retrieved. The request supplies conflicting current leaderboard maxima; neither is selected as fact. Historical weekly-slot labels likewise cannot establish the live cap.

The competition objective verified here is geological fault detection; geothermal flow is an exploration motivation, not a newly verified vent-detection target. Source-code comparison and raster hashes do not prove physical causality, official data provenance, outside-data licensing, hidden-truth performance or portal acceptance.

## 6. Irregularities to retain, not conceal

1. Assigned method paragraph is absent. Ranked hypotheses are not lane allocations.
2. The old UI recommended an archive primary even while saying the newest run failed uniqueness. The primary itself is now numerically rejected as a duplicate.
3. Multiple priority repositories distribute identical footprint predictions under different names/packaging.
4. Three GEMSDOE31 “allfinite” variants have NaN nodata metadata but do not satisfy the NaN-outside mask convention. This is an independent local format warning, not a proven cause of any portal error.
5. The GEMSDOE36 README's listed NaN-variant SHA differs from the freshly fetched NaN file; the fetched zero-outside champion identity matches the educational comparison. Preserve actual inspected hashes, not copied documentation values.
6. GEMSDOE32's page/README include contradictory submit/stop language and an owner-reported “ORGANIZER-CONFIRMED” label without an inspected receipt. No local confidence is upgraded by that wording.
7. The raster `depth_to_base_surf` is interpreted inconsistently by historical code/docstrings (basement vs conductive-base surface). No new proposal depends on resolving that ambiguity by guesswork; official source metadata are still needed.
8. The legacy interleaved/component holdout and full-catalogue-trained TIFF evaluator are retained for provenance but are not promotion evidence under the stricter current protocol.

These are entered in `registry/irregularities.json` with links to the corresponding evidence. Historical evidence files are not silently recomputed into improved-looking results.

## 7. Reproduction commands and next session

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python scripts/restore_data.py --group all
.venv/bin/python scripts/prepare_data.py                 # existing cache preparation, no model
.venv/bin/python scripts/verify_restored_inputs.py --out evidence/current_input_audit.json
.venv/bin/python scripts/restore_protocol_assets.py
.venv/bin/python scripts/audit_shared_template.py        # synthetic software checks only
.venv/bin/python scripts/audit_priority_repositories.py  # GitHub source/old-raster audit only
.venv/bin/python scripts/audit_existing_submissions.py   # no training or new TIFF
.venv/bin/python scripts/check_run_preflight.py          # expected exit 1 until resolved
.venv/bin/python scripts/check_promotion.py evidence/current_run_card.json  # expected exit 1
.venv/bin/python scripts/build_site.py
```

Re-running a source audit creates a **new observation**. Do not overwrite an old scientific run, reuse consumed seeds or treat cached mirror hashes as organizer authentication. The current run card must be regenerated with `scripts/record_current_review.py` if its cited review evidence changes; the recorder refuses use as a scientific-run card.

Next priorities, in order:

1. Supply an explicit lane assignment in `registry/current_session.json` and a complete versioned external parallel-run registry. This is project coordination, not human scientific inspection.
2. Re-evaluate and freeze the incumbent using the same read-only shared buffered protocol and visible-only feature construction. Authenticated segment identities are preferable to raster-component proxies; do not claim the latter recover expert trace segmentation.
3. Freeze one candidate method and its named confounder. Run every feature-alone canary and registry surface check before placement; stop on a duplicate. Do not perturb/rerank against registry values to evade thresholds.
4. Within three experiments or two hours, generate genuine fold-independent predictions, pool TP/FP/FN, compute spatial/segment-cluster CIs and the paired gain interval. Negative evidence remains final; no same-seed retries for a green light.
5. Only if gates pass, use the shared writer and independent re-read to publish a truly new content-bound TIFF with a ≤140-character note. Evaluate final-dot uniqueness against every registry member.
6. Let the separate selector check current official slot limits. No archived primary is an automatic fallback. Obtain a filename/hash-bound submission-page receipt before reporting an organizer score.

## 8. Three verification passes

This section is finalized after implementation, review and full-suite re-check; it is not a claim that a geological experiment passed. The machine-readable verification record is `evidence/current_verification.json`.

- **Pass 1:** restore/verify inputs and existing cache; pin shared tools; source/raster audit; current/archive UI separation; strict negative run card and preflight; targeted software tests.
- **Pass 2:** review malformed evidence, negative-polarity leakage, undefined pre-placement overlap, wrong shapes/nodata, non-real predictions, atomic publishing, template/ZIP self-overwrite, unsafe feed redirects and stale observations. Add regressions and fix defects, without rerunning historical science.
- **Pass 3:** reconcile against the full user request; full lint/tests; deterministic site rebuild; internal-link and live-preview smoke checks; verify evidence hashes, no new TIFF/slot/score claim, and branch/PR integration. Missing unique-TIFF and top-candidate-holdout requirements remain explicitly incomplete rather than being marked fulfilled.

### Final local verification notes

- Installed the existing vector-test dependencies (`geopandas`, `pyogrio`) and included them in `requirements.txt`, so their regression modules are no longer silently skipped. The final local suite passed **441 tests, no skips**. This is software verification, not 441 geological experiments.
- Full-repository Ruff passes. Three inherited unused-variable warnings in two legacy runners were removed without changing their numerical operations; those runners were not re-executed as science.
- Fixed an inherited test side effect: the archived-download regression now writes its fresh audit to a temporary report rather than rewriting tracked historical `submission_file_audit.json`. The original historical evidence was preserved.
- Edge-case regressions exercise missing/unlisted/tampered shared assets, stale bytecode, path/symlink escapes, expired/future/missing budget clocks, incomplete registry/baseline metadata, malformed text and inverted leakage, missing pre-placement/final-dot evidence, complex/NaN/wrong-shape rasters, nodata sentinels, failed atomic TIFF/ZIP publication and ZIP hardlinks to the source.
- Restricted local source refresh observed **2 of 10** sources (GitHub); eight official/non-GitHub sources were **not attempted**, and their actual prior successful observation dates are retained. New per-source status/counts are visible. The redirect guard rejects DrivenData and hosts outside the runtime allowlist before contacting them.
- Scheduled source refresh now rebuilds the dated HTML and triggers Pages through `workflow_run`; relying only on a `GITHUB_TOKEN` commit's push event would not deploy the refresh. It no longer races active research branches. Pages staging preserves both root and legacy `/docs/` URLs.
- `evidence/current_verification.json` records the local/clean-checkout checks and their limits. PR, merge and deployment outcomes must be read from the actual GitHub results and the final report, not predicted from local tests.
