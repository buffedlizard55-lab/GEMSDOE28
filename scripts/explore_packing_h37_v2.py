#!/usr/bin/env python3
"""EXPLORATORY pass 2 (not a gate): isolate *why* the coverage-greedy packer wins.

Pass 1 (evidence/_scratch/packing_h37_explore.json) measured, on spent seeds 181/185:
  base_oof_d280 (index-order dot_thin on the top-k pool)  mean DTI 0.09952
  greedy_prob    (probability order, same pool)           0.09680   -0.00272
  cover_topk     (max expected coverage, same pool)       0.09928   -0.00024
  cover_allridge (max expected coverage, all ridge px)    0.10885   +0.00933
  control_random_n (random N from the same pool)          0.08154   -0.01799

so the ingredient is not "use the probability" (that alone lost) and not "cover" on the restricted
pool (neutral); it is covering a *larger candidate pool* optimally. This pass separates the two
remaining candidates: (a) merely dropping the top-k pre-filter, (b) the coverage objective, and
(c) which field is covered (detector probability vs the binary ridge set - the only one that exists
at submission time, because the shipped H19-5 surface is binary).

Also sweeps the emission budget, because a different packer can move the optimal N.

Usage: GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/explore_packing_h37_v2.py --seeds 181,185
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import grid, holdout, oof_detector, paths  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from explore_packing_h37 import (  # noqa: E402
    THIN_D,
    coverage_greedy,
    disc_rel,
    eval_dti,
)


def index_pack_matched_n(cand: np.ndarray, n_target: int, min_dist: float = THIN_D) -> np.ndarray:
    """`dot_thin`'s rule (ascending raster index, first-come-first-served) truncated at n_target.

    Isolates the pool question: same rule as the reference, but no top-k pre-filter.
    """
    ys, xs = np.nonzero(cand)
    if len(ys) == 0 or n_target <= 0:
        return np.zeros_like(cand, bool)
    r, mask = disc_rel(min_dist)
    pad = r + 1
    H, W = cand.shape
    blocked = np.zeros((H + 2 * pad, W + 2 * pad), bool)
    keep = np.zeros_like(cand, bool)
    n_kept = 0
    for y0, x0 in zip(ys.tolist(), xs.tolist()):
        y, x = y0 + pad, x0 + pad
        if blocked[y, x]:
            continue
        keep[y0, x0] = True
        n_kept += 1
        if n_kept >= n_target:
            break
        blocked[y - r:y + r + 1, x - r:x + r + 1] |= mask
    return keep


def coverage_greedy_weighted(cand: np.ndarray, weight: np.ndarray, n_target: int) -> np.ndarray:
    """Same lazy-greedy coverage as `coverage_greedy`, but the covered field is `weight`."""
    return coverage_greedy(cand, weight, n_target)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="181,185")
    ap.add_argument("--out", default="evidence/_scratch/packing_h37_explore_v2.json")
    args = ap.parse_args()
    seeds = [int(s) for s in args.seeds.split(",")]

    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)
    cache = Path("data_cache")
    oof_prob = np.load(cache / "oof_prob.npy")
    ridge_all = np.load(cache / "ridge_all.npy")
    print(f"loaded cached detector t={time.time()-t0:.0f}s", flush=True)

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

            binary_w = ridges.astype(np.float32)

            variants = {
                "base_oof_d280": base,
                "index_allridge_n": index_pack_matched_n(ridges, n_base),
                "cover_prob_allridge_n": coverage_greedy_weighted(ridges, prob, n_base),
                "cover_binary_allridge_n": coverage_greedy_weighted(ridges, binary_w, n_base),
                "cover_prob_allridge_1p5n": coverage_greedy_weighted(ridges, prob, int(round(1.5 * n_base))),
                "cover_prob_allridge_2n": coverage_greedy_weighted(ridges, prob, 2 * n_base),
                "cover_prob_allridge_0p75n": coverage_greedy_weighted(ridges, prob, int(round(0.75 * n_base))),
                "cover_prob_allridge_0p5n": coverage_greedy_weighted(ridges, prob, int(round(0.5 * n_base))),
            }
            row = {"seed": seed, "fold": sp.name, "n_truth": int(g.sum()), "n_base": n_base}
            for vn, mask in variants.items():
                row[vn] = eval_dti(mask, g, active)
            rows.append(row)
            print("  seed {} fold {:18s} ".format(seed, sp.name)
                  + " ".join(f"{vn.split('_')[1][:6]}={row[vn]['dti']:.4f}" for vn in list(variants)[1:]),
                  flush=True)

    names = [k for k in rows[0] if k not in ("seed", "fold", "n_truth", "n_base")]
    summary = {}
    for vn in names:
        gains = [r[vn]["dti"] - r["base_oof_d280"]["dti"] for r in rows]
        fold_gains = {
            fn: float(np.mean([r[vn]["dti"] - r["base_oof_d280"]["dti"] for r in rows if r["fold"] == fn]))
            for fn in holdout.FOLD_NAMES
        }
        summary[vn] = {
            "mean_dti": float(np.mean([r[vn]["dti"] for r in rows])),
            "mean_gain": float(np.mean(gains)),
            "min_cell_gain": float(np.min(gains)),
            "seeds_won": int(sum(
                np.mean([r[vn]["dti"] - r["base_oof_d280"]["dti"] for r in rows if r["seed"] == s]) > 0
                for s in seeds
            )),
            "n_seeds": len(seeds),
            "folds_improved": int(sum(v > 0 for v in fold_gains.values())),
            "fold_gains": fold_gains,
            "mean_n": float(np.mean([r[vn]["n"] for r in rows])),
        }
    out = {"exploratory": True, "pass": 2, "seeds": seeds, "n_cells": len(rows),
           "summary": summary, "runtime_s": round(time.time() - t0, 1), "rows": rows}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "fold_gains"} for k, v in summary.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
