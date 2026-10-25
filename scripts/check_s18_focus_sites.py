#!/usr/bin/env python3
"""S18 Pass-3 verification (not an experiment): final-dot overlap of the built
H39-5 candidate vs the scored rasters of the prompt's focus sites that were
not already in the Exp1/Exp3 registry tables.

Rasters checked (education/forensic only; nothing copied into any shipped file):
  * GEMSDOE33 h33d-analog-tip-stepover-r30 cb490425926e (owner-reported 0.2632),
    /tmp/forensic copy byte-verified vs its published receipt primary_sha256.
  * GEMSDOE25/30 dotted-h19-5-d2-8 (owner-reported 0.2600): the GEMSDOE30 scored
    filename carries content id 91eae1ca, matching the pinned local mirror
    data/dotted_h19_5_d2_8_nan.tif (sha256 91eae1ca... in registry/data_manifest.json).
  * GEMSDOE24 dotted-h19-5-d1-5 (owner-reported 0.2477): pinned local mirror
    data/dotted_h19_5_d1_5_nan.tif.
Already covered in evidence/s18_candidate_build.json: GEMSDOE32 champion (0.2778),
GEMSDOE36 (0.2750), GEMSDOE27 T-v2 + GEMSDOE28/31 solo & rungs (local *-nan.tif).
Writes evidence/s18_focus_sites_overlap.json. All scores OWNER-REPORTED.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import paths  # noqa: E402

CANDIDATE = ROOT / "docs/downloads/gems28-h39-5-extrap-swap35-20261025-719b83fb659b-nan.tif"
TARGETS = {
    "gems33_h33d_cb490425926e_owner_reported_0.2632": (
        Path("/tmp/forensic/gems33_cb490425926e.tif"),
        "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757"),
    "gems25_30_dotted_h19_5_d2_8_owner_reported_0.2600": (
        paths.DOTTED_D2_8, "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8"),
    "gems24_dotted_h19_5_d1_5_owner_reported_0.2477": (
        paths.DOTTED_0_2477, "68d0e2e4fcc594f9a23f56c44b885fee733d026d39be55e18ad2a07289525310"),
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while c := f.read(1 << 20):
            h.update(c)
    return h.hexdigest()


def load_dots(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        a = s.read(1)
    return np.isfinite(a) & (a > 0)


def within_frac(ours: np.ndarray, ref: np.ndarray, r: float = 3.0) -> float:
    y, x = np.nonzero(ours)
    yb, xb = np.nonzero(ref)
    d, _ = cKDTree(np.c_[yb, xb].astype(float)).query(np.c_[y, x].astype(float), workers=1)
    return float((d <= r).mean())


def main() -> int:
    ours = load_dots(CANDIDATE)
    out = {"candidate": CANDIDATE.name, "candidate_dots": int(ours.sum()),
           "candidate_sha256": sha256_file(CANDIDATE),
           "metric": "fraction of candidate dots within 3 px of the registry raster (protocol limit 0.70)",
           "targets": {}}
    for name, (p, sha) in TARGETS.items():
        ok = p.is_file() and sha256_file(p) == sha
        row = {"path": str(p), "sha256_verified": bool(ok)}
        if ok:
            ref = load_dots(p)
            row["registry_dots"] = int(ref.sum())
            row["frac_our_dots_within3px"] = within_frac(ours, ref)
            row["pass_le_0.70"] = bool(row["frac_our_dots_within3px"] <= 0.70)
        out["targets"][name] = row
    out["all_pass"] = all(r.get("pass_le_0.70") for r in out["targets"].values())
    (ROOT / "evidence/s18_focus_sites_overlap.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0 if out["all_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
