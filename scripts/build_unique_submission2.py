#!/usr/bin/env python3
"""
Build UNIQUE submission H41-1: thermal-spring corridor dots + H36-1 base.

Method: start from validated H36-1 base (rung-3.0 re-pack + blind flank prune,
37,660 px) and add dots at GDR hot-spring (>40 C) pixel locations that are
>= 3 px from known catalogue faults and >= 3 px from existing H36-1 dots,
thinned at min_dist=3.0 px (a rung distinct from d=2.8 used by H19-5/H27-4/H36-1
and d=1.5 used by H19-5/T-v2).

Thermal springs mark geothermal fluid upflow along concealed faults omitted
from the USGS/INGENIOUS surface catalogue — an independent physical signal
not used by any in-repo submission.

Output: docs/downloads/gems28-h41-1-thermal-spring-r30-<cid>-nan.tif
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
SPRING_CSV = DATA / "gdr_wellspring_in_footprint.csv"

MIN_DIST_PX = 3.0
BUFFER_PX = 3.0
TEMP_THRESHOLD_C = 40.0  # hot springs only


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_hot_springs(csv_path: Path, temp_threshold: float) -> list[tuple[int, int]]:
    """Read unique (row, col) of hot springs (> temp_threshold C)."""
    pts: set[tuple[int, int]] = set()
    with open(csv_path, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            try:
                r = int(float(row["row"]))
                c = int(float(row["col"]))
                t = row.get("temp_c", "")
                temp = float(t) if t and t not in ("NULL", "") else None
                if temp is not None and temp > temp_threshold:
                    pts.add((r, c))
            except (KeyError, ValueError, TypeError):
                continue
    return sorted(pts)


def poisson_disk_thin(candidate_mask: np.ndarray, min_dist: float, seed: int) -> np.ndarray:
    H, W = candidate_mask.shape
    ys, xs = np.nonzero(candidate_mask)
    if len(ys) == 0:
        return np.zeros_like(candidate_mask, bool)
    order = np.lexsort((xs, ys))
    kept = np.zeros_like(candidate_mask, bool)
    d2 = min_dist * min_dist
    rng = np.random.default_rng(seed)
    perm = rng.permutation(len(ys))
    for idx in perm:
        y, x = int(ys[order[idx]]), int(xs[order[idx]])
        if kept[y, x]:
            continue
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

    # ---- 1. H36-1 base ----
    with rasterio.open(H36_1) as s:
        base = s.read(1).astype(np.float32)
    base_dot = (base > 0.5) & foot
    n_base = int(base_dot.sum())
    print(f"H36-1 base: {n_base:,} px")

    # ---- 2. Catalogue faults ----
    with rasterio.open(LABELS) as s:
        labels = s.read(1)
    cat = (labels == 1) & foot

    # ---- 3. Hot springs ----
    springs = load_hot_springs(SPRING_CSV, TEMP_THRESHOLD_C)
    print(f"Hot springs (>40C): {len(springs):,}")
    spring_mask = np.zeros((H, W), bool)
    for r, c in springs:
        if 0 <= r < H and 0 <= c < W and foot[r, c]:
            spring_mask[r, c] = True
    n_spring_in_foot = int(spring_mask.sum())
    print(f"Hot springs inside footprint: {n_spring_in_foot:,}")

    # ---- 4. Filter: >=3px from catalogue and base dots ----
    d_cat = distance_transform_edt(~cat)
    d_base = distance_transform_edt(~base_dot)
    eligible = spring_mask & (d_cat >= BUFFER_PX) & (d_base >= BUFFER_PX) & foot
    n_eligible = int(eligible.sum())
    print(f"Eligible (>=3px from cat & base): {n_eligible:,}")

    # ---- 5. Thin at unique rung 3.0px ----
    thin = poisson_disk_thin(eligible, MIN_DIST_PX, seed=4242)
    n_thin = int(thin.sum())
    print(f"After Poisson-disk thinning (min_dist={MIN_DIST_PX}px): {n_thin:,}")

    # ---- 6. Combine ----
    combined = base_dot | thin
    n_combined = int(combined.sum())
    n_new = n_combined - n_base
    print(f"Combined: {n_combined:,} px ({n_new:,} new spring dots)")

    # ---- 7. Build prediction ----
    pred = np.where(combined & foot, np.float32(1.0), np.float32(0.0))
    pred = np.where(foot, pred, np.float32(np.nan))

    # ---- 8. Content ID ----
    cid_input = pred[foot & ~cat].astype("<f4").copy()
    cid_input[cid_input == 0] = 0
    cid = hashlib.sha256(cid_input.tobytes()).hexdigest()[:12]

    # ---- 9. Filenames ----
    date = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    slug = "h41-1-thermal-spring-r30"
    fname_nan = f"gems28-{slug}-{date}-{cid}-nan.tif"
    fname_allfinite = f"gems28-{slug}-{date}-{cid}-allfinite.tif"
    fname_zip = f"gems28-{slug}-{date}-{cid}-nan.zip"
    path_nan = DL / fname_nan
    path_allfinite = DL / fname_allfinite
    path_zip = DL / fname_zip

    # ---- 10. Write NaN variant ----
    with rasterio.open(TEMPLATE) as t:
        profile = t.profile.copy()
    profile.update(driver="GTiff", dtype="float32", count=1, nodata=np.nan, compress="lzw")
    with rasterio.open(path_nan, "w", **profile) as dst:
        dst.write(pred.astype(np.float32), 1)
        dst.update_tags(AREA_OR_POINT="Area")

    # ---- 11. Write all-finite variant ----
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
        "n_spring_dots": n_new,
        "spring_min_dist_px": MIN_DIST_PX,
        "temp_threshold_c": TEMP_THRESHOLD_C,
    }
    checks = {
        "values_in_0_1_inside": bool((pred[foot][np.isfinite(pred[foot])] >= 0).all()
                                     and (pred[foot][np.isfinite(pred[foot])] <= 1).all()),
        "no_nan_inside": bool((~np.isfinite(pred[foot])).sum() == 0),
        "nan_outside": bool((~np.isfinite(pred[~foot])).sum() == (pred[~foot]).size),
        "shape_matches": pred.shape == (H, W),
        "single_band": True,
    }
    verify["format_checks"] = checks
    verify["all_checks_passed"] = all(checks.values())

    check_path = DL / f"checks-{fname_nan}.json"
    check_path.write_text(json.dumps(verify, indent=2) + "\n")

    # ---- 14. Submission name & note ----
    note = (
        f"28GEMSDOE H41-1 thermal-spring r3.0 | H36-1 base {n_base:,}px + {n_new:,} GDR hot-spring dots "
        f"(>40C, >=3px from cat & base, min_dist={MIN_DIST_PX}px) | UNSCORED holdout-pending | id {cid}"
    )
    if len(note) > 200:
        note = note[:200]
    submission_name = f"GEMSDOE28-h41-1-thermal-spring-r30-{cid}"

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
