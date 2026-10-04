# 40 — Session 14 Closeout: `H36-1` Far-Field Verified, `H38-1` Multi-Physics Corroboration Validated, and Next Steps

**Date:** 2026-10-03 (UTC)
**Branch:** `arena/01a1040a-gemsdoe28`

---

## 1. What Was Accomplished in Session 14

1. **Autonomous Data Restoration & Baseline Verification:**
   - Restored and SHA-256 verified all `17/17` competition rasters and vector inputs (`evidence/restore_audit.json`: PASS) and rebuilt `data/prepared/features.npy` (`(5167373, 32)` `float32`, SHA-256 `83ed2704ee2de03cf8b1c8f2966fcf71813501df97c1c35400e6c0415393f6dc`).
2. **External Layer Bridge Audit & Irregularity Flag (`IRR-2026-10-03-78`):**
   - Verified that the GitHub Actions runner bridge (`evidence/external_layer_inventory.json`, `2026-10-03T21:47:18Z`) already downloaded, pin-verified (`130,154,244` B, SHA-256 `e7fd62c6…`), and committed `docs/data/sb_heat_flow_in_footprint.{csv,json}` (`4,217` records across 3 layers, including `2,108` borehole records in `USGS_gbHeatFlowWells_wEstimates.shp` from DeAngelo et al., 2022, DOI [10.5066/P9BZPVUC](https://doi.org/10.5066/P9BZPVUC), `1,546` inside the valid footprint, and `753` with conductive heat-flow residual `hf_resid >= 50.0 mW/m²`). Logged `IRR-2026-10-03-78` in `registry/irregularities.json` for the stale queued status in `README.md` §5 and `registry/next_hypotheses.json`.
3. **Executed Session 13's #1 Next Step (`H36-1` LOSFO Far-Field Verification on `seeds 265–269`, `knowledge/38–39`):**
   - Verified on 20 fresh far-field cells (`evidence/losfo_session14_h36_1_and_h38.json`) that `H36-1` (`rung30_blind_r1`, `b531dae0a36f`, $N = 37{,}660\text{ px}$) passes **all four frozen far-field criteria (`F1–F4`)**:
     - `F1`: `rung30_unpruned` beats matched-`N` random drop by `+0.002073` (`17/20` cells, `5/5` seeds);
     - `F2`: $e_{\text{far}}(2.8 \to 3.0) = 0.02529 < \tau_{\text{live}} = 0.054852$ (`19/20` cells below $\tau_{\text{live}}$);
     - `F3`: `rung30_blind_r1` improves raw LOSFO DTI over `base` (`d=2.8`) by `+0.001713` (`16/20` cells, `5/5` seeds, $e_{\text{far}} = 0.01359$, `+0.005810` over matched-count random drop across `20/20` cells);
     - `F4`: `h27_4_blind_r1_d280` loses **exact zero** far-field truth credit (`sum_tp_removed = 0.0` across `20/20` cells) while improving DTI by `+0.002249` across `20/20` cells.
4. **Generated 5 Untried Candidate Geological Hypotheses (`H38-1` through `H38-5`, `knowledge/37`) and Validated Top Candidates (`H38-1` & `H38-2`, `knowledge/38–39`):**
   - Implemented `src/gems27/heatflow_euler.py` (`tests/test_heatflow_euler.py`) and evaluated 5 pre-declared arms (`h38_1_joint`, `h38_1a_heatflow`, `h38_1b_euler_lineament`, `h38_2_low_relief_euler`, `h38_1_joint_on_r30_r1`) on **both** fresh LOSFO far-field seeds `265–269` (`20` cells) and fresh interleaved spatial-CV seeds `270–279` (`40` cells):
     - **`h38_1_joint` (`ALL_PASS = True` on LOSFO):** `+0.000792` mean LOSFO $\Delta\text{DTI}$ (`17/20` cells, `4/5` seeds, `4/4` folds), **`0.07724` credit/dot** ($\ge \tau_{\text{live}} = 0.054852$, vs `0.04098` uncorroborated sub-ridge control and `0.02333` random control), and **`+0.000656` mean interleaved $\Delta\text{DTI}$** (`27/40` cells, `9/10` seeds, `4/4` folds, `0.06440` credit/dot).
     - **`h38_1_joint_on_r30_r1` (`ALL_PASS = True` on LOSFO):** `+0.000747` mean LOSFO $\Delta\text{DTI}$ over `H36-1` (`+0.002460` over `d=2.8` base, `16/20` cells, `4/5` seeds, `4/4` folds), **`0.06993` credit/dot** ($\ge \tau_{\text{live}} = 0.054852$, vs `0.03227` sub-ridge control and `0.02681` random control), and **`+0.000543` mean interleaved $\Delta\text{DTI}$ over `H36-1`** (`27/40` cells, `8/10` seeds, `4/4` folds).
     - **`h38_2_low_relief_euler` (`ALL_PASS = False`):** Refuted (`-0.000045` LOSFO $\Delta\text{DTI}$, `0.01398` credit/dot, `5/20` cells) because hidden truth in `labels.tif` is itself scarp-biased (`knowledge/35`).
5. **Built & Audited the Companion `H38-1` Submission Package (`56a9f473edc7`, `37,860` px):**
   - Built `gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif`, `-allfinite.tif`, `-nan.zip`, and `note-gemsdoe28-h38-1-hf-euler-r30-r1-56a9f473edc7.txt`, verified across all `237/237` checks in `scripts/verify_downloads.py` (`0 failure(s)`).

---

## 2. Current Limitations

1. **Detector-ridge vs `H19-5`-surface gap for `H38-1`'s `200` added dots:**
   While `H36-1`'s `37,660` pixels are drawn strictly from the live-scored `H19-5` (`0.2600`) surface, `H38-1`'s `200` added pixels are drawn from the 32-band detector's sub-threshold 1-px ridge (`ridge_nms(prob_full)`). Because those `200` dots represent only `0.53%` of the total `37,860`-px emission, the maximum theoretical downside if every added dot earned zero live credit is bounded at $-0.0005\text{ DTI}$, while the upside at the measured `0.0699–0.0772` credit/dot is `+0.0005 to +0.0009` live DTI. We keep `H36-1` (`b531dae0a36f`, `37,660` px) at `"primary"` and slot `H38-1` (`56a9f473edc7`, `37,860` px) at `"secondary"` so the operator has both audited options on the first screen.
2. **Catalogue-bias ceiling on flat alluvial basins (`H38-2` negative result):**
   Any addition arm restricted to `relief <= P35` is penalized when evaluated against `labels.tif` because the USGS Quaternary compilation under-maps concealed basin-interior faults.
3. **Multi-depth MT crustal conductance rasters (`H38-3`):**
   The 5 USGS Great Basin MT conductance GeoTIFFs (`Bedrosian et al., 2022`, DOI `10.5066/P9TWT2LU`) are byte- and hash-verified by the Actions runner (`evidence/external_layer_inventory.json`), but have not yet been clipped/reprojected into `docs/data/` as `EPSG:32611` rasters.

---

## 3. Queued Next Steps for Session 15

1. **`H38-3` Multi-Depth MT Crustal Conductance Pipe Alignment (`Bedrosian et al., 2022`, DOI `10.5066/P9TWT2LU`):**
   Add a raster-clip step to `scripts/fetch_external_layers.py` so the GitHub Actions bridge reprojects `gb_conductance_surface_tp.tif`, `gb_conductance_middle_crust_tp.tif`, and `gb_conductance_lower_crust_tp.tif` onto the `3730 × 3292` template grid (downsampled or uint8-quantized in `docs/data/`), then preregister and evaluate `H38-3` on fresh LOSFO seeds `280–284`.
2. **`H38-4` Cultural & Constructional Shoreline Artifact Suppression with Budget-Neutral `H38-1` Reallocation:**
   Preregister and test whether pruning zero-potential-field, ultra-linear 1 m LiDAR steps along constant `det_elev` contours and replacing them 1-for-1 with `H38-1` corroborated dots improves LOSFO far-field DTI at fixed $N = 37{,}660\text{ px}$.
3. **Live Score Feedback Incorporation:**
   If the human operator submits either `b531dae0a36f` (`H36-1`, `37,660` px) or `56a9f473edc7` (`H38-1`, `37,860` px) and records a live organizer score, immediately add that 5th live anchor to `scripts/invert_live_scores.py` and re-solve the exact $(\text{TP}_w, \text{FP}_w, |G|)$ system.
