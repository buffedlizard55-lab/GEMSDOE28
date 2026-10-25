#!/usr/bin/env python3
"""
Holdout evaluation of the unique H40-1 thermal-vent submission using the
existing 4-quadrant component-hiding holdout (src/gems27/holdout.py).

Reports pooled DTI and paired delta vs the H36-1 base on the same folds.
This is a catalogue-internal proxy (HOLDOUT-DTI), not an organizer score.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import grid, holdout  # noqa: E402
from gems27.metric import dti_binary  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DL = ROOT / "docs" / "downloads"

H36_1 = DL / "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif"
NEW_SUBMISSION = DL / "gems28-h40-1-thermal-vent-r35-20261025T204851Z-7935260dcfad-nan.tif"
LABELS = DATA / "labels.tif"
TEMPLATE = DATA / "sample_submission.tif"


def load_pred(path: Path) -> np.ndarray:
    with rasterio.open(path) as s:
        a = s.read(1).astype(np.float32)
    return np.where(np.isfinite(a), a, 0.0)


def main() -> int:
    foot = grid.load_footprint(TEMPLATE)
    labels = grid.load_labels(LABELS)

    base = load_pred(H36_1)
    cand = load_pred(NEW_SUBMISSION)

    fold = holdout.make_quadrant_folds(foot)

    results = []
    for fold_id in range(4):
        split = holdout.make_split(labels, fold, fold_id, seed=1)
        # DTI on the hidden truth of this fold, known faults masked everywhere.
        for name, pred in (("base_H36_1", base), ("cand_H40_1", cand)):
            r = dti_binary(
                pred,
                split.hidden,
                valid=foot,
                known=split.known,
            )
            results.append(
                {
                    "fold": fold_id,
                    "fold_name": split.name,
                    "arm": name,
                    "dti": r["dti"],
                    "tpw": r["TPw"],
                    "fpw": r["FPw"],
                    "fnw": r["FNw"],
                    "n_truth": r["n_truth"],
                    "n_emitted": r["n_emitted"],
                }
            )

    # Compute paired deltas per fold.
    folds = {}
    for r in results:
        folds.setdefault(r["fold"], {})[r["arm"]] = r

    deltas = []
    for arms in folds.values():
        d = arms["cand_H40_1"]["dti"] - arms["base_H36_1"]["dti"]
        deltas.append(d)

    deltas_arr = np.array(deltas)
    mean_delta = float(deltas_arr.mean())
    se = deltas_arr.std(ddof=1) / np.sqrt(len(deltas_arr)) if len(deltas_arr) > 1 else 0.0
    ci = (mean_delta - 1.96 * se, mean_delta + 1.96 * se)

    pooled_base_tp = sum(r["tpw"] for r in results if r["arm"] == "base_H36_1")
    pooled_base_fp = sum(r["fpw"] for r in results if r["arm"] == "base_H36_1")
    pooled_base_fn = sum(r["fnw"] for r in results if r["arm"] == "base_H36_1")
    pooled_base_n = sum(r["n_truth"] for r in results if r["arm"] == "base_H36_1")
    from gems27.metric import ALPHA, BETA, EPS
    pooled_base_dti = pooled_base_tp / (pooled_base_tp + ALPHA * pooled_base_fp + BETA * pooled_base_fn + EPS)

    pooled_cand_tp = sum(r["tpw"] for r in results if r["arm"] == "cand_H40_1")
    pooled_cand_fp = sum(r["fpw"] for r in results if r["arm"] == "cand_H40_1")
    pooled_cand_fn = sum(r["fnw"] for r in results if r["arm"] == "cand_H40_1")
    pooled_cand_dti = pooled_cand_tp / (pooled_cand_tp + ALPHA * pooled_cand_fp + BETA * pooled_cand_fn + EPS)

    pooled_delta = pooled_cand_dti - pooled_base_dti

    report = {
        "evaluated_utc": datetime.now(timezone.utc).isoformat(),
        "submission_file": NEW_SUBMISSION.name,
        "submission_cid": "7935260dcfad",
        "base_file": H36_1.name,
        "method": "4-quadrant component-hiding holdout (src/gems27/holdout.py)",
        "note": "HOLDOUT-DTI (catalogue-internal proxy), NOT an organizer score",
        "folds": results,
        "paired_deltas_per_fold": deltas,
        "mean_paired_delta_dti": mean_delta,
        "ci95_approx": ci,
        "pooled_base_dti": pooled_base_dti,
        "pooled_cand_dti": pooled_cand_dti,
        "pooled_delta_dti": pooled_delta,
        "n_withheld_positives": int(pooled_base_n),
        "positive_folds": int(sum(1 for d in deltas if d > 0)),
        "total_folds": len(deltas),
    }
    out_path = DL / "checks-gems28-h40-1-thermal-vent-r35-20261025T204851Z-7935260dcfad-holdout.json"
    out_path.write_text(json.dumps(report, indent=2) + "\n")

    print(f"Pooled base DTI:  {pooled_base_dti:.6f}")
    print(f"Pooled cand DTI:  {pooled_cand_dti:.6f}")
    print(f"Pooled delta DTI: {pooled_delta:+.6f}")
    print(f"Mean paired delta: {mean_delta:+.6f} (95% CI approx [{ci[0]:+.6f}, {ci[1]:+.6f}])")
    print(f"Positive folds: {report['positive_folds']}/{report['total_folds']}")
    print(f"Report: {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
