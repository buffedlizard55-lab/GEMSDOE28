# S18 — migration-extrapolated placement (2026-10-25)

## Lane and provenance
The current user message omits its promised single method paragraph. Autonomous interpretation:
use the **next step already recommended in knowledge/50 and ranked first in knowledge/51**,
not the closed H40-1 migration-feature lane. Session-scoped ID: `S18-MXTP` (avoids parallel H40 collisions).
No claim of an externally assigned exclusive lane; assignment remains unconfirmed. No competition upload.

**Frozen method paragraph (before outputs):** Reuse the prepared feature stack's physical `tmi` and
`iso_grav_anom` columns. Upward-continue each at 1, 2, 3 km using the shared Fourier transform;
extract HG ridges with shared NMS. Match a 1-km ridge point q1 to its nearest 2-km ridge q2,
then match q2 to its nearest 3-km ridge q3. Under a *testable linear-in-observation-height ridge-locus
model*, extrapolate q0 = 2*q1-q2. Retain shifts from 2 to 12 pixels and residual
||q3-(2*q2-q1)|| <= 3 pixels. Confidence = empirical midrank HG(q1) * exp(-residual/3).
Splat maxima at rounded q0, Gaussian smooth sigma=0.75 px, normalize each field by its own maximum,
and combine by maximum. Exclude positions within 32 px of footprint edges. These are hypotheses
about apparent contact positions, **not uniquely determined dips, source depths, fault traces or vents**.
No fitting to labels, registry rasters, or organizer scores. Threshold support at 0.25, pack using
shared probability-order packing at >=2.8 px, at most 37,654 dots, and exclude <=2 px from VISIBLE
catalogue only. Do not add any previous submission's dots.

## Ranked candidates before implementation
Qualitative *expected utility*, not projected/observed DTI. Novelty means not executed in this checkout,
not a claim that nobody else has studied the process. All use existing hash-pinned owner-mirrored
physical channels; provenance is NOT organizer authentication. No new external-data gate needed.

| Rank | Hypothesis / layers | Signature and missing-catalogue rationale | Difference from implemented work | Non-fault mimic | Expected benefit / cost |
|---|---|---|---|---|---|
| 1 | Migration-extrapolated placement; TMI + isostatic gravity | Stable multi-height HG-ridge translation; project a buried contact locus away from the standard scarp-ridge network, potentially recovering concealed extensions | H40 migration encoded offsets as classifier features but did not move the placement pool | Dipping lithologic contact or mafic dike | Best uniqueness headroom, uncertain recovery / medium |
| 2 | Paired basin-thickness hinge; depth_to_base_surf + gravity | Parallel opposite-curvature lobes in basement depth, with gravity-edge concordance, may locate buried normal-fault basin margins absent from scarp maps | Euler clusters and slope features exist; explicit paired thickness-hinge objects have not been executed | Sedimentary facies thickness boundary | Moderate / medium; depth-model provenance must be audited before execution |
| 3 | Along-strike shear/dilation transition; geod_shearrate + geod_dilaterate + TMI | Local zero-crossing of dilation flanked by high shear and a potential-field lineament could identify concealed transfer structures | Existing kinematic gates use scalar tendencies; no explicit signed transition object located in reviewed code | Distributed ductile strain or interpolation boundary | Low spatial-resolution ceiling / low |
| 4 | Terrain-conditioned radiometric sign reversal; det_elev + K/Th/U | Linear ratio reversal recurring across opposing drainage slopes may distinguish alteration conduit from topographic gamma attenuation; concealed faults need not have scarps | Scalar radiometric additions and H39-2 lineaments were proposed; cross-slope sign-consistency test not executed | Felsic contact or transported alluvium | Uncertain / medium; mirrored ratio quantization must be audited first |

Ranks 2–4 are proposals only, not alternate experiments in this lane. Geological plausibility is
not verified causal attribution. Cached physical inputs are obtainable: restored this session with
all manifest hashes matching (evidence/restore_audit.json). Source links and current access limits
will be retained in the result report.

## Budget and gates (freeze)
Maximum three experiments / two hours from initial audit (2026-10-25 22:45 UTC).
1. Build label-free surface; each TMI/gravity feature-alone AUC and combined AUC on LOSFO seed 310
   hidden systems (negative pool >=600m from hidden). AUC or inverted AUC >0.90 => stop.
   Compare **surface before placement** with every valid raster in a pinned snapshot of the nine
   requested sibling repositories' published submission directories plus pre-existing local downloads.
   Record exclusions and failures, not silent skips. Spearman >0.90 or support overlap within3px >0.70
   against ANY raster => duplicate, log and STOP (no final TIFF, no hide/recover fit).
2. Only if step1 passes, shared packing, then same registry tests on final dots. Any duplicate =>
   log and STOP. Otherwise write new allfinite TIFF through shared submission.write_geotiff;
   re-open and validate exact file. Research download remains NOT APPROVED unless all later gates pass.
3. Only if uniqueness passes: buffered whole-system LOSFO seeds 310–314, four geographic quadrants,
   existing shared eval_set and pooled metric. Features remain label-free; only visible-fault masks
   may affect placement. Compare against freshly recomputed H38-1 joint-on-r30-r1 (registered prior best
   candidate) using its shared helpers, not fixed submitted dots (which would mask hidden truth).
   Paired fold-block bootstrap pooled DTI and gain CIs (10,000 resamples; folds are resampling units,
   repeated seeds are not independent faults). Require gain lower95% >0, gain>0.001, positive in >=3/4
   folds and >=4/5 seeds. Do not equate outperforming one historical baseline with an authenticated
   global holdout best; the selector must resolve conflicting historical promotion records.

Existing shared evaluator bug found during audit: run_losfo_harness.eval_set calls EDT on an empty
prediction (SciPy invents distance to an implicit external background). Fix ONCE in that shared tool
by delegating to metric.dti_binary, which already handles empties and masks truth correctly. Version
and hash both helpers; synthetic regression tests. No private evaluator or submission-writer fork.

## Disposition
Promotion and slot selection are separate. No organizer score, current leaderboard, official weekly
cap or PDF contents can be confirmed over this environment's GitHub/PyPI/npm-only network.
No safe path may manufacture a unique approved TIFF after a duplicate-stop. Negative / blocked
run cards are required deliverables. A research TIFF, if reached, must be plainly NOT APPROVED.
