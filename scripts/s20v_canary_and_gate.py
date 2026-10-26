#!/usr/bin/env python3
"""S20 Experiment 2: leakage canary + LOSFO gate for the Hessian-tubularity lane (knowledge/59).

Frozen design (do not tune after seeing results):
  * Lane surface V = vesselness.frangi_vesselness(lidar step_max) — label-free, computed once.
  * LOSFO splits (losfo.fault_systems/assign_systems_to_folds/build_losfo_split), seeds 340-342,
    dilate 3 px, buffer 6 px, quadrant folds. Catalogue-derived quantities (visible-catalogue
    distance, known mask) use ONLY the split's visible faults; visible faults are masked
    pixel-exactly by the shared evaluator (metric.dti_binary, alpha=0.2, beta=0.8, 300 m kernel).
  * Control = LOSFO OOF HGB detector trained on buffer-masked labels per seed (harness pattern).
  * Both arms: ridge pool restricted to d_visible > 2 px, top-K (PRE_THIN_FRAC) by own score,
    dot_thin(2.8), then exact matched-N by dropping lowest-scored dots of the larger arm.
  * Canary first (seed 340 cells): AUC(V alone) and AUC(step_max alone) hidden vs background.
    AUC > 0.90 aborts before any DTI is trusted (protocol section 4).
  * Pre-placement uniqueness: Spearman(V, registry rasters) on a fixed 400k footprint sample.

Writes evidence/s20v_holdout.json and caches the surface to data/prepared/s20_vesselness.npy
(git-ignored) for the Experiment-3 build. Every performance number written here is HOLDOUT-DTI.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, holdout, losfo, metric, oof_detector, paths, thinning, vesselness  # noqa: E402

SEEDS = (340, 341, 342)
EVALUATOR = "shared metric.dti_binary (eval_set v2 semantics) on LOSFO splits; src/gems27/metric.py+losfo.py"
FORENSIC_EXTRA = {
    "champion_GEMSDOE32_e5eb6e7e": Path("/tmp/gems-mirrors/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"),
    "site36_GEMSDOE36_9b9ea4e6": Path("/tmp/gems-mirrors/GEMSDOE36/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif"),
}


def emit(score, ridge, active, d_visible, k_budget):
    pool = ridge & active & (d_visible > 2.0)
    ys, xs = np.nonzero(pool)
    if len(ys) == 0 or k_budget <= 0:
        return np.zeros_like(active)
    if len(ys) > k_budget:
        top = np.argpartition(-score[ys, xs].astype(np.float64), k_budget - 1)[:k_budget]
        ys, xs = ys[top], xs[top]
    raw = np.zeros_like(active)
    raw[ys, xs] = True
    return thinning.dot_thin(raw, 2.8) & active


def match_n(dots_a, score_a, dots_b, score_b):
    """Drop lowest-scored dots of the larger arm to exact matched-N (preregistered)."""
    na, nb = int(dots_a.sum()), int(dots_b.sum())
    if na == nb:
        return dots_a, dots_b, 0, 0
    if na > nb:
        ys, xs = np.nonzero(dots_a)
        drop = np.argsort(score_a[ys, xs].astype(np.float64), kind="stable")[: na - nb]
        out = dots_a.copy()
        out[ys[drop], xs[drop]] = False
        return out, dots_b, na - nb, 0
    ys, xs = np.nonzero(dots_b)
    drop = np.argsort(score_b[ys, xs].astype(np.float64), kind="stable")[: nb - na]
    out = dots_b.copy()
    out[ys[drop], xs[drop]] = False
    return dots_a, out, 0, nb - na


def score_cell(dots, hidden, active):
    r = metric.dti_binary(dots.astype(np.float32), hidden, valid=active)
    return {"TPw": r["TPw"], "FPw": r["FPw"], "FNw": r["FNw"], "dti": r["dti"],
            "n_truth": r["n_truth"], "n_emitted": r["n_emitted"],
            "credit_per_dot": (r["TPw"] / r["n_emitted"]) if r["n_emitted"] else 0.0}


def main() -> int:
    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS) & foot
    fold = holdout.make_quadrant_folds(foot)

    with rasterio.open(paths.LIDAR) as s:
        descs = tuple((d or "").split(" - ")[0].strip() for d in s.descriptions)
        assert descs[2] == "step_max" and descs[11] == "valid", descs
        step = s.read(3).astype(np.float32)
        lidar_valid = (s.read(12) > 0) & foot
    print("computing vesselness surface (label-free) ...", flush=True)
    surf_path = paths.DATA / "prepared/s20_vesselness.npy"
    surf_path.parent.mkdir(parents=True, exist_ok=True)
    V = vesselness.frangi_vesselness(step, lidar_valid)
    np.save(surf_path, V)
    ridge_lane = oof_detector.ridge_nms(V, lidar_valid, sigma=1.0)
    print(f"V done {time.time()-t0:.0f}s; ridge px={int(ridge_lane.sum()):,}; "
          f"V>0 px={int((V > 0).sum()):,}", flush=True)

    sys_grid, n_sys = losfo.fault_systems(labels, losfo.DEFAULT_DILATE_PX)
    tab = losfo.system_table(sys_grid, n_sys, foot)
    print(f"catalogue {int(labels.sum()):,} px in {n_sys} systems", flush=True)

    # ---- Canary on seed-340 cells (before any DTI) ----
    hold340 = losfo.assign_systems_to_folds(tab, fold, 4, seed=340)
    rng = np.random.default_rng(340)
    pos_v, pos_s, neg_v, neg_s = [], [], [], []
    for f in range(4):
        sp = losfo.build_losfo_split(labels, sys_grid, hold340, fold, f, 340,
                                     holdout.FOLD_NAMES, losfo.DEFAULT_BUFFER_PX)
        if not sp.hidden.any():
            continue
        active = sp.fold_mask & ~sp.known & foot
        hid = sp.hidden & active
        bg = active & ~sp.hidden
        pos_v.append(V[hid])
        pos_s.append(step[hid])
        by, bx = np.nonzero(bg)
        take = rng.choice(len(by), size=min(len(by), 125_000), replace=False)
        neg_v.append(V[by[take], bx[take]])
        neg_s.append(step[by[take], bx[take]])
    y = np.r_[np.ones(sum(len(a) for a in pos_v)), np.zeros(sum(len(a) for a in neg_v))]
    auc_v = float(roc_auc_score(y, np.r_[*pos_v, *neg_v].astype(np.float64)))
    auc_s = float(roc_auc_score(y, np.r_[*pos_s, *neg_s].astype(np.float64)))
    canary = {"seed": 340, "n_pos": int(y.sum()), "n_neg_sampled": int((y == 0).sum()),
              "auc_vesselness_alone": auc_v, "auc_step_max_alone": auc_s,
              "leakage_stop_above": 0.90, "pass": bool(auc_v <= 0.90 and auc_s <= 0.90)}
    print(f"canary: AUC(V)={auc_v:.4f} AUC(step)={auc_s:.4f} pass={canary['pass']}", flush=True)

    # ---- Pre-placement uniqueness (surface vs registry) ----
    rng20 = np.random.default_rng(20)
    foot_idx = np.flatnonzero(foot.ravel())
    sample = np.sort(rng20.choice(foot_idx, size=400_000, replace=False))
    v_s = V.ravel()[sample].astype(np.float64)
    registry_paths = {p.name: p for p in sorted((ROOT / "docs/downloads").glob("*-nan.tif"))}
    registry_paths.update({k: v for k, v in FORENSIC_EXTRA.items() if v.is_file()})
    surf_corr = {}
    for name, p in registry_paths.items():
        with rasterio.open(p) as s:
            a = s.read(1)
        ref = (np.isfinite(a) & (a > 0)).ravel()[sample].astype(np.float64)
        surf_corr[name] = float(spearmanr(v_s, ref).statistic) if ref.sum() else 0.0
    worst_name = max(surf_corr, key=lambda k: abs(surf_corr[k])) if surf_corr else None
    preplacement = {"n_registry_rasters": len(surf_corr), "sample_px": 400_000, "rng": 20,
                    "worst_raster": worst_name,
                    "worst_abs_spearman": abs(surf_corr[worst_name]) if worst_name else None,
                    "threshold_stop_above": 0.90,
                    "pass": bool(worst_name is not None and abs(surf_corr[worst_name]) <= 0.90),
                    "per_raster": surf_corr}
    print(f"pre-placement: worst |rho|={preplacement['worst_abs_spearman']:.4f} vs {worst_name} "
          f"pass={preplacement['pass']}", flush=True)

    if not canary["pass"] or not preplacement["pass"]:
        out = {"schema": 1, "session": "S20 Experiment 2", "status": "STOPPED at canary/pre-placement",
               "canary": canary, "preplacement": preplacement, "holdout": None}
        (ROOT / "evidence/s20v_holdout.json").write_text(json.dumps(out, indent=2) + "\n")
        print("STOPPED before DTI per protocol.")
        return 0

    # ---- LOSFO gate ----
    cells, unique_hidden = [], np.zeros(foot.shape, bool)
    for seed in SEEDS:
        hold = losfo.assign_systems_to_folds(tab, fold, 4, seed=seed)
        masked = losfo.masked_labels(labels, sys_grid, hold, losfo.DEFAULT_BUFFER_PX)
        print(f"seed {seed}: training LOSFO control on masked labels ({int(masked.sum()):,} px) ...",
              flush=True)
        prob = oof_detector.fit_predict_oof_probabilities(foot, masked, fold)
        ridge_ctrl = oof_detector.ridge_nms(prob, foot, sigma=1.0)
        print(f"seed {seed}: control ready {time.time()-t0:.0f}s", flush=True)
        for f in range(4):
            sp = losfo.build_losfo_split(labels, sys_grid, hold, fold, f, seed,
                                         holdout.FOLD_NAMES, losfo.DEFAULT_BUFFER_PX)
            if not sp.hidden.any():
                continue
            unique_hidden |= sp.hidden
            sl = holdout.crop(None, sp.fold_mask)
            fm, hidden, known_c = sp.fold_mask[sl], sp.hidden[sl], sp.known[sl]
            active = fm & ~known_c
            d_vis = distance_transform_edt(~sp.known)[sl]
            k = int(round(oof_detector.PRE_THIN_FRAC * int(fm.sum())))
            lane = emit(V[sl], ridge_lane[sl], active, d_vis, k)
            ctrl = emit(prob[sl], ridge_ctrl[sl], active, d_vis, k)
            lane, ctrl, dl, dc = match_n(lane, V[sl], ctrl, prob[sl])
            assert not (lane & known_c).any() and not (ctrl & known_c).any()
            rl, rc = score_cell(lane, hidden, active), score_cell(ctrl, hidden, active)
            cells.append({"seed": seed, "fold": holdout.FOLD_NAMES[f],
                          "min_dist_hidden_to_known_px": (None if not np.isfinite(sp.min_dist_hidden_to_known)
                                                          else float(sp.min_dist_hidden_to_known)),
                          "matched_n_dropped_lane": dl, "matched_n_dropped_control": dc,
                          "lane": rl, "control": rc, "delta_dti": rl["dti"] - rc["dti"]})
            print(f"  seed{seed} {holdout.FOLD_NAMES[f]}: lane {rl['dti']:.5f} ctrl {rc['dti']:.5f} "
                  f"d={rl['dti']-rc['dti']:+.5f} N={rl['n_emitted']} T={rl['n_truth']}", flush=True)

    def pooled(arm):
        tp = sum(c[arm]["TPw"] for c in cells)
        fp = sum(c[arm]["FPw"] for c in cells)
        fn = sum(c[arm]["FNw"] for c in cells)
        return {"TPw": tp, "FPw": fp, "FNw": fn, "dti": tp / (tp + 0.2 * fp + 0.8 * fn + 1e-7),
                "n_emitted": sum(c[arm]["n_emitted"] for c in cells),
                "n_truth": sum(c[arm]["n_truth"] for c in cells)}
    deltas = np.array([c["delta_dti"] for c in cells])
    brng = np.random.default_rng(20261026)
    boots = np.array([deltas[brng.integers(0, len(deltas), len(deltas))].mean() for _ in range(10_000)])
    gate = {"G1_pooled_delta_gt0": bool(pooled("lane")["dti"] - pooled("control")["dti"] > 0),
            "G2_paired_ci_lower_gt0": bool(float(np.percentile(boots, 2.5)) > 0)}
    out = {"schema": 1, "session": "S20 Experiment 2", "label": "HOLDOUT-DTI",
           "evaluator": EVALUATOR, "seeds": list(SEEDS), "cells": cells,
           "pooled_lane": pooled("lane"), "pooled_control": pooled("control"),
           "pooled_delta_dti": pooled("lane")["dti"] - pooled("control")["dti"],
           "paired_mean_delta": float(deltas.mean()),
           "paired_ci95_bootstrap_cells": [float(np.percentile(boots, 2.5)), float(np.percentile(boots, 97.5))],
           "withheld_positives_pooled": int(sum(c["lane"]["n_truth"] for c in cells)),
           "withheld_positives_unique": int(unique_hidden.sum()),
           "cells_lane_wins": int((deltas > 0).sum()), "n_cells": len(cells),
           "canary": canary, "preplacement": preplacement, "gate": gate,
           "gate_pass": bool(all(gate.values()) and canary["pass"] and preplacement["pass"]),
           "surface_cache": str(surf_path), "seconds": round(time.time() - t0, 1),
           "caveats": ["LOSFO truth is still mapped faults: absolute DTI is an upper bound vs genuinely unmapped faults.",
                       "12 cells / 4 geographic blocks: bootstrap CI is optimistic about spatial independence.",
                       "HOLDOUT-DTI is a local recovery proxy, never an organizer score."]}
    (ROOT / "evidence/s20v_holdout.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"pooled_lane_dti": out["pooled_lane"]["dti"], "pooled_control_dti": out["pooled_control"]["dti"],
                      "pooled_delta": out["pooled_delta_dti"], "paired_ci95": out["paired_ci95_bootstrap_cells"],
                      "gate_pass": out["gate_pass"], "seconds": out["seconds"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
