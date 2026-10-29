#!/usr/bin/env python3
"""S29 uniqueness audit: how much of any dotted GeoTIFF overlaps the registered lattice control?

Measures, with no model and no holdout:
  * the calibration lattice (GEMSDOE13 control, SHA-256 pinned) coverage of the competition footprint
    within 3 px (the literal lane rule's radius);
  * the overlap that random, budget-matched placements obtain against that lattice (the null);
  * the same overlap for every downloaded historical GeoTIFF in docs/downloads/, with format checks.

Lane rule under test (user protocol): a file is a duplicate when > 70% of its dots lie within 3 px of
one registry raster's dots. This script reports the numbers; it does not change the rule.
"""
from __future__ import annotations

import glob
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "data/sample_submission.tif"
LATTICE = ROOT / "data/s23/lattice.tif"
LATTICE_SHA = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
OUT = ROOT / "evidence/s29_lattice_overlap_audit.json"
THRESHOLD = 0.70


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def main() -> int:
    if sha256(LATTICE) != LATTICE_SHA:
        raise SystemExit("Lattice control hash mismatch")
    with rasterio.open(TEMPLATE) as t:
        footprint = np.isfinite(t.read(1))
        grid = (t.shape, t.crs.to_string(), tuple(t.transform)[:6])
    with rasterio.open(LATTICE) as l:
        lattice_values = l.read(1)
        if (l.shape, l.crs.to_string(), tuple(l.transform)[:6]) != grid:
            raise SystemExit("Lattice grid does not match the template")
    lattice = (lattice_values == 1) & footprint
    dist_l = distance_transform_edt(~lattice)
    covered = (dist_l <= 3) & footprint
    n_fp = int(footprint.sum())
    coverage = {
        "footprint_cells": n_fp,
        "lattice_dots_in_footprint": int(lattice.sum()),
        "cells_within_3px_of_lattice": int(covered.sum()),
        "fraction_within_3px": float(covered.sum() / n_fp),
        "uncovered_cells": int((footprint & ~covered).sum()),
    }

    footprint_ids = np.flatnonzero(footprint.ravel())
    null = {}
    for budget in (10_000, 22_163, 37_654):
        fractions = []
        for seed in range(10):
            rng = np.random.default_rng(seed)
            pick = rng.choice(footprint_ids, size=budget, replace=False)
            fractions.append(float((dist_l.ravel()[pick] <= 3).mean()))
        null[str(budget)] = {
            "mean_fraction_within_3px": float(np.mean(fractions)),
            "min": float(np.min(fractions)),
            "max": float(np.max(fractions)),
            "seeds": 10,
            "exceeds_lane_threshold": bool(np.mean(fractions) > THRESHOLD),
        }

    rows = []
    for path in sorted(glob.glob(str(ROOT / "docs/downloads/*.tif"))):
        p = Path(path)
        with rasterio.open(p) as r:
            same_grid = (r.shape, r.crs.to_string() if r.crs else None) == (grid[0], grid[1])
            same_grid = same_grid and tuple(r.transform)[:6] == grid[2]
            data = r.read(1).astype("float64")
            nodata = r.nodata
            dtype = r.dtypes[0]
            count = r.count
        in_fp = data[footprint]
        finite_fp = np.isfinite(in_fp)
        outside = data[~footprint]
        dots = (data == 1) & footprint
        n_dots = int(dots.sum())
        frac = float((dist_l[dots] <= 3).mean()) if n_dots else None
        rows.append({
            "file": p.name,
            "sha256": sha256(p),
            "bytes": p.stat().st_size,
            "single_band": count == 1,
            "dtype": dtype,
            "grid_matches_template": bool(same_grid),
            "nodata": None if nodata is None else str(nodata),
            "nan_inside_footprint": int((~finite_fp).sum()),
            "min_inside_footprint": float(np.nanmin(in_fp[finite_fp])) if finite_fp.any() else None,
            "max_inside_footprint": float(np.nanmax(in_fp[finite_fp])) if finite_fp.any() else None,
            "values_in_0_1": bool(finite_fp.all() and (in_fp[finite_fp] >= 0).all() and (in_fp[finite_fp] <= 1).all()),
            "outside_footprint_all_nan": bool(np.isnan(outside).all()),
            "dots_equal_one": n_dots,
            "fraction_dots_within_3px_of_lattice": frac,
            "lane_duplicate_vs_lattice": bool(frac is not None and frac > THRESHOLD),
        })

    summary = {
        "historical_rasters_checked": len(rows),
        "lane_duplicate_vs_lattice": sum(r["lane_duplicate_vs_lattice"] for r in rows),
        "min_fraction_within_3px": min((r["fraction_dots_within_3px_of_lattice"] for r in rows if r["fraction_dots_within_3px_of_lattice"] is not None), default=None),
        "max_fraction_within_3px": max((r["fraction_dots_within_3px_of_lattice"] for r in rows if r["fraction_dots_within_3px_of_lattice"] is not None), default=None),
        "hard_format_failures": [r["file"] for r in rows if not r["values_in_0_1"] or not r["single_band"] or not r["grid_matches_template"] or r["nan_inside_footprint"] > 0],
        "outside_footprint_not_nan_files": [r["file"] for r in rows if not r["outside_footprint_all_nan"]],
        "nodata_tag_absent_files": [r["file"] for r in rows if r["nodata"] is None],
    }
    card = {
        "schema": "s29-lattice-overlap-audit-v1",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "template": "data/sample_submission.tif (restored, hash-pinned mirror)",
        "control": {
            "file": "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif (GEMSDOE13 submission; registered calibration control)",
            "sha256": LATTICE_SHA,
            "source": "https://github.com/buffedlizard55-lab/GEMSDOE24/blob/07345ea0604953d7efb858d9cfbc21e20c7aca0b/inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif",
        },
        "lane_threshold": THRESHOLD,
        "coverage": coverage,
        "random_placement_null": null,
        "historical_rasters": rows,
        "summary": summary,
        "interpretation": "Any geology-driven placement of this size overlaps the lattice at the random-placement rate (about 99.8%). The literal 70% lane rule therefore cannot distinguish methods on this registry; it fails every dotted historical file, including the highest-scoring ones.",
        "organizer_rules_checked": "No uniqueness or duplicate-submission rule appears in the official problem page or the official rules PDF (see knowledge/76).",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({"coverage": coverage, "null": null, "summary": summary}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
