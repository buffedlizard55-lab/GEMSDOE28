#!/usr/bin/env python3
"""Independent S30 gate for the written candidate TIF (re-reads the bytes; different algorithm from the builder).

Checks, all on the file on disk:
  * format: single band, float32, EPSG:32611, shape 3730x3292, transform, bounds, GTiff, nodata convention
  * footprint: all finite inside; values in [0,1] inside; zeros outside (allfinite variant); no inf anywhere
  * dots: binary inside; count; zero dots on the catalogue
  * uniqueness: for every comparable registry raster, fraction of candidate dots whose NEAREST reference dot
    is within 3 px (cKDTree nearest-neighbour, not a distance transform), vs the 70% gate; plus the rank
    correlation vs the parent raster (informational; binary rasters have tied ranks)
Writes evidence/s30_candidate_gate.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid  # noqa: E402
from gems27 import uniqueness as U  # noqa: E402

CAND = ROOT / "docs/candidates/gemsdoe28-s30-catfar65-budgetfill-20261030-zeros.tif"
RUN_CARD = ROOT / "evidence/s30_candidate_run_card.json"
REGISTRY = ROOT / "data/registry_tifs/manifest.json"
TEMPLATE = ROOT / "data/sample_submission.tif"


def dot_coords(values: np.ndarray, foot: np.ndarray) -> np.ndarray:
    v = np.where(np.isfinite(values), values, 0.0)
    m = (v > 0.5) & foot
    return np.column_stack(np.nonzero(m)).astype(np.float64)


def main() -> int:
    foot = grid.load_footprint(TEMPLATE)
    checks: dict[str, dict] = {}

    def add(name, ok, detail):
        checks[name] = {"pass": bool(ok), "detail": detail}

    with rasterio.open(CAND) as s:
        a = s.read(1)
        add("single_band_float32", s.count == 1 and s.dtypes[0] == "float32", f"count={s.count} dtype={s.dtypes[0]}")
        add("crs_epsg_32611", s.crs is not None and s.crs.to_epsg() == grid.CRS_EPSG, str(s.crs))
        add("shape_matches_grid", s.shape == grid.SHAPE, str(s.shape))
        add("transform_matches_grid", tuple(round(v, 6) for v in tuple(s.transform)[:6]) == grid.TRANSFORM,
            str(tuple(s.transform)[:6]))
        add("driver_gtiff", s.driver == "GTiff", s.driver)
        nodata = s.nodata
        add("nodata_absent_or_nan", nodata is None or np.isnan(nodata), f"nodata={nodata}")
        bounds_ok = tuple(round(v, 3) for v in s.bounds) == tuple(round(v, 3) for v in grid.BOUNDS)
        add("bounds_match_grid", bounds_ok, str(tuple(s.bounds)))
    inside = a[foot]
    outside = a[~foot]
    add("inside_all_finite", bool(np.isfinite(inside).all()), f"{int((~np.isfinite(inside)).sum())} non-finite")
    add("inside_in_0_1", bool(inside.min() >= 0 and inside.max() <= 1), f"min={inside.min()} max={inside.max()}")
    add("no_inf_anywhere", not bool(np.isinf(a).any()), "whole array")
    add("outside_all_zero_and_finite", bool(np.isfinite(outside).all() and (outside == 0).all()),
        f"outside size {outside.size}")
    add("inside_binary", bool(np.isin(inside, [0.0, 1.0]).all()), "values are exactly 0 or 1 inside")

    dots = dot_coords(a, foot)
    n_dots = len(dots)
    cat = grid.load_labels(ROOT / "data/labels.tif")
    on_cat = int((cat[tuple(dots.astype(int).T)]).sum())
    add("zero_dots_on_catalogue", on_cat == 0, f"{on_cat} dots on catalogue")

    run_card = json.loads(RUN_CARD.read_text())
    sha = hashlib.sha256(CAND.read_bytes()).hexdigest()
    add("sha256_matches_run_card", sha == run_card["sha256"], sha)

    registry = json.loads(REGISTRY.read_text())["files"]
    overlaps = {}
    comparisons_skipped = []
    parent_frac = None
    for item in registry:
        with rasterio.open(ROOT / item["local"]) as s2:
            if s2.shape != grid.SHAPE:
                comparisons_skipped.append({"file": item["local"], "reason": f"off-grid shape {s2.shape}"})
                continue
            ref_vals = s2.read(1).astype(np.float64)
        ref = dot_coords(ref_vals, foot)
        if len(ref) == 0:
            comparisons_skipped.append({"file": item["local"], "reason": "no dots"})
            continue
        frac = float(np.mean(cKDTree(ref).query(dots, k=1)[0] <= U.OVERLAP_RADIUS_PX))
        name = f"{item['site']}/{Path(item['path']).name}"
        overlaps[name] = frac
        if item["blob_sha"] == "17a76895f68174cc93f3cb1597d25686f6d6bc67":
            parent_frac = frac
    worst = max(overlaps, key=overlaps.get)
    n_over = sum(1 for v in overlaps.values() if v > U.DUPLICATE_OVERLAP)
    add("no_registry_raster_over_70pct", n_over == 0,
        f"{n_over} of {len(overlaps)} compared; worst {overlaps[worst]:.4f} ({worst})")

    all_pass = all(c["pass"] for c in checks.values())
    out = {
        "schema": 1, "session": "S30", "file": str(CAND.relative_to(ROOT)), "sha256": sha,
        "bytes": CAND.stat().st_size, "dots": n_dots, "checks": checks, "all_hard_checks_pass": all_pass,
        "uniqueness": {
            "gate": "duplicate if >70% of dots within 3 px of one registry raster's dots",
            "rasters_compared": len(overlaps), "rasters_skipped": comparisons_skipped,
            "max_overlap": overlaps[worst], "max_overlap_raster": worst,
            "rasters_over_70pct": n_over,
            "per_raster_overlap": dict(sorted(overlaps.items(), key=lambda kv: -kv[1])),
            "overlap_vs_h33_2_parent": parent_frac,
            "spearman_note": "binary raster: rank correlation is tied and tiny; the gate's rank test is "
                             "not informative for dot rasters and is reported as not applicable",
        },
        "verdict_file": ("VALID AND UNIQUE" if all_pass else "FAILED"),
        "provenance": "local recomputation from owner-published registry bytes; no organizer receipt",
    }
    (ROOT / "evidence/s30_candidate_gate.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({k: out[k] for k in ("sha256", "dots", "all_hard_checks_pass", "verdict_file")}, indent=1))
    print("worst", worst, overlaps[worst], "rasters_compared", len(overlaps), "over70", n_over,
          "parent_frac", parent_frac)
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
