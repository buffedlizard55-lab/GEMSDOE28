#!/usr/bin/env python3
"""S31 EXP-1: hide-and-recover holdout suite (lane method, fresh seeds 400-409).

Lane paragraph (parallel-run protocol): use the template's cached feature stack and
src/gems27/holdout.py + src/gems27/metric.py. Holdout = hide-and-recover: withhold whole
fault segments, derive every catalogue-based feature ONLY from the visible faults, mask
visible faults pixel-exactly, score pooled DTI (alpha 0.2, beta 0.8, 300 m triangular kernel).

Arms (all dot sets are derived WITHOUT reading the hidden components):
  base               GEMSDOE32 H33-2 dots (USER-REPORTED 0.2778) as-is.
  prune3 / prune5    base minus dots within 3 / 5 px of the VISIBLE faults.
  prune3_strainkeep  prune3, but restore band (3,6] px dots whose strain-edge value is at or
                     above the in-footprint median of that band (catalogue-independent surface).
  fill_shear/rtp/tmi base plus 11,520 prior dots (strain-edge / RTP ridge / tmi high-pass edge),
                     >= 6 px from the VISIBLE faults, 4 px greedy spacing.
  fill_shear_only    the shear fill dots alone (prior quality isolated).
  control_random     11,520 uniform random dots >= 6 px from the VISIBLE faults (matched control).

Leakage canary: ROC AUC of each prior surface alone, at base-free cells, predicting a cell
within 3 px of hidden truth. AUC > 0.90 = leakage until proven otherwise.

Output: evidence/s31_holdout.json. HOLDOUT-DTI labels; never a leaderboard score.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_filter, gaussian_gradient_magnitude
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, holdout  # noqa: E402
from gems27.metric import dti_binary  # noqa: E402

PARENT = ROOT / "data/registry_tifs/GEMSDOE32/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
SEEDS = list(range(400, 405))  # 5 fresh seeds x 4 folds = 20 splits (0 collisions, evidence/s31_seed_audit.json)
N_FILL = 11_520
FILL_MIN_VISIBLE_PX = 6.0
FILL_SPACING_PX = 4
CANARY_AUC_FAIL = 0.90


def load_band(path: Path, band: int) -> np.ndarray:
    with rasterio.open(path) as s:
        a = s.read(band).astype(np.float64)
    foot_finite = np.isfinite(a)
    fill = np.nanmedian(a[foot_finite]) if foot_finite.any() else 0.0
    return np.where(foot_finite, a, fill)


def edge_surface(values: np.ndarray, sigma: float) -> np.ndarray:
    return gaussian_gradient_magnitude(values, sigma=sigma)


def greedy_top(dots_forbidden: np.ndarray, score: np.ndarray, n: int, spacing: int,
               top_multiplier: int = 8) -> np.ndarray:
    """Greedy: highest-score cells, 4-px Chebyshev suppression, forbidden cells excluded.

    Candidates are pre-truncated to the top `top_multiplier * n` cells by score before the Python
    loop; with 4 px suppression this truncation almost never binds (each accept suppresses < 81
    cells) and it is applied identically to every arm, so arm comparisons stay fair.
    """
    cand = np.flatnonzero(dots_forbidden)
    order = cand[np.argsort(-score.reshape(-1)[cand], kind="stable")]
    if top_multiplier and order.size > top_multiplier * n:
        order = order[:top_multiplier * n]
    blocked = np.zeros(score.shape, bool)
    r = spacing - 1
    out: list[int] = []
    for flat in order:
        if len(out) >= n:
            break
        y, x = divmod(int(flat), score.shape[1])
        if blocked[y, x]:
            continue
        out.append(int(flat))
        blocked[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1] = True
    g = np.zeros(score.shape, bool)
    g.reshape(-1)[np.asarray(out, dtype=np.int64)] = True
    return g


def main() -> int:
    t0 = time.time()
    foot = grid.load_footprint(ROOT / "data/sample_submission.tif")
    labels = grid.load_labels(ROOT / "data/labels.tif")
    with rasterio.open(PARENT) as s:
        base = ((np.where(np.isfinite(s.read(1).astype(np.float64)), s.read(1).astype(np.float64), 0.0) > 0.5) & foot)
    n_base = int(base.sum())

    training = ROOT / "data/training_features.tif"
    shear_band = load_band(training, 7)    # geod_shearrate (verified band names, prepare_data.py)
    rtp_band = load_band(training, 2)      # rtp
    tmi_hg_band = load_band(training, 3)   # tmi_hg
    shear_edge = edge_surface(gaussian_filter(shear_band, 2.0), 1.5)
    rtp_ridge = edge_surface(rtp_band, 1.5)              # S30's prior, reference arm
    tmi_edge = edge_surface(tmi_hg_band, 1.5)
    shear_thr = float(np.median(shear_edge[foot]))

    fold = holdout.make_quadrant_folds(foot)
    W = foot.shape[1]

    arms = ["base", "prune3", "prune5", "prune3_strainkeep",
            "fill_shear", "fill_rtp", "fill_tmi", "fill_shear_only", "control_random",
            "fill_mid_shear", "fill_mid_random", "fill_mid_shear_only"]
    sums = {a: {"TPw": 0.0, "FPw": 0.0, "FNw": 0.0, "n_truth": 0, "n_emitted": 0} for a in arms}
    per_fold: dict[str, list[float]] = {a: [] for a in arms}
    canary_scores: dict[str, list[float]] = {"shear_edge": [], "rtp_ridge": [], "tmi_edge": []}
    # Memory guard: per-split AUC scalars + a capped pooled subsample (never full grids x splits).
    # Frozen pre-result build rule (S31 candidate) is recorded in the output JSON.
    canary_labels: dict[str, list[float]] = {k: [] for k in canary_scores}
    canary_pooled: dict[str, dict[str, list]] = {k: {"x": [], "y": []} for k in canary_scores}

    for seed in SEEDS:
        for fold_id in range(4):
            print(f"split seed={seed} fold={fold_id}", flush=True)
            split = holdout.make_split(labels, fold, fold_id, seed=seed)
            visible = split.known
            hidden = split.hidden
            if not hidden.any():
                continue
            dist_visible = distance_transform_edt(~visible)
            d_to_g = None  # computed lazily inside dti_binary per arm; pool instead per arm below

            arm_dots: dict[str, np.ndarray] = {
                "base": base,
                "prune3": base & (dist_visible > 3.0),
                "prune5": base & (dist_visible > 5.0),
                # H-S31-A: drop strain-negative dots in the (3,6] px band; keep them if strain-positive.
                "prune3_strainkeep": (
                    (base & (dist_visible > 6.0))
                    | (base & (dist_visible > 3.0) & (dist_visible <= 6.0) & (shear_edge >= shear_thr))),
                "control_random": np.zeros_like(base),
            }

            forbidden = (dist_visible <= FILL_MIN_VISIBLE_PX) | ~foot
            # Per-split candidate mask: not on visible/near-visible, not on existing base dots.
            base_free = foot & ~base
            fill_sets: dict[str, np.ndarray] = {}
            for name, surf in (("fill_shear", shear_edge), ("fill_rtp", rtp_ridge), ("fill_tmi", tmi_edge)):
                cand_ok = base_free & ~forbidden
                sc = np.where(cand_ok, surf, -np.inf)
                fill_sets[name] = greedy_top(cand_ok, sc, N_FILL, FILL_SPACING_PX)
            rng = np.random.default_rng(9100 + seed * 10 + fold_id)
            free_idx = np.flatnonzero(base_free & ~forbidden)
            ctrl_idx = rng.choice(free_idx, size=min(N_FILL, free_idx.size), replace=False)
            ctrl = np.zeros_like(base)
            ctrl.reshape(-1)[ctrl_idx] = True
            fill_sets["control_random"] = ctrl
            fill_sets["fill_shear_only"] = fill_sets["fill_shear"]

            arm_dots["fill_shear"] = base | fill_sets["fill_shear"]
            arm_dots["fill_rtp"] = base | fill_sets["fill_rtp"]
            arm_dots["fill_tmi"] = base | fill_sets["fill_tmi"]
            arm_dots["fill_shear_only"] = fill_sets["fill_shear"]
            arm_dots["control_random"] = ctrl

            # H-S31-B' mid-halo habitat arms: fill in the (3, 6] px band (added BEFORE any EXP-1
            # result was read; motivated by the family calibration, adjudicated here).
            mid_ok = base_free & (dist_visible > 3.0) & (dist_visible <= 6.0)
            sc_mid = np.where(mid_ok, shear_edge, -np.inf)
            fill_mid_shear = greedy_top(mid_ok, sc_mid, N_FILL, FILL_SPACING_PX)
            mid_idx = np.flatnonzero(mid_ok)
            mid_rng_idx = rng.choice(mid_idx, size=min(N_FILL, mid_idx.size), replace=False)
            fill_mid_random = np.zeros_like(base)
            fill_mid_random.reshape(-1)[mid_rng_idx] = True
            arm_dots["fill_mid_shear"] = base | fill_mid_shear
            arm_dots["fill_mid_random"] = base | fill_mid_random
            arm_dots["fill_mid_shear_only"] = fill_mid_shear

            for arm in arms:
                r = dti_binary(arm_dots[arm], hidden, valid=foot, known=visible)
                sums[arm]["TPw"] += r["TPw"]; sums[arm]["FPw"] += r["FPw"]; sums[arm]["FNw"] += r["FNw"]
                sums[arm]["n_truth"] += r["n_truth"]; sums[arm]["n_emitted"] += r["n_emitted"]
                per_fold[arm].append(r["dti"])

            # Leakage canary: surface alone predicting near-hidden membership at base-free cells.
            hidden_dil = (distance_transform_edt(~hidden) <= 3.0)
            sel = base_free & ~visible
            ys, xs = np.nonzero(sel)
            if ys.size > 400_000:  # subsample cells for the canary (memory guard)
                keep = np.random.default_rng(seed * 100 + fold_id).choice(
                    ys.size, size=400_000, replace=False)
                ys, xs = ys[keep], xs[keep]
            y_lab = hidden_dil[ys, xs].astype(int)
            for cname, surf in (("shear_edge", shear_edge), ("rtp_ridge", rtp_ridge), ("tmi_edge", tmi_edge)):
                xsurf = surf[ys, xs].astype(np.float64)
                auc = float("nan")
                if 0 < y_lab.sum() < y_lab.size:
                    auc = float(roc_auc_score(y_lab, xsurf))
                if auc == auc:
                    canary_scores[cname].append(auc)
                if len(canary_scores[cname]) * ys.size <= 4_000_000:  # pooled subsample cap
                    canary_labels.setdefault(cname, []).append(y_lab)
                    canary_pooled.setdefault(cname, {"x": [], "y": []})
                    canary_pooled[cname]["x"].append(xsurf.astype(np.float32))
                    canary_pooled[cname]["y"].append(y_lab)

    pooled = {}
    for arm in arms:
        tp, fp, fn = sums[arm]["TPw"], sums[arm]["FPw"], sums[arm]["FNw"]
        pooled[arm] = {
            "dti_pooled": tp / (tp + 0.2 * fp + 0.8 * fn + 1e-7),
            "TPw": tp, "FPw": fp, "FNw": fn,
            "n_emitted_total": sums[arm]["n_emitted"],
            "n_splits": len(per_fold[arm]),
            "dti_fold_mean": float(np.mean(per_fold[arm])),
            "dti_fold_ci95": [float(np.mean(per_fold[arm]) - 1.96 * np.std(per_fold[arm]) / np.sqrt(len(per_fold[arm]))),
                              float(np.mean(per_fold[arm]) + 1.96 * np.std(per_fold[arm]) / np.sqrt(len(per_fold[arm])))],
        }

    canary = {}
    for cname in canary_scores:
        aucs = canary_scores[cname]
        pooled_auc = float("nan")
        if cname in canary_pooled and canary_pooled[cname]["x"]:
            x = np.concatenate(canary_pooled[cname]["x"]).astype(np.float64)
            y = np.concatenate(canary_pooled[cname]["y"])
            if 0 < y.sum() < y.size:
                pooled_auc = float(roc_auc_score(y, x))
        mean_auc = float(np.mean(aucs)) if aucs else float("nan")
        auc = pooled_auc if pooled_auc == pooled_auc else mean_auc
        canary[cname] = {"auc_pooled_subsample": pooled_auc, "auc_mean_of_splits": mean_auc,
                         "auc": auc, "pass_below_0p90": bool(auc == auc and auc < CANARY_AUC_FAIL),
                         "n_splits_with_auc": len(aucs)}

    out = {
        "schema": 1, "session": "S31", "experiment": "EXP-1 hide-and-recover suite",
        "evaluator_version": "gems-segment-pooled-v1 (src/gems27/holdout.py + metric.py)",
        "label": "HOLDOUT-DTI (not a leaderboard score)",
        "seeds": SEEDS, "n_splits": sum(len(v) for v in per_fold.values()) // len(arms),
        "parent": PARENT.name, "parent_user_reported_score": 0.2778,
        "n_base_dots": n_base, "n_fill": N_FILL,
        "fill_rule": f">= {FILL_MIN_VISIBLE_PX} px from visible faults, {FILL_SPACING_PX} px greedy spacing, prior-ranked",
        "shear_threshold_median_in_footprint": shear_thr,
        "arms": pooled,
        "paired_delta_dti_pooled": {
            arm: pooled[arm]["dti_pooled"] - pooled["base"]["dti_pooled"]
            for arm in arms if arm != "base"},
        "leakage_canary": canary,
        "runtime_s": round(time.time() - t0, 1),
    }
    (ROOT / "evidence" / "s31_holdout.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({"arms": {a: pooled[a]["dti_pooled"] for a in arms},
                      "deltas": out["paired_delta_dti_pooled"], "canary": canary,
                      "runtime_s": out["runtime_s"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
