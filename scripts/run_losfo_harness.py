#!/usr/bin/env python3
"""Run the leave-fault-system-out (LOSFO) far-field diagnostic.

This is a **measurement instrument, not a promotion gate.** It does not spend a weekly submission
slot and it does not consume a hypothesis-gate decade in the sense of `knowledge/03`; it is given a
dedicated seed decade (default 210-214) so it can be re-run and audited like any other evidence file.

What it measures
----------------
The repository's standing holdout (`src/gems27/holdout.py`) hides 20 % of catalogue components
*interleaved* with the known catalogue. `evidence/arm_habitat_decomposition.json` showed 100 % of
that hidden truth lies at distance 0 from the full catalogue, so it cannot see the far field. This
script runs the **same held-out fault systems** through two detectors that differ in exactly one
respect:

  * `losfo`    - trained on the catalogue with a 600 m buffer around every held-out system erased
                 (`src/gems27/losfo.masked_labels`). To score on the truth it must detect the fault
                 from the physics in the 32 label-free bands.
  * `leaky`    - trained on the unmasked catalogue, so mapped faults remain visible right up to the
                 held-out trace. To score on the truth it only has to learn "emit near mapped
                 faults".

The ratio `credit_losfo / credit_leaky` on identical truth is the quantitative form of the standing
caveat "catalogue-internal truth overstates real-world enrichment". A ratio near 1 would mean the
interleaved protocol was already an honest far-field test; a ratio well below 1 measures exactly how
much of every previous gate result was catalogue interpolation.

It also reports the far-field habitat split of the truth and of the emitted dots, which is the check
that the protocol did what it claims.

Nothing here contacts drivendata.org or any network host.

Usage
-----
    python scripts/run_losfo_harness.py --seeds 210-214 \
        --out evidence/losfo_farfield_diagnostic.json
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import (  # noqa: E402
    grid,
    heatflow_euler,
    holdout,
    losfo,
    metric,
    oof_detector,
    packing,
    paths,
    thinning,
)

FOLD_NAMES = holdout.FOLD_NAMES


def ridge_candidate_pool(prob: np.ndarray, ridge: np.ndarray, fold_mask: np.ndarray,
                         known: np.ndarray, budget_frac: float) -> np.ndarray:
    """The exact candidate pool ``build_oof_dotted_base`` packs: top-budget ridge pixels."""
    active = fold_mask & ~known
    cand = ridge & active
    k = int(round(budget_frac * int(fold_mask.sum())))
    ys, xs = np.nonzero(cand)
    pool = np.zeros_like(cand)
    if len(ys) == 0 or k <= 0:
        return pool
    if len(ys) > k:
        sc = prob[ys, xs]
        top = np.argpartition(-sc, k - 1)[:k]
        ys, xs = ys[top], xs[top]
    pool[ys, xs] = True
    return pool


def packing_arms(prob: np.ndarray, ridge: np.ndarray, fold_mask: np.ndarray, known: np.ndarray,
                 base: np.ndarray, active: np.ndarray, hidden: np.ndarray, n_target: int,
                 thin_d: float, seed: int) -> dict:
    """Pack the same candidate pool by evidence, at random, and by max coverage, at matched N."""
    pool = ridge_candidate_pool(prob, ridge, fold_mask, known, oof_detector.PRE_THIN_FRAC)
    if not np.array_equal(thinning.dot_thin(pool, thin_d) & active, base & active):
        raise SystemExit("pool equivalence check failed: the replica does not reproduce the base arm")
    weight = np.where(active, prob, 0.0).astype(np.float32)
    out = {"base": {"coverage": packing.coverage_of(base & active, weight),
                    "requested_n": int(n_target), "n_candidates": int(pool.sum())}}
    for name, sel in (
        ("prob_order", packing.prob_order_pack(prob, pool, n_target=n_target, min_dist=thin_d)),
        ("random_order", packing.random_order_pack(pool, n_target=n_target, min_dist=thin_d,
                                                   seed=seed)),
        ("max_coverage", packing.coverage_greedy(pool, prob, n_target)),
    ):
        s = sel & active
        out[name] = {"coverage": packing.coverage_of(s, weight), **eval_set(s, hidden, active)}
    return out


def eval_set(pred: np.ndarray, truth: np.ndarray, active: np.ndarray) -> dict:
    """DTI of a binary emission against a truth set, restricted to `active` cells."""
    p = pred & active
    n_g = int(truth.sum())
    if n_g == 0:
        return {"tp": 0.0, "fp": float(p.sum()), "dti": 0.0, "dots": int(p.sum()), "n_truth": 0}
    tp = float(metric.kernel_from_distance(distance_transform_edt(~p)[truth]).sum())
    fp = float((1.0 - metric.kernel_from_distance(distance_transform_edt(~truth))[p]).sum())
    dti = tp / (tp + metric.ALPHA * fp + metric.BETA * (n_g - tp) + metric.EPS)
    return {"tp": tp, "fp": fp, "dti": dti, "dots": int(p.sum()), "n_truth": n_g}


def load_licence_mask(csv_path, shape, mad_max=60.0, depth_max=400.0, n_min=8):
    """H37-3 licence: SI-0 depth-coherent clusters -> one candidate pixel each, on the full grid.

    Thresholds are frozen in knowledge/34_preregistration_H37-3_licence.md; changing them is a
    preregistration deviation and must be declared in the result write-up.
    """
    mask = np.zeros(shape, dtype=bool)
    rows, cols, kept = [], [], 0
    with open(csv_path, newline="") as fh:
        for r in csv.DictReader(fh):
            if float(r["depth_mad_m"]) > mad_max:
                continue
            if float(r["median_depth_m"]) > depth_max:
                continue
            if int(r["n_solutions"]) < n_min:
                continue
            y, x = int(round(float(r["row"]))), int(round(float(r["col"])))
            if 0 <= y < shape[0] and 0 <= x < shape[1]:
                rows.append(y)
                cols.append(x)
                kept += 1
    mask[rows, cols] = True
    return mask, kept


def pack_licence_dots(candidates, base, min_dist):
    """Greedy independent set over `candidates` (raster order), spacing `min_dist` from `base`."""
    bys, bxs = np.nonzero(base)
    base_tree = cKDTree(np.column_stack([bys, bxs])) if bys.size else None
    ys, xs = np.nonzero(candidates)
    kept = []
    kept_tree = None
    for y, x in zip(ys, xs):
        if base_tree is not None and base_tree.query([y, x])[0] < min_dist:
            continue
        if kept_tree is not None and kept_tree.query([y, x])[0] < min_dist:
            continue
        kept.append((y, x))
        kept_tree = cKDTree(np.array(kept, dtype=float))
    out = np.zeros_like(candidates)
    if kept:
        ky, kx = np.array(kept).T
        out[ky, kx] = True
    return out


def random_matched_dots(pool, base, n_keep, min_dist, seed):
    """Same count, same spacing, same eligibility pool -- only the choosing rule is content-blind."""
    out = np.zeros_like(pool)
    if n_keep <= 0:
        return out
    ys, xs = np.nonzero(pool)
    rng = np.random.default_rng(seed)
    order = rng.permutation(len(ys))
    bys, bxs = np.nonzero(base)
    base_tree = cKDTree(np.column_stack([bys, bxs])) if bys.size else None
    kept = []
    for i in order:
        y, x = ys[i], xs[i]
        if base_tree is not None and base_tree.query([y, x])[0] < min_dist:
            continue
        if kept:
            ktree = cKDTree(np.array(kept, dtype=float))
            if ktree.query([y, x])[0] < min_dist:
                continue
        kept.append((y, x))
        if len(kept) >= n_keep:
            break
    if kept:
        out[tuple(np.array(kept).T)] = True
    return out


def _random_drop_to_n(base: np.ndarray, n_keep: int, seed: int) -> np.ndarray:
    """Content-blind random deletion from ``base`` down to exact count ``n_keep``."""
    out = np.zeros_like(base, dtype=bool)
    ys, xs = np.nonzero(base)
    if len(ys) == 0 or n_keep <= 0:
        return out
    if len(ys) <= n_keep:
        return base.copy()
    rng = np.random.default_rng(seed)
    keep = rng.choice(len(ys), size=int(n_keep), replace=False)
    out[ys[keep], xs[keep]] = True
    return out


def h36_1_farfield_arms(
    prob: np.ndarray,
    ridge: np.ndarray,
    fold_mask: np.ndarray,
    known: np.ndarray,
    base_d28: np.ndarray,
    active: np.ndarray,
    hidden: np.ndarray,
    seed: int,
    f: int,
) -> dict:
    """Evaluate H36-1 spacing + flank-suppression arms and matched-N random drop controls."""
    blind_r1 = distance_transform_edt(~known) <= 1.0
    h27_4_r1 = (base_d28 & ~blind_r1) & active
    rung30 = (
        oof_detector.build_oof_dotted_base(
            prob,
            ridge,
            fold_mask,
            known,
            budget_frac=oof_detector.PRE_THIN_FRAC,
            thin_d=3.0,
        )
        & active
    )
    rung30_r1 = (rung30 & ~blind_r1) & active
    n_r30 = int(rung30.sum())
    n_r30_r1 = int(rung30_r1.sum())
    rand_n = _random_drop_to_n(base_d28, n_r30, 910_000 + 10 * seed + f) & active
    rand_r1 = _random_drop_to_n(base_d28, n_r30_r1, 920_000 + 10 * seed + f) & active

    r_base = eval_set(base_d28, hidden, active)
    r_h27 = eval_set(h27_4_r1, hidden, active)
    r_r30 = eval_set(rung30, hidden, active)
    r_r30_r1 = eval_set(rung30_r1, hidden, active)
    r_randn = eval_set(rand_n, hidden, active)
    r_randr1 = eval_set(rand_r1, hidden, active)

    dtp_r30 = float(r_base["tp"] - r_r30["tp"])
    dfp_r30 = float(r_base["fp"] - r_r30["fp"])
    dtp_r30_r1 = float(r_base["tp"] - r_r30_r1["tp"])
    dfp_r30_r1 = float(r_base["fp"] - r_r30_r1["fp"])
    dtp_h27 = float(r_base["tp"] - r_h27["tp"])
    dfp_h27 = float(r_base["fp"] - r_h27["fp"])

    return {
        "base": r_base,
        "h27_4_blind_r1_d280": r_h27,
        "rung30_unpruned": r_r30,
        "rung30_blind_r1": r_r30_r1,
        "control_random_drop_matched_n": r_randn,
        "control_random_drop_matched_r1": r_randr1,
        "e_far_rung30": float(dtp_r30 / max(1e-9, dfp_r30)),
        "e_far_rung30_blind_r1": float(dtp_r30_r1 / max(1e-9, dfp_r30_r1)),
        "e_far_h27_4_blind_r1": float(dtp_h27 / max(1e-9, dfp_h27)),
    }


def h38_corroboration_arms(
    prob: np.ndarray,
    ridge: np.ndarray,
    fold_mask: np.ndarray,
    known: np.ndarray,
    base_d28: np.ndarray,
    active: np.ndarray,
    hidden: np.ndarray,
    fields: dict,
    sl: tuple,
    seed: int,
    f: int,
    r_base: dict,
) -> dict:
    """Evaluate H38 conductive heat-flow residual & shallow SI=0 Euler lineament arms."""
    blind_r1 = distance_transform_edt(~known) <= 1.0
    rung30 = (
        oof_detector.build_oof_dotted_base(
            prob,
            ridge,
            fold_mask,
            known,
            budget_frac=oof_detector.PRE_THIN_FRAC,
            thin_d=3.0,
        )
        & active
    )
    rung30_r1 = (rung30 & ~blind_r1) & active
    r_r30_r1 = eval_set(rung30_r1, hidden, active)

    arm_specs = [
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
            rung30_r1,
            r_r30_r1,
            fields["joint_mask"][sl],
            fields["score_mult"][sl],
            50_000,
        ),
    ]

    out: dict = {}
    for name, ref_mask, r_ref, cond_c, mult_c, offset in arm_specs:
        sel = heatflow_euler.select_corroborated_ridge_dots(
            prob,
            ridge,
            active,
            ref_mask,
            known,
            cond_c,
            score_mult=mult_c,
            k_cap=heatflow_euler.K_CAP_PER_CELL,
            min_dist_base=heatflow_euler.MIN_DIST_BASE_PX,
            min_dist_known=heatflow_euler.MIN_DIST_KNOWN_PX,
            thin_d=heatflow_euler.THIN_D_PX,
            rng_seed=offset + seed * 10 + f,
        )
        r_arm = eval_set(ref_mask | sel["added"], hidden, active)
        r_sub = eval_set(ref_mask | sel["control_sub_ridge"], hidden, active)
        r_ran = eval_set(ref_mask | sel["control_random"], hidden, active)
        out[name] = {
            "n_sub_pool": sel["n_sub_pool"],
            "n_eligible": sel["n_eligible"],
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
    return out


def summarize_h36_1_farfield(cells: list[dict], tau_live: float = 0.054852) -> dict:
    """Summarize H36-1 spacing + flank-suppression results across all LOSFO cells."""
    rows = [c for c in cells if c.get("h36_1")]
    if not rows:
        return {}
    out: dict = {
        "preregistration": "knowledge/38_preregistration_H36_1_and_H38_farfield.md",
        "tau_live_bar": float(tau_live),
        "n_cells": len(rows),
        "detectors": {},
    }
    arm_names = (
        "base",
        "h27_4_blind_r1_d280",
        "rung30_unpruned",
        "rung30_blind_r1",
        "control_random_drop_matched_n",
        "control_random_drop_matched_r1",
    )
    for det in ("losfo", "leaky"):
        arms_agg = {}
        for name in arm_names:
            tp = sum(c["h36_1"][det][name]["tp"] for c in rows)
            fp = sum(c["h36_1"][det][name]["fp"] for c in rows)
            ng = sum(c["h36_1"][det][name]["n_truth"] for c in rows)
            dots = sum(c["h36_1"][det][name]["dots"] for c in rows)
            dtis = [c["h36_1"][det][name]["dti"] for c in rows]
            arms_agg[name] = {
                "mean_dti": float(np.mean(dtis)),
                "sum_tp": float(tp),
                "sum_fp": float(fp),
                "sum_n_truth": int(ng),
                "pooled_dti": float(
                    tp / (tp + metric.ALPHA * fp + metric.BETA * (ng - tp) + metric.EPS)
                ),
                "credit_per_dot": float(tp / max(1, dots)),
                "mean_dots": float(dots / max(1, len(rows))),
                "recall_w": float(tp / ng) if ng else 0.0,
            }

        d_f1 = [
            c["h36_1"][det]["rung30_unpruned"]["dti"]
            - c["h36_1"][det]["control_random_drop_matched_n"]["dti"]
            for c in rows
        ]
        d_r30_base = [
            c["h36_1"][det]["rung30_unpruned"]["dti"] - c["h36_1"][det]["base"]["dti"]
            for c in rows
        ]
        d_r30_r1_base = [
            c["h36_1"][det]["rung30_blind_r1"]["dti"] - c["h36_1"][det]["base"]["dti"]
            for c in rows
        ]
        d_r30_r1_ctrl = [
            c["h36_1"][det]["rung30_blind_r1"]["dti"]
            - c["h36_1"][det]["control_random_drop_matched_r1"]["dti"]
            for c in rows
        ]
        d_h27_base = [
            c["h36_1"][det]["h27_4_blind_r1_d280"]["dti"] - c["h36_1"][det]["base"]["dti"]
            for c in rows
        ]

        dtp_r30 = float(arms_agg["base"]["sum_tp"] - arms_agg["rung30_unpruned"]["sum_tp"])
        dfp_r30 = float(arms_agg["base"]["sum_fp"] - arms_agg["rung30_unpruned"]["sum_fp"])
        dtp_r30_r1 = float(arms_agg["base"]["sum_tp"] - arms_agg["rung30_blind_r1"]["sum_tp"])
        dfp_r30_r1 = float(arms_agg["base"]["sum_fp"] - arms_agg["rung30_blind_r1"]["sum_fp"])
        dtp_h27 = float(
            arms_agg["base"]["sum_tp"] - arms_agg["h27_4_blind_r1_d280"]["sum_tp"]
        )
        dfp_h27 = float(
            arms_agg["base"]["sum_fp"] - arms_agg["h27_4_blind_r1_d280"]["sum_fp"]
        )

        seeds_set = sorted({c["seed"] for c in rows})
        per_seed_f1 = {
            str(s): float(
                np.mean(
                    [
                        c["h36_1"][det]["rung30_unpruned"]["dti"]
                        - c["h36_1"][det]["control_random_drop_matched_n"]["dti"]
                        for c in rows
                        if c["seed"] == s
                    ]
                )
            )
            for s in seeds_set
        }
        per_seed_r30_r1 = {
            str(s): float(
                np.mean(
                    [
                        c["h36_1"][det]["rung30_blind_r1"]["dti"]
                        - c["h36_1"][det]["base"]["dti"]
                        for c in rows
                        if c["seed"] == s
                    ]
                )
            )
            for s in seeds_set
        }

        out["detectors"][det] = {
            "arms": arms_agg,
            "F1_rung30_vs_matched_random": {
                "mean_delta_dti": float(np.mean(d_f1)),
                "cells_improved": int(sum(1 for v in d_f1 if v > 0)),
                "seeds_improved": int(sum(1 for v in per_seed_f1.values() if v > 0)),
                "per_seed_delta": per_seed_f1,
            },
            "F2_rung30_removal_efficiency": {
                "mean_delta_dti_vs_base": float(np.mean(d_r30_base)),
                "sum_tp_removed": dtp_r30,
                "sum_fp_removed": dfp_r30,
                "pooled_e_far": float(dtp_r30 / max(1e-9, dfp_r30)),
                "cells_e_far_below_tau_live": int(
                    sum(1 for c in rows if c["h36_1"][det]["e_far_rung30"] < tau_live)
                ),
                "passes_tau_live": bool(float(dtp_r30 / max(1e-9, dfp_r30)) < tau_live),
            },
            "F3_rung30_blind_r1_vs_base": {
                "mean_delta_dti_vs_base": float(np.mean(d_r30_r1_base)),
                "mean_delta_dti_vs_matched_random": float(np.mean(d_r30_r1_ctrl)),
                "cells_improved_vs_base": int(sum(1 for v in d_r30_r1_base if v > 0)),
                "cells_improved_vs_matched_random": int(
                    sum(1 for v in d_r30_r1_ctrl if v > 0)
                ),
                "seeds_improved_vs_base": int(
                    sum(1 for v in per_seed_r30_r1.values() if v > 0)
                ),
                "per_seed_delta_vs_base": per_seed_r30_r1,
                "sum_tp_removed": dtp_r30_r1,
                "sum_fp_removed": dfp_r30_r1,
                "pooled_e_far": float(dtp_r30_r1 / max(1e-9, dfp_r30_r1)),
                "cells_e_far_below_tau_live": int(
                    sum(
                        1
                        for c in rows
                        if c["h36_1"][det]["e_far_rung30_blind_r1"] < tau_live
                    )
                ),
            },
            "F4_h27_4_blind_r1_vs_base": {
                "mean_delta_dti_vs_base": float(np.mean(d_h27_base)),
                "cells_improved_vs_base": int(sum(1 for v in d_h27_base if v > 0)),
                "sum_tp_removed": dtp_h27,
                "sum_fp_removed": dfp_h27,
                "pooled_e_far": float(dtp_h27 / max(1e-9, dfp_h27)),
                "exact_zero_tp_loss_all_cells": bool(abs(dtp_h27) < 1e-9),
            },
        }
    return out


def summarize_h38_corroboration(
    cells: list[dict], fields_meta: dict, tau_live: float = 0.054852
) -> dict:
    """Summarize H38 multi-physics corroboration arms across all LOSFO cells."""
    rows = [c for c in cells if c.get("h38")]
    if not rows:
        return {}
    arm_names = (
        "h38_1_joint",
        "h38_1a_heatflow",
        "h38_1b_euler_lineament",
        "h38_2_low_relief_euler",
        "h38_1_joint_on_r30_r1",
    )
    seeds_set = sorted({c["seed"] for c in rows})
    arms_out = {}
    for name in arm_names:
        added = sum(c["h38"][name]["added_dots"] for c in rows)
        ctrl_sub = sum(c["h38"][name]["control_sub_ridge_dots"] for c in rows)
        ctrl_ran = sum(c["h38"][name]["control_random_dots"] for c in rows)
        tp_arm = sum(c["h38"][name]["delta_tp_arm"] for c in rows)
        tp_sub = sum(c["h38"][name]["delta_tp_sub_ridge"] for c in rows)
        tp_ran = sum(c["h38"][name]["delta_tp_random"] for c in rows)

        d_arm = [c["h38"][name]["delta_dti_arm"] for c in rows]
        d_sub = [c["h38"][name]["delta_dti_sub_ridge"] for c in rows]
        d_ran = [c["h38"][name]["delta_dti_random"] for c in rows]
        d_vs_sub = [c["h38"][name]["delta_dti_vs_sub_ridge"] for c in rows]
        d_vs_ran = [c["h38"][name]["delta_dti_vs_random"] for c in rows]

        per_seed = {
            str(s): float(
                np.mean([c["h38"][name]["delta_dti_arm"] for c in rows if c["seed"] == s])
            )
            for s in seeds_set
        }
        per_fold = {}
        for fn in FOLD_NAMES:
            f_rows = [c for c in rows if c["fold"] == fn]
            per_fold[fn] = {
                "mean_delta_dti_arm": (
                    float(np.mean([c["h38"][name]["delta_dti_arm"] for c in f_rows]))
                    if f_rows
                    else 0.0
                ),
                "credit_per_added_dot": float(
                    sum(c["h38"][name]["delta_tp_arm"] for c in f_rows)
                    / max(1, sum(c["h38"][name]["added_dots"] for c in f_rows))
                ),
                "added_dots": int(sum(c["h38"][name]["added_dots"] for c in f_rows)),
            }

        c_per_dot_arm = float(tp_arm / max(1, added))
        c_per_dot_sub = float(tp_sub / max(1, ctrl_sub))
        c_per_dot_ran = float(tp_ran / max(1, ctrl_ran))
        dti_ref = float(np.mean([c["h38"][name]["ref"]["dti"] for c in rows]))
        tau_far = float(0.2 * dti_ref / (1.0 - 0.2 * dti_ref))

        req_cells = int(np.ceil(0.75 * len(rows)))
        req_seeds = int(np.ceil(0.80 * len(seeds_set)))
        c1_pass = (
            float(np.mean(d_arm)) > 0.0
            and sum(1 for v in d_arm if v > 0) >= req_cells
            and sum(1 for v in per_seed.values() if v > 0) >= req_seeds
        )
        c2_pass = c_per_dot_arm >= tau_live
        c3a_pass = c_per_dot_arm > c_per_dot_sub and float(np.mean(d_vs_sub)) > 0.0
        c3b_pass = (
            float(np.mean(d_vs_ran)) > 0.0 and sum(1 for v in d_vs_ran if v > 0) >= req_cells
        )

        arms_out[name] = {
            "n_cells": len(rows),
            "added_dots_total": int(added),
            "control_sub_ridge_dots_total": int(ctrl_sub),
            "control_random_dots_total": int(ctrl_ran),
            "mean_added_per_cell": float(added / max(1, len(rows))),
            "credit_per_added_dot_arm": c_per_dot_arm,
            "credit_per_added_dot_control_sub_ridge": c_per_dot_sub,
            "credit_per_added_dot_control_random": c_per_dot_ran,
            "tau_live_bar": float(tau_live),
            "tau_farfield_bar": tau_far,
            "mean_delta_dti_arm_vs_ref": float(np.mean(d_arm)),
            "mean_delta_dti_sub_ridge_vs_ref": float(np.mean(d_sub)),
            "mean_delta_dti_random_vs_ref": float(np.mean(d_ran)),
            "mean_delta_dti_arm_vs_sub_ridge": float(np.mean(d_vs_sub)),
            "mean_delta_dti_arm_vs_random": float(np.mean(d_vs_ran)),
            "cells_arm_improved_vs_ref": int(sum(1 for v in d_arm if v > 0)),
            "cells_arm_improved_vs_sub_ridge": int(sum(1 for v in d_vs_sub if v > 0)),
            "cells_arm_improved_vs_random": int(sum(1 for v in d_vs_ran if v > 0)),
            "seeds_arm_improved_vs_ref": int(sum(1 for v in per_seed.values() if v > 0)),
            "per_seed_delta_arm": per_seed,
            "per_fold": per_fold,
            "criteria": {
                "C1_transfer": bool(c1_pass),
                "C2_live_bar": bool(c2_pass),
                "C3a_beats_uncorroborated_sub_ridge": bool(c3a_pass),
                "C3b_beats_random_offcat": bool(c3b_pass),
                "ALL_PASS": bool(c1_pass and c2_pass and c3a_pass and c3b_pass),
            },
        }
    return {
        "preregistration": "knowledge/38_preregistration_H36_1_and_H38_farfield.md",
        "fields_meta": fields_meta,
        "arms": arms_out,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="210-214")
    ap.add_argument("--dilate-px", type=int, default=losfo.DEFAULT_DILATE_PX)
    ap.add_argument("--buffer-px", type=int, default=losfo.DEFAULT_BUFFER_PX)
    ap.add_argument("--thin-d", type=float, default=2.8, help="dot spacing of the evaluated arm")
    ap.add_argument("--out", default=str(paths.EVIDENCE / "losfo_farfield_diagnostic.json"))
    ap.add_argument("--euler-licence", default=None,
                    help="CSV of SI-0 Euler clusters; enables the H37-3 positive emission licence "
                         "arm (knowledge/34_preregistration_H37-3_licence.md)")
    ap.add_argument("--packing-variants", action="store_true",
                    help="also pack the same candidate pool by evidence / at random / by max "
                         "coverage at matched N, and score each on the identical far-field truth")
    ap.add_argument("--h36-1-farfield", action="store_true",
                    help="also evaluate the H36-1 spacing + flank-suppression arms "
                         "(rung30_unpruned, rung30_blind_r1, h27_4_blind_r1_d280, "
                         "control_random_drop_matched_n, control_random_drop_matched_r1)")
    ap.add_argument("--h38-corroboration", action="store_true",
                    help="also evaluate the Session 14 H38 conductive heat-flow residual & "
                         "shallow SI=0 Euler lineament corroboration arms")
    args = ap.parse_args()

    a, _, b = args.seeds.partition("-")
    seeds = list(range(int(a), int(b) + 1)) if b else [int(a)]
    t0 = time.time()

    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)

    h38_fields = None
    if args.h38_corroboration:
        h38_fields = heatflow_euler.build_corroboration_fields(
            foot,
            hf_json_path=paths.SB_HEAT_FLOW_JSON,
            euler_csv_path=paths.EULER_CLUSTERS_CSV,
            lidar_path=paths.LIDAR,
        )
        print(
            f"H38 corroboration fields built: hf_wells_in_foot="
            f"{h38_fields['meta']['heatflow']['n_in_footprint']}, "
            f"hf_above_50={h38_fields['meta']['heatflow']['n_records_above_cut']}, "
            f"euler_kept={h38_fields['meta']['euler']['n_kept_clusters']}",
            flush=True,
        )

    licence_mask = None
    licence_meta = None
    if args.euler_licence:
        licence_mask, n_cand = load_licence_mask(args.euler_licence, foot.shape)
        licence_meta = {
            "csv": str(args.euler_licence),
            "csv_sha256": hashlib.sha256(Path(args.euler_licence).read_bytes()).hexdigest(),
            "rule": "depth_mad_m <= 60 and median_depth_m <= 400 and n_solutions >= 8",
            "n_candidate_clusters": int(n_cand),
            "thin_d_px": args.thin_d,
        }
        print(f"H37-3 licence: {n_cand} candidate clusters from {args.euler_licence}", flush=True)

    sys_grid, n_sys = losfo.fault_systems(labels, args.dilate_px)
    tab = losfo.system_table(sys_grid, n_sys, foot)
    sizes = tab["n_px"]
    print(f"catalogue {int(labels.sum()):,} px in {n_sys:,} fault systems "
          f"(median {int(np.median(sizes))} px, max {int(sizes.max())} px)", flush=True)

    cells = []
    per_fold_summary = {fn: [] for fn in FOLD_NAMES}
    diag_meta = {}

    for seed in seeds:
        hold = losfo.assign_systems_to_folds(tab, fold, 4, seed=seed)
        n_held = int((hold >= 0).sum())
        masked = losfo.masked_labels(labels, sys_grid, hold, args.buffer_px)

        # Detector A: honest - the held-out systems and their buffer were never positive labels.
        prob_losfo = oof_detector.fit_predict_oof_probabilities(foot, masked, fold)
        ridge_losfo = oof_detector.ridge_nms(prob_losfo, foot, sigma=1.0)
        # Detector B: leaky control - same held-out truth, trained on the full catalogue.
        prob_leaky = oof_detector.fit_predict_oof_probabilities(foot, labels, fold)
        ridge_leaky = oof_detector.ridge_nms(prob_leaky, foot, sigma=1.0)

        diag_meta = {
            "n_systems": n_sys, "n_systems_held_out": n_held,
            "held_out_px": int(np.isin(sys_grid, np.flatnonzero(hold >= 0) + 1).sum()),
            "masked_label_px": int(masked.sum()), "full_label_px": int(labels.sum()),
            "dilate_px": args.dilate_px, "buffer_px": args.buffer_px,
        }

        for f in range(4):
            sp = losfo.build_losfo_split(labels, sys_grid, hold, fold, f, seed,
                                        FOLD_NAMES, args.buffer_px)
            if not sp.hidden.any():
                continue
            sl = holdout.crop(None, sp.fold_mask)
            fm = sp.fold_mask[sl]
            hidden = sp.hidden[sl]
            # The two protocols differ in the label set the detector saw; the *evaluated* active
            # region is identical so the comparison is paired cell for cell.
            active = fm & ~sp.known[sl]

            base_l = oof_detector.build_oof_dotted_base(
                prob_losfo[sl], ridge_losfo[sl], fm, sp.known[sl],
                budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=args.thin_d) & active
            base_k = oof_detector.build_oof_dotted_base(
                prob_leaky[sl], ridge_leaky[sl], fm, sp.known[sl],
                budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=args.thin_d) & active

            r_l = eval_set(base_l, hidden, active)
            r_k = eval_set(base_k, hidden, active)

            var_l = var_k = None
            if args.packing_variants:
                n_l = int(base_l.sum())
                n_k = int(base_k.sum())
                var_l = packing_arms(prob_losfo[sl], ridge_losfo[sl], fm, sp.known[sl], base_l,
                                     active, hidden, n_l, args.thin_d, seed * 4 + f)
                var_k = packing_arms(prob_leaky[sl], ridge_leaky[sl], fm, sp.known[sl], base_k,
                                     active, hidden, n_k, args.thin_d, seed * 4 + f)

            euler_block = None
            if licence_mask is not None:
                elig = licence_mask[sl] & active & ~base_l & ~sp.known[sl]
                lic = pack_licence_dots(elig, base_l, args.thin_d)
                rng_seed = seed * 4 + f + 1000
                rand = random_matched_dots(active & ~base_l & ~sp.known[sl], base_l,
                                           int(lic.sum()), args.thin_d, rng_seed)
                assert not (lic & base_l).any(), "licence overlaps the base emission"
                assert not (lic & sp.known[sl]).any(), "licence overlaps the catalogue"
                assert not (rand & base_l).any(), "random control overlaps the base emission"
                rl = eval_set(base_l | lic, hidden, active)
                rr = eval_set(base_l | rand, hidden, active)
                euler_block = {
                    "added_dots": int(lic.sum()), "control_dots": int(rand.sum()),
                    "eligible_px": int(elig.sum()),
                    "licence": rl, "random_control": rr,
                    "delta_tp_licence": float(rl["tp"] - r_l["tp"]),
                    "delta_tp_random": float(rr["tp"] - r_l["tp"]),
                    "delta_dti_licence": float(rl["dti"] - r_l["dti"]),
                    "delta_dti_random": float(rr["dti"] - r_l["dti"]),
                }

            # habitat check: is the truth actually far from what the detector could see?
            # (distance transform on the full grid, then cropped with everything else)
            d_known = distance_transform_edt(~sp.known)[sl]
            truth_dist = d_known[hidden]
            dot_dist_l = d_known[base_l] if base_l.any() else np.zeros(0)

            h36_block = None
            if args.h36_1_farfield:
                h36_block = {
                    "losfo": h36_1_farfield_arms(
                        prob_losfo[sl],
                        ridge_losfo[sl],
                        fm,
                        sp.known[sl],
                        base_l,
                        active,
                        hidden,
                        seed,
                        f,
                    ),
                    "leaky": h36_1_farfield_arms(
                        prob_leaky[sl],
                        ridge_leaky[sl],
                        fm,
                        sp.known[sl],
                        base_k,
                        active,
                        hidden,
                        seed,
                        f,
                    ),
                }

            h38_block = None
            if h38_fields is not None:
                h38_block = h38_corroboration_arms(
                    prob_losfo[sl],
                    ridge_losfo[sl],
                    fm,
                    sp.known[sl],
                    base_l,
                    active,
                    hidden,
                    h38_fields,
                    sl,
                    seed,
                    f,
                    r_l,
                )

            row = {
                "seed": seed, "fold": sp.name, "n_truth": r_l["n_truth"],
                "min_dist_truth_to_known_px": float(sp.min_dist_hidden_to_known),
                "median_dist_truth_to_known_px": float(np.median(truth_dist)),
                "losfo": r_l, "leaky": r_k,
                "dots_median_dist_to_known_px": (float(np.median(dot_dist_l))
                                                 if dot_dist_l.size else None),
                "frac_dots_ge_3px_from_known": (
                    float((dot_dist_l >= 3).mean()) if dot_dist_l.size else None),
                "packing": ({"losfo": var_l, "leaky": var_k} if var_l is not None else None),
                "euler": euler_block,
                "h36_1": h36_block,
                "h38": h38_block,
            }
            cells.append(row)
            per_fold_summary[sp.name].append(row)
        print(f"seed {seed} done (t={time.time() - t0:.0f}s)", flush=True)

    if not cells:
        raise SystemExit("no evaluation cells produced")

    def agg(key: str) -> dict:
        def get(c: dict, k: str) -> dict:
            if c.get("packing") and key.startswith(("losfo__", "leaky__")):
                arm, name = key.split("__", 1)
                return c["packing"][arm][name]
            return c[k]

        tp = sum(get(c, key)["tp"] for c in cells)
        fp = sum(get(c, key)["fp"] for c in cells)
        ng = sum(get(c, key)["n_truth"] for c in cells)
        dtis = [get(c, key)["dti"] for c in cells]
        return {
            "mean_dti": float(np.mean(dtis)), "sum_tp": float(tp), "sum_fp": float(fp),
            "sum_n_truth": int(ng), "pooled_dti": float(
                tp / (tp + metric.ALPHA * fp + metric.BETA * (ng - tp) + metric.EPS)),
            "credit_per_dot": float(tp / max(1, sum(get(c, key)["dots"] for c in cells))),
            "mean_dots": float(np.mean([get(c, key)["dots"] for c in cells])),
            "recall_w": float(tp / ng) if ng else 0.0,
        }

    euler_block_out = None
    if licence_mask is not None:
        rows = [c for c in cells if c.get("euler")]
        added = sum(c["euler"]["added_dots"] for c in rows)
        ctrl = sum(c["euler"]["control_dots"] for c in rows)
        d_lic = [c["euler"]["delta_dti_licence"] for c in rows]
        d_ran = [c["euler"]["delta_dti_random"] for c in rows]
        d_pp = [c["euler"]["delta_dti_licence"] - c["euler"]["delta_dti_random"] for c in rows]
        tp_lic = sum(c["euler"]["delta_tp_licence"] for c in rows)
        dti_base = float(np.mean([c["losfo"]["dti"] for c in rows]))
        euler_block_out = {
            "preregistration": "knowledge/34_preregistration_H37-3_licence.md",
            "input": licence_meta,
            "n_cells": len(rows),
            "added_dots_total": int(added),
            "control_dots_total": int(ctrl),
            "mean_added_per_cell": float(added / max(1, len(rows))),
            "credit_per_added_dot": float(tp_lic / max(1, added)),
            "tau_live_bar": 0.0548,
            "tau_farfield_bar": float(0.2 * dti_base / (1.0 - 0.2 * dti_base)),
            "mean_delta_dti_licence_vs_base": float(np.mean(d_lic)),
            "mean_delta_dti_random_vs_base": float(np.mean(d_ran)),
            "mean_delta_dti_licence_vs_random": float(np.mean(d_pp)),
            "cells_licence_improved_vs_base": int(sum(1 for v in d_lic if v > 0)),
            "cells_licence_improved_vs_random": int(sum(1 for v in d_pp if v > 0)),
            "seeds_licence_improved": int(len({c["seed"] for c in rows if c["euler"]["delta_dti_licence"] > 0})),
            "per_seed_delta_licence": {str(s): float(np.mean([c["euler"]["delta_dti_licence"]
                                                              for c in rows if c["seed"] == s]))
                                       for s in sorted({c["seed"] for c in rows})},
        }

    los, leak = agg("losfo"), agg("leaky")

    packing_block = None
    if args.packing_variants:
        arms = {}
        for det in ("losfo", "leaky"):
            arms[det] = {"base": agg(det)}
            for name in ("prob_order", "random_order", "max_coverage"):
                arms[det][name] = agg(f"{det}__{name}")
        paired = {}
        for det in ("losfo", "leaky"):
            rows = [c for c in cells if c.get("packing")]
            entry = {"base_coverage": float(np.mean(
                [c["packing"][det]["base"]["coverage"] for c in rows]))}
            for name in ("prob_order", "random_order", "max_coverage"):
                d_dti = [c["packing"][det][name]["dti"] - c[det]["dti"] for c in rows]
                d_pp = [c["packing"][det][name]["dti"] - c["packing"][det]["prob_order"]["dti"]
                        for c in rows] if name != "prob_order" else [0.0] * len(rows)
                entry[name] = {
                    "mean_delta_dti_vs_base": float(np.mean(d_dti)),
                    "mean_delta_dti_vs_prob_order": float(np.mean(d_pp)),
                    "cells_improved_vs_base": int(sum(1 for v in d_dti if v > 0)),
                    "n_cells": len(rows),
                    "mean_coverage": float(np.mean([c["packing"][det][name]["coverage"]
                                                    for c in rows])),
                }
            paired[det] = entry
        packing_block = {
            "description": "Same candidate pool, same matched dot count, same far-field truth. "
                           "prob_order = evidence-ordered spacing cascade; random_order = the "
                           "content-blind control with the identical rule; max_coverage = greedy "
                           "maximum expected coverage of the detector field.",
            "thin_d_px": args.thin_d,
            "arms": arms,
            "paired_vs_base": paired,
        }
    per_fold = {
        fn: {
            "n_cells": len(v),
            "losfo_mean_dti": float(np.mean([c["losfo"]["dti"] for c in v])) if v else None,
            "leaky_mean_dti": float(np.mean([c["leaky"]["dti"] for c in v])) if v else None,
            "losfo_tp": float(sum(c["losfo"]["tp"] for c in v)),
            "leaky_tp": float(sum(c["leaky"]["tp"] for c in v)),
        }
        for fn, v in per_fold_summary.items()
    }
    ratios = {
        "mean_dti_losfo_over_leaky": (los["mean_dti"] / leak["mean_dti"]) if leak["mean_dti"] else None,
        "credit_losfo_over_leaky": (los["sum_tp"] / leak["sum_tp"]) if leak["sum_tp"] else None,
        "recall_w_losfo_over_leaky": (los["recall_w"] / leak["recall_w"]) if leak["recall_w"] else None,
    }

    h36_1_block_out = (
        summarize_h36_1_farfield(cells) if args.h36_1_farfield else None
    )
    h38_block_out = (
        summarize_h38_corroboration(cells, h38_fields["meta"])
        if h38_fields is not None
        else None
    )

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": "DIAGNOSTIC, NOT A PROMOTION GATE. It measures how much of the interleaved "
                "protocol's credit is catalogue interpolation. It approves nothing and spends no slot.",
        "protocol": "src/gems27/losfo.py (leave-fault-system-out with a 600 m label buffer)",
        "code_sha256": {
            "losfo": hashlib.sha256((paths.REPO / "src" / "gems27" / "losfo.py").read_bytes()).hexdigest(),
            "oof_detector": hashlib.sha256(
                (paths.REPO / "src" / "gems27" / "oof_detector.py").read_bytes()).hexdigest(),
            "heatflow_euler": hashlib.sha256(
                (paths.REPO / "src" / "gems27" / "heatflow_euler.py").read_bytes()).hexdigest(),
            "runner": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "seeds": seeds, "cells": cells, "meta": diag_meta,
        "thin_d_px": args.thin_d,
        "arms": {
            "losfo": {"description": "trained with held-out systems + 600 m buffer erased", **los},
            "leaky": {"description": "trained on the unmasked catalogue (control)", **leak},
        },
        "per_fold": per_fold,
        "ratios": ratios,
        "packing_variants": packing_block,
        "euler_licence": euler_block_out,
        "h36_1_farfield": h36_1_block_out,
        "h38_corroboration": h38_block_out,
        "far_field_check": {
            "min_dist_truth_to_known_px_over_cells": float(
                min(c["min_dist_truth_to_known_px"] for c in cells)),
            "median_dist_truth_to_known_px_over_cells": float(
                np.median([c["median_dist_truth_to_known_px"] for c in cells])),
            "frac_dots_ge_300m_from_known": float(np.mean(
                [c["frac_dots_ge_3px_from_known"] for c in cells
                 if c["frac_dots_ge_3px_from_known"] is not None])) if cells else None,
            "reading": "truth sits >= buffer_px from every pixel the losfo detector saw as positive, "
                       "which the interleaved protocol cannot achieve (0 px by construction)",
        },
        "seconds": time.time() - t0,
    }
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(out, indent=1) + "\n")

    print(f"\nLOSFO   mean DTI {los['mean_dti']:.5f}  credit {los['sum_tp']:,.1f}  "
          f"recall_w {los['recall_w']:.4f}  credit/dot {los['credit_per_dot']:.4f}")
    print(f"LEAKY   mean DTI {leak['mean_dti']:.5f}  credit {leak['sum_tp']:,.1f}  "
          f"recall_w {leak['recall_w']:.4f}  credit/dot {leak['credit_per_dot']:.4f}")
    print(f"ratio   DTI {ratios['mean_dti_losfo_over_leaky']:.4f}   "
          f"credit {ratios['credit_losfo_over_leaky']:.4f}")
    print(f"truth is >= {out['far_field_check']['min_dist_truth_to_known_px_over_cells']:.0f} px "
          f"({100 * out['far_field_check']['min_dist_truth_to_known_px_over_cells']:.0f} m) from "
          f"every known pixel")
    if packing_block:
        for det in ("losfo", "leaky"):
            for name in ("prob_order", "random_order", "max_coverage"):
                e = packing_block["paired_vs_base"][det][name]
                print(f"  {det:5s} {name:13s} dDTI(vs base) {e['mean_delta_dti_vs_base']:+.5f} "
                      f"({e['cells_improved_vs_base']}/{e['n_cells']} up) "
                      f"coverage {e['mean_coverage']:.1f} vs base "
                      f"{packing_block['paired_vs_base'][det]['base_coverage']:.1f}")
    if h36_1_block_out:
        det_l = h36_1_block_out["detectors"]["losfo"]
        f1 = det_l["F1_rung30_vs_matched_random"]
        f2 = det_l["F2_rung30_removal_efficiency"]
        f3 = det_l["F3_rung30_blind_r1_vs_base"]
        f4 = det_l["F4_h27_4_blind_r1_vs_base"]
        print(
            f"H36-1 LOSFO: F1(r30-randN)={f1['mean_delta_dti']:+.6f} ({f1['cells_improved']}/{h36_1_block_out['n_cells']} up) | "
            f"F2 e_far={f2['pooled_e_far']:.5f} (<{h36_1_block_out['tau_live_bar']:.5f}: {f2['passes_tau_live']}) | "
            f"F3(r30_r1-base)={f3['mean_delta_dti_vs_base']:+.6f} ({f3['cells_improved_vs_base']}/{h36_1_block_out['n_cells']} up, e_far={f3['pooled_e_far']:.5f}) | "
            f"F4(h27_4_r1-base)={f4['mean_delta_dti_vs_base']:+.6f} (dTP={f4['sum_tp_removed']:.2f})"
        )
    if h38_block_out:
        for name, a in h38_block_out["arms"].items():
            print(
                f"H38 {name:24s}: dots={a['added_dots_total']:4d} "
                f"c/dot={a['credit_per_added_dot_arm']:.5f} "
                f"(sub_ctrl={a['credit_per_added_dot_control_sub_ridge']:.5f}, "
                f"rand_ctrl={a['credit_per_added_dot_control_random']:.5f}) | "
                f"dDTI={a['mean_delta_dti_arm_vs_ref']:+.6f} "
                f"({a['cells_arm_improved_vs_ref']}/{a['n_cells']} cells, "
                f"{a['seeds_arm_improved_vs_ref']} seeds) | "
                f"ALL_PASS={a['criteria']['ALL_PASS']}"
            )
    print(f"written {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
