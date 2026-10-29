#!/usr/bin/env python3
"""Literal duplicate / lane gate for one candidate GeoTIFF against every pinned registry raster.

Decisive gate = shared project rule (data/shared_template/src/gems/novelty.py ``compare_registry``):
  * raw or kernel rank correlation with any registry raster > 0.90 -> duplicate
  * > 70% of candidate dots within 3 px of that raster's dots (dot = value > 0) -> duplicate
Supplementary (reported, not decisive): overlap using dot = value > 0.5 (scripts/run_s25_pcse.py
convention). The more conservative of the two is shown as ``max_overlap_either_convention``.
Also reports exact file SHA-256 duplicates. Output: evidence/s29_registry_gate.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, paths, registry_compare  # noqa: E402
from gems27.shared_template import load_shared  # noqa: E402

REG_DIR = ROOT / "data/research/registry_rasters"
REG_RECEIPT = ROOT / "evidence/s29_registry_fetch.json"
LOCAL_DIR = ROOT / "docs/downloads"
OUT = ROOT / "evidence/s29_registry_gate.json"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def build_entries(foot: np.ndarray):
    """Pinned registry entries (SHA-verified receipt) plus readable local TIFs, deduplicated by SHA."""
    receipt = json.loads(REG_RECEIPT.read_text(encoding="utf-8"))
    entries, skipped, seen = [], [], set()
    for row in receipt["rows"]:
        if not row.get("sha_match"):
            raise SystemExit(f"registry receipt mismatch for {row['id']}")
        path = REG_DIR / f"{row['id']}.tif"
        if sha256_file(path) != row["sha256"]:
            raise SystemExit(f"cached raster hash changed: {path.name}")
        entries.append({"id": row["id"], "file": row["file"], "cache_path": str(path.relative_to(ROOT)),
                        "sha256": row["sha256"], "source": f"{row['repo']}@{row['ref'][:12]}"})
        seen.add(row["sha256"])
    for p in sorted(LOCAL_DIR.glob("*.tif")):
        sha = sha256_file(p)
        if sha in seen:
            continue
        seen.add(sha)
        entries.append({"id": f"local:{p.name}", "file": p.name, "cache_path": str(p.relative_to(ROOT)),
                        "sha256": sha, "source": "repo docs/downloads (historical, owner)"})
    ok = []
    for e in entries:
        try:
            with rasterio.open(ROOT / e["cache_path"]) as ds:
                a = ds.read(1)
                if ds.shape != foot.shape or ds.crs is None or ds.crs.to_epsg() != grid.CRS_EPSG:
                    raise ValueError("grid")
                if not np.isfinite(a[foot]).all() or np.any((a[foot] < 0) | (a[foot] > 1)):
                    raise ValueError("values outside [0,1] or non-finite in footprint")
            e["footprint_sha256"] = hashlib.sha256(np.asarray(a[foot], dtype="<f4").tobytes()).hexdigest()
            ok.append(e)
        except (ValueError, rasterio.errors.RasterioIOError) as exc:
            skipped.append({"id": e["id"], "reason": str(exc)})
    return ok, skipped


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("candidate", type=Path)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()
    cand = args.candidate.resolve()
    shared = load_shared(ROOT)
    foot = grid.load_footprint(paths.TEMPLATE)
    with rasterio.open(cand) as ds:
        vals = ds.read(1).astype(np.float64)
        if ds.shape != grid.SHAPE or ds.crs.to_epsg() != grid.CRS_EPSG or ds.transform != paths_transform():
            raise SystemExit("candidate grid mismatch")
    if not np.isfinite(vals[foot]).all() or vals[foot].min() < 0 or vals[foot].max() > 1:
        raise SystemExit("candidate violates finite/[0,1] inside footprint; gate refuses to score it")
    dots = foot & (vals > 0)
    if not dots.any():
        raise SystemExit("candidate has no dots")
    entries, skipped = build_entries(foot)
    cand_sha = sha256_file(cand)
    exact = [e["id"] for e in entries if e["sha256"] == cand_sha]
    comp = shared.novelty.compare_registry(vals, foot, entries, ROOT, dots=dots, template_path=paths.TEMPLATE,
                                           sample_size=200_000)
    rows = []
    for r in comp["rows"] if isinstance(comp, dict) and "rows" in comp else comp.get("entries", []):
        rid = r.get("registry_id")
        e = next(x for x in entries if x["id"] == rid)
        ref = np.asarray(rasterio.open(ROOT / e["cache_path"]).read(1))
        half = registry_compare.within_fraction(dots, foot & np.isfinite(ref) & (ref > 0.5), 3.0)
        r = {**r, "supplementary_overlap_gt05": half, "file_sha256": e["sha256"], "exact_file_duplicate": e["sha256"] == cand_sha}
        r["max_overlap_either_convention"] = max(x for x in (r.get("candidate_dot_overlap_within_3px"), half) if x is not None) if (r.get("candidate_dot_overlap_within_3px") is not None or half is not None) else None
        rows.append(r)
    max_ov = max((r["max_overlap_either_convention"] for r in rows if r["max_overlap_either_convention"] is not None), default=None)
    flagged = [r["registry_id"] for r in rows if r.get("duplicate") or r.get("exact_file_duplicate")]
    result = {
        "schema": "s29-registry-gate-v1",
        "candidate": cand.name,
        "candidate_sha256": cand_sha,
        "candidate_dots": int(dots.sum()),
        "references_checked": len(rows),
        "references_skipped": skipped,
        "rules": {"rank_limit": 0.90, "overlap_limit": 0.70, "radius_px": 3.0, "decisive": "novelty.compare_registry (dot = value>0)"},
        "exact_file_duplicates": exact,
        "max_candidate_within_3px_any_convention": max_ov,
        "flagged_duplicates": flagged,
        "lane_protocol_passed": bool(comp["passed"]) and not flagged and not exact,
        "rows": rows,
        "interpretation": "Literal protocol result only. Not a holdout score, not an organizer score, and not permission to submit.",
    }
    args.out.write_text(json.dumps(result, indent=2, default=float, allow_nan=False) + "\n", encoding="utf-8")
    print(f"refs={len(rows)} skipped={len(skipped)} flagged={len(flagged)} passed={result['lane_protocol_passed']} max_overlap={max_ov}")
    return 0


def paths_transform():
    return rasterio.Affine(*grid.TRANSFORM)


if __name__ == "__main__":
    raise SystemExit(main())
