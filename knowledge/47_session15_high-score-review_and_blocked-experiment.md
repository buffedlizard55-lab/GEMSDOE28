# Session 15 — high-score audit, hypothesis slate, and no-slot decision

**Date:** 2026-10-25 (UTC)  
**Status:** Research/review deliverable; no new model fit, no new TIFF, no competition upload, no submission slot used.  
**Claim class:** Scores from the user prompt and repository history are not organizer-confirmed receipts unless explicitly described as such.

## Decision in brief

The cited GEMSDOE32 entry `h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros: 0.2778` is the highest numerical score in the specific GEMSDOE24/25/27/28/30/31/32/33/36 list supplied in the request. This is a statement about that supplied list, not a current leaderboard claim and not organizer verification. A cross-site GitHub audit checked in at [`evidence/cross_site_audit_2026-10-25.json`](../evidence/cross_site_audit_2026-10-25.json) identifies the owner-repository paths for the H33-2 TIFFs and pins the GEMSDOE32 tree/page identity. The immutable owner-page source recorded there is [GEMSDOE32 `docs/index.html` at tree `012e17b`](https://github.com/buffedlizard55-lab/GEMSDOE32/blob/012e17b2a115c3c0d5e7885bea625bf9657c99fc/docs/index.html). The separate audit summary [`evidence/review_2026-10-25.md`](../evidence/review_2026-10-25.md) reports that the owner page describes H33-2-B2 as pruning an existing dotted base by excluding predictions close to the catalogue, and explicitly says no organizer score exists for those artifacts. The raw H33-2 TIFF is not in this checkout; the exact raster bytes, receipt, full processing code, and score/evaluator association are unavailable here. Therefore the scientifically supportable answer is: the reported 0.2778 is **not established as an organizer score**, and its realized score mechanism cannot be independently attributed. The owner-described pruning mechanism is only a qualitative description, not evidence that it caused the reported number.

The broader user brief gives two different purported current leaderboard maxima, 0.4413 and 0.3195. The repo's only stored leaderboard read is an old one-off observation from 2026-10-03, not a live refresh. This inconsistency is unresolved. Do not report either value as current without a fresh, manually reviewed organizer page/receipt. No DrivenData page was accessed in this session.

The most credible mechanism visible in the repository's prior work for the older 0.2600 local family is emission geometry: a sparse, spatially distributed set along the same continuous ridge can preserve credit to a 300 m triangular kernel while paying less additive false-positive cost than a dense one-cell trace. That explanation is conditional on an owner-reported score-to-file pairing; it does **not** explain the absent H33-2 artifact. The filename's `zeros` suffix does not establish how outside-footprint values were encoded, what predictor was used, or whether the file was accepted. Earlier repo work also records failure of straight topology-gap interpolation against owner-reported live scoring and a distinction between interleaved catalogue holdouts and far-field tests. These are lessons, not proof of 0.2778's mechanism.

**Can we beat 0.2778?** It is scientifically possible in principle, but not established by this checkout or the scores alone. Under the competition's asymmetric DTI, a higher score requires a better trade-off between spatially credited hidden-fault pixels and false-positive mass. Pruning redundant dots near known faults can improve a proximity metric by reallocating predictions away from neighborhoods already covered by the same visible labels; however, if catalogue-distance features are not recomputed from the visible-only catalogue inside each buffered whole-segment split, that rule risks label leakage or an optimistic holdout. The cross-site page summary does not provide enough code to determine whether this was handled correctly. The repository's own historical analysis argues that re-thinning the same predictor cannot bridge a large recall gap without genuinely new information. Independent geomorphic, thermal, geophysical or seismic evidence remains a plausible route, subject to strict falsification controls. The owner-site `0.2778` is not an organizer-confirmed score or a valid local holdout baseline, and no candidate here has been shown to beat it on matching hidden truth. Therefore the answer today is **not proven; no new higher-scoring TIFF is authorized**.

## Evidence review and score hygiene

- The user-supplied scores are retained as user claims, not receipts. The local repository does not include the H33-2 TIFF bytes or a submission-page receipt. [`evidence/cross_site_audit_2026-10-25.json`](../evidence/cross_site_audit_2026-10-25.json) identifies the owner-repository paths `docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-nan.tif` and `...-zeros.tif` at tree `012e17b2a115c3c0d5e7885bea625bf9657c99fc`. No numerical correlation/overlap test is possible without the underlying rasters.
- Repo artifacts `evidence/why_026_won.json`, `knowledge/01_why_0.2477_won_and_the_ceiling.md`, `evidence/scored_corpus.json` and `registry/live_scores.json` support a local, conditional geometric interpretation of the H19-5 d=2.8/d=1.5 family. They do not establish a causal explanation of H33-2's 0.2778.
- Repo's documented GEMSDOE28 results are internal HOLDOUT-DTI / LOSFO measurements, not competition scores. They use a catalogue-derived surrogate truth and cannot establish the performance on truly omitted expert labels. No candidate in the repo has an organizer-confirmed GEMSDOE28 score.
- The highest score in the user-supplied local-site list is 0.2778 (GEMSDOE32); next are 0.2750 (GEMSDOE36), 0.2710 (GEMSDOE28 H36-1 as reported by the prompt), 0.2708 entries (GEMSDOE28/31), 0.2649 (GEMSDOE28), 0.2632 (GEMSDOE33), and 0.2600 entries (GEMSDOE25/30). Do not treat this ordering as current leaderboard rank or comparable experiment evidence: it mixes external owner-site reports, different artifacts, and no accessible raw files/evaluators. The user's distinct `0.4413` and `0.3195` leaderboard claims remain a discrepancy for review.

| Site | Highest result quoted by the user for this site | Evidence status in this checkout |
|---|---|---|
| [GEMSDOE24](https://buffedlizard55-lab.github.io/GEMSDOE24/) | `0.2477` | User-supplied owner-site result; no organizer receipt bound to a local file here. |
| [GEMSDOE25](https://buffedlizard55-lab.github.io/GEMSDOE25/) | `0.2600` | User-supplied owner-site result; repo has conditional local analysis, not organizer confirmation. |
| [GEMSDOE27](https://buffedlizard55-lab.github.io/GEMSDOE27/) | `0.2449` | User-supplied owner-site result; repo's historical claim remains owner-reported. |
| [GEMSDOE28](https://buffedlizard55-lab.github.io/GEMSDOE28/) | `0.2710` (`h36-1-rung30-blind-r1`), plus `0.2708`, `0.2649` | Supplied by user; repo records H36-1 as unscored/not organizer-confirmed. |
| [GEMSDOE30](https://buffedlizard55-lab.github.io/GEMSDOE30/) | `0.2600` | User-supplied owner-site result; no local receipt/raster association checked. |
| [GEMSDOE31](https://buffedlizard55-lab.github.io/GEMSDOE31/docs/) | `0.2708` | User-supplied owner-site result; no local artifact/receipt available. |
| [GEMSDOE32](https://buffedlizard55-lab.github.io/GEMSDOE32/docs/index.html) | `0.2778` (`h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros`) | User-supplied highest cited result; local cross-site audit identifies raster paths and a prose summary of catalogue-proximity pruning, while the raw bytes/full code/receipt remain absent. |
| [GEMSDOE33](https://buffedlizard55-lab.github.io/GEMSDOE33/) | `0.2632` | User-supplied owner-site result; no local artifact/receipt available. |
| [GEMSDOE36](https://buffedlizard55-lab.github.io/GEMSDOE36/docs/) | `0.2750` | User-supplied owner-site result; no local artifact/receipt available. |

Do not state that H36-1 got `0.2710` as fact about this repo: the local manifest labels it `UNSCORED`, and the user's external-site report cannot be independently linked to the file in this checkout. Manual-review site links are provided above; they were not fetched in this session.

## Candidate hypotheses for future preregistration (none run; proposals are not assigned lanes)

These four proposals are ranked by qualitative expected information gain × tractability. No numerical DTI improvement is assigned: the feature stack is absent and no evaluation was run. They are distinct from already implemented methods locally, but cross-repository/global novelty is **not established**. A missing assigned method paragraph means none is authorized for this parallel session.

### Rank A — magnetic/gravity edge-migration consistency across upward-continuation heights

- **Layers/signature:** competition TMI/magnetic and isostatic-gravity fields; compute NaN-safe, edge-tapered upward continuations over several heights and trace the signed lateral migration of matched gradient ridges. The target is coherent depth-dependent edge movement, not a single static edge or Euler solution.
- **Why a missing fault could appear:** a dipping density/susceptibility boundary can produce a systematic edge shift with continuation height even where no surface rupture is mapped; map the structure as a subsurface contact/fault candidate rather than asserting fault identity from magnetics alone.
- **Difference from implemented work:** prior H28-1 computes cross-scale edge coherence on existing grids, and Euler work estimates source locations/depth under structural-index assumptions. This hypothesis tests the *trajectory/migration of an edge with continuation height*, a different observable; verify code inventory before calling it novel.
- **Named non-fault mimic:** dipping lithological contact or dike with magnetic/density contrast.
- **Expected improvement/cost:** highest qualitative information potential; medium implementation cost. No numeric DTI projection.
- **Data gate:** uses competition feature bands in principle, but the exact cached stack and template are absent in this checkout. Restore hash-pinned owner mirrors and verify band metadata before viability. This is the leading research proposal, not the authorized lane.

### Rank B — paired, signed cross-scarp change points in elevation and radiometry

- **Layers/signature:** DEM-derived elevation plus radiometric K/Th or U/Th channels; estimate along-strike paired flank change points after detrending the regional field. Target co-located, signed material/relief contrast, not generic co-location of a radiometric ridge with a scarp.
- **Why a missing fault could appear:** repeated, consistently oriented changes across several aligned transects may reveal subtle or degraded fault scarps whose individual elevation contrast is weak, while alteration-related radiometric asymmetry can provide an independent corroboration channel.
- **Difference from implemented work:** existing H32 structural-step tests and H38 heat-flow/Euler work do not test paired signed cross-fault change points in radiometry and topography as a joint statistic. Existing radiometric work in other sites is indicated by owner-repo inventories; cross-repo novelty is not proven.
- **Named non-fault mimic:** lithologic contact, alluvial-fan boundary, paleoshoreline or road/earthwork can create aligned topographic/radiometric breaks.
- **Expected improvement/cost:** moderate qualitative potential; medium cost. No numeric DTI projection.
- **Data gate:** official GeoDAWN survey landing page supplied in the project: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and . The current sandbox cannot fetch that host, and the required radiometric bands are not in the local checkout. Treat as not viable until exact official data or hash-pinned input bytes, units, coverage, and license are verified.

### Rank C — basin-scale drainage-divide asymmetry reversals aligned with an independent magnetic edge

- **Layers/signature:** conditioned DEM and candidate magnetic edges; measure multi-basin divide asymmetry and direction reversals along a mapped corridor, with basin-scale cross-validation rather than single-channel curvature peaks.
- **Why a missing fault could appear:** distributed tilting associated with a concealed normal fault may perturb drainage divides and basin geometry where a sharp scarp is absent.
- **Difference from implemented work:** current terrain descriptors and structural-step work are pixel/local-scape features; this tests basin-scale drainage-network response. H38-4 drainage neotectonics was previously proposed but not established as an implemented, tested pipeline, so this is a refinement of an old proposal—not a brand-new concept.
- **Named non-fault mimic:** lithology-controlled erosion, stream capture, or climatic/tectonic base-level change.
- **Expected improvement/cost:** moderate but highly uncertain potential; high cost due hydrologic conditioning, DEM tile processing, and scale/coverage QC. No numeric DTI projection.
- **Data gate:** official USGS 3DEP 1 m DEM catalog: https://data.usgs.gov/datacatalog/data/USGS:77ae0551-c61e-4979-aedd-d797abdcde0e . DEM tiles are not present; exact footprint tile availability/bytes were not checked in this restricted session. Not viable until obtainable and coverage is verified.

### Rank D — depth-coherent lateral MT conductance-boundary migration plus gravity

- **Layers/signature:** USGS multi-depth magnetotelluric conductance slices and gravity; follow a lateral conductance boundary's apparent position across depth slices and require a separate gravity-edge corroboration, rather than using one absolute-conductance threshold.
- **Why a missing fault could appear:** a concealed fluid-bearing or altered structure may produce a coherent conductive boundary beneath cover without a Quaternary surface trace.
- **Difference from implemented work:** differs from the single-depth conductance × dilatation proxy and prior proposed pipe-alignment test by targeting a *depth-dependent boundary trajectory* with gravity corroboration. Verify against queued H38-3 and other site code before claiming novelty.
- **Named non-fault mimic:** clay-rich sedimentary basin margin or a lithologic conductor.
- **Expected improvement/cost:** low-to-moderate qualitative potential; high cost and currently data-blocked. No numeric DTI projection.
- **Data gate:** official USGS Bedrosian et al. release, DOI 10.5066/P9TWT2LU: https://doi.org/10.5066/P9TWT2LU . The exact source item/bytes and in-footprint coverage were not verified obtainable in this session; under the user protocol this hypothesis is **not viable yet**, not a runnable candidate.

### Rank summary

A leads because it can be formulated from the competition's geophysical feature families and tests new depth-sensitive edge information, though even its cached inputs are absent. B and C require geophysical/DEM channels whose exact local bytes and coverage remain unverified. D requires an official MT archive explicitly not verified obtainable. These ordinal rankings are design judgments, not HOLDOUT-DTI results, score projections, or approval to run.

### Leakage/holdout preregistration requirements before any experiment

1. Resolve the missing parallel-run lane paragraph and pick a single hypothesis, not a blend of the five.
2. Restore the hash-pinned competition template, labels, full cached feature stack and the source layers for the selected hypothesis. The present checkout contains `data/manifest.json`, but no `data/*.tif`, prepared feature array, or cached full feature stack. Do not replace missing inputs with outputs from prior submissions.
3. Use one preregistered whole-fault-segment spatial holdout with a buffer, derive all catalogue-derived features only from visible segments, and mask visible traces pixel-exactly. Apply the specified DTI α=0.2, β=0.8, 300 m triangular kernel and compute a paired 95% CI. The existing `src/gems27/holdout.py` is explicitly catalogue-internal and has known bias; the user protocol requires whole-segment hide-and-recover with buffer, so first audit/fix the shared harness in the template if it does not implement that exact design. Do not privately fork it.
4. Test each feature alone for AUC/leakage before any combination; any AUC >0.90 is a leak warning until explained. Also test spatial overlap and rank correlation against every registry raster both before placement and after placement; if Spearman |rho| >0.90 or >70% of dots are within 3 px of a registry raster's positive pixels, log duplicate/stop. These cannot be computed now because registry source rasters are absent.
5. A submission TIFF may be written only after the candidate beats the frozen current holdout comparator and passes the independent format/registry-uniqueness audit. No submission slot is authorized by this review.

## Pass review

- **Pass 1 — implementation/review:** reviewed repository objective, score/provenance ledgers, available candidate artifacts, holdout code, submission writer and static site. Identified H33-2 artifact absence, score provenance gap, branch-local missing cached rasters and unspecified lane.
- **Pass 2 — defect/assumption review:** checked that reported site scores are not being represented as organizer scores; separated prior OOF/LOSFO results from competition scores; flagged stale leaderboard and conflicting maxima; did not infer H33-2's method from its filename.
- **Pass 3 — requirements review:** ranked five distinct, unrun research directions and specified data/access gates, controls and protocol. The top candidate cannot be validated in this checkout, so there is no honest holdout DTI, correlation/overlap measurement or unique candidate TIFF. Negative/no-slot disposition is the outcome, not a fabricated positive result.

## Official/manual-review sources

The owner-page characterization and H33-2 path above come from the already checked-in `evidence/cross_site_audit_2026-10-25.json` and `evidence/review_2026-10-25.md`, which record an immutable GEMSDOE32 tree SHA. A fresh GitHub API content fetch in this session returned HTTP 403 (API rate limit), so the page bytes were not independently re-read here. The sources below are provided for manual review; non-GitHub official pages were not fetched in this network-restricted run.

- [DrivenData GEMS overview/problem description](https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/) (official competition page; score metric and task).
- [DrivenData GEMS about page](https://www.drivendata.org/competitions/306/competition-doe-gems/page/968/) (official competition background).
- [DrivenData official public leaderboard](https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/) (manual review only; not accessed in this session).
- [DOE GDR #1391 INGENIOUS compilation](https://gdr.openei.org/submissions/1391).
- [USGS Great Basin MT conductance ScienceBase release](https://www.sciencebase.gov/catalog/item/62979746d34ec53d276c113b).
- [USGS Great Basin heat-flow ScienceBase release](https://www.sciencebase.gov/catalog/item/6297d2fad34ec53d276c5b28).
- [USGS 3DEP 1 m DEM catalog](https://data.usgs.gov/datacatalog/data/USGS:77ae0551-c61e-4979-aedd-d797abdcde0e).
- [USGS ANSS ComCat FDSN API](https://earthquake.usgs.gov/fdsnws/event/1/) (availability not verified from this sandbox).

## Run card (negative / blocked)

See [`evidence/session15_review.json`](../evidence/session15_review.json). No score is entered: there was no eligible experiment run. No projected value is used as a holdout result.
