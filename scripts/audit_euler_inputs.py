#!/usr/bin/env python3
"""Audit mirrored magnetic bands and the vertical-derivative sign before any Euler holdout run.

This is an input-convention diagnostic, not a structural interpretation or a label/score test. The
owner-mirrored TIFF is not organizer-authenticated. The Fourier comparison is a local sign/scale check
on Hann-tapered patches and must not be presented as independent calibration of the survey product.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
import scipy
from scipy.stats import pearsonr, spearmanr

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("GEMS_DATA_DIR", ROOT / "data"))
TEMPLATE = DATA / "sample_submission.tif"
TRAINING = DATA / "training_features.tif"
PATCH = 256


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def patch_starts(valid: np.ndarray) -> list[tuple[int, int]]:
    """Choose one all-valid patch in each grid quadrant, deterministically via integral sums."""
    h, w = valid.shape
    integral = np.pad(valid.astype(np.int32), ((1, 0), (1, 0))).cumsum(0).cumsum(1)
    y_mid, x_mid = h // 2, w // 2
    boxes = ((0, y_mid, 0, x_mid), (0, y_mid, x_mid, w),
             (y_mid, h, 0, x_mid), (y_mid, h, x_mid, w))
    out = []
    for r0, r1, c0, c1 in boxes:
        found = None
        for r in range(r0, min(r1 - PATCH + 1, h - PATCH + 1), 32):
            for c in range(c0, min(c1 - PATCH + 1, w - PATCH + 1), 32):
                total = (integral[r + PATCH, c + PATCH] - integral[r, c + PATCH]
                         - integral[r + PATCH, c] + integral[r, c])
                if total == PATCH * PATCH:
                    found = (r, c)
                    break
            if found:
                break
        if found is not None:
            out.append(found)
    if len(out) < 3:
        raise RuntimeError(f"Only {len(out)} fully valid 256x256 patches found")
    return out


def audit() -> dict:
    with rasterio.open(TEMPLATE) as t:
        footprint = np.isfinite(t.read(1))
        grid = {
            "crs": t.crs.to_string(),
            "shape": list(t.shape),
            "transform": list(tuple(t.transform)[:6]),
            "footprint_pixels": int(footprint.sum()),
            "template_sha256": sha256_file(TEMPLATE),
        }
    with rasterio.open(TRAINING) as s:
        if s.count != 19 or s.shape != footprint.shape:
            raise ValueError("Training TIFF band count or grid does not match the template")
        tmi_desc = s.descriptions[13] or ""
        vg_desc = s.descriptions[8] or ""
        hg_desc = s.descriptions[2] or ""
        required = ((14, "tmi"), (9, "tmi_vg"), (3, "tmi_hg"))
        for band, prefix in required:
            description = s.descriptions[band - 1] or ""
            tag_name = s.tags(band).get("band_name", "")
            if not description.startswith(prefix) or tag_name != prefix:
                raise ValueError(f"Unexpected magnetic band {band}: {description!r}, tag={tag_name!r}")
        nodata = s.nodata
        tmi = s.read(14, out_dtype="float32")
        tmi_vg = s.read(9, out_dtype="float32")
        tmi_hg = s.read(3, out_dtype="float32")
        training_sha = sha256_file(TRAINING)
        tags = [s.tags(i) for i in range(1, s.count + 1)]
    valid = footprint & np.isfinite(tmi) & np.isfinite(tmi_vg) & np.isfinite(tmi_hg)
    if nodata is not None:
        valid &= (tmi != np.float32(nodata)) & (tmi_vg != np.float32(nodata)) & (tmi_hg != np.float32(nodata))
    valid &= (np.abs(tmi) < 1e30) & (np.abs(tmi_vg) < 1e30) & (np.abs(tmi_hg) < 1e30)
    valid_pixels = int(valid.sum())
    missing_in_footprint = int((footprint & ~valid).sum())
    valid_outside = int((~footprint & valid).sum())
    if valid_pixels < int(0.999 * footprint.sum()):
        raise ValueError("Too much magnetic no-data inside the template footprint for this audit")

    rows = []
    for r, c in patch_starts(valid):
        a = tmi[r:r + PATCH, c:c + PATCH].astype(np.float64)
        z = tmi_vg[r:r + PATCH, c:c + PATCH].astype(np.float64)
        hm = tmi_hg[r:r + PATCH, c:c + PATCH].astype(np.float64)
        raw = a.copy()
        raw -= raw.mean()
        taper = np.outer(np.hanning(PATCH), np.hanning(PATCH))
        tapered = raw * taper
        fy = 2.0 * np.pi * np.fft.fftfreq(PATCH, d=100.0)
        fx = 2.0 * np.pi * np.fft.fftfreq(PATCH, d=100.0)
        wave = np.hypot(fy[:, None], fx[None, :])
        vertical_down_m = np.fft.ifft2(np.fft.fft2(tapered) * wave).real
        # Edge-excluded cellwise diagnostics; they characterize convention only.
        sl = (slice(16, -16), slice(16, -16))
        zv = z[sl].ravel()
        dv = vertical_down_m[sl].ravel()
        valid_pair = np.isfinite(zv) & np.isfinite(dv)
        zv, dv = zv[valid_pair], dv[valid_pair]
        denom = float(np.dot(dv, dv))
        fit_scale = float(np.dot(zv, dv) / denom) if denom else None
        row, col = np.gradient(raw, 100.0, 100.0)
        horizontal_from_tmi = np.hypot(row, col)
        hvec = hm[sl].ravel()
        gvec = horizontal_from_tmi[sl].ravel()
        ratio = np.median(hvec / np.maximum(gvec, 1e-12))
        rows.append({
            "window_row": int(r), "window_col": int(c), "window_size": PATCH,
            "tmi_vg_vs_fft_downward_derivative": {
                "pearson_r": float(pearsonr(zv, dv).statistic),
                "spearman_r": float(spearmanr(zv, dv).statistic),
                "least_squares_scale_tmi_vg_per_fft_downward_derivative": fit_scale,
                "negative_sign_pearson_r": float(pearsonr(zv, -dv).statistic),
            },
            "tmi_hg_vs_finite_difference_horizontal_gradient": {
                "median_ratio_mirror_to_tmi_gradient_magnitude": float(ratio),
                "pearson_r": float(pearsonr(hvec, gvec).statistic),
            },
        })
    band_names = [tag.get("band_name", "") for tag in tags]
    explicit_depth_names = [name for name in band_names if "magnetic" in name.lower() and "depth" in name.lower()]
    return {
        "checked_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "owner-mirror input audit only; no DrivenData download or organizer authentication",
        "runtime_versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "scipy": scipy.__version__,
            "rasterio": rasterio.__version__,
        },
        "implementation": {"audit_script_sha256": sha256_file(Path(__file__).resolve())},
        "inputs": {
            "template_sha256": grid["template_sha256"],
            "training_features_sha256": training_sha,
            "training_features_bytes": TRAINING.stat().st_size,
        },
        "grid": grid,
        "magnetic_bands": {
            "tmi_band_1based": 14, "tmi_description": tmi_desc,
            "tmi_vg_band_1based": 9, "tmi_vg_description": vg_desc,
            "tmi_hg_band_1based": 3, "tmi_hg_description": hg_desc,
            "valid_footprint_cells": int((valid & footprint).sum()),
            "template_footprint_cells_with_any_magnetic_nodata": missing_in_footprint,
            "finite_magnetic_values_outside_template_footprint": valid_outside,
            "outside_nodata": nodata,
            "unit_metadata_present": False,
            "explicit_magnetic_source_depth_band_found_in_embedded_band_names": bool(explicit_depth_names),
            "embedded_band_names": band_names,
        },
        "patch_convention_checks": rows,
        "interpretation": (
            "On the selected fully valid 256x256 owner-mirror patches, the raw tmi_vg sign/scale is compared "
            "with |k| times the Hann-tapered TMI FFT, where positive is downward. Band-unit metadata is absent; "
            "the derivative is expressed relative to the source field's unverified units. This is a convention "
            "check, not a calibration of the original processing or a fault-depth estimate. Publish any "
            "patch-to-patch variation and do not infer physical units from correlation alone."
        ),
        "source_limits": [
            "USGS ScienceBase GeoDAWN release describes magnetic survey line spacing as 200 m in Area 1 and 400 m in Area 2, with variable terrain clearance; the competition mirror is 100 m gridded and may be interpolated between lines.",
            "The USGS catalog record is a source/metadata verification, not an independent byte-for-byte authentication of the owner mirror.",
            "No explicit magnetic-source-depth band was identified among the owner's embedded band_name tags; this does not prove the organizer's original file has identical metadata.",
        ],
    }


def main() -> int:
    result = audit()
    result["sha256"] = None
    result["sha256"] = hashlib.sha256(json.dumps(result, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    out = ROOT / "evidence" / "euler_input_audit.json"
    out.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
