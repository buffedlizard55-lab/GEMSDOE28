#!/usr/bin/env python3
"""S24 independent re-check of the nine focus-site best files (GEOMETRY-AUDIT, not HOLDOUT-DTI).

Re-fetches each file from its pinned GitHub commit (docs/data/s23_scorecard.json `source`), hashes
the bytes, counts positive cells inside the competition footprint and computes every pairwise
within-3 px dot overlap plus overlap against the registry-039 lattice control.
The overlap definition mirrors the protocol: fraction of candidate A's dots within 3 px of B's dots.
Raw fetched bytes stay under data/ (git-ignored).
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, paths  # noqa: E402

SCORECARD = ROOT / "docs" / "data" / "s23_scorecard.json"
FETCH = ROOT / "data" / "s24_fetch"
OUT = ROOT / "evidence" / "s24_nine_site_overlap.json"
CONTROL = ROOT / "data" / "s24_fetch" / "lattice_control.tif"  # filled below from the S23 pin
CONTROL_SHA = "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2"
CONTROL_SOURCE = ("https://github.com/buffedlizard55-lab/GEMSDOE24/blob/"
                  "07345ea0604953d7efb858d9cfbc21e20c7aca0b/inputs/calibration/"
                  "13gems_20261001_r13-lattice-s5_v2_nan-outside.tif")


def fetch(url: str, dest: Path) -> None:
    """Fetch a github.com /blob/<sha>/<path> URL through the GitHub API (raw content)."""
    prefix = "https://github.com/"
    assert url.startswith(prefix) and "/blob/" in url, url
    repo_part, rest = url[len(prefix):].split("/blob/", 1)
    sha, path = rest.split("/", 1)
    if not dest.exists():
        with dest.open("wb") as out:
            subprocess.run(["gh", "api", f"repos/{repo_part}/contents/{path}?ref={sha}",
                            "-H", "Accept: application/vnd.github.raw"], stdout=out, check=True)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def dots_of(path: Path, foot: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as ds:
        a = ds.read(1)
        assert a.shape == foot.shape, (path, a.shape)
    v = np.where(np.isfinite(a), a, 0)
    if (v[foot] < 0).any() or (v[foot] > 1).any():
        raise SystemExit(f"{path.name}: in-footprint values outside [0,1]")
    return foot & (v > 0)


def within3(a: np.ndarray, b: np.ndarray) -> float:
    """Fraction of a's dots lying within 3 px of some b dot."""
    if a.sum() == 0 or b.sum() == 0:
        return 0.0
    d = distance_transform_edt(~b)
    return float((d[a] <= 3.0).mean())


def main() -> int:
    foot = grid.load_footprint(paths.TEMPLATE)
    sc = json.loads(SCORECARD.read_text())
    rows = []
    for s in sc["sites"]:
        name = s["file"]
        dest = FETCH / f"{s['site']}-{name}"
        fetch(s["source"], dest)
        rows.append({"site": s["site"], "file": name, "source": s["source"],
                     "highest_supplied_score": s["highest_supplied_score"],
                     "bytes": dest.stat().st_size, "sha256": sha256(dest), "path": dest})
    control_path = FETCH / "lattice_control.tif"
    if not control_path.exists():
        # The control is in this repo's own evidence/S23 lineage; fetch the pinned GitHub blob.
        fetch(CONTROL_SOURCE, control_path)
    ctl_sha = sha256(control_path)
    if ctl_sha != CONTROL_SHA:
        raise SystemExit(f"lattice control sha mismatch: {ctl_sha}")

    dots = {r["site"]: dots_of(r["path"], foot) for r in rows}
    labels = grid.load_labels(paths.LABELS)
    d_cat = distance_transform_edt(~labels)  # distance to the competition catalogue (known faults)
    ctl = dots_of(control_path, foot)
    sites = [r["site"] for r in rows]
    matrix = {}
    for a in sites:
        for b in sites:
            if a != b:
                matrix[f"{a}->{b}"] = within3(dots[a], dots[b])
    worst_pair = max(matrix.items(), key=lambda kv: kv[1])
    lattice = {a: within3(dots[a], ctl) for a in sites}

    result = {
        "schema": "s24-nine-site-overlap-v1",
        "label": "GEOMETRY-AUDIT (not HOLDOUT-DTI, not an organizer score)",
        "rule": "overlap(A->B) = fraction of A's dots within 3 px of any B dot; duplicate if > 0.70",
        "footprint_pixels": int(foot.sum()),
        "control": {"file": control_path.name, "sha256": ctl_sha, "dots": int(ctl.sum()),
                    "source": CONTROL_SOURCE,
                    "note": "calibration lattice, not a competition submission"},
        "files": [{"site": r["site"], "file": r["file"], "source": r["source"],
                   "bytes": r["bytes"], "sha256": r["sha256"], "dots_in_footprint": int(dots[r["site"]].sum()),
                   "highest_supplied_score": r["highest_supplied_score"],
                   "overlap_to_lattice_control": lattice[r["site"]],
                   "dots_on_catalogue_px": int((dots[r["site"]] & labels).sum()),
                   "dots_within_2px_of_catalogue": int((dots[r["site"]] & (d_cat <= 2)).sum()),
                   "median_catalogue_distance_px": float(np.median(d_cat[dots[r["site"]]])),
                   } for r in rows],
        "pairwise_overlap": matrix,
        "max_pairwise_overlap": {"pair": worst_pair[0], "value": worst_pair[1]},
        "pairs_over_0_70": int(sum(v > 0.70 for v in matrix.values())),
        "pairs_total": len(matrix),
        "identical_dot_sets": [f"{a}=={b}" for i, a in enumerate(sites) for b in sites[i + 1:]
                               if dots[a].shape == dots[b].shape and (dots[a] == dots[b]).all()],
    }
    # Exact set relations between the focus-site files (verified, not inferred from scores).
    by_site = {r["site"]: dots[r["site"]] for r in rows}
    labels_b = grid.load_labels(paths.LABELS)
    assert labels_b.shape == foot.shape
    nested = {
        "GEMSDOE32_subset_of_GEMSDOE31": bool(not (by_site["GEMSDOE32"] & ~by_site["GEMSDOE31"]).any()),
        "GEMSDOE31_minus_GEMSDOE32_count": int((by_site["GEMSDOE31"] & ~by_site["GEMSDOE32"]).sum()),
        "GEMSDOE31_dots_within_2px_of_catalogue": int((by_site["GEMSDOE31"] & (d_cat <= 2)).sum()),
        "GEMSDOE31_removed_set_equals_within2px_set": bool(
            ((by_site["GEMSDOE31"] & ~by_site["GEMSDOE32"]) == (by_site["GEMSDOE31"] & (d_cat <= 2))).all()),
        "GEMSDOE32_subset_of_GEMSDOE36": bool(not (by_site["GEMSDOE32"] & ~by_site["GEMSDOE36"]).any()),
        "GEMSDOE36_minus_GEMSDOE32_count": int((by_site["GEMSDOE36"] & ~by_site["GEMSDOE32"]).sum()),
        "catalogue_pixels_in_footprint": int((labels_b & foot).sum()),
    }
    result["nested_relations"] = nested
    OUT.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: result[k] for k in ("pairs_over_0_70", "pairs_total", "max_pairwise_overlap",
                                             "identical_dot_sets")}, indent=2))
    print("lattice overlap:", {k: round(v, 4) for k, v in lattice.items()})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
