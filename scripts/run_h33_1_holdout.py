#!/usr/bin/env python3
"""Frozen holdout run for H33-1: kinematic reactivation favourability gate.

Implements `knowledge/19_preregistration_H33-1.md` exactly as registered there. Seeds 200-209,
one use. The six promotion criteria in section 3 are evaluated numerically and written to the
evidence JSON; this script never retunes, never widens a radius and never picks a variant after
seeing the result.

Arms, all four evaluated on every cell from one shared OOF fit:
  base_oof_d28     the H32-1 holdout-best base (unchanged control)
  h33_1_prune_p10  remove the bottom decile of *scored* base dots by `fav`   <- primary
  h33_1_prune_p05  remove the bottom 5 % (dose check)
  control_top_p10  remove the *top* decile by `fav` (direction control)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import grid, holdout, kinematics, layers, metric, oof_detector, paths  # noqa: E402

GEOD_BAND = "geod_2ndinv"
VARIANTS = ["base_oof_d28", "h33_1_prune_p10", "h33_1_prune_p05", "control_top_p10"]
PRIMARY = "h33_1_prune_p10"
DIRECTION_CONTROL = "control_top_p10"


def eval_set(pred: np.ndarray, g: np.ndarray, active: np.ndarray, k_pt: np.ndarray):
    p = pred & active
    n_g = int(g.sum())
    if not p.any() or n_g == 0:
        fp = float((1.0 - k_pt[p]).sum()) if p.any() else 0.0
        return 0.0, fp, 0.0, int(p.sum())
    tp = float(metric.kernel_from_distance(distance_transform_edt(~p)[g]).sum())
    fp = float((1.0 - k_pt[p]).sum())
    dti = tp / (tp + 0.2 * fp + 0.8 * (n_g - tp) + 1e-7)
    return tp, fp, dti, int(p.sum())


def prune_by_quantile(base: np.ndarray, fav: np.ndarray, frac: float, from_top: bool) -> np.ndarray:
    """Drop the extreme `frac` of *scored* dots; neutral (NaN) dots are never touched.

    All indexing is done in flat space on purpose: `base` is 2-D, so a flat index array cannot be
    used to subscript it directly (that raises, or worse silently broadcasts).
    """
    out = base.copy()
    fav_flat = np.asarray(fav, float).ravel()
    idx = np.flatnonzero(base.ravel())
    scored = idx[np.isfinite(fav_flat[idx])]
    if len(scored) == 0:
        return out
    order = np.argsort(fav_flat[scored], kind="stable")
    if from_top:
        order = order[::-1]
    cut = int(np.floor(len(scored) * frac))
    if cut:
        out.reshape(-1)[scored[order[:cut]]] = False
    return out


def dot_strike(dot_rc: np.ndarray, strike_map: np.ndarray) -> np.ndarray:
    """Strike of the nearest ridge pixel within STRIKE_SEARCH_PX, else NaN."""
    rows = dot_rc[:, 0].astype(int)
    cols = dot_rc[:, 1].astype(int)
    out = strike_map[rows, cols].astype(float)
    missing = ~np.isfinite(out)
    if missing.any():
        on_ridge = np.flatnonzero(np.isfinite(strike_map).ravel())
        if len(on_ridge):
            ry, rx = np.unravel_index(on_ridge, strike_map.shape)
            tree = cKDTree(np.column_stack([rx, ry]).astype(float))
            d, j = tree.query(np.column_stack([cols[missing], rows[missing]]).astype(float),
                              distance_upper_bound=kinematics.STRIKE_SEARCH_PX)
            hit = np.isfinite(d)
            filled = np.full(int(missing.sum()), np.nan)
            filled[hit] = strike_map[ry[j[hit]], rx[j[hit]]]
            out[missing] = filled
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="200-209")
    ap.add_argument("--clip", default=str(paths.DOCS / "data" / "sb_slip_tendency_in_footprint.json"))
    ap.add_argument("--prereg", default=str(paths.REPO / "knowledge" / "19_preregistration_H33-1.md"))
    ap.add_argument("--out", default=str(paths.EVIDENCE / "h33_1_holdout.json"))
    ap.add_argument("--limit-seeds", type=int, default=0, help="smoke-test cap; burns nothing")
    args = ap.parse_args()
    a, _, b = args.seeds.partition("-")
    seeds = list(range(int(a), int(b) + 1)) if b else [int(a)]
    if args.limit_seeds:
        seeds = seeds[: args.limit_seeds]

    t0 = time.time()
    prereg_sha = hashlib.sha256(Path(args.prereg).read_bytes()).hexdigest()
    clip_bytes = Path(args.clip).read_bytes()
    clip_sha = hashlib.sha256(clip_bytes).hexdigest()

    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)

    seg = kinematics.load_segments(args.clip)
    schema = json.loads(clip_bytes)["schema"]
    fields = sorted(next(iter(schema["layers"].values()))["attribute_fields"])
    has_ts_td = "TS" in fields and "TD" in fields
    print(f"clip: {seg['n_segments']:,} segments, {len(seg['trace_colrow']):,} trace pts, "
          f"TS/TD present={has_ts_td}, sha256={clip_sha[:16]}...", flush=True)
    if not has_ts_td:
        print("FATAL: the clip schema does not list slip/dilation-tendency fields; precondition unmet",
              file=sys.stderr)
        return 2

    geod = layers.load_training()[GEOD_BAND].astype(float)
    geod = np.where(np.isfinite(geod), geod, np.nan)
    geod_ref = geod[foot & np.isfinite(geod)]
    print(f"{GEOD_BAND} footprint reference: n={len(geod_ref):,} "
          f"p1={np.percentile(geod_ref,1):.3e} med={np.median(geod_ref):.3e} "
          f"p99={np.percentile(geod_ref,99):.3e}", flush=True)

    print("Training 4-fold spatial-CV HistGradientBoostingClassifier (600 m buffer)...", flush=True)
    oof_prob = oof_detector.fit_predict_oof_probabilities(foot, labels, fold)
    ridge_all = oof_detector.ridge_nms(oof_prob, foot, sigma=1.0)
    strike_map = oof_detector.ridge_strike_degrees(oof_prob, foot, sigma=1.0)
    print(f"OOF fit done in {time.time()-t0:.0f}s (ridges={int(ridge_all.sum()):,}, "
          f"strikes={int(np.isfinite(strike_map).sum()):,})", flush=True)

    cells = []
    coverages = []
    for seed in seeds:
        for f in range(4):
            sp = holdout.make_split(labels, fold, f, seed)
            fm = sp.fold_mask
            sl = holdout.crop(None, fm)
            hid, kn, fmc = sp.hidden[sl], (sp.known & fm)[sl], fm[sl]
            g = hid & fmc & ~kn
            active = fmc & ~kn
            k_pt = metric.kernel_from_distance(distance_transform_edt(~g)) if g.any() else np.zeros_like(g, float)
            origin = (int(np.flatnonzero(fm.any(axis=1))[0]), int(np.flatnonzero(fm.any(axis=0))[0]))

            base = oof_detector.build_oof_dotted_base(
                oof_prob[sl], ridge_all[sl], fmc, kn,
                budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=2.8) & active

            # argwhere, NOT column_stack(flatnonzero(...)): the latter returns shape (1, 2) - a
            # single row of flat indices - which silently scores one dot instead of every dot.
            dot_rc = np.argwhere(base).astype(float)
            if len(dot_rc) != int(base.sum()):
                raise AssertionError(f"dot_rc {dot_rc.shape} does not match {int(base.sum())} dots")
            rows_i, cols_i = dot_rc[:, 0].astype(int), dot_rc[:, 1].astype(int)
            # the segment trace lives in FULL-grid pixel space; the cell is a crop of it
            dot_colrow = np.column_stack([cols_i + origin[1], rows_i + origin[0]]).astype(float)
            fav, cov = kinematics.favourability(
                dot_colrow, dot_strike(dot_rc, strike_map[sl]), seg,
                geod[sl][rows_i, cols_i], geod_ref)
            coverages.append(cov)
            # `fav` is a per-dot vector; scatter it back to the cell grid so the quantile prunes
            # pixels. Off-dot cells stay NaN and are inert because every arm intersects `base`.
            fav_grid = np.full(base.shape, np.nan)
            fav_grid[dot_rc[:, 0].astype(int), dot_rc[:, 1].astype(int)] = fav

            v_sets = {
                "base_oof_d28": base,
                PRIMARY: prune_by_quantile(base, fav_grid, 0.10, from_top=False),
                "h33_1_prune_p05": prune_by_quantile(base, fav_grid, 0.05, from_top=False),
                DIRECTION_CONTROL: prune_by_quantile(base, fav_grid, 0.10, from_top=True),
            }
            row = {"seed": seed, "fold": sp.name, "n_truth": int(g.sum()), "fav_coverage": cov}
            for vn, mask in v_sets.items():
                tp, fp, dti, n_px = eval_set(mask, g, active, k_pt)
                row[vn] = {"tp": tp, "fp": fp, "dti": dti, "dots": n_px}
            cells.append(row)
        done = [c for c in cells if c["seed"] == seed]
        print(f"seed {seed} done (t={time.time()-t0:.0f}s): "
              f"base={np.mean([c['base_oof_d28']['dti'] for c in done]):.5f} "
              f"p10={np.mean([c[PRIMARY]['dti'] for c in done]):.5f} "
              f"p05={np.mean([c['h33_1_prune_p05']['dti'] for c in done]):.5f} "
              f"top10={np.mean([c[DIRECTION_CONTROL]['dti'] for c in done]):.5f} "
              f"cov={np.mean([c['fav_coverage'] for c in done]):.3f}", flush=True)

    base_mean_dti = float(np.mean([c["base_oof_d28"]["dti"] for c in cells]))
    m_oof = metric.inclusion_threshold(base_mean_dti)

    summary = {}
    for vn in VARIANTS[1:]:
        gains_by_seed = [float(np.mean([c[vn]["dti"] - c["base_oof_d28"]["dti"]
                                        for c in cells if c["seed"] == s])) for s in seeds]
        gains_by_fold = {fn: float(np.mean([c[vn]["dti"] - c["base_oof_d28"]["dti"]
                                            for c in cells if c["fold"] == fn]))
                         for fn in holdout.FOLD_NAMES}
        dtp = sum(c[vn]["tp"] - c["base_oof_d28"]["tp"] for c in cells)
        dfp = sum(c[vn]["fp"] - c["base_oof_d28"]["fp"] for c in cells)
        eff = (dtp / dfp) if dfp > 0 else ((-dtp) / (-dfp) if dfp < 0 else 0.0)
        summary[vn] = {
            "mean_dti": float(base_mean_dti + np.mean(gains_by_seed)),
            "mean_dti_gain": float(np.mean(gains_by_seed)),
            "min_seed_gain": float(np.min(gains_by_seed)),
            "max_seed_gain": float(np.max(gains_by_seed)),
            "seeds_won": int(sum(gx > 0 for gx in gains_by_seed)),
            "n_seeds": len(seeds),
            "fold_gains": gains_by_fold,
            "folds_improved": int(sum(v > 0 for v in gains_by_fold.values())),
            "delta_dots_per_seed": sum(c[vn]["dots"] - c["base_oof_d28"]["dots"] for c in cells) / len(seeds),
            "removed_credit_per_removed_fp": float(eff),
        }

    p, c = summary[PRIMARY], summary[DIRECTION_CONTROL]
    cov_mean = float(np.mean(coverages)) if coverages else 0.0
    criteria = {
        "1_mean_dti_gain_ge_0.0010": {"value": p["mean_dti_gain"], "threshold": 0.0010,
                                      "passed": bool(p["mean_dti_gain"] >= 0.0010)},
        "2_folds_improved_ge_3_of_4": {"value": p["folds_improved"], "threshold": 3,
                                       "passed": bool(p["folds_improved"] >= 3)},
        "3_seeds_won_ge_8_of_10": {"value": p["seeds_won"], "threshold": 8,
                                   "passed": bool(p["seeds_won"] >= 8)},
        "4_removed_eff_below_inclusion_threshold": {
            "value": p["removed_credit_per_removed_fp"], "threshold": m_oof,
            "passed": bool(p["removed_credit_per_removed_fp"] < m_oof)},
        "5_direction_control_worse": {
            "value": c["removed_credit_per_removed_fp"],
            "threshold": p["removed_credit_per_removed_fp"],
            "passed": bool(c["removed_credit_per_removed_fp"] >= p["removed_credit_per_removed_fp"])},
        "6_fav_coverage_ge_0.60": {"value": cov_mean, "threshold": 0.60,
                                   "passed": bool(cov_mean >= 0.60)},
    }
    gate_passed = all(v["passed"] for v in criteria.values())

    out = {
        "hypothesis": "H33-1: kinematic reactivation favourability gate (slip/dilation tendency x strain)",
        "preregistration": "knowledge/19_preregistration_H33-1.md",
        "preregistration_sha256": prereg_sha,
        "data_precondition": {
            "clip": str(args.clip), "sha256": clip_sha,
            "n_segments": int(seg["n_segments"]), "n_trace_points": int(len(seg["trace_colrow"])),
            "attribute_fields": fields,
            "slip_and_dilation_tendency_fields_present": has_ts_td,
        },
        "seeds": seeds, "folds": list(holdout.FOLD_NAMES),
        "base_oof_d28_mean_dti": base_mean_dti,
        "inclusion_threshold_oof": m_oof,
        "fav_coverage_mean": cov_mean,
        "fav_coverage_min": float(np.min(coverages)) if coverages else 0.0,
        "variants": summary,
        "promotion_criteria": criteria,
        "gate_passed": gate_passed,
        "seconds": time.time() - t0,
        "cells": cells,
    }
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: v for k, v in out.items() if k != "cells"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
