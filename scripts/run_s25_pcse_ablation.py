#!/usr/bin/env python3
"""S25 experiment 2 (diagnostic ablation of the frozen PCSE operator; no GeoTIFF, no upload).

Splits the frozen PCSE score into its two multiplicative factors and scores each alone on the same
shared SegmentHoldout, same K, same folds, same seeds:
  * ``phase_stepfrac_only``  = max_theta(phase * stepfrac)            (step-polarity term only)
  * ``energy_only``          = max_theta(sum_s |A_s|) / MAD           (amplitude term only)
Reuses the frozen preprocessing and derivative code from scripts/run_s25_pcse.py (imported, not copied).
Also records the leakage canary per feature. Writes evidence/s25_pcse_ablation.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "data" / "shared_template" / "src"))

from gems import holdout as H  # noqa: E402

import run_s25_pcse as P  # noqa: E402
from gems27 import paths  # noqa: E402

OUT = ROOT / "evidence" / "s25_pcse_ablation.json"


def components(hp: np.ndarray, footprint: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    eps = 1e-6
    best_pc = np.zeros(hp.shape, np.float32)
    best_e = np.zeros(hp.shape, np.float32)
    fields = {}
    for s in P.SCALES:
        fields[s] = {
            "gy": gaussian_filter(hp, s, order=(1, 0)) * s,
            "gx": gaussian_filter(hp, s, order=(0, 1)) * s,
            "gyy": gaussian_filter(hp, s, order=(2, 0)) * s * s,
            "gxx": gaussian_filter(hp, s, order=(0, 2)) * s * s,
            "gxy": gaussian_filter(hp, s, order=(1, 1)) * s * s,
        }
    for th in np.arange(P.N_THETA) * np.pi / P.N_THETA:
        c, sn = np.cos(th), np.sin(th)
        odd_sum = np.zeros(hp.shape, np.float32)
        amp_sum = np.zeros(hp.shape, np.float32)
        abs_odd = np.zeros(hp.shape, np.float32)
        abs_even = np.zeros(hp.shape, np.float32)
        for s in P.SCALES:
            f = fields[s]
            odd = (c * f["gx"] + sn * f["gy"]).astype(np.float32)
            even = (c * c * f["gxx"] + 2 * c * sn * f["gxy"] + sn * sn * f["gyy"]).astype(np.float32)
            odd_sum += odd
            amp_sum += np.sqrt(odd * odd + even * even)
            abs_odd += np.abs(odd)
            abs_even += np.abs(even)
        pc = (np.abs(odd_sum) / (amp_sum + eps)) * (abs_odd / (abs_odd + abs_even + eps))
        best_pc = np.maximum(best_pc, pc.astype(np.float32))
        best_e = np.maximum(best_e, amp_sum)
    return best_pc, best_e


def main() -> int:
    with rasterio.open(paths.TEMPLATE) as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(paths.LABELS) as ds:
        lbl = ds.read(1)
    catalogue = footprint & np.isfinite(lbl) & (lbl > 0.5)

    phase_layers, energy_layers, hp_layers = [], [], {}
    with rasterio.open(paths.TRAINING) as ds:
        for name, band in P.LAYERS.items():
            hp = P.fill_and_highpass(ds.read(band).astype(np.float64), footprint)
            hp_layers[name] = hp
            pc, e = components(hp, footprint)
            phase_layers.append(np.where(footprint, pc, 0.0))
            energy_layers.append(np.where(footprint, e / P.robust_scale(e, footprint), 0.0))
    phase_surface = np.mean(np.stack(phase_layers), axis=0).astype(np.float32)
    energy_surface = np.mean(np.stack(energy_layers), axis=0).astype(np.float32)

    ho = H.SegmentHoldout(footprint, catalogue, buffer_px=15)
    results = {}
    for label, surface in (("phase_stepfrac_only", phase_surface), ("energy_only", energy_surface)):
        preds = []
        for fold in ho.folds:
            eligible = footprint & ~fold["visible"]
            preds.append(P.select_dots(surface, eligible, P.K_DOTS).astype(np.int8))
        s = ho.summarize(preds)
        results[label] = {
            "label": "HOLDOUT-DTI",
            "dti": s["dti"],
            "ci95": s["ci95"]["interval"],
            "TP_w": s["TP_w"], "FP_w": s["FP_w"], "FN_w": s["FN_w"],
            "n_withheld_positive_pixels": s["n_withheld_positive_pixels"],
        }
    canary = ho.canary({
        "phase_stepfrac_only": phase_surface,
        "energy_only": energy_surface,
    })
    out = {
        "experiment": "S25-exp2 PCSE ablation (diagnostic, frozen K and folds; no GeoTIFF)",
        "results": results,
        "canary": {k: {"pooled_auc": v["pooled_auc"], "leakage_suspected": v["leakage_suspected"]}
                   for k, v in canary["features"].items()},
        "canary_passed": canary["passed"],
        "interpretation": "Each factor alone is an ablation diagnostic; neither is a submission.",
    }
    OUT.write_text(json.dumps(out, indent=2, default=float) + "\n")
    print(json.dumps(out, indent=2, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
