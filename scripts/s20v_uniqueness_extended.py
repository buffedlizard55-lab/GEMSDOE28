#!/usr/bin/env python3
"""S20V Pass-2/merge extended uniqueness: candidate dots vs every distinct registry dot-set.

Registry = all .tif dot-sets under sparse clones (/tmp/gems-mirrors/*/docs/downloads) plus local
docs/downloads (which after the PR #53 merge includes the parallel S19-ASCP, S19B-RADLIN and
Session 20-H43 rasters). Own content-id files excluded; nan/zeros convention duplicates collapsed
by dot-set hash. Writes evidence/s20v_uniqueness_extended.json. Threshold: >0.70 within 3 px fails.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
CID = "7a7c5e449fe0"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        while chunk := fh.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def load_dots(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        a = s.read(1)
    return np.isfinite(a) & (a > 0)


def main() -> int:
    ours_path = ROOT / "docs/downloads/gems28-s20-vesselness-lidarstep-20261026-7a7c5e449fe0-allfinite.tif"
    ours = load_dots(ours_path)
    oy, ox = np.nonzero(ours)
    pts = np.c_[oy, ox].astype(float)
    seen_sha = {sha256_file(ours_path)}
    seen_dotsets = {hashlib.sha256(ours.tobytes()).hexdigest()}
    candidates = sorted(Path("/tmp/gems-mirrors").glob("*/docs/downloads/*.tif")) + sorted(
        (ROOT / "docs/downloads").glob("*.tif"))
    rows, skipped_self, skipped_dotdup = [], 0, 0
    for p in candidates:
        if CID in p.name:
            skipped_self += 1
            continue
        sha = sha256_file(p)
        if sha in seen_sha:
            continue
        seen_sha.add(sha)
        try:
            ref = load_dots(p)
        except Exception:
            continue
        dh = hashlib.sha256(ref.tobytes()).hexdigest()
        if dh in seen_dotsets:
            skipped_dotdup += 1
            continue
        seen_dotsets.add(dh)
        ry, rx = np.nonzero(ref)
        if len(ry) == 0:
            continue
        d, _ = cKDTree(np.c_[ry, rx].astype(float)).query(pts, workers=1)
        rows.append({"file": str(p), "sha256": sha, "dotset_sha256": dh,
                     "registry_dots": int(len(ry)),
                     "frac_our_dots_within3px": float((d <= 3.0).mean())})
    rows.sort(key=lambda r: -r["frac_our_dots_within3px"])
    out = {"scope": ("S20V extended uniqueness, regenerated at PR #53 merge so the registry includes the "
                     "parallel S19-ASCP / S19B-RADLIN / Session 20-H43 rasters merged to main. Distinct "
                     "dot-sets under sparse clones of GEMSDOE,GEMSDOE24,25,27,30,31,32,33,36 docs/downloads "
                     "+ local docs/downloads, snapshot 2026-10-26."),
           "n_distinct_dotsets": len(rows), "skipped_own_files": skipped_self,
           "skipped_dotset_duplicates": skipped_dotdup, "our_dots": int(len(oy)),
           "threshold_stop_above": 0.70, "worst": rows[0] if rows else None,
           "pass": bool(rows and rows[0]["frac_our_dots_within3px"] <= 0.70),
           "top10": rows[:10], "all": rows,
           "pass2_note": ("Pre-merge run (100 dot-sets, worst 54.2% GEMSDOE31 lidar-scarp) predated the "
                          "parallel-session rasters; this regeneration supersedes its registry scope.")}
    (ROOT / "evidence/s20v_uniqueness_extended.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"n": len(rows), "pass": out["pass"], "worst": out["worst"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
