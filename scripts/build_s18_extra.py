#!/usr/bin/env python3
"""S18 Experiment 1 (knowledge/52): H42-1 migration vector field + leakage canary.

Builds the label-free migration vector field (data/prepared/migration_vectors.npz) and the
four H40-1 scalar bands, then runs the frozen single-feature canary: AUC of each candidate
band alone vs LOSFO seed-310 withheld systems (S16 protocol). max(AUC,1-AUC) > 0.90 is
leakage -> nonzero exit, no gate may run. No detector is trained here.
Writes evidence/s18_canary.json.
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

SEED = 310


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
    print(f"scalar bands done ({time.time()-t0:.0f}s)", flush=True)
    vec = migration.build_migration_vectors(paths.TRAINING, foot)
    depth = migration.read_depth_to_base(paths.TRAINING, foot)
    print(f"vector field done ({time.time()-t0:.0f}s)", flush=True)

    vmag = np.hypot(vec["vx"], vec["vy"]).astype(np.float32)
    smag = migration.shift_magnitude(vec["vy"], vec["vx"], depth)
    bands = dict(built["bands"])
    bands["migvec_mag_px"] = vmag
    bands["migx_shift_mag_px"] = smag
    names = list(bands)

    out_npz = paths.DATA / "prepared/migration_vectors.npz"
    out_npz.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_npz, vy=vec["vy"], vx=vec["vx"],
                        coherence_tmi=vec["coherence_tmi"], coherence_grav=vec["coherence_grav"])

    fold = holdout.make_quadrant_folds(foot)
    sys_grid, n_sys = losfo.fault_systems(labels, losfo.DEFAULT_DILATE_PX)
    tab = losfo.system_table(sys_grid, n_sys, foot)
    hold = losfo.assign_systems_to_folds(tab, fold, 4, seed=SEED)
    hidden = np.isin(sys_grid, np.flatnonzero(hold >= 0) + 1) & foot
    d_hidden = distance_transform_edt(~hidden)
    rng = np.random.default_rng(SEED)
    neg_pool = np.flatnonzero((foot & ~labels & (d_hidden > 6)).ravel())
    pos_rc = np.argwhere(hidden)
    n_neg = min(len(neg_pool), max(50_000, 20 * len(pos_rc)), 250_000)
    neg_flat = rng.choice(neg_pool, size=n_neg, replace=False)
    neg_rc = np.column_stack(np.unravel_index(neg_flat, foot.shape))
    y = np.r_[np.ones(len(pos_rc), int), np.zeros(len(neg_rc), int)]
    aucs = {}
    for name in names:
        b = bands[name]
        s = np.r_[b[pos_rc[:, 0], pos_rc[:, 1]], b[neg_rc[:, 0], neg_rc[:, 1]]]
        auc = float(roc_auc_score(y, s))
        aucs[name] = {"auc": auc, "canary_max_auc_1mauc": max(auc, 1.0 - auc)}

    # Spearman of new bands vs in-stack bands on a 200k footprint sample (surface-duplicate check)
    X = np.load(paths.PREPARED_FEATURES, mmap_mode="r")
    meta = json.loads(paths.PREPARED_META.read_text())
    idx_names = {n: i for i, n in enumerate(meta["names"])}
    foot_rc = np.argwhere(foot)
    rng2 = np.random.default_rng(2026)
    samp = np.sort(rng2.choice(len(foot_rc), size=200_000, replace=False))
    rc = foot_rc[samp]
    spear = {}
    for name in names:
        bv = bands[name][rc[:, 0], rc[:, 1]].astype(np.float64)
        spear[name] = {}
        for ref in ("tmi_hg", "tmi", "iso_grav_anom_hg", "iso_grav_anom", "rtp"):
            rv = np.asarray(X[samp, idx_names[ref]], dtype=np.float64)
            ok = np.isfinite(bv) & np.isfinite(rv)  # prepared stack carries NaN at invalid px
            spear[name][ref] = float(spearmanr(bv[ok], rv[ok]).statistic)

    support = vmag[foot] > 0
    sm = smag[foot]
    inventory = {
        "vector_support_frac_footprint": float(support.mean()),
        "vmag_px_on_support": {
            "p50": float(np.median(vmag[foot][support])), "p90": float(np.percentile(vmag[foot][support], 90)),
            "max": float(vmag[foot].max())},
        "shift_mag_px_footprint": {
            "frac_ge_0p5": float((sm >= 0.5).mean()), "frac_ge_1p5": float((sm >= 1.5).mean()),
            "frac_at_cap3": float((sm >= 3.0).mean()), "p99": float(np.percentile(sm, 99))},
        "depth_to_base_m_footprint": {
            "p50": float(np.median(depth[foot])), "p95": float(np.percentile(depth[foot], 95)),
            "frac_zero_invalid": float((depth[foot] == 0).mean())},
    }
    band_stats = {n: {"min": float(bands[n][foot].min()), "p50": float(np.median(bands[n][foot])),
                      "max": float(bands[n][foot].max()),
                      "finite_frac": float(np.isfinite(bands[n][foot]).mean())} for n in names}

    canary = {
        "experiment": "S18 Exp1 canary (knowledge/52); no detector trained",
        "bands": names,
        "valid_frac_in_footprint": built["valid_frac"],
        "vectors_npz": str(out_npz.relative_to(ROOT)),
        "vectors_npz_sha256": sha256_file(out_npz),
        "prepared_features_sha256": sha256_file(paths.PREPARED_FEATURES),
        "losfo_assignment_seed": SEED,
        "n_systems": int(n_sys),
        "n_hidden_px_seed310": int(hidden.sum()),
        "n_neg_sampled": int(n_neg),
        "single_feature_auc_vs_hidden_systems": aucs,
        "canary_threshold": 0.9,
        "canary_pass": all(v["canary_max_auc_1mauc"] <= 0.90 for v in aucs.values()),
        "spearman_vs_instack_sample200k": spear,
        "label_free_shift_inventory": inventory,
        "band_stats_footprint": band_stats,
        "seconds": round(time.time() - t0, 1),
    }
    outp = ROOT / "evidence/s18_canary.json"
    outp.write_text(json.dumps(canary, indent=2) + "\n")
    print(json.dumps(canary, indent=2))
    return 0 if canary["canary_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
