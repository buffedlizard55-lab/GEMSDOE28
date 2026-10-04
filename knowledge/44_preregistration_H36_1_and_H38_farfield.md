# 38 — Preregistration: `H36-1` LOSFO Far-Field Verification & `H38-1` / `H38-2` Multi-Physics Lineament Corroboration

**Status:** FROZEN BEFORE RUNNING SEEDS `265–269` (LOSFO) AND `270–279` (INTERLEAVED)  
**Date:** 2026-10-03 (UTC)  
**Branch:** `arena/01a1040a-gemsdoe28`  
**Modules under test:** `src/gems27/heatflow_euler.py`, `scripts/run_losfo_harness.py`, `scripts/run_h38_1_interleaved_holdout.py`

---

## 1. Purpose and Scope

This preregistration freezes two coupled evaluations before any fresh seed is touched:

1. **Part A — `H36-1` LOSFO Far-Field Falsification / Verification Test (`knowledge/36` §5.1):**
   Session 13 (`knowledge/33`) falsified `H37-1` (`max_coverage` packer) on the LOSFO far-field harness and restored `H36-1` (`rung30_blind_r1`, `gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif`, $N = 37{,}660\text{ px}$) as the one-click primary, queueing the direct LOSFO far-field test of `H36-1` as the #1 next step. Part A executes that test on fresh LOSFO seeds `265–269` (`5 seeds × 4 quadrant folds = 20 paired cells`).
2. **Part B — `H38-1` (with pure components `H38-1a`, `H38-1b`, and `H38-1` on `rung30_blind_r1`) & `H38-2` Multi-Physics Lineament Corroboration Gate (`knowledge/37`):**
   Tests whether corroborating a sub-threshold 1-px structural ridge lineament (`ridge_nms`) with the newly bridged USGS Great Basin conductive heat-flow residual (`hf_resid >= 50 mW/m²` within $1\text{ km}$, DeAngelo et al., 2022, DOI [10.5066/P9BZPVUC](https://doi.org/10.5066/P9BZPVUC)) and/or a shallow, depth-coherent SI=0 Euler contact cluster (`depth_mad_m <= 60 m`, `median_depth_m <= 400 m`, `n_solutions >= 8` within $300\text{ m}$, Reid et al., 1990, DOI [10.1190/1.1442774](https://doi.org/10.1190/1.1442774)) clears both the LOSFO far-field gate (`seeds 265–269`, 20 cells) and the standing 4-fold interleaved spatial-CV holdout (`seeds 270–279`, 40 cells).

---

## 2. Seed Ledger & Exploratory Disclosure

- **Previously spent seeds (`evidence/` ledger audit via `scripts/audit_euler_seed_reuse.py`):**
  - Interleaved 10-seed gates: `100–209`, `220–259` (plus smoke seeds `998, 999`).
  - LOSFO 5-seed gates / diagnostics: `210–214` (`H37-1`), `260–264` (`H37-3`).
- **Disclosed exploratory checks on already-spent seeds (`181`, `185`, `240`):**
  - Before freezing `src/gems27/heatflow_euler.py`, we ran preliminary mechanics checks strictly on already-spent seeds `181` and `185` (and verified same-seed `240` bit-identity against `evidence/h36_1_holdout.json`).
  - Zero seeds in `265–279` have ever been passed to `run_losfo_harness.py`, `holdout.make_split`, or `losfo.assign_systems_to_folds`.
- **Reserved fresh seed ranges for this preregistration:**
  - **LOSFO far-field evaluation (`scripts/run_losfo_harness.py`):** `seeds 265–269` (`5 seeds × 4 folds = 20 cells`), saved to `evidence/losfo_session14_h36_1_and_h38.json`.
  - **Interleaved 4-fold spatial-CV evaluation (`scripts/run_h38_1_interleaved_holdout.py`):** `seeds 270–279` (`10 seeds × 4 folds = 40 cells`), saved to `evidence/h38_1_interleaved_holdout.json`.

---

## 3. Part A — Frozen `H36-1` LOSFO Far-Field Falsification Criteria (`F1–F4` on `seeds 265–269`)

In each of the 20 LOSFO cells (`dilate_px = 2`, `buffer_px = 6`, so every hidden truth pixel sits at Euclidean distance $\ge 8.0\text{ px} = 800\text{ m}$ from `sp.known`), we evaluate on the honest `losfo` detector:
- `base`: `build_oof_dotted_base(prob_losfo[sl], ridge_losfo[sl], fm, sp.known[sl], budget_frac=0.0245, thin_d=2.8) & active`
- `h27_4_blind_r1_d280`: `base & ~(distance_transform_edt(~sp.known[sl]) <= 1.0) & active`
- `rung30_unpruned`: `build_oof_dotted_base(prob_losfo[sl], ridge_losfo[sl], fm, sp.known[sl], budget_frac=0.0245, thin_d=3.0) & active`
- `rung30_blind_r1`: `rung30_unpruned & ~(distance_transform_edt(~sp.known[sl]) <= 1.0) & active` (the `H36-1` one-click primary rule)
- `control_random_drop_matched_n`: random subset of `base` of exact size `int(rung30_unpruned.sum())` (`seed = 910_000 + 10*seed + f`)
- `control_random_drop_matched_r1`: random subset of `base` of exact size `int(rung30_blind_r1.sum())` (`seed = 920_000 + 10*seed + f`)

### Frozen `H36-1` Criteria (`F1–F4`):
- **`F1` (Spacing layout beats matched-`N` random drop on far-field truth):**
  `mean paired ΔDTI(rung30_unpruned - control_random_drop_matched_n) > 0`, with $\ge 15 / 20$ cells positive and $\ge 4 / 5$ seeds positive.
- **`F2` (Spacing increase `2.8 -> 3.0 px` is profitable at the live `0.2600` bar):**
  Pooled far-field removal efficiency $e_{\text{far}}(2.8 \to 3.0) = \sum \Delta\text{TP}_w / \sum \Delta\text{FP}_w < \tau_{\text{live}} = 0.054852$.
- **`F3` (`rung30_blind_r1` one-click primary improves raw LOSFO DTI over `base` and beats `tau_live`):**
  `mean paired ΔDTI(rung30_blind_r1 - base) > 0`, with $\ge 15 / 20$ cells positive, $\ge 4 / 5$ seeds positive, and pooled removal efficiency $e_{\text{far}}(\text{rung30\_blind\_r1}) < \tau_{\text{live}} = 0.054852$.
- **`F4` (Triangle-inequality zero-loss guarantee of `blind_r1`):**
  Because hidden truth is $\ge 8\text{ px}$ from `known` and `blind_r1` is $\le 1\text{ px}$ from `known`, every pixel deleted by `blind_r1` is at distance $\ge 8 - 1 = 7 > 3\text{ px}$ from hidden truth, so `h27_4_blind_r1_d280` must lose **exact zero** truth credit (`sum_tp_removed == 0.0` across all 20 cells) while improving DTI in `20 / 20` cells.

---

## 4. Part B — Frozen `H38` Multi-Physics Corroboration Specification & Criteria (`C1–C4`)

### 4.1 Frozen Physical Parameters (`src/gems27/heatflow_euler.py`)

1. **Conductive heat-flow residual halo (`hf_halo`):**
   - Source: `docs/data/sb_heat_flow_in_footprint.json` (`sha256 = 29ba5517…` of clipped JSON from `sb_heat_flow_zip` `sha256 = e7fd62c6…`, layer `USGS_gbHeatFlowWells_wEstimates.shp`, DeAngelo et al., 2022, DOI [10.5066/P9BZPVUC](https://doi.org/10.5066/P9BZPVUC)).
   - Threshold: `hf_resid >= 50.0` $\text{mW/m}^2$ (`753` wells / `677` unique 100 m cells inside the valid footprint).
   - Halo radius: `hf_radius_px = 10.0` ($1.0\text{ km}$ Euclidean distance transform).
2. **Shallow, depth-coherent SI=0 Euler contact cluster halo (`euler_halo`):**
   - Source: `evidence/h31_1_euler_clusters.csv` (`sha256 = 4695d9d1c27a57b5ba677252f46835be69373f5fb7226d1e81326cefd29558da`, `6,309` SI=0 clusters per Reid et al., 1990, DOI [10.1190/1.1442774](https://doi.org/10.1190/1.1442774)).
   - Filter: `depth_mad_m <= 60.0`, `median_depth_m <= 400.0`, `n_solutions >= 8` (`1,435` kept clusters / `1,435` 100 m cells).
   - Corroboration radius to candidate ridge lineament: `euler_radius_px = 3.0` ($300\text{ m}$ Euclidean distance transform, matching the $300\text{ m}$ DTI kernel radius and the lateral standard error of a $1\text{ km}$ Euler window).
3. **Low-relief smooth basin-fill mask (`low_relief_euler_mask` for `H38-2`):**
   - Source: `data/lidar_scarp_features_u8.tif` band 9 (`relief`) and band 12 (`valid`).
   - Threshold: `valid > 0` and `relief <= quantile(relief[valid & foot], 0.35)`, intersected with `euler_halo`.
4. **Candidate sub-threshold ridge pool and selection rule (`select_corroborated_ridge_dots`):**
   - In each evaluation cell, `sub_pool = ridge & active & (d_base >= 2.8) & (d_known >= 3.0)`.
   - Eligible corroborated ridge pixels `elig = sub_pool & cond_mask` are ranked by `prob * score_mult` (where `score_mult = 1.0 + 0.5*hf_halo + 0.5*euler_halo` for `h38_1_joint` and `h38_1_joint_on_r30_r1`, and `1.0` for the single-leg arms), capped at `k_cap = 100` pre-thinning pixels per cell, and Poisson-disk thinned via `thinning.dot_thin(raw, 2.8)`.
   - **Pre-declared arms:**
     - **Primary arm `h38_1_joint`**: `cond_mask = hf_halo | euler_halo`, `score_mult = 1 + 0.5*hf_halo + 0.5*euler_halo` on `base` (`d=2.8`);
     - **Stacked primary arm `h38_1_joint_on_r30_r1`**: identical `H38-1` rule applied on top of `rung30_blind_r1` (`H36-1`);
     - **Component arm `h38_1a_heatflow`**: `cond_mask = hf_halo` (`d_hf <= 10.0` alone) on `base`;
     - **Component arm `h38_1b_euler_lineament`**: `cond_mask = euler_halo` (`d_eu <= 3.0` alone) on `base`;
     - **Secondary arm `h38_2_low_relief_euler`**: `cond_mask = low_relief_euler_mask` on `base`.

### 4.2 Frozen Pass / Fail Criteria (`C1–C4` on LOSFO `seeds 265–269`)

An `H38` addition arm passes its LOSFO far-field gate if and only if all four criteria hold on `seeds 265–269` (`20` cells):
- **`C1` (Far-field transfer):** `mean paired ΔDTI(arm - ref) > 0`, with $\ge 15 / 20$ cells positive and $\ge 4 / 5$ seeds positive.
- **`C2` (Pays at the live `0.2600` break-even bar):** Pooled marginal credit per added dot across the 20 cells satisfies:
  $$\frac{\sum_{c=1}^{20} \Delta \text{TP}_w(c)}{\sum_{c=1}^{20} N_{\text{added}}(c)} \ge \tau_{\text{live}} = 0.054852.$$
- **`C3` (Beats BOTH matched controls):**
  - **`C3a` (Beats uncorroborated detector sub-ridge control):** `credit_per_added_dot(arm) > credit_per_added_dot(control_sub_ridge)` and `mean paired ΔDTI(arm - control_sub_ridge) > 0` (proving the geological corroboration leg adds true physical discrimination beyond the 32-band detector's own sub-threshold ridge).
  - **`C3b` (Beats content-blind random off-catalogue control):** `mean paired ΔDTI(arm - control_random) > 0` in $\ge 15 / 20$ cells.
- **`C4` (Integrity & same-seed bit-identity):**
  - `(added & ref).sum() == 0`, `(added & known).sum() == 0`, minimum distance to `known` $\ge 3.0\text{ px}$, minimum distance to `ref` $\ge 2.8\text{ px}$;
  - Unmodified base arms (`losfo`, `leaky`) on spent seed `181` match `evidence/losfo_h37_3_licence.json` / `evidence/h37_3_licence_integrity.json` to machine precision (`< 1e-12`).

### 4.3 Coupled Interleaved Spatial-CV Check (`seeds 270–279`, 40 cells)

In addition to the LOSFO far-field gate (`seeds 265–269`), we run `scripts/run_h38_1_interleaved_holdout.py` on fresh seeds `270–279` (`40` cells) to measure the exact standing 4-fold interleaved spatial-CV delta (`mean ΔDTI`, seeds won `/10`, folds improved `/4`, and same-seed `240` bit-identity against `evidence/h36_1_holdout.json`).
If `h38_1_joint` and `h38_1_joint_on_r30_r1` pass `C1–C4` on `seeds 265–269` AND improve interleaved holdout DTI across $\ge 8/10$ seeds and $4/4$ folds on `seeds 270–279`, we build and audit the companion full-map submission package (`gems28-h38-1-hf-euler-r30-r1-20261003-<hash12>-nan.tif`, `-allfinite.tif`, `.zip`, `note-...txt`) alongside `H36-1` (`b531dae0a36f`). If any criterion fails, we report the negative result without retuning.
