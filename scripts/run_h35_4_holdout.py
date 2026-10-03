#!/usr/bin/env python3
"""Frozen LOSFO far-field holdout gate for H35-4 (buried range-front gravity bench ADD).

Preregistration: knowledge/26_preregistration_H35-4.md (SHA-256 recorded in the output; the run
is invalid if the text changed). Seeds 240-249, 10 seeds x 4 quadrant folds = 40 paired cells.

Per seed the detector trains on LOSFO-masked labels (held-out fault systems + 600 m buffer
erased - identical to scripts/run_losfo_harness.py), and each fold scores three emissions against
its held-out systems: the d=2.8 base, base + budgeted gravity-bench dots (grav_hg-ranked), and
base + a same-budget non-bench far-field-ridge direction control (same ranker). The gate
threshold is the LIVE inclusion threshold tau_live(0.2600) = 0.05485, never the cell threshold
(knowledge/22 section 3).

The mesa mask is a SHARED pre-filter: both arms emit from sub-threshold ridge minus mesa, so
the gate tests bench-vs-non-bench, not bench-vs-known-junk. The grav_hg ranker is used in the
holdout AND in the frozen full-map construction, closing the H35-1 transfer gap by design.

Leakage guards (asserted per cell): added dots are far-field (>= 3 px from the buffered known
set), disjoint from known, >= 2.8 px from every base dot, and hidden truth sits >= 6 px from
known.

Nothing here contacts drivendata.org or any network host.

Usage:
    python scripts/run_h35_4_holdout.py --seeds 240-249 --out evidence/h35_4_holdout.json
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
    gravity_bench,
    grid,
    holdout,
    losfo,
    metric,
    oof_detector,
    paths,
)
from gems27 import (
    hydrothermal as H,
)

PREREG = paths.REPO / "knowledge" / "26_preregistration_H35-4.md"
LIVE_ANCHOR = 0.2600
FOLD_NAMES = holdout.FOLD_NAMES


def eval_set(pred: np.ndarray, truth: np.ndarray, active: np.ndarray) -> dict:
    """DTI of a binary emission against a truth set, restricted to `active` cells."""
    p = np.asarray(pred, bool) & np.asarray(active, bool)
    n_g = int(np.asarray(truth, bool).sum())
    if n_g == 0:
        return {"tp": 0.0, "fp": float(p.sum()), "dti": 0.0, "dots": int(p.sum()),
                "n_truth": 0}
    tp = float(metric.kernel_from_distance(distance_transform_edt(~p)[truth]).sum())
    fp = float((1.0 - metric.kernel_from_distance(distance_transform_edt(~truth))[p]).sum())
    dti = tp / (tp + metric.ALPHA * fp + metric.BETA * (n_g - tp) + metric.EPS)
    return {"tp": tp, "fp": fp, "dti": dti, "dots": int(p.sum()), "n_truth": n_g}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="240-249")
    ap.add_argument("--out", default=str(paths.EVIDENCE / "h35_4_holdout.json"))
    args = ap.parse_args()
    a, _, b = args.seeds.partition("-")
    seeds = list(range(int(a), int(b) + 1)) if b else [int(a)]
    t0 = time.time()

    prereg_sha = hashlib.sha256(PREREG.read_bytes()).hexdigest()
    tau_live = float(metric.inclusion_threshold(LIVE_ANCHOR))

    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)
    sys_grid, n_sys = losfo.fault_systems(labels, losfo.DEFAULT_DILATE_PX)
    tab = losfo.system_table(sys_grid, n_sys, foot)
    print(f"catalogue {int(labels.sum()):,} px in {n_sys:,} fault systems", flush=True)

    # Label-free bench/mesa legs, computed once on the full grid (no truth contact).
    legs = gravity_bench.load_gravity_bench(paths.TRAINING, paths.LIDAR, foot)
    bench, mesa, grav = legs["bench"], legs["mesa"], legs["grav_hg"]
    print(f"bench={legs['bench_px']} ({legs['bench_frac_of_footprint']:.3f} of footprint) "
          f"mesa={legs['mesa_px']} ({legs['mesa_frac_of_footprint']:.4f}) "
          f"grav_cut={legs['grav_cut']} step_cut={legs['step_cut']} "
          f"relief_cut={legs['relief_cut']} step_hi={legs['step_hi_cut']} "
          f"tmi_hi={legs['tmi_hi_cut']} grav_lo={legs['grav_lo_cut']}", flush=True)

    cells: list[dict] = []
    skipped: list[dict] = []
    for seed in seeds:
        hold = losfo.assign_systems_to_folds(tab, fold, 4, seed=seed)
        masked = losfo.masked_labels(labels, sys_grid, hold, losfo.DEFAULT_BUFFER_PX)
        prob = oof_detector.fit_predict_oof_probabilities(foot, masked, fold)
        ridge = oof_detector.ridge_nms(prob, foot, sigma=1.0)
        for f in range(4):
            sp = losfo.build_losfo_split(labels, sys_grid, hold, fold, f, seed,
                                         FOLD_NAMES, losfo.DEFAULT_BUFFER_PX)
            if not sp.hidden.any():
                skipped.append({"seed": seed, "fold": sp.name, "reason": "empty_hidden"})
                continue
            if not np.isfinite(sp.min_dist_hidden_to_known) or sp.min_dist_hidden_to_known < 6.0:
                raise AssertionError(
                    f"seed {seed} fold {sp.name}: hidden-to-known separation "
                    f"{sp.min_dist_hidden_to_known} < 6 px - the far-field guarantee is broken")
            sl = holdout.crop(None, sp.fold_mask)
            fm = sp.fold_mask[sl]
            hidden = sp.hidden[sl]
            known = (sp.known & sp.fold_mask)[sl]
            active = fm & ~known

            base = oof_detector.build_oof_dotted_base(
                prob[sl], ridge[sl], fm, known,
                budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=H.THIN_D) & active
            sub = H.subthreshold_ridge(
                prob[sl], ridge[sl], fm, known, oof_detector.PRE_THIN_FRAC)
            if (base & ~sub["selected"]).any():
                raise AssertionError(
                    f"seed {seed} fold {sp.name}: base is not a subset of the top-k cut - "
                    f"the sub-threshold partition does not replicate build_oof_dotted_base")
            budget = int(round(gravity_bench.BUDGET_FRAC * int(base.sum())))
            # Shared mesa pre-filter for both arms (frozen prereg section 2).
            sub_clean = sub["subthreshold"] & ~mesa[sl]
            bench_sl, grav_sl = bench[sl], grav[sl]
            none = np.zeros_like(base, bool)
            add = H.select_additions(
                prob=prob[sl], subthreshold=sub_clean, base=base, known=known,
                thermal=bench_sl, halo=none, euler=none,
                budget_dots=budget, require_thermal=True, score=grav_sl)
            ctrl = H.select_additions(
                prob=prob[sl], subthreshold=sub_clean, base=base, known=known,
                thermal=bench_sl, halo=none, euler=none,
                budget_dots=budget, require_thermal=False, score=grav_sl)
            added, controld = add["added"] & active, ctrl["added"] & active

            # Frozen integrity assertions (criterion 6): any violation fails the RUN.
            d_known = distance_transform_edt(~known) if known.any() else np.full(fm.shape, np.inf)
            d_base = distance_transform_edt(~base) if base.any() else np.full(fm.shape, np.inf)
            for arm, dots in (("added", added), ("control", controld)):
                if dots.any():
                    assert not (dots & known).any(), f"{arm}: dot on a known pixel"
                    assert bool((d_known[dots] >= H.FAR_PX).all()), f"{arm}: dot not far-field"
                    assert bool((d_base[dots] >= H.THIN_D - 1e-9).all()), \
                        f"{arm}: dot within 2.8 px of a base dot"
                    assert not (dots & mesa[sl]).any(), f"{arm}: dot on mesa (shared floor broken)"

            r_base = eval_set(base, hidden, active)
            r_add = eval_set(base | added, hidden, active)
            r_ctrl = eval_set(base | controld, hidden, active)
            n_add, n_ctrl = int(added.sum()), int(controld.sum())
            far = base & (d_known >= H.FAR_PX)
            cells.append({
                "seed": seed, "fold": sp.name, "n_truth": r_base["n_truth"],
                "min_dist_hidden_to_known_px": float(sp.min_dist_hidden_to_known),
                "base": r_base, "tau_cell": float(metric.inclusion_threshold(r_base["dti"])),
                "budget": budget, "n_eligible_add": add["info"]["n_eligible"],
                "n_eligible_ctrl": ctrl["info"]["n_eligible"],
                "added": {"dots": n_add, "marginal_tp": r_add["tp"] - r_base["tp"],
                          "credit_per_dot": ((r_add["tp"] - r_base["tp"]) / n_add
                                             if n_add else None),
                          "dti_union": r_add["dti"]},
                "control": {"dots": n_ctrl, "marginal_tp": r_ctrl["tp"] - r_base["tp"],
                            "credit_per_dot": ((r_ctrl["tp"] - r_base["tp"]) / n_ctrl
                                               if n_ctrl else None),
                            "dti_union": r_ctrl["dti"]},
                "base_farfield_abs_credit_per_dot": (
                    losfo.credit_on(far, hidden) / int(far.sum()) if far.any() else None),
            })
        n_seed_cells = sum(1 for c in cells if c["seed"] == seed)
        print(f"seed {seed} done: {n_seed_cells} cells (t={time.time() - t0:.0f}s)", flush=True)

    if not cells:
        raise SystemExit("no evaluation cells produced")

    def seed_mean(key: str, seed: int) -> float | None:
        vals = [c[key]["credit_per_dot"] for c in cells
                if c["seed"] == seed and c[key]["credit_per_dot"] is not None]
        return float(np.mean(vals)) if vals else None

    def fold_mean(key: str, name: str) -> float | None:
        vals = [c[key]["credit_per_dot"] for c in cells
                if c["fold"] == name and c[key]["credit_per_dot"] is not None]
        return float(np.mean(vals)) if vals else None

    def pooled(key: str) -> float | None:
        num = sum(c[key]["marginal_tp"] for c in cells)
        den = sum(c[key]["dots"] for c in cells)
        return float(num / den) if den else None

    seed_means = {s: seed_mean("added", s) for s in seeds}
    fold_means = {fn: fold_mean("added", fn) for fn in FOLD_NAMES}
    ctrl_seed_means = {s: seed_mean("control", s) for s in seeds}
    mean_over_seeds = float(np.mean([v for v in seed_means.values() if v is not None])) \
        if any(v is not None for v in seed_means.values()) else None
    seeds_won = sum(1 for v in seed_means.values() if v is not None and v > tau_live)
    folds_won = sum(1 for v in fold_means.values() if v is not None and v > tau_live)
    pooled_add, pooled_ctrl = pooled("added"), pooled("control")
    n_nonempty = len(cells)
    coverage = sum(1 for c in cells if c["added"]["dots"] >= 10) / n_nonempty

    criteria = {
        "c1_mean_over_seed_means_gt_tau_live": bool(
            mean_over_seeds is not None and mean_over_seeds > tau_live),
        "c2_seeds_won_ge_8": bool(seeds_won >= 8),
        "c3_folds_won_ge_3": bool(folds_won >= 3),
        "c4_pooled_added_gt_pooled_control": bool(
            pooled_add is not None and pooled_ctrl is not None and pooled_add > pooled_ctrl),
        "c5_coverage_ge_half": bool(coverage >= 0.5),
        "c6_integrity_asserted_in_runner": True,  # any violation raises before this line
    }
    gate_passed = bool(all(criteria.values()))

    out = {
        "hypothesis": "H35-4: buried range-front gravity bench ADD (grav_hg bench x low scarp "
                      "x low relief, mesa shared floor, grav-ranked)",
        "preregistration": "knowledge/26_preregistration_H35-4.md",
        "preregistration_sha256": prereg_sha,
        "code_sha256": {
            "gravity_bench": hashlib.sha256(
                (paths.REPO / "src" / "gems27" / "gravity_bench.py").read_bytes()).hexdigest(),
            "hydrothermal": hashlib.sha256(
                (paths.REPO / "src" / "gems27" / "hydrothermal.py").read_bytes()).hexdigest(),
            "runner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seeds": seeds,
        "live_anchor": LIVE_ANCHOR,
        "tau_live": tau_live,
        "bench_inputs": {
            "bench_px": legs["bench_px"], "mesa_px": legs["mesa_px"],
            "bench_frac_of_footprint": legs["bench_frac_of_footprint"],
            "mesa_frac_of_footprint": legs["mesa_frac_of_footprint"],
            "grav_p75_cut": legs["grav_cut"], "step_p50_cut": legs["step_cut"],
            "relief_p50_cut": legs["relief_cut"], "step_p90_cut": legs["step_hi_cut"],
            "tmi_p90_cut": legs["tmi_hi_cut"], "grav_p50_cut": legs["grav_lo_cut"],
            "training_bands": legs["training_bands"], "lidar_bands": legs["lidar_bands"],
            "budget_frac": gravity_bench.BUDGET_FRAC, "thin_d": H.THIN_D, "far_px": H.FAR_PX,
        },
        "cells": cells,
        "skipped_cells": skipped,
        "summary": {
            "n_cells": n_nonempty,
            "mean_over_seed_means_added_cpd": mean_over_seeds,
            "seed_means_added_cpd": {str(k): v for k, v in seed_means.items()},
            "fold_means_added_cpd": fold_means,
            "seed_means_control_cpd": {str(k): v for k, v in ctrl_seed_means.items()},
            "seeds_won": seeds_won, "n_seeds": len(seeds),
            "folds_won": folds_won,
            "pooled_added_cpd": pooled_add, "pooled_control_cpd": pooled_ctrl,
            "total_added_dots": sum(c["added"]["dots"] for c in cells),
            "total_added_marginal_tp": sum(c["added"]["marginal_tp"] for c in cells),
            "total_control_dots": sum(c["control"]["dots"] for c in cells),
            "total_control_marginal_tp": sum(c["control"]["marginal_tp"] for c in cells),
            "coverage_frac_cells_ge_10_added": coverage,
        },
        "criteria": criteria,
        "gate_passed": gate_passed,
        "seconds": time.time() - t0,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")
    print(f"\nH35-4 gate: {'PASS' if gate_passed else 'FAIL'} "
          f"(mean c/d {mean_over_seeds} vs tau_live {tau_live:.5f}; "
          f"seeds {seeds_won}/{len(seeds)}; folds {folds_won}/4; "
          f"pooled add {pooled_add} vs ctrl {pooled_ctrl}; coverage {coverage:.2f})")
    print(f"written {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
