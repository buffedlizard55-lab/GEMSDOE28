#!/usr/bin/env python3
"""EXPLORATORY pass 3 (not a gate): which coverage field, and at what budget, and why.

Pass 2 (evidence/_scratch/packing_h37_explore_v2.json) showed
  index rule on the FULL ridge pool                       -0.0473   (raster order is spatially biased
                                                                    once the top-k pre-filter is gone)
  coverage of the BINARY ridge set                        -0.0356   (piles dots into dense ridge knots)
  coverage of the DETECTOR PROBABILITY field, pooled       +0.0093  at matched N
  same, budget x1.5                                        +0.0133
  same, budget x2.0                                        +0.0119
  same, budget x0.75                                       +0.0021
  same, budget x0.5                                        -0.0098

So the win needs a *smooth* coverage field. At submission time the shipped surface (H19-5) is binary,
so this pass asks the decisive transferability question: does a Gaussian-smoothed binary surface - which
can be built from the shipped file alone, with no detector - reproduce the gain? It also adds the
matched-budget control that a gate will need (old rule, same N) and an off-ridge ceiling probe.

Usage: GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/explore_packing_h37_v3.py --seeds 181,185
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import gaussian_filter

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import grid, holdout, oof_detector, paths  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from explore_packing_h37 import THIN_D, coverage_greedy, eval_dti  # noqa: E402

SMOOTH_SIGMA = 2.0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="181,185")
    ap.add_argument("--out", default="evidence/_scratch/packing_h37_explore_v3.json")
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
            smooth = gaussian_filter(ridges.astype(np.float32), SMOOTH_SIGMA) * active

            base = oof_detector.build_oof_dotted_base(
                oof_prob[sl], ridge_all[sl], fmc, kn,
                budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=THIN_D,
            ) & active
            n_base = int(base.sum())
            n15 = int(round(1.5 * n_base))

            variants = {
                "base_oof_d280": base,
                # old rule at the SAME larger budget: the anti-budget control at x1.5
                "control_oldrule_1p5n": oof_detector.build_oof_dotted_base(
                    oof_prob[sl], ridge_all[sl], fmc, kn,
                    budget_frac=1.5 * oof_detector.PRE_THIN_FRAC, thin_d=THIN_D,
                ) & active,
                "cover_prob_1p5n": coverage_greedy(ridges, prob, n15),
                "cover_smooth_1p5n": coverage_greedy(ridges, smooth, n15),
                "cover_smooth_1n": coverage_greedy(ridges, smooth, n_base),
                "cover_prob_anywhere_1p5n": coverage_greedy(active, prob, n15),
            }
            row = {"seed": seed, "fold": sp.name, "n_truth": int(g.sum()), "n_base": n_base}
            for vn, mask in variants.items():
                row[vn] = eval_dti(mask, g, active)
            rows.append(row)
            print("  seed {} fold {:18s} ".format(seed, sp.name)
                  + " ".join(f"{vn}={row[vn]['dti']:.4f}" for vn in variants),
                  flush=True)

    names = [k for k in rows[0] if k not in ("seed", "fold", "n_truth", "n_base")]
    summary = {}
    for vn in names:
        gains = [r[vn]["dti"] - r["base_oof_d280"]["dti"] for r in rows]
        gains15 = [r[vn]["dti"] - r["control_oldrule_1p5n"]["dti"] for r in rows]
        fold_gains = {
            fn: float(np.mean([r[vn]["dti"] - r["base_oof_d280"]["dti"] for r in rows if r["fold"] == fn]))
            for fn in holdout.FOLD_NAMES
        }
        summary[vn] = {
            "mean_dti": float(np.mean([r[vn]["dti"] for r in rows])),
            "mean_gain_vs_base": float(np.mean(gains)),
            "mean_gain_vs_oldrule_1p5n": float(np.mean(gains15)),
            "min_cell_gain_vs_base": float(np.min(gains)),
            "seeds_won": int(sum(
                np.mean([r[vn]["dti"] - r["base_oof_d280"]["dti"] for r in rows if r["seed"] == s]) > 0
                for s in seeds
            )),
            "n_seeds": len(seeds),
            "folds_improved": int(sum(v > 0 for v in fold_gains.values())),
            "fold_gains": fold_gains,
            "mean_n": float(np.mean([r[vn]["n"] for r in rows])),
        }
    out = {"exploratory": True, "pass": 3, "seeds": seeds, "n_cells": len(rows),
           "summary": summary, "runtime_s": round(time.time() - t0, 1), "rows": rows}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: {kk: vv for kk, vv in v.items() if kk != "fold_gains"} for k, v in summary.items()}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
