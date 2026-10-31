#!/usr/bin/env python3
"""S31 EXP-3: independent gate over the written candidate bytes (no builder bookkeeping reused).

Re-reads docs/candidates/<S31 file>.tif and checks, independently of the builder:
  validator   CRS/shape/transform match the competition grid; single band; float32; zeros outside
              the footprint; every in-footprint value finite and in [0, 1]; no NaN inside footprint.
  uniqueness  exact KD-tree (nearest registry dot) overlap for every registry raster and every
              in-repo candidate raster; DUPLICATE if any overlap > 0.70.
  lane        rank correlation of the final dot mask's gaussian density vs every comparable raster's
              density; flag any |rho| > 0.90 (binary-vs-binary Spearman is structurally tied and is
              reported as not applicable, matching S30).
  projection  PRIMARY calibration projection (labelled PROJECTION; never a score).
Prints a JSON verdict and writes evidence/s31_gate.json.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import gaussian_filter
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, submission  # noqa: E402
from gems27 import uniqueness as U  # noqa: E402

REGISTRY = ROOT / "data/registry_tifs/manifest.json"
DUPLICATE_OVERLAP = 0.70
RANK_CORR_FAIL = 0.90


def main() -> int:
    build = json.loads((ROOT / "evidence" / "s31_build.json").read_text())
    cand_path = ROOT / build["path"]
    template = ROOT / "data/sample_submission.tif"

    validator = submission.verify_geotiff(cand_path, template)
    foot = grid.load_footprint(template)
    with rasterio.open(cand_path) as s:
        arr = s.read(1).astype(np.float64)
    cand = U.dot_mask(arr, foot)
    n_final = int(cand.sum())

    items = json.loads(REGISTRY.read_text())["files"]
    cand_paths = sorted((ROOT / "docs" / "candidates").glob("*.tif"))
    cand_paths = [p for p in cand_paths if p.resolve() != cand_path.resolve()]

    overlaps, densities = {}, []
    yy, xx = np.nonzero(cand)
    cand_tree = cKDTree(np.column_stack([yy, xx]).astype(np.float64))
    cand_density = gaussian_filter(cand.astype(np.float64), 10.0)

    worst_name, worst = None, -1.0
    over70 = 0
    rho_failures = []
    rho_max = 0.0
    paths = [ROOT / it["local"] for it in items] + cand_paths
    for p in paths:
        with rasterio.open(p) as s:
            if s.shape != foot.shape:
                continue
            v = s.read(1).astype(np.float64)
        ref = U.registry_dot_mask(v, foot)
        if not ref.any():
            continue
        d = U.distance_to_dots(ref)
        ov = float(np.mean(d[cand] <= U.OVERLAP_RADIUS_PX))
        overlaps[str(p.relative_to(ROOT))] = ov
        if ov > worst:
            worst_name, worst = str(p.relative_to(ROOT)), ov
        if ov > DUPLICATE_OVERLAP:
            over70 += 1
        ref_density = gaussian_filter(ref.astype(np.float64), 10.0)
        rho = float(spearmanr(cand_density[foot], ref_density[foot]).statistic)
        rho_max = max(rho_max, abs(rho))
        if abs(rho) > RANK_CORR_FAIL:
            rho_failures.append(str(p.relative_to(ROOT)))

    sha = hashlib.sha256(cand_path.read_bytes()).hexdigest()
    cal = json.loads((ROOT / "evidence" / "s31_calibration.json").read_text())
    prim = cal["primary"]

    hard_ok = bool(validator["hard_checks_passed"])
    unique_ok = over70 == 0
    lane_ok = not rho_failures
    if prim["usable"]:
        frac_mid36 = build["frac_mid36_final"]
        mu = prim["coefficients"]["intercept"] + prim["coefficients"]["frac_mid36"] * frac_mid36
        rng = np.random.default_rng(31)
        npz = np.load(ROOT / "evidence" / "s31_calibration.npz")
        samples = mu + rng.choice(npz["resid_primary"], size=(2000,), replace=True)
        fam_vals = [r["frac_mid36"] for r in cal["family_rows"]]
        in_range = bool(min(fam_vals) <= frac_mid36 <= max(fam_vals))
        projection = {"estimable": in_range,
                      "projected_mean_unextrapolated": float(mu),
                      "ci95_unextrapolated": [float(np.percentile(samples, 2.5)),
                                              float(np.percentile(samples, 97.5))],
                      "in_calibration_range": in_range,
                      "verdict": ("PROJECTION valid" if in_range else
                                  "NOT ESTIMABLE: outside calibration support; direction only")}
    else:
        projection = {"estimable": False}

    verdict = {
        "schema": 1, "session": "S31", "experiment": "EXP-3 gate",
        "file": cand_path.name, "path": str(cand_path.relative_to(ROOT)),
        "sha256": sha, "sha_matches_builder": sha == build["sha256"],
        "n_final_dots": n_final, "n_dots_match_builder": n_final == build["n_final"],
        "validator_hard_checks_passed": hard_ok, "validator_failures": validator["hard_failures"],
        "no_nan_inside_footprint": bool(np.isfinite(arr[foot]).all()),
        "values_in_01": bool((arr[foot] >= 0).all() and (arr[foot] <= 1).all()),
        "max_overlap": worst, "max_overlap_raster": worst_name,
        "rasters_over_70pct": over70, "unique_under_70pct_3px": unique_ok,
        "density_rank_corr_max_abs": rho_max, "density_rank_corr_failures": rho_failures,
        "binary_spearman": "not applicable (tied ranks, as in S30)",
        "lane_ok": lane_ok,
        "projection": projection,
        "projection_label": "PROJECTION calibrated on 13 OWNER-REPORTED family scores; NOT a score",
        "verdict": {
            "format_valid": hard_ok,
            "unique": unique_ok,
            "lane_ok": lane_ok,
            "ok_to_download": bool(hard_ok and unique_ok and lane_ok),
            "score": "NOT ESTABLISHED: no organizer receipt; projection is not a score",
        },
    }
    (ROOT / "evidence" / "s31_gate.json").write_text(json.dumps(verdict, indent=1) + "\n")
    print(json.dumps(verdict, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
