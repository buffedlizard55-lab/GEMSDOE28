# Session 22 preregistration — S22-MOFR (H44-1: potential-field marker-offset / piercing-point realignment)

Frozen before any holdout number is read. Do not retune thresholds after seeing a result; any change
after this point is a new, separately numbered hypothesis.

## 1. Lane and method paragraph

**Layers.** Organizer-supplied `tmi_hg` (total-magnetic-intensity horizontal gradient, training_features.tif
band 3) and `iso_grav_anom_hg` (isostatic-gravity horizontal gradient, band 18). These are the raw
Cordell & Grauch (1985) horizontal-gradient-magnitude basement-contact edge detector, already present
in the organizer feature stack (not recomputed by us).

**Physical signature.** A concealed, uncatalogued fault truncates and laterally displaces
("piercing-point" offsets) the linear ridge a basement contact produces in the HGM field, exactly the
way a structural geologist restores a marker horizon across a fault throw. The detector:
1. extracts a 1-px ridge skeleton of each field with the repo's existing `ridge_nms` +
   `skimage.morphology.skeletonize`,
2. assigns each ridge pixel a strike with the repo's existing `ridge_strike_degrees`,
3. finds ridge endpoints (open tips),
4. pairs endpoints from DIFFERENT connected ridge segments whose strikes agree (<=20 deg, the same
   tolerance already used by `newinfo.steppover_links`), whose along-strike gap is 200-1500 m, whose
   perpendicular offset is 100-800 m, and whose own local outward heading points at its partner
   (<=35 deg), and
5. marks the straight connector between each matched pair as the candidate fault trace (the same
   "shortest breaching segment" convention `newinfo.steppover_links` already uses for catalogue
   step-overs).

**Why this should catch a fault the catalogue is missing, not one it already has.** The test never
reads the catalogue, a candidate trace, or any catalogue-adjacency distance; it is purely a geometric
property of two independent geophysical rasters. A concealed fault with little or no preserved surface
scarp (LiDAR-silent) can still truncate a basement contact at depth, so this targets exactly the class
of structure that mapped-trace-based or scarp-based detectors (the great majority of this repo's prior
hypotheses) cannot see.

**How this differs from everything already implemented here.** `potential_edges.py` (H28-1) scores
contact-gradient AMPLITUDE/concordance, not geometric discontinuity. `euler.py` / `heatflow_euler.py`
(H31/H32/H36/H38) invert source DEPTH from multiple upward-continuation levels. `migration.py`'s
`ridge_displacement_from_hg_levels` tracks how the SAME ridge moves with continuation HEIGHT (a dip
estimator), not how two SEPARATE ridge segments are offset at one height. `newinfo.steppover_links`
needs a `FaultGraph` already built from candidate/catalogue strands; this module needs none.

**Non-fault mimics this test is vulnerable to** (reported honestly, not hidden): a strike change at an
intrusive contact corner, interference from an unrelated crossing contact, a magnetic/gravity
survey flight-line or levelling seam (a straight, grid/compass-aligned artifact), two unrelated nearby
contacts that satisfy the geometry by chance, and a genuine lithologic contact offset with no
Quaternary slip (i.e. an old, inactive structure). None of these are excluded by the geometry alone;
only the quantitative HOLDOUT-DTI result below can show whether the net effect is useful.

## 2. Evaluator (reused, not rebuilt)

`data/shared_template/src/gems/holdout.SegmentHoldout(footprint, labels, buffer_px=15)` (hash-verified
via `gems27.shared_template.verify_assets`), `pooled_dti` (alpha=0.2, beta=0.8, 300 m triangular
kernel), `canary` (single-feature AUC), `data/shared_template/src/gems/novelty.compare_registry`
against the fetched byte-identical copies of the 9 requested sites
(`evidence/priority_repository_audit.json`, refreshed this session through the GitHub API, plus every
other TIFF already in `docs/downloads/`), and `data/shared_template/src/gems/submission.write_submission`
/ `check_variants` for the exact output file. No private fork of any shared tool.

## 3. Comparator (frozen, computed fresh this session)

Per `SegmentHoldout` fold: a `HistGradientBoostingClassifier` (`max_iter=100, max_leaf_nodes=31,
learning_rate=0.08, l2_regularization=5.0`) trained ONLY on `fold["train"]` with `fold["visible"]`
labels on the 32-band label-free `prepared/features.npy` cache (identical hyperparameters to every
prior session's baseline), emitting `oof_detector.build_oof_dotted_base` at the same
`PRE_THIN_FRAC`/`thin_d=2.8` budget used by the H19-5 lineage. This is the same "retrained visible-only
baseline" family cited in knowledge/57 and knowledge/61; it is recomputed fresh here (not copied from
another session's JSON) so today's gain/loss numbers are internally paired and comparable to each
other, per the irregularity-registry rule never to pool numbers across sessions.

## 4. Experiments (budget: 3; stop immediately on lane drift or a failed gate)

1. Leakage canary on `tmi_hg` raw |HGM|, `iso_grav_anom_hg` raw |HGM|, and the combined
   marker-offset `support` surface (continuous), plus pre-placement registry comparison of `support`.
   Stop if canary AUC > 0.90 on any feature, or registry rank correlation/overlap exceeds the
   0.90/70% lane-drift rule.
2. Final dot placement (both the `union` variant — either field alone is enough — and the
   `corroborated` variant — both fields must agree within 2 px — are built and compared; only the
   variant that passes the final registry novelty check is written to disk), exact-format
   validation, and final registry comparison of the written dots.
3. One `SegmentHoldout.summarize` evaluation of the candidate vs the fresh retrained baseline on all
   four folds, paired spatial-block bootstrap CI, and the promotion gate (candidate pooled DTI greater
   than baseline, CI lower bound > 0, and positive in >= 3 of 4 folds).

## 5. Promotion rule

Promote only if experiment 3's gate passes AND experiments 1-2 passed their canary/registry gates. A
negative result on any gate is reported in full (a negative result is a deliverable) and **zero**
weekly submission slots are spent regardless of outcome; slot selection is a separate, later step.

## 6. External data

None required beyond what is already pinned (`data/manifest.json`, `registry/protocol_assets.json`).
If a future increment of this hypothesis needs USGS ComCat hypocentres or 3DEP DEM tiles, those hosts
(`earthquake.usgs.gov`, `www.usgs.gov`, `apps.nationalmap.gov`) are outside this sandbox's allowed host
list (`github.com`, `codeload.github.com`, `api.github.com`, `registry.npmjs.org`, `pypi.org`,
`files.pythonhosted.org`) and are explicitly deferred, not silently assumed obtainable.
