#!/usr/bin/env python3
"""S29-E2: holdout validation of the hole-constrained candidate B (experiment 2 of 3).

Same per-quadrant cross-fitted surfaces and SegmentHoldout as E1 (scripts/run_s29_experiment.py), but the
budget is K_total = 20,000 (the builder's largest passing count) and, inside each quadrant, ceil(0.32 * K_f)
dots are forced into registry-039-uncovered pixels (>3 px from every registry-039 dot) and the rest are
ridge-NMS top cells. Random-K uses the same K_f. Decision rule (recorded in evidence/s29_b_prereg.json):
slot allowed only if HOLDOUT-DTI(B) > comparable best 0.0553736 (S28-TCB) AND paired CI vs random-K > 0.
Output: evidence/s29_b_holdout.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import run_s29_experiment as s29  # noqa: E402
from gems27.shared_template import load_shared  # noqa: E402

K_B = 20_000
HOLE_SHARE = 0.32
COMPARABLE_BEST = 0.0553736  # S28-TCB HOLDOUT-DTI, gems-segment-pooled-v1 (evidence/s28_tcb_run_card.json)
OUT = ROOT / "evidence/s29_b_holdout.json"


def main() -> int:
    shared = load_shared(ROOT)
    footprint, catalogue = s29.load_grid()
    X, names = s29.load_features(footprint)
    fp_idx = np.flatnonzero(footprint.ravel())
    ho = shared.holdout.SegmentHoldout(footprint, catalogue, buffer_px=s29.BUFFER_PX)
    with rasterio.open(s29.LATTICE) as src:
        lat_vals = src.read(1)
    reg039 = footprint & np.isfinite(lat_vals) & (lat_vals > 0)
    uncovered = footprint & (distance_transform_edt(~reg039) > 3.0)
    rng = np.random.default_rng(s29.SEED)
    preds_b, preds_rand = [], []
    fold_log = []
    for fold in ho.folds:
        valid, visible, train = fold["valid"], fold["visible"], fold["train"]
        k_f = int(round(K_B * int(valid.sum()) / s29.FOOTPRINT_PX))
        surface = s29.fit_surface(X, fp_idx, (train & footprint).ravel()[fp_idx], visible.ravel()[fp_idx],
                                  seed=s29.SEED + fold["id"])
        eligible = valid & ~visible
        nms = shared.metric.ridge_nms(surface, eligible, sigma=1.0) & eligible
        hole_pool = eligible & uncovered
        h = min(int(hole_pool.sum()), int(np.ceil(HOLE_SHARE * k_f)))
        hole_sel = shared.metric.select_top_positive(surface, hole_pool, h).astype(bool) if h else np.zeros_like(valid)
        rest = shared.metric.select_top_positive(surface, nms & ~hole_pool, k_f - int(hole_sel.sum())).astype(bool)
        dots = hole_sel | rest
        ids = np.flatnonzero(eligible.ravel())
        rnd = np.zeros(footprint.size, bool)
        rnd[rng.choice(ids, size=min(k_f, len(ids)), replace=False)] = True
        preds_b.append(dots)
        preds_rand.append(rnd.reshape(footprint.shape))
        fold_log.append({"fold": fold["name"], "K_f": k_f, "hole_dots": int(hole_sel.sum()),
                         "dots": int(dots.sum()), "hole_pool_px": int(hole_pool.sum())})
        print(fold["name"], fold_log[-1], flush=True)
    res_b = ho.summarize(preds_b)
    res_rand = ho.summarize(preds_rand)
    paired = ho.compare_paired(preds_b, preds_rand)
    decision = {
        "beats_comparable_best": bool(res_b["dti"] > COMPARABLE_BEST),
        "paired_ci_excludes_zero_positive": bool(paired["paired_delta_ci95"][0] > 0),
        "slot_allowed": bool(res_b["dti"] > COMPARABLE_BEST and paired["paired_delta_ci95"][0] > 0),
    }
    out = {
        "schema": "s29-b-holdout-v1",
        "label": "HOLDOUT-DTI (gems-segment-pooled-v1, catalogue-internal; not an organizer or leaderboard score)",
        "candidate": "s29_B_holeconstrained_k20000 (placement rule replicated per quadrant)",
        "K_total": K_B,
        "hole_share": HOLE_SHARE,
        "folds": fold_log,
        "B_holdout": res_b,
        "random_K_holdout": res_rand,
        "paired_B_minus_random_K": paired,
        "comparable_best_HOLDOUT_DTI": COMPARABLE_BEST,
        "comparable_best_source": "evidence/s28_tcb_run_card.json (S28-TCB, same evaluator)",
        "decision": decision,
        "note": "Surfaces are the same per-quadrant fits as E1 (same seeds); only placement differs.",
    }
    OUT.write_text(json.dumps(out, indent=2, default=float, allow_nan=False) + "\n", encoding="utf-8")
    print("B DTI", round(res_b["dti"], 6), "random", round(res_rand["dti"], 6), "paired", paired["paired_delta_dti"],
          paired["paired_delta_ci95"], "decision", decision, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
