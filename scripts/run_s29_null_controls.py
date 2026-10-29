#!/usr/bin/env python3
"""S29 experiment 1 of 3: fixed-budget null and catalogue-only controls on the shared holdout.

Purpose (a diagnostic, not a candidate): does the shared buffered hide-and-recover evaluator
distinguish geology from budget-matched geology-blind placement? Three controls, each placing
K = 37,654 dots per held-out fold on cells that are NOT visible catalogue faults:

  1. random-K          : uniform random cells (same control as S28, same seed 20261029)
  2. lattice-subset    : random K nodes of the registered spacing-five calibration lattice
                         (GEMSDOE13 control raster; geology-blind coverage pattern)
  3. visible-proximity : the K eligible cells nearest to VISIBLE catalogue faults only
                         (uses fold.visible exactly as the protocol allows; hidden faults unread)

No geological layer is used. No DTI is a leaderboard estimate. Every number is HOLDOUT-DTI.
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
from run_s28_tcb import (  # noqa: E402  reuse the verified S28 harness functions; no private fork
    BUFFER_PX,
    CONTROL_PATH,
    K_DOTS,
    random_control,
    read_footprint_and_catalogue,
    sha256_file,
)

OUT = ROOT / "evidence/s29_null_controls.json"
SEED = 20261029


def lattice_subset_control(ho, footprint: np.ndarray, lattice: np.ndarray, seed: int = SEED):
    rng = np.random.default_rng(seed)
    predictions = []
    for fold in ho.folds:
        eligible = footprint & ~fold["visible"] & lattice
        ids = np.flatnonzero(eligible.ravel())
        if len(ids) < K_DOTS:
            raise ValueError("Lattice has fewer eligible nodes than the fixed budget")
        mask = np.zeros(footprint.size, dtype=bool)
        mask[rng.choice(ids, size=K_DOTS, replace=False)] = True
        predictions.append(mask.reshape(footprint.shape))
    return predictions


def visible_proximity_control(ho, footprint: np.ndarray, random_predictions, seed: int = SEED):
    """Catalogue-proximity placement INSIDE the scored quadrant, budget matched to random-K.

    Within each fold, the number of dots equals the random-K dots that fall inside the scored
    quadrant (the only dots the evaluator reads). Cells are chosen nearest to VISIBLE faults.
    Whole components touching the quadrant and its 15 px collar are hidden, so visible faults
    sit >= BUFFER_PX away from the scored region; this control measures that structural limit.
    """
    rng = np.random.default_rng(seed + 1)
    predictions = []
    for fold, rnd in zip(ho.folds, random_predictions):
        k_scope = int((rnd & fold["valid"]).sum())
        eligible = fold["valid"] & ~fold["visible"]
        dist = distance_transform_edt(~fold["visible"])
        ids = np.flatnonzero(eligible.ravel())
        key = dist.ravel()[ids] + rng.random(len(ids)) * 1e-3
        chosen = ids[np.argpartition(key, k_scope - 1)[:k_scope]]
        mask = np.zeros(footprint.size, dtype=bool)
        mask[chosen] = True
        predictions.append(mask.reshape(footprint.shape))
    return predictions


def main() -> int:
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if sha256_file(CONTROL_PATH) != "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2":
        raise SystemExit("Calibration lattice hash mismatch; refusing to run")
    shared = load_shared(ROOT)
    footprint, catalogue = read_footprint_and_catalogue()
    with rasterio.open(CONTROL_PATH) as src:
        lattice = (src.read(1) == 1) & footprint
    ho = shared.holdout.SegmentHoldout(footprint, catalogue, buffer_px=BUFFER_PX)

    controls_random = random_control(ho, footprint, seed=SEED)
    controls = {
        "random_k": controls_random,
        "lattice_subset": lattice_subset_control(ho, footprint, lattice),
        "visible_proximity": visible_proximity_control(ho, footprint, controls_random),
    }
    for name, preds in controls.items():
        for p, fold in zip(preds, ho.folds):
            assert not (p & fold["visible"]).any(), f"{name} placed on visible catalogue"
            if name != "visible_proximity":
                assert int(p.sum()) == K_DOTS, name
    structural = {
        "min_distance_visible_to_scored_quadrant_px": [
            float(distance_transform_edt(~fold["visible"])[fold["valid"]].min()) for fold in ho.folds
        ],
        "scored_dots_per_fold_random_k": [int((p & f["valid"]).sum()) for p, f in zip(controls_random, ho.folds)],
        "scored_dots_per_fold_visible_proximity": [
            int((p & f["valid"]).sum()) for p, f in zip(controls["visible_proximity"], ho.folds)
        ],
    }

    summaries = {name: ho.summarize(preds) for name, preds in controls.items()}
    paired = {
        "lattice_subset_vs_random_k": ho.compare_paired(controls["lattice_subset"], controls["random_k"]),
        "visible_proximity_vs_random_k": ho.compare_paired(controls["visible_proximity"], controls["random_k"]),
    }

    def brief(s):
        return {
            "label": "HOLDOUT-DTI",
            "evaluator_version": s["evaluator_version"],
            "dti": float(s["dti"]),
            "ci95": s["ci95"]["interval"],
            "withheld_positives": int(s["n_withheld_positive_pixels"]),
            "n_emitted": int(s["n_emitted"]),
            "recall_w": float(s["TP_w"]) / float(s["n_truth"]),
        }

    card = {
        "run_card_schema": "s29-null-controls-v1",
        "run_id": "S29-NULL-CONTROLS-20261029",
        "started_at_utc": started,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "purpose": "Diagnostic: does the shared holdout separate geology from budget-matched geology-blind placement?",
        "budget_dots_per_fold": K_DOTS,
        "buffer_px": BUFFER_PX,
        "controls": {name: brief(summaries[name]) for name in controls},
        "paired": {
            name: {
                "candidate_dti": p["candidate_dti"],
                "baseline_dti": p["baseline_dti"],
                "paired_delta_dti": p["paired_delta_dti"],
                "paired_delta_ci95": list(p["paired_delta_ci95"]),
                "fold_wins": p["fold_wins"],
                "n_folds": p["n_folds"],
            }
            for name, p in paired.items()
        },
        "structural_checks": structural,
        "inputs": {
            "calibration_lattice_sha256": sha256_file(CONTROL_PATH),
            "lattice_dots_in_footprint": int(lattice.sum()),
            "catalogue_positive_pixels": int(catalogue.sum()),
        },
        "uses_geology_layers": False,
        "leaderboard_estimate": None,
        "new_tiff_generated": False,
        "slot_selected": False,
        "experiments_run_this_session": 1,
        "experiment_cap": 3,
        "verdict": "diagnostic",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps(card["controls"], indent=2))
    print(json.dumps(card["paired"], indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
