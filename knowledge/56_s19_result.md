# S19-ASCP result — unique all-finite TIFF, negative holdout

**Date:** 2026-10-26 UTC  
**Decision:** safe to download for research; **DO NOT SUBMIT**. No competition slot was selected.

## Executive result

S19 executed the frozen top-ranked hypothesis in [`55_s19_preregistration.md`](55_s19_preregistration.md): a LiDAR-derived conjunction of 10–50 m step strength, paired crest/toe curvature, uphill-facing selectivity and 100 m coherence. It generated 37,654 new dots without copying or modifying a prior submission.

The exact output is [`gems28-s19-ascp-20261026-dc717c1ab13b-allfinite.tif`](../docs/downloads/gems28-s19-ascp-20261026-dc717c1ab13b-allfinite.tif), SHA-256 `553bbd6db1ae0f3a8fc41a81ed8bc1f438e5af6bd74d43c5d260d6889d0e6537`.

- One float32 band, 3,730 × 3,292, EPSG:32611.
- Exact template CRS, shape and transform.
- No NaN inside the footprint or elsewhere; values are exactly 0 or 1.
- Name: `GEMSDOE28-S19-ASCP-dc717c1ab13b`.
- Note (84/140): `S19 ASCP paired antislope LiDAR scarps; 37654 dots; holdout rejected; DO NOT SUBMIT.`
- These are local exact-file facts, not a guarantee of portal acceptance.

## Three experiments

### 1. Feature-alone canary and pre-placement novelty

The hash-verified shared `SegmentHoldout.canary` tested each physical leg and the combined surface, including both AUC polarities and each fold. All passed the 0.90 leakage stop. Pooled AUCs are recorded in `evidence/s19_ascp_stage.json`; a low AUC is not proof of usefulness or independence.

The fresh registry contains 53 unique-byte valid-grid rasters from the nine requested priority repositories and the pre-run local archive. Exact continuous-surface |Spearman| peaked at 0.103044, below 0.90.

The frozen runner's preliminary proximity check used a conservative 7 × 7 square neighborhood, which includes diagonal cells farther than three Euclidean pixels. That labeling defect is disclosed in `registry/irregularities.json`. A post-run read-only correction on identical bytes (`evidence/s19_exact_registry_overlap.json`) measured exact Euclidean distance ≤3 pixels: maximum support overlap 0.205685. Both versions pass; no model was refit and no threshold changed.

### 2. Final placement and exact bytes

Fixed ridge NMS and 2.8-pixel packing produced 37,654 dots. Maximum final binary |Spearman| was 0.006538. Exact Euclidean ≤3-pixel overlap peaked at 0.279811, below 0.70. The shared writer produced the all-finite file, and the exact disk bytes passed every required format check.

### 3. Shared buffered holdout

**HOLDOUT-DTI** — evaluator `gems-segment-pooled-v1`; 60,988 withheld-positive pixels; whole 8-connected components hidden everywhere; 1.5 km collar; four geographic quadrants; visible-only catalogue exclusion; pixel-exact visible masking; pooled α=0.2, β=0.8, 300 m triangular kernel; 10 km spatial-block percentile intervals:

| Arm | HOLDOUT-DTI | 95% CI |
|---|---:|---:|
| S19 antislope paired-curvature candidate | 0.080806 | [0.072325, 0.089111] |
| Recomputed visible-only 32-band H38-style baseline | 0.141694 | [0.128368, 0.154587] |
| Paired gain | −0.060888 | [−0.074029, −0.047638] |

The candidate lost in every fold. The superiority, paired-interval and 3-of-4-fold gates failed. Canary, uniqueness and validator gates passed. The final verdict is therefore `negative`.

This holdout uses catalogue-mapped raster components as a recovery proxy. It is neither private organizer truth nor an organizer score. Eight-connected components are not authenticated expert segment IDs.

## Scientific interpretation

The test targeted an antislope crest/toe pair that a subtle normal-fault scarp might preserve after regional mapping missed it. Named non-fault mimics were road cuts, channels, terrace and paleo-shoreline risers, landslides and mine benches. The negative result says this exact statistic and emission rule are less effective at recovering withheld mapped faults than the recomputed baseline. It does not prove that scarps or LiDAR are generally uninformative.

The input descriptor is an owner-mirrored, hash-pinned derivative of USGS 3DEP tiles. Its sidecar reports 706 of 716 tiles succeeded and explicitly calls the descriptors uncalibrated terrain measurements. Mirror integrity does not authenticate organizer provenance or complete coverage.

## GEMSDOE32 and the nine priority sites

The prior byte forensic result remains the strongest explanation available for the owner-reported GEMSDOE32 value 0.2778: its 37,654-dot artifact equals the solo raster after deleting 2,545 catalogue-near dots, with no additions. Reducing low-credit prediction mass can improve the Tversky denominator while spaced dots preserve some triangular-kernel coverage. This proves pruning construction, not hidden-label causation or receipt-linked score attribution.

The site's current nine-row table names each site's highest owner-reported historical artifact and clearly labels every one as unverified and not approved. None is an eligible new submission. S19 is unique but fails performance. Consequently the evidence-based submission choice today is **none**. There is no defensible evidence that S19 would exceed 0.2778, 0.3195 or 0.4413; the latter two are historical/conflicting leaderboard context, not projections for this raster.

## Official/source links for manual review

- [DrivenData problem, metric and submission format](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/)
- [DrivenData public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/)
- [Official reference solution](https://github.com/drivendataorg/gems-prize-reference-solution)
- [USGS 3DEP data catalog](https://data.usgs.gov/datacatalog/data/USGS:77ae0551-c61e-4979-aedd-d797abdcde0e)
- [USGS GeoDAWN data page](https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and)
- [DOE GDR compilation 1391](https://gdr.openei.org/submissions/1391)

The non-GitHub pages were not newly fetched by the batch runtime in S19. Their most recent observed status and claim boundaries remain in the repository source ledger and S18 official-source review; links are provided for manual review, not represented as fresh authentication.

## Next work and limits

1. Do not retune S19 on this spent holdout or submit its TIFF.
2. Create a new preregistered lane from the remaining ranked hypotheses only after synchronizing the parallel registry.
3. Prefer a direct displacement observable—repeated piercing-marker offsets or ordered flexural flank pairs—over another scalar scarp-strength reweighting.
4. Preserve separate roles: automated evidence can establish promotion eligibility; only the selector may choose a weekly slot after checking the authenticated account allowance.
5. A filename/hash-bound submission-page receipt is required before labeling any result ORGANIZER-CONFIRMED.
