#!/usr/bin/env python3
"""LOSFO far-field probe of the *emission rule* (H37-1 coverage packing vs raster-order thinning).

Why this file exists
--------------------
`knowledge/31_hypotheses_session13.md` §7 names this as the one measurement that outranks every
geological arm: H37-1's +0.007289 OOF gain was measured on the *interleaved* proxy, whose truth is
100 % catalogue geometry at distance 0 from the published catalogue. A coverage objective aimed at a
catalogue-trained probability field is **a priori favoured** by that protocol (registered as
`h37-1-is-proxy-favoured-by-construction`, severity high). This probe re-runs the same comparison
under the leave-fault-system-out protocol (`src/gems27/losfo.py`), where the detector never saw a
positive label within 600 m of the evaluated truth.

This is a **measurement instrument, not a promotion gate.** It spends no weekly submission slot and
approves no file. Fresh seed decade 215-219 (the diagnostic in `evidence/losfo_farfield_diagnostic.json`
used 210-214, so these cells are unseen).

What is compared, holding everything else fixed
----------------------------------------------
Per seed, one honest detector is trained on `losfo.masked_labels` (held-out systems and their 600 m
buffer erased). Per fold, the same candidate ridges and the same pre-thin budget `k` feed four
emission rules:

  thin_d28      reference: `thinning.dot_thin(top-k ridge pool, 2.8)` - the content-blind raster-order
                rule that produced the live 0.2600 file.
  thin_d30      reference: `dot_thin(top-k pool, 3.0)` - the H36-1 rung.
  cover_n       H37-1: greedy maximum expected coverage of the detector's probability field at the
                *same* emitted count as `thin_d30` (`n_pre`), i.e. layout-only at matched N.
  cover_1p5n    dose probe: the same objective at 1.5 x n_pre.

All four are evaluated on identical truth, identical active cells, and the same crop, so the
comparison is paired cell for cell.

Usage
-----
    GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_losfo_cover_probe.py --seeds 215-219 \\
        --out evidence/losfo_cover_probe.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import (  # noqa: E402
    grid,
    holdout,
    losfo,
    metric,
    oof_detector,
    packing,
    paths,
    thinning,
)

FOLD_NAMES = holdout.FOLD_NAMES
RUNG30 = 3.0
ARMS = ["thin_d28", "thin_d30", "cover_n", "cover_1p5n"]


def top_pool(ridge: np.ndarray, prob: np.ndarray, k: int) -> np.ndarray:
    """The k highest-probability ridge pixels (identical to run_h37_1_holdout.py)."""
    ys, xs = np.nonzero(ridge)
    pool = np.zeros_like(ridge, bool)
    if len(ys) == 0 or k <= 0:
        return pool
    if len(ys) > k:
        top = np.argpartition(-prob[ys, xs], k - 1)[:k]
        ys, xs = ys[top], xs[top]
    pool[ys, xs] = True
    return pool


def eval_set(pred: np.ndarray, truth: np.ndarray, active: np.ndarray) -> dict:
    """(TPw, FPw, DTI, dots) for one arm on one cell - same closure as the LOSFO diagnostic."""
    p = pred & active
    n_g = int(truth.sum())
    if n_g == 0:
        return {"tp": 0.0, "fp": float(p.sum()), "dti": 0.0, "dots": int(p.sum()), "n_truth": 0}
    tp = float(metric.kernel_from_distance(distance_transform_edt(~p)[truth]).sum())
    fp = float((1.0 - metric.kernel_from_distance(distance_transform_edt(~truth))[p]).sum())
    dti = tp / (tp + metric.ALPHA * fp + metric.BETA * (n_g - tp) + metric.EPS)
    return {"tp": tp, "fp": fp, "dti": dti, "dots": int(p.sum()), "n_truth": n_g}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="215-219")
    ap.add_argument("--dilate-px", type=int, default=losfo.DEFAULT_DILATE_PX)
    ap.add_argument("--buffer-px", type=int, default=losfo.DEFAULT_BUFFER_PX)
    ap.add_argument("--out", default=str(paths.EVIDENCE / "losfo_cover_probe.json"))
    args = ap.parse_args()

    a, _, b = args.seeds.partition("-")
    seeds = list(range(int(a), int(b) + 1)) if b else [int(a)]
    t0 = time.time()

    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)

    sys_grid, n_sys = losfo.fault_systems(labels, args.dilate_px)
    tab = losfo.system_table(sys_grid, n_sys, foot)
    print(f"catalogue {int(labels.sum()):,} px in {n_sys:,} fault systems", flush=True)

    cells: list[dict] = []
    meta: dict = {}
    for seed in seeds:
        hold = losfo.assign_systems_to_folds(tab, fold, 4, seed=seed)
        masked = losfo.masked_labels(labels, sys_grid, hold, args.buffer_px)
        prob = oof_detector.fit_predict_oof_probabilities(foot, masked, fold)
        ridge = oof_detector.ridge_nms(prob, foot, sigma=1.0)
        meta = {
            "n_systems": n_sys,
            "n_systems_held_out": int((hold >= 0).sum()),
            "masked_label_px": int(masked.sum()),
            "full_label_px": int(labels.sum()),
            "buffer_px": args.buffer_px,
            "dilate_px": args.dilate_px,
        }
        for f in range(4):
            sp = losfo.build_losfo_split(labels, sys_grid, hold, fold, f, seed, FOLD_NAMES,
                                         args.buffer_px)
            if not sp.hidden.any():
                continue
            sl = holdout.crop(None, sp.fold_mask)
            fm = sp.fold_mask[sl]
            hidden = sp.hidden[sl] & fm & ~sp.known[sl]
            active = fm & ~sp.known[sl]
            rid = ridge[sl] & active
            pr = np.where(active, prob[sl], 0.0).astype(np.float32)

            k = int(round(oof_detector.PRE_THIN_FRAC * int(fm.sum())))
            pool = top_pool(rid, pr, k)
            n_pre = int(thinning.dot_thin(pool, RUNG30).sum())

            emissions = {
                "thin_d28": oof_detector.build_oof_dotted_base(
                    prob[sl], ridge[sl], fm, sp.known[sl],
                    budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=2.8) & active,
                "thin_d30": thinning.dot_thin(pool, RUNG30) & active,
                "cover_n": packing.coverage_greedy(rid, pr, n_pre) & active,
                "cover_1p5n": packing.coverage_greedy(rid, pr, int(round(1.5 * n_pre))) & active,
            }

            row = {"seed": seed, "fold": sp.name, "n_truth": int(hidden.sum()),
                   "n_pre_rung30": n_pre, "n_ridges": int(rid.sum()),
                   "min_dist_truth_to_known_px": float(sp.min_dist_hidden_to_known),
                   "median_dist_truth_to_known_px": float(
                       np.median(distance_transform_edt(~sp.known)[sl][hidden]))
                   if sp.known.any() else None}
            for arm, mask in emissions.items():
                row[arm] = eval_set(mask, hidden, active)
            cells.append(row)
        print(f"seed {seed} done (t={time.time() - t0:.0f}s)", flush=True)

    if not cells:
        raise SystemExit("no evaluation cells produced")

    def agg(arm: str) -> dict:
        tp = sum(c[arm]["tp"] for c in cells)
        fp = sum(c[arm]["fp"] for c in cells)
        ng = sum(c[arm]["n_truth"] for c in cells)
        dtis = [c[arm]["dti"] for c in cells]
        return {
            "mean_dti": float(np.mean(dtis)), "sum_tp": float(tp), "sum_fp": float(fp),
            "sum_n_truth": int(ng),
            "credit_per_dot": float(tp / max(1, sum(c[arm]["dots"] for c in cells))),
            "mean_dots": float(np.mean([c[arm]["dots"] for c in cells])),
            "recall_w": float(tp / ng) if ng else 0.0,
        }

    arms = {arm: agg(arm) for arm in ARMS}
    per_seed_delta = {
        arm: [float(np.mean([c[arm]["dti"] - c["thin_d28"]["dti"] for c in cells if c["seed"] == s]))
              for s in seeds]
        for arm in ARMS
    }
    fold_delta = {
        arm: {fn: float(np.mean([c[arm]["dti"] - c["thin_d28"]["dti"]
                                for c in cells if c["fold"] == fn])) for fn in FOLD_NAMES}
        for arm in ARMS
    }
    summary = {
        arm: {
            **arms[arm],
            "mean_gain_vs_thin_d28": float(np.mean(per_seed_delta[arm])),
            "seeds_won_vs_thin_d28": int(sum(g > 0 for g in per_seed_delta[arm])),
            "min_seed_gain_vs_thin_d28": float(np.min(per_seed_delta[arm])),
            "fold_gains_vs_thin_d28": fold_delta[arm],
            "folds_won_vs_thin_d28": int(sum(v > 0 for v in fold_delta[arm].values())),
            "n_seeds": len(seeds),
        }
        for arm in ARMS
    }
    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": ("DIAGNOSTIC, NOT A PROMOTION GATE. Far-field (>= 600 m label-buffer) paired test of "
                 "the H37-1 coverage packing rule against raster-order thinning at matched budget. "
                 "It approves nothing and spends no slot."),
        "protocol": "src/gems27/losfo.py (leave-fault-system-out, 600 m label buffer)",
        "question": ("does the H37-1 emission-rule gain survive when the detector never saw a positive "
                     "label within 600 m of the evaluated truth?"),
        "code_sha256": {
            "losfo": hashlib.sha256((paths.REPO / "src" / "gems27" / "losfo.py").read_bytes()).hexdigest(),
            "packing": hashlib.sha256((paths.REPO / "src" / "gems27" / "packing.py").read_bytes()).hexdigest(),
            "oof_detector": hashlib.sha256(
                (paths.REPO / "src" / "gems27" / "oof_detector.py").read_bytes()).hexdigest(),
            "runner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "seeds": seeds, "cells": cells, "meta": meta,
        "arms": summary,
        "far_field_check": {
            "min_dist_truth_to_known_px_over_cells": float(
                min(c["min_dist_truth_to_known_px"] for c in cells)),
            "median_dist_truth_to_known_px_over_cells": float(
                np.median([c["median_dist_truth_to_known_px"] for c in cells
                           if c["median_dist_truth_to_known_px"] is not None])),
        },
        "seconds": time.time() - t0,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")

    for arm in ARMS:
        s = summary[arm]
        print(f"{arm:12s} mean DTI {s['mean_dti']:.5f}  credit/dot {s['credit_per_dot']:.4f}  "
              f"gains {s['seeds_won_vs_thin_d28']}/{len(seeds)} seeds "
              f"{s['folds_won_vs_thin_d28']}/4 folds  dDTI {s['mean_gain_vs_thin_d28']:+.6f}")
    print(f"truth >= {out['far_field_check']['min_dist_truth_to_known_px_over_cells']:.0f} px from "
          f"every known pixel; written {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
