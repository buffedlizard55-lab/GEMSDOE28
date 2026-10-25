#!/usr/bin/env python3
"""S16 Experiment 1 (knowledge/49): build H40-1 migration bands + leakage canary.

Writes data/prepared/migration_extra.npy (5167373, 4) float32 and
evidence/s16_canary.json (per-band AUC vs LOSFO seed-300 withheld systems;
max(AUC,1-AUC) > 0.90 = leakage -> stop). No detector is trained here.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, holdout, losfo, migration, paths  # noqa: E402


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while c := f.read(1 << 20):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    built = migration.build_migration_bands(paths.TRAINING, foot)
    X = migration.bands_to_footprint_matrix(built, foot)
    out_extra = paths.DATA / "prepared/migration_extra.npy"
    out_extra.parent.mkdir(parents=True, exist_ok=True)
    np.save(out_extra, X)
    print(f"extra {X.shape} -> {out_extra} ({time.time()-t0:.0f}s)", flush=True)

    fold = holdout.make_quadrant_folds(foot)
    sys_grid, n_sys = losfo.fault_systems(labels, losfo.DEFAULT_DILATE_PX)
    tab = losfo.system_table(sys_grid, n_sys, foot)
    hold = losfo.assign_systems_to_folds(tab, fold, 4, seed=300)
    hidden = np.isin(sys_grid, np.flatnonzero(hold >= 0) + 1) & foot
    d_hidden = distance_transform_edt(~hidden)
    rng = np.random.default_rng(300)
    neg_pool = np.flatnonzero((foot & ~labels & (d_hidden > 6)).ravel())
    pos_rc = np.argwhere(hidden)
    n_neg = min(len(neg_pool), max(50_000, 20 * len(pos_rc)), 250_000)
    neg_flat = rng.choice(neg_pool, size=n_neg, replace=False)
    neg_rc = np.column_stack(np.unravel_index(neg_flat, foot.shape))
    y = np.r_[np.ones(len(pos_rc), int), np.zeros(len(neg_rc), int)]
    aucs = {}
    for name in built["names"]:
        b = built["bands"][name]
        s = np.r_[b[pos_rc[:, 0], pos_rc[:, 1]], b[neg_rc[:, 0], neg_rc[:, 1]]].astype(np.float64)
        auc = float(roc_auc_score(y, s))
        aucs[name] = {"auc": auc, "canary_max_auc_1mauc": max(auc, 1.0 - auc)}

    prep = np.load(paths.PREPARED_FEATURES, mmap_mode="r")
    meta = json.loads(paths.PREPARED_META.read_text())
    idx = {n: i for i, n in enumerate(meta["names"])}
    sample = np.sort(rng.choice(X.shape[0], size=200_000, replace=False))
    ref = {r: np.asarray(prep[sample, idx[r]], dtype=np.float64)
           for r in ("tmi_hg", "tmi", "iso_grav_anom_hg", "iso_grav_anom", "rtp")}
    spear = {}
    for j, name in enumerate(built["names"]):
        v = X[sample, j].astype(np.float64)
        spear[name] = {r: float(spearmanr(v, ref[r], nan_policy="omit").statistic) for r in ref}

    canary = {
        "experiment": "S16 Exp1 canary (knowledge/49); no detector trained",
        "bands": built["names"], "valid_frac_in_footprint": built["valid_frac"],
        "extra_npy": str(out_extra.relative_to(ROOT)), "extra_sha256": sha256_file(out_extra),
        "prepared_features_sha256": meta["sha256"],
        "losfo_assignment_seed": 300, "n_systems": int(n_sys),
        "n_hidden_px_seed300": int(hidden.sum()), "n_neg_sampled": int(n_neg),
        "single_feature_auc_vs_hidden_systems": aucs,
        "canary_threshold": 0.90,
        "canary_pass": all(v["canary_max_auc_1mauc"] <= 0.90 for v in aucs.values()),
        "spearman_vs_instack_sample200k": spear,
        "band_stats_footprint": {
            n: {"min": float(np.nanmin(X[:, j])), "p50": float(np.nanmedian(X[:, j])),
                "max": float(np.nanmax(X[:, j])), "finite_frac": float(np.isfinite(X[:, j]).mean())}
            for j, n in enumerate(built["names"])},
        "seconds": round(time.time() - t0, 1),
    }
    outp = ROOT / "evidence/s16_canary.json"
    outp.write_text(json.dumps(canary, indent=2) + "\n")
    print(json.dumps(canary, indent=2))
    return 0 if canary["canary_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
