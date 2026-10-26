# Session 20 preregistration — H43-1 TPB2-GKC (frozen before Experiments 1–3)

**Date:** 2026-10-26 (UTC). **Branch:** `arena/36be803a-gemsdoe28`.
**Lane assignment disclosure:** the owner prompt says "Your lane is the single method
paragraph below", but no identifiable method paragraph is present in the prompt
(Session 19 flagged the same gap and stopped). This session therefore *declares its own
single lane explicitly below (§3), before running any experiment*, stays inside it, and
discloses the interpretation instead of silently inventing an assignment. This is the same
disclosed-interpretation route Session 18 took. Budget: ≤3 experiments, ≤2 h of experiment
time. This session never uploads anything and never selects a competition slot; slot
promotion remains a separate selector step.

**Score-labelling contract:** every number produced here is labelled
**HOLDOUT-DTI** (evaluator `src/gems27/metric.py:dti_binary`, α=0.2, β=0.8, 300 m triangular
kernel, with withheld-positive count and 95% CI), **USER-REPORTED / UNVERIFIED** (values
copied from the owner prompt; no submission-page receipt exists in this checkout), or
**MODEL** (arithmetic under stated assumptions; never a score). No number in this session is
ORGANIZER-CONFIRMED.

## 1. Why the cited GEMSDOE32 champion scored highest in the supplied list (evidence, not folklore)

Fresh byte forensics are Experiment 1, but the frozen facts this preregistration relies on were
each re-read in this checkout before writing this file:

* `data/registry_edu/champion_g32_h33_2_b2_zeros.tif` (fetched this session from
  `buffedlizard55-lab/GEMSDOE32@012e17b`, SHA-256 `c55bafc4…6fa9`, matching that repo's own
  audit JSON) contains exactly **37,654** positive pixels. Its sibling audit JSON describes it,
  verbatim in substance, as the owner-reported-0.2708 base "with every dot at d(catalogue) ≤ 2 px
  deleted", and its embedded submission note says **UNSCORED**, "projected live 0.2747"
  (`holdout_metrics.predicted_leaderboard_dti = 0.27467315976932155`). So the 0.2778 in the owner
  prompt is at best a later owner-reported association, close to the file's own MODEL projection;
  there is still **no organizer receipt** in any repo examined. It remains USER-REPORTED / UNVERIFIED.
* Local restored inputs, SHA-256-verified against `registry/data_manifest.json` this session:
  H19-5 solid ridge = **121,131** px; `dotted-h19-5-d2-8` = **44,090** px; local solo-r1
  (`gems28-h27-4-r1-solo-d2-8…8acb75e1f2cc-nan.tif`) = **40,199** px; catalogue labels = **60,988** px.
  The lineage solid (0.1922) → d=1.5 dotted (0.2477) → d=2.8 dotted (0.2600) → ring-1 prune/solo
  (0.2708) → ring-2 prune/champion (0.2778) is therefore, at every scored step, **the same
  H19-5 multiline-corroborated surface under successively cleaner emission hygiene**:
  ① Poisson spacing matched to the 300 m credit kernel (a dot keeps ≈0.78 mean on-line credit at
  s=3 px for ⅓ the FP mass — `knowledge/01…md` §2, exact arithmetic), then
  ② deletion of catalogue-flank digitisation shadow, whose dots sit off any hidden fault with
  probability ≈1 (hidden truth is *new* expert traces; known catalogue pixels are masked in the
  official metric) and therefore pay ≈full FP cost for ≈zero credit. Each removed ring was below
  the inclusion break-even τ(DTI)=0.2·DTI/(1−0.2·DTI) ≈ 0.055–0.059 credit/FP at these operating
  points (`src/gems27/metric.py:inclusion_threshold`, derived and unit-tested).
* The contrapositive is the PhD-level lesson of 100+ sibling submissions: **detection novelty kept
  losing to emission hygiene** (owner-reported: dilcond-OOF 0.1223, T-v2 gap closure −0.0028 live,
  fresh ML/Euler/physics surfaces mostly 0.02–0.19). The binding constraint at 0.2778 is no longer
  dot spacing; under the corrected closure DTI = a/(0.8+0.2·N/|G|) (`knowledge/01…md` Addendum-F,
  MODEL with |G|≈12,226 px from one lattice calibration, unconfirmed), beating 0.2778 at N=37,654
  requires *more weighted credit per dot* — a ranking/placement problem plus any genuinely new
  credit the champion's blind rules threw away — not another re-spacing of the same dots.

**Answer to "can we generate > 0.2778?":** in principle yes, only via (a) higher credit/dot at
matched budget (better placement over the same pool) and/or (b) rescuing credit-bearing pool mass
the blind B2 rule deleted or `dot_thin`'s raster-order phase never emitted. Whether the candidate
below achieves either is exactly what the frozen holdout gate decides. No score above 0.2778 is
claimed in advance; any projection stays labelled MODEL.

## 2. Hypotheses generated before implementation, ranked (expected benefit ÷ cost)

All five were checked against this repo's implemented modules (`src/gems27/`) and the cross-site
record. "Expected" is qualitative prioritisation, never a numerical DTI projection.

| Rank | Hypothesis | Layers / signature | Why it should catch a catalogue-missing fault | Difference from this repo | Cost / data gate |
|---:|---|---|---|---|---|
| **1 (the lane)** | **H43-1 TPB2-GKC** — tip-protected B2 eligibility + greedy triangular-kernel max-cover re-placement over the H19-5 pool at the champion's exact budget | `h19_5_nan.tif` pool; `labels.tif` distance + degree-≤1 endpoint distance (the repo's existing `build_flank_mid_mask` geometry, ring extended to 2 px) | Fault *tips* propagate, step over and splay beyond mapped endpoints — the one ring-≤2 subclass with measured elevated credit density (H32-1: protected tip/Euler dots 0.0092 vs 0.0040 credit/FP, HOLDOUT, seeds 180–189). Blind B2 deleted them; mid-segment flank shadow stays deleted | H32-1 was a *subset prune* of `dot_thin` output protecting ring 1 only. The champion is a blind subset prune. H43-1 is **generative**: greedy max-cover may place pool pixels no registry raster emitted, with protection extended to ring 2. `src/gems27/packing.py` re-packs existing dots; nothing in-repo does pool-level kernel-cover placement | Low. No new data; both inputs SHA-256-pinned and restored |
| 2 | Displaced potential-field piercing markers (Session 19 rank 1) | RTP/TMI + isostatic gravity; coherent lateral offset of multiple marker ridges across a corridor | Buried fault offsets basement contacts with no scarp to catalogue | No patch-registration/displacement transform in-repo | Medium-high. Needs the 419 MB training stack (obtainable, hash-pinned mirror, not organizer-authenticated) + new registration code; cannot be gated honestly inside this session's remaining budget after the lane |
| 3 | Multi-method consensus-vote surface, kernel-cover emission | Vote of local diverse registry rasters | Agreement of unrelated detectors localises structure each one phases differently | New surface type | Medium, but parents were built with full-catalogue knowledge ⇒ holdout leakage control is genuinely hard; deferred rather than faked |
| 4 | Artifact-swap mimic suppression (queued H39-4) | LiDAR coherence/strike + DEM + potential fields | Frees budget spent on roads/shorelines for real structure | No explicit mimic model in-repo | Medium; needs LiDAR/extension stacks restored (37 MB + 27 MB pinned mirrors) |
| — rejected | B3 flank ring (200–300 m) prune of the champion | `labels.tif` only | — | **Rejected as a lane**: a subset of the champion has 100% of dots within 3 px of a registry raster ⇒ duplicate by the owner's own >70% rule. Kept only as a labelled MODEL extrapolation in the report, never as a submission | — |

## 3. THE LANE (single method paragraph — this session stays inside it)

**H43-1 TPB2-GKC.** Take the frozen H19-5 binary pool (121,131 px, SHA-256 `ec1f9b56…dee8d`) as the
only candidate set. A pool pixel is *eligible* iff it is inside the footprint, not on the visible
catalogue, and (d_visible > 2 px **or** d_endpoint ≤ 3 px), where d_visible is Euclidean distance to
the visible catalogue and d_endpoint is distance to a visible-catalogue pixel whose 8-neighbourhood
catalogue degree is ≤ 1 (the repo's existing endpoint geometry in
`scripts/run_h32_1_holdout.py:build_flank_mid_mask`, ring widened from 1 px to 2 px, Euler term
dropped because its licence was refuted in H37-3). Place dots by deterministic lazy-greedy
maximisation of covered pool mass under the official triangular kernel k(d)=max(1−d/3,0): each pick
maximises Σ over pool pixels of the *increase* in max-kernel credit, subject to min inter-dot
distance ≥ 2.8 px, until the budget is met. Full-build budget = **37,654** dots (the champion's,
so any difference is placement, not budget). Named non-fault mimic: **catalogue digitisation
endpoints** (a truncated mapping terminus is not a geological tip) plus inherited H19-5 cultural
lineaments (roads/strandlines) — the lane re-places H19-5 evidence, it does not re-detect geology,
and says so.

## 4. Frozen experiments (≤3)

**Experiment 1 — forensics + leakage canary (no gate seeds touched).**
(a) Byte-level: champion vs local solo-r1 vs d2.8 vs H19-5 (subset relations, ring histograms,
exact symmetric differences); regenerate `dot_thin(H19-5 minus catalogue, 2.8)` and compare to the
pinned d2.8 raster. (b) Canary: single-feature AUC of each catalogue-derived eligibility input
(d_visible, ring≤2 indicator, tip indicator d_endpoint≤3, eligibility) against seed-340 hidden
components (assignment only, no fitting). Any AUC > 0.90 ⇒ leakage ⇒ stop.

**Experiment 2 — holdout gate.** Evaluator: repo `holdout.make_quadrant_folds` + `make_split`
(20% of 8-connected components hidden per quadrant) driving `metric.dti_binary` (α=0.2, β=0.8,
300 m triangular kernel), visible faults masked pixel-exactly via `known=visible`, all
catalogue-derived quantities (d_visible, endpoints, pool-minus-visible) recomputed from visible
faults only, per cell. Seeds **340–344** (verified unused: ledger runs to 310–314) × 4 quadrants =
20 paired cells. Emissions restricted to each cell's quadrant. Arms, identical pool/truth/mask:
**C0** = `dot_thin(pool & ~visible, 2.8)` then blind-delete d_visible ≤ 2 (champion analogue);
**C1** = H43-1 lane truncated to exactly |C0| dots in that cell (pure ranking test).
**Pass requires ALL:** G1 pooled ΔDTI > 0 and mean paired ΔDTI ≥ +0.0005;
G2 ≥ 12/20 cells positive; G3 pooled credit/dot(C1) ≥ credit/dot(C0);
G4 zero dots on visible catalogue in every cell, both arms; G5 Experiment-1 canary clean.
Report regardless: pooled HOLDOUT-DTI per arm, withheld positives (pooled + unique), paired
bootstrap 95% CI over the 20 cells. **Known bias, stated in advance:** hidden pieces are
catalogue-internal, so this proxy *rewards* catalogue-adjacent dots that the live metric punishes;
it can therefore only understate the B2-flank half of the lane and is used here to test the
placement + tip-rescue half. A pass is necessary, not sufficient, and is never a live score.

**Experiment 3 — build + uniqueness + validator.** Full-catalogue H43-1 at 37,654 dots via
`src/gems27/submission.py` (primary: all-finite zeros-outside variant, so the entire stored array
is finite and in [0,1] — the direct fix for the owner's *"Predicted values must be in range
[0, 1]"* portal error; companion NaN-outside variant + single-member ZIP also written).
Pre-placement surface (pool kernel-density × eligibility) and final dots each compared against
every distinct-dot-set registry raster available locally (all `docs/downloads/*.tif` dot sets +
H19-5/d1.5/d2.8 + the GEMSDOE32 champion education copy): Spearman(surface, registry) and
fraction of final dots within 3 px per registry raster. Duplicate stop: any Spearman > 0.90 or
any within-3px fraction > 0.70 ⇒ log duplicate, mark DO NOT SUBMIT. Exact-file validator:
single-band float32, EPSG:32611, 3730×3292, template transform, no NaN inside footprint (none
anywhere in the primary), values ⊆ {0,1} ⊂ [0,1], 0 dots on catalogue, SHA-256 recorded.

**Reading rule (frozen):** Experiment 2 pass **and** Experiment 3 uniqueness + validator pass ⇒
verdict `promote` (eligible for the separate selector step; site banner may say OK to download
and submit, with the weekly-cap + receipt instructions). Anything else ⇒ verdict `negative`,
TIFF still generated for reproducibility but banner-marked **DO NOT SUBMIT**. No retuning on
seeds 340–344 either way.

## 5. Official sources (manual review)

Competition + metric: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ ·
Rules PDF: https://docs.nlr.gov/docs/fy26osti/96647.pdf · Reference solution:
https://github.com/drivendataorg/gems-prize-reference-solution · USGS GeoDAWN:
https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and ·
INGENIOUS / GDR 1391: https://gdr.openei.org/submissions/1391 · EPSG:32611: https://epsg.io/32611 ·
Tversky index: https://en.wikipedia.org/wiki/Tversky_index. Input rasters are owner-supplied
GitHub mirrors, hash-pinned in `registry/data_manifest.json`, **not organizer-authenticated** —
no DrivenData login was used or attempted.
