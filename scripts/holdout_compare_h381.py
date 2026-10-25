#!/usr/bin/env python3
"""Experiment 3 verification for the regenerated H38-1 unique submission.

Independent re-reads of docs/downloads/gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif:
  1. Format verification via src/gems27/submission.verify_geotiff
     (no NaN inside footprint; values in [0,1]; CRS/shape/transform == template).
  2. Paired 4-quadrant component-hiding holdout (src/gems27/holdout.py) of H38-1 vs H36-1 base:
     pooled HOLDOUT-DTI (alpha=0.2, beta=0.8, 300 m triangular kernel), per-fold deltas,
     paired 95% CI, credit per added dot.
  3. Uniqueness vs registry rasters present locally:
     dots on catalogue (=0 required), d_cat >= 3 px build rule, dot overlap with H36-1 base,
     Spearman surface similarity + 3-px dot overlap vs the H37-1 dense probe raster
     (gems28-h37-1-probe-union-pool-r1-...-52a13184267e-nan.tif).
Outputs evidence/holdout_compare_gems28-h38-1_vs_h36-1_2026-10-25.json.
This is HOLDOUT-DTI (a local catalogue-internal proxy), never an organizer score.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import grid, holdout, metric, submission  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DL = ROOT / "docs" / "downloads"
DATA = ROOT / "data"
EVID = ROOT / "evidence"

H36_1 = DL / "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif"
H38_1 = DL / "gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif"
PROBE = DL / "gems28-h37-1-probe-union-pool-r1-20261003-52a13184267e-nan.tif"
LABELS = DATA / "labels.tif"
TEMPLATE = DATA / "sample_submission.tif"


def load_pred(path: Path) -> np.ndarray:
    with rasterio.open(path) as s:
        a = s.read(1).astype(np.float32)
    return np.where(np.isfinite(a), a, 0.0)


def spearman(a: np.ndarray, b: np.ndarray, mask: np.ndarray) -> float:
    from scipy.stats import spearmanr

    x = a[mask].ravel()
    y = b[mask].ravel()
    return float(spearmanr(x, y).statistic)


def main() -> int:
    foot = grid.load_footprint(TEMPLATE)
    labels = grid.load_labels(LABELS)
    catalogue = labels & foot

    # ---- 1. Independent format re-read of the candidate ----
    v_nan = submission.verify_geotiff(H38_1, TEMPLATE)

    base = load_pred(H36_1)
    cand = load_pred(H38_1)
    base_dot = base > 0.5
    cand_dot = cand > 0.5
    added = cand_dot & ~base_dot & foot
    n_added = int(added.sum())

    # ---- 2. Paired holdout, 4 spatial quadrants ----
    fold = holdout.make_quadrant_folds(foot)
    results = []
    for fold_id in range(4):
        split = holdout.make_split(labels, fold, fold_id, seed=1)
        for name, pred in (("base_H36_1", base), ("cand_H38_1", cand)):
            r = metric.dti_binary(pred, split.hidden, valid=foot, known=split.known)
            results.append(
                {
                    "fold": fold_id,
                    "fold_name": split.name,
                    "arm": name,
                    "dti": r["dti"],
                    "TPw": r["TPw"],
                    "FPw": r["FPw"],
                    "FNw": r["FNw"],
                    "n_truth": r["n_truth"],
                    "n_emitted": r["n_emitted"],
                }
            )

    deltas = []
    folds_map = {}
    for r in results:
        folds_map.setdefault(r["fold"], {})[r["arm"]] = r
    for fid in sorted(folds_map):
        deltas.append(
            folds_map[fid]["cand_H38_1"]["dti"] - folds_map[fid]["base_H36_1"]["dti"]
        )
    deltas_arr = np.array(deltas, dtype=np.float64)
    mean_delta = float(deltas_arr.mean())
    if len(deltas_arr) > 1:
        se = deltas_arr.std(ddof=1) / np.sqrt(len(deltas_arr))
        ci = (mean_delta - 1.96 * se, mean_delta + 1.96 * se)
    else:
        ci = (mean_delta, mean_delta)

    from gems27.metric import ALPHA, BETA, EPS

    def pooled(arm):
        rows = [r for r in results if r["arm"] == arm]
        tp = sum(r["TPw"] for r in rows)
        fp = sum(r["FPw"] for r in rows)
        fn = sum(r["FNw"] for r in rows)
        n = sum(r["n_truth"] for r in rows)
        return tp / (tp + ALPHA * fp + BETA * fn + EPS), tp, fp, fn, n

    pooled_base, ptb, fpb, fnb, nb = pooled("base_H36_1")
    pooled_cand, ptc, fpc, fnc, nc = pooled("cand_H38_1")
    pooled_delta = pooled_cand - pooled_base

    # credit per added dot: pooled true-positive credit gain divided by added dots
    # inside the withheld truth footprint approximation -> use pooled TPw delta / n_added
    credit_per_added_dot = (ptc - ptb) / max(n_added, 1)

    # ---- 3. Uniqueness vs registry ----
    d_cat = distance_transform_edt(~catalogue)
    dots_on_cat = int((cand_dot & catalogue).sum())
    min_d_cat_added = float(d_cat[added].min()) if n_added else None

    probe_exists = PROBE.is_file()
    probe_report = {}
    if probe_exists:
        with rasterio.open(PROBE) as s:
            probe_a = s.read(1)
        probe_dot = np.isfinite(probe_a) & (probe_a > 0.5) & foot
        d_probe = distance_transform_edt(~probe_dot)
        within3 = int((d_probe[added] <= 3.0).sum()) if n_added else 0
        probe_report["cand_dots_within_3px_of_probe_all_dots"] = int(
            (d_probe[cand_dot] <= 3.0).sum()
        )
        # Spearman on finite overlap of the two binary surfaces
        both_finite = foot & np.isfinite(probe_a)
        sp = spearman(cand, probe_a, both_finite) if both_finite.any() else None
        probe_report = {
            "probe_file": PROBE.name,
            "probe_dots": int(probe_dot.sum()),
            "cand_dots_within_3px_of_probe": within3,
            "fraction_cand_dots_within_3px_of_probe": (within3 / n_added) if n_added else None,
            "surface_spearman_cand_vs_probe": sp,
        }

    # surface similarity vs H36-1 base (expected near-1: H38-1 extends H36-1)
    sp_base = spearman(cand, base, foot)

    report = {
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "candidate_file": H38_1.name,
        "candidate_sha256": v_nan["sha256"],
        "content_id": "56a9f473edc7",
        "base_file": H36_1.name,
        "method": (
            "paired 4-quadrant component-hiding holdout (src/gems27/holdout.py); "
            "metric src/gems27/metric.py alpha=0.2 beta=0.8 300 m triangular kernel; "
            "format re-read src/gems27/submission.verify_geotiff"
        ),
        "note": "HOLDOUT-DTI (catalogue-internal proxy), NOT an organizer score; no claim of portal acceptance",
        "format_verification": v_nan,
        "format_all_hard_checks_passed": bool(v_nan["hard_checks_passed"]),
        "emitted_px": int(cand_dot.sum()),
        "n_added_over_h36_1": n_added,
        "dots_on_catalogue": dots_on_cat,
        "min_d_cat_of_added_dots_px": min_d_cat_added,
        "holdout_folds": results,
        "paired_deltas_per_fold": deltas,
        "mean_paired_delta_dti": mean_delta,
        "ci95_paired_approx": ci,
        "positive_folds": int(sum(1 for d in deltas if d > 0)),
        "total_folds": len(deltas),
        "pooled_base_dti": pooled_base,
        "pooled_cand_dti": pooled_cand,
        "pooled_delta_dti": pooled_delta,
        "pooled_delta_over_base": pooled_delta,
        "n_withheld_positives_pooled": int(nb),
        "credit_per_added_dot_px": credit_per_added_dot,
        "surface_spearman_cand_vs_base": sp_base,
        "uniqueness_vs_registry": probe_report,
        "verdict": None,  # set below
    }

    tau_live = 0.054852
    passes = (
        v_nan["hard_checks_passed"]
        and dots_on_cat == 0
        and (min_d_cat_added or 999) >= 3.0
        and pooled_delta > 0
        and credit_per_added_dot >= tau_live
    )
    report["verdict"] = (
        "promote" if passes else "negative"
    )
    report["verdict_reason"] = (
        "format PASS; 0 dots on catalogue; added dots >= 3 px from catalogue; "
        f"pooled ΔDTI {pooled_delta:+.6f}; credit/dot {credit_per_added_dot:.5f} vs tau_live {tau_live}"
        if passes else "one or more gates failed"
    )
    out_path = (
        EVID
        / "holdout_compare_gems28-h38-1_vs_h36-1_2026-10-25.json"
    )
    out_path.write_text(json.dumps(report, indent=2, default=float) + "\n")

    print(json.dumps(
        {
            "format_hard_checks_passed": v_nan["hard_checks_passed"],
            "emitted_px": int(cand_dot.sum()),
            "n_added": n_added,
            "dots_on_catalogue": dots_on_cat,
            "pooled_base_dti": pooled_base,
            "pooled_cand_dti": pooled_cand,
            "pooled_delta_dti": pooled_delta,
            "mean_paired_delta_dti": mean_delta,
            "ci95": ci,
            "credit_per_added_dot": credit_per_added_dot,
            "tau_live": tau_live,
            "verdict": report["verdict"],
        },
        indent=2,
    ))
    print(f"Evidence: {out_path}")
    return 0 if passes else 1


if __name__ == "__main__":
    raise SystemExit(main())
