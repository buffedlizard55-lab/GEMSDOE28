#!/usr/bin/env python3
"""Session 21 (S21-PUHGB) — fresh PU-HGB lane. 3 experiments, budget-bound.

Exp1: byte-forensic replication of champion lineage (learning only).
Exp2: hide-and-recover holdout (seeds 350-352, quadrant folds) comparing
      fresh PU-HGB surface, rank-fusion with lidar step ridge, and the
      dotted H19-5 d2.8 emission baseline, all under identical emission
      (greedy 2.8px spacing, catalogue ring<=2 excluded, matched budget).
Exp3: full-data emission of the fresh lane + uniqueness vs registry.

No DrivenData contact. All numbers labelled HOLDOUT-DTI (local) or
OWNER-REPORTED (user-supplied). Projections are MODEL, never scores.
"""
from __future__ import annotations
import hashlib, json, sys, time
from pathlib import Path
import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, uniform_filter
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, holdout, metric, submission  # noqa: E402
from gems27.thinning import dot_thin  # noqa: E402

DATA = ROOT / "data"
EV = ROOT / "evidence"
T0 = time.time()
BANDS = 19
SENTINEL = -1e30

def log(*a): print(f"[{time.time()-T0:7.1f}s]", *a, flush=True)

def read1(path):
    with rasterio.open(path) as ds: return ds.read(1)

def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""): h.update(c)
    return h.hexdigest()

foot = grid.load_footprint(DATA / "sample_submission.tif")
labels = grid.load_labels(DATA / "labels.tif")
H, W = foot.shape
log("footprint", int(foot.sum()), "labels", int(labels.sum()))

# ---------- Exp 1: forensic ----------
h195 = read1(DATA / "h19_5_nan.tif") > 0
dotted = read1(DATA / "dotted_h19_5_d2_8_nan.tif") > 0
solo = read1(ROOT / "docs/downloads/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-allfinite.tif") > 0
d_cat = distance_transform_edt(~labels)
re_dotted = dot_thin(h195 & foot, 2.8)
re_solo = dotted & (d_cat > 1)
champion = solo & (d_cat > 2)
champion_b3 = solo & (d_cat > 3)
forensic = {
    "h19_5_px": int(h195.sum()), "dotted_file_px": int(dotted.sum()),
    "recomputed_dot_thin_2.8_px": int(re_dotted.sum()),
    "symdiff_recomputed_vs_dotted_file": int((re_dotted ^ dotted).sum()),
    "solo_file_px": int(solo.sum()), "recomputed_solo_d_minus_ring_le1_px": int(re_solo.sum()),
    "symdiff_recomputed_solo_vs_file": int((re_solo ^ solo).sum()),
    "champion_constructed_solo_minus_ring_le2_px": int(champion.sum()),
    "champion_b3_constructed_px": int(champion_b3.sum()),
    "ring_le2_removed_from_solo": int((solo & (d_cat <= 2)).sum()),
    "ring_2_to_3_removed_from_champion": int((champion & (d_cat <= 3)).sum()),
}
log("FORENSIC", json.dumps(forensic))

# ---------- feature engineering helpers ----------
# Load training cube band-wise into float32 stack restricted to footprint rows chunking at predict time.
# For sampling we index pixels directly via rasterio window reads is slow; instead load all bands
# as float32 (19*12.3M*4 = 935MB) - too big. Load as float16 after robust scaling per band (global,
# unsupervised percentiles on footprint sample). Keep raw sample extraction from disk per band.
rng0 = np.random.default_rng(7)
foot_idx = np.flatnonzero(foot)
scaler_sample = np.sort(rng0.choice(foot_idx, size=200_000, replace=False))
rows_s, cols_s = np.divmod(scaler_sample, W)

band_stats = []
cube16 = np.empty((BANDS, H * W), dtype=np.float16)  # 467MB
with rasterio.open(DATA / "training_features.tif") as ds:
    for b in range(BANDS):
        arr = ds.read(b + 1).ravel()
        arr = np.where(arr < SENTINEL, np.nan, arr).astype(np.float32)
        samp = arr[scaler_sample]
        lo, hi = np.nanpercentile(samp, [0.5, 99.5])
        band_stats.append((float(lo), float(hi)))
        scaled = np.clip((arr - lo) / max(hi - lo, 1e-9), -0.5, 1.5)
        scaled[~np.isfinite(scaled)] = 0.0
        cube16[b] = scaled.astype(np.float16)
        del arr, scaled
log("cube16 built", cube16.shape)

# lidar bands appended to cube (v2 fix: v1 omitted the sharp scarp signal entirely)
with rasterio.open(DATA / "lidar_scarp_features_u8.tif") as ds:
    lidar_cube = np.stack([(ds.read(i + 1).astype(np.float32) / 255.0).ravel() for i in range(12)])
    step = ds.read(3).astype(np.float32); ex = ds.read(1).astype(np.float32); coh = ds.read(10).astype(np.float32)
lidar_score = (0.5 * step + 0.3 * ex + 0.2 * coh).ravel()
del step, ex, coh
cube16 = np.vstack([cube16, lidar_cube.astype(np.float16)])
NB = cube16.shape[0]  # 19 geodawn + 12 lidar = 31
log("cube with lidar", cube16.shape)

def catalogue_features(known_mask):
    """distance + ring densities from VISIBLE catalogue only."""
    d = distance_transform_edt(~known_mask).astype(np.float32)
    kf = known_mask.astype(np.float32)
    ring300 = uniform_filter(kf, size=7, mode="nearest")   # ~300m halfwindow proxy
    ring1000 = uniform_filter(kf, size=21, mode="nearest")
    return d.ravel(), ring300.ravel(), ring1000.ravel()

def design_matrix(idx, dflat, r300, r1000, yy, xx):
    # v3 fix (canary-voided v2; v3a also canary-failed at 0.963 on ring1000): ALL catalogue-
    # density/distance features dropped. Any such feature separates by construction under
    # uniform negative sampling (positives sit on catalogue lines by definition; AUC 1.00 for
    # ring300 in v2, 0.963 for ring1000 in v3a — both voided, see evidence/). Features are
    # purely the 31 geophysical/LiDAR bands + normalized coordinates. Catalogue geometry is
    # used ONLY for emission masking (allowed zone), never as a model feature.
    X = np.empty((len(idx), NB + 2), dtype=np.float32)
    for b in range(NB): X[:, b] = cube16[b, idx]
    r, c = np.divmod(idx, W)
    X[:, NB] = r / H; X[:, NB + 1] = c / W
    return X

def greedy_emit(score_flat, allowed_flat_idx, budget, min_dist=2.8):
    order = allowed_flat_idx[np.argsort(-score_flat[allowed_flat_idx], kind="stable")]
    cand = order[: max(budget * 8, budget + 1000)]
    blocked = np.zeros(H * W, dtype=bool)
    r = int(np.ceil(min_dist)); lim = min_dist * min_dist
    offs = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1) if dy * dy + dx * dx < lim]
    kept = []
    rows, cols = np.divmod(cand, W)
    for i in range(len(cand)):
        if len(kept) >= budget: break
        f = int(cand[i])
        if blocked[f]: continue
        kept.append(f)
        rr, cc = int(rows[i]), int(cols[i])
        for dy, dx in offs:
            y, x = rr + dy, cc + dx
            if 0 <= y < H and 0 <= x < W: blocked[y * W + x] = True
    out = np.zeros(H * W, dtype=bool); out[np.asarray(kept, dtype=int)] = True
    return out.reshape(H, W)

def rank01(vals):
    return rankdata(vals, method="average") / len(vals)

# ---------- Exp 2: holdout ----------
folds = holdout.make_quadrant_folds(foot)
TOTAL_BUDGET = 37654
cells = []
canary_max = {}
seeds = [350, 351, 352]
for seed in seeds:
    for fid in range(4):
        sp = holdout.make_split(labels, folds, fid, seed)
        fm, hidden, known = sp.fold_mask, sp.hidden, sp.known
        dflat, r300, r1000 = catalogue_features(known)
        d_all = d_cat.ravel()
        rng = np.random.default_rng(seed * 100 + fid)
        train_region = foot & ~fm
        pos_idx = np.flatnonzero((known & train_region).ravel())
        neg_pool = np.flatnonzero((train_region & ~labels).ravel() & (d_all >= 3))
        pos_s = rng.choice(pos_idx, size=min(20000, len(pos_idx)), replace=False)
        neg_s = rng.choice(neg_pool, size=60000, replace=False)
        Xp = design_matrix(pos_s, dflat, r300, r1000, None, None)
        Xn = design_matrix(neg_s, dflat, r300, r1000, None, None)
        # canary on first cell only (full feature list)
        X = np.vstack([Xp, Xn]); y = np.r_[np.ones(len(Xp)), np.zeros(len(Xn))]
        if seed == seeds[0] and fid == 0:
            for j in range(X.shape[1]):
                try: canary_max[f"f{j}"] = float(roc_auc_score(y, X[:, j]))
                except Exception: canary_max[f"f{j}"] = None
            worst = max(v for v in canary_max.values() if v is not None)
            log("CANARY max single-feature AUC", worst)
            assert worst <= 0.90, f"LEAKAGE CANARY FAIL: max AUC {worst}"
        clf = HistGradientBoostingClassifier(max_iter=250, learning_rate=0.06, max_leaf_nodes=63,
                                             min_samples_leaf=40, l2_regularization=1.0, random_state=seed)
        clf.fit(X, y)
        # predict ALL test-fold unknown pixels (for honest surface AUC); emission restricted below
        test_all = np.flatnonzero((fm & ~known).ravel())
        test_allowed = np.flatnonzero((fm & ~known).ravel() & (dflat > 2))
        probs = np.zeros(H * W, dtype=np.float32)
        for s0 in range(0, len(test_all), 200_000):
            idx = test_all[s0:s0 + 200_000]
            probs[idx] = clf.predict_proba(design_matrix(idx, dflat, r300, r1000, None, None))[:, 1]
        budget = int(round(TOTAL_BUDGET * fm.sum() / foot.sum()))
        rs, cs = holdout.crop(fm, fm)
        def score(em):
            return metric.dti_binary(em[rs, cs].astype(float), hidden[rs, cs],
                                     valid=fm[rs, cs], known=known[rs, cs])
        em_hgb = greedy_emit(probs, test_allowed, budget)
        fus = probs.copy()
        fus[test_allowed] = (0.5 * rank01(probs[test_allowed]) + 0.5 * rank01(lidar_score[test_allowed])).astype(np.float32)
        em_fus = greedy_emit(fus, test_allowed, budget)
        # v2 fix: prune baseline against VISIBLE catalogue only (v1 used full labels incl. hidden truth)
        base_allowed = np.flatnonzero((dotted & fm & ~known).ravel() & (dflat > 2))
        em_base = np.zeros(H * W, dtype=bool); em_base[base_allowed] = True; em_base = em_base.reshape(H, W)
        # surface AUC: hidden px vs sampled fold negatives
        hid_idx = np.flatnonzero(hidden.ravel())
        neg_t = rng.choice(test_allowed, size=min(20000, len(test_allowed)), replace=False)
        auc = float(roc_auc_score(np.r_[np.ones(len(hid_idx)), np.zeros(len(neg_t))],
                                  np.r_[probs[hid_idx], probs[neg_t]]))
        cell = {"seed": seed, "fold": holdout.FOLD_NAMES[fid], "budget": budget,
                "n_hidden": int(hidden.sum()), "surface_auc_hgb": auc,
                "hgb": score(em_hgb), "fusion": score(em_fus), "dotted_b2": score(em_base)}
        cells.append(cell)
        log(f"cell s{seed} {cell['fold']} hid={cell['n_hidden']} AUC={auc:.3f} "
            f"HGB={cell['hgb']['dti']:.4f} FUS={cell['fusion']['dti']:.4f} BASE={cell['dotted_b2']['dti']:.4f}")

def pooled(key):
    TP = sum(c[key]["TPw"] for c in cells); FP = sum(c[key]["FPw"] for c in cells); FN = sum(c[key]["FNw"] for c in cells)
    return TP / (TP + 0.2 * FP + 0.8 * FN + 1e-7)

def boot_ci(key_a, key_b=None, n=2000, rng_s=99):
    rng = np.random.default_rng(rng_s); vals = []
    for _ in range(n):
        idx = rng.integers(0, len(cells), len(cells))
        def p(key):
            TP = sum(cells[i][key]["TPw"] for i in idx); FP = sum(cells[i][key]["FPw"] for i in idx); FN = sum(cells[i][key]["FNw"] for i in idx)
            return TP / (TP + 0.2 * FP + 0.8 * FN + 1e-7)
        vals.append(p(key_a) - (p(key_b) if key_b else 0.0))
    return [float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))]

holdout_res = {
    "evaluator": "src/gems27/metric.py dti_binary (alpha0.2 beta0.8 300m triangular), holdout=gems27.holdout quadrant component-hide 20%",
    "seeds": seeds, "cells": len(cells),
    "withheld_positives_total_across_cells": int(sum(c["n_hidden"] for c in cells)),
    "pooled": {"hgb": pooled("hgb"), "fusion": pooled("fusion"), "dotted_b2": pooled("dotted_b2")},
    "ci95_hgb": boot_ci("hgb"), "ci95_fusion": boot_ci("fusion"), "ci95_base": boot_ci("dotted_b2"),
    "delta_hgb_minus_base": pooled("hgb") - pooled("dotted_b2"), "ci95_delta_hgb": boot_ci("hgb", "dotted_b2"),
    "delta_fus_minus_base": pooled("fusion") - pooled("dotted_b2"), "ci95_delta_fus": boot_ci("fusion", "dotted_b2"),
    "canary_single_feature_auc_cell0": canary_max,
    "canary_max_abs_dev_from_0.5": max(abs(v - 0.5) for v in canary_max.values() if v is not None),
    "cells_detail": cells,
}
log("HOLDOUT pooled", json.dumps(holdout_res["pooled"]), "deltaHGB", holdout_res["delta_hgb_minus_base"], holdout_res["ci95_delta_hgb"])

# ---------- Exp 3: full emission ----------
dflat, r300, r1000 = catalogue_features(labels)
rng = np.random.default_rng(2026)
pos_idx = np.flatnonzero(labels.ravel())
neg_pool = np.flatnonzero((foot & ~labels).ravel() & (d_cat.ravel() >= 3))
pos_s = rng.choice(pos_idx, size=40000, replace=False)
neg_s = rng.choice(neg_pool, size=120000, replace=False)
X = np.vstack([design_matrix(pos_s, dflat, r300, r1000, None, None),
               design_matrix(neg_s, dflat, r300, r1000, None, None)])
y = np.r_[np.ones(len(pos_s)), np.zeros(len(neg_s))]
clf = HistGradientBoostingClassifier(max_iter=350, learning_rate=0.06, max_leaf_nodes=63,
                                     min_samples_leaf=40, l2_regularization=1.0, random_state=2026)
clf.fit(X, y)
allowed = np.flatnonzero((foot & ~labels).ravel() & (d_cat.ravel() > 2))
probs = np.zeros(H * W, dtype=np.float32)
for s0 in range(0, len(allowed), 200_000):
    idx = allowed[s0:s0 + 200_000]
    probs[idx] = clf.predict_proba(design_matrix(idx, dflat, r300, r1000, None, None))[:, 1]
log("full prediction done; allowed", len(allowed))
em_hgb = greedy_emit(probs, allowed, TOTAL_BUDGET)
fus = probs.copy()
fus[allowed] = (0.5 * rank01(probs[allowed]) + 0.5 * rank01(lidar_score[allowed])).astype(np.float32)
em_fus = greedy_emit(fus, allowed, TOTAL_BUDGET)
np.save("/tmp/s21_probs.npy", probs); np.save("/tmp/s21_em_hgb.npy", em_hgb); np.save("/tmp/s21_em_fus.npy", em_fus)

# uniqueness vs registry binaries
def overlap_3px(em, ref):
    d = distance_transform_edt(~ref)
    return float((d[em] <= 3).mean()) if em.any() else 0.0

def load_bin(p): return read1(p) > 0
registry = {
    "solo_h27_4": solo, "champion_constructed_b2": champion, "dotted_d2_8": dotted,
    "h36_1": load_bin(ROOT / "docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif"),
    "s20_nchc": load_bin(ROOT / "docs/downloads/gems28-s20-nchc-20261026-d432a1d5d6ee-allfinite.tif"),
    "s20v": load_bin(ROOT / "docs/downloads/gems28-s20-vesselness-lidarstep-20261026-7a7c5e449fe0-allfinite.tif"),
}
samp = np.sort(rng.choice(foot_idx, size=200_000, replace=False))
uniq = {}
for name, em in [("hgb", em_hgb), ("fusion", em_fus)]:
    uniq[name] = {}
    for rn, ref in registry.items():
        sp = float(np.corrcoef(rankdata(probs[samp]), rankdata(ref.ravel().astype(float)[samp]))[0, 1]) if name == "hgb" else None
        uniq[name][rn] = {"overlap3px": overlap_3px(em, ref),
                          "jaccard": float((em & ref).sum() / max((em | ref).sum(), 1)),
                          "spearman_surface_vs_binary_sample200k": sp}
log("UNIQ", json.dumps(uniq)[:800])

out = {"forensic": forensic, "holdout": {k: v for k, v in holdout_res.items() if k != "cells_detail"},
       "cells_detail": cells, "uniqueness": uniq,
       "full_emission": {"hgb_px": int(em_hgb.sum()), "fusion_px": int(em_fus.sum()),
                         "hgb_on_catalogue": int((em_hgb & labels).sum()), "fus_on_catalogue": int((em_fus & labels).sum()),
                         "hgb_outside_footprint": int((em_hgb & ~foot).sum())},
       "band_stats": band_stats, "runtime_s": time.time() - T0}
(EV / "s21_lane_result.json").write_text(json.dumps(out, indent=1, default=str))
log("DONE", out["runtime_s"])
