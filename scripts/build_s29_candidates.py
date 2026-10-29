#!/usr/bin/env python3
"""S29 candidate builder: (A) dense S29 surface, (B) hole-constrained S29 surface.

A = top-37,654 ridge-NMS dots of the all-catalogue HGB surface (the S29 design). Expected to fail the gate.
B = same surface, but with >= 32% of dots forced into pixels > 3 px from every one of the 87 local/registry
    reference dot sets (the only region where the literal 70% overlap rule can pass). N is the largest
    tested count whose worst-reference overlap is <= 0.69 (margin under the 0.70 limit).
Writes candidates to data/research/candidates/ (git-ignored). The gate decides any promotion; this script
never marks a file OK. Output: evidence/s29_candidate_build.json.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import run_s29_experiment as s29  # noqa: E402
import s29_gate  # noqa: E402
from gems27 import paths, submission  # noqa: E402
from gems27.shared_template import load_shared  # noqa: E402

CAND_DIR = ROOT / "data/research/candidates"
CACHE = ROOT / "data/research/s29_within3"
N_GRID = [37654, 30000, 25000, 20000, 15000, 12000, 10000, 8000, 6000]
MARGIN_LIMIT = 0.69
HOLE_SHARE = 0.32


def main() -> int:
    shared = load_shared(ROOT)
    footprint, catalogue = s29.load_grid()
    X, _ = s29.load_features(footprint)
    fp_idx = np.flatnonzero(footprint.ravel())
    surface = s29.fit_surface(X, fp_idx, footprint.ravel()[fp_idx], catalogue.ravel()[fp_idx], seed=s29.SEED)
    eligible = footprint & ~catalogue
    nms = shared.metric.ridge_nms(surface, eligible, sigma=1.0) & eligible
    CAND_DIR.mkdir(parents=True, exist_ok=True)
    CACHE.mkdir(parents=True, exist_ok=True)

    entries, skipped = s29_gate.build_entries(footprint)
    within = {}
    for e in entries:
        f = CACHE / f"{e['sha256'][:16]}.npy"
        if f.is_file():
            within[e["id"]] = np.unpackbits(np.load(f))[: footprint.size].astype(bool).reshape(footprint.shape)
            continue
        with rasterio.open(s29_gate.ROOT / e["cache_path"]) as ds:
            a = ds.read(1)
        dots = footprint & np.isfinite(a) & (a > 0)
        w = (distance_transform_edt(~dots) <= 3.0) & footprint if dots.any() else np.zeros_like(footprint)
        within[e["id"]] = w
        np.save(f, np.packbits(w.ravel()))
    union_cover = np.zeros_like(footprint)
    for w in within.values():
        union_cover |= w
    hole_all = footprint & ~union_cover
    hole_039 = footprint & ~within["registry-039"]

    def worst_overlap(dots: np.ndarray):
        n = int(dots.sum())
        worst = max(((within[k] & dots).sum() / n, k) for k in within)
        return float(worst[0]), worst[1]

    # A: dense S29 design.
    dense = shared.metric.select_top_positive(surface, nms, s29.K_TOTAL).astype(bool)
    a_vals = np.where(dense, np.float32(1.0), np.float32(0.0))
    a_worst = worst_overlap(dense)
    a_name = "s29_A_dense_k37654.tif"
    submission.write_geotiff(a_vals, paths.TEMPLATE, CAND_DIR / a_name, outside="nan")

    # B: hole-constrained, largest N with worst reference overlap <= MARGIN_LIMIT.
    hole_pool = hole_039 & eligible
    search = []
    chosen = None
    for n in N_GRID:
        h = min(int(hole_pool.sum()), int(np.ceil(HOLE_SHARE * n)))
        hole_sel = shared.metric.select_top_positive(surface, hole_pool, h).astype(bool) if h else np.zeros_like(footprint)
        rest = shared.metric.select_top_positive(surface, nms & ~hole_pool, n - int(hole_sel.sum())).astype(bool)
        dots = hole_sel | rest
        worst, wk = worst_overlap(dots)
        search.append({"N": int(dots.sum()), "hole_dots": int(hole_sel.sum()), "worst_overlap": worst,
                       "worst_reference": wk, "passes_margin": worst <= MARGIN_LIMIT})
        if chosen is None and worst <= MARGIN_LIMIT and dots.sum() > 0:
            chosen = dots
            break
    if chosen is None:
        raise SystemExit("no tested hole-constrained N passes the margin")
    b_vals = np.where(chosen, np.float32(1.0), np.float32(0.0))
    b_name = f"s29_B_holeconstrained_k{int(chosen.sum())}.tif"
    submission.write_geotiff(b_vals, paths.TEMPLATE, CAND_DIR / b_name, outside="nan")

    out = {
        "schema": "s29-candidate-build-v1",
        "entries_used": len(entries),
        "entries_skipped": skipped,
        "uncovered_px_union_all_references": int(hole_all.sum()),
        "uncovered_px_registry_039": int(hole_039.sum()),
        "A": {"file": a_name, "dots": int(dense.sum()), "worst_overlap": a_worst[0], "worst_reference": a_worst[1]},
        "B_search": search,
        "B": {"file": b_name, "dots": int(chosen.sum()), "hole_dots": int((chosen & hole_039).sum())},
        "interpretation": "Builder output only. Overlap here is a pre-gate estimate; the gate decides OK status.",
    }
    (ROOT / "evidence/s29_candidate_build.json").write_text(json.dumps(out, indent=2, default=float, allow_nan=False) + "\n")
    print(json.dumps({k: out[k] for k in ("uncovered_px_union_all_references", "uncovered_px_registry_039", "A", "B")}, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
