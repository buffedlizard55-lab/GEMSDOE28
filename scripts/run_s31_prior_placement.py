#!/usr/bin/env python3
"""S31 experiment 1 of <=3: placement-prior comparison on the shared buffered holdout.

Question (preregistered before the run): among catalogue-free placement priors, does any
recover withheld catalogue segments better than the budget-matched random-K control, and
better than the S30 refill prior (RTP ridge gradient), under the same-evaluator protocol?

Arms (each places K = 37,654 dots per fold on eligible = footprint & ~visible catalogue,
after 1-px across-strike ridge NMS; same budget and eligibility as the S28/S29 harness):

  random_k   budget-matched geology-blind control (seed 20261031)
  rtp_ridge  S30 refill prior: gradient magnitude of smoothed RTP (band 'rtp'), sigma 1.5
  joint_px   H-S31-1 JPX: geometric mean of percentile ranks of smoothed RTP gradient and
             isostatic-gravity gradient (two independent potential fields must agree)
  gsd_strain H-S31-2 GSD: geometric mean of percentile ranks of smoothed geodetic shear
             rate and dilatation rate (active deformation without surface expression)
  cs_step    H-S31-3 CS: gradient magnitude of smoothed depth-to-basement (step edges at
             basin-bounding faults)

Every surface is tested alone by the shared leakage canary (AUC > 0.90 = leakage until
explained). Before placement, each surface's Spearman correlation with the nine-site
registry density map is computed (lane gate 0.90). Every number emitted here is
HOLDOUT-DTI (evaluator: shared pinned template, buffer 15 px, pooled TPw/FPw/FNw,
alpha 0.2, beta 0.8, 300 m triangular kernel). Nothing here is a leaderboard estimate.

Run:  python scripts/run_s31_prior_placement.py
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter, gaussian_gradient_magnitude

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

from gems27 import uniqueness as U  # noqa: E402
from gems27.shared_template import load_shared  # noqa: E402
from run_s28_tcb import K_DOTS, random_control, read_footprint_and_catalogue, sha256_file  # noqa: E402

OUT = ROOT / "evidence/s31_prior_placement.json"
REGISTRY = ROOT / "data/registry_tifs/manifest.json"
FEATURES = ROOT / "data/prepared/features.npy"
FEATURES_META = ROOT / "data/prepared/features.json"
SEED = 20261031
RIDGE_SIGMA = 1.5
SMOOTH_SIGMA = 2.0
SURFACE_GATE = 0.90
N_SAMPLE = 200_000


def load_feature_2d(name: str, shape: tuple[int, int], footprint: np.ndarray,
                    cache: dict) -> np.ndarray:
    if name in cache:
        return cache[name]
    meta = json.loads(FEATURES_META.read_text())
    idx = meta["names"].index(name)
    table = np.load(FEATURES, mmap_mode="r")
    if table.shape != tuple(meta["shape"]) or table.shape[0] != int(footprint.sum()):
        raise ValueError("Prepared cache does not match its metadata/footprint")
    flat = np.asarray(table[:, idx], dtype=np.float32)
    out = np.full(shape, np.nan, dtype=np.float32)
    out[footprint] = flat  # cache rows are exactly the footprint cells, raster order
    cache[name] = out
    return out


def percentile_rank(x: np.ndarray, footprint: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """Percentile rank of finite x inside the footprint, in [0,1]; outside -> 0."""
    ids = np.flatnonzero(footprint.ravel())
    vals = np.asarray(x, dtype=np.float64).ravel()[ids]
    finite = np.isfinite(vals)
    sample = vals[finite]
    if sample.size > N_SAMPLE:
        sample = rng.choice(sample, size=N_SAMPLE, replace=False)
    sample = np.sort(sample)
    ranks = np.zeros(x.size, dtype=np.float32)
    ranks[ids[finite]] = (
        np.searchsorted(sample, vals[finite], side="right") / max(sample.size, 1))
    return ranks.reshape(x.shape)


def registry_density(footprint: np.ndarray) -> tuple[np.ndarray, int]:
    """Smoothed per-cell registry dot density (the S30 lane comparator)."""
    manifest = json.loads(REGISTRY.read_text())
    acc = np.zeros(footprint.shape, np.float32)
    n = 0
    for item in manifest["files"]:
        path = ROOT / item["local"]
        with rasterio.open(path) as src:
            if src.shape != footprint.shape:
                continue
            v = src.read(1).astype(np.float32)
        acc += U.registry_dot_mask(v, footprint)
        n += 1
    return gaussian_filter(acc, 2.0), n


def surface_spearman(surface: np.ndarray, density: np.ndarray, footprint: np.ndarray,
                     rng: np.random.Generator) -> float:
    from scipy.stats import spearmanr

    ids = rng.choice(np.flatnonzero(footprint.ravel()),
                     size=min(N_SAMPLE, int(footprint.sum())), replace=False)
    a = np.asarray(surface, dtype=np.float64).ravel()[ids]
    b = np.asarray(density, dtype=np.float64).ravel()[ids]
    ok = np.isfinite(a) & np.isfinite(b)
    rho, _ = spearmanr(a[ok], b[ok])
    return float(rho)


def main() -> int:
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    t0 = time.time()
    shared = load_shared(ROOT)
    footprint, catalogue = read_footprint_and_catalogue()
    shape = footprint.shape
    ho = shared.holdout.SegmentHoldout(footprint, catalogue, buffer_px=15)
    rng = np.random.default_rng(SEED)
    cache: dict[str, np.ndarray] = {}

    # ---- surfaces (catalogue-free; built from prepared features only) -------------
    rtp_ridge = gaussian_gradient_magnitude(
        gaussian_filter(load_feature_2d("rtp", shape, footprint, cache), RIDGE_SIGMA), RIDGE_SIGMA)
    grav_ridge = gaussian_gradient_magnitude(
        gaussian_filter(load_feature_2d("iso_grav_anom", shape, footprint, cache), RIDGE_SIGMA), RIDGE_SIGMA)
    shear = gaussian_filter(load_feature_2d("geod_shearrate", shape, footprint, cache), SMOOTH_SIGMA)
    dilat = gaussian_filter(load_feature_2d("geod_dilaterate", shape, footprint, cache), SMOOTH_SIGMA)
    dbase_step = gaussian_gradient_magnitude(
        gaussian_filter(load_feature_2d("depth_to_base_surf", shape, footprint, cache), SMOOTH_SIGMA),
        SMOOTH_SIGMA)

    surfaces = {
        "rtp_ridge": rtp_ridge.astype(np.float32),
        "joint_px": np.sqrt(percentile_rank(rtp_ridge, footprint, rng)
                            * percentile_rank(grav_ridge, footprint, rng)),
        "gsd_strain": np.sqrt(percentile_rank(shear, footprint, rng)
                              * percentile_rank(dilat, footprint, rng)),
        "cs_step": dbase_step.astype(np.float32),
    }

    # ---- leakage canary: every surface and the underlying raw layers alone ---------
    canary = ho.canary({
        "layer_rtp_ridge": surfaces["rtp_ridge"],
        "layer_grav_ridge": grav_ridge.astype(np.float32),
        "layer_geod_shear": shear.astype(np.float32),
        "layer_geod_dilat": dilat.astype(np.float32),
        "layer_depth_base_step": surfaces["cs_step"],
        **surfaces,
    }, seed=SEED)
    del rtp_ridge, grav_ridge, shear, dilat, dbase_step

    # ---- pre-placement surface vs registry density (lane gate 0.90) --------------
    density, n_registry = registry_density(footprint)
    surface_checks = {
        name: {"spearman_vs_registry_density": surface_spearman(s, density, footprint, rng),
               "passes_lane_gate_abs_lt_0_90": None}
        for name, s in surfaces.items()
    }
    for chk in surface_checks.values():
        chk["passes_lane_gate_abs_lt_0_90"] = (
            abs(chk["spearman_vs_registry_density"]) < SURFACE_GATE)
    del density

    # ---- placement per fold ------------------------------------------------------
    predictions: dict[str, list[np.ndarray]] = {
        "random_k": random_control(ho, footprint, seed=SEED)}
    for name, surface in surfaces.items():
        preds = []
        for fold in ho.folds:
            eligible = footprint & ~fold["visible"]
            nms = shared.metric.ridge_nms(surface, eligible, sigma=1.0)
            pred = shared.metric.select_top_positive(surface, nms & eligible, K_DOTS).astype(bool)
            if int(pred.sum()) < 1000:
                raise ValueError(f"Arm {name} placed too few dots in {fold['name']}")
            if (pred & fold["visible"]).any():
                raise ValueError(f"Arm {name} placed on the visible catalogue")
            preds.append(pred)
        predictions[name] = preds

    # ---- scoring -----------------------------------------------------------------
    summaries = {name: ho.summarize(preds) for name, preds in predictions.items()}
    paired = {
        f"{name}_vs_random_k": ho.compare_paired(predictions[name], predictions["random_k"],
                                                 seed=SEED)
        for name in ("rtp_ridge", "joint_px", "gsd_strain", "cs_step")
    }
    paired["joint_px_vs_rtp_ridge"] = ho.compare_paired(predictions["joint_px"],
                                                        predictions["rtp_ridge"], seed=SEED)

    result = {
        "schema": "s31-prior-placement/v1",
        "session": "S31",
        "experiment": "E1 (of at most 3): placement-prior comparison on the shared holdout",
        "started_utc": started,
        "runtime_seconds": round(time.time() - t0, 1),
        "branch": "arena/6c34b640-gemsdoe28",
        "hypothesis": (
            "A catalogue-free conjunction prior (two independent potential fields, or geodetic "
            "strain, or a basement step edge) places the fixed 37,654-dot budget nearer withheld "
            "catalogue segments than random-K and than the single-field RTP ridge prior."
        ),
        "named_non_fault_mimics": {
            "joint_px": ("Igneous intrusion contacts and basin-edge density contrasts mimic "
                         "RTP x gravity coherence."),
            "gsd_strain": ("Plate-boundary-wide smooth strain gradients and aquifer extraction "
                           "mimic shear/dilatation ridges."),
            "cs_step": "Playa edges and lithologic contacts mimic basement depth steps.",
            "rtp_ridge": "Single-field magnetic contacts and dike swarms mimic RTP ridges.",
        },
        "budget": {"k_dots_per_fold": K_DOTS, "buffer_px": 15, "seed": SEED,
                   "eligible": "footprint & ~visible catalogue; 1-px ridge NMS"},
        "registry": {"n_comparable_rasters": n_registry,
                     "manifest_sha256": sha256_file(REGISTRY)},
        "prepared_features_sha256": sha256_file(FEATURES),
        "canary": canary,
        "surface_checks": surface_checks,
        "holdout": {"label": "HOLDOUT-DTI", "evaluator": summaries["random_k"]["evaluator_version"],
                    "n_withheld_positive_pixels": summaries["random_k"]["n_withheld_positive_pixels"],
                    "summaries": summaries, "paired_vs_random_k": paired},
        "promotion_reference": {
            "random_k_control_s29": 0.0674060,
            "lattice_subset_control_s29": 0.0748360,
            "note": ("Historical HOLDOUT-DTI values from evidence/s29_lattice_run_card.json, same "
                     "evaluator family; not leaderboard estimates."),
        },
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps({
        "holdout_dti": {k: round(v["dti"], 6) for k, v in summaries.items()},
        "paired": {k: {"delta": round(v["paired_delta_dti"], 6),
                       "ci95": [round(c, 6) for c in v["paired_delta_ci95"]],
                       "positive": v["ci95_strictly_positive"],
                       "fold_wins": v["fold_wins"]}
                   for k, v in paired.items()},
        "canary_passed": canary["passed"],
        "canary_auc": {k: round(v["pooled_auc"], 4) for k, v in canary["features"].items()},
        "surface_checks": {k: round(v["spearman_vs_registry_density"], 4)
                           for k, v in surface_checks.items()},
        "runtime_seconds": result["runtime_seconds"],
    }, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
