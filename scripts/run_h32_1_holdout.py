#!/usr/bin/env python3
"""Spatially-blocked 4-fold out-of-fold holdout validation for H32-1:
Tip- & Euler-Depth-Cluster-Protected Mid-Segment Flank-Shadow De-Jittering at d=2.8.

Evaluates on fresh untouched seeds 170-179 across the 4 spatial quadrant folds (NW, NE_LidarGapHeavy,
SW, SE) with 600 m spatial buffer collar:
  - base_oof_d28: 4-fold OOF HistGradientBoostingClassifier + ridge NMS + dot_thin(d=2.8)
  - h32_1_post_d28: base_oof_d28 with mid-segment lateral flank-shadow pixels removed
                    (d_known <= 1.0 & d_end > 3.0 & cat_nbrs >= 2 & d_euler > 3.0)
  - h32_1_pre_d28:  dot_thin(ridge & ~known & ~flank_mid, d=2.8) (pre-thinning de-jitter)
  - h27_4_blind_r1_d28: blind removal of all d_known <= 1.0 pixels (unprotected comparator)
  - pruned_tip_or_euler_only_d28: diagnostic control removing ONLY the protected tip/Euler pixels
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import convolve, distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import grid, holdout, metric, oof_detector, paths, thinning  # noqa: E402


def eval_set(pred: np.ndarray, g: np.ndarray, active: np.ndarray, k_pt: np.ndarray) -> tuple[float, float, float, int]:
    p = pred & active
    n_g = int(g.sum())
    if not p.any() or n_g == 0:
        fp = float((1.0 - k_pt[p]).sum()) if p.any() else 0.0
        return 0.0, fp, 0.0, int(p.sum())
    tp = float(metric.kernel_from_distance(distance_transform_edt(~p)[g]).sum())
    fp = float((1.0 - k_pt[p]).sum())
    dti = tp / (tp + 0.2 * fp + 0.8 * (n_g - tp) + 1e-7)
    return tp, fp, dti, int(p.sum())


def load_euler_halo(shape: tuple[int, int], radius_px: float = 3.0) -> np.ndarray:
    df_eu = pd.read_csv(paths.EVIDENCE / "h31_1_euler_clusters.csv")
    eu_mask = np.zeros(shape, bool)
    rr = np.clip(np.round(df_eu["row"].to_numpy()).astype(int), 0, shape[0] - 1)
    cc = np.clip(np.round(df_eu["col"].to_numpy()).astype(int), 0, shape[1] - 1)
    eu_mask[rr, cc] = True
    return distance_transform_edt(~eu_mask) <= radius_px


def build_flank_mid_mask(known: np.ndarray, eu_halo: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (flank_mid, tip_or_euler) Partition of the d_known <= 1.0 (100 m) ring."""
    if not known.any():
        z = np.zeros_like(known, bool)
        return z, z
    d_kn = distance_transform_edt(~known)
    kn_deg = convolve(known.astype(int), np.ones((3, 3), int), mode="constant") - 1
    end_mask = known & (kn_deg <= 1)
    d_end = distance_transform_edt(~end_mask) if end_mask.any() else np.full(known.shape, np.inf)
    kn_nbrs = convolve(known.astype(int), np.ones((3, 3), int), mode="constant")
    r1 = (d_kn > 0.0) & (d_kn <= 1.0)
    flank_mid = r1 & (d_end > 3.0) & (kn_nbrs >= 2) & ~eu_halo
    tip_or_euler = r1 & ~flank_mid
    return flank_mid, tip_or_euler


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="180-189")
    ap.add_argument("--out", default=str(paths.EVIDENCE / "h32_1_holdout.json"))
    args = ap.parse_args()
    a, _, b = args.seeds.partition("-")
    seeds = list(range(int(a), int(b) + 1)) if b else [int(a)]

    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)
    eu_halo = load_euler_halo(labels.shape, radius_px=3.0)

    print("Training 4-fold spatial-CV HistGradientBoostingClassifier (600 m buffer)...", flush=True)
    oof_prob = oof_detector.fit_predict_oof_probabilities(foot, labels, fold)
    ridge_all = oof_detector.ridge_nms(oof_prob, foot, sigma=1.0)
    print(f"OOF probabilities & ridges computed in {time.time()-t0:.1f}s (total ridges={int(ridge_all.sum()):,})", flush=True)

    variants = [
        "base_oof_d28",
        "h32_1_post_d28",
        "h32_1_pre_d28",
        "h27_4_blind_r1_d28",
        "control_prune_protected_only_d28",
    ]
    cells = []
    for seed in seeds:
        for f in range(4):
            sp = holdout.make_split(labels, fold, f, seed)
            fm = sp.fold_mask
            sl = holdout.crop(None, fm)
            hid, kn, fmc = sp.hidden[sl], (sp.known & fm)[sl], fm[sl]
            g = hid & fmc & ~kn
            active = fmc & ~kn
            k_pt = metric.kernel_from_distance(distance_transform_edt(~g)) if g.any() else np.zeros_like(g, float)

            flank_mid, tip_or_eu = build_flank_mid_mask(kn, eu_halo[sl])
            r1_all = flank_mid | tip_or_eu

            # Base OOF at d=2.8
            base_c = oof_detector.build_oof_dotted_base(
                oof_prob[sl], ridge_all[sl], fmc, kn, budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=2.8
            ) & active

            # Post-thinning H32-1 (remove only mid-segment flank shadow, keep tip/Euler pixels)
            h32_post = base_c & ~flank_mid

            # Pre-thinning H32-1 (suppress mid-segment flank shadow before dot_thin(2.8))
            h32_pre = oof_detector.build_oof_dotted_base(
                oof_prob[sl], ridge_all[sl] & ~flank_mid, fmc, kn,
                budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=2.8
            ) & active

            # Unprotected H27-4 blind r<=1 prune on d=2.8
            blind_r1 = base_c & ~r1_all

            # Diagnostic control: prune ONLY the protected tip/Euler pixels
            ctrl_prot = base_c & ~tip_or_eu

            v_sets = {
                "base_oof_d28": base_c,
                "h32_1_post_d28": h32_post,
                "h32_1_pre_d28": h32_pre,
                "h27_4_blind_r1_d28": blind_r1,
                "control_prune_protected_only_d28": ctrl_prot,
            }
            row = {"seed": seed, "fold": sp.name, "n_truth": int(g.sum())}
            for vn, s_mask in v_sets.items():
                tp, fp, dti, n_px = eval_set(s_mask, g, active, k_pt)
                row[vn] = {"tp": tp, "fp": fp, "dti": dti, "dots": n_px}
            cells.append(row)
        print(
            f"seed {seed} done (t={time.time()-t0:.0f}s): "
            f"base_d28={np.mean([c['base_oof_d28']['dti'] for c in cells if c['seed']==seed]):.5f} "
            f"h32_1_post={np.mean([c['h32_1_post_d28']['dti'] for c in cells if c['seed']==seed]):.5f} "
            f"h32_1_pre={np.mean([c['h32_1_pre_d28']['dti'] for c in cells if c['seed']==seed]):.5f} "
            f"blind_r1={np.mean([c['h27_4_blind_r1_d28']['dti'] for c in cells if c['seed']==seed]):.5f}",
            flush=True,
        )

    base_mean_dti = float(np.mean([c["base_oof_d28"]["dti"] for c in cells]))
    m_oof = metric.inclusion_threshold(base_mean_dti)
    m_live_0260 = metric.inclusion_threshold(0.2600)

    summary = {}
    for vn in variants[1:]:
        gains_by_seed = [
            float(np.mean([c[vn]["dti"] - c["base_oof_d28"]["dti"] for c in cells if c["seed"] == s]))
            for s in seeds
        ]
        gains_by_fold = {
            fn: float(np.mean([c[vn]["dti"] - c["base_oof_d28"]["dti"] for c in cells if c["fold"] == fn]))
            for fn in holdout.FOLD_NAMES
        }
        dtp = sum(c[vn]["tp"] - c["base_oof_d28"]["tp"] for c in cells)
        dfp = sum(c[vn]["fp"] - c["base_oof_d28"]["fp"] for c in cells)
        d_dots = sum(c[vn]["dots"] - c["base_oof_d28"]["dots"] for c in cells) / len(seeds)
        eff = (dtp / dfp) if dfp > 0 else ((-dtp) / (-dfp) if dfp < 0 else 0.0)
        summary[vn] = {
            "mean_dti": float(base_mean_dti + np.mean(gains_by_seed)),
            "mean_dti_gain": float(np.mean(gains_by_seed)),
            "min_seed_gain": float(np.min(gains_by_seed)),
            "max_seed_gain": float(np.max(gains_by_seed)),
            "seeds_won": int(sum(g > 0 for g in gains_by_seed)),
            "n_seeds": len(seeds),
            "fold_gains": gains_by_fold,
            "folds_improved": int(sum(v > 0 for v in gains_by_fold.values())),
            "delta_dots_per_seed": float(d_dots),
            "removed_credit_per_removed_fp": float(eff),
        }

    # Full-footprint audit on the actual 0.2600 d=2.8 raster
    import rasterio
    with rasterio.open(paths.DOTTED_D2_8) as s:
        d28_full = (np.nan_to_num(s.read(1)) > 0) & foot & ~labels
    with rasterio.open(paths.H19_5) as s:
        h19_full = (np.nan_to_num(s.read(1)) > 0) & foot & ~labels
    flank_mid_full, tip_or_eu_full = build_flank_mid_mask(labels, eu_halo)
    d28_h32_post = d28_full & ~flank_mid_full
    d28_h32_pre = thinning.dot_thin(h19_full & ~flank_mid_full, 2.8)

    gate_passed = bool(
        summary["h32_1_post_d28"]["mean_dti_gain"] >= 0.0010
        and summary["h32_1_post_d28"]["folds_improved"] == 4
        and summary["h32_1_post_d28"]["seeds_won"] == len(seeds)
        and summary["h32_1_post_d28"]["removed_credit_per_removed_fp"] < m_oof
        and summary["h32_1_post_d28"]["removed_credit_per_removed_fp"] < summary["control_prune_protected_only_d28"]["removed_credit_per_removed_fp"]
    )

    out = {
        "hypothesis": "H32-1: Tip- & Euler-Depth-Cluster-Protected Mid-Segment Flank-Shadow De-Jittering at d=2.8",
        "preregistration": "knowledge/13_current_ranked_hypotheses_2026-10-03.md",
        "seeds": seeds,
        "base_oof_d28_mean_dti": base_mean_dti,
        "base_oof_d28_dots_per_seed": float(np.mean([sum(c["base_oof_d28"]["dots"] for c in cells if c["seed"] == s) for s in seeds])),
        "inclusion_threshold_oof": m_oof,
        "inclusion_threshold_live_0_2600": m_live_0260,
        "variants": summary,
        "full_footprint_d28_audit": {
            "d28_base_px": int(d28_full.sum()),
            "d28_r1_total_px": int((d28_full & (flank_mid_full | tip_or_eu_full)).sum()),
            "d28_mid_segment_flank_shadow_pruned_px": int((d28_full & flank_mid_full).sum()),
            "d28_protected_tip_or_euler_kept_px": int((d28_full & tip_or_eu_full).sum()),
            "d28_h32_1_post_px": int(d28_h32_post.sum()),
            "d28_h32_1_pre_px": int(d28_h32_pre.sum()),
        },
        "gate_passed": gate_passed,
        "seconds": time.time() - t0,
    }
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
