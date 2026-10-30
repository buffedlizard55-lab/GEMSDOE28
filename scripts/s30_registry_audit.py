#!/usr/bin/env python3
"""S30 registry audit: format, encoding, catalogue overlap and 3-px duplicate map for every site raster.

Inputs (all local, hash-pinned):
  data/registry_tifs/manifest.json   475 owner-published GeoTIFFs from the nine GEMSDOE repositories
  data/sample_submission.tif         competition footprint and grid template (restored, hash-pinned)
  data/labels.tif                    catalogue raster (restored, hash-pinned)

Outputs:
  evidence/s30_registry_audit.json   per-file checks + focus-file duplicate map (no raw rasters)

Only 3-px dot overlap and footprint/format facts are computed here; no holdout scoring is performed.
"""
from __future__ import annotations

import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, uniqueness as U  # noqa: E402

FOCUS = {  # user-named best submission per site (USER-REPORTED scores; see README S30 table)
    "GEMSDOE24": "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif",
    "GEMSDOE25": "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
    "GEMSDOE27": "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif",
    "GEMSDOE28": "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
    "GEMSDOE30": "gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
    "GEMSDOE31": "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-nan.tif",
    "GEMSDOE32": "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "GEMSDOE33": "GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
    "GEMSDOE36": "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
}
USER_REPORTED = {"GEMSDOE24": 0.2477, "GEMSDOE25": 0.2600, "GEMSDOE27": 0.2449, "GEMSDOE28": 0.2710,
                 "GEMSDOE30": 0.2600, "GEMSDOE31": 0.2708, "GEMSDOE32": 0.2778, "GEMSDOE33": 0.2632,
                 "GEMSDOE36": 0.2750}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    foot = grid.load_footprint(ROOT / "data" / "sample_submission.tif")
    labels = grid.load_labels(ROOT / "data" / "labels.tif")
    manifest = json.loads((ROOT / "data" / "registry_tifs" / "manifest.json").read_text())
    files = manifest["files"]

    rows = []
    dots_by_path: dict[str, np.ndarray] = {}
    for item in files:
        path = ROOT / item["local"]
        with rasterio.open(path) as src:
            nodata = src.nodata
            crs = src.crs.to_epsg() if src.crs else None
            ok_grid = (src.shape == grid.SHAPE and tuple(src.transform)[:6] == tuple(grid.TRANSFORM)[:6]
                       and crs == grid.CRS_EPSG and src.count == 1)
            values = src.read(1).astype(np.float64)
        if values.shape != foot.shape:
            # Off-grid raster: recorded, never compared dot-for-dot (not a competition-grid submission).
            rows.append({"site": item["site"], "file": Path(item["path"]).name, "local": item["local"],
                         "sha256": item["sha256"], "bytes": item["bytes"], "grid_ok": False,
                         "nodata": None if nodata is None else str(nodata), "encoding": "off_grid",
                         "inside_finite": None, "inside_in_0_1": None, "inside_binary_0_1": None,
                         "dots": None, "dots_on_catalogue": None, "shape": list(values.shape)})
            print("OFF-GRID", item["local"], values.shape, file=sys.stderr)
            continue
        inside = values[foot]
        outside = values[~foot]
        finite_inside = bool(np.isfinite(inside).all())
        in_range = bool(finite_inside and inside.min() >= 0.0 and inside.max() <= 1.0)
        binary = bool(finite_inside and np.isin(inside, [0.0, 1.0]).all())
        encoding = ("nan_outside" if np.isnan(outside).all() else
                    "zeros_outside" if (np.isfinite(outside).all() and (outside == 0).all()) else
                    "mixed_or_other")
        dots = (np.where(np.isfinite(values), values, 0.0) > 0.5) & foot
        dots_by_path[item["local"]] = np.flatnonzero(dots)
        cat_overlap = int((dots & labels).sum())
        rows.append({
            "site": item["site"], "file": Path(item["path"]).name, "local": item["local"],
            "sha256": item["sha256"], "bytes": item["bytes"], "grid_ok": bool(ok_grid),
            "nodata": None if nodata is None else ("nan" if np.isnan(nodata) else str(nodata)),
            "encoding": encoding, "inside_finite": finite_inside, "inside_in_0_1": in_range,
            "inside_binary_0_1": binary, "dots": int(dots.sum()),
            "dots_on_catalogue": cat_overlap,
        })
        print(item["local"], int(dots.sum()), encoding, file=sys.stderr)

    # Focus files: duplicate map against every registry raster (excluding the same bytes).
    focus_paths = {}
    for site, name in FOCUS.items():
        matches = [r for r in rows if r["file"] == name and r["site"] == site]
        if len(matches) != 1:
            raise SystemExit(f"focus file not uniquely found: {site} {name} -> {len(matches)}")
        focus_paths[site] = matches[0]["local"]

    focus_dots = {s: dots_by_path[p] for s, p in focus_paths.items()}

    def to_mask(idx: np.ndarray) -> np.ndarray:
        m = np.zeros(foot.shape, bool)
        m.reshape(-1)[idx] = True
        return m & foot

    focus_masks = {s: to_mask(v) for s, v in focus_dots.items()}
    dup_counts: dict[str, dict] = {s: {"max_overlap": 0.0, "max_overlap_file": None, "n_duplicate_rasters": 0,
                                       "n_compared": 0} for s in FOCUS}
    for item in files:  # one EDT per reference raster, reused for all focus files
        if item["local"] not in dots_by_path:
            continue
        ref_mask = to_mask(dots_by_path[item["local"]])
        if not ref_mask.any():
            continue
        dist = U.distance_to_dots(ref_mask)
        for site, fm in focus_masks.items():
            if focus_paths[site] == item["local"]:
                continue
            frac = float(np.mean(dist[fm] <= U.OVERLAP_RADIUS_PX))
            entry = dup_counts[site]
            entry["n_compared"] += 1
            if frac > entry["max_overlap"]:
                entry["max_overlap"] = frac
                entry["max_overlap_file"] = f"{item['site']}/{Path(item['path']).name}"
            if frac > U.DUPLICATE_OVERLAP:
                entry["n_duplicate_rasters"] += 1

    summary = {
        "schema": 1,
        "session": "S30",
        "purpose": "format + catalogue + 3-px duplicate audit of the nine named sites' best files",
        "grid": {"shape": list(grid.SHAPE), "crs": f"EPSG:{grid.CRS_EPSG}", "transform": list(grid.TRANSFORM),
                 "footprint_px": int(foot.sum())},
        "rule": "duplicate if >70% of a file's dots lie within 3 px of one other raster's dots",
        "n_registry_rasters": len(files),
        "encoding_counts": dict(Counter(r["encoding"] for r in rows)),
        "all_inside_binary_on_grid": all(r["inside_binary_0_1"] for r in rows if r["grid_ok"]),
        "n_off_grid": sum(1 for r in rows if not r["grid_ok"]),
        "all_on_grid_ok": all(r["grid_ok"] for r in rows if r["encoding"] != "off_grid"),
        "rasters_with_catalogue_dots": sum(1 for r in rows if (r["dots_on_catalogue"] or 0) > 0),
        "focus": {
            site: {
                "file": FOCUS[site], "local": focus_paths[site], "user_reported_score": USER_REPORTED[site],
                "sha256": next(r["sha256"] for r in rows if r["local"] == focus_paths[site]),
                "dots": int(focus_dots[site].size),
                "duplicate_map_vs_all_registry": dup_counts[site],
            } for site in FOCUS
        },
        "rows": rows,
        "provenance": "owner-published files via GitHub API; not organizer receipts; scores USER-REPORTED",
    }
    out = ROOT / "evidence" / "s30_registry_audit.json"
    out.write_text(json.dumps(summary, indent=1) + "\n")
    print(f"wrote {out}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
