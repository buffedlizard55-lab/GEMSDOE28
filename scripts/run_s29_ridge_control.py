#!/usr/bin/env python3
"""S29 experiment 3 of 3 (final allowed): isolate the ranking signal in the dispersed TCB result.

Same ridge-NMS candidate geometry and the same 5 px minimum spacing as experiment 2, but the
ordering is RANDOM (seeded) instead of TCB-strength. If random ordering matches the TCB ordering,
the holdout gain is ridge geometry plus spacing, not the TCB operator. Diagnostic only.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems27.shared_template import load_shared  # noqa: E402
from gems27.tcb import build_surface  # noqa: E402
from run_s28_tcb import (  # noqa: E402
    BUFFER_PX, CONTROL_PATH, K_DOTS, random_control, read_cached_layers, read_footprint_and_catalogue,
)
from run_s29_dispersion import R_MIN, dispersed_top_k  # noqa: E402
from run_s29_null_controls import lattice_subset_control  # noqa: E402

OUT = ROOT / "evidence/s29_ridge_control_run_card.json"
SEED = 20261029


def main() -> int:
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    shared = load_shared(ROOT)
    footprint, catalogue = read_footprint_and_catalogue()
    layers, _ = read_cached_layers(footprint)
    surface, _ = build_surface(layers, footprint)
    with rasterio.open(CONTROL_PATH) as src:
        lattice = (src.read(1) == 1) & footprint
    ho = shared.holdout.SegmentHoldout(footprint, catalogue, buffer_px=BUFFER_PX)
    rng = np.random.default_rng(SEED + 7)
    random_priority = rng.random(surface.shape).astype(np.float64)

    preds = []
    for fold in ho.folds:
        eligible = footprint & ~fold["visible"]
        dots, _ = dispersed_top_k(shared, surface, eligible, K_DOTS, R_MIN, priority=random_priority)
        assert not (dots & fold["visible"]).any()
        preds.append(dots)
    random_preds = random_control(ho, footprint, seed=SEED)
    lattice_preds = lattice_subset_control(ho, footprint, lattice, seed=SEED)

    s = ho.summarize(preds)
    rnd = ho.summarize(random_preds)
    lat = ho.summarize(lattice_preds)
    pr = ho.compare_paired(preds, random_preds)
    pl = ho.compare_paired(preds, lattice_preds)
    prev = json.loads((ROOT / "evidence/s29_dispersion_run_card.json").read_text())
    tcb = prev["holdout"]["dti"]
    card = {
        "run_card_schema": "s29-ridge-control-v1",
        "run_id": "S29-RIDGE-RANDOM-PRIORITY-20261029",
        "started_at_utc": started,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "question": "Is the dispersed-TCB gain due to TCB ranking, or to ridge geometry plus spacing?",
        "control": "Same ridge-NMS candidates and R_MIN=5 px spacing; random seeded priority replaces TCB ranking.",
        "holdout": {"label": "HOLDOUT-DTI", "evaluator_version": s["evaluator_version"], "dti": float(s["dti"]),
                    "ci95": s["ci95"]["interval"], "withheld_positives": int(s["n_withheld_positive_pixels"])},
        "reference_dispersed_tcb_holdout_dti": tcb,
        "reference_random_k_holdout_dti": float(rnd["dti"]),
        "reference_lattice_subset_holdout_dti": float(lat["dti"]),
        "paired_vs_random_k": {"paired_delta_dti": pr["paired_delta_dti"], "ci95": list(pr["paired_delta_ci95"]),
                               "fold_wins": pr["fold_wins"]},
        "paired_vs_lattice_subset": {"paired_delta_dti": pl["paired_delta_dti"], "ci95": list(pl["paired_delta_ci95"]),
                                     "fold_wins": pl["fold_wins"]},
        "new_tiff_generated": False,
        "slot_selected": False,
        "experiments_run_this_session": 3,
        "experiment_cap": 3,
        "verdict": "diagnostic",
    }
    OUT.write_text(json.dumps(card, indent=2, allow_nan=False, default=str) + "\n", encoding="utf-8")
    print(json.dumps(card, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
