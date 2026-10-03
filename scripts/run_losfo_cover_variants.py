#!/usr/bin/env python3
"""Reconcile two conflicting far-field measurements of the same packing rule (frozen before this run).

Why this file exists
--------------------
Two LOSFO measurements of "greedy maximum expected coverage" disagree:

* `evidence/losfo_packing_farfield.json` (knowledge/33, seeds 210-214): the arm
  `max_coverage = packing.coverage_greedy(pool, prob, n_base)` - candidates restricted to the **top-k
  ridge pool** that `build_oof_dotted_base` packs, target count `n_base` = the `d=2.8` emission count -
  scored **-0.000037** against `base` (F1 FAIL).
* `evidence/losfo_cover_probe.json` (this session, seeds 215-219): the arm
  `cover_n = packing.coverage_greedy(ridge & active, prob, n_pre)` - candidates are **every ridge
  pixel**, target count `n_pre` = the rung-3.0 `dot_thin(pool, 3.0)` count, which is exactly the
  H37-1 gate's `cover_prob_r1` construction - scored **+0.005275** against `thin_d30` at an identical
  emitted count (5/5 seeds, 16/20 cells).

The two arms differ in two ways: the candidate set (top-k pool vs all ridges) and the target count
(`n_base` vs `n_pre`). This script runs all four combinations on the same detector, the same splits and
the same truth, so the difference can be attributed. It is a **measurement instrument, not a promotion
gate**; it approves nothing and spends no weekly submission slot.

Arms (per cell, all masked to `active = fold_mask & ~known`)
-----------------------------------------------------------
  base_d28            dot_thin(top-k pool, 2.8)                        reference, n_base dots
  pool_cover_nbase    coverage_greedy(pool, prob, n_base)              the merged F1 arm
  all_cover_nbase     coverage_greedy(all ridges, prob, n_base)        same count, free candidates
  pool_cover_npre     coverage_greedy(pool, prob, n_pre)               pool-restricted, rung-3.0 count
  all_cover_npre      coverage_greedy(all ridges, prob, n_pre)         the H37-1 gate construction

Frozen seeds: **215-219** (the same LOSFO decade as `run_losfo_cover_probe.py`, so `all_cover_npre`
must reproduce that file's `cover_n` to numerical tolerance - the built-in reproduction check).

Usage
-----
    GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/run_losfo_cover_variants.py --seeds 215-219 \\
        --out evidence/losfo_cover_variants.json
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
THIN_D_REF = 2.8
ARMS = ["base_d28", "pool_cover_nbase", "all_cover_nbase", "pool_cover_npre", "all_cover_npre"]


def top_pool(ridge: np.ndarray, prob: np.ndarray, k: int) -> np.ndarray:
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
    ap.add_argument("--buffer-px", type=int, default=losfo.DEFAULT_BUFFER_PX)
    ap.add_argument("--out", default=str(paths.EVIDENCE / "losfo_cover_variants.json"))
    args = ap.parse_args()
    a, _, b = args.seeds.partition("-")
    seeds = list(range(int(a), int(b) + 1)) if b else [int(a)]

    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)
    sys_grid, n_sys = losfo.fault_systems(labels, losfo.DEFAULT_DILATE_PX)
    tab = losfo.system_table(sys_grid, n_sys, foot)
    print(f"catalogue {int(labels.sum()):,} px in {n_sys:,} fault systems", flush=True)

    cells: list[dict] = []
    integrity: list[str] = []
    for seed in seeds:
        hold = losfo.assign_systems_to_folds(tab, fold, 4, seed=seed)
        masked = losfo.masked_labels(labels, sys_grid, hold, args.buffer_px)
        prob = oof_detector.fit_predict_oof_probabilities(foot, masked, fold)
        ridge = oof_detector.ridge_nms(prob, foot, sigma=1.0)
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
            base = thinning.dot_thin(pool, THIN_D_REF) & active
            n_base = int(base.sum())
            n_pre = int((thinning.dot_thin(pool, RUNG30) & active).sum())

            requested = {"base_d28": n_base, "pool_cover_nbase": n_base, "all_cover_nbase": n_base,
                         "pool_cover_npre": n_pre, "all_cover_npre": n_pre}
            emissions = {
                "base_d28": base,
                "pool_cover_nbase": packing.coverage_greedy(pool, pr, n_base) & active,
                "all_cover_nbase": packing.coverage_greedy(rid, pr, n_base) & active,
                "pool_cover_npre": packing.coverage_greedy(pool, pr, n_pre) & active,
                "all_cover_npre": packing.coverage_greedy(rid, pr, n_pre) & active,
            }
            for name, mask in emissions.items():
                if int(mask.sum()) != requested[name]:
                    integrity.append(f"seed {seed} {sp.name} {name}: emitted {int(mask.sum())} "
                                     f"!= requested {requested[name]}")

            row = {"seed": seed, "fold": sp.name, "n_truth": int(hidden.sum()),
                   "n_base": n_base, "n_pre": n_pre, "n_pool": int(pool.sum()),
                   "n_ridges": int(rid.sum())}
            for name, mask in emissions.items():
                row[name] = eval_set(mask, hidden, active)
            cells.append(row)
        print(f"seed {seed} done (t={time.time()-t0:.0f}s)", flush=True)

    def agg(arm: str) -> dict:
        tp = sum(c[arm]["tp"] for c in cells)
        fp = sum(c[arm]["fp"] for c in cells)
        ng = sum(c[arm]["n_truth"] for c in cells)
        return {"mean_dti": float(np.mean([c[arm]["dti"] for c in cells])), "sum_tp": float(tp),
                "sum_fp": float(fp), "credit_per_dot": float(tp / max(1, sum(c[arm]["dots"] for c in cells))),
                "mean_dots": float(np.mean([c[arm]["dots"] for c in cells])), "recall_w": float(tp / ng)}

    arms = {a_: agg(a_) for a_ in ARMS}
    paired = {}
    for ref in ("base_d28", "pool_cover_nbase", "pool_cover_npre"):
        for arm in ARMS:
            if arm == ref:
                continue
            per_seed = {s: float(np.mean([c[arm]["dti"] - c[ref]["dti"] for c in cells if c["seed"] == s]))
                        for s in seeds}
            per_fold = {fn: float(np.mean([c[arm]["dti"] - c[ref]["dti"] for c in cells if c["fold"] == fn]))
                        for fn in FOLD_NAMES}
            deltas = np.array([c[arm]["dti"] - c[ref]["dti"] for c in cells])
            paired[f"{arm}_minus_{ref}"] = {
                "mean": float(deltas.mean()), "sd": float(deltas.std(ddof=1)),
                "sem": float(deltas.std(ddof=1) / np.sqrt(len(deltas))),
                "cells_up": int((deltas > 0).sum()), "n_cells": len(deltas),
                "per_seed": per_seed, "seeds_up": int(sum(v > 0 for v in per_seed.values())),
                "per_fold": per_fold, "folds_up": int(sum(v > 0 for v in per_fold.values())),
            }

    # Reproduction check against evidence/losfo_cover_probe.json (same seeds, same construction).
    repro = {"file": "evidence/losfo_cover_probe.json", "present": False}
    ref_path = paths.EVIDENCE / "losfo_cover_probe.json"
    if ref_path.exists():
        ref = json.loads(ref_path.read_text())
        ref_cells = {(c["seed"], c["fold"]): c for c in ref.get("cells", [])}
        # Arm-matched reproduction: every stored probe arm must be reproduced by the same-named arm here
        # (base_d28 <-> thin_d28, all_cover_npre <-> cover_n). The d=2.8 vs d=3.0 difference is a
        # DIFFERENT-arm diagnostic and is labelled as such rather than reported as a reproduction error.
        pairs = (("all_cover_npre", "cover_n"), ("base_d28", "thin_d28"),
                 ("pool_cover_nbase", "thin_d28"), ("base_d28", "thin_d30"))
        maxdiff = {}
        for mine, theirs in pairs:
            diffs = [abs(c[mine]["dti"] - ref_cells[(c["seed"], c["fold"])][theirs]["dti"])
                     for c in cells if (c["seed"], c["fold"]) in ref_cells]
            maxdiff[f"max_abs_dti_diff_{mine}_vs_{theirs}"] = float(max(diffs)) if diffs else None
        repro = {"file": "evidence/losfo_cover_probe.json", "present": True,
                 "n_cells_compared": sum(1 for c in cells if (c["seed"], c["fold"]) in ref_cells),
                 **maxdiff,
                 "reading": ("Arm-matched comparisons are all_cover_npre vs cover_n and base_d28 vs "
                             "thin_d28; 0.0 means the two independent runs agree exactly. The d=2.8 vs "
                             "d=3.0 line is a different-arm diagnostic (candidate-set- and count-matched, "
                             "the dose ladder), not a reproduction error.")}

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": ("DIAGNOSTIC, NOT A PROMOTION GATE. Attribute the disagreement between "
                 "knowledge/33's F1 (pool-restricted coverage at n_base) and this session's "
                 "losfo_cover_probe (all-ridge coverage at n_pre)."),
        "protocol": "src/gems27/losfo.py (leave-fault-system-out, 600 m label buffer)",
        "seeds": seeds, "cells": cells, "arms": arms, "paired": paired,
        "integrity_violations": integrity,
        "reproduction_check": repro,
        "code_sha256": {
            "packing": hashlib.sha256((paths.REPO / "src" / "gems27" / "packing.py").read_bytes()).hexdigest(),
            "losfo": hashlib.sha256((paths.REPO / "src" / "gems27" / "losfo.py").read_bytes()).hexdigest(),
            "runner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "seconds": time.time() - t0,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")

    for a_ in ARMS:
        s = arms[a_]
        print(f"{a_:16s} dots {s['mean_dots']:9.1f}  dti {s['mean_dti']:.5f}  "
              f"credit/dot {s['credit_per_dot']:.4f}")
    for key in ("pool_cover_nbase_minus_base_d28", "all_cover_nbase_minus_base_d28",
                "pool_cover_npre_minus_base_d28", "all_cover_npre_minus_base_d28",
                "all_cover_nbase_minus_pool_cover_nbase", "all_cover_npre_minus_pool_cover_npre"):
        p = paired[key]
        print(f"  {key:44s} {p['mean']:+.6f}  {p['cells_up']}/{p['n_cells']} cells  "
              f"{p['seeds_up']}/{len(seeds)} seeds  {p['folds_up']}/4 folds")
    print(json.dumps(repro, indent=1))
    print(f"written {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
