# Preregistration H32-1 — structural-step coherence of the conductivity / conductive-base / strain group

**Written before any H32-1 classifier fit or holdout run.** The runner refuses to execute unless the
working bytes of this file match the committed Git blob, exactly as the H31-1 runner does.

## Falsifiable geological hypothesis

**Hypothesis.** Spatial *derivative* structure of the subsurface-conductivity group — depth to the
conductive base (`depth_to_base_surf`, band 15), surface conductivity (`cond_surf`, band 17) and the
geodetic strain-rate second invariant (`geod_2ndinv`, band 4) — carries fault information that the
shipped row-wise detector cannot represent, because a pixel-independent gradient-boosted model sees
only band *values* and never a spatial derivative. A fault that displaces the conductive base, or
that bounds a conductive basin fill, produces a localized step: a ridge of |grad| with an inflection
across the trace. Such a structure can be blind at the surface, which is the class the Quaternary
surface-rupture catalogue is expected to miss.

**Target.** Fault-location pixels, judged on the same spatially blocked catalogue hide-and-recover
holdout the repository already uses for every arm. This is a *proxy*; it cannot see the far field
(100 % of proxy truth sits on the published catalogue, `evidence/arm_habitat_decomposition.json`),
and a pass is not evidence of organizer-label performance.

**Not claimed.** That `depth_to_base_surf` is a verified fault-sensitive surface, that a step is
diagnostic of faulting (lithologic contacts, conductivity contrasts and interpolation artefacts are
equally plausible), or that any gain transfers to the hidden expert labels. The band's derivation is
documented only by its embedded description and the USGS GeoDAWN release metadata.

## Difference from prior work in this checkout

* The 32-band prepared matrix contains these three bands as **values only**; no arm in this
  repository has ever added a spatial derivative of any conductivity / conductive-base / strain band.
  A row-wise HistGradientBoostingClassifier cannot construct one from neighbouring rows.
* H28-1 built a scale-space gradient arm for the *magnetics/gravity* pair and passed its gate
  (seeds 140-149, +0.00294884 paired DTI). H32-1 applies the same frozen transform pattern to a
  different physical group; it therefore tests whether that pattern generalizes rather than
  re-testing H28-1.
* H27-12/Addendum D tested radiometric ratios and thermal point distances (near-null on this proxy)
  and an SGMC mask (proxy gain, rejected as catalogue-proximity habitat). Neither used derivative
  structure of the conductivity group.
* H31-1 (Euler depth clusters) failed its frozen screen on seeds 160-169 and is closed.

## Frozen transform (`src/gems27/structural_step.py`)

Six deterministic, label-free features, all float32 in [0, 1], exactly 0 outside the valid mask:

1. `struct_cb_step_300m` — |∇(G_3(depth_to_base))|, robust-scaled at the in-footprint 5th/95th
   percentiles (300 m scale).
2. `struct_cb_step_1000m` — |∇(G_10(depth_to_base))|, same scaling (1 km scale).
3. `struct_cb_curvature_1000m` — |Laplacian(G_10(depth_to_base))|, same scaling.
4. `struct_cb_cond_concordance_1000m` — min(scale_1km(depth), scale_1km(cond)) where **both** 1 km
   gradient magnitudes are at or above their own in-footprint 10th percentile, else 0.
5. `struct_cb_cond_orientation_agreement_1000m` — |cos| between the two 1 km gradient normals under
   the same both-strong condition, else 0.
6. `struct_strain_step_1000m` — |∇(G_10(geod_2ndinv))|, same scaling.

Valid = footprint ∧ finite ∧ |value| < 1e30 ∧ value ≠ declared nodata for **all three** bands;
nearest-valid fill supplies filtering context only, and every output outside the valid mask is 0.
Grid, CRS and transform are asserted to equal the template before any read; no resampling.

## Frozen experiment

* Features: the existing 38-column control (32 prepared + the six H28-1 potential-field edge
  features, cached at `prepared/h28_1_edge_features.npy`) plus the six H32-1 columns = 44.
* Model: the repository's frozen `oof_detector.fit_predict_oof_probabilities`, identical
  hyper-parameters, negative ratio 10, `seed=2026`, 4 spatial quadrant folds, 600 m buffer.
* Emission: `build_oof_dotted_base(..., budget_frac=PRE_THIN_FRAC, thin_d=1.5)` then the frozen
  H27-4 r1 flank prune (`distance to known catalogue > 1 px`) then the deterministic T-v2 link dots
  at ≥ 3 px from the pruned set — the exact `*_best_Tv2_prune_r1` recipe used by H28-1.
* Control: the same recipe on the 38-column matrix, in the same run, same folds, same seeds.
* Seeds: **170-179** — a fresh decade reserved by the local seed ledger (`evidence/h31_1_seed_reuse_audit.json`
  records 160-169 consumed by the H31-1 screen; 170-179 unused locally). Exactly ten seeds, one run.
* Response: paired DTI difference (candidate − control) per cell, using the repository's balanced
  metric implementation with the same error model as H28-1's runner.

## Promotion gate (frozen; no threshold may be tuned afterwards)

1. mean paired ΔDTI ≥ **+0.0010**;
2. improvement in ≥ **3 of 4** folds;
3. improvement in ≥ **8 of 10** seeds;
4. data checks: all OOF probabilities finite and in [0, 1]; all feature values finite and in [0, 1];
   ≥ 95 % of footprint cells valid for all three source bands; zero prediction pixels on known
   catalogue; 40 cells × 2 variants evaluated.

**Failure means**: no confirmation run, no retuning on these seeds, no submission candidate, and the
hypothesis is recorded as a closed negative result. **Passing means**: eligible for a fresh-seed
confirmation (180-189) with frozen code, then an exact-file audit — never an automatic upload.
