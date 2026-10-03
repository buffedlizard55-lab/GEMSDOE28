#!/usr/bin/env python3
"""H37-1 frozen gate: metric-aware packing (lazy-greedy maximum expected coverage) at matched N.

Protocol frozen in ``knowledge/29_preregistration_H37-1.md`` **before** this file was executed. Fresh
seed decade 250-259. The detector, the folds, the 600 m buffer, ``PRE_THIN_FRAC`` and the
``H27-4`` blind 1-px catalogue-flank prune are **unmodified** from ``scripts/run_h36_1_holdout.py``;
only the packing rule differs, and the primary variant starts from exactly the incumbent's dot count,
so the comparison is layout-only.

Variants:
  base_oof_d280                    reference: dot_thin(top-k pool, 2.8)
  rung30_blind_r1                  incumbent (H36-1 winner)
  cover_prob_r1                    PRIMARY: coverage(max expected, detector field) at N_pre(rung30)
  cover_prob_1p5n_r1               dose: 1.5 x N_pre(rung30)
  cover_prob_pool3x_r1             pool-density probe: top-3k pool instead of all ridge pixels
  control_random_matched_n         content-blind control at the same N from the same pool
  cover_prob_anywhere_r1           exploratory ceiling (off-ridge pool; never promotable)

Writes ``evidence/h37_1_holdout.json``. Reads no hidden truth; never contacts drivendata.org.
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
from gems27 import grid, holdout, metric, oof_detector, packing, paths, thinning  # noqa: E402

VARIANT_NAMES = [
    "base_oof_d280",
    "rung30_blind_r1",
    "cover_prob_r1",
    "cover_prob_1p5n_r1",
    "cover_prob_pool3x_r1",
    "control_random_matched_n",
    "cover_prob_anywhere_r1",
]
INCUMBENT = "rung30_blind_r1"
PRIMARY = "cover_prob_r1"
CONTROL = "control_random_matched_n"
PROMOTION_MARGIN = 0.0005
#: RNG namespace for the content control, disjoint from the holdout seeds (4242 + fold + 1000*seed).
CONTROL_SEED_BASE = 990_000
THIN_D_REF = 2.8
RUNG30 = 3.0


def eval_set(pred: np.ndarray, g: np.ndarray, active: np.ndarray) -> tuple[float, float, float, int]:
    """(TPw, FPw, DTI, n_emitted) for one variant on one cell - identical to run_h36_1_holdout.py."""
    p = pred & active
    n_g = int(g.sum())
    if not p.any() or n_g == 0:
        k_pt = metric.kernel_from_distance(distance_transform_edt(~g)) if n_g else np.zeros_like(g, float)
        fp = float((1.0 - k_pt[p]).sum()) if p.any() else 0.0
        return 0.0, fp, 0.0, int(p.sum())
    k_pt = metric.kernel_from_distance(distance_transform_edt(~g))
    tp = float(metric.kernel_from_distance(distance_transform_edt(~p)[g]).sum())
    fp = float((1.0 - k_pt[p]).sum())
    dti = tp / (tp + 0.2 * fp + 0.8 * (n_g - tp) + 1e-7)
    return tp, fp, dti, int(p.sum())


def top_pool(ridge: np.ndarray, prob: np.ndarray, k: int) -> np.ndarray:
    """The k highest-probability ridge pixels (the reference rule's candidate pool)."""
    ys, xs = np.nonzero(ridge)
    pool = np.zeros_like(ridge, bool)
    if len(ys) == 0 or k <= 0:
        return pool
    if len(ys) > k:
        top = np.argpartition(-prob[ys, xs], k - 1)[:k]
        ys, xs = ys[top], xs[top]
    pool[ys, xs] = True
    return pool


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="250-259")
    ap.add_argument("--out", default=str(paths.EVIDENCE / "h37_1_holdout.json"))
    args = ap.parse_args()
    a, _, b = args.seeds.partition("-")
    seeds = list(range(int(a), int(b) + 1)) if b else [int(a)]

    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)

    print("Training 4-fold spatial-CV HistGradientBoostingClassifier (600 m buffer)...", flush=True)
    oof_prob = oof_detector.fit_predict_oof_probabilities(foot, labels, fold)
    ridge_all = oof_detector.ridge_nms(oof_prob, foot, sigma=1.0)
    print(f"OOF probabilities & ridges in {time.time()-t0:.1f}s (ridges={int(ridge_all.sum()):,})",
          flush=True)

    cells = []
    integrity: list[str] = []
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

            k = int(round(oof_detector.PRE_THIN_FRAC * int(fmc.sum())))
            pool = top_pool(ridges, prob, k)
            pool3x = top_pool(ridges, prob, 3 * k)
            blind_r1 = distance_transform_edt(~kn) <= 1.0

            base = oof_detector.build_oof_dotted_base(
                oof_prob[sl], ridge_all[sl], fmc, kn,
                budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=THIN_D_REF,
            ) & active
            rung30_pre = thinning.dot_thin(pool, RUNG30)
            n_pre = int(rung30_pre.sum())

            rng = np.random.default_rng(CONTROL_SEED_BASE + 10 * seed + f)
            ys, xs = np.nonzero(ridges)
            random_sel = np.zeros_like(ridges)
            if len(ys) and n_pre > 0:
                take = rng.choice(len(ys), size=min(n_pre, len(ys)), replace=False)
                random_sel[ys[take], xs[take]] = True

            primary_pre = packing.coverage_greedy(ridges, prob, n_pre)
            variants = {
                "base_oof_d280": base,
                "rung30_blind_r1": rung30_pre & ~blind_r1,
                "cover_prob_r1": primary_pre & ~blind_r1,
                "cover_prob_1p5n_r1": packing.coverage_greedy(ridges, prob, int(round(1.5 * n_pre)))
                                       & ~blind_r1,
                "cover_prob_pool3x_r1": packing.coverage_greedy(pool3x, prob, n_pre) & ~blind_r1,
                "control_random_matched_n": random_sel & ~blind_r1,
                "cover_prob_anywhere_r1": packing.coverage_greedy(active, prob, n_pre) & ~blind_r1,
            }

            # ---- G5 integrity, evaluated per cell before any metric is read ---------------------
            if int(primary_pre.sum()) != n_pre:
                integrity.append(f"seed {seed} fold {sp.name}: packer emitted {int(primary_pre.sum())} "
                                 f"!= N_pre(rung30)={n_pre}")
            if (variants[PRIMARY] & ~active).any():
                integrity.append(f"seed {seed} fold {sp.name}: primary outside the active area")
            if (variants[PRIMARY] & kn).any():
                integrity.append(f"seed {seed} fold {sp.name}: primary overlaps known catalogue pixels")
            if (variants[PRIMARY] & fmc).sum() == 0:
                integrity.append(f"seed {seed} fold {sp.name}: primary emitted nothing")

            row = {"seed": seed, "fold": sp.name, "n_truth": int(g.sum()), "n_pre_rung30": n_pre,
                   "n_pool": int(pool.sum()), "n_ridges": int(ridges.sum())}
            for vn, mask in variants.items():
                tp, fp, dti, n_px = eval_set(mask, g, active)
                row[vn] = {"tp": tp, "fp": fp, "dti": dti, "dots": n_px}
            cells.append(row)
        print(f"seed {seed} done (t={time.time()-t0:.0f}s): "
              f"base={np.mean([c['base_oof_d280']['dti'] for c in cells if c['seed']==seed]):.5f} "
              f"inc={np.mean([c['rung30_blind_r1']['dti'] for c in cells if c['seed']==seed]):.5f} "
              f"cover={np.mean([c['cover_prob_r1']['dti'] for c in cells if c['seed']==seed]):.5f} "
              f"rand={np.mean([c['control_random_matched_n']['dti'] for c in cells if c['seed']==seed]):.5f}",
              flush=True)

    base_mean = float(np.mean([c["base_oof_d280"]["dti"] for c in cells]))

    def gains(vn: str, ref: str = "base_oof_d280") -> list[float]:
        return [float(np.mean([c[vn]["dti"] - c[ref]["dti"] for c in cells if c["seed"] == s]))
                for s in seeds]

    summary = {}
    for vn in VARIANT_NAMES[1:]:
        g_seed = gains(vn)
        g_vs_inc = [float(np.mean([c[vn]["dti"] - c[INCUMBENT]["dti"] for c in cells if c["seed"] == s]))
                    for s in seeds]
        fold_gains = {fn: float(np.mean([c[vn]["dti"] - c["base_oof_d280"]["dti"]
                                        for c in cells if c["fold"] == fn])) for fn in holdout.FOLD_NAMES}
        dtp = sum(c[vn]["tp"] for c in cells) - sum(c[INCUMBENT]["tp"] for c in cells)
        dfp = sum(c[vn]["fp"] for c in cells) - sum(c[INCUMBENT]["fp"] for c in cells)
        summary[vn] = {
            "mean_dti": float(base_mean + np.mean(g_seed)),
            "mean_gain_vs_base": float(np.mean(g_seed)),
            "mean_gain_vs_incumbent": float(np.mean(g_vs_inc)),
            "min_seed_gain_vs_incumbent": float(np.min(g_vs_inc)),
            "max_seed_gain_vs_incumbent": float(np.max(g_vs_inc)),
            "seeds_won_vs_incumbent": int(sum(g > 0 for g in g_vs_inc)),
            "n_seeds": len(seeds),
            "fold_gains_vs_base": fold_gains,
            "folds_improved_vs_base": int(sum(v > 0 for v in fold_gains.values())),
            "delta_tp_vs_incumbent": float(dtp),
            "delta_fp_vs_incumbent": float(dfp),
            "delta_dots_per_seed_vs_incumbent": float(
                sum(c[vn]["dots"] - c[INCUMBENT]["dots"] for c in cells) / len(seeds)),
            "mean_dots": float(np.mean([c[vn]["dots"] for c in cells])),
        }

    g_primary = summary[PRIMARY]["mean_gain_vs_base"]
    g_inc = summary[INCUMBENT]["mean_gain_vs_base"]
    g_control = summary[CONTROL]["mean_gain_vs_base"]
    gate = {
        "G1_direction": bool(summary[PRIMARY]["mean_gain_vs_incumbent"] > 0),
        "G2_promotion": bool((g_primary - g_inc) >= PROMOTION_MARGIN),
        "G2_margin_observed": float(g_primary - g_inc),
        "G2_margin_required": PROMOTION_MARGIN,
        "G3_seeds_ge_8": bool(summary[PRIMARY]["seeds_won_vs_incumbent"] >= 8),
        "G3_folds_4of4": bool(summary[PRIMARY]["folds_improved_vs_base"] == 4),
        "G4_content_control_margin": float(g_primary - g_control),
        "G4_passed": bool((g_primary - g_control) >= PROMOTION_MARGIN),
        "G5_integrity_violations": integrity,
        "G5_passed": bool(not integrity),
        "report_only_incumbent_gain_vs_base": float(g_inc),
        "reproducibility_note": ("H36-1 measured +0.002599 for rung30_blind_r1 on seeds 240-249; this "
                                 "decade is fresh, so a different value is expected and is reported, "
                                 "not gated."),
    }
    gate["passed"] = bool(gate["G1_direction"] and gate["G2_promotion"] and gate["G3_seeds_ge_8"]
                          and gate["G3_folds_4of4"] and gate["G4_passed"] and gate["G5_passed"])

    out = {
        "hypothesis": ("H37-1: metric-aware dot packing (lazy-greedy maximum expected coverage of the "
                       "detector probability field under the official 300 m kernel) at matched emission "
                       "count, with the unchanged H27-4 blind 1-px catalogue-flank prune"),
        "preregistration": "knowledge/29_preregistration_H37-1.md",
        "runner_sha256_note": "see evidence/h37_1_holdout.json written by the committed runner",
        "seeds": seeds,
        "n_cells": len(cells),
        "base_oof_d280_mean_dti": base_mean,
        "variants": summary,
        "gate": gate,
        "runtime_s": round(time.time() - t0, 1),
        "cells": cells,
    }
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: v for k, v in summary.items()}, indent=2))
    print(json.dumps(gate, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
