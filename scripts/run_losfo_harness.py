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
    args = ap.parse_args()

    a, _, b = args.seeds.partition("-")
    seeds = list(range(int(a), int(b) + 1)) if b else [int(a)]
    t0 = time.time()

    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    fold = holdout.make_quadrant_folds(foot)

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

    out = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "kind": "DIAGNOSTIC, NOT A PROMOTION GATE. It measures how much of the interleaved "
                "protocol's credit is catalogue interpolation. It approves nothing and spends no slot.",
        "protocol": "src/gems27/losfo.py (leave-fault-system-out with a 600 m label buffer)",
        "code_sha256": {
            "losfo": hashlib.sha256((paths.REPO / "src" / "gems27" / "losfo.py").read_bytes()).hexdigest(),
            "oof_detector": hashlib.sha256(
                (paths.REPO / "src" / "gems27" / "oof_detector.py").read_bytes()).hexdigest(),
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
    print(f"written {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
