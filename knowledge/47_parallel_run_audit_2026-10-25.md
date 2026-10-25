> **Later same-date update:** data, the existing feature cache and pinned shared tools have now been restored and audited. Absence statements below record the earlier observation, not current blockers. No new TIFF, score or assigned lane was created. See [current review](51_current_review_and_next_steps.md).

# Parallel-run audit — 2026-10-25

## Decision: NEGATIVE / NOT READY TO SUBMIT

No new competition TIFF was generated, no slot was selected, and no competition upload was attempted. This is a negative deliverable, not a successful model run. The missing assigned method lane makes a new scientific experiment incompatible with the parallel-run instructions. Do not manufacture uniqueness by renaming, flipping bits, moving old dots, or adding random dots.

## Verified local findings

- `data/` initially contains only `manifest.json`; the feature cache is absent in this checkout. Historical restoration receipts do not establish that files exist in this runtime.
- `src/gems27/holdout.py` hides components **after** intersecting with quadrants. Therefore a connected whole fault can be cut at a quadrant boundary. `make_split` does not remove a buffer from the visible catalogue. Existing historical metrics must not be retroactively called compliant with the new protocol.
- The exact requested shared-template files `evaluate_holdout.py` and `submission_writer.py` are absent locally. There are existing shared `holdout.py`, `metric.py`, and `submission.py` modules; no private evaluator was created. The template repository/path was not supplied.
- `submission.py` previously checked only the template's footprint count on write. It now calls the existing grid validator on write and independent verification. A shifted grid and wrong CRS have regression tests.
- The new `promotion.py` fails closed on absent lane, metrics, confidence intervals, feature-alone leakage canaries, surface/final-dot comparisons, incomplete registry, or format evidence. It checks the evidence schema, **not the authenticity of supplied evidence**. It is not a working end-to-end evaluator or uniqueness engine.

## Cross-site inspection

All nine requested owner repositories were inspected through the GitHub API. Immutable tree IDs, page URLs and hashes, raster paths, and requested evaluator/writer filenames are recorded in `evidence/cross_site_audit_2026-10-25.json`. Owner sites are secondary project reports, not official competition evidence. A tree snapshot is not a complete downloaded raster registry; correlation and dot overlap remain unmeasured.

### Why GEMSDOE32 might work — and what is not known

The inspected GEMSDOE32 page calls the leading artifact H33-2-B2: a prune of an existing dotted base, excluding dots close to the catalogue. It explicitly says no organizer score exists for its artifacts. That statement conflicts with the supplied score claim; it may simply be stale. There is no submission-page receipt available to resolve it. **No ORGANIZER-CONFIRMED score is asserted here.** The user supplied inconsistent leaderboard maxima; none is adopted as current.

Mechanistically, a triangular proximity reward can saturate when several dots cover the same target neighborhood, while extra positive mass still incurs false-positive cost. Sparsifying redundant coverage can therefore improve a distance-weighted Tversky objective without discovering a new fault. Deleting catalogue-adjacent predictions can also change allocation toward unmapped targets. Neither mechanism establishes geothermal productivity. The competition task is fault mapping, not a direct geothermal-vent inventory. Improving placement and improving geological detection are different experiments.

Can a new submission exceed the reported incumbent? Possibly, but there is no defensible quantitative forecast from these records. A hidden-set score cannot be inferred from a simulated truth model or historical mean fold scores. Require paired buffered hide-and-recover evaluation, pooled sufficient statistics, and a segment-level bootstrap before promotion. Historical bests must be rerun under the same compliant instrument.

## Ranked hypotheses — provisional design proposals, NOT assigned lanes

Expected improvement is ordinal scientific judgment, not a score projection. No proposal is claimed globally novel across all owner implementations. The local `src/gems27` and knowledge inventory was reviewed, but exhaustive cross-repository source-code novelty is unverified. No experiment was run.

| Rank / cost | Layers and signature | Why potentially missing from catalogue | Distinction and named non-fault mimic |
|---|---|---|---|
| A / medium | Magnetic and gravity grids: measure lateral **edge migration with upward-continuation height**, fit signed migration consistency across scales rather than Euler depth | A buried dipping density/susceptibility boundary can persist where a surface scarp is absent | Alternative to implemented Euler-source clustering and static gradient agreement; a dipping lithological contact or dike can mimic it. New continuation-migration feature not established in local inventory. |
| B / medium | Elevation and radiometric channels: along-strike **paired cross-scarp change points** after removing regional elevation trends | Mutually consistent offsets of material and relief may expose eroded or subtle scarps missed by a single-channel threshold | Tests signed flank contrasts, not merely radiometric ridge coincidence; alluvial contacts, paleoshorelines and roads are confounders. Existing structural-step work may overlap; source-level disambiguation required. |
| C / medium–high | DEM: multi-basin **drainage-divide asymmetry reversals** aligned along candidate magnetic edges | Distributed tilting around a concealed normal fault may affect drainage without a crisp surface break | Network/topographic response, not the existing scarp or heat-flow corroboration; lithology-controlled erosion and stream capture mimic it. Requires hydrologic conditioning and a defensible resolution audit. |
| D / high, currently blocked | USGS multi-depth MT conductance plus gravity: depth-coherent **lateral conductance-boundary migration**, not absolute conductivity | A concealed fluid-bearing structure could cross sedimentary cover | Different observable from queued H38-3 pipe alignment; clay-rich sedimentary basin margins mimic it. Official source: Bedrosian et al., https://doi.org/10.5066/P9TWT2LU . Specific item must be resolved via the DOI; not verified obtainable this session, so NOT viable yet. |

A–C are conditional on actual feature-band inventory and restoring pinned inputs; no new external dataset is asserted necessary. None may be executed until an assigned lane is present and cross-repository novelty is checked. D is explicitly blocked rather than silently assumed available. Previous next steps (MT pipe alignment and shoreline suppression, `knowledge/46`) remain queued; executing them now would invent the missing lane.

## Sources and verification limits

- Official organizer reference: https://github.com/drivendataorg/gems-prize-reference-solution . README retrieved through GitHub this session. It supports training with CPU-only environments as well as GPU acceleration; the old blanket claim that a GPU is required is incorrect.
- Official problem/metric/format: https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/ . Link retained for review; not retrieved in this network-restricted runtime.
- Official leaderboard: https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/ . Not verified current; no claim about weekly cap or current leader.
- Official USGS survey landing page supplied by owner: https://www.usgs.gov/data/geodawn-airborne-magnetic-and-radiometric-surveys-northwestern-great-basin-nevada-and . Not fetched this session.
- Prior local evidence: `evidence/why_026_won.json`, `knowledge/46_session14b_closeout.md`. Historical proxy results are not upgraded to current HOLDOUT-DTI evidence.

Outbound access is restricted to GitHub and package registries. Official non-GitHub sources, Dropbox downloads, and organizer-authenticated data cannot be verified directly here. GitHub mirrors are obtainable but remain owner mirrors, not organizer-authenticated data. No full-data restoration was attempted after the lane blocker was established; this is not a claim that restoration is impossible.

## Next execution prerequisites (automated pipeline, no human inspection gate)

1. Supply the missing lane and shared-template location through project configuration; retain a complete, hash-pinned raster/surface registry for the nine sites and other parallel lanes.
2. Repair whole-segment buffered splitting **in that shared template**, then rerun baselines there. Do not create a private fork or silently rewrite historical evidence.
3. Restore pinned inputs and rebuild catalogue-based features from visible segments independently for every split. Run each feature alone; quarantine high-AUC canaries.
4. Measure surface correlation before placement; stop and record duplicate if the limits are exceeded. Measure final-dot rank correlation and directed within-radius overlap against every registry member.
5. Run at most the specified experiment budget, score pooled DTI and segment-bootstrap confidence intervals, and compare paired gains against the frozen best. Only then write a genuinely new allfinite TIFF using the shared writer and independently validate actual bytes and hashes.
6. Populate a machine-readable run card and call the evidence gate. Promotion does not select a weekly slot. Automated competition upload is neither implemented nor attempted.
