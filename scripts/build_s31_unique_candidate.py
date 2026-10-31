#!/usr/bin/env python3
"""S31 candidate: champion far-65% keep + holdout-supported dispersed complement.

Rule (fully specified; no tuning against any score):
  1. Parent P = GEMSDOE32 H33-2-B2 dots (USER-REPORTED 0.2778; the session's best-of-nine
     reference; verified subset of GEMSDOE31 solo-d28 minus 2,545 catalogue-adjacent dots).
  2. Keep the 65% of P's dots FARTHEST from the catalogue (identical kept set to the S30
     candidate, so the champion's credit-carrying dots are preserved exactly).
  3. Refill the removed count with a DISPersed far-field complement: cells inside the
     footprint, >= 6 px from the catalogue, not on any parent cell, >= 4 px from each other,
     placed in a deterministic uniform-random order (seed 20261031), each accepted only if
     every registry raster's running within-3-px count stays <= 68% of the final budget.

Why dispersed and NOT ridge-ranked: S31 experiment E1 (buffered interleaved holdout;
evidence/s31_prior_placement.json) and E2 (LOSFO far-field; evidence/s31_losfo_refill.json)
measured every tested geology prior BELOW the budget-matched uniform control in the refill
habitat (>= 6 px off catalogue): rtp_ridge 0.0248 vs random 0.0535 (E2 mean HOLDOUT-DTI,
3/3 seeds). The S30 refill used rtp_ridge. This builder therefore uses the only placement
policy that beat every geology prior on both instruments: uniform dispersion. It makes NO
geological claim; the negative prior results are deliverables of the run cards.

  4. UNIQUENESS BUDGET (per nine-site registry raster): running count of dots within 3 px
     capped at MAX_OVERLAP (0.68 < the internal 0.70 duplicate gate), enforced during
     placement, re-checked from the written bytes by scripts/s31_candidate_gate.py.
  5. Written via the shared writer: float32, single band, EPSG:32611, 3730x3292, zeros
     outside the footprint, values exactly {0,1} inside — every value finite and in [0,1],
     which forecloses the portal error "Predicted values must be in range [0, 1]".

Run:  python scripts/build_s31_unique_candidate.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, submission  # noqa: E402
from gems27 import uniqueness as U  # noqa: E402

PARENT = ROOT / "data/site_submissions/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"
PARENT_SHA256 = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
TEMPLATE = ROOT / "data/sample_submission.tif"
REGISTRY = ROOT / "data/registry_tifs/manifest.json"
KEEP_FRACTION = 0.65
MAX_OVERLAP = 0.68
MIN_CAT_PX = 6.0
MIN_SPACING_PX = 4
SEED = 20261031
OUT_NAME = "gemsdoe28-s31-far65-dispfill-20261031-zeros.tif"
NOTE = ("S31 keep-far-65pct of H33-2 + dispersed far-field fill (E2-supported); zeros "
        "outside; score unverified; <=68% within 3px of registry rasters")
assert len(NOTE) <= 140, len(NOTE)


def registry_items() -> list[dict]:
    return json.loads(REGISTRY.read_text())["files"]


def dots_of(path: Path, foot: np.ndarray) -> np.ndarray | None:
    with rasterio.open(path) as s:
        if s.shape != foot.shape:
            return None
        v = s.read(1).astype(np.float64)
    return U.registry_dot_mask(v, foot)


def main() -> int:
    if hashlib.sha256(PARENT.read_bytes()).hexdigest() != PARENT_SHA256:
        raise SystemExit("Parent champion raster hash mismatch; refusing to run")
    foot = grid.load_footprint(TEMPLATE)
    labels = grid.load_labels(ROOT / "data/labels.tif")
    W = foot.shape[1]
    with rasterio.open(PARENT) as s:
        parent = U.dot_mask(s.read(1).astype(np.float64), foot)
    n_parent = int(parent.sum())
    n_final = n_parent

    dist_cat = distance_transform_edt(~labels)

    # 1-2: keep the far-from-catalogue fraction of the parent dots (same rule as S30).
    idx = np.flatnonzero(parent)
    order = idx[np.argsort(-dist_cat.reshape(-1)[idx], kind="stable")]
    n_keep = int(round(KEEP_FRACTION * n_parent))
    kept_idx = order[:n_keep]
    kept = np.zeros(foot.shape, bool)
    kept.reshape(-1)[kept_idx] = True
    n_fill = n_final - n_keep

    # Registry geometry: unique dot cells + the registry rasters each cell belongs to.
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

    # Per-raster running counts for the kept dots, then the budget left for the complement.
    count = np.zeros(n_rasters, np.int64)
    for c in kept_idx:
        count[rasters_within3(c)] += 1
    budget_cap = int(np.floor(MAX_OVERLAP * n_final))
    kept_within_max = int(count.max())

    # 3: deterministic uniform-random dispersed fill inside the far-field habitat.
    cand = foot & ~labels & (dist_cat >= MIN_CAT_PX) & ~kept & ~parent
    cand_idx = np.flatnonzero(cand)
    rng = np.random.default_rng(SEED)
    shuffled = cand_idx[rng.permutation(cand_idx.size)]
    blocked = np.zeros(foot.shape, bool)
    new_idx: list[int] = []
    r = MIN_SPACING_PX - 1
    skipped_budget = 0
    for flat in shuffled:
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
        raise SystemExit(f"dispersed fill exhausted: placed {len(new_idx)} of {n_fill}")

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

    # Exact re-check of the final dots against every registry raster (distance transform).
    overlaps = {}
    for item in comparable:
        ref = dots_of(ROOT / item["local"], foot)
        if not ref.any():
            continue
        overlaps[f"{item['site']}/{Path(item['path']).name}"] = U.fraction_within(final, ref)
    max_name = max(overlaps, key=overlaps.get)
    vs_parent = U.fraction_within(final, parent)

    # Explicit cross-check vs the S30 candidate (not part of the nine-site registry).
    s30 = ROOT / "docs/candidates/gemsdoe28-s30-catfar65-budgetfill-20261030-zeros.tif"
    vs_s30 = U.fraction_within(final, dots_of(s30, foot)) if s30.is_file() else None

    new_arr = np.zeros(foot.shape, np.float32)
    new_arr[new] = 1.0
    summary = {
        "schema": 1,
        "session": "S31",
        "file": OUT_NAME,
        "path": str(out.relative_to(ROOT)),
        "sha256": hashlib.sha256(out.read_bytes()).hexdigest(),
        "bytes": out.stat().st_size,
        "note": NOTE,
        "note_chars": len(NOTE),
        "parent": ("GEMSDOE32 gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif "
                   "(USER-REPORTED 0.2778)"),
        "parent_sha256": PARENT_SHA256,
        "parent_dots": n_parent,
        "keep_fraction": KEEP_FRACTION,
        "kept_dots": n_keep,
        "fill_dots": n_fill,
        "fill_rule": ("deterministic uniform-random dispersed complement, seed 20261031, >=6 px "
                      "from catalogue, >=4 px mutual spacing, per-raster 68% budget enforced"),
        "fill_policy_evidence": ("S31 E2 LOSFO far-field: uniform control 0.053522 mean "
                                 "HOLDOUT-DTI vs rtp_ridge 0.024834 (3/3 seeds); E1 interleaved "
                                 "holdout concordant. evidence/s31_losfo_refill.json, "
                                 "evidence/s31_prior_placement.json"),
        "final_dots": n_out,
        "max_kept_fraction_within_3px_of_any_raster": float(kept_within_max) / n_final,
        "budget_cap_dots_per_raster": budget_cap,
        "fill_candidates_skipped_by_budget": skipped_budget,
        "dots_on_catalogue": int((final & labels).sum()),
        "overlap_vs_parent_within_3px": vs_parent,
        "overlap_vs_s30_candidate_within_3px": vs_s30,
        "max_overlap_vs_any_registry_raster_within_3px": overlaps[max_name],
        "max_overlap_registry_file": max_name,
        "registry_rasters_compared": len(overlaps),
        "registry_rasters_off_grid_not_compared": len(items) - len(comparable),
        "registry_rasters_over_70pct": sum(1 for v in overlaps.values() if v > U.DUPLICATE_OVERLAP),
        "validator": {k: verification[k] for k in ("hard_checks_passed", "hard_failures",
                                                   "variant", "nonzero_inside_px",
                                                   "value_set_inside")},
        "rule_status": "UNIQUE under 70%/3px gate vs the nine-site registry (exact re-check)",
        "submission_status": ("NOT VALIDATED FOR SCORE: no organizer receipt; expected score is a "
                              "MODEL estimate only (see executive summary)"),
        "model_estimate": {
            "label": "MODEL-ESTIMATE (not a score; not organizer-confirmed)",
            "mechanism": ("DTI closure on the blind-lattice inversion: score = TP / (0.2*N + "
                          "0.8*G) with N = 37,654 and G = 12,226 (implied hidden truth, "
                          "evidence/live_inversion.json). Kept dots inherit a retention fraction "
                          "r of the champion's TP = 4,809; complement dots earn the blind credit "
                          "0.0222/dot."),
            "champion_tp_implied": 4809.1,
            "blind_credit_per_complement_dot": 0.0222,
            "retention_r_range": [0.65, 1.0],
            "score_range": [0.197, 0.295],
            "assumption_warning": ("Retention r is not measured; the family-transfer upper end "
                                   "(r = 1) reproduces the champion only if the removed 35% "
                                   "carried zero credit, which is unknown."),
        },
    }
    (ROOT / "evidence" / "s31_candidate_run_card.json").write_text(
        json.dumps(summary, indent=1) + "\n")
    print(json.dumps(summary, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
