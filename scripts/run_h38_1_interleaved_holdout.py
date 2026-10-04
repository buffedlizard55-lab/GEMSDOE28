#!/usr/bin/env python3
"""Evaluate H38 conductive heat-flow residual & shallow SI=0 Euler lineament arms on interleaved holdout.

Runs on fresh seeds 270-279 (10 seeds x 4 quadrant folds = 40 paired cells) and includes an
automated same-seed integrity check on spent seed 240 against ``evidence/h36_1_holdout.json``.
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
from gems27 import grid, heatflow_euler, holdout, metric, oof_detector, paths  # noqa: E402

SEEDS_DEFAULT = list(range(270, 280))
TAU_LIVE = 0.2 * 0.2600 / (1.0 - 0.2 * 0.2600)


def _eval_mask(pred: np.ndarray, g: np.ndarray, k_pt: np.ndarray, n_g: int) -> dict:
    n_p = int(pred.sum())
    if n_p == 0 or n_g == 0:
        return {"tp": 0.0, "fp": float(n_p), "dti": 0.0, "dots": n_p, "n_truth": n_g}
    tp = float(metric.kernel_from_distance(distance_transform_edt(~pred)[g]).sum())
    fp = float((1.0 - k_pt[pred]).sum())
    dti = tp / (tp + metric.ALPHA * fp + metric.BETA * (n_g - tp) + metric.EPS)
    return {"tp": tp, "fp": fp, "dti": dti, "dots": n_p, "n_truth": n_g}


def _eval_seed(
    seed: int,
    labels: np.ndarray,
    fold: np.ndarray,
    oof_prob: np.ndarray,
    ridge_all: np.ndarray,
    fields: dict,
) -> dict:
    per_cell: dict = {}
    for f in range(4):
        sp = holdout.make_split(labels, fold, f, seed)
        fm = sp.fold_mask
        sl = holdout.crop(None, fm)
        hid, kn, fmc = sp.hidden[sl], (sp.known & fm)[sl], fm[sl]
        g = hid & fmc & ~kn
        active = fmc & ~kn
        n_g = int(g.sum())
        k_pt = metric.kernel_from_distance(distance_transform_edt(~g))
        blind_r1 = distance_transform_edt(~kn) <= 1.0

        base_d28 = (
            oof_detector.build_oof_dotted_base(
                oof_prob[sl],
                ridge_all[sl],
                fmc,
                kn,
                budget_frac=oof_detector.PRE_THIN_FRAC,
                thin_d=2.8,
            )
            & active
        )
        rung30 = (
            oof_detector.build_oof_dotted_base(
                oof_prob[sl],
                ridge_all[sl],
                fmc,
                kn,
                budget_frac=oof_detector.PRE_THIN_FRAC,
                thin_d=3.0,
            )
            & active
        )
        r30_r1 = (rung30 & ~blind_r1) & active

        r_base = _eval_mask(base_d28, g, k_pt, n_g)
        r_r30_r1 = _eval_mask(r30_r1, g, k_pt, n_g)

        specs = [
            (
                "h38_1_joint",
                base_d28,
                r_base,
                fields["joint_mask"][sl],
                fields["score_mult"][sl],
                10_000,
            ),
            (
                "h38_1a_heatflow",
                base_d28,
                r_base,
                fields["hf_halo"][sl],
                None,
                20_000,
            ),
            (
                "h38_1b_euler_lineament",
                base_d28,
                r_base,
                fields["euler_halo"][sl],
                None,
                30_000,
            ),
            (
                "h38_2_low_relief_euler",
                base_d28,
                r_base,
                fields["low_relief_euler_mask"][sl],
                None,
                40_000,
            ),
            (
                "h38_1_joint_on_r30_r1",
                r30_r1,
                r_r30_r1,
                fields["joint_mask"][sl],
                fields["score_mult"][sl],
                50_000,
            ),
        ]

        arms_cell: dict = {}
        for name, ref_mask, r_ref, cond_c, mult_c, offset in specs:
            sel = heatflow_euler.select_corroborated_ridge_dots(
                oof_prob[sl],
                ridge_all[sl],
                active,
                ref_mask,
                kn,
                cond_c,
                score_mult=mult_c,
                k_cap=heatflow_euler.K_CAP_PER_CELL,
                min_dist_base=heatflow_euler.MIN_DIST_BASE_PX,
                min_dist_known=heatflow_euler.MIN_DIST_KNOWN_PX,
                thin_d=heatflow_euler.THIN_D_PX,
                rng_seed=offset + seed * 10 + f,
            )
            r_arm = _eval_mask(ref_mask | sel["added"], g, k_pt, n_g)
            r_sub = _eval_mask(ref_mask | sel["control_sub_ridge"], g, k_pt, n_g)
            r_ran = _eval_mask(ref_mask | sel["control_random"], g, k_pt, n_g)
            arms_cell[name] = {
                "added_dots": sel["n_added"],
                "control_sub_ridge_dots": sel["n_control_sub_ridge"],
                "control_random_dots": sel["n_control_random"],
                "ref": r_ref,
                "arm": r_arm,
                "control_sub_ridge": r_sub,
                "control_random": r_ran,
                "delta_tp_arm": float(r_arm["tp"] - r_ref["tp"]),
                "delta_tp_sub_ridge": float(r_sub["tp"] - r_ref["tp"]),
                "delta_tp_random": float(r_ran["tp"] - r_ref["tp"]),
                "delta_dti_arm": float(r_arm["dti"] - r_ref["dti"]),
                "delta_dti_sub_ridge": float(r_sub["dti"] - r_ref["dti"]),
                "delta_dti_random": float(r_ran["dti"] - r_ref["dti"]),
                "delta_dti_vs_sub_ridge": float(r_arm["dti"] - r_sub["dti"]),
                "delta_dti_vs_random": float(r_arm["dti"] - r_ran["dti"]),
            }
        per_cell[sp.name] = {
            "base_d28": r_base,
            "rung30_blind_r1": r_r30_r1,
            "arms": arms_cell,
        }
    return per_cell


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="270-279")
    ap.add_argument("--out", default=str(paths.EVIDENCE / "h38_1_interleaved_holdout.json"))
    args = ap.parse_args()

    a, _, b = args.seeds.partition("-")
    seeds = list(range(int(a), int(b) + 1)) if b else [int(a)]
    t0 = time.time()

    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)
    fields = heatflow_euler.build_corroboration_fields(
        foot,
        hf_json_path=paths.SB_HEAT_FLOW_JSON,
        euler_csv_path=paths.EULER_CLUSTERS_CSV,
        lidar_path=paths.LIDAR,
    )

    oof_prob = oof_detector.fit_predict_oof_probabilities(foot, labels, fold)
    ridge_all = oof_detector.ridge_nms(oof_prob, foot, sigma=1.0)

    # Same-seed integrity check on spent seed 240 against evidence/h36_1_holdout.json
    ref_240 = _eval_seed(240, labels, fold, oof_prob, ridge_all, fields)
    h36_ref_path = paths.EVIDENCE / "h36_1_holdout.json"
    integrity_240 = {
        "seed": 240,
        "base_d28_mean_dti": float(
            np.mean([ref_240[fn]["base_d28"]["dti"] for fn in holdout.FOLD_NAMES])
        ),
        "rung30_blind_r1_mean_dti": float(
            np.mean([ref_240[fn]["rung30_blind_r1"]["dti"] for fn in holdout.FOLD_NAMES])
        ),
    }
    if h36_ref_path.is_file():
        h36_ref = json.loads(h36_ref_path.read_text())
        s240_gain_now = float(
            integrity_240["rung30_blind_r1_mean_dti"] - integrity_240["base_d28_mean_dti"]
        )
        min_g = float(h36_ref["variants"]["rung30_blind_r1"]["min_seed_gain"])
        max_g = float(h36_ref["variants"]["rung30_blind_r1"]["max_seed_gain"])
        integrity_240["now_rung30_blind_r1_gain"] = s240_gain_now
        integrity_240["ref_min_seed_gain"] = min_g
        integrity_240["ref_max_seed_gain"] = max_g
        assert min_g - 1e-12 <= s240_gain_now <= max_g + 1e-12, (
            f"Seed 240 gain {s240_gain_now} outside ref [{min_g}, {max_g}]"
        )

    per_seed_cells: dict = {}
    for s in seeds:
        per_seed_cells[str(s)] = _eval_seed(s, labels, fold, oof_prob, ridge_all, fields)
        print(f"interleaved seed {s} done (t={time.time() - t0:.1f}s)", flush=True)

    arm_names = (
        "h38_1_joint",
        "h38_1a_heatflow",
        "h38_1b_euler_lineament",
        "h38_2_low_relief_euler",
        "h38_1_joint_on_r30_r1",
    )
    arms_summary: dict = {}
    for name in arm_names:
        d_arm, d_sub, d_ran, d_vs_sub, d_vs_ran = [], [], [], [], []
        added_tot, sub_tot, ran_tot = 0, 0, 0
        tp_arm, tp_sub, tp_ran = 0.0, 0.0, 0.0
        seed_deltas: dict = {}
        fold_deltas = {fn: [] for fn in holdout.FOLD_NAMES}
        for s in seeds:
            sc = per_seed_cells[str(s)]
            s_d = []
            for fn in holdout.FOLD_NAMES:
                c = sc[fn]["arms"][name]
                d_arm.append(c["delta_dti_arm"])
                d_sub.append(c["delta_dti_sub_ridge"])
                d_ran.append(c["delta_dti_random"])
                d_vs_sub.append(c["delta_dti_vs_sub_ridge"])
                d_vs_ran.append(c["delta_dti_vs_random"])
                s_d.append(c["delta_dti_arm"])
                fold_deltas[fn].append(c["delta_dti_arm"])
                added_tot += c["added_dots"]
                sub_tot += c["control_sub_ridge_dots"]
                ran_tot += c["control_random_dots"]
                tp_arm += c["delta_tp_arm"]
                tp_sub += c["delta_tp_sub_ridge"]
                tp_ran += c["delta_tp_random"]
            seed_deltas[str(s)] = float(np.mean(s_d))
        arms_summary[name] = {
            "n_cells": len(d_arm),
            "added_dots_total": int(added_tot),
            "credit_per_added_dot_arm": float(tp_arm / max(1, added_tot)),
            "credit_per_added_dot_control_sub_ridge": float(tp_sub / max(1, sub_tot)),
            "credit_per_added_dot_control_random": float(tp_ran / max(1, ran_tot)),
            "mean_delta_dti_arm_vs_ref": float(np.mean(d_arm)),
            "mean_delta_dti_sub_ridge_vs_ref": float(np.mean(d_sub)),
            "mean_delta_dti_random_vs_ref": float(np.mean(d_ran)),
            "mean_delta_dti_arm_vs_sub_ridge": float(np.mean(d_vs_sub)),
            "mean_delta_dti_arm_vs_random": float(np.mean(d_vs_ran)),
            "cells_improved_vs_ref": int(sum(1 for v in d_arm if v > 0)),
            "cells_improved_vs_sub_ridge": int(sum(1 for v in d_vs_sub if v > 0)),
            "cells_improved_vs_random": int(sum(1 for v in d_vs_ran if v > 0)),
            "seeds_improved_vs_ref": int(sum(1 for v in seed_deltas.values() if v > 0)),
            "folds_improved_vs_ref": int(
                sum(1 for fn in holdout.FOLD_NAMES if float(np.mean(fold_deltas[fn])) > 0)
            ),
            "per_fold_mean_delta": {
                fn: float(np.mean(fold_deltas[fn])) for fn in holdout.FOLD_NAMES
            },
            "per_seed_mean_delta": seed_deltas,
        }
        a = arms_summary[name]
        print(
            f"Interleaved {name:24s}: dots={a['added_dots_total']:4d} "
            f"c/dot={a['credit_per_added_dot_arm']:.5f} "
            f"(sub={a['credit_per_added_dot_control_sub_ridge']:.5f}, "
            f"rand={a['credit_per_added_dot_control_random']:.5f}) | "
            f"dDTI={a['mean_delta_dti_arm_vs_ref']:+.6f} "
            f"({a['cells_improved_vs_ref']}/{a['n_cells']} cells, "
            f"{a['seeds_improved_vs_ref']}/{len(seeds)} seeds, "
            f"{a['folds_improved_vs_ref']}/4 folds)",
            flush=True,
        )

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "preregistration": "knowledge/38_preregistration_H36_1_and_H38_farfield.md",
        "seeds": seeds,
        "n_cells": 4 * len(seeds),
        "tau_live_0_2600": TAU_LIVE,
        "integrity_seed_240": integrity_240,
        "fields_meta": fields["meta"],
        "arms": arms_summary,
        "code_sha256": {
            "heatflow_euler": hashlib.sha256(
                (paths.REPO / "src" / "gems27" / "heatflow_euler.py").read_bytes()
            ).hexdigest(),
            "runner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "seconds": time.time() - t0,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=2) + "\n")
    print(f"written {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
