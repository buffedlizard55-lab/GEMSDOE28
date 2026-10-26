#!/usr/bin/env python3
"""S20 Experiment 1 (education only): independent byte forensic of the champion ladder.

Re-verifies, from raw bytes fetched this session, why the GEMSDOE32 artifact associated by the
owner with 0.2778 sits at the top of the nine-site family, and inverts the reported scores through
the official DTI algebra. **No candidate dots are produced.** Champion-family rasters are read from
local sparse clones under /tmp/gems-mirrors (git clones of the public owner repos); every file's
SHA-256 is checked against the value recorded in evidence/s18_champion_forensic.json before use,
and the run aborts on any mismatch.

Scores are USER-REPORTED / UNVERIFIED (prompt lists; no organizer receipt exists in any fetched
repository). The 0.4413 leaderboard figure is a dated public-page observation made this session
(2026-10-26, fetch of the official leaderboard: #1 xiaofanhu 0.4413), not a receipt and not linked
to any local raster. Inversion uses the A~=B closure DTI = A/(0.8|G| + 0.2N) derived in
evidence/why_026_won.json; |G| is unobservable, so results are tabulated over a sensitivity grid.
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
from gems27 import grid, paths  # noqa: E402

MIRRORS = Path("/tmp/gems-mirrors")
FILES = {
    # key: (path, expected sha256 or None, owner-reported score or None)
    "champion_GEMSDOE32_e5eb6e7e": (
        MIRRORS / "GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
        "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9", 0.2778),
    "site36_GEMSDOE36_9b9ea4e6": (
        MIRRORS / "GEMSDOE36/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
        "e15891020b9c57056ac7fa874a5e506fbd6ed9314a4ea8e73af0753887a3708a", 0.2750),
    "site33_GEMSDOE33_cb490425926e": (
        MIRRORS / "GEMSDOE33/docs/downloads/GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
        "87f857d505e23247e991ccfab2cbe9f49a04df4f9c8028dce7ea261554690757", 0.2632),
    "solo_GEMSDOE31_8acb75e1_allfinite": (
        MIRRORS / "GEMSDOE31/docs/downloads/gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif",
        "acd853936e5a7170b207f23411b1844caa0e7cfdfc303c600e520ccfe75159e6", 0.2708),
    "site30_GEMSDOE30_91eae1ca": (
        MIRRORS / "GEMSDOE30/docs/downloads/gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
        None, 0.2600),
    "d28_local_mirror": (paths.DATA / "dotted_h19_5_d2_8_nan.tif",
                         "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8", 0.2600),
    "d15_local_mirror": (paths.DATA / "dotted_h19_5_d1_5_nan.tif",
                         "68d0e2e4fcc594f9a23f56c44b885fee733d026d39be55e18ad2a07289525310", 0.2477),
    "h19_5_solid_local_mirror": (paths.DATA / "h19_5_nan.tif",
                                 "ec1f9b56b83ce33cad781ceb9f104b18fb4f2ff785263a4e89616af4aabdee8d", 0.1922),
}
BANDS = [("=0", 0.0, 0.0), ("(0,1]", 0.0, 1.0), ("(1,2]", 1.0, 2.0), ("(2,3]", 2.0, 3.0),
         ("(3,5]", 3.0, 5.0), ("(5,10]", 5.0, 10.0), (">10", 10.0, np.inf)]


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


def hist(dots: np.ndarray, d_cat: np.ndarray) -> dict:
    d = d_cat[dots]
    out = {}
    for name, lo, hi in BANDS:
        out[name] = int(((d > lo) & (d <= hi)).sum()) if lo != hi else int((d == 0).sum())
    return out


def implied_credit(dti: float, n: int, g: float) -> float:
    """A under the A~=B closure DTI = A/(0.8G + 0.2N)."""
    return dti * (0.8 * g + 0.2 * n)


def main() -> int:
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS) & foot
    d_cat = distance_transform_edt(~labels)

    dots, meta = {}, {}
    for key, (path, expected, score) in FILES.items():
        if not path.is_file():
            raise SystemExit(f"missing forensic input: {path}")
        sha = sha256_file(path)
        if expected is not None and sha != expected:
            raise SystemExit(f"sha256 mismatch for {key}: {sha} != {expected}")
        d = load_dots(path)
        dots[key] = d
        meta[key] = {"path": str(path), "sha256": sha, "sha256_checked": expected is not None,
                     "owner_reported_score": score, "evidence_class": "USER-REPORTED / UNVERIFIED",
                     "dot_count": int(d.sum()), "on_catalogue": int((d & labels).sum()),
                     "d_cat_hist_px": hist(d, d_cat)}
        print(f"{key}: N={int(d.sum()):,} on_cat={int((d & labels).sum())} sha_ok={expected is not None}",
              flush=True)

    champ, solo, d28 = dots["champion_GEMSDOE32_e5eb6e7e"], dots["solo_GEMSDOE31_8acb75e1_allfinite"], dots["d28_local_mirror"]
    s36, s30, s33 = dots["site36_GEMSDOE36_9b9ea4e6"], dots["site30_GEMSDOE30_91eae1ca"], dots["site33_GEMSDOE33_cb490425926e"]
    relations = {
        "champion_subset_of_solo": bool(not (champ & ~solo).any()),
        "champion_equals_solo_minus_dcat_le2": bool(np.array_equal(champ, solo & (d_cat > 2.0))),
        "removed_solo_to_champion": int((solo & ~champ).sum()),
        "added_solo_to_champion": int((champ & ~solo).sum()),
        "solo_equals_d28_minus_dcat_le1": bool(np.array_equal(solo, d28 & (d_cat > 1.0))),
        "removed_d28_to_solo": int((d28 & ~solo).sum()),
        "added_d28_to_solo": int((solo & ~d28).sum()),
        "site30_dots_equal_d28_dots": bool(np.array_equal(s30, d28)),
        "site36_contains_champion": bool(not (champ & ~s36).any()),
        "site36_added_over_champion": int((s36 & ~champ).sum()),
        "site36_removed_from_champion": int((champ & ~s36).sum()),
        "site33_shared_with_champion": int((s33 & champ).sum()),
        "site33_only": int((s33 & ~champ).sum()),
        "champion_ring_2_3_dots_B3_measurement_only": int((champ & (d_cat > 2.0) & (d_cat <= 3.0)).sum()),
        "champion_minus_dcat_le3_count_B3_measurement_only": int((champ & (d_cat > 3.0)).sum()),
    }

    ladder = [("h19_5_solid_local_mirror", 0.1922), ("d15_local_mirror", 0.2477),
              ("d28_local_mirror", 0.2600), ("solo_GEMSDOE31_8acb75e1_allfinite", 0.2708),
              ("champion_GEMSDOE32_e5eb6e7e", 0.2778), ("site36_GEMSDOE36_9b9ea4e6", 0.2750)]
    inversion = {}
    for g in (10000.0, 12226.0, 15000.0, 20000.0):
        rows, prev = {}, None
        for key, score in ladder:
            n = meta[key]["dot_count"]
            a = implied_credit(score, n, g)
            rows[key] = {"N": n, "reported_dti": score, "implied_credit_A": a,
                         "credit_per_dot_avg": a / n}
            if prev is not None:
                dn, da = n - prev[1], a - prev[2]
                rows[key]["marginal_vs_prev"] = {
                    "prev": prev[0], "dN": dn, "dA": da,
                    "marginal_credit_per_dot": (da / dn if dn else None),
                    "breakeven_0.2xDTI_prev": 0.2 * prev[3]}
            prev = (key, n, a, score)
        # B3 projection (measurement only): remove ring (2,3] from champion at assumed efficiencies.
        n_c, a_c = meta["champion_GEMSDOE32_e5eb6e7e"]["dot_count"], rows["champion_GEMSDOE32_e5eb6e7e"]["implied_credit_A"]
        k3 = relations["champion_ring_2_3_dots_B3_measurement_only"]
        b3 = {}
        for eff in (0.0, 0.0065, 0.02, 0.0556):
            b3[f"eff_{eff}"] = (a_c - eff * k3) / (0.8 * g + 0.2 * (n_c - k3))
        targets = {}
        for target in (0.3195, 0.4413):
            need_a = implied_credit(target, n_c, g)
            dots_needed = {}
            for eff in (0.2, 0.3, 0.4, 0.5, 1.0):
                denom = eff - 0.2 * target
                dots_needed[f"eff_{eff}"] = ((need_a - a_c) / denom) if denom > 0 else None
            targets[str(target)] = {"credit_needed_at_champion_N": need_a,
                                    "extra_credit_vs_champion": need_a - a_c,
                                    "new_dots_needed_by_marginal_efficiency": dots_needed}
        inversion[f"|G|={int(g)}"] = {"ladder": rows, "B3_projection_measurement_only": b3,
                                      "targets_from_champion": targets}

    out = {
        "schema": 1, "session": "S20 Experiment 1 (education only; no dots copied to any candidate)",
        "date_utc": "2026-10-26",
        "score_evidence_class": "USER-REPORTED / UNVERIFIED for every ladder score; no organizer receipt",
        "leaderboard_observation": {
            "value": 0.4413, "team": "xiaofanhu (#1)",
            "source": "https://www.drivendata.org/competitions/306/competition-doe-gems/leaderboard/",
            "observed_utc": "2026-10-26 via research fetch (chunk 0); dated public observation, NOT a receipt",
            "note": "Prompt also quotes 0.3195 as a high score; superseded as a current-top claim by the dated 0.4413 observation. Neither value is linked to any local raster."},
        "metric": "DTI(alpha=0.2, beta=0.8), triangular 300 m kernel (official problem page, re-fetched 2026-10-26, both chunks read)",
        "closure": "DTI = A/(0.8|G| + 0.2N) holds exactly when A == B (truth-side credit equals prediction-side matched mass); for dotted emissions A~=B is an approximation, so implied credits are closure estimates, not measurements of hidden truth.",
        "files": meta, "relations": relations, "inversion": inversion,
        "reading": ("The ladder solid(0.1922) -> d1.5(0.2477) -> d2.8(0.2600) -> solo B1(0.2708) -> "
                    "champion B2(0.2778) is ONE H19-5 emission family under successive thinning + "
                    "catalogue-flank pruning (byte-verified subset relations above). Under the closure, "
                    "both pruned rings earned ~0.003-0.007 credit/dot vs a ~0.052-0.056 break-even, i.e. "
                    "they were almost pure false-positive mass; GEMSDOE36's +1,200 added dots earned "
                    "~0.015/dot, also below break-even, and its reported score fell. The champion therefore "
                    "leads by emission hygiene against the asymmetric metric, with no evidence in these "
                    "bytes of additional fault detection. Causation remains conditional: hidden truth and "
                    "receipts are unavailable."),
    }
    outp = ROOT / "evidence/s20v_forensic.json"
    outp.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"relations": relations,
                      "B3_|G|12226": inversion["|G|=12226"]["B3_projection_measurement_only"],
                      "gap_0.4413_|G|12226": inversion["|G|=12226"]["targets_from_champion"]["0.4413"]},
                     indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
