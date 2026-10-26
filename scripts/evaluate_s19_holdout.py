#!/usr/bin/env python3
"""S19 Experiment 2 (knowledge/55): buffered whole-system LOSFO gate, seeds 320-324.

Candidate = shared detector all-ridge coverage packing weighted by
prob * (1 + 0.5 * RADLIN bonus). Baseline = S18-registered H38-1 recipe
(rung-3.0 dotted base + joint heat-flow/Euler additions) recomputed on
visible-only labels. Shared evaluator only; no TIFF tuning; spent seeds
refuse a re-run via the started marker.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src"), str(ROOT / "scripts")]
from gems27 import (  # noqa: E402
    grid,
    heatflow_euler,
    holdout,
    losfo,
    metric,
    oof_detector,
    packing,
    paths,
    submission,
)
from run_losfo_harness import eval_set  # noqa: E402

SEEDS = list(range(320, 325))


def pooled(rows):
    tp = sum(r["tp"] for r in rows)
    fp = sum(r["fp"] for r in rows)
    ng = sum(r["n_truth"] for r in rows)
    dots = sum(r["dots"] for r in rows)
    return {"dti": float(tp / (tp + metric.ALPHA * fp + metric.BETA * (ng - tp) + metric.EPS)),
            "tp": float(tp), "fp": float(fp), "n_truth": int(ng), "dots": int(dots)}


def confidence_intervals(cells):
    grouped = {arm: [pooled([r[arm] for r in cells if r["fold_id"] == f]) for f in range(4)]
               for arm in ("candidate", "baseline")}
    rng = np.random.default_rng(42019)
    choices = rng.integers(0, 4, size=(10_000, 4))
    scores = {}
    for arm in grouped:
        groups = grouped[arm]
        tp = np.array([g["tp"] for g in groups])[choices].sum(axis=1)
        fp = np.array([g["fp"] for g in groups])[choices].sum(axis=1)
        ng = np.array([g["n_truth"] for g in groups])[choices].sum(axis=1)
        scores[arm] = tp / (tp + 0.2 * fp + 0.8 * (ng - tp) + metric.EPS)
    return {"method": "paired geographic-fold block percentile bootstrap; 10000 replicates; only 4 blocks",
            "candidate_ci95": np.quantile(scores["candidate"], [0.025, 0.975]).tolist(),
            "baseline_ci95": np.quantile(scores["baseline"], [0.025, 0.975]).tolist(),
            "paired_gain_ci95": np.quantile(scores["candidate"] - scores["baseline"], [0.025, 0.975]).tolist()}


def main():
    t0 = time.monotonic()
    output = ROOT / "evidence/s19_holdout.json"
    started = ROOT / "evidence/s19_holdout.started.json"
    if output.exists() or started.exists():
        raise SystemExit("Frozen experiment already started; do not rerun spent seeds 320-324.")
    stage = json.loads((ROOT / "evidence/s19_surface.json").read_text())
    if not stage["passed"]:
        raise SystemExit("Experiment 1 (canary/pre-placement) did not pass; gate is stopped.")
    surf_path = paths.DATA / "prepared" / "s19_radlin_surface.npz"
    if submission.sha256_file(surf_path) != stage["surface_npz_sha256"]:
        raise ValueError("RADLIN surface changed since Experiment 1")
    z = np.load(surf_path)
    bonus = z["bonus"]

    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)
    sys_grid, n_sys = losfo.fault_systems(labels, losfo.DEFAULT_DILATE_PX)
    table = losfo.system_table(sys_grid, n_sys, foot)
    fields = heatflow_euler.build_corroboration_fields(
        foot, hf_json_path=paths.SB_HEAT_FLOW_JSON,
        euler_csv_path=paths.EULER_CLUSTERS_CSV, lidar_path=paths.LIDAR)
    inputs = {"cache": paths.PREPARED_FEATURES, "heat_flow": paths.SB_HEAT_FLOW_JSON,
              "euler_clusters": paths.EULER_CLUSTERS_CSV, "lidar": paths.LIDAR,
              "labels": paths.LABELS, "template": paths.TEMPLATE,
              "surface_npz": surf_path, "extensions": paths.DATA / "geodawn_extensions_u8.tif"}
    hashes = {name: submission.sha256_file(p) for name, p in inputs.items()}
    baseline_hash = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
    evaluator_hashes = {name: submission.sha256_file(ROOT / p) for name, p in {
        "eval_set_v2": "scripts/run_losfo_harness.py", "metric": "src/gems27/metric.py",
        "split": "src/gems27/losfo.py", "runner": "scripts/evaluate_s19_holdout.py",
        "radlin": "src/gems27/radlin.py", "packing": "src/gems27/packing.py"}.items()}
    started.write_text(json.dumps({
        "session": "S19-RADLIN", "experiment": 2, "seeds": SEEDS,
        "preregistration": "knowledge/55_s19_preregistration.md",
        "evaluator_hashes": evaluator_hashes, "baseline_sha256": baseline_hash,
        "inputs": hashes}, indent=2) + "\n")

    cells, hidden_union = [], np.zeros_like(foot)
    for seed in SEEDS:
        assignment = losfo.assign_systems_to_folds(table, fold, 4, seed=seed)
        visible = losfo.masked_labels(labels, sys_grid, assignment, losfo.DEFAULT_BUFFER_PX)
        prob = oof_detector.fit_predict_oof_probabilities(foot, visible, fold)
        ridge = oof_detector.ridge_nms(prob, foot, sigma=1.0)
        for f in range(4):
            split = losfo.build_losfo_split(labels, sys_grid, assignment, fold, f, seed,
                                            holdout.FOLD_NAMES, losfo.DEFAULT_BUFFER_PX)
            if not split.hidden.any():
                raise ValueError("empty frozen evaluation cell")
            hidden_union |= split.hidden
            sl = holdout.crop(None, split.fold_mask)
            fm, known, truth = split.fold_mask[sl], split.known[sl], split.hidden[sl]
            active = fm & ~known
            d_known = distance_transform_edt(~known)
            # Baseline: S18-registered H38-1 recipe on visible-only labels.
            base = oof_detector.build_oof_dotted_base(prob[sl], ridge[sl], fm, known,
                                                      budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=3.0)
            base &= active & (d_known > 1)
            added = heatflow_euler.select_corroborated_ridge_dots(
                prob[sl], ridge[sl], active, base, known, fields["joint_mask"][sl],
                score_mult=fields["score_mult"][sl], k_cap=heatflow_euler.K_CAP_PER_CELL,
                min_dist_base=heatflow_euler.MIN_DIST_BASE_PX,
                min_dist_known=heatflow_euler.MIN_DIST_KNOWN_PX,
                thin_d=heatflow_euler.THIN_D_PX, rng_seed=50_000 + seed * 10 + f)["added"]
            baseline = base | added
            # Candidate: frozen RADLIN-weighted all-ridge coverage, count-matched per cell.
            n_target = int(baseline.sum())
            eligible = ridge[sl] & active & (d_known > 2)
            weight = (prob[sl] * (1.0 + 0.5 * bonus[sl])).astype(np.float32)
            candidate = packing.coverage_greedy(eligible, weight, n_target) & active
            row = {"seed": seed, "fold_id": f, "fold": split.name,
                   "minimum_hidden_to_visible_px": float(split.min_dist_hidden_to_known),
                   "candidate": eval_set(candidate, truth, active),
                   "baseline": eval_set(baseline, truth, active),
                   "candidate_on_visible": int((candidate & known).sum()),
                   "baseline_on_visible": int((baseline & known).sum()),
                   "candidate_target": n_target,
                   "visible_mask_sha256": hashlib.sha256(known.tobytes()).hexdigest()}
            cells.append(row)
        print(f"seed {seed} complete; {len(cells)} cells; {time.monotonic()-t0:.1f}s", flush=True)
        (paths.DATA / "s19_partial_holdout.json").write_text(json.dumps(cells, indent=2) + "\n")

    cand, base_p = (pooled([r[a] for r in cells]) for a in ("candidate", "baseline"))
    ci = confidence_intervals(cells)
    gain = cand["dti"] - base_p["dti"]
    per_fold, per_seed = {}, {}
    for group, values, target in (("fold_id", range(4), per_fold), ("seed", SEEDS, per_seed)):
        for key in values:
            subset = [r for r in cells if r[group] == key]
            target[str(key)] = pooled([r["candidate"] for r in subset])["dti"] - pooled([r["baseline"] for r in subset])["dti"]
    gate = {"positive_paired_gain_ci": ci["paired_gain_ci95"][0] > 0,
            "pooled_gain_gt_0.001": gain > 0.001,
            "positive_3_of_4_folds": sum(v > 0 for v in per_fold.values()) >= 3,
            "positive_4_of_5_seeds": sum(v > 0 for v in per_seed.values()) >= 4,
            "all_cells_buffered": all(r["minimum_hidden_to_visible_px"] > 6 for r in cells),
            "no_visible_dots": all(r["candidate_on_visible"] == r["baseline_on_visible"] == 0 for r in cells)}
    result = {"label": "HOLDOUT-DTI", "session": "S19-RADLIN", "experiment": 2,
              "baseline": "H38-1 joint-on-r30-r1 recomputed via registered shared recipe on visible-only labels",
              "baseline_scope": "Registered prior best candidate; not a certified global or organizer best",
              "baseline_sha256": baseline_hash,
              "evaluator_version": "run_losfo_harness.eval_set v2 -> metric.dti_binary; S19 evaluator hash bundle",
              "evaluator_hashes": evaluator_hashes, "inputs": hashes, "seeds": SEEDS,
              "whole_segments": True, "buffered": True, "visible_only_features": True,
              "pixel_exact_visible_mask": True, "pooled": True,
              "alpha": 0.2, "beta": 0.8, "kernel_m": 300, "kernel": "triangular",
              "withheld_positives": cand["n_truth"], "unique_withheld_positive_pixels": int(hidden_union.sum()),
              "candidate_pooled": cand, "baseline_pooled": base_p, "pooled_gain": gain,
              "ci": ci, "per_fold_gain": per_fold, "per_seed_gain": per_seed,
              "candidate_credit_per_dot": cand["tp"] / max(1, cand["dots"]),
              "baseline_credit_per_dot": base_p["tp"] / max(1, base_p["dots"]),
              "gate": gate, "gate_passed": all(gate.values()), "cells": cells,
              "limitations": ["Catalogue-mapped systems are not a sample of truly unmapped faults.",
                              "Only four geographic bootstrap blocks; uncertainty is descriptive.",
                              "Withheld-positive pooled count repeats faults across seeds; unique count reported separately.",
                              "Historical heat-flow/Euler external mirrors are not independently authenticated official inputs."],
              "seconds": round(time.monotonic() - t0, 1)}
    output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: result[k] for k in ("candidate_pooled", "baseline_pooled", "pooled_gain", "ci", "per_fold_gain", "per_seed_gain", "gate", "gate_passed", "seconds")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
