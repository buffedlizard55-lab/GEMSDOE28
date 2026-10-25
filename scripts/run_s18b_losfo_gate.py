#!/usr/bin/env python3
"""S18B Experiment 2 (knowledge/52 frozen gate): H42-1 migration-extrapolated relocation on LOSFO.

Paired cells, seeds 310-314 x 4 quadrant folds. One frozen 32-band LOSFO detector per seed
(prob trained on visible faults only, 600 m buffer erased); arms differ ONLY in dot placement:
base (detector dots), phys (up-dip relocated), anti (sign-flipped), rand (seeded rotations).
Blocking inside the gate uses visible faults only. Evaluator is the shared harness eval_set
(imported, not forked): pooled DTI alpha=0.2 beta=0.8, 300 m triangular kernel.
Requires evidence/s18b_canary.json with canary_pass=true. Writes evidence/s18_h42_losfo_gate.json.
No TIFF, no slot.
"""
from __future__ import annotations

import importlib.util
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems27 import grid, holdout, losfo, metric, migration, oof_detector, paths, thinning  # noqa: E402

spec = importlib.util.spec_from_file_location("losfo_harness", ROOT / "scripts/run_losfo_harness.py")
harness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(harness)
eval_set = harness.eval_set

SEEDS = list(range(310, 315))
ARMS = ("base", "phys", "anti", "rand")


def pooled(rows, arm):
    tp = sum(r[arm]["tp"] for r in rows)
    fp = sum(r[arm]["fp"] for r in rows)
    ng = sum(r[arm]["n_truth"] for r in rows)
    dots = sum(r[arm]["dots"] for r in rows)
    dti = tp / (tp + metric.ALPHA * fp + metric.BETA * (ng - tp) + metric.EPS)
    return {"dti": float(dti), "tp": float(tp), "fp": float(fp), "n_truth": int(ng),
            "dots": int(dots), "credit_per_dot": float(tp / max(1, dots))}


def main() -> int:
    t0 = time.time()
    canary = json.loads((ROOT / "evidence/s18b_canary.json").read_text())
    if not canary.get("canary_pass"):
        print("CANARY FAILED — frozen stop rule: no gate may run (knowledge/52).", flush=True)
        return 2
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)
    vec = np.load(paths.DATA / "prepared/migration_vectors.npz")
    vy_full, vx_full = vec["vy"], vec["vx"]
    depth_full = migration.read_depth_to_base(paths.TRAINING, foot)
    sys_grid, n_sys = losfo.fault_systems(labels, losfo.DEFAULT_DILATE_PX)
    tab = losfo.system_table(sys_grid, n_sys, foot)

    cells = []
    for seed in SEEDS:
        hold = losfo.assign_systems_to_folds(tab, fold, 4, seed=seed)
        masked = losfo.masked_labels(labels, sys_grid, hold, losfo.DEFAULT_BUFFER_PX)
        prob = oof_detector.fit_predict_oof_probabilities(foot, masked, fold)
        ridge = oof_detector.ridge_nms(prob, foot, sigma=1.0)
        for f in range(4):
            sp = losfo.build_losfo_split(labels, sys_grid, hold, fold, f, seed,
                                         holdout.FOLD_NAMES, losfo.DEFAULT_BUFFER_PX)
            if not sp.hidden.any():
                continue
            sl = holdout.crop(None, sp.fold_mask)
            fm, hidden = sp.fold_mask[sl], sp.hidden[sl]
            known = sp.known[sl]
            active = fm & ~known
            base = oof_detector.build_oof_dotted_base(
                prob[sl], ridge[sl], fm, known,
                budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=2.8) & active
            # Visible-faults-only blocking: catalogue pixels + 2 px hygiene ring around them.
            blocked = known | (distance_transform_edt(~known) <= 2.0) | ~fm
            row = {"seed": seed, "fold": sp.name, "base": eval_set(base, hidden, active),
                   "min_dist_truth_to_known_px": float(sp.min_dist_hidden_to_known)}
            stats = {}
            for arm in ("phys", "anti", "rand"):
                rel, st = migration.relocate_dots(
                    base, vy_full[sl], vx_full[sl], depth_full[sl], blocked, fm,
                    mode=arm, seed=seed * 10 + f)
                rel = thinning.dot_thin(rel, 2.8) & active
                st["n_after_thin_active"] = int(rel.sum())
                st["on_known"] = int((rel & known).sum())
                stats[arm] = st
                row[arm] = eval_set(rel, hidden, active)
            row["relocation"] = stats
            cells.append(row)
        print(f"seed {seed} done ({time.time()-t0:.0f}s) cells={len(cells)}", flush=True)

    p = {a: pooled(cells, a) for a in ARMS}
    paired = np.array([c["phys"]["dti"] - c["base"]["dti"] for c in cells])
    rng = np.random.default_rng(42)
    boot = np.array([rng.choice(paired, size=len(paired), replace=True).mean() for _ in range(10_000)])
    # Cell-bootstrap CI for the pooled candidate (phys) DTI itself (promotion-card field).
    idx = np.arange(len(cells))
    boot_dti = []
    for _ in range(2000):
        pick = rng.choice(idx, size=len(idx), replace=True)
        tp = sum(cells[i]["phys"]["tp"] for i in pick)
        fp = sum(cells[i]["phys"]["fp"] for i in pick)
        ng = sum(cells[i]["phys"]["n_truth"] for i in pick)
        boot_dti.append(tp / (tp + metric.ALPHA * fp + metric.BETA * (ng - tp) + metric.EPS))
    per_seed = {str(s): float(np.mean([c["phys"]["dti"] - c["base"]["dti"]
                                       for c in cells if c["seed"] == s])) for s in SEEDS}
    folds = sorted(set(c["fold"] for c in cells))
    per_fold = {fd: float(np.mean([c["phys"]["dti"] - c["base"]["dti"]
                                    for c in cells if c["fold"] == fd])) for fd in folds}
    d_phys = p["phys"]["dti"] - p["base"]["dti"]
    d_anti = p["anti"]["dti"] - p["base"]["dti"]
    d_rand = p["rand"]["dti"] - p["base"]["dti"]
    moved = sum(c["relocation"]["phys"]["n_moved_ge1px"] for c in cells)
    moved_den = sum(c["relocation"]["phys"]["n_in"] for c in cells)
    gate = {
        "G1_pooled_gt0_and_mean_ge_0.0005": bool(d_phys > 0 and paired.mean() >= 0.0005),
        "G2_spread_14cells_4seeds_3folds": bool(
            (paired > 0).sum() >= 14 and sum(v > 0 for v in per_seed.values()) >= 4
            and sum(v > 0 for v in per_fold.values()) >= 3),
        "G3_falsification_phys_gt_anti_and_rand_pooled": bool(d_phys > d_anti and d_phys > d_rand),
        "G4_integrity_onknown0_and_count_ratio_le_0.05": bool(
            sum(c["relocation"]["phys"]["on_known"] for c in cells) == 0
            and abs(p["phys"]["dots"] - p["base"]["dots"]) / max(1, p["base"]["dots"]) <= 0.05),
        "G5_canary_pass_from_evidence_s18b_canary": bool(canary.get("canary_pass")),
    }
    out = {
        "label": "HOLDOUT-DTI (not an organizer score)",
        "evaluator": ("scripts/run_losfo_harness.py eval_set imported; src/gems27/losfo.py + "
                      "metric.py (alpha=0.2, beta=0.8, 300 m triangular kernel, pooled over cells)"),
        "evaluator_version": "losfo.py+metric.py @ arena/384a5345-gemsdoe28 (knowledge/52)",
        "seeds": SEEDS, "n_cells": len(cells),
        "n_withheld_positives_pooled_cell_truth_px": int(sum(c["base"]["n_truth"] for c in cells)),
        "pooled": p,
        "pooled_delta_dti_phys_minus_base": float(d_phys),
        "pooled_delta_dti_anti_minus_base": float(d_anti),
        "pooled_delta_dti_rand_minus_base": float(d_rand),
        "mean_paired_delta_dti": float(paired.mean()),
        "ci95_paired_bootstrap": [float(np.percentile(boot, 2.5)), float(np.percentile(boot, 97.5))],
        "ci95_pooled_phys_dti_cell_bootstrap": [float(np.percentile(boot_dti, 2.5)),
                                                float(np.percentile(boot_dti, 97.5))],
        "cells_positive": int((paired > 0).sum()),
        "per_seed_mean_delta": per_seed, "per_fold_mean_delta": per_fold,
        "pooled_frac_dots_moved_ge1px_phys": float(moved / max(1, moved_den)),
        "canary_single_feature_aucs": canary.get("single_feature_auc_vs_hidden_systems"),
        "gate": gate, "gate_passed": bool(all(gate.values())),
        "cells": cells, "seconds": round(time.time() - t0, 1),
    }
    outp = ROOT / "evidence/s18_h42_losfo_gate.json"
    outp.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("pooled", "pooled_delta_dti_phys_minus_base",
                                          "pooled_delta_dti_anti_minus_base",
                                          "pooled_delta_dti_rand_minus_base",
                                          "mean_paired_delta_dti", "ci95_paired_bootstrap",
                                          "cells_positive", "pooled_frac_dots_moved_ge1px_phys",
                                          "gate", "gate_passed")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
