#!/usr/bin/env python3
"""S30 unique candidate: catalogue-distance-ranked retention of the GEMSDOE32 H33-2 dots + budgeted fill.

Rule (fully specified; no tuning against any score):
  1. Parent P = GEMSDOE32 H33-2-B2 dots (USER-REPORTED 0.2778). Verified subset of GEMSDOE31 solo-d28 minus
     2,545 dots within 2 px of the catalogue (see scripts/s30_registry_audit.py and knowledge/77_s30).
  2. Keep the KEEP_FRACTION of P's dots that lie FARTHEST from the catalogue; drop the rest.
  3. Fill the removed count N_fill with NEW dots at cells that are inside the footprint, not catalogue,
     at least MIN_CAT_PX from the catalogue, and at least MIN_SPACING_PX from each other. Cells are ranked
     by a magnetic-ridge prior (gradient magnitude of the smoothed reduced-to-pole band).
  4. UNIQUENESS BUDGET (per registry raster, the gate's own unit): for every one of the registry rasters R_i,
     (dots of this file within 3 px of R_i) / (dots of this file) must stay <= MAX_OVERLAP (0.68, which is
     below the 0.70 duplicate gate). A new cell is accepted only if every raster's running count stays within
     its budget. Each new dot is tested against all registry rasters with an exact KD-tree query.
  5. Write a single-band float32 GeoTIFF with zeros outside the footprint (all finite; values in {0,1}).

The gate is re-checked from the written file's bytes by an exact distance-transform pass over all registry
rasters (scripts/s30_candidate_gate.py); the builder's own numbers are not treated as proof.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt, gaussian_gradient_magnitude, gaussian_filter
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, submission, uniqueness as U  # noqa: E402

PARENT = ROOT / "data/site_submissions/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
TEMPLATE = ROOT / "data/sample_submission.tif"
TRAINING = ROOT / "data/training_features.tif"
REGISTRY = ROOT / "data/registry_tifs/manifest.json"
KEEP_FRACTION = 0.65
MAX_OVERLAP = 0.68
MIN_CAT_PX = 6.0
MIN_SPACING_PX = 4
RIDGE_SIGMA_PX = 1.5
OUT_NAME = "gemsdoe28-s30-catfar65-budgetfill-20261030-zeros.tif"
NOTE = ("S30 H33-2 keep-far-65pct + budgeted RTP-ridge fill; zeros outside; score unverified; "
        "<=68% within 3px of any registry raster")
assert len(NOTE) <= 140, len(NOTE)


def registry_items() -> list[dict]:
    return json.loads(REGISTRY.read_text())["files"]


def dots_of(path: Path, foot: np.ndarray) -> np.ndarray | None:
    """Dot mask of a REGISTRY raster on the competition grid, or None if off-grid (never compared)."""
    with rasterio.open(path) as s:
        if s.shape != foot.shape:
            return None
        v = s.read(1).astype(np.float64)
    return U.registry_dot_mask(v, foot)


def main() -> int:
    foot = grid.load_footprint(TEMPLATE)
    labels = grid.load_labels(ROOT / "data/labels.tif")
    H, W = foot.shape
    with rasterio.open(PARENT) as s:
        parent = U.dot_mask(s.read(1).astype(np.float64), foot)
    n_parent = int(parent.sum())
    n_final = n_parent  # the file keeps the parent's dot count; the removed slots are refilled

    dist_cat = distance_transform_edt(~labels)

    # 1-2: keep the far-from-catalogue fraction of the parent dots.
    idx = np.flatnonzero(parent)
    order = idx[np.argsort(-dist_cat.reshape(-1)[idx], kind="stable")]
    n_keep = int(round(KEEP_FRACTION * n_parent))
    kept_idx = order[:n_keep]
    kept = np.zeros(foot.shape, bool)
    kept.reshape(-1)[kept_idx] = True
    n_fill = n_final - n_keep

    # Registry geometry: unique dot cells + the list of registry rasters each cell belongs to.
    items = registry_items()
    cell_list, raster_list, comparable = [], [], []
    for item in items:
        d = dots_of(ROOT / item["local"], foot)
        if d is None:
            continue
        rid = len(comparable)
        comparable.append(item)
        cell_list.append(np.flatnonzero(d))
        raster_list.append(np.full(cell_list[-1].size, rid, dtype=np.int32))
    all_cells = np.concatenate(cell_list)
    all_rids = np.concatenate(raster_list)
    uniq_cells, inv = np.unique(all_cells, return_inverse=True)
    order_c = np.argsort(inv, kind="stable")
    rids_sorted = all_rids[order_c]
    starts = np.searchsorted(inv[order_c], np.arange(uniq_cells.size + 1))
    ry, rx = np.divmod(uniq_cells, W)
    tree = cKDTree(np.column_stack([ry, rx]).astype(np.float64))
    n_rasters = len(comparable)

    def rasters_within3(cell_flat: int) -> np.ndarray:
        y, x = divmod(int(cell_flat), W)
        hits = tree.query_ball_point([y, x], r=U.OVERLAP_RADIUS_PX)
        if not hits:
            return np.empty(0, dtype=np.int32)
        return np.unique(np.concatenate([rids_sorted[starts[h]:starts[h + 1]] for h in hits]))

    # Per-raster running counts for the kept dots, then the budget that remains for new dots.
    count = np.zeros(n_rasters, dtype=np.int64)
    for c in kept_idx:
        count[rasters_within3(c)] += 1
    budget_cap = int(np.floor(MAX_OVERLAP * n_final))
    kept_within_max = int(count.max())
    kept_within_fraction_max = float(kept_within_max) / n_final

    # Surface check before placement: the ridge prior must not be a copy of the registry density.
    with rasterio.open(TRAINING) as s:
        rtp = s.read(2).astype(np.float64)  # band 2 = rtp (verified by descriptions)
    rtp = np.where(np.isfinite(rtp), rtp, np.nanmedian(rtp[foot]))
    ridge = gaussian_gradient_magnitude(rtp, sigma=RIDGE_SIGMA_PX)
    union_mask = np.zeros(foot.shape, bool)
    union_mask.reshape(-1)[uniq_cells] = True
    density = gaussian_filter(union_mask.astype(np.float64), sigma=10.0)
    surface_rho = U.rank_correlation(ridge, density, foot)

    # 3-4: budgeted greedy fill in ridge-prior order.
    # Never re-place on a kept dot or on a parent dot that was removed: the refill must be new positions.
    cand = foot & ~labels & (dist_cat >= MIN_CAT_PX) & ~kept & ~parent
    cand_idx = np.flatnonzero(cand)
    cand_idx = cand_idx[np.argsort(-ridge.reshape(-1)[cand_idx], kind="stable")]
    blocked = np.zeros(foot.shape, bool)
    new_idx: list[int] = []
    r = MIN_SPACING_PX - 1
    skipped_budget = 0
    for flat in cand_idx:
        if len(new_idx) >= n_fill:
            break
        y, x = divmod(int(flat), W)
        if blocked[y, x]:
            continue
        hits = rasters_within3(flat)
        if hits.size and np.any(count[hits] + 1 > budget_cap):
            skipped_budget += 1
            continue
        count[hits] += 1
        new_idx.append(int(flat))
        blocked[max(0, y - r):y + r + 1, max(0, x - r):x + r + 1] = True
    if len(new_idx) < n_fill:
        raise SystemExit(f"budgeted fill exhausted: placed {len(new_idx)} of {n_fill}")

    new = np.zeros(foot.shape, bool)
    new.reshape(-1)[np.asarray(new_idx, dtype=np.int64)] = True
    final = (kept | new) & foot
    n_out = int(final.sum())
    assert n_out == n_final, (n_out, n_final)

    pred = final.astype(np.float32)
    out_dir = ROOT / "docs" / "candidates"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / OUT_NAME
    submission.write_geotiff(pred, TEMPLATE, out, outside="zero")
    verification = submission.verify_geotiff(out, TEMPLATE)

    # Exact re-check of the final dots against every registry raster (distance transform, not the KD budget).
    overlaps = {}
    for item in comparable:
        ref = dots_of(ROOT / item["local"], foot)
        if not ref.any():
            continue
        overlaps[f"{item['site']}/{Path(item['path']).name}"] = U.fraction_within(final, ref)
    max_name = max(overlaps, key=overlaps.get)
    vs_parent = U.fraction_within(final, parent)

    summary = {
        "schema": 1,
        "session": "S30",
        "file": OUT_NAME,
        "path": str(out.relative_to(ROOT)),
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "bytes": out.stat().st_size,
        "note": NOTE,
        "note_chars": len(NOTE),
        "parent": "GEMSDOE32 gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif (USER-REPORTED 0.2778)",
        "parent_dots": n_parent,
        "keep_fraction": KEEP_FRACTION,
        "kept_dots": n_keep,
        "fill_dots": n_fill,
        "final_dots": n_out,
        "max_kept_fraction_within_3px_of_any_raster": kept_within_fraction_max,
        "budget_cap_dots_per_raster": budget_cap,
        "fill_candidates_skipped_by_budget": skipped_budget,
        "dots_on_catalogue": int((final & labels).sum()),
        "overlap_vs_parent_within_3px": vs_parent,
        "max_overlap_vs_any_registry_raster_within_3px": overlaps[max_name],
        "max_overlap_registry_file": max_name,
        "registry_rasters_compared": len(overlaps),
        "registry_rasters_off_grid_not_compared": len(items) - len(comparable),
        "registry_rasters_over_70pct": sum(1 for v in overlaps.values() if v > U.DUPLICATE_OVERLAP),
        "surface_rank_corr_ridge_vs_registry_density": surface_rho,
        "validator": {k: verification[k] for k in ("hard_checks_passed", "hard_failures", "variant",
                                                    "nonzero_inside_px", "value_set_inside")},
        "rule_status": "UNIQUE under 70%/3px gate (exact re-check; see max overlap)",
        "submission_status": "NOT VALIDATED FOR SCORE: no holdout estimate; expected score unknown",
    }
    (ROOT / "evidence" / "s30_candidate_run_card.json").write_text(json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
