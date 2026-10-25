#!/usr/bin/env python3
"""S18 Experiment 1 (knowledge/52): H39-5 extrapolated surfaces + leakage canary
+ pre-placement uniqueness.

Label-free pool build (surface code reads no labels). Writes
data/prepared/extrap_surfaces.npz and evidence/s18_canary.json. Canary: each
surface alone vs LOSFO seed-310 withheld systems; max(AUC,1-AUC) > 0.90 =
leakage -> stop. Pre-placement uniqueness vs every registry raster
(docs/downloads/*-nan.tif + byte-verified /tmp/forensic champion/GEMSDOE36
education copies when present): surface Spearman on a 400k footprint sample,
and fraction of the top-37,654 thinned eligible pool dots within 3 px of each
registry raster. No detector is trained here.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, holdout, losfo, migration, paths  # noqa: E402

REGISTRY_EXTRA = {
    "champion_e5eb6e7e_GEMSDOE32": Path("/tmp/forensic/champion_e5eb6e7e_zeros.tif"),
    "gems36_9b9ea4e6_GEMSDOE36": Path("/tmp/forensic/gems36_9b9ea4e6_zeros.tif"),
}
EXTRA_SHA = {
    "champion_e5eb6e7e_GEMSDOE32": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "gems36_9b9ea4e6_GEMSDOE36": "e15891020b9c57056ac7fa874a5e506fbd6ed9314a4ea8e73af0753887a3708a",
}
TARGET_N = 37_654


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while c := f.read(1 << 20):
            h.update(c)
    return h.hexdigest()


def load_dots(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        a = s.read(1)
    return np.isfinite(a) & (a > 0)


def within_frac(ours: np.ndarray, ref: np.ndarray, r: float = 3.0) -> float:
    y, x = np.nonzero(ours)
    yb, xb = np.nonzero(ref)
    if len(y) == 0 or len(yb) == 0:
        return 0.0
    d, _ = cKDTree(np.c_[yb, xb].astype(float)).query(np.c_[y, x].astype(float), workers=1)
    return float((d <= r).mean())


def main() -> int:
    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    built = migration.build_extrapolated_surfaces(paths.TRAINING, foot)
    out_npz = paths.DATA / "prepared/extrap_surfaces.npz"
    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        out_npz,
        **{n: built["surfaces"][n] for n in built["names"]},
        disp_mag_union=built["disp_mag_union"],
    )
    print(f"surfaces -> {out_npz} ({time.time()-t0:.0f}s)", flush=True)

    # --- canary vs LOSFO seed-310 withheld systems (recipe: build_s16_extra) ---
    fold = holdout.make_quadrant_folds(foot)
    sys_grid, n_sys = losfo.fault_systems(labels, losfo.DEFAULT_DILATE_PX)
    tab = losfo.system_table(sys_grid, n_sys, foot)
    hold = losfo.assign_systems_to_folds(tab, fold, 4, seed=310)
    hidden = np.isin(sys_grid, np.flatnonzero(hold >= 0) + 1) & foot
    d_hidden = distance_transform_edt(~hidden)
    rng = np.random.default_rng(310)
    neg_pool = np.flatnonzero((foot & ~labels & (d_hidden > 6)).ravel())
    pos_rc = np.argwhere(hidden)
    n_neg = min(len(neg_pool), max(50_000, 20 * len(pos_rc)), 250_000)
    neg_flat = rng.choice(neg_pool, size=n_neg, replace=False)
    neg_rc = np.column_stack(np.unravel_index(neg_flat, foot.shape))
    y = np.r_[np.ones(len(pos_rc), int), np.zeros(len(neg_rc), int)]
    aucs = {}
    for name in built["names"]:
        b = built["surfaces"][name]
        s = np.r_[b[pos_rc[:, 0], pos_rc[:, 1]], b[neg_rc[:, 0], neg_rc[:, 1]]].astype(np.float64)
        auc = float(roc_auc_score(y, s))
        aucs[name] = {"auc": auc, "canary_max_auc_1mauc": max(auc, 1.0 - auc)}
    canary_pass = all(v["canary_max_auc_1mauc"] <= 0.90 for v in aucs.values())

    # --- eligible pool sizing (full catalogue used for sizing only, prereg) ---
    d_cat = distance_transform_edt(~(labels & foot))
    union = built["surfaces"]["extrap_surface_union"]
    disp = built["disp_mag_union"]
    eligible = foot & (union > 0) & (disp >= migration.EXTRAP_MIN_DISP_PX) & (d_cat > 2.0)
    ys, xs = np.nonzero(eligible)
    order = np.argsort(-union[ys, xs].astype(np.float64), kind="stable")
    # greedy top-TARGET_N with 2.8 px spacing via the shared spacing hash
    h = migration._SpacingHash(2.8)
    picked = []
    for j in order:
        if len(picked) >= TARGET_N:
            break
        yy, xx = int(ys[j]), int(xs[j])
        if h.clear(yy, xx):
            h.add(yy, xx)
            picked.append((yy, xx))
    pool_dots = np.zeros(foot.shape, bool)
    if picked:
        py, px = np.array(picked).T
        pool_dots[py, px] = True
    # sanity: pool dots are a thinned set (no pair < 2.8 px)
    assert not (pool_dots & (labels & foot)).any()

    # --- pre-placement uniqueness vs registry ---
    registry = {p.name: p for p in sorted((ROOT / "docs/downloads").glob("*-nan.tif"))}
    for k, v in REGISTRY_EXTRA.items():
        if v.is_file() and sha256_file(v) == EXTRA_SHA[k]:
            registry[k] = v
    foot_idx = np.flatnonzero(foot.ravel())
    sample = np.sort(rng.choice(foot_idx, size=400_000, replace=False))
    surf_s = union.ravel()[sample].astype(np.float64)
    uniq = {}
    for name, p in registry.items():
        ref = load_dots(p)
        uniq[name] = {
            "spearman_lane_surface_vs_binary_sample400k": float(
                spearmanr(surf_s, ref.ravel()[sample].astype(np.float64)).statistic),
            "frac_pool_dots_within3px": within_frac(pool_dots, ref),
            "registry_dots": int(ref.sum()),
        }
    worst_spearman = max(
        ((abs(v["spearman_lane_surface_vs_binary_sample400k"]), k) for k, v in uniq.items()),
        default=(0.0, None))
    worst_pool = max(uniq.items(), key=lambda kv: kv[1]["frac_pool_dots_within3px"],
                     default=(None, {}))

    out = {
        "experiment": "S18 Exp1 canary + pre-placement uniqueness (knowledge/52); no detector trained",
        "bands": built["names"], "valid_frac_in_footprint": built["valid_frac"],
        "field_stats": built["field_stats"],
        "surfaces_npz": str(out_npz.relative_to(ROOT)), "surfaces_npz_sha256": sha256_file(out_npz),
        "losfo_assignment_seed": 310, "n_systems": int(n_sys),
        "n_hidden_px_seed310": int(hidden.sum()), "n_neg_sampled": int(n_neg),
        "single_feature_auc_vs_hidden_systems": aucs,
        "canary_threshold": 0.90, "canary_pass": bool(canary_pass),
        "eligible_pool_px_full_catalogue_sizing": int(eligible.sum()),
        "pool_dots_top37654_thinned2p8": int(pool_dots.sum()),
        "disp_mag_percentiles_on_eligible": {
            f"p{q}": float(np.percentile(disp[eligible], q)) for q in (50, 75, 90, 99)},
        "preplacement_uniqueness": {
            "worst_abs_spearman": {"value": float(worst_spearman[0]), "raster": worst_spearman[1]},
            "worst_pool_overlap": {"raster": worst_pool[0], **worst_pool[1]} if worst_pool[0] else None,
            "surface_spearman_pass_le_0.90": bool(worst_spearman[0] <= 0.90),
            "table": uniq,
        },
        "surface_stats_footprint": {
            n: {"frac_positive": float((built["surfaces"][n][foot] > 0).mean()),
                "max": float(built["surfaces"][n][foot].max())} for n in built["names"]},
        "seconds": round(time.time() - t0, 1),
    }
    outp = ROOT / "evidence/s18_canary.json"
    outp.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in (
        "single_feature_auc_vs_hidden_systems", "canary_pass",
        "eligible_pool_px_full_catalogue_sizing", "pool_dots_top37654_thinned2p8",
    )}, indent=2))
    print("worst |spearman|:", out["preplacement_uniqueness"]["worst_abs_spearman"])
    print("worst pool overlap:", out["preplacement_uniqueness"]["worst_pool_overlap"])
    return 0 if (canary_pass and out["preplacement_uniqueness"]["surface_spearman_pass_le_0.90"]) else 2


if __name__ == "__main__":
    raise SystemExit(main())
