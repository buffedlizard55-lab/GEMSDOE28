#!/usr/bin/env python3
"""Session 20 Experiment 2 — frozen H43-1 holdout gate (seeds 340-344).

Preregistration: knowledge/56_s20_preregistration_H43-1.md §4. Arms per cell, identical
pool / truth / masks, emissions restricted to the cell's quadrant, every catalogue-derived
quantity recomputed from visible faults only:
  C0 = dot_thin(pool & ~visible, 2.8) then blind-delete d_visible <= 2   (champion analogue)
  C1 = H43-1 greedy kernel-cover over tip-protected-B2 eligibles, budget == |C0| in the cell
Scored with gems27.metric.dti_binary (alpha 0.2, beta 0.8, 300 m triangular kernel),
known=visible (pixel-exact mask), valid=footprint. Refuses to rerun if output exists.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "src")]
from gems27 import grid, holdout, metric, paths  # noqa: E402
from gems27.greedy_cover import eligibility, greedy_kernel_cover  # noqa: E402
from gems27.thinning import dot_thin  # noqa: E402

SEEDS = list(range(340, 345))
OUT = ROOT / "evidence/s20_holdout.json"
STARTED = ROOT / "evidence/s20_holdout.started.json"


def pooled(rows):
    tp = sum(r["tp"] for r in rows)
    fp = sum(r["fp"] for r in rows)
    ng = sum(r["n_truth"] for r in rows)
    dots = sum(r["dots"] for r in rows)
    return {
        "dti": float(tp / (tp + metric.ALPHA * fp + metric.BETA * (ng - tp) + metric.EPS)),
        "tp": float(tp), "fp": float(fp), "n_truth": int(ng), "dots": int(dots),
        "credit_per_dot": float(tp / dots) if dots else 0.0,
    }


def fold_block_ci(cells, arm_c, arm_b, seed=20261026):
    """Paired percentile bootstrap over the FOUR geographic fold blocks (repo S18 method)."""
    grouped = {arm: [pooled([r[arm] for r in cells if r["fold_id"] == f]) for f in range(4)]
               for arm in (arm_c, arm_b)}
    rng = np.random.default_rng(seed)
    choices = rng.integers(0, 4, size=(10_000, 4))
    scores = {}
    for arm in grouped:
        g = grouped[arm]
        tp = np.array([x["tp"] for x in g])[choices].sum(axis=1)
        fp = np.array([x["fp"] for x in g])[choices].sum(axis=1)
        ng = np.array([x["n_truth"] for x in g])[choices].sum(axis=1)
        scores[arm] = tp / (tp + 0.2 * fp + 0.8 * (ng - tp) + metric.EPS)
    return {
        "method": "paired geographic-fold block percentile bootstrap, 10000 replicates, 4 blocks (S18 method)",
        "candidate_ci95": np.quantile(scores[arm_c], [0.025, 0.975]).tolist(),
        "baseline_ci95": np.quantile(scores[arm_b], [0.025, 0.975]).tolist(),
        "paired_gain_ci95": np.quantile(scores[arm_c] - scores[arm_b], [0.025, 0.975]).tolist(),
    }


def cell_ci(cells, arm_c, arm_b, seed=20261027):
    """Sensitivity: naive paired bootstrap over 20 cells (cells share components; optimistic)."""
    rng = np.random.default_rng(seed)
    n = len(cells)
    gains = []
    for _ in range(10_000):
        idx = rng.integers(0, n, size=n)
        rc = pooled([cells[i][arm_c] for i in idx])
        rb = pooled([cells[i][arm_b] for i in idx])
        gains.append(rc["dti"] - rb["dti"])
    return {"method": "paired 20-cell bootstrap (sensitivity only)",
            "paired_gain_ci95": np.quantile(np.array(gains), [0.025, 0.975]).tolist()}


def score(pred_bool, truth, valid, known):
    r = metric.dti_binary(pred_bool.astype(np.float64), truth, valid=valid, known=known)
    return {"dti": float(r["dti"]), "tp": float(r["TPw"]), "fp": float(r["FPw"]),
            "n_truth": int(r["n_truth"]), "dots": int(r["n_emitted"]),
            "credit_per_dot": float(r["TPw"] / r["n_emitted"]) if r["n_emitted"] else 0.0}


def main() -> int:
    if OUT.exists() or STARTED.exists():
        raise SystemExit("Frozen gate already started; seeds 340-344 must not be rerun.")
    STARTED.write_text(json.dumps({"seeds": SEEDS, "started_unix": time.time()}, indent=1))
    t0 = time.monotonic()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    with rasterio.open(paths.DATA / "h19_5_nan.tif") as s:
        pool = np.isfinite(s.read(1)) & (s.read(1) > 0) if False else None
    with rasterio.open(paths.DATA / "h19_5_nan.tif") as s:
        a = s.read(1)
    pool = np.isfinite(a) & (a > 0) & foot
    fold = holdout.make_quadrant_folds(foot)

    cells, unique_hidden = [], np.zeros(labels.shape, dtype=np.int32)
    for seed in SEEDS:
        for fid in range(4):
            tc = time.monotonic()
            sp = holdout.make_split(labels, fold, fid, seed=seed)
            visible, hidden, fmask = sp.known, sp.hidden, sp.fold_mask
            unique_hidden += hidden.astype(np.int32)
            sl = holdout.crop(fmask, fmask)
            fmc = fmask[sl]
            poolc = pool[sl] & fmc
            visc, hidc, footc = visible[sl], hidden[sl], foot[sl]
            elig, d_vis, _d_end = eligibility(poolc, visc)
            c0 = dot_thin(poolc & ~visc, 2.8) & (d_vis > 2.0) & fmc
            budget = int(c0.sum())
            c1 = greedy_kernel_cover(poolc, elig, budget, min_dist=2.8) & fmc
            row = {
                "seed": int(seed), "fold_id": int(fid), "fold": holdout.FOLD_NAMES[fid],
                "budget_c0": budget,
                "c1_dots": int(c1.sum()),
                "c0_on_visible": int((c0 & visc).sum()),
                "c1_on_visible": int((c1 & visc).sum()),
                "C0": score(c0, hidc, footc, visc),
                "C1": score(c1, hidc, footc, visc),
            }
            row["delta_dti"] = float(row["C1"]["dti"] - row["C0"]["dti"])
            cells.append(row)
            print(f"seed {seed} {row['fold']:18s} budget {budget:6d} c1 {int(c1.sum()):6d} "
                  f"C0 {row['C0']['dti']:.6f} C1 {row['C1']['dti']:.6f} d {row['delta_dti']:+.6f} "
                  f"({time.monotonic()-tc:.1f}s)", flush=True)

    rows_c0 = [c["C0"] for c in cells]
    rows_c1 = [c["C1"] for c in cells]
    p0, p1 = pooled(rows_c0), pooled(rows_c1)
    deltas = np.array([c["delta_dti"] for c in cells])
    exp1 = json.loads((ROOT / "evidence/s20_exp1_forensic.json").read_text())
    gates = {
        "G1_pooled_gain_positive_and_mean_ge_0p0005": bool(
            (p1["dti"] - p0["dti"] > 0) and (deltas.mean() >= 0.0005)),
        "G2_at_least_12_of_20_cells_positive": bool((deltas > 0).sum() >= 12),
        "G3_credit_per_dot_C1_ge_C0": bool(p1["credit_per_dot"] >= p0["credit_per_dot"]),
        "G4_zero_on_visible_every_cell": bool(
            all(c["c0_on_visible"] == 0 and c["c1_on_visible"] == 0 for c in cells)),
        "G5_canary_clean": bool(exp1["canary_pass_le_0_90"]),
    }
    out = {
        "experiment": "S20-EXP2 H43-1 frozen holdout gate",
        "preregistration": "knowledge/56_s20_preregistration_H43-1.md",
        "label": "HOLDOUT-DTI",
        "evaluator": "src/gems27/metric.py:dti_binary via holdout.make_split (quadrants, 20% of "
                     "8-connected components hidden per quadrant); alpha=0.2 beta=0.8 R=3px (300 m)",
        "seeds": SEEDS, "cells": cells,
        "pooled_C0_champion_analogue": p0,
        "pooled_C1_H43_1": p1,
        "pooled_gain": float(p1["dti"] - p0["dti"]),
        "mean_paired_gain": float(deltas.mean()),
        "cells_positive": int((deltas > 0).sum()),
        "withheld_positives_pooled": int(p0["n_truth"]),
        "withheld_positives_unique": int((unique_hidden > 0).sum()),
        "ci_fold_block": fold_block_ci(cells, "C1", "C0"),
        "ci_cell_sensitivity": cell_ci(cells, "C1", "C0"),
        "gates": gates,
        "gate_pass": bool(all(gates.values())),
        "runtime_s": round(time.monotonic() - t0, 1),
        "bias_disclosure": "Hidden pieces are catalogue-internal; this proxy rewards catalogue-"
                           "adjacent dots relative to the live hidden set and is used to test the "
                           "placement + tip-rescue half of the lane (preregistration §4).",
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("pooled_C0_champion_analogue", "pooled_C1_H43_1",
                                           "pooled_gain", "mean_paired_gain", "cells_positive",
                                           "gates", "gate_pass", "runtime_s")}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
