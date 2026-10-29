#!/usr/bin/env python3
"""S29-E1: cross-fitted gradient-boosted surface, one holdout run plus one final raster.

Pre-registered in evidence/s29_prereg.json before any fit. Reuses the shared holdout (gems-segment-pooled-v1),
the shared ridge-NMS/top-K placement, the shared canary, the registered lattice, and the shared GeoTIFF writer.

Outputs
* evidence/s29_holdout.json    HOLDOUT-DTI for S29, random-K and registry-039 lattice, paired CIs, canaries.
* docs/downloads/<name>.tif    only with --write-final: one binary dotted raster (values exactly 0.0/1.0,
                               NaN outside the 5,167,373-cell footprint, float32, EPSG:32611 grid).
Nothing here calls DrivenData or any host other than the pinned GitHub mirror files already on disk.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems27 import grid as grid_module  # noqa: E402
from gems27 import paths, submission  # noqa: E402
from gems27.shared_template import load_shared  # noqa: E402

RUN_ID = "S29-E1-HGB-CF-20261029"
K_TOTAL = 37_654
FOOTPRINT_PX = 5_167_373
BUFFER_PX = 15
SEED = 20261029
# Band indices in data/training_features.tif, names from scripts/prepare_data.py (band 6 'tc' excluded).
BANDS = [
    (1, "mag_anom"), (2, "rtp"), (3, "tmi_hg"), (4, "geod_2ndinv"), (5, "iso_grav_anom_slope"),
    (7, "geod_shearrate"), (8, "geod_dilaterate"), (9, "tmi_vg"), (10, "deq_n100a15"),
    (11, "iso_grav_anom_vg"), (12, "det_elev"), (13, "iso_grav_anom"), (14, "tmi"),
    (15, "depth_to_base_surf"), (16, "ieq_n100a15"), (17, "cond_surf"), (18, "iso_grav_anom_hg"),
    (19, "det_elev_slope"),
]
LATTICE = ROOT / "data/research/registry_rasters/registry-039.tif"
LATTICE_SHA = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
OUT_HOLDOUT = ROOT / "evidence/s29_holdout.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def load_grid():
    """Footprint from the official-grid template; catalogue from the owner-mirror labels (checked grid)."""
    with rasterio.open(paths.TEMPLATE) as template, rasterio.open(paths.LABELS) as labels:
        if (labels.shape, labels.crs, labels.transform) != (template.shape, template.crs, template.transform):
            raise ValueError("labels and sample template do not share the grid")
        footprint = np.isfinite(template.read(1))
        values = labels.read(1)
    if int(footprint.sum()) != FOOTPRINT_PX:
        raise ValueError("unexpected footprint size")
    catalogue = footprint & np.isfinite(values) & (values > 0.5)
    return footprint, catalogue


def load_features(footprint: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """(n_footprint_px, 18) float32 matrix of training features; NaN kept (HGB handles missing)."""
    cols = []
    with rasterio.open(paths.TRAINING) as src:
        if src.shape != footprint.shape or src.count != 19:
            raise ValueError("training feature raster shape/band count differs from the expected stack")
        for band, _name in BANDS:
            a = src.read(band).astype(np.float32)
            a[(a < -1e38) | ~np.isfinite(a)] = np.nan
            cols.append(a[footprint])
    return np.stack(cols, axis=1), [n for _, n in BANDS]


def fit_surface(X_fp, footprint_idx_map, train_mask_fp, label_fp, seed):
    """Fit on up to 250k training pixels (all visible positives up to 60k) and predict every footprint px."""
    from sklearn.ensemble import HistGradientBoostingClassifier

    rng = np.random.default_rng(seed)
    tr = np.flatnonzero(train_mask_fp)
    pos = tr[label_fp[tr]]
    neg = tr[~label_fp[tr]]
    pos = rng.choice(pos, min(len(pos), 60_000), replace=False)
    neg = rng.choice(neg, min(len(neg), 250_000 - len(pos)), replace=False)
    idx = np.r_[pos, neg]
    model = HistGradientBoostingClassifier(
        max_iter=200, learning_rate=0.1, max_leaf_nodes=31, l2_regularization=1.0,
        random_state=seed,
    )
    model.fit(X_fp[idx], label_fp[idx].astype(int))
    proba = model.predict_proba(X_fp)[:, 1].astype(np.float32)
    out = np.zeros(grid_module.SHAPE, np.float32)
    out.ravel()[footprint_idx_map] = proba
    return out


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--write-final", action="store_true", help="also write the binary final raster")
    args = parser.parse_args(argv)
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    t0 = time.monotonic()

    shared = load_shared(ROOT)
    footprint, catalogue = load_grid()
    X, names = load_features(footprint)
    fp_idx = np.flatnonzero(footprint.ravel())
    ho = shared.holdout.SegmentHoldout(footprint, catalogue, buffer_px=BUFFER_PX)
    lattice = None
    if LATTICE.is_file() and sha256_file(LATTICE) == LATTICE_SHA:
        with rasterio.open(LATTICE) as src:
            lattice = (src.read(1) > 0) & footprint
    else:
        raise SystemExit("registry-039 lattice missing or hash mismatch; run scripts/fetch_registry_rasters.py")

    preds_s29, preds_rand, preds_lat = [], [], []
    stitched = np.zeros(footprint.shape, np.float32)
    fold_log = []
    rng = np.random.default_rng(SEED)
    for fold in ho.folds:
        valid, visible, train = fold["valid"], fold["visible"], fold["train"]
        k_f = int(round(K_TOTAL * int(valid.sum()) / FOOTPRINT_PX))
        surface = fit_surface(X, fp_idx, (train & footprint).ravel()[fp_idx],
                              visible.ravel()[fp_idx], seed=SEED + fold["id"])
        stitched[valid] = surface[valid]
        eligible = valid & ~visible
        nms = shared.metric.ridge_nms(surface, eligible, sigma=1.0)
        s29 = shared.metric.select_top_positive(surface, nms & eligible, k_f).astype(bool)
        ids = np.flatnonzero(eligible.ravel())
        rnd = np.zeros(footprint.size, bool)
        rnd[rng.choice(ids, size=min(k_f, len(ids)), replace=False)] = True
        rnd = rnd.reshape(footprint.shape)
        lat = lattice & eligible
        preds_s29.append(s29)
        preds_rand.append(rnd)
        preds_lat.append(lat)
        fold_log.append({"fold": fold["name"], "K_f": k_f, "valid_px": int(valid.sum()),
                         "visible_px": int(visible.sum()), "truth_px": int(fold["truth"].sum()),
                         "s29_dots": int(s29.sum()), "random_dots": int(rnd.sum()),
                         "lattice_dots_in_eligible": int(lat.sum())})
        print(f"{fold['name']}: K_f={k_f} s29={int(s29.sum())} lattice={int(lat.sum())}", flush=True)

    res_s29 = ho.summarize(preds_s29)
    res_rand = ho.summarize(preds_rand)
    res_lat = ho.summarize(preds_lat)
    paired_rand = ho.compare_paired(preds_s29, preds_rand)
    paired_lat = ho.compare_paired(preds_s29, preds_lat)
    features = {n: np.nan_to_num(np.where(footprint, np.nan_to_num(_full(X, footprint, j)), 0.0))
                for j, n in enumerate(names)}
    features["s29_cross_fitted_surface"] = np.where(footprint, stitched, 0.0)
    canary = ho.canary(features, seed=SEED)
    # canary["features"] maps feature -> {"pooled_auc", "leakage_suspected", "folds"}; the gate is max(auc, 1-auc) > 0.90.
    canary_rows = canary.get("features", {})
    max_auc = max(float(max(r["pooled_auc"], 1 - r["pooled_auc"])) for r in canary_rows.values()) if canary_rows else None
    result = {
        "schema": "s29-holdout-v1",
        "run_id": RUN_ID,
        "started_utc": started,
        "runtime_s": round(time.monotonic() - t0, 1),
        "label": "HOLDOUT-DTI (gems-segment-pooled-v1, catalogue-internal; not an organizer or leaderboard score)",
        "buffer_px": BUFFER_PX,
        "K_total": K_TOTAL,
        "folds": fold_log,
        "s29_holdout": res_s29,
        "random_K_holdout": res_rand,
        "registry_039_lattice_holdout": res_lat,
        "paired_s29_minus_random_K": paired_rand,
        "paired_s29_minus_lattice": paired_lat,
        "canary": canary,
        "canary_max_auc_reported": max_auc,
        "pre_registration": "evidence/s29_prereg.json",
        "runner_sha256": sha256_file(Path(__file__)),
    }
    OUT_HOLDOUT.write_text(json.dumps(result, indent=2, default=float, allow_nan=False) + "\n")
    print("S29 DTI", round(res_s29["dti"], 6), "random", round(res_rand["dti"], 6),
          "lattice", round(res_lat["dti"], 6), flush=True)

    if args.write_final:
        raise SystemExit("--write-final was retired in S29: final rasters are produced by scripts/build_s29_candidates.py and gated by scripts/s29_gate.py")
    return 0


def _full(X, footprint, j):
    out = np.full(footprint.shape, np.nan, np.float32)
    out.ravel()[np.flatnonzero(footprint.ravel())] = X[:, j]
    return out


def write_final(shared, footprint, catalogue, X, fp_idx) -> None:
    """Final raster: one model on all visible catalogue labels, eligible = footprint minus catalogue."""
    surface = fit_surface(X, fp_idx, footprint.ravel()[fp_idx], catalogue.ravel()[fp_idx], seed=SEED)
    eligible = footprint & ~catalogue
    nms = shared.metric.ridge_nms(surface, eligible, sigma=1.0)
    dots = shared.metric.select_top_positive(surface, nms & eligible, K_TOTAL).astype(bool)
    values = np.where(dots, np.float32(1.0), np.float32(0.0))
    cid = submission.scored_content_id(values, footprint, catalogue)
    name = submission.make_filename("gems29", "s29-hgb-cf-k37654", "20261029", cid, "nan")
    path = ROOT / "docs/downloads" / name
    submission.write_geotiff(values, paths.TEMPLATE, path, outside="nan")
    receipt = submission.verify_geotiff(path, paths.TEMPLATE)
    out = ROOT / "evidence/s29_final_raster.json"
    out.write_text(json.dumps({"file": name, "dots": int(dots.sum()), "content_id": cid,
                               "validator": receipt}, indent=2, default=str, allow_nan=False) + "\n")
    print("wrote", name, "dots", int(dots.sum()), "hard_pass", receipt["hard_checks_passed"], flush=True)


if __name__ == "__main__":
    raise SystemExit(main())
