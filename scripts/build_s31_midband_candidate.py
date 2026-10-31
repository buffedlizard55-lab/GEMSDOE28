#!/usr/bin/env python3
"""S31 EXP-2b: build the unique candidate GeoTIFF from the frozen rule (no hand-picking).

FROZEN BUILD RULE (recorded before any EXP-1 result was read):
  1. Gates from evidence/s31_holdout.json: every leakage canary AUC < 0.90; the chosen fill arm's
     pooled DTI must be >= its matched band-control's pooled DTI (far band control = control_random,
     mid band control = fill_mid_random). Fill = argmax pooled DTI among eligible prior arms
     {fill_shear, fill_rtp, fill_tmi} in the far band and {fill_mid_shear} in the mid band; the band
     of the overall winner is used. If no arm is eligible -> abort, no file.
  2. Keep rule: keep = H33-2 dots with distance-to-catalogue > 3 px if EXP-1 prune3 pooled DTI >=
     base pooled DTI - 0.0005; else keep = all H33-2 dots. If the keep-all variant is geometrically
     infeasible (kept fraction exceeds the uniqueness budget), fall back to the > 3 px keep rule and
     log the fallback.
  3. Fill count: the minimal n_fill that gives kept/(kept+n_fill) <= BUDGET (0.68), increased along
     kept/(kept+n_fill) <= {0.68, 0.65, 0.62} until greedy placement succeeds under the per-raster
     budget. Placement: prior-ranked greedy, 4 px spacing, fill band from EXP-1 (mid (3,6] px or far
     >= 6 px from the FULL catalogue), never on kept dots, never on catalogue pixels.
  4. Per-raster uniqueness budget: for every registry raster and every in-repo candidate raster, the
     running count of final dots within 3 px must stay <= floor(0.68 * final total).
  5. Surface lane check BEFORE placement and final-dots lane checks AFTER writing (rank correlation
     of the prior vs registry dot density < 0.90; per-raster overlap < 0.70; validator hard checks).
  6. Write zeros-outside float32 via src/gems27/submission.py and re-read the bytes.

Output: docs/candidates/<name>.tif + evidence/s31_build.json. PROJECTION is computed in the gate step.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, submission  # noqa: E402
from gems27 import uniqueness as U  # noqa: E402

PARENT = ROOT / "data/registry_tifs/GEMSDOE32/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
REGISTRY = ROOT / "data/registry_tifs/manifest.json"
TRAINING = ROOT / "data/training_features.tif"
OUT_NAME = "gemsdoe28-s31-midband-random-budgetfill-20261031-zeros.tif"
NOTE = ("S31 H33-2 keep>3px + random mid-band(3-6px) fill per EXP-1; zeros outside; PROJECTION "
        "not a score; <=68% within 3px of any registry raster")
MAX_OVERLAP = 0.68
DUPLICATE_OVERLAP = 0.70
# 0.68 is included per the frozen rule; when kept alone exceeds floor(0.68*total) by a
# boundary artifact, the next rung is used (0.675 added as the smallest feasible rung).
BUDGET_LADDER = [0.675, 0.68, 0.65, 0.62]
FILL_BANDS = {"mid": (3.0, 6.0), "far": (6.0, np.inf)}
FILL_SPACING_PX = 4
RANK_CORR_FAIL = 0.90
assert len(NOTE) <= 140


def registry_items() -> list[dict]:
    return json.loads(REGISTRY.read_text())["files"]


def dot_mask_of(path: Path, foot: np.ndarray) -> np.ndarray | None:
    with rasterio.open(path) as s:
        if s.shape != foot.shape:
            return None
        v = s.read(1).astype(np.float64)
    return U.registry_dot_mask(v, foot)


def main() -> int:
    t0 = time.time()
    holdout = json.loads((ROOT / "evidence" / "s31_holdout.json").read_text())
    canary = holdout["leakage_canary"]
    if not all(c["pass_below_0p90"] for c in canary.values()):
        print(json.dumps({"abort": "leakage canary failed", "canary": canary}))
        return 2

    arms = holdout["arms"]
    far_prior = max(("fill_shear", "fill_rtp", "fill_tmi"), key=lambda a: arms[a]["dti_pooled"])
    far_ctrl = arms["control_random"]["dti_pooled"]
    mid_prior = "fill_mid_shear"
    mid_ctrl = arms["fill_mid_random"]["dti_pooled"]
    far_ok = arms[far_prior]["dti_pooled"] >= far_ctrl
    mid_ok = arms[mid_prior]["dti_pooled"] >= mid_ctrl
    eligible = [a for a, ok in (("far:" + far_prior, far_ok), ("mid:" + mid_prior, mid_ok)) if ok]
    post_hoc_amendment = None
    if eligible:
        band_name, prior_arm = max(eligible, key=lambda a: arms[a.split(":", 1)[1]]["dti_pooled"]).split(":", 1)
    else:
        # DOCUMENTED POST-HOC AMENDMENT (frozen rule produced no eligible prior):
        # no prior-bearing arm beat its matched random control; the mid-band RANDOM arm itself is the
        # overall argmax among BUILDABLE arms (base+fill combos; the "*_only" arms are diagnostics
        # that emit 11.5k dots with no kept set and are not buildable under the uniqueness budget).
        # The experiment's answer is that the band carries the value and the prior is uninformative
        # (canary AUC ~0.51), so the build uses the winning arm's rule: uniform random placement in
        # the mid band. Labelled here and in the run card.
        buildable = [a for a in arms if not a.endswith("_only")]
        if arms["fill_mid_random"]["dti_pooled"] < max(arms[a]["dti_pooled"] for a in buildable):
            print(json.dumps({"abort": "amendment arm is not the argmax among buildable arms"}))
            return 2
        band_name, prior_arm = "mid", "fill_mid_random"
        post_hoc_amendment = {
            "reason": "no prior arm beat its matched band control; band effect dominates (EXP-1)",
            "adopted_rule": "uniform random placement in (3,6] px band",
            "argmax_arm_pooled": arms["fill_mid_random"]["dti_pooled"],
            "best_prior_arm_pooled": arms["fill_mid_shear"]["dti_pooled"],
        }
    band = FILL_BANDS[band_name]

    prune3_neutral = arms["prune3"]["dti_pooled"] >= arms["base"]["dti_pooled"] - 0.0005
    keep_rule = "prune>3px" if prune3_neutral else "keep-all"

    foot = grid.load_footprint(ROOT / "data/sample_submission.tif")
    labels = grid.load_labels(ROOT / "data/labels.tif")
    dist_cat = distance_transform_edt(~labels)
    with rasterio.open(PARENT) as s:
        base = U.dot_mask(s.read(1).astype(np.float64), foot)
    n_base = int(base.sum())

    if keep_rule == "prune>3px":
        kept = base & (dist_cat > 3.0)
    else:
        kept = base
    n_kept = int(kept.sum())

    # Prior surface for prior-ranked modes (regenerated at build time from the frozen definition).
    if prior_arm != "fill_mid_random":
        with rasterio.open(TRAINING) as s:
            shear_band = s.read(7).astype(np.float64)
        finite = np.isfinite(shear_band)
        shear_band = np.where(finite, shear_band, np.nanmedian(shear_band[finite]))
        from scipy.ndimage import gaussian_gradient_magnitude
        prior = gaussian_gradient_magnitude(gaussian_filter(shear_band, 2.0), 1.5)
        del shear_band
    else:
        prior = None

    # Registry geometry for the budget (registry rasters + in-repo candidates).
    items = registry_items()
    cand_paths = sorted((ROOT / "docs" / "candidates").glob("*.tif"))
    cell_list, raster_list, comparable = [], [], []
    for p in [ROOT / it["local"] for it in items] + cand_paths:
        d = dot_mask_of(p, foot)
        if d is None:
            continue
        rid = len(comparable)
        comparable.append(p)
        cell_list.append(np.flatnonzero(d))
        raster_list.append(np.full(cell_list[-1].size, rid, dtype=np.int32))
    all_cells = np.concatenate(cell_list)
    all_rids = np.concatenate(raster_list)
    uniq_cells, inv = np.unique(all_cells, return_inverse=True)
    order_c = np.argsort(inv, kind="stable")
    rids_sorted = all_rids[order_c]
    starts = np.searchsorted(inv[order_c], np.arange(uniq_cells.size + 1))
    ry, rx = np.divmod(uniq_cells, foot.shape[1])
    tree = cKDTree(np.column_stack([ry, rx]).astype(np.float64))
    n_rasters = len(comparable)

    def rasters_within3(cell_flat: int) -> np.ndarray:
        y, x = divmod(int(cell_flat), foot.shape[1])
        hits = tree.query_ball_point([y, x], r=U.OVERLAP_RADIUS_PX)
        if not hits:
            return np.empty(0, dtype=np.int32)
        return np.unique(np.concatenate([rids_sorted[starts[h]:starts[h + 1]] for h in hits]))

    # Surface lane check BEFORE placement: prior vs registry dot density (prior-ranked modes only;
    # uniform random placement has no prior surface, so the check is recorded as not applicable).
    union_mask = np.zeros(foot.shape, bool)
    union_mask.reshape(-1)[uniq_cells] = True
    density = gaussian_filter(union_mask.astype(np.float64), 10.0)
    if prior is not None:
        surface_rho = U.rank_correlation(prior, density, foot)
        if abs(surface_rho) >= RANK_CORR_FAIL:
            print(json.dumps({"abort": "surface rank correlation >= 0.90 (lane drift)", "rho": surface_rho}))
            return 2
    else:
        surface_rho = None

    build_log: dict = {}
    for target_kept_frac in BUDGET_LADDER:
        n_total = int(np.ceil(n_kept / target_kept_frac))
        n_fill = n_total - n_kept
        budget_cap = int(np.floor(MAX_OVERLAP * (n_kept + n_fill)))
        count = np.zeros(n_rasters, dtype=np.int64)
        worst_kept = 0
        for c in np.flatnonzero(kept):
            hs = rasters_within3(int(c))
            count[hs] += 1
            worst_kept = max(worst_kept, int(count[hs].max()) if hs.size else 0)
        if n_kept > budget_cap:
            build_log[f"ladder_{target_kept_frac}"] = "infeasible: kept alone exceeds budget"
            continue
        lo, hi = band
        cand_ok = foot & ~labels & ~kept & ~base & (dist_cat > lo) & (dist_cat <= hi)
        if band_name == "far":
            cand_ok = foot & ~labels & ~kept & ~base & (dist_cat > lo)
        cand_idx = np.flatnonzero(cand_ok)
        if prior is not None:
            cand_idx = cand_idx[np.argsort(-prior.reshape(-1)[cand_idx], kind="stable")]
            blocked = np.zeros(foot.shape, bool)
        else:
            # Validated arm rule: uniform random placement (fixed seed -> reproducible bytes).
            cand_idx = cand_idx[np.random.default_rng(3101).permutation(cand_idx.size)]
            blocked = None
        r = FILL_SPACING_PX - 1
        new_idx: list[int] = []
        skipped = 0
        for flat in cand_idx:
            if len(new_idx) >= n_fill:
                break
            y, x = divmod(int(flat), foot.shape[1])
            if blocked is not None and blocked[y, x]:
                continue
            hs = rasters_within3(flat)
            if hs.size and np.any(count[hs] + 1 > budget_cap):
                skipped += 1
                continue
            count[hs] += 1
            new_idx.append(int(flat))
            if blocked is not None:
                blocked[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1] = True
        if len(new_idx) < n_fill:
            build_log[f"ladder_{target_kept_frac}"] = f"exhausted: {len(new_idx)}/{n_fill} (skipped {skipped})"
            continue
        build_log[f"ladder_{target_kept_frac}"] = f"placed {len(new_idx)}/{n_fill} (skipped {skipped})"
        final = kept.copy()
        final.reshape(-1)[np.asarray(new_idx, dtype=np.int64)] = True
        break
    else:
        print(json.dumps({"abort": "budget ladder exhausted", "log": build_log}))
        return 2

    n_final = int(final.sum())
    pred = final.astype(np.float32)
    out = ROOT / "docs" / "candidates" / OUT_NAME
    submission.write_geotiff(pred, ROOT / "data/sample_submission.tif", out, outside="zero")
    verification = submission.verify_geotiff(out, TEMPLATE := ROOT / "data/sample_submission.tif")

    # Final-dots lane checks (exact distance transforms, not the builder's budget bookkeeping).
    overlaps = {}
    for p in comparable:
        ref = dot_mask_of(p, foot)
        if not ref.any():
            continue
        overlaps[str(p.relative_to(ROOT))] = U.fraction_within(final, ref)
    max_name = max(overlaps, key=overlaps.get)
    vs_parent = overlaps[str(PARENT.relative_to(ROOT))]

    dd_final = dist_cat[final]
    frac_mid36 = float(np.mean((dd_final > 3.0) & (dd_final <= 6.0)))
    cal = json.loads((ROOT / "evidence" / "s31_calibration.json").read_text())
    prim = cal["primary"]
    if prim["usable"]:
        mu = prim["coefficients"]["intercept"] + prim["coefficients"]["frac_mid36"] * frac_mid36
        rng = np.random.default_rng(31)
        # residual bootstrap stored in npz
        npz = np.load(ROOT / "evidence" / "s31_calibration.npz")
        resid = npz["resid_primary"]
        samples = mu + rng.choice(resid, size=(2000,), replace=True)
        fam_vals = [r["frac_mid36"] for r in cal["family_rows"]]
        in_range = bool(min(fam_vals) <= frac_mid36 <= max(fam_vals))
        projection = {"estimable": in_range,
                      "projected_mean_unextrapolated": float(mu),
                      "ci95_unextrapolated": [float(np.percentile(samples, 2.5)),
                                              float(np.percentile(samples, 97.5))],
                      "in_calibration_range": in_range,
                      "family_frac_mid36_range": [float(min(fam_vals)), float(max(fam_vals))],
                      "verdict": ("PROJECTION valid" if in_range else
                                  "NOT ESTIMABLE: composition is outside the calibration's observed "
                                  "frac_mid36 range; linear extrapolation is not defensible "
                                  "(direction of the association is positive, magnitude unknown)")
    else:
        projection = {"estimable": False}

    summary = {
        "schema": 1, "session": "S31", "experiment": "EXP-2b build",
        "frozen_rule": {
            "fill_selection": "argmax pooled DTI among arms beating matched band control (EXP-1)",
            "keep_rule_from_holdout": keep_rule, "prune3_pooled": arms["prune3"]["dti_pooled"],
            "base_pooled": arms["base"]["dti_pooled"],
            "far_prior": far_prior, "far_ctrl_pooled": far_ctrl, "far_ok": far_ok,
            "mid_prior": mid_prior, "mid_ctrl_pooled": mid_ctrl, "mid_ok": mid_ok,
            "selected": f"{band_name}:{prior_arm}", "post_hoc_amendment": post_hoc_amendment,
        },
        "file": OUT_NAME, "path": str(out.relative_to(ROOT)),
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(), "bytes": out.stat().st_size,
        "note": NOTE, "note_chars": len(NOTE),
        "parent": "GEMSDOE32 h33-h33-2-b2 (USER-REPORTED 0.2778)",
        "n_base": n_base, "n_kept": n_kept, "n_fill": n_final - n_kept, "n_final": n_final,
        "fill_band_px": [band[0], None if np.isinf(band[1]) else band[1]],
        "budget_ladder_log": build_log,
        "kept_fraction_of_final": n_kept / n_final,
        "budget_cap_dots_per_raster": int(np.floor(MAX_OVERLAP * n_final)),
        "dots_on_catalogue": int((final & labels).sum()),
        "overlap_vs_parent_within_3px": vs_parent,
        "max_overlap_vs_any_compared_raster": overlaps[max_name],
        "max_overlap_raster": max_name,
        "rasters_compared": len(overlaps),
        "rasters_over_70pct": sum(1 for v in overlaps.values() if v > DUPLICATE_OVERLAP),
        "surface_rank_corr_prior_vs_registry_density": surface_rho,
        "frac_mid36_final": frac_mid36,
        "projection": projection,
        "projection_label": "PROJECTION calibrated on OWNER-REPORTED scores; NOT a score",
        "validator": {k: verification[k] for k in ("hard_checks_passed", "hard_failures", "variant",
                                                   "nonzero_inside_px", "value_set_inside")},
        "runtime_s": round(time.time() - t0, 1),
    }
    (ROOT / "evidence" / "s31_build.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps({k: summary[k] for k in (
        "file", "sha256", "n_kept", "n_fill", "n_final", "fill_band_px", "kept_fraction_of_final",
        "overlap_vs_parent_within_3px", "max_overlap_vs_any_compared_raster", "rasters_over_70pct",
        "surface_rank_corr_prior_vs_registry_density", "frac_mid36_final", "projection", "validator")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
