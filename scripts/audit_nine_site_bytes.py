#!/usr/bin/env python3
"""Byte-level audit of the nine competitor sites' best-claimed GeoTIFFs.

Reads the actual .tif bytes (not web pages or claims) from local clones of the
competitor repositories and checks, for each file:

* official format (float32, single band, EPSG:32611, 100 m, shape/transform
  of the competition grid, values in [0, 1] inside the footprint, NaN/nodata
  handling outside it);
* positive-pixel (dot) count and overlap with the catalogue labels;
* pairwise overlap: fraction of A's dots within 3 px (300 m) of any dot of B,
  and the Spearman rank correlation over the footprint (binary => phi).

Usage:
  python scripts/audit_nine_site_bytes.py --sites-dir /path/to/clones \
      --labels data/labels.tif --out evidence/nine_site_byte_audit.json

The site repositories are NOT vendored in this checkout. Fetch them from
github.com (codeload tarballs of buffedlizard55-lab/GEMSDOE<NN>, main branch)
into --sites-dir, one directory per site, then run this script.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy import ndimage

# Best-claimed file per site, exactly as named in the prompt's leaderboard lists.
# The claimed score is copied from the prompt; it is USER-REPORTED, not organizer-confirmed.
BEST_CLAIMS: dict[str, tuple[str, float]] = {
    "GEMSDOE24": ("h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan", 0.2477),
    "GEMSDOE25": ("dotted-h19-5-d2-8-20261002-e56ea318af89-nan", 0.2600),
    "GEMSDOE27": ("topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan", 0.2449),
    "GEMSDOE28": ("h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan", 0.2710),
    "GEMSDOE30": ("d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca", 0.2600),
    "GEMSDOE31": ("h27-4-solo-d28-20261004-8acb75e1-nan", 0.2708),
    "GEMSDOE32": ("h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros", 0.2778),
    "GEMSDOE33": ("h33d-analog-tip-stepover-r30-20261004-cb490425926e", 0.2632),
    "GEMSDOE36": ("anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros", 0.2750),
}

RADIUS_PX = 3  # 300 m at 100 m pixels (official metric kernel support)
OVERLAP_LIMIT = 0.70  # the lane protocol's 3-px duplicate threshold
RHO_LIMIT = 0.90
EXPECTED_SHAPE = (3730, 3292)
EXPECTED_TRANSFORM = (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_file(sites_dir: Path, site: str, slug: str) -> Path | None:
    matches = sorted((sites_dir / site).rglob(f"*{slug}*.tif"))
    # Prefer the file under docs/downloads and the exact slug match.
    exact = [m for m in matches if m.name.endswith(".tif") and slug in m.name]
    exact.sort(key=lambda m: ("docs/downloads" not in str(m), len(m.name)))
    return exact[0] if exact else None


def read_binary(path: Path) -> tuple[np.ndarray, np.ndarray, dict]:
    """Return (values_in_footprint_mask, binary_positive_map, format_record)."""
    with rasterio.open(path) as src:
        arr = src.read(1).astype("float64")
        record = {
            "count": src.count,
            "dtype": src.dtypes[0],
            "shape": list(src.shape),
            "crs": src.crs.to_string() if src.crs else None,
            "transform": list(src.transform)[:6],
            "nodata": src.nodata,
        }
    finite = np.isfinite(arr)
    record["finite_pixels"] = int(finite.sum())
    record["nan_pixels"] = int((~finite).sum())
    record["values_min"] = float(np.nanmin(arr)) if finite.any() else None
    record["values_max"] = float(np.nanmax(arr)) if finite.any() else None
    record["unique_finite_values"] = [float(v) for v in np.unique(arr[finite])[:4]]
    record["in_0_1_all_finite"] = bool(finite.any() and np.all((arr[finite] >= 0) & (arr[finite] <= 1)))
    record["positive_pixels"] = int(np.sum(arr[finite] > 0))
    record["format_matches_grid"] = bool(
        record["count"] == 1
        and record["dtype"] == "float32"
        and tuple(record["shape"]) == EXPECTED_SHAPE
        and tuple(round(v, 6) for v in record["transform"]) == EXPECTED_TRANSFORM
        and record["crs"] == "EPSG:32611"
    )
    positive = np.zeros(arr.shape, dtype=bool)
    positive[finite] = arr[finite] > 0
    return finite, positive, record


def within_radius(a_pos: np.ndarray, b_pos: np.ndarray) -> float:
    """Fraction of A positives with a B positive within RADIUS_PX pixels."""
    if not b_pos.any():
        return 0.0
    dist_to_b = ndimage.distance_transform_edt(~b_pos)
    a_count = int(a_pos.sum())
    if a_count == 0:
        return 0.0
    return float(np.sum(dist_to_b[a_pos] <= RADIUS_PX) / a_count)


def phi(a: np.ndarray, b: np.ndarray, footprint: np.ndarray) -> float:
    x = a[footprint].astype("float64")
    y = b[footprint].astype("float64")
    if x.std() == 0 or y.std() == 0:
        return float("nan")
    return float(np.corrcoef(x, y)[0, 1])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sites-dir", type=Path, required=True)
    parser.add_argument("--labels", type=Path, default=Path("data/labels.tif"))
    parser.add_argument("--footprint", type=Path, default=Path("data/sample_submission.tif"),
                        help="raster whose finite pixels define the GeoDAWN footprint (5,167,373 px)")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    with rasterio.open(args.footprint) as src:
        footprint_mask = np.isfinite(src.read(1).astype("float64"))

    catalogue = None
    if args.labels.is_file():
        with rasterio.open(args.labels) as src:
            lab = src.read(1)
            catalogue = (lab == 1)

    files: dict[str, dict] = {}
    masks: dict[str, tuple[np.ndarray, np.ndarray, np.ndarray]] = {}
    for site, (slug, claim) in BEST_CLAIMS.items():
        path = find_file(args.sites_dir, site, slug)
        if path is None:
            files[site] = {"status": "MISSING", "slug": slug, "claimed_score": claim}
            continue
        finite, positive, record = read_binary(path)
        record.update(
            {
                "status": "READ",
                "site": site,
                "file": str(path.relative_to(args.sites_dir)),
                "sha256": sha256(path),
                "claimed_score": claim,
                "claim_class": "USER-REPORTED / UNVERIFIED (no organizer receipt)",
            }
        )
        if catalogue is not None:
            record["positives_on_catalogue"] = int(np.sum(positive & catalogue))
        record["dots_within_3px_of_catalogue"] = None
        if catalogue is not None and catalogue.any():
            dist_cat = ndimage.distance_transform_edt(~catalogue)
            record["dots_within_3px_of_catalogue"] = int(np.sum(positive & (dist_cat <= RADIUS_PX)))
        files[site] = record
        masks[site] = (footprint_mask, positive, finite)

    sites = [s for s in BEST_CLAIMS if s in masks]
    overlap = {}
    rho = {}
    for a in sites:
        overlap[a] = {}
        rho[a] = {}
        for b in sites:
            if a == b:
                continue
            overlap[a][b] = round(within_radius(masks[a][1], masks[b][1]), 4)
            rho[a][b] = round(phi(masks[a][1], masks[b][1], footprint_mask), 4)

    pair_flags = []
    for a in sites:
        for b in sites:
            if a >= b:
                continue
            o = max(overlap[a][b], overlap[b][a])
            r = rho[a][b]
            dup = o > OVERLAP_LIMIT or (r == r and abs(r) > RHO_LIMIT)
            pair_flags.append({"a": a, "b": b, "max_overlap_3px": o, "phi": r, "duplicate_under_lane_rule": dup})

    summary = {
        "schema": "nine-site-byte-audit/v1",
        "generated_by": "scripts/audit_nine_site_bytes.py",
        "rule_references": {
            "overlap_limit": OVERLAP_LIMIT,
            "radius_px": RADIUS_PX,
            "rho_limit": RHO_LIMIT,
            "source": "Internal lane protocol (not an organizer rule). Official rules contain no duplicate rule.",
        },
        "files": files,
        "overlap_3px": overlap,
        "phi_footprint": rho,
        "pair_flags": pair_flags,
        "pairs_flagged_duplicate": sum(1 for p in pair_flags if p["duplicate_under_lane_rule"]),
        "pairs_total": len(pair_flags),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(summary, indent=2) + "\n")
    print(f"wrote {args.out}: {len(sites)} files read, {summary['pairs_flagged_duplicate']}/{summary['pairs_total']} pairs flagged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
