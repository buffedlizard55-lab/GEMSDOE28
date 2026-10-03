#!/usr/bin/env python3
"""EXPLORATORY (not a gate): does an evidence-aware packing rule beat the raster-index cascade?

Diagnostic only. Runs on **spent** seed decades so no fresh seed is consumed; its purpose is to
size the effect and to choose ONE variant to freeze in a later preregistration. It reads no hidden
truth beyond the standing spatially-blocked holdout, and it never contacts DrivenData.

Why this is worth measuring
---------------------------
`gems27.thinning.dot_thin` keeps a pixel iff no already-kept pixel is closer than `min_dist`, walking
candidates in ascending raster index and seeding the breadth-first cascade at the lowest index of each
8-connected component. The rule is therefore *content-blind*: a candidate's evidence strength never
influences whether it survives, only its position in memory does. H36-1 measured that changing the
layout at constant budget is worth +0.0026 OOF DTI (10/10 seeds) while a matched-N random deletion
*loses* 0.0017 - so layout carries real information that the current rule does not read.

Three packers, all matched to the reference emission's per-cell pixel count N:
  base_oof_d280        (reference) top-k ridge pixels then dot_thin(2.8)              [index order]
  greedy_prob          same candidate pool, kept in DESCENDING OOF probability order
  cover_topk           same candidate pool, greedy maximum EXPECTED COVERAGE of the OOF
                       probability field under the official triangular kernel (R = 3 px)
  cover_allridge       as cover_topk but the pool is every ridge pixel in the cell
  control_random_n     same pool, N pixels drawn uniformly at random (content-blind control)

Expected-coverage model: a dot at x contributes  sum_q p(q) * max(0, k(|x-q|) - C(q)) where q runs over
the 7x7 neighbourhood, k(d) = max(1 - d/3, 0) is the official kernel and C is the coverage already
achieved by the kept dots. That is the expected distance-weighted TP of the official metric under the
detector's own probability field, so this is the metric itself used as the packing objective.

Usage:  GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/explore_packing_h37.py --seeds 181,185
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import grid, holdout, metric, oof_detector, paths  # noqa: E402

RADIUS_PX = metric.RADIUS_PX  # 3.0 px = 300 m, the official kernel
THIN_D = 2.8


def disc_rel(min_dist: float) -> tuple[int, np.ndarray]:
    r = int(np.ceil(min_dist))
    dy, dx = np.mgrid[-r:r + 1, -r:r + 1]
    return r, (dy * dy + dx * dx) < min_dist * min_dist


def greedy_prob_pack(cand: np.ndarray, prob: np.ndarray, n_target: int, min_dist: float = THIN_D) -> np.ndarray:
    """Keep candidates in descending probability order subject to the same hard spacing as dot_thin."""
    ys, xs = np.nonzero(cand)
    if len(ys) == 0 or n_target <= 0:
        return np.zeros_like(cand, bool)
    r, mask = disc_rel(min_dist)
    pad = r + 1
    H, W = cand.shape
    blocked = np.zeros((H + 2 * pad, W + 2 * pad), bool)
    keep = np.zeros_like(cand, bool)
    order = np.argsort(-prob[ys, xs], kind="stable")
    n_kept = 0
    for i in order:
        y, x = int(ys[i]) + pad, int(xs[i]) + pad
        if blocked[y, x]:
            continue
        keep[y - pad, x - pad] = True
        n_kept += 1
        if n_kept >= n_target:
            break
        blocked[y - r:y + r + 1, x - r:x + r + 1] |= mask
    return keep


def _kernel_patch(radius: int) -> np.ndarray:
    dy, dx = np.mgrid[-radius:radius + 1, -radius:radius + 1]
    return np.maximum(1.0 - np.hypot(dy, dx) / RADIUS_PX, 0.0).astype(np.float32)


def coverage_greedy(cand: np.ndarray, prob: np.ndarray, n_target: int) -> np.ndarray:
    """Lazy-greedy maximum expected coverage of `prob` by at most `n_target` dots on `cand`.

    gain(x) = sum_q prob(q) * max(0, k(|x-q|) - C(q)), q in the 7x7 neighbourhood of x, C = achieved
    coverage. Submodular, so the lazy (accelerated) greedy of Minoux (1978) is exact for the greedy
    order; the classic (1 - 1/e) guarantee of Nemhauser, Wolsey & Fisher (1978) applies.
    """
    H, W = prob.shape
    ys, xs = np.nonzero(cand)
    if len(ys) == 0 or n_target <= 0:
        return np.zeros_like(cand, bool)
    r = int(RADIUS_PX)
    patch = _kernel_patch(r)
    padded = np.zeros((H + 2 * r, W + 2 * r), np.float32)
    padded[r:r + H, r:r + W] = np.asarray(prob, np.float32)
    cov = np.zeros_like(padded)
    keep = np.zeros_like(cand, bool)

    def gain(py: int, px: int) -> float:
        sub = padded[py - r:py + r + 1, px - r:px + r + 1] * patch - cov[py - r:py + r + 1, px - r:px + r + 1]
        np.maximum(sub, 0.0, out=sub)
        return float(sub.sum())

    # Initial upper bounds: exact gains with C = 0 (a 7x7 correlation per candidate).
    heap: list[tuple[float, int, int, int]] = []  # (-gain, y, x, stamp)
    stamp = 0
    for y, x in zip(ys.tolist(), xs.tolist()):
        # upper bound: the coverage of the kernel patch centred here, ignoring C
        sub = padded[y:y + 2 * r + 1, x:x + 2 * r + 1] * patch
        heap.append((-float(sub.sum()), y + r, x + r, stamp))
        stamp += 1
    import heapq

    heapq.heapify(heap)
    n_kept = 0
    while heap and n_kept < n_target:
        neg_ub, py, px, st = heapq.heappop(heap)
        exact = gain(py, px)
        if heap and -exact > heap[0][0] + 1e-9:
            # a stale bound cannot win yet: re-insert with the tighter bound
            heapq.heappush(heap, (-exact, py, px, st))
            continue
        if exact <= 0.0:
            break
        keep[py - r, px - r] = True
        n_kept += 1
        window = cov[py - r:py + r + 1, px - r:px + r + 1]
        np.maximum(window, patch, out=window)
    return keep


def random_pack(cand: np.ndarray, n_target: int, rng: np.random.Generator) -> np.ndarray:
    ys, xs = np.nonzero(cand)
    if len(ys) == 0 or n_target <= 0:
        return np.zeros_like(cand, bool)
    n = min(n_target, len(ys))
    sel = rng.choice(len(ys), size=n, replace=False)
    out = np.zeros_like(cand, bool)
    out[ys[sel], xs[sel]] = True
    return out


def eval_dti(pred: np.ndarray, g: np.ndarray, active: np.ndarray) -> dict:
    p = pred & active
    n_g = int(g.sum())
    if not p.any() or n_g == 0:
        return {"tp": 0.0, "fp": float(p.sum()), "dti": 0.0, "n": int(p.sum())}
    k_pt = metric.kernel_from_distance(distance_transform_edt(~g)) if n_g else np.zeros_like(g, float)
    tp = float(metric.kernel_from_distance(distance_transform_edt(~p)[g]).sum())
    fp = float((1.0 - k_pt[p]).sum())
    return {"tp": tp, "fp": fp, "dti": tp / (tp + 0.2 * fp + 0.8 * (n_g - tp) + 1e-7), "n": int(p.sum())}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="181,185")
    ap.add_argument("--out", default="evidence/_scratch/packing_h37_explore.json")
    args = ap.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]

    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)
    cache = Path("data_cache")
    cache.mkdir(exist_ok=True)
    if (cache / "oof_prob.npy").exists():
        oof_prob = np.load(cache / "oof_prob.npy")
        ridge_all = np.load(cache / "ridge_all.npy")
        print("loaded cached OOF probabilities", flush=True)
    else:
        oof_prob = oof_detector.fit_predict_oof_probabilities(foot, labels, fold)
        ridge_all = oof_detector.ridge_nms(oof_prob, foot, sigma=1.0)
        np.save(cache / "oof_prob.npy", oof_prob)
        np.save(cache / "ridge_all.npy", ridge_all)
    print(f"detector ready t={time.time()-t0:.0f}s ridges={int(ridge_all.sum()):,}", flush=True)

    rows = []
    for seed in seeds:
        for f in range(4):
            sp = holdout.make_split(labels, fold, f, seed)
            fm = sp.fold_mask
            sl = holdout.crop(None, fm)
            hid, kn, fmc = sp.hidden[sl], (sp.known & fm)[sl], fm[sl]
            g = hid & fmc & ~kn
            active = fmc & ~kn
            prob = np.where(active, oof_prob[sl], 0.0).astype(np.float32)
            ridges = ridge_all[sl] & active

            base = oof_detector.build_oof_dotted_base(
                oof_prob[sl], ridge_all[sl], fmc, kn,
                budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=THIN_D,
            ) & active
            n_base = int(base.sum())

            k = int(round(oof_detector.PRE_THIN_FRAC * int(fmc.sum())))
            ys, xs = np.nonzero(ridges)
            pool_topk = np.zeros_like(ridges)
            if len(ys) > k:
                top = np.argpartition(-prob[ys, xs], k - 1)[:k]
                pool_topk[ys[top], xs[top]] = True
            else:
                pool_topk[ys, xs] = True

            variants = {
                "base_oof_d280": base,
                "greedy_prob": greedy_prob_pack(pool_topk & active, prob, n_base),
                "cover_topk": coverage_greedy(pool_topk & active, prob, n_base),
                "cover_allridge": coverage_greedy(ridges, prob, n_base),
                "control_random_n": random_pack(pool_topk & active, n_base, np.random.default_rng(770_000 + 10 * seed + f)),
            }
            row = {"seed": seed, "fold": sp.name, "n_truth": int(g.sum()), "n_base": n_base}
            for vn, mask in variants.items():
                row[vn] = eval_dti(mask, g, active)
            rows.append(row)
            print(f"  seed {seed} fold {sp.name}: base={row['base_oof_d280']['dti']:.5f} "
                  f"prob={row['greedy_prob']['dti']:.5f} cover_topk={row['cover_topk']['dti']:.5f} "
                  f"cover_all={row['cover_allridge']['dti']:.5f} rand={row['control_random_n']['dti']:.5f}",
                  flush=True)

    names = [k for k in rows[0] if k not in ("seed", "fold", "n_truth", "n_base")]
    summary = {}
    for vn in names:
        gains = [r[vn]["dti"] - r["base_oof_d280"]["dti"] for r in rows]
        summary[vn] = {
            "mean_dti": float(np.mean([r[vn]["dti"] for r in rows])),
            "mean_gain": float(np.mean(gains)),
            "min_gain": float(np.min(gains)),
            "seeds_won": int(sum(
                np.mean([r[vn]["dti"] - r["base_oof_d280"]["dti"] for r in rows if r["seed"] == s]) > 0
                for s in seeds
            )),
            "n_seeds": len(seeds),
            "mean_n": float(np.mean([r[vn]["n"] for r in rows])),
        }
    out = {"exploratory": True, "seeds": seeds, "n_cells": len(rows), "summary": summary,
           "runtime_s": round(time.time() - t0, 1), "rows": rows}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
