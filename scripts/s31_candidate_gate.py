#!/usr/bin/env python3
"""Independent S31 gate for the written candidate TIF (re-reads the bytes; different
algorithm from the builder: cKDTree nearest-neighbour instead of a distance transform).

Checks, all on the file on disk:
  * format: single band, float32, EPSG:32611, shape 3730x3292, transform, bounds, GTiff
  * footprint: all finite inside; values in [0,1] inside; zeros outside; no inf anywhere;
    inside binary {0,1}
  * dots: count; zero dots on the catalogue
  * uniqueness: for every comparable nine-site registry raster, fraction of candidate dots
    whose NEAREST reference dot is within 3 px, vs the 70% internal gate; plus the overlap
    vs the S30 candidate and vs the H33-2 parent (informational)
  * cross-file: overlap vs docs/candidates/gemsdoe28-s30-catfar65-budgetfill-20261030-zeros.tif

Writes evidence/s31_candidate_gate.json. This gate never contacts the network.

Run:  python scripts/s31_candidate_gate.py
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

CAND = ROOT / "docs/candidates/gemsdoe28-s31-far65-dispfill-20261031-zeros.tif"
RUN_CARD = ROOT / "evidence/s31_candidate_run_card.json"
REGISTRY = ROOT / "data/registry_tifs/manifest.json"
TEMPLATE = ROOT / "data/sample_submission.tif"
S30_CAND = ROOT / "docs/candidates/gemsdoe28-s30-catfar65-budgetfill-20261030-zeros.tif"
PARENT_BLOB = "17a76895f68174cc93f3cb1597d25686f6d6bc67"  # GEMSDOE32 H33-2-B2 zeros variant


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
        add("single_band_float32", s.count == 1 and s.dtypes[0] == "float32",
            f"count={s.count} dtype={s.dtypes[0]}")
        add("crs_epsg_32611", s.crs is not None and s.crs.to_epsg() == grid.CRS_EPSG, str(s.crs))
        add("shape_matches_grid", s.shape == grid.SHAPE, str(s.shape))
        add("transform_matches_grid",
            tuple(round(v, 6) for v in tuple(s.transform)[:6]) == grid.TRANSFORM,
            str(tuple(s.transform)[:6]))
        add("driver_gtiff", s.driver == "GTiff", s.driver)
        nodata = s.nodata
        add("nodata_absent_or_nan", nodata is None or np.isnan(nodata), f"nodata={nodata}")
        bounds_ok = tuple(round(v, 3) for v in s.bounds) == tuple(round(v, 3) for v in grid.BOUNDS)
        add("bounds_match_grid", bounds_ok, str(tuple(s.bounds)))
    inside = a[foot]
    outside = a[~foot]
    add("inside_all_finite", bool(np.isfinite(inside).all()),
        f"non-finite={int((~np.isfinite(inside)).sum())}")
    add("inside_in_0_1", bool(inside.min() >= 0 and inside.max() <= 1),
        f"min={inside.min()} max={inside.max()}")
    add("no_inf_anywhere", not bool(np.isinf(a).any()), "whole array")
    add("outside_all_zero_and_finite", bool(np.isfinite(outside).all() and (outside == 0).all()),
        f"outside size {outside.size}")
    add("inside_binary", bool(np.isin(inside, [0.0, 1.0]).all()),
        "values are exactly 0 or 1 inside")

    dots = dot_coords(a, foot)
    n_dots = len(dots)
    cat = grid.load_labels(ROOT / "data/labels.tif")
    on_cat = int((cat[tuple(dots.astype(int).T)]).sum())
    add("zero_dots_on_catalogue", on_cat == 0, f"{on_cat} dots on catalogue")

    run_card = json.loads(RUN_CARD.read_text())
    sha = hashlib.sha256(CAND.read_bytes()).hexdigest()
    add("sha256_matches_run_card", sha == run_card["sha256"], sha)
    add("note_within_140_chars", len(run_card["note"]) <= 140, f"{len(run_card['note'])} chars")

    registry = json.loads(REGISTRY.read_text())["files"]
    overlaps = {}
    comparisons_skipped = []
    parent_frac = None
    for item in registry:
        with rasterio.open(ROOT / item["local"]) as s2:
            if s2.shape != grid.SHAPE:
                comparisons_skipped.append(
                    {"file": item["local"], "reason": f"off-grid shape {s2.shape}"})
                continue
            ref_vals = s2.read(1).astype(np.float64)
        ref = dot_coords(ref_vals, foot)
        if len(ref) == 0:
            comparisons_skipped.append({"file": item["local"], "reason": "no dots"})
            continue
        # Direction of the lane rule: fraction of CANDIDATE dots within 3 px of this raster.
        frac = float(np.mean(cKDTree(ref).query(dots, k=1)[0] <= U.OVERLAP_RADIUS_PX))
        name = f"{item['site']}/{Path(item['path']).name}"
        overlaps[name] = frac
        if item["blob_sha"] == PARENT_BLOB:
            parent_frac = frac
    worst = max(overlaps, key=overlaps.get)
    n_over = sum(1 for v in overlaps.values() if v > U.DUPLICATE_OVERLAP)
    add("no_registry_raster_over_70pct", n_over == 0,
        f"{n_over} of {len(overlaps)} compared; worst {overlaps[worst]:.4f} ({worst})")

    s30_frac = None
    if S30_CAND.is_file():
        with rasterio.open(S30_CAND) as s30:
            s30_ref = dot_coords(s30.read(1).astype(np.float64), foot)
        s30_frac = float(np.mean(cKDTree(s30_ref).query(dots, k=1)[0] <= U.OVERLAP_RADIUS_PX))
        add("s30_candidate_overlap_under_70pct", s30_frac <= 0.70, f"{s30_frac:.4f}")

    all_pass = all(c["pass"] for c in checks.values())
    out = {
        "schema": 1,
        "session": "S31",
        "file": str(CAND.relative_to(ROOT)),
        "sha256": sha,
        "bytes": CAND.stat().st_size,
        "dots": n_dots,
        "checks": checks,
        "all_hard_checks_pass": all_pass,
        "uniqueness": {
            "gate": "duplicate if >70% of dots within 3 px of one registry raster's dots",
            "registry_scope": ("the nine owner-published sites GEMSDOE{24,25,27,28,30,31,32,33,36}; "
                               "the GEMSDOE13 spacing-five calibration lattice is NOT a submission "
                               "and is excluded by the S30 merged convention (flagged for the owner)"),
            "rasters_compared": len(overlaps),
            "rasters_skipped": comparisons_skipped,
            "max_overlap": overlaps[worst],
            "max_overlap_raster": worst,
            "rasters_over_70pct": n_over,
            "per_raster_overlap": dict(sorted(overlaps.items(), key=lambda kv: -kv[1])[:20]),
            "overlap_vs_h33_2_parent": parent_frac,
            "overlap_vs_s30_candidate": s30_frac,
            "spearman_note": ("binary dot raster: rank correlation vs registry rasters is tied and "
                              "tiny; the 70%/3 px overlap gate is the operative uniqueness test "
                              "(same convention as the S30 sessions)"),
        },
        "verdict_file": ("VALID AND UNIQUE" if all_pass else "FAILED"),
        "provenance": "local recomputation from owner-published registry bytes; no organizer receipt",
    }
    (ROOT / "evidence/s31_candidate_gate.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({"verdict": out["verdict_file"], "all_hard_checks_pass": all_pass,
                      "dots": n_dots, "max_overlap": overlaps[worst],
                      "max_overlap_raster": worst, "rasters_over_70pct": n_over,
                      "overlap_vs_parent": parent_frac, "overlap_vs_s30": s30_frac}, indent=1))
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
