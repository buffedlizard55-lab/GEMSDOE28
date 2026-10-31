#!/usr/bin/env python3
"""S31 experiment 2 of <=3: refill-prior validation in the LOSFO far-field holdout.

Why this protocol: experiment E1 (scripts/run_s31_prior_placement.py) showed that the
buffered interleaved holdout cannot rank placement priors for FAR-FIELD dots: its truth
sits on the catalogue, while a shippable file (and the S30/S31 refill) must place dots
>= 6 px (600 m) off the catalogue, where the interleaved holdout has no truth by
construction (evidence/arm_habitat_decomposition.json; knowledge/77 section 5). The
leave-fault-system-out (LOSFO) protocol in src/gems27/losfo.py is the repository's
documented ADD-arm instrument: whole fault systems held out, a 600 m buffer erased
around every held-out system, truth genuinely off-catalogue.

Question (preregistered): among catalogue-free priors, does any place a fixed per-fold
budget (9,414 dots = 37,654 / 4 quadrants) nearer held-out far-field systems than a
uniform random control, inside the refill habitat (footprint, >= 6 px from the known
catalogue)?

Arms: random (seeded), rtp_ridge (S30 refill prior), joint_px (H-S31-1), gsd_strain
(H-S31-2), cs_step (H-S31-3) — the same surfaces as E1, rebuilt identically.

Every number is HOLDOUT-DTI (shared exact metric, alpha 0.2, beta 0.8, 300 m kernel)
under the LOSFO protocol. It is never a leaderboard estimate. Seeds 210-212 (the
diagnostic's reserved decade 210-219, already partly used).

Run:  python scripts/run_s31_losfo_refill.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, gaussian_gradient_magnitude

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems27 import losfo, metric  # noqa: E402
from gems27.shared_template import load_shared  # noqa: E402
from run_s28_tcb import read_footprint_and_catalogue, sha256_file  # noqa: E402
from run_s31_prior_placement import (  # noqa: E402  reuse the exact surface builders
    FEATURES,
    RIDGE_SIGMA,
    SMOOTH_SIGMA,
    load_feature_2d,
    percentile_rank,
)

OUT = ROOT / "evidence/s31_losfo_refill.json"
SEEDS = (210, 211, 212)
K_FOLD = 9_414          # 37,654 / 4 quadrads, the champion budget per scored quadrant
MIN_CAT_PX = 6          # the refill habitat: >= 600 m from the known catalogue
ARMS = ("random", "rtp_ridge", "joint_px", "gsd_strain", "cs_step")


def build_surfaces(footprint, rng):
    shape = footprint.shape
    cache: dict[str, np.ndarray] = {}
    rtp_ridge = gaussian_gradient_magnitude(
        gaussian_filter(load_feature_2d("rtp", shape, footprint, cache), RIDGE_SIGMA), RIDGE_SIGMA)
    grav_ridge = gaussian_gradient_magnitude(
        gaussian_filter(load_feature_2d("iso_grav_anom", shape, footprint, cache), RIDGE_SIGMA),
        RIDGE_SIGMA)
    shear = gaussian_filter(load_feature_2d("geod_shearrate", shape, footprint, cache), SMOOTH_SIGMA)
    dilat = gaussian_filter(load_feature_2d("geod_dilaterate", shape, footprint, cache), SMOOTH_SIGMA)
    dbase_step = gaussian_gradient_magnitude(
        gaussian_filter(load_feature_2d("depth_to_base_surf", shape, footprint, cache), SMOOTH_SIGMA),
        SMOOTH_SIGMA)
    return {
        "rtp_ridge": rtp_ridge.astype(np.float32),
        "joint_px": np.sqrt(percentile_rank(rtp_ridge, footprint, rng)
                            * percentile_rank(grav_ridge, footprint, rng)),
        "gsd_strain": np.sqrt(percentile_rank(shear, footprint, rng)
                              * percentile_rank(dilat, footprint, rng)),
        "cs_step": dbase_step.astype(np.float32),
    }


def place(surface, eligible, shared, k, rng):
    if surface is None:
        ids = np.flatnonzero(eligible.ravel())
        mask = np.zeros(eligible.size, bool)
        mask[rng.choice(ids, size=min(k, len(ids)), replace=False)] = True
        return mask.reshape(eligible.shape)
    nms = shared.metric.ridge_nms(surface, eligible, sigma=1.0)
    return shared.metric.select_top_positive(surface, nms & eligible, k).astype(bool)


def main() -> int:
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    t0 = time.time()
    shared = load_shared(ROOT)
    footprint, catalogue = read_footprint_and_catalogue()
    rng_global = np.random.default_rng(20261031)
    surfaces = build_surfaces(footprint, rng_global)

    sys_grid, n_systems = losfo.fault_systems(catalogue)
    table = losfo.system_table(sys_grid, n_systems, footprint)
    fold_grid, fold_names = shared.holdout.make_quadrant_folds(footprint)

    cells = []
    arm_dti: dict[str, list[float]] = {a: [] for a in ARMS}
    for seed in SEEDS:
        holdout_fold = losfo.assign_systems_to_folds(table, fold_grid, 4, seed)
        pooled = {a: {"tp": 0.0, "fp": 0.0, "n_truth": 0.0, "dots": 0} for a in ARMS}
        for f_id in range(4):
            split = losfo.build_losfo_split(
                catalogue, sys_grid, holdout_fold, fold_grid, f_id, seed, fold_names)
            truth = split.hidden
            active = split.fold_mask & footprint
            dist_known = distance_transform_edt(~split.known)
            eligible = active & (dist_known >= MIN_CAT_PX)
            for arm in ARMS:
                surface = None if arm == "random" else surfaces[arm]
                pred = place(surface, eligible, shared, K_FOLD, rng_global)
                if (pred & split.known).any():
                    raise ValueError(f"{arm}: placed on the known catalogue")
                r = metric.dti_binary(pred, truth, valid=active)
                pooled[arm]["tp"] += r["TPw"]
                pooled[arm]["fp"] += r["FPw"]
                pooled[arm]["n_truth"] += r["n_truth"]
                pooled[arm]["dots"] += r["n_emitted"]
            cells.append({"seed": seed, "fold": split.name,
                          "n_truth": int(truth.sum()),
                          "min_dist_hidden_to_known_px": split.min_dist_hidden_to_known})
        for arm in ARMS:
            p = pooled[arm]
            denom = p["tp"] + 0.2 * p["fp"] + 0.8 * (p["n_truth"] - p["tp"]) + 1e-7
            arm_dti[arm].append(p["tp"] / denom)

    summary = {
        arm: {
            "dti_per_seed": [round(v, 6) for v in vals],
            "mean_dti": float(np.mean(vals)),
            "std_dti": float(np.std(vals)),
        }
        for arm, vals in arm_dti.items()
    }
    paired = {}
    for arm in ARMS[1:]:
        deltas = np.asarray(arm_dti[arm]) - np.asarray(arm_dti["random"])
        paired[f"{arm}_vs_random"] = {
            "delta_per_seed": [round(float(d), 6) for d in deltas],
            "mean_delta": float(deltas.mean()),
            "seeds_improved": int((deltas > 0).sum()),
            "n_seeds": len(SEEDS),
        }

    result = {
        "schema": "s31-losfo-refill/v1",
        "session": "S31",
        "experiment": "E2 (of at most 3): refill-prior validation, LOSFO far-field protocol",
        "started_utc": started,
        "runtime_seconds": round(time.time() - t0, 1),
        "branch": "arena/6c34b640-gemsdoe28",
        "protocol": {
            "instrument": "src/gems27/losfo.py (leave-fault-system-out, 600 m buffer)",
            "seeds": list(SEEDS),
            "k_dots_per_fold": K_FOLD,
            "habitat": f"footprint cells >= {MIN_CAT_PX} px from the known catalogue",
            "metric": "shared exact DTI, alpha 0.2, beta 0.8, 300 m triangular kernel",
            "truth_is_off_catalogue": True,
            "known_limit": ("Held-out systems are mapped faults; absolute DTI is an upper bound "
                            "for genuinely unmapped faults, not an estimate of leaderboard skill."),
        },
        "n_fault_systems": n_systems,
        "cells": cells,
        "summary": summary,
        "paired_vs_random": paired,
        "input_hashes": {"features": sha256_file(FEATURES)},
    }
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({"summary": summary, "paired": paired,
                      "runtime_seconds": result["runtime_seconds"]}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
