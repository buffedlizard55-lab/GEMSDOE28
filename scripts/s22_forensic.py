#!/usr/bin/env python3
"""S22 Experiment 1 — byte forensic on already-scored files (learning only, emits no dots).

Fetches were made 2026-10-26 via the GitHub contents API into evidence/_scratch/registry32/
(git-ignored). All scores are USER-REPORTED (owner prompt/sites); no organizer receipt exists
in this repository. This script only measures dot-set identity/overlap of existing files.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid  # noqa: E402
from gems27.thinning import dot_thin  # noqa: E402

SCRATCH = ROOT / "evidence/_scratch/registry32"
DATA = ROOT / "data"
DL = ROOT / "docs/downloads"


def read1(path: Path) -> np.ndarray:
    with rasterio.open(path) as ds:
        return ds.read(1)


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dotset_sha(dots: np.ndarray) -> str:
    rc = np.argwhere(dots).astype(np.int32)
    return hashlib.sha256(rc.tobytes()).hexdigest()


def main() -> int:
    labels = grid.load_labels(DATA / "labels.tif")
    foot = grid.load_footprint(DATA / "sample_submission.tif")
    d_cat = distance_transform_edt(~labels)

    files = {
        "h19_5_parent_GEMSDOE19_reported_0.1922": DATA / "h19_5_nan.tif",
        "GEMSDOE24_best_dotted_d1.5_reported_0.2477": DATA / "dotted_h19_5_d1_5_nan.tif",
        "GEMSDOE25_best_dotted_d2.8_reported_0.2600": DATA / "dotted_h19_5_d2_8_nan.tif",
        "GEMSDOE27_best_topo_gap_tv2_reported_0.2449":
            DL / "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif",
        "GEMSDOE28_solo_r1_reported_0.2708":
            DL / "gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-allfinite.tif",
        "GEMSDOE28_best_h36_1_rung30_reported_0.2710":
            DL / "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif",
        "GEMSDOE30_best_d28_poisson_reported_0.2600": SCRATCH / "best30.tif",
        "GEMSDOE31_best_solo_d28_reported_0.2708": SCRATCH / "best31.tif",
        "GEMSDOE32_champion_h33_2_b2_reported_0.2778": SCRATCH / "champion32_zeros.tif",
        "GEMSDOE33_best_h33d_reported_0.2632": SCRATCH / "best33.tif",
        "GEMSDOE36_best_pinn_reported_0.2750": SCRATCH / "pinn36_zeros.tif",
    }
    dots: dict[str, np.ndarray] = {}
    info: dict[str, dict] = {}
    for name, path in files.items():
        a = read1(path)
        d = np.isfinite(a) & (a > 0)
        dots[name] = d
        info[name] = {
            "path": str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path),
            "file_sha256": sha256_file(path),
            "dotset_sha256": dotset_sha(d),
            "n_dots": int(d.sum()),
            "dots_on_catalogue": int((d & labels).sum()),
            "dots_outside_footprint": int((d & ~foot).sum()),
            "min_dist_to_catalogue_px": float(d_cat[d].min()) if d.any() else None,
            "value_set_inside": sorted({float(v) for v in np.unique(a[foot & np.isfinite(a)])})[:5],
        }

    champ_name = "GEMSDOE32_champion_h33_2_b2_reported_0.2778"
    champ = dots[champ_name]
    d_champ = distance_transform_edt(~champ)
    overlap = {}
    for name, d in dots.items():
        if name == champ_name:
            continue
        overlap[name] = {
            "frac_own_dots_within3px_of_champion": float((d_champ[d] <= 3).mean()),
            "frac_champion_dots_within3px_of_own": float(
                (distance_transform_edt(~d)[champ] <= 3).mean()),
            "exact_shared_dots": int((d & champ).sum()),
            "jaccard_exact": float((d & champ).sum() / max((d | champ).sum(), 1)),
        }

    # Champion lineage replication (learning only)
    h195 = dots["h19_5_parent_GEMSDOE19_reported_0.1922"] & foot
    re_dotted = dot_thin(h195 & ~labels, 2.8)
    dotted28 = dots["GEMSDOE25_best_dotted_d2.8_reported_0.2600"]
    solo = dots["GEMSDOE28_solo_r1_reported_0.2708"]
    lineage = {
        "h19_5_offcat_px_used": int((h195 & ~labels).sum()),
        "recomputed_dot_thin_2.8_px": int(re_dotted.sum()),
        "symdiff_recomputed_vs_dotted_d2.8_file": int((re_dotted ^ dotted28).sum()),
        "recomputed_solo_dotted_minus_ring_le1_px": int((dotted28 & (d_cat > 1)).sum()),
        "symdiff_recomputed_solo_vs_solo_file": int(((dotted28 & (d_cat > 1)) ^ solo).sum()),
        "recomputed_champion_solo_minus_ring_le2_px": int((solo & (d_cat > 2)).sum()),
        "symdiff_recomputed_champion_vs_fetched_GEMSDOE32_bytes": int(((solo & (d_cat > 2)) ^ champ).sum()),
        "b3_solo_minus_ring_le3_px_NOT_SHIPPED_duplicate": int((solo & (d_cat > 3)).sum()),
        "b3_frac_within3px_of_champion": float(
            (d_champ[(solo & (d_cat > 3))] <= 3).mean()),
        "champion_dot_distance_to_catalogue_histogram_px": {
            "(2,3]": int((champ & (d_cat > 2) & (d_cat <= 3)).sum()),
            "(3,5]": int((champ & (d_cat > 3) & (d_cat <= 5)).sum()),
            "(5,10]": int((champ & (d_cat > 5) & (d_cat <= 10)).sum()),
            ">10": int((champ & (d_cat > 10)).sum()),
        },
    }

    out = {
        "experiment": "S22 Exp1 forensic (learning only; no candidate dots)",
        "date_utc": "2026-10-26",
        "score_provenance": "All scores USER-REPORTED in the session prompt; none is an organizer receipt.",
        "fetched_bytes": "GEMSDOE30/31/32/33/36 best files fetched 2026-10-26 via GitHub contents API (raw).",
        "files": info,
        "overlap_vs_champion": overlap,
        "champion_lineage": lineage,
    }
    ev = ROOT / "evidence/s22_forensic.json"
    ev.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"files": {k: v["n_dots"] for k, v in info.items()},
                      "overlap_vs_champion": overlap, "lineage": lineage}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
