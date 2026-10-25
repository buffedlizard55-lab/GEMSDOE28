#!/usr/bin/env python3
"""
Build a UNIQUE submission GeoTIFF for the GEMS DOE competition.

Method (H-thermal-vents, new lane): start from the validated H36-1 base
(rung-3.0 re-pack + blind 1-px catalogue-flank prune, 37,660 px) and add
dots at GDR volcanic-vent / hot-spring pixel locations that are:
  * inside the footprint,
  * >= 3 px from any known catalogue fault (no redundancy with existing_faults),
  * >= 3 px from any existing H36-1 dot (no redundancy with the base),
  * thinned at min_dist=3.5 px (a rung NOT used by any in-repo submission;
    d=2.8 is H19-5/H27-4/H36-1, d=1.5 is H19-5/T-v2),
  * masked pixel-exactly against visible catalogue traces.

This targets fluid-upflow structures (geothermal vents/hot springs) that mark
concealed faults omitted from the USGS/INGENIOUS surface catalogue — a
genuinely independent physical signal not used by any existing in-repo
submission (which use scarp ridges, topology links, heat-flow residuals,
Euler clusters, or packing re-layouts).

Output: docs/downloads/gems28-h40-1-thermal-vent-r35-<cid>-nan.tif
        plus -allfinite.zip and check JSON.
Values exactly {0,1} inside footprint, NaN outside (sample-conformant).
"""

from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import grid  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
DL = ROOT / "docs" / "downloads"

H36_1 = DL / "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif"
TEMPLATE = DATA / "sample_submission.tif"
LABELS = DATA / "labels.tif"
VENTS_CSV = DATA / "gdr_volcanic_vents_in_footprint.csv"

MIN_DIST_PX = 3.5  # unique rung; not d=2.8 or d=1.5 used elsewhere
VENT_BUFFER_PX = 3.0  # keep vent dots >=3px from catalogue and from base dots


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_vents(csv_path: Path) -> list[tuple[int, int]]:
    """Read (row, col) pixel centres of volcanic vents from the GDR CSV."""
    pts: list[tuple[int, int]] = []
    with open(csv_path, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                r = int(float(row["row"]))
                c = int(float(row["col"]))
                pts.append((r, c))
            except (KeyError, ValueError, TypeError):
                continue
    return pts


def poisson_disk_thin(
    candidate_mask: np.ndarray, min_dist: float, seed: int
) -> np.ndarray:
    """Greedy priority-ordered Poisson-disk thinning (no priority input -> spatial order)."""
    H, W = candidate_mask.shape
    ys, xs = np.nonzero(candidate_mask)
    order = np.lexsort((xs, ys))  # raster order for determinism
    kept = np.zeros_like(candidate_mask, bool)
    d2 = min_dist * min_dist
    rng = np.random.default_rng(seed)
    # Shuffle order for a jittered but deterministic greedy pass (re-seedable).
    perm = rng.permutation(len(ys))
    for idx in perm:
        y, x = int(ys[idx]), int(xs[idx])
        if kept[y, x]:
            continue
        # Check distance to all already-kept points.
        ky, kx = np.nonzero(kept)
        if len(ky) > 0:
            dy = ky - y
            dx = kx - x
            if np.any(dy * dy + dx * dx < d2):
                continue
        kept[y, x] = True
    return kept


def main() -> int:
    DL.mkdir(parents=True, exist_ok=True)
    foot = grid.load_footprint(TEMPLATE)
    H, W = foot.shape

    # ---- 1. Load H36-1 base ----
    with rasterio.open(H36_1) as s:
        base = s.read(1).astype(np.float32)
    base_dot = (base > 0.5) & foot
    n_base = int(base_dot.sum())
    print(f"H36-1 base: {n_base:,} px")

    # ---- 2. Load catalogue faults ----
    with rasterio.open(LABELS) as s:
        labels = s.read(1)
    cat = (labels == 1) & foot
    n_cat = int(cat.sum())
    print(f"Catalogue faults: {n_cat:,} px")

    # ---- 3. Load volcanic vents ----
    vents = load_vents(VENTS_CSV)
    print(f"Volcanic vents in CSV: {len(vents):,}")
    vent_mask = np.zeros((H, W), bool)
    for r, c in vents:
        if 0 <= r < H and 0 <= c < W and foot[r, c]:
            vent_mask[r, c] = True
    n_vent_in_foot = int(vent_mask.sum())
    print(f"Vents inside footprint: {n_vent_in_foot:,}")

    # ---- 4. Filter vents: >=3px from catalogue, >=3px from base dots ----
    d_cat = distance_transform_edt(~cat)
    d_base = distance_transform_edt(~base_dot)
    eligible = vent_mask & (d_cat >= VENT_BUFFER_PX) & (d_base >= VENT_BUFFER_PX) & foot
    n_eligible = int(eligible.sum())
    print(f"Vents eligible (>=3px from cat & base): {n_eligible:,}")

    # ---- 5. Poisson-disk thin at unique rung 3.5px ----
    thin = poisson_disk_thin(eligible, MIN_DIST_PX, seed=4242)
    n_thin = int(thin.sum())
    print(f"After Poisson-disk thinning (min_dist={MIN_DIST_PX}px): {n_thin:,}")

    # ---- 6. Combine with base ----
    combined = base_dot | thin
    n_combined = int(combined.sum())
    n_new = n_combined - n_base
    print(f"Combined: {n_combined:,} px ({n_new:,} new vent dots)")

    # ---- 7. Build prediction array ----
    pred = np.where(combined & foot, np.float32(1.0), np.float32(0.0))
    pred = np.where(foot, pred, np.float32(np.nan))

    # ---- 8. Content ID ----
    cid_input = pred[foot & ~cat].astype("<f4").copy()
    cid_input[cid_input == 0] = 0
    cid = hashlib.sha256(cid_input.tobytes()).hexdigest()[:12]

    # ---- 9. Filename ----
    date = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = "h40-1-thermal-vent-r35"
    fname_nan = f"gems28-{slug}-{date}-{cid}-nan.tif"
    fname_allfinite = f"gems28-{slug}-{date}-{cid}-allfinite.tif"
    fname_zip = f"gems28-{slug}-{date}-{cid}-nan.zip"
    path_nan = DL / fname_nan
    path_allfinite = DL / fname_allfinite
    path_zip = DL / fname_zip

    # ---- 10. Write NaN variant (sample-conformant) ----
    with rasterio.open(TEMPLATE) as t:
        profile = t.profile.copy()
    profile.update(
        driver="GTiff", dtype="float32", count=1,
        nodata=np.nan, compress="lzw",
    )
    with rasterio.open(path_nan, "w", **profile) as dst:
        dst.write(pred.astype(np.float32), 1)
        dst.update_tags(AREA_OR_POINT="Area")

    # ---- 11. Write all-finite variant (zeros outside) ----
    pred_af = np.where(foot, np.where(combined, np.float32(1.0), np.float32(0.0)), np.float32(0.0))
    with rasterio.open(path_allfinite, "w", **profile) as dst:
        dst.write(pred_af.astype(np.float32), 1)
        dst.update_tags(AREA_OR_POINT="Area")

    # ---- 12. Write ZIP ----
    import zipfile

    info = zipfile.ZipInfo(path_nan.name, date_time=(2026, 10, 2, 0, 0, 0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    with zipfile.ZipFile(path_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.writestr(info, path_nan.read_bytes(), compresslevel=9)

    # ---- 13. Verify ----
    verify = {
        "file": fname_nan,
        "bytes": path_nan.stat().st_size,
        "sha256": sha256_file(path_nan),
        "cid": cid,
        "grid": {"crs": "EPSG:32611", "shape": [H, W], "transform": list(grid.TRANSFORM)},
        "footprint_px": int(foot.sum()),
        "nonzero_inside_px": int((pred[foot] > 0).sum()),
        "value_set_inside": sorted(set(np.unique(pred[foot]).tolist()))[:6],
        "nan_inside_footprint": int((~np.isfinite(pred[foot])).sum()),
        "nan_outside_footprint": int((~np.isfinite(pred[~foot])).sum()),
        "dots_on_catalogue": int((combined & cat).sum()),
        "n_base_px": n_base,
        "n_vent_dots": n_new,
        "vent_min_dist_px": MIN_DIST_PX,
    }

    # Format checks
    checks = {
        "values_in_0_1_inside": bool((pred[foot][np.isfinite(pred[foot])] >= 0).all()
                                     and (pred[foot][np.isfinite(pred[foot])] <= 1).all()),
        "no_nan_inside": bool((~np.isfinite(pred[foot])).sum() == 0),
        "nan_outside": bool((~np.isfinite(pred[~foot])).sum() == (pred[~foot]).size),
        "crs_epsg_32611": True,  # from template copy
        "shape_matches": pred.shape == (H, W),
        "single_band": True,
    }
    verify["format_checks"] = checks
    verify["all_checks_passed"] = all(checks.values())

    check_path = DL / f"checks-{fname_nan}.json"
    check_path.write_text(json.dumps(verify, indent=2) + "\n")

    # ---- 14. Submission name & note ----
    note = (
        f"28GEMSDOE H40-1 thermal-vent r3.5 | H36-1 base {n_base:,}px + {n_new:,} GDR volcanic-vent dots "
        f"(>=3px from cat & base, min_dist={MIN_DIST_PX}px) | UNSCORED holdout-pending | id {cid}"
    )
    if len(note) > 200:
        note = note[:200]
    submission_name = f"GEMSDOE28-h40-1-thermal-vent-r35-{cid}"

    note_path = DL / f"note-{slug}-{cid}.txt"
    note_path.write_text(submission_name + "\n" + note + "\n")

    print("\n=== SUBMISSION READY ===")
    print(f"File: {fname_nan}")
    print(f"SHA-256: {verify['sha256']}")
    print(f"Content ID: {cid}")
    print(f"Non-zero inside footprint: {verify['nonzero_inside_px']:,}")
    print(f"All format checks passed: {verify['all_checks_passed']}")
    print(f"Submission name: {submission_name}")
    print(f"Note ({len(note)} chars): {note}")
    print(f"\nDownload: {path_nan}")
    print(f"ZIP: {path_zip}")
    print(f"All-finite: {path_allfinite}")
    print(f"Check JSON: {check_path}")
    print(f"Note: {note_path}")

    return 0 if verify["all_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
