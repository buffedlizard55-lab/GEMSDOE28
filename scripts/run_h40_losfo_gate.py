#!/usr/bin/env python3
"""S16 Experiment 2 (knowledge/49 frozen gate): H40-1 migration bands on LOSFO.

Paired cells, seeds 300-304 x 4 quadrant folds. D0 = frozen 32-band LOSFO detector;
D1 = D0 + 4 migration bands (extra=data/prepared/migration_extra.npy), ranking by
probability only. Evaluator is the shared harness eval_set (imported, not forked):
pooled DTI alpha=0.2 beta=0.8, 300 m triangular kernel, truth >=800 m from known.
Writes evidence/s16_h40_losfo_gate.json. No TIFF, no slot.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems27 import grid, holdout, losfo, oof_detector, paths  # noqa: E402

spec = importlib.util.spec_from_file_location("losfo_harness", ROOT / "scripts/run_losfo_harness.py")
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)
eval_set = harness.eval_set

SEEDS = list(range(300, 305))


def pooled(rows, arm):
    tp = sum(r[arm]["tp"] for r in rows)
    fp = sum(r[arm]["fp"] for r in rows)
    ng = sum(r[arm]["n_truth"] for r in rows)
    dots = sum(r[arm]["dots"] for r in rows)
    from gems27 import metric
    dti = tp / (tp + metric.ALPHA * fp + metric.BETA * (ng - tp) + metric.EPS)
    return {"dti": float(dti), "tp": float(tp), "fp": float(fp), "n_truth": int(ng),
            "dots": int(dots), "credit_per_dot": float(tp / max(1, dots))}


def main() -> int:
    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)
    extra = np.load(paths.DATA / "prepared/migration_extra.npy", mmap_mode="r")
    canary = json.loads((ROOT / "evidence/s16_canary.json").read_text())
    sys_grid, n_sys = losfo.fault_systems(labels, losfo.DEFAULT_DILATE_PX)
    tab = losfo.system_table(sys_grid, n_sys, foot)
    cells = []
    for seed in SEEDS:
        hold = losfo.assign_systems_to_folds(tab, fold, 4, seed=seed)
        masked = losfo.masked_labels(labels, sys_grid, hold, losfo.DEFAULT_BUFFER_PX)
        prob0 = oof_detector.fit_predict_oof_probabilities(foot, masked, fold)
        ridge0 = oof_detector.ridge_nms(prob0, foot, sigma=1.0)
        prob1 = oof_detector.fit_predict_oof_probabilities(foot, masked, fold, extra=extra)
        ridge1 = oof_detector.ridge_nms(prob1, foot, sigma=1.0)
        for f in range(4):
            sp = losfo.build_losfo_split(labels, sys_grid, hold, fold, f, seed,
                                         holdout.FOLD_NAMES, losfo.DEFAULT_BUFFER_PX)
            if not sp.hidden.any():
                continue
            sl = holdout.crop(None, sp.fold_mask)
            fm, hidden = sp.fold_mask[sl], sp.hidden[sl]
            active = fm & ~sp.known[sl]
            base0 = oof_detector.build_oof_dotted_base(prob0[sl], ridge0[sl], fm, sp.known[sl],
                                                       budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=2.8) & active
            base1 = oof_detector.build_oof_dotted_base(prob1[sl], ridge1[sl], fm, sp.known[sl],
                                                       budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=2.8) & active
            cells.append({"seed": seed, "fold": sp.name,
                          "d0": eval_set(base0, hidden, active), "d1": eval_set(base1, hidden, active),
                          "d0_on_known": int((base0 & sp.known[sl]).sum()),
                          "d1_on_known": int((base1 & sp.known[sl]).sum()),
                          "min_dist_truth_to_known_px": float(sp.min_dist_hidden_to_known)})
        print(f"seed {seed} done ({time.time()-t0:.0f}s) cells={len(cells)}", flush=True)

    p0, p1 = pooled(cells, "d0"), pooled(cells, "d1")
    paired = np.array([c["d1"]["dti"] - c["d0"]["dti"] for c in cells])
    rng = np.random.default_rng(42)
    boot = np.array([rng.choice(paired, size=len(paired), replace=True).mean() for _ in range(10_000)])
    per_seed = {str(s): float(np.mean([c["d1"]["dti"] - c["d0"]["dti"] for c in cells if c["seed"] == s])) for s in SEEDS}
    folds = sorted(set(c["fold"] for c in cells))
    per_fold = {f: float(np.mean([c["d1"]["dti"] - c["d0"]["dti"] for c in cells if c["fold"] == f])) for f in folds}
    gate = {
        "G1_pooled_gt0_and_mean_ge_0.001": bool(p1["dti"] - p0["dti"] > 0 and paired.mean() >= 0.001),
        "G2_spread_14cells_4seeds_3folds": bool((paired > 0).sum() >= 14 and sum(v > 0 for v in per_seed.values()) >= 4
                                                and sum(v > 0 for v in per_fold.values()) >= 3),
        "G3_credit_per_dot_not_worse": bool(p1["credit_per_dot"] >= p0["credit_per_dot"]),
        "G4_integrity_onknown0_and_count_ratio_le_0.10": bool(
            sum(c["d1_on_known"] for c in cells) == 0 and abs(p1["dots"] - p0["dots"]) / max(1, p0["dots"]) <= 0.10),
        "G5_canary_pass_from_evidence_s16_canary": bool(canary.get("canary_pass")),
    }
    out = {
        "label": "HOLDOUT-DTI (not an organizer score)",
        "evaluator": "scripts/run_losfo_harness.py eval_set imported; src/gems27/losfo.py + metric.py (alpha=0.2, beta=0.8, 300 m triangular kernel, pooled over cells)",
        "seeds": SEEDS, "n_cells": len(cells),
        "n_withheld_positives_pooled_cell_truth_px": int(sum(c["d0"]["n_truth"] for c in cells)),
        "d0_pooled": p0, "d1_pooled": p1,
        "pooled_delta_dti": float(p1["dti"] - p0["dti"]),
        "mean_paired_delta_dti": float(paired.mean()),
        "ci95_paired_bootstrap": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
        "cells_positive": int((paired > 0).sum()), "per_seed_mean_delta": per_seed, "per_fold_mean_delta": per_fold,
        "canary_single_feature_aucs": canary.get("single_feature_auc_vs_hidden_systems"),
        "gate": gate, "gate_passed": bool(all(gate.values())),
        "cells": cells, "seconds": round(time.time() - t0, 1),
    }
    outp = ROOT / "evidence/s16_h40_losfo_gate.json"
    outp.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("d0_pooled", "d1_pooled", "pooled_delta_dti",
                                          "mean_paired_delta_dti", "ci95_paired_bootstrap",
                                          "cells_positive", "gate", "gate_passed")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
