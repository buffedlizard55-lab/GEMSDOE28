#!/usr/bin/env python3
"""LOSFO far-field test of the H38-1 radiometric information (D1) against the frozen detector (D0).

Protocol frozen in ``knowledge/39_preregistration_H38-1_farfield.md`` **before** this file was executed.
It is the transfer test that ``knowledge/37`` section 5 requires before any H38-1 artifact may be built,
and it is the same instrument as ``scripts/run_losfo_cover_probe.py``: leave-fault-system-out folds, a
600 m label buffer, per-cell crops, identical hyper-parameters.

Per seed, two detectors are trained on the *same* LOSFO-masked labels and the *same* quadrant folds -
D0 on the frozen 32-band matrix, D1 on that matrix plus the six GeoDAWN radiometric channels. The
primary comparison is count-matched (``cover_matched_D1`` is packed to ``n_pre_D0``), so it isolates
information from budget. The extra-channel loader is imported from ``run_h38_1_holdout.py`` so the two
scripts cannot drift apart.

Writes ``evidence/losfo_rad_farfield.json``. This is a measurement, not a promotion gate: it spends no
weekly submission slot and contacts no external service (every input is a hash-pinned local raster).
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

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
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
from run_h38_1_holdout import RAD_EXTRA_BANDS, load_extras  # noqa: E402

FOLD_NAMES = holdout.FOLD_NAMES
RUNG30 = 3.0
THIN_D_REF = 2.8
ARMS = ["thin_d28_D0", "cover_n_D0", "thin_d28_D1", "cover_matched_D1", "cover_n_D1"]
PRIMARY = "cover_matched_D1"
REFERENCE = "cover_n_D0"
#: Probe means this run's D0 arms must reproduce within +/- 0.004 (knowledge/39 section 3, F4).
PROBE_COVER_N_MEAN = 0.11163472693767611
PROBE_THIN_D28_MEAN = 0.10647630400243077
F4_TOLERANCE = 0.004


def top_pool(ridge: np.ndarray, prob: np.ndarray, k: int) -> np.ndarray:
    """The k highest-probability ridge pixels (identical to run_h38_1_holdout.py)."""
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
    """(TPw, FPw, DTI, dots) for one arm on one cell - same closure as the probe and the gate."""
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
    ap.add_argument("--seeds", default="220-224")
    ap.add_argument("--dilate-px", type=int, default=losfo.DEFAULT_DILATE_PX)
    ap.add_argument("--buffer-px", type=int, default=losfo.DEFAULT_BUFFER_PX)
    ap.add_argument("--out", default=str(paths.EVIDENCE / "losfo_rad_farfield.json"))
    args = ap.parse_args()

    a, _, b = args.seeds.partition("-")
    seeds = list(range(int(a), int(b) + 1)) if b else [int(a)]
    t0 = time.time()

    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)
    extras, extra_diag = load_extras(foot)
    print(f"extras {extra_diag['names']} finite {extra_diag['finite_fraction_inside_footprint']:.5f}",
          flush=True)

    sys_grid, n_sys = losfo.fault_systems(labels, args.dilate_px)
    tab = losfo.system_table(sys_grid, n_sys, foot)
    print(f"catalogue {int(labels.sum()):,} px in {n_sys:,} fault systems", flush=True)

    cells: list[dict] = []
    integrity: list[str] = []
    determinism = None
    meta: dict = {}
    for seed in seeds:
        hold = losfo.assign_systems_to_folds(tab, fold, 4, seed=seed)
        masked = losfo.masked_labels(labels, sys_grid, hold, args.buffer_px)
        prob0 = oof_detector.fit_predict_oof_probabilities(foot, masked, fold)
        ridge0 = oof_detector.ridge_nms(prob0, foot, sigma=1.0)
        prob1 = oof_detector.fit_predict_oof_probabilities(foot, masked, fold, extra=extras)
        ridge1 = oof_detector.ridge_nms(prob1, foot, sigma=1.0)
        meta = {
            "n_systems": n_sys,
            "n_systems_held_out": int((hold >= 0).sum()),
            "masked_label_px": int(masked.sum()),
            "full_label_px": int(labels.sum()),
            "buffer_px": args.buffer_px,
            "dilate_px": args.dilate_px,
            "extra_bands": extra_diag,
            "ridge_px_D0": int(ridge0.sum()),
            "ridge_px_D1": int(ridge1.sum()),
        }
        for f in range(4):
            sp = losfo.build_losfo_split(labels, sys_grid, hold, fold, f, seed, FOLD_NAMES,
                                         args.buffer_px)
            if not sp.hidden.any():
                continue
            sl = holdout.crop(None, sp.fold_mask)
            fm = sp.fold_mask[sl]
            hid, kn = sp.hidden[sl] & fm & ~sp.known[sl], sp.known[sl]
            active = fm & ~kn
            rid0, rid1 = ridge0[sl] & active, ridge1[sl] & active
            p0 = np.where(active, prob0[sl], 0.0).astype(np.float32)
            p1 = np.where(active, prob1[sl], 0.0).astype(np.float32)

            k = int(round(oof_detector.PRE_THIN_FRAC * int(fm.sum())))
            npre0 = int(thinning.dot_thin(top_pool(rid0, p0, k), RUNG30).sum())
            npre1 = int(thinning.dot_thin(top_pool(rid1, p1, k), RUNG30).sum())

            # D0 reference emissions (once, so the exact-count assertions can be checked against them).
            thin0 = oof_detector.build_oof_dotted_base(
                prob0[sl], ridge0[sl], fm, kn, budget_frac=oof_detector.PRE_THIN_FRAC,
                thin_d=THIN_D_REF) & active
            thin1 = oof_detector.build_oof_dotted_base(
                prob1[sl], ridge1[sl], fm, kn, budget_frac=oof_detector.PRE_THIN_FRAC,
                thin_d=THIN_D_REF) & active

            emissions = {
                "thin_d28_D0": thin0,
                "cover_n_D0": packing.coverage_greedy(rid0, p0, npre0) & active,
                "thin_d28_D1": thin1,
                PRIMARY: packing.coverage_greedy(rid1, p1, npre0) & active,
                "cover_n_D1": packing.coverage_greedy(rid1, p1, npre1) & active,
            }
            if determinism is None:
                again = packing.coverage_greedy(rid1, p1, npre0) & active
                determinism = bool(np.array_equal(again, emissions[PRIMARY]))

            # ---- F3 integrity, per cell, before any metric is read --------------------------------
            for arm, target in (("cover_n_D0", npre0), (PRIMARY, npre0), ("cover_n_D1", npre1)):
                if int(emissions[arm].sum()) != target:
                    integrity.append(f"seed {seed} fold {sp.name}: {arm} emitted "
                                     f"{int(emissions[arm].sum())} != requested {target}")
            if not np.array_equal(emissions["thin_d28_D0"],
                                  thinning.dot_thin(top_pool(rid0, p0, k), THIN_D_REF) & active):
                integrity.append(f"seed {seed} fold {sp.name}: thin_d28_D0 != dot_thin(pool_D0, 2.8)")
            if not np.array_equal(emissions["thin_d28_D1"],
                                  thinning.dot_thin(top_pool(rid1, p1, k), THIN_D_REF) & active):
                integrity.append(f"seed {seed} fold {sp.name}: thin_d28_D1 != dot_thin(pool_D1, 2.8)")
            for arm, mask in emissions.items():
                if (mask & ~active).any():
                    integrity.append(f"seed {seed} fold {sp.name}: {arm} leaves active")
                if (mask & kn).any():
                    integrity.append(f"seed {seed} fold {sp.name}: {arm} overlaps known")

            row = {"seed": seed, "fold": sp.name, "n_truth": int(hid.sum()),
                   "n_pre_rung30_D0": npre0, "n_pre_rung30_D1": npre1,
                   "n_ridges_D0": int(rid0.sum()), "n_ridges_D1": int(rid1.sum()),
                   "min_dist_truth_to_known_px": float(sp.min_dist_hidden_to_known)}
            for arm, mask in emissions.items():
                row[arm] = eval_set(mask, hid, active)
            cells.append(row)
        print(f"seed {seed} done (t={time.time() - t0:.0f}s)", flush=True)

    if not cells:
        raise SystemExit("no evaluation cells produced")

    def agg(arm: str) -> dict:
        tp = sum(c[arm]["tp"] for c in cells)
        fp = sum(c[arm]["fp"] for c in cells)
        ng = sum(c[arm]["n_truth"] for c in cells)
        return {
            "mean_dti": float(np.mean([c[arm]["dti"] for c in cells])),
            "sum_tp": float(tp), "sum_fp": float(fp), "sum_n_truth": int(ng),
            "credit_per_dot": float(tp / max(1, sum(c[arm]["dots"] for c in cells))),
            "mean_dots": float(np.mean([c[arm]["dots"] for c in cells])),
            "recall_w": float(tp / ng) if ng else 0.0,
        }

    arms = {arm: agg(arm) for arm in ARMS}
    contrasts = {}
    for ref in (REFERENCE, "thin_d28_D0"):
        for arm in ARMS:
            if arm == ref:
                continue
            deltas = np.array([c[arm]["dti"] - c[ref]["dti"] for c in cells])
            per_seed = {str(s): float(np.mean([c[arm]["dti"] - c[ref]["dti"]
                                               for c in cells if c["seed"] == s])) for s in seeds}
            per_fold = {fn: float(np.mean([c[arm]["dti"] - c[ref]["dti"]
                                           for c in cells if c["fold"] == fn])) for fn in FOLD_NAMES}
            contrasts[f"{arm}_minus_{ref}"] = {
                "mean": float(deltas.mean()), "sd": float(deltas.std(ddof=1)),
                "sem": float(deltas.std(ddof=1) / np.sqrt(len(deltas))),
                "ci95": float(1.96 * deltas.std(ddof=1) / np.sqrt(len(deltas))),
                "cells_up": int((deltas > 0).sum()), "cells_below_-0.005": int((deltas < -0.005).sum()),
                "n_cells": len(deltas), "per_seed": per_seed,
                "seeds_up": int(sum(v > 0 for v in per_seed.values())),
                "per_fold": per_fold, "folds_up": int(sum(v > 0 for v in per_fold.values())),
            }

    f1 = contrasts[f"{PRIMARY}_minus_{REFERENCE}"]
    f4_ok = (abs(arms["cover_n_D0"]["mean_dti"] - PROBE_COVER_N_MEAN) <= F4_TOLERANCE
             and abs(arms["thin_d28_D0"]["mean_dti"] - PROBE_THIN_D28_MEAN) <= F4_TOLERANCE)
    criteria = {
        "F1_information_transfer_ge_0": bool(f1["mean"] >= 0),
        "F1_observed": f1["mean"], "F1_ci95": f1["ci95"],
        "F1_cells_up": f1["cells_up"], "F1_cells_below_-0.005": f1["cells_below_-0.005"],
        "F1_heavy_tail_ok": bool(f1["cells_below_-0.005"] <= 2),
        "F2_report_only_thin_d28_D1_vs_D0": contrasts["thin_d28_D1_minus_thin_d28_D0"]["mean"],
        "F3_integrity_violations": integrity,
        "F3_passed": bool(not integrity),
        "F3_determinism_replicated": determinism,
        "F4_tolerance": F4_TOLERANCE,
        "F4_cover_n_D0_mean": arms["cover_n_D0"]["mean_dti"],
        "F4_thin_d28_D0_mean": arms["thin_d28_D0"]["mean_dti"],
        "F4_probe_cover_n_mean": PROBE_COVER_N_MEAN,
        "F4_probe_thin_d28_mean": PROBE_THIN_D28_MEAN,
        "F4_passed": bool(f4_ok),
        "break_even_credit_per_dot": 0.054852,
        "passed": bool(f1["mean"] >= 0 and f1["cells_below_-0.005"] <= 2 and not integrity and f4_ok),
    }

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": ("MEASUREMENT, NOT A SUBMISSION DECISION. Far-field (>= 600 m label-buffer) paired test "
                 "of the H38-1 radiometric information at matched dot count."),
        "preregistration": "knowledge/39_preregistration_H38-1_farfield.md",
        "hypothesis_set": "knowledge/36_hypotheses_session14.md",
        "gate": "evidence/h38_1_holdout.json",
        "protocol": "src/gems27/losfo.py (leave-fault-system-out, 600 m label buffer)",
        "seeds": seeds, "meta": meta, "extra_bands": RAD_EXTRA_BANDS,
        "code_sha256": {
            "losfo": hashlib.sha256((REPO / "src" / "gems27" / "losfo.py").read_bytes()).hexdigest(),
            "packing": hashlib.sha256((REPO / "src" / "gems27" / "packing.py").read_bytes()).hexdigest(),
            "oof_detector": hashlib.sha256(
                (REPO / "src" / "gems27" / "oof_detector.py").read_bytes()).hexdigest(),
            "runner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            "h38_1_gate_runner": hashlib.sha256(
                (REPO / "scripts" / "run_h38_1_holdout.py").read_bytes()).hexdigest(),
        },
        "cells": cells, "arms": arms, "contrasts": contrasts, "criteria": criteria,
        "seconds": time.time() - t0,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n", encoding="utf-8")

    for arm in ARMS:
        s = arms[arm]
        print(f"{arm:18s} dti {s['mean_dti']:.5f}  dots {s['mean_dots']:9.1f}  "
              f"credit/dot {s['credit_per_dot']:.4f}")
    for key, blk in contrasts.items():
        print(f"  {key:34s} {blk['mean']:+.6f} (95% +/-{blk['ci95']:.6f})  "
              f"{blk['cells_up']}/{blk['n_cells']} cells  {blk['seeds_up']}/{len(seeds)} seeds  "
              f"{blk['folds_up']}/4 folds")
    print(json.dumps(criteria, indent=1)[:800])
    print(f"written {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
