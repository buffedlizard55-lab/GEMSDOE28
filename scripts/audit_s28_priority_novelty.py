#!/usr/bin/env python3
"""Compare nine historical leaders with pinned shared tools; never generate predictions."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid  # noqa: E402
from gems27.shared_template import load_shared  # noqa: E402
from gems27.submission import sha256_file  # noqa: E402

# Historical user reports, NOT organizer receipts or score estimates.
LEADERS = {
    "GEMSDOE24": ("989f59505db1", 0.2477),
    "GEMSDOE25": ("e56ea318af89", 0.2600),
    "GEMSDOE27": ("5512495c6bd1", 0.2449),
    "GEMSDOE28": ("b531dae0a36f", 0.2710),
    "GEMSDOE30": ("91eae1ca", 0.2600),
    "GEMSDOE31": ("h27-4-solo", 0.2708),
    "GEMSDOE32": ("e5eb6e7e", 0.2778),
    "GEMSDOE33": ("cb490425926e", 0.2632),
    "GEMSDOE36": ("9b9ea4e6", 0.2750),
}


def select_leaders(inventory):
    """Choose one archived NaN variant per named leader, not an optimized candidate."""
    selected = []
    for name, (token, score) in LEADERS.items():
        repo = next(r for r in inventory["repositories"] if r["repository"].endswith("/" + name))
        choices = [r for r in repo["priority_rasters"]
                   if token in r["path"] and r["path"].endswith(("-nan.tif", "-nanoutside.tif"))]
        if len(choices) != 1:
            raise ValueError(f"Expected exactly one historical NaN variant: {name}: {len(choices)}")
        selected.append({"site": name, "reported_score": score, "score_label": "USER-REPORTED / UNVERIFIED",
                         "raster": choices[0], "commit": repo["commit"]})
    return selected


def main():
    import rasterio

    source = ROOT / "evidence/s28_priority_repository_audit.json"
    inventory = json.loads(source.read_text())
    if not inventory["priority_inventory_retrieved"]:
        raise ValueError("Incomplete priority inventory")
    leaders = select_leaders(inventory)
    template = ROOT / "data/sample_submission.tif"
    footprint = grid.load_footprint(template)
    shared = load_shared()
    for leader in leaders:
        raster = leader["raster"]
        path = ROOT / raster["local_path"]
        if sha256_file(path) != raster["sha256"]:
            raise ValueError("Changed source raster")
        with rasterio.open(path) as ds:
            values = ds.read(1)
        refs = [{"id": other["site"], "file": other["raster"]["file"], "cache_path": other["raster"]["local_path"],
                 "footprint_sha256": other["raster"]["footprint_values_sha256"]}
                for other in leaders if other["site"] != leader["site"]]
        leader["final_dots"] = shared.novelty.compare_registry(
            values, footprint, refs, ROOT, dots=footprint & (values > 0), template_path=template)
        leader["surface_before_placement"] = "UNAVAILABLE; final raster correlation is not a surface check"
        leader["estimated_leaderboard_score"] = None
        leader["ok_to_submit"] = False
        print(leader["site"], leader["final_dots"]["passed"], flush=True)
    import numpy as np
    from scipy.ndimage import distance_transform_edt

    def dots(site, token):
        repo = next(r for r in inventory["repositories"] if r["repository"].endswith("/" + site))
        raster = next(r for r in repo["priority_rasters"] if token in r["path"])
        with rasterio.open(ROOT / raster["local_path"]) as ds:
            return footprint & (ds.read(1) > 0)

    solo = dots("GEMSDOE28", "8acb75e1f2cc")
    champion = dots("GEMSDOE32", "e5eb6e7e")
    d28 = dots("GEMSDOE25", "e56ea318af89")
    catalogue = grid.load_labels(ROOT / "data/labels.tif")
    forensic = {
        "label": "PIXEL-SET FORENSICS; not a performance estimate",
        "champion_equals_solo_minus_catalogue_distance_le_2px": bool(
            np.array_equal(champion, solo & (distance_transform_edt(~catalogue) > 2))),
        "champion_pixels": int(champion.sum()),
        "removed_solo_to_champion": int((solo & ~champion).sum()),
        "added_solo_to_champion": int((champion & ~solo).sum()),
        "gems25_equals_gems30_inside_footprint": bool(np.array_equal(d28, dots("GEMSDOE30", "91eae1ca"))),
        "solo_equals_gems31_inside_footprint": bool(np.array_equal(solo, dots("GEMSDOE31", "h27-4-solo"))),
        "causal_score_improvement_proven": False,
    }
    report = {"scope": "Nine user-named historical leaders only; not a complete parallel registry",
              "forensic": forensic,
              "source_inventory_sha256": sha256_file(source), "leaders": leaders,
              "new_raster_generated": False, "experiments_run": 0, "slot_selected": False}
    (ROOT / "evidence/s28_priority_novelty.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
