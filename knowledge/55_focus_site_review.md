# Focus-site submission review (2026-10-26)

## Executive decision

**No file in this repository is approved for a competition slot.** The current generated S18-MXTP GeoTIFF is downloadable for reproducibility only and is explicitly **DO NOT SUBMIT**: its registered holdout gate failed. The best score in the supplied nine-site list is GEMSDOE32's `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` at **0.2778, owner-reported**. It is not an ORGANIZER-CONFIRMED score because no submission-page receipt is present in this checkout. Do not copy it; its reported score does not establish a new candidate will beat it.

The user-provided leaderboard figure `0.3195` and separate `0.4413` observation are not authenticated receipts in this repository. They are different reported snapshots and must not be conflated with a local HOLDOUT-DTI or a competition score. Current project README also records a 2026-10-25 public-page observation of 0.4413; that dated observation is not a receipt and should be refreshed from the official leaderboard before making a current-leader claim.

## Highest listed entry for each site

The scores and artifact names in this table are transcribed from the request, not independently confirmed against an organizer receipt. “Best listed” means the maximum supplied for that repository, not a claim about every historical upload on its hosted page.

| Site | Best submission listed | Reported score | Executive interpretation |
|---|---|---:|---|
| GEMSDOE24 | `h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan` | 0.2477 | Best listed is a historical dotted H19-5 family raster. Research record says the dense legacy family is catalogue-derived; use only as a benchmark, never as a file to copy. |
| GEMSDOE25 | `dotted-h19-5-d2-8-20261002-e56ea318af89-nan` | 0.2600 | Best listed is the D2.8 thinning variant from the same H19-5 emission family. The incremental score over GEMSDOE24 is only the supplied report; no receipt is available here. |
| GEMSDOE27 | `topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan` | 0.2449 | Best listed topology/gap-closure attempt is below the supplied GEMSDOE24/25 values. The repo history describes this branch as a negative relative to the 0.2477 comparison; do not infer topology closure is generally ineffective from one artifact. |
| GEMSDOE28 | `h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan` | 0.2710 | Highest listed historical GEMSDOE28 result; still below the GEMSDOE32 claim. It is a legacy file, not the currently generated S18 research artifact and not cleared for this run. |
| GEMSDOE30 | `d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca` | 0.2600 | Best listed is a Poisson-spaced off-catalogue emission. Similar score to GEMSDOE25 does not establish the same raster or method performance under a holdout. |
| GEMSDOE31 | `h27-4-solo-d28-20261004-8acb75e1-nan` | 0.2708 | Best listed is the H27-4 solo D2.8 raster, effectively tied with the supplied GEMSDOE28 result to the precision shown. The values are owner-reported. |
| GEMSDOE32 | `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros` | **0.2778** | Highest of the nine supplied site maxima. Existing byte-forensic notes characterize the winning change as removing 2,545 catalogue-flank dots from a 40,199-dot base (37,654 retained); this is a plausible metric-alignment mechanism, not proof of the organizer score attribution. |
| GEMSDOE33 | `h33d-analog-tip-stepover-r30-20261004-cb490425926e` | 0.2632 | Best listed analog-tip/stepover candidate trails the reported GEMSDOE32 result. Do not infer causal superiority from the cross-site score alone. |
| GEMSDOE36 | `anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros` | 0.2750 | Second-highest supplied site maximum, 0.0028 below GEMSDOE32 as reported. The site’s PINN/geothermal framing does not make this a verified score or a validated new method. |

## Answer: why did the GEMSDOE32 entry lead, and can a better one be built?

The most defensible explanation recorded in this checkout is **emission hygiene and alignment with the asymmetric distance-tolerant metric**, not evidence that its geological probability model discovered more faults. In the archived reconstruction, a 2-pixel catalogue-flank exclusion removed 2,545 dots from a 40,199-dot parent raster while retaining 37,654. The local analysis argues that removing predicted dots near known catalogue faults can reduce false-positive penalty without materially removing credit under the metric's distance tolerance. That mechanism is scientifically plausible for this metric, but the exact `0.2778` score/file association remains owner-reported and no organizer receipt was found.

A score above 0.2778 is **possible in principle, not demonstrated here**. Cross-site leaderboard claims are not a substitute for a properly buffered spatial holdout. The latest S18 candidate is decisively negative on the project's local recovery proxy and must not be submitted. Its HOLDOUT-DTI is not comparable to a leaderboard score. Current response should therefore be: **no validated better submission is available; do not spend a slot**.

## Automated submission status in this checkout

- Current S18-MXTP artifact: `docs/downloads/gems28-s18-mxtp-20261025-3e95505c011a-allfinite.tif`.
- Explicit decision: **safe to download for research/reproducibility; NOT OK to upload or submit**. The executive summary disables the submission control and displays the warning before the download.
- Current S18 HOLDOUT-DTI: **0.020384** (shared evaluator `eval_set v2 → metric.dti_binary`; 76,869 pooled withheld positives, 45,155 unique; 95% CI [0.016438, 0.024729]); paired gain vs recomputed baseline −0.087855 (95% CI [−0.112958, −0.059642]). This is a local whole-segment buffered recovery test, not an organizer score.
- The artifact is locally checked for all-finite values in [0,1], single-band float32 and matching template grid, and is unique within a pinned 166-raster snapshot under the stated thresholds. These checks do **not** rescue its failed scientific gate, guarantee portal acceptance, or prove global uniqueness across concurrent repositories.
- The requested budget is already exhausted for that run; no further experiments or candidate selection are authorized by its frozen run record. Three experiments were used across the relevant parallel S18 work. Start a future experiment only with a new explicit lane, preregistration, fresh seed allocation and synchronized registry.

## Evidence and limitations

- Primary current run summary: [`README.md`](../README.md); [S18 run card](../evidence/s18_mxtp_run_card.json); [focus-site overlap audit](../evidence/s18_focus_sites_overlap.json); [owner-site source refresh snapshot](../evidence/s18_owner_site_refresh.json).
- Public site pages supplied for manual review: [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/), [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/), [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/), [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/), [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/), [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/), [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html), [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/), [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/).
- Competition source: [DrivenData competition](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/). A public page view is not a submission receipt.
- This table uses the user's supplied score list, plus repository evidence for interpretation; it is not a fresh scrape or official verification of all nine deployed pages. The pinned owner-published snapshots in `evidence/s18_owner_site_refresh.json` are expressly not organizer-authenticated and show that hosted pages contain historical and potentially inconsistent claims.
- No current DrivenData login, hidden test labels, submission receipt, quota state, or synchronized registry across all parallel runs is available. No automatic upload has occurred.

## Recommendations

1. Keep the prominent landing-page decision **NOT APPROVED — DO NOT SUBMIT** until an independently preregistered candidate beats the frozen holdout baseline and passes the complete uniqueness/format gates.
2. Preserve the H33-2 B2 file as a forensic benchmark only; never clone or perturb it to manufacture novelty.
3. Before future experimentation, reconcile all parallel registry snapshots, declare one lane and non-fault mimic, verify the shared evaluator/writer API contract, allocate unused seeds, and preregister 3–5 hypotheses. Run feature-alone leakage canaries before the full holdout.
4. For any future candidate, publish a run card with evaluator version, withheld positives and CI, pre-placement and final-dot uniqueness, content SHA-256, exact format audit, unique name, ≤140-character note, and explicit promote/negative decision. A negative result is the correct outcome when gates fail.
5. Keep current TIF downloadable only under the unambiguous research-only warning; do not present it as a submission-ready deliverable.
