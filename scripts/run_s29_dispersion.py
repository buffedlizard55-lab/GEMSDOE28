#!/usr/bin/env python3
"""S29 experiment 2 of 3: does spacing (dispersion) explain the holdout gain of the lattice control?

Candidate: the existing S26/S28 TCB surface (label-free; reused unchanged from src/gems27/tcb.py) with
ONE change: dots are chosen strongest-first from ridge-NMS candidates, but a dot is rejected if any
accepted dot lies within R_MIN pixels. R_MIN matches the calibration lattice's node spacing (5 px) so
the comparison with the lattice-subset control is like-for-like. Everything else follows S28.

Per fold: candidates may use only fold.visible (the shared protocol). The final global placement
(footprint minus full catalogue) is also built, for the registry duplicate check. Labels: HOLDOUT-DTI.
Negative or positive, the outcome is recorded; nothing is written to docs/downloads.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems27.shared_template import load_shared  # noqa: E402
from gems27.tcb import build_surface  # noqa: E402
from run_s28_tcb import (  # noqa: E402
    BUFFER_PX,
    CONTROL_PATH,
    K_DOTS,
    random_control,
    read_cached_layers,
    read_footprint_and_catalogue,
)
from run_s29_null_controls import lattice_subset_control  # noqa: E402

OUT = ROOT / "evidence/s29_dispersion_run_card.json"
R_MIN = 5.0
SEED = 20261029


def dispersed_top_k(shared, surface: np.ndarray, eligible: np.ndarray, k: int, r_min: float,
                    priority: np.ndarray | None = None):
    """Strongest-first ridge candidates with a minimum-spacing exclusion (Euclidean).

    ``priority`` (optional) replaces the surface as the ordering key; the ridge candidates
    still come from NMS of ``surface``. Used only by the S29 ridge-geometry control.
    """
    nms = shared.metric.ridge_nms(surface, eligible, sigma=1.0)
    cand = nms & eligible & np.isfinite(surface) & (surface > 0)
    ids = np.flatnonzero(cand.ravel())
    key = surface if priority is None else priority
    order = np.lexsort((ids, -key.ravel()[ids]))
    ids = ids[order]
    h, w = surface.shape
    r = int(np.ceil(r_min))
    offs = [(dy, dx) for dy in range(-r, r + 1) for dx in range(-r, r + 1) if dy * dy + dx * dx < r_min * r_min]
    blocked = np.zeros((h, w), dtype=bool)
    accepted = []
    for i in ids:
        y, x = divmod(int(i), w)
        if blocked[y, x]:
            continue
        accepted.append(i)
        for dy, dx in offs:
            yy, xx = y + dy, x + dx
            if 0 <= yy < h and 0 <= xx < w:
                blocked[yy, xx] = True
        if len(accepted) >= k:
            break
    out = np.zeros(surface.size, dtype=bool)
    out[np.asarray(accepted, dtype=np.int64)] = True
    return out.reshape(surface.shape), len(ids)


def main() -> int:
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    shared = load_shared(ROOT)
    footprint, catalogue = read_footprint_and_catalogue()
    layers, cache = read_cached_layers(footprint)
    surface, per_layer = build_surface(layers, footprint)
    with rasterio.open(CONTROL_PATH) as src:
        lattice = (src.read(1) == 1) & footprint
    ho = shared.holdout.SegmentHoldout(footprint, catalogue, buffer_px=BUFFER_PX)

    preds, shortfall, candidate_counts = [], [], []
    for fold in ho.folds:
        eligible = footprint & ~fold["visible"]
        dots, n_cand = dispersed_top_k(shared, surface, eligible, K_DOTS, R_MIN)
        preds.append(dots)
        shortfall.append(K_DOTS - int(dots.sum()))
        candidate_counts.append(int(n_cand))
        assert not (dots & fold["visible"]).any()

    random_preds = random_control(ho, footprint, seed=SEED)
    lattice_preds = lattice_subset_control(ho, footprint, lattice, seed=SEED)
    cand_sum = ho.summarize(preds)
    rnd_sum = ho.summarize(random_preds)
    lat_sum = ho.summarize(lattice_preds)
    vs_random = ho.compare_paired(preds, random_preds)
    vs_lattice = ho.compare_paired(preds, lattice_preds)

    # Leakage canary: the surface is label-free; test it alone against the fold-visible catalogue.
    canary = ho.canary({"tcb_fused_surface": surface}, seed=SEED)

    # Registry duplicate check (global placement, footprint minus full catalogue, as in S28).
    global_dots, _ = dispersed_top_k(shared, surface, footprint & ~catalogue, K_DOTS, R_MIN)
    dl = distance_transform_edt(~lattice)
    within3 = float((dl[global_dots] <= 3).mean()) if global_dots.any() else float("nan")
    rho = float(np.corrcoef(global_dots[footprint].astype(float), lattice[footprint].astype(float))[0, 1])

    def brief(s):
        return {
            "label": "HOLDOUT-DTI",
            "evaluator_version": s["evaluator_version"],
            "dti": float(s["dti"]),
            "ci95": s["ci95"]["interval"],
            "withheld_positives": int(s["n_withheld_positive_pixels"]),
            "n_emitted_scored": int(s["n_emitted"]),
        }

    def pair(p):
        return {
            "candidate_dti": p["candidate_dti"],
            "baseline_dti": p["baseline_dti"],
            "paired_delta_dti": p["paired_delta_dti"],
            "paired_delta_ci95": list(p["paired_delta_ci95"]),
            "fold_wins": p["fold_wins"],
            "n_folds": p["n_folds"],
        }

    card = {
        "run_card_schema": "s29-dispersion-v1",
        "run_id": "S29-DISPERSED-TCB-20261029",
        "started_at_utc": started,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hypothesis": "Spacing, not geology, explains the lattice control's holdout gain; a spacing-constrained TCB placement should match or beat the lattice-subset control if the TCB surface carries signal beyond coverage.",
        "candidate": "TCB surface (S26/S28 operator, unchanged) + minimum-spacing selection R_MIN=5 px",
        "r_min_px": R_MIN,
        "budget_dots_per_fold": K_DOTS,
        "fold_shortfall_dots": shortfall,
        "fold_ridge_candidates": candidate_counts,
        "holdout": brief(cand_sum),
        "random_k": brief(rnd_sum),
        "lattice_subset": brief(lat_sum),
        "paired_vs_random_k": pair(vs_random),
        "paired_vs_lattice_subset": pair(vs_lattice),
        "feature_canary": {
            "passed": bool(canary.get("passed")),
            "note": "Surface is label-free; canary tests fold-visible one-feature AUC only.",
            "summary": {k: v for k, v in canary.items() if k in ("passed", "max_fold_auc", "max_pooled_auc", "threshold")},
        },
        "registry_global_overlap": {
            "dots": int(global_dots.sum()),
            "fraction_within_3px_of_calibration_lattice": within3,
            "binary_pearson_vs_calibration_lattice": rho,
            "duplicate_rule_70pct_triggered": bool(within3 > 0.70),
        },
        "uses_catalogue_in_surface": False,
        "new_tiff_generated": False,
        "slot_selected": False,
        "experiments_run_this_session": 2,
        "experiment_cap": 3,
        "verdict": "promote" if (vs_lattice["ci95_strictly_positive"] and bool(canary.get("passed"))) else "negative",
        "verdict_note": "promote here means only: beats the budget-matched lattice control with a positive paired CI. It is NOT a leaderboard estimate and does not clear the lane duplicate rule.",
        "cache_sha256": cache["sha256"],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(card, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")
    print(json.dumps({k: card[k] for k in ("holdout", "random_k", "lattice_subset", "paired_vs_random_k",
                                           "paired_vs_lattice_subset", "fold_shortfall_dots",
                                           "registry_global_overlap", "verdict")}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
