#!/usr/bin/env python3
"""S15 forensic (EDUCATION ONLY): what exactly is the owner-reported 0.2778 champion?

Fetches nothing; reads byte-verified local rasters:
  champion  /tmp/forensic/champion_e5eb6e7e_zeros.tif  (GEMSDOE32 e5eb6e7e zeros,
            sha256 must equal its audit.json c55bafc4...; owner-reported live 0.2778)
  gems36    /tmp/forensic/gems36_9b9ea4e6_zeros.tif     (GEMSDOE36, owner-reported 0.2750)
  local     docs/downloads/*-nan.tif + data/dotted_h19_5_d2_8_nan.tif (owner-reported 0.2600)

Score labels: every live number here is OWNER-REPORTED (task statement lists). No repository
fetched this session contains an organizer submission-page receipt for these files, so none is
labelled ORGANIZER-CONFIRMED. Output: evidence/s15_champion_forensic.json.
Nothing measured here is copied into any shipped raster; it sizes the flank-prune effect and
defines the uniqueness bar (protocol: >70% of dots within 3 px of one registry raster = duplicate).
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
from gems27 import grid, paths  # noqa: E402

CHAMP = Path("/tmp/forensic/champion_e5eb6e7e_zeros.tif")
CHAMP_SHA = "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9"
G36 = Path("/tmp/forensic/gems36_9b9ea4e6_zeros.tif")
G36_SHA = "e15891020b9c57056ac7fa874a5e506fbd6ed9314a4ea8e73af0753887a3708a"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    h.update(p.read_bytes())
    return h.hexdigest()


def load_dots(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        assert s.count == 1 and s.shape == grid.SHAPE and s.crs.to_epsg() == grid.CRS_EPSG, p
        a = s.read(1)
    return np.isfinite(a) & (a > 0)


def within_frac(a: np.ndarray, b: np.ndarray, r: float = 3.0) -> float:
    """Fraction of dots of `a` within r px of any dot of `b` (protocol uniqueness metric)."""
    ya, xa = np.nonzero(a)
    yb, xb = np.nonzero(b)
    if len(ya) == 0 or len(yb) == 0:
        return 0.0
    d, _ = cKDTree(np.c_[yb, xb].astype(float)).query(np.c_[ya, xa].astype(float), workers=1)
    return float((d <= r).mean())


def dcat_hist(dots: np.ndarray, d_cat: np.ndarray) -> dict:
    v = d_cat[dots]
    bins = {"=0": 0.0, "(0,1]": 1.0, "(1,2]": 2.0, "(2,3]": 3.0, "(3,5]": 5.0, "(5,10]": 10.0}
    out, lo = {}, -1e-9
    for name, hi in bins.items():
        out[name] = int(((v > lo) & (v <= hi)).sum())
        lo = hi
    out[">10"] = int((v > 10.0).sum())
    return out


def main() -> int:
    assert sha256_file(CHAMP) == CHAMP_SHA, "champion bytes differ from GEMSDOE32 audit.json"
    assert sha256_file(G36) == G36_SHA, "gems36 bytes differ from GEMSDOE36 audit.json"
    foot = grid.load_footprint(paths.TEMPLATE)
    with rasterio.open(paths.LABELS) as s:
        labels = s.read(1) > 0
    labels &= foot
    d_cat = distance_transform_edt(~labels)

    files = {
        "champion_e5eb6e7e_GEMSDOE32_owner_reported_0.2778": CHAMP,
        "gems36_9b9ea4e6_GEMSDOE36_owner_reported_0.2750": G36,
        "d2_8_e56ea318af89_owner_reported_0.2600": paths.DOTTED_D2_8,
        "solo_r1_8acb75e1f2cc_owner_reported_0.2708":
            ROOT / "docs/downloads/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif",
        "h36_1_b531dae0a36f_unscored":
            ROOT / "docs/downloads/gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif",
        "h38_1_56a9f473edc7_unscored":
            ROOT / "docs/downloads/gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif",
        "h37_1_0bbddf41eb6d_unscored":
            ROOT / "docs/downloads/gems28-h37-1-coverprob-h19-5-r1-20261003-0bbddf41eb6d-nan.tif",
    }
    dots = {k: load_dots(p) for k, p in files.items()}
    champ = dots["champion_e5eb6e7e_GEMSDOE32_owner_reported_0.2778"]
    solo = dots["solo_r1_8acb75e1f2cc_owner_reported_0.2708"]
    d28 = dots["d2_8_e56ea318af89_owner_reported_0.2600"]

    # Verify GEMSDOE32's own construction claim exactly: champion == solo minus d_cat<=2 ?
    claim_rebuild = solo & (d_cat > 2.0)
    # d_cat is Euclidean EDT; GEMSDOE32 wording: "every dot at d(catalogue) <= 2 px deleted".
    out = {
        "purpose": "S15 champion forensic, education only; no dots copied to any shipped raster",
        "score_label": "OWNER-REPORTED (task-statement lists); no organizer receipt found in "
                       "GEMSDOE32/36 bytes fetched 2026-10-25, so NOT ORGANIZER-CONFIRMED",
        "champion_sha256_verified_vs_audit": True,
        "counts": {k: int(v.sum()) for k, v in dots.items()},
        "on_catalogue_dots": {k: int((v & labels).sum()) for k, v in dots.items()},
        "d_cat_hist_px": {k: dcat_hist(v, d_cat) for k, v in dots.items()},
        "champion_subset_of_solo": bool((champ & ~solo).sum() == 0),
        "champion_equals_solo_minus_dcat_le2_exact": bool((claim_rebuild == champ).all()),
        "symdiff_champion_vs_solo_minus_dcat_le2": int((claim_rebuild ^ champ).sum()),
        "removed_solo_to_champion": int((solo & ~champ).sum()),
        "added_solo_to_champion": int((champ & ~solo).sum()),
        "removed_d28_to_solo": int((d28 & ~solo).sum()),
        "added_d28_to_solo": int((solo & ~d28).sum()),
        "frac_of_each_within3px_of_champion": {
            k: within_frac(v, champ) for k, v in dots.items()},
        "frac_of_champion_within3px_of_each": {
            k: within_frac(champ, v) for k, v in dots.items()},
        "owner_reported_live_ladder": {
            "d2_8_N44090": 0.2600, "solo_r1": 0.2708, "champion_B2": 0.2778,
            "gems36_champion_plus_conduits": 0.2750,
            "delta_per_removed_dot_ring1": (0.2708 - 0.2600) / max(1, int((d28 & ~solo).sum())),
            "delta_per_removed_dot_ring2": (0.2778 - 0.2708) / max(1, int((solo & ~champ).sum())),
        },
        "ring3_candidate_dots_in_champion_dcat_(2,3]": int((champ & (d_cat > 2.0) & (d_cat <= 3.0)).sum()),
        "gems36_vs_champion": {
            "added": int((dots["gems36_9b9ea4e6_GEMSDOE36_owner_reported_0.2750"] & ~champ).sum()),
            "removed": int((champ & ~dots["gems36_9b9ea4e6_GEMSDOE36_owner_reported_0.2750"]).sum()),
        },
    }
    outp = ROOT / "evidence/s15_champion_forensic.json"
    outp.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
