#!/usr/bin/env python3
"""S25 · PCSE (phase-congruent scarp energy): one frozen operator, holdout, novelty, GeoTIFF.

Hypothesis (knowledge/66_s23_preregistration.md, candidate 1): a subtle scarp or buried displacement
shows a cross-profile STEP (odd, first-derivative) with consistent polarity across scales, and little
RIDGE/TROUGH (even, second-derivative) energy. The operator is catalogue-free: it reads only the
training layers ``det_elev``, ``tmi`` and ``iso_grav_anom`` from the restored template raster. Because
no catalogue feature is used, the only catalogue dependence is the shared mask (visible faults in each
holdout fold; all catalogue pixels for the final file).

Operator (fixed here, not tuned):
  1. Fill invalid cells by normalized Gaussian interpolation (sigma 7 px), remove a 20 px background,
     scale by robust MAD. (Pixel = 100 m, template grid EPSG:32611.)
  2. For 4 scales sigma in {1,2,4,7} px and 8 orientations theta, form the directional odd response
     (first derivative across strike, scale-normalized by sigma) and even response (second derivative).
  3. Per orientation: phase = |sum_s odd| / (sum_s |A_s| + eps), where A_s = sqrt(odd^2+even^2);
     stepfrac = sum_s|odd| / (sum_s(|odd|+|even|)+eps); energy = max_s-sum amplitude / MAD.
     layer score = max_theta(phase * stepfrac) * energy_norm. Final surface = mean over the 3 layers.
  4. 1-px ridge NMS (shared ``metric.ridge_nms``), then top-K over eligible cells (shared
     ``metric.select_top_positive``). K = 37,654 dots (the budget label used by other lanes).

Holdout: shared ``SegmentHoldout`` (whole-component, buffered 15 px = 1.5 km, quadrant folds), pooled
DTI alpha .2 / beta .8 / 300 m triangular kernel, paired 10 km block bootstrap vs a seeded random-K
control. Canary: each feature alone (AUC > 0.90 = leakage until explained). Novelty: dot-overlap and
Spearman against every binary raster in docs/downloads.

Writes: docs/downloads/*.tif (+zip, note), evidence/s25_pcse_*.json. Never contacts DrivenData.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "data" / "shared_template" / "src"))

from gems import holdout as H  # noqa: E402  (shared evaluator, restored template)
from gems import metric as M  # noqa: E402
from gems import novelty as N  # noqa: E402

from gems27 import paths, submission  # noqa: E402

FAMILY = "gems28"
SLUG = "s25-pcse-scarp-energy-k37654"
DATE = "20261028"
K_DOTS = 37654
SCALES = (1, 2, 4, 7)
N_THETA = 8
EVIDENCE = ROOT / "evidence" / "s25_pcse_run_card.json"
HOLDOUT_JSON = ROOT / "evidence" / "s25_pcse_holdout.json"
NOVELTY_JSON = ROOT / "evidence" / "s25_pcse_novelty.json"
DOWNLOADS = ROOT / "docs" / "downloads"
LAYERS = {"det_elev": 12, "tmi": 14, "iso_grav_anom": 13}  # verified in scripts/prepare_data.py


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def robust_scale(x: np.ndarray, valid: np.ndarray) -> float:
    v = x[valid]
    med = np.median(v)
    mad = 1.4826 * np.median(np.abs(v - med))
    return float(mad) if mad > 0 else float(np.std(v) or 1.0)


def fill_and_highpass(raw: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Normalized-convolution fill (sigma 7 px) + 20 px background removal + MAD scaling."""
    # float32 minimum (-3.4e38) is the training raster's missing-data sentinel (3,061 footprint cells).
    valid = footprint & np.isfinite(raw) & (np.abs(raw) < 1e30)
    w = valid.astype(np.float64)
    x = np.where(valid, raw, 0.0).astype(np.float64)
    fill = gaussian_filter(x, 7) / np.maximum(gaussian_filter(w, 7), 1e-9)
    filled = np.where(valid, x, fill)
    hp = filled - gaussian_filter(filled, 20)
    return (hp / robust_scale(hp, footprint)).astype(np.float32)


def pcse_layer(hp: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    eps = 1e-6
    best_pc = np.zeros(hp.shape, np.float32)
    best_e = np.zeros(hp.shape, np.float32)
    best_score = np.zeros(hp.shape, np.float32)
    thetas = np.arange(N_THETA) * np.pi / N_THETA
    # Precompute derivative fields per scale (order = (row, col) for scipy).
    fields = {}
    for s in SCALES:
        fields[s] = {
            "gy": gaussian_filter(hp, s, order=(1, 0)) * s,
            "gx": gaussian_filter(hp, s, order=(0, 1)) * s,
            "gyy": gaussian_filter(hp, s, order=(2, 0)) * s * s,
            "gxx": gaussian_filter(hp, s, order=(0, 2)) * s * s,
            "gxy": gaussian_filter(hp, s, order=(1, 1)) * s * s,
        }
    for th in thetas:
        c, sn = np.cos(th), np.sin(th)
        odd_sum = np.zeros(hp.shape, np.float32)
        amp_sum = np.zeros(hp.shape, np.float32)
        abs_odd = np.zeros(hp.shape, np.float32)
        abs_even = np.zeros(hp.shape, np.float32)
        for s in SCALES:
            f = fields[s]
            odd = (c * f["gx"] + sn * f["gy"]).astype(np.float32)
            even = (c * c * f["gxx"] + 2 * c * sn * f["gxy"] + sn * sn * f["gyy"]).astype(np.float32)
            odd_sum += odd
            amp_sum += np.sqrt(odd * odd + even * even)
            abs_odd += np.abs(odd)
            abs_even += np.abs(even)
        phase = np.abs(odd_sum) / (amp_sum + eps)
        stepfrac = abs_odd / (abs_odd + abs_even + eps)
        pc = (phase * stepfrac).astype(np.float32)
        upd = pc > best_pc
        best_pc = np.where(upd, pc, best_pc)
        best_e = np.maximum(best_e, amp_sum)
    e_scale = robust_scale(best_e, footprint)
    energy = best_e / e_scale
    best_score = best_pc * np.log1p(energy)
    return np.where(footprint, best_score, 0.0).astype(np.float32)


def build_surface(footprint: np.ndarray) -> tuple[np.ndarray, dict]:
    layers = {}
    with rasterio.open(paths.TRAINING) as ds:
        for name, band in LAYERS.items():
            raw = ds.read(band).astype(np.float64)
            layers[name] = fill_and_highpass(raw, footprint)
    per = {k: pcse_layer(v, footprint) for k, v in layers.items()}
    surface = np.mean(np.stack(list(per.values())), axis=0).astype(np.float32)
    surface = np.where(footprint, surface, 0.0).astype(np.float32)
    return surface, {"layers": layers, "per_layer": per}


def select_dots(score: np.ndarray, eligible: np.ndarray, k: int) -> np.ndarray:
    nms = M.ridge_nms(score, eligible, sigma=1.0)
    return M.select_top_positive(score, nms & eligible, k).astype(bool)


def main() -> int:
    t0 = time.time()
    template = paths.TEMPLATE
    with rasterio.open(template) as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(paths.LABELS) as ds:
        lbl = ds.read(1)
    catalogue = footprint & np.isfinite(lbl) & (lbl > 0.5)
    assert int(footprint.sum()) == 5167373, int(footprint.sum())

    surface, parts = build_surface(footprint)
    print(f"surface built in {time.time()-t0:.0f}s; footprint={int(footprint.sum())}", flush=True)

    # ---- Holdout -----------------------------------------------------------------------------
    ho = H.SegmentHoldout(footprint, catalogue, buffer_px=15)
    preds, rand_preds = [], []
    rng = np.random.default_rng(20261028)
    for fold in ho.folds:
        eligible = footprint & ~fold["visible"]
        p = select_dots(surface, eligible, K_DOTS)
        preds.append(p.astype(np.int8))
        idx = np.flatnonzero(eligible.ravel())
        r = np.zeros(footprint.size, bool)
        r[rng.choice(idx, size=min(K_DOTS, idx.size), replace=False)] = True
        rand_preds.append(r.reshape(footprint.shape).astype(np.int8))
    summary = ho.summarize(preds)
    control = ho.summarize(rand_preds)
    paired = ho.compare_paired(preds, rand_preds)

    canary_features = {
        "pcse_surface": surface,
        "det_elev_highpass": parts["layers"]["det_elev"],
        "tmi_highpass": parts["layers"]["tmi"],
        "iso_grav_anom_highpass": parts["layers"]["iso_grav_anom"],
    }
    canary = ho.canary(canary_features)

    # ---- Final dots (whole footprint, catalogue excluded) -------------------------------------
    eligible_final = footprint & ~catalogue
    final = select_dots(surface, eligible_final, K_DOTS)
    assert int(final.sum()) == K_DOTS, int(final.sum())
    overlap_cat = int((final & catalogue).sum())
    assert overlap_cat == 0

    # ---- Novelty vs every binary registry raster in docs/downloads ----------------------------
    reg_rows = []
    sv = surface[footprint].astype(np.float64)
    surf_ranks = rankdata(sv)  # surface is finite everywhere in the footprint (sentinel-filled)
    for tif in sorted(DOWNLOADS.glob("*.tif")):
        with rasterio.open(tif) as ds:
            if ds.shape != footprint.shape:
                reg_rows.append({"file": tif.name, "skipped": "shape mismatch"})
                continue
            ref = ds.read(1)
        ref_bin = np.isfinite(ref) & (ref > 0.5) & footprint
        ov = N.dot_overlap(final, ref_bin, radius_px=3.0)
        both = np.isfinite(ref[footprint])
        rv = ref[footprint][both].astype(np.float64)
        if not rv.size:
            rho_surface = None
        elif both.all():
            rho_surface = N.rank_correlation(surf_ranks, rv)
        else:  # ranks must be recomputed on the valid subset, never subsetted from the full array
            rho_surface = N.correlation(sv[both], rv)
        rho_final = N.correlation(final[footprint][both].astype(np.float64), rv) if rv.size else None
        reg_rows.append({
            "file": tif.name,
            "sha256": sha256_file(tif),
            "candidate_within_3px_of_reference": ov["candidate_within_3px_of_reference"],
            "reference_within_3px_of_candidate": ov["reference_within_3px_of_candidate"],
            "reference_dots": ov["reference_dots"],
            "spearman_surface_vs_reference": rho_surface,
            "spearman_final_vs_reference": rho_final,
            "duplicate_flag": bool(N.is_duplicate(rho_final, ov["candidate_within_3px_of_reference"])),
        })
    max_overlap = max((r.get("candidate_within_3px_of_reference") or 0.0) for r in reg_rows)
    max_rho_surface = max(abs(r["spearman_surface_vs_reference"]) for r in reg_rows
                          if r.get("spearman_surface_vs_reference") is not None)
    dup_any = any(r.get("duplicate_flag") for r in reg_rows)

    # ---- Write submission ---------------------------------------------------------------------
    pred_clean = np.where(eligible_final & final, np.float32(1.0), np.float32(0.0)).astype(np.float32)
    cid = submission.scored_content_id(pred_clean, footprint, catalogue)
    nan_name = submission.make_filename(FAMILY, SLUG, DATE, cid, "nan")
    nan_path = DOWNLOADS / nan_name
    submission.write_geotiff(pred_clean, template, nan_path, outside="nan")
    v = submission.verify_geotiff(nan_path, template)
    zip_path = submission.zip_single(nan_path)

    result = {
        "run_card_schema": "s25-pcse-v1",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hypothesis": "H-PCSE: cross-profile step (odd) energy with cross-scale polarity agreement, "
                      "minus ridge (even) energy, over det_elev/tmi/iso_grav_anom; catalogue-free operator",
        "mechanism": "Odd/even quadrature ratio at 100-700 m scales; scarps give consistent step phase",
        "named_non_fault_mimic": "terrace risers, roads, paleoshorelines, unfaulted lithologic contacts",
        "evaluator": summary["evaluator_version"],
        "holdout_dti": {
            "label": "HOLDOUT-DTI",
            "value": summary["dti"],
            "components": {k: summary[k] for k in ("TP_w", "FP_w", "FN_w", "n_truth", "n_emitted")},
            "n_withheld_positive_pixels": summary["n_withheld_positive_pixels"],
            "ci95": summary["ci95"],
        },
        "control_random_k_holdout_dti": {"label": "HOLDOUT-DTI", "value": control["dti"],
                                         "ci95": control["ci95"]},
        "paired_vs_random_k": paired,
        "canary": canary,
        "novelty": {
            "max_dot_overlap_within_3px_candidate_side": max_overlap,
            "max_abs_surface_spearman": max_rho_surface,
            "any_duplicate_flag": dup_any,
            "rule": "dup if overlap>0.70 or |rho|>0.90 (shared novelty.is_duplicate)",
            "details_file": str(NOVELTY_JSON.relative_to(ROOT)),
        },
        "budget_dots": int(final.sum()),
        "emitted_on_catalogue": overlap_cat,
        "submission": {
            "name": nan_name,
            "zip": zip_path.name,
            "sha256_tif": v["sha256"],
            "sha256_zip": submission.sha256_file(zip_path),
            "note_max_chars": 140,
        },
        "validator": {k: v[k] for k in v if k not in ("file", "bytes", "sha256")},
        "verdict": "pending-review",
        "runtime_seconds": round(time.time() - t0, 1),
    }
    HOLDOUT_JSON.write_text(json.dumps({"holdout": summary, "control": control, "paired": paired,
                                        "canary": canary}, indent=2, default=float) + "\n")
    NOVELTY_JSON.write_text(json.dumps(reg_rows, indent=2, default=float) + "\n")
    EVIDENCE.write_text(json.dumps(result, indent=2, default=float) + "\n")
    print(json.dumps({k: result[k] for k in ("holdout_dti", "control_random_k_holdout_dti",
                                              "novelty", "submission", "budget_dots")},
                     indent=2, default=float))
    return 0 if v.get("hard_checks_passed") and not dup_any else 2


if __name__ == "__main__":
    raise SystemExit(main())
