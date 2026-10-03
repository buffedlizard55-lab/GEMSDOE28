#!/usr/bin/env python3
"""Spatially-blocked 4-fold out-of-fold holdout validation for H32-2:
Shallow-Over-Deep Magnetic Gradient De-Screening (Intrusive-Pluton Margin Suppression) at d=2.8.

Frozen protocol: knowledge/16_preregistration_H32-2.md (SHA-256 recorded in the evidence JSON).

Variants per cell (quantiles computed label-free over that cell's base d=2.8 dots):
  - base_oof_d28:          control, identical to the H32-1 base.
  - h32_2_p05_d28:         remove bottom 5 % of base dots by R (deepest magnetic sources).
  - h32_2_p10_d28:         remove bottom 10 % of base dots by R (PRIMARY).
  - control_top_p10_d28:   remove TOP 10 % of base dots by R (direction control).

R = (tmi_hg / P99(tmi_hg)) / (|grad H(TMI_up150 u8)| / P99(|grad H(TMI_up150)|) + 1e-3),
a label-free rank proxy for magnetic-source shallowness via upward-continuation attenuation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import grid, holdout, metric, oof_detector, paths  # noqa: E402

PREREG = paths.REPO / "knowledge" / "16_preregistration_H32-2.md"
EPS = 1e-3


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


def build_r_shallow(shape: tuple[int, int]) -> tuple[np.ndarray, dict]:
    """Label-free upward-continuation attenuation ratio R on the full grid."""
    def band_index(descriptions, key: str) -> int:
        for i, desc in enumerate(descriptions):
            name = (desc or "").split(" - ")[0].strip()
            if name == key:
                return i
        raise ValueError(f"band {key!r} not found in {descriptions}")

    with rasterio.open(paths.TRAINING) as ds:
        tmi_hg = ds.read(band_index(ds.descriptions, "tmi_hg") + 1).astype(np.float64)
    with rasterio.open(paths.EXTENSIONS) as ds:
        up150 = ds.read(band_index(ds.descriptions, "TMI_up150") + 1).astype(np.float64)
    g150y, g150x = np.gradient(up150)
    hg150 = np.hypot(g150y, g150x)

    def p99(a: np.ndarray) -> float:
        # Repo-wide null convention: |value| >= 1e30 is the declared nodata sentinel
        # (matches the frozen validity rule in knowledge/14_preregistration_H32-1.md).
        v = a[np.isfinite(a) & (np.abs(a) < 1e30) & (a > 0)]
        return float(np.percentile(v, 99)) if v.size else 1.0

    g1_raw = np.abs(tmi_hg)
    g1 = np.where(g1_raw < 1e30, g1_raw / max(p99(g1_raw), 1e-12), 0.0)
    g150 = hg150 / max(p99(hg150), 1e-12)
    r = g1 / (g150 + EPS)
    r = np.where(g1_raw < 1e30, r, 0.0)  # outside valid mask: neutral, never pruned nor protected
    stats = {
        "tmi_hg_p99": p99(np.abs(tmi_hg)),
        "hg_up150_p99": p99(hg150),
        "tmi_hg_valid_frac": float((np.abs(tmi_hg) < 1e30).mean()),
        "r_finite_frac": float(np.isfinite(r).mean()),
        "r_p10": float(np.nanpercentile(r, 10)),
        "r_p50": float(np.nanpercentile(r, 50)),
        "r_p90": float(np.nanpercentile(r, 90)),
    }
    r = np.where(np.isfinite(r), r, np.inf)  # non-finite -> treated as maximally shallow (never pruned)
    return r, stats


def prune_low_r(base: np.ndarray, r: np.ndarray, frac: float) -> np.ndarray:
    ys, xs = np.nonzero(base)
    if ys.size == 0 or frac <= 0:
        return base
    vals = r[ys, xs]
    vals = np.where(np.isfinite(vals), vals, np.inf)
    cut = np.quantile(vals, frac)
    keep = ~(base & (r <= cut))
    return keep & base | (base & np.isinf(r))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="190-199")
    ap.add_argument("--out", default=str(paths.EVIDENCE / "h32_2_holdout.json"))
    args = ap.parse_args()
    a, _, b = args.seeds.partition("-")
    seeds = list(range(int(a), int(b) + 1)) if b else [int(a)]

    t0 = time.time()
    prereg_sha = hashlib.sha256(PREREG.read_bytes()).hexdigest()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)
    r_field, r_stats = build_r_shallow(labels.shape)
    print(f"R field built in {time.time()-t0:.1f}s (finite frac={r_stats['r_finite_frac']:.4f})", flush=True)

    print("Training 4-fold spatial-CV HistGradientBoostingClassifier (600 m buffer)...", flush=True)
    oof_prob = oof_detector.fit_predict_oof_probabilities(foot, labels, fold)
    ridge_all = oof_detector.ridge_nms(oof_prob, foot, sigma=1.0)
    print(f"OOF probabilities & ridges computed in {time.time()-t0:.1f}s", flush=True)

    variants = ["base_oof_d28", "h32_2_p05_d28", "h32_2_p10_d28", "control_top_p10_d28"]
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

            base_c = oof_detector.build_oof_dotted_base(
                oof_prob[sl], ridge_all[sl], fmc, kn, budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=2.8
            ) & active
            r_sl = r_field[sl]

            v_sets = {
                "base_oof_d28": base_c,
                "h32_2_p05_d28": prune_low_r(base_c, r_sl, 0.05),
                "h32_2_p10_d28": prune_low_r(base_c, r_sl, 0.10),
                "control_top_p10_d28": base_c & ~_top_mask(base_c, r_sl, 0.10),
            }
            row = {"seed": seed, "fold": sp.name, "n_truth": int(g.sum())}
            for vn, s_mask in v_sets.items():
                tp, fp, dti, n_px = eval_set(s_mask, g, active, k_pt)
                row[vn] = {"tp": tp, "fp": fp, "dti": dti, "dots": n_px}
            cells.append(row)
        print(
            f"seed {seed} done (t={time.time()-t0:.0f}s): "
            f"base={np.mean([c['base_oof_d28']['dti'] for c in cells if c['seed']==seed]):.5f} "
            f"p05={np.mean([c['h32_2_p05_d28']['dti'] for c in cells if c['seed']==seed]):.5f} "
            f"p10={np.mean([c['h32_2_p10_d28']['dti'] for c in cells if c['seed']==seed]):.5f} "
            f"top10={np.mean([c['control_top_p10_d28']['dti'] for c in cells if c['seed']==seed]):.5f}",
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
            "seeds_won": int(sum(gg > 0 for gg in gains_by_seed)),
            "n_seeds": len(seeds),
            "fold_gains": gains_by_fold,
            "folds_improved": int(sum(v > 0 for v in gains_by_fold.values())),
            "delta_dots_per_seed": float(d_dots),
            "removed_credit_per_removed_fp": float(eff),
        }

    # Full-footprint audit on the actual 0.2600 d=2.8 raster
    with rasterio.open(paths.DOTTED_D2_8) as s:
        d28_full = (np.nan_to_num(s.read(1)) > 0) & foot & ~labels
    r_dots = r_field[d28_full]
    r_dots_fin = r_dots[np.isfinite(r_dots)]
    full_audit = {
        "d28_base_px": int(d28_full.sum()),
        "d28_px_with_finite_r": int(r_dots_fin.size),
        "d28_p05_pruned_px": int((r_dots <= np.quantile(r_dots_fin, 0.05)).sum()) if r_dots_fin.size else 0,
        "d28_p10_pruned_px": int((r_dots <= np.quantile(r_dots_fin, 0.10)).sum()) if r_dots_fin.size else 0,
        "d28_dot_r_p10": float(np.percentile(r_dots_fin, 10)) if r_dots_fin.size else None,
        "d28_dot_r_p50": float(np.percentile(r_dots_fin, 50)) if r_dots_fin.size else None,
        "d28_dot_r_p90": float(np.percentile(r_dots_fin, 90)) if r_dots_fin.size else None,
    }

    p = summary["h32_2_p10_d28"]
    gate_passed = bool(
        p["mean_dti_gain"] >= 0.0010
        and p["folds_improved"] >= 3
        and p["seeds_won"] >= 8
        and p["removed_credit_per_removed_fp"] < m_oof
        and summary["control_top_p10_d28"]["removed_credit_per_removed_fp"] >= p["removed_credit_per_removed_fp"]
        and r_stats["r_finite_frac"] >= 0.95
    )

    out = {
        "hypothesis": "H32-2: Shallow-over-deep magnetic gradient de-screening (upward-continuation attenuation ratio) at d=2.8",
        "preregistration": "knowledge/16_preregistration_H32-2.md",
        "preregistration_sha256": prereg_sha,
        "seeds": seeds,
        "base_oof_d28_mean_dti": base_mean_dti,
        "base_oof_d28_dots_per_seed": float(np.mean([sum(c["base_oof_d28"]["dots"] for c in cells if c["seed"] == s) for s in seeds])),
        "inclusion_threshold_oof": m_oof,
        "inclusion_threshold_live_0_2600": m_live_0260,
        "r_field_stats": r_stats,
        "variants": summary,
        "full_footprint_d28_audit": full_audit,
        "gate_passed": gate_passed,
        "seconds": time.time() - t0,
    }
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0


def _top_mask(base: np.ndarray, r: np.ndarray, frac: float) -> np.ndarray:
    ys, xs = np.nonzero(base)
    mask = np.zeros_like(base, bool)
    if ys.size == 0 or frac <= 0:
        return mask
    vals = r[ys, xs]
    vals = np.where(np.isfinite(vals), vals, -np.inf)
    cut = np.quantile(vals, 1.0 - frac)
    top = (vals >= cut) & np.isfinite(r[ys, xs])
    mask[ys[top], xs[top]] = True
    return mask


if __name__ == "__main__":
    raise SystemExit(main())
