#!/usr/bin/env python3
"""S22 Experiment 2 — leakage canary + 12-cell hide-and-recover holdout gate (frozen, knowledge/62).

Arms (identical splits/samples/emission): lane = 32 base + 32 context; control = 32 base;
dotted_b2 = S21 baseline construction (reference only). Seeds 360-362 x 4 quadrant folds.
Evaluator: gems27.metric.dti_binary (alpha 0.2, beta 0.8, 300 m triangular). All numbers are
HOLDOUT-DTI (local hide-and-recover), never organizer scores.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, holdout, metric, paths  # noqa: E402
from gems27.oof_detector import ridge_nms  # noqa: E402

T0 = time.time()
SEEDS = [360, 361, 362]
TOTAL_BUDGET = 37_654
MIN_DIST = 2.8


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


def greedy_emit(score: np.ndarray, allowed: np.ndarray, ridge: np.ndarray, budget: int):
    """Highest-score-first dots with 2.8px spacing; ridge pool first, then pre-registered fill."""
    H, W = score.shape
    disc_r = int(np.ceil(MIN_DIST))
    offs = [(dy, dx) for dy in range(-disc_r, disc_r + 1) for dx in range(-disc_r, disc_r + 1)
            if dy * dy + dx * dx < MIN_DIST * MIN_DIST]
    blocked = np.zeros((H, W), dtype=bool)
    kept_rc: list[tuple[int, int]] = []
    stats = {"ridge_dots": 0, "fill_dots": 0}

    def passes(pool: np.ndarray, key: str):
        ys, xs = np.nonzero(pool)
        if len(ys) == 0:
            return
        order = np.argsort(-score[ys, xs], kind="stable")
        ys, xs = ys[order], xs[order]
        for r, c in zip(ys.tolist(), xs.tolist()):
            if len(kept_rc) >= budget:
                return
            if blocked[r, c]:
                continue
            kept_rc.append((r, c))
            stats[key] += 1
            for dy, dx in offs:
                yy, xx = r + dy, c + dx
                if 0 <= yy < H and 0 <= xx < W:
                    blocked[yy, xx] = True

    passes(allowed & ridge, "ridge_dots")
    if len(kept_rc) < budget:
        passes(allowed & ~ridge, "fill_dots")
    out = np.zeros((H, W), dtype=bool)
    for r, c in kept_rc:
        out[r, c] = True
    return out, stats


def main() -> int:
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    H, W = foot.shape
    foot_flat = np.flatnonzero(foot.ravel())
    pos_of_flat = -np.ones(H * W, dtype=np.int32)
    pos_of_flat[foot_flat] = np.arange(len(foot_flat), dtype=np.int32)

    meta = json.loads(paths.PREPARED_META.read_text())
    cmeta = json.loads((paths.PREPARED_FEATURES.parent / "context_s22.json").read_text())
    feat_names = meta["names"] + cmeta["names"]
    Xb = np.load(paths.PREPARED_FEATURES, mmap_mode="r")
    Xc = np.load(paths.PREPARED_FEATURES.parent / "context_s22.npy", mmap_mode="r")
    log("features", Xb.shape, Xc.shape, "footprint", int(foot.sum()), "labels", int(labels.sum()))

    with rasterio.open(paths.DOTTED_D2_8) as ds:
        a = ds.read(1)
    dotted = np.isfinite(a) & (a > 0)
    del a

    def assemble(rows: np.ndarray, lane: bool) -> np.ndarray:
        base = np.asarray(Xb[rows], dtype=np.float32)
        if not lane:
            return base
        ctx = np.asarray(Xc[rows], dtype=np.float32)
        return np.concatenate([base, ctx], axis=1)

    folds = holdout.make_quadrant_folds(foot)
    cells: list[dict] = []
    canary: dict[str, float | None] = {}

    for seed in SEEDS:
        for fid in range(4):
            sp = holdout.make_split(labels, folds, fid, seed)
            fm, hidden, known = sp.fold_mask, sp.hidden, sp.known
            d_vis = distance_transform_edt(~known)
            rng = np.random.default_rng(seed * 100 + fid)

            train_region = foot & ~fm
            pos_flat = np.flatnonzero((known & train_region).ravel())
            neg_flat = np.flatnonzero((train_region & ~labels).ravel() & (d_vis.ravel() >= 3))
            pos_s = rng.choice(pos_flat, size=min(25_000, len(pos_flat)), replace=False)
            neg_s = rng.choice(neg_flat, size=min(75_000, len(neg_flat)), replace=False)
            train_rows = pos_of_flat[np.sort(np.r_[pos_s, neg_s])]
            y_train = np.r_[np.ones(len(pos_s), int), np.zeros(len(neg_s), int)]
            # rows were sorted jointly; rebuild y by membership in pos set
            pos_set_mask = np.isin(np.sort(np.r_[pos_s, neg_s]), pos_s)
            y_train = pos_set_mask.astype(int)

            test_flat = np.flatnonzero((fm & ~known).ravel())
            test_rows = pos_of_flat[test_flat]

            # ---- leakage canary on first cell: every feature alone, hidden vs allowed negs ----
            if seed == SEEDS[0] and fid == 0:
                hid_flat = np.flatnonzero(hidden.ravel())
                allowed_flat = np.flatnonzero((fm & ~known & ~hidden).ravel() & (d_vis.ravel() > 2))
                neg_t = rng.choice(allowed_flat, size=min(20_000, len(allowed_flat)), replace=False)
                rows_h, rows_n = pos_of_flat[hid_flat], pos_of_flat[neg_t]
                Xh = assemble(rows_h, lane=True)
                Xn = assemble(rows_n, lane=True)
                y_c = np.r_[np.ones(len(Xh)), np.zeros(len(Xn))]
                Xall = np.vstack([Xh, Xn])
                for j, name in enumerate(feat_names):
                    v = Xall[:, j]
                    ok = np.isfinite(v)
                    if ok.sum() < 100 or len(np.unique(y_c[ok])) < 2 or np.nanstd(v[ok]) == 0:
                        canary[name] = None
                        continue
                    canary[name] = float(roc_auc_score(y_c[ok], v[ok]))
                vals = [v for v in canary.values() if v is not None]
                worst = max(max(vals), 1 - min(vals))
                log("CANARY worst |AUC-0.5| mapped:", round(worst, 4),
                    "max AUC", round(max(vals), 4), "min AUC", round(min(vals), 4))
                if worst > 0.90:
                    raise SystemExit(f"LEAKAGE CANARY FAIL: worst single-feature AUC {worst}")
                del Xh, Xn, Xall

            rs, cs = holdout.crop(fm, fm)
            budget = int(round(TOTAL_BUDGET * fm.sum() / foot.sum()))
            cell: dict = {"seed": seed, "fold": holdout.FOLD_NAMES[fid], "budget": budget,
                          "n_hidden": int(hidden.sum())}

            fm_c, known_c, hidden_c = fm[rs, cs], known[rs, cs], hidden[rs, cs]
            dvis_c = d_vis[rs, cs]
            allowed_c = fm_c & ~known_c & (dvis_c > 2)

            def score(em: np.ndarray, _h=hidden_c, _v=fm_c, _k=known_c) -> dict:
                return metric.dti_binary(em.astype(float), _h, valid=_v, known=_k)

            for arm, lane_flag in (("lane", True), ("control", False)):
                clf = HistGradientBoostingClassifier(
                    max_iter=250, learning_rate=0.06, max_leaf_nodes=63,
                    min_samples_leaf=40, l2_regularization=1.0, random_state=seed)
                clf.fit(assemble(train_rows, lane_flag), y_train)
                probs = np.zeros(len(test_rows), dtype=np.float32)
                for s0 in range(0, len(test_rows), 200_000):
                    idx = test_rows[s0:s0 + 200_000]
                    probs[s0:s0 + 200_000] = clf.predict_proba(assemble(idx, lane_flag))[:, 1]
                surf = np.zeros((H, W), dtype=np.float32)
                rr, cc = np.divmod(test_flat, W)
                surf[rr, cc] = probs
                surf_c = surf[rs, cs]
                ridge = ridge_nms(surf_c, fm_c, sigma=1.0)
                em, stats = greedy_emit(surf_c, allowed_c, ridge, budget)
                cell[arm] = score(em)
                cell[f"{arm}_emission"] = {**stats, "n_emitted": int(em.sum())}
                # surface AUC hidden vs sampled allowed negatives
                hid_rows_mask = hidden.ravel()[test_flat]
                neg_pick = rng.choice(np.flatnonzero(~hid_rows_mask),
                                      size=min(20_000, int((~hid_rows_mask).sum())), replace=False)
                y_a = np.r_[np.ones(int(hid_rows_mask.sum())), np.zeros(len(neg_pick))]
                v_a = np.r_[probs[hid_rows_mask], probs[neg_pick]]
                cell[f"surface_auc_{arm}"] = float(roc_auc_score(y_a, v_a))
                del surf, surf_c, ridge, em, clf, probs

            em_base = dotted[rs, cs] & allowed_c
            cell["dotted_b2"] = score(em_base)
            cell["dotted_b2_emission"] = {"n_emitted": int(em_base.sum())}
            cells.append(cell)
            log(f"cell s{seed} {cell['fold']} hid={cell['n_hidden']} budget={budget} "
                f"LANE={cell['lane']['dti']:.4f} CTRL={cell['control']['dti']:.4f} "
                f"BASE={cell['dotted_b2']['dti']:.4f} (base n={int(em_base.sum())}) "
                f"AUC lane={cell['surface_auc_lane']:.3f} ctrl={cell['surface_auc_control']:.3f}")

    def pooled(key: str) -> float:
        TP = sum(c[key]["TPw"] for c in cells)
        FP = sum(c[key]["FPw"] for c in cells)
        FN = sum(c[key]["FNw"] for c in cells)
        return TP / (TP + 0.2 * FP + 0.8 * FN + 1e-7)

    def boot_delta(a: str, b: str, n: int = 10_000):
        rng = np.random.default_rng(20261026)
        deltas = []
        idxs = np.arange(len(cells))
        for _ in range(n):
            pick = rng.choice(idxs, size=len(idxs), replace=True)
            def pool(key, _pick=pick):
                TP = sum(cells[i][key]["TPw"] for i in _pick)
                FP = sum(cells[i][key]["FPw"] for i in _pick)
                FN = sum(cells[i][key]["FNw"] for i in _pick)
                return TP / (TP + 0.2 * FP + 0.8 * FN + 1e-7)
            deltas.append(pool(a) - pool(b))
        d = np.asarray(deltas)
        return float(np.percentile(d, 2.5)), float(np.percentile(d, 97.5))

    def boot_abs(key: str, n: int = 10_000):
        rng = np.random.default_rng(20261027)
        vals = []
        idxs = np.arange(len(cells))
        for _ in range(n):
            pick = rng.choice(idxs, size=len(idxs), replace=True)
            TP = sum(cells[i][key]["TPw"] for i in pick)
            FP = sum(cells[i][key]["FPw"] for i in pick)
            FN = sum(cells[i][key]["FNw"] for i in pick)
            vals.append(TP / (TP + 0.2 * FP + 0.8 * FN + 1e-7))
        v = np.asarray(vals)
        return [float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5))]

    result = {
        "experiment": "S22 Exp2 canary + holdout gate (frozen knowledge/62)",
        "label": "HOLDOUT-DTI",
        "evaluator": "gems27.metric.dti_binary alpha0.2 beta0.8 300m triangular; "
                     "gems27.holdout quadrant component-hide 20% (gems-segment-pooled-v1 semantics)",
        "seeds": SEEDS,
        "n_cells": len(cells),
        "withheld_positives_pooled_across_cells": int(sum(c["n_hidden"] for c in cells)),
        "canary_single_feature_auc_cell_360_NW": canary,
        "canary_worst_abs": float(max(max(v for v in canary.values() if v is not None),
                                       1 - min(v for v in canary.values() if v is not None))),
        "pooled_dti": {k: pooled(k) for k in ("lane", "control", "dotted_b2")},
        "pooled_ci95": {k: boot_abs(k) for k in ("lane", "control", "dotted_b2")},
        "delta_lane_minus_base": pooled("lane") - pooled("dotted_b2"),
        "delta_lane_minus_base_ci95": list(boot_delta("lane", "dotted_b2")),
        "delta_lane_minus_control": pooled("lane") - pooled("control"),
        "delta_lane_minus_control_ci95": list(boot_delta("lane", "control")),
        "cells": cells,
        "runtime_s": time.time() - T0,
    }
    result["gate"] = {
        "canary_pass": bool(result["canary_worst_abs"] <= 0.90),
        "delta_vs_base_gt0": bool(result["delta_lane_minus_base"] > 0),
        "delta_vs_base_ci_lower_gt0": bool(result["delta_lane_minus_base_ci95"][0] > 0),
        "delta_vs_control_gt0": bool(result["delta_lane_minus_control"] > 0),
    }
    out = ROOT / "evidence/s22_holdout.json"
    out.write_text(json.dumps(result, indent=2, default=float) + "\n")
    log("POOLED", json.dumps(result["pooled_dti"], indent=2))
    log("DELTA vs base", result["delta_lane_minus_base"], result["delta_lane_minus_base_ci95"])
    log("DELTA vs ctrl", result["delta_lane_minus_control"], result["delta_lane_minus_control_ci95"])
    log("GATE", result["gate"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
