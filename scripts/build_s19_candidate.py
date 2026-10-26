#!/usr/bin/env python3
"""S19 Experiment 3 (knowledge/57): build the RADLIN candidate GeoTIFF package.

Runs only if Experiment 1 passed (a duplicate/canary stop means no TIFF).
The LOSFO verdict does not change the build; it changes the label the
finalizer may put on the download. Full-fit shared detector, RADLIN-weighted
all-ridge coverage packing to 37,654 dots at >2 px from the full catalogue,
written through the shared submission writer and independently re-validated.
Final dots are compared with every registry raster from Experiment 1's
declared scope. No previous submission's pixels are read into placement.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree
from scipy.stats import spearmanr

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, oof_detector, packing, paths, submission  # noqa: E402

TARGET_N = 37_654
DATE = "20261026"


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
    if len(y) == 0 or len(yb) == 0:
        return 0.0
    d, _ = cKDTree(np.c_[yb, xb].astype(float)).query(np.c_[y, x].astype(float), workers=1)
    return float((d <= r).mean())


def main() -> int:
    t0 = time.time()
    stage = json.loads((ROOT / "evidence/s19b_radlin_surface.json").read_text())
    if not stage["passed"]:
        raise SystemExit("Experiment 1 did not pass; preregistration says STOP, no TIFF.")
    surf_path = paths.DATA / "prepared" / "s19_radlin_surface.npz"
    if submission.sha256_file(surf_path) != stage["surface_npz_sha256"]:
        raise ValueError("RADLIN surface changed since Experiment 1")
    bonus = np.load(surf_path)["bonus"]

    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS) & foot
    d_cat = distance_transform_edt(~labels)

    print("full-fit detector (32 bands) ...", flush=True)
    prob = oof_detector.fit_predict_full_probabilities(foot, labels)
    print(f"detector done ({time.time()-t0:.0f}s)", flush=True)
    ridge = oof_detector.ridge_nms(prob, foot, sigma=1.0)
    eligible = ridge & foot & ~labels & (d_cat > 2.0)
    weight = (prob * (1.0 + 0.5 * bonus)).astype(np.float32)
    print(f"ridge eligible (d_cat>2): {int(eligible.sum()):,} px; packing to {TARGET_N:,} ...", flush=True)
    dots = packing.coverage_greedy(eligible, weight, TARGET_N) & foot & ~labels
    n_final = int(dots.sum())
    print(f"packed {n_final:,} dots ({time.time()-t0:.0f}s)", flush=True)
    assert not (dots & labels).any() and float(d_cat[dots].min()) > 2.0

    pred = np.where(dots, 1.0, 0.0).astype(np.float32)
    cid = submission.scored_content_id(pred, foot, labels)
    slug = "s19-radlin-cover"
    nan_name = submission.make_filename("gems28", slug, DATE, cid, "nan")
    af_name = submission.make_filename("gems28", slug, DATE, cid, "allfinite")
    dl = ROOT / "docs/downloads"
    p_nan = submission.write_geotiff(pred, paths.TEMPLATE, dl / nan_name, outside="nan")
    p_af = submission.write_geotiff(pred, paths.TEMPLATE, dl / af_name, outside="zero")
    p_zip = submission.zip_single(p_nan)
    v_nan = submission.verify_geotiff(p_nan, paths.TEMPLATE)
    v_af = submission.verify_geotiff(p_af, paths.TEMPLATE)

    # Final-dot uniqueness over the same declared registry scope as Experiment 1.
    reg: dict[str, Path] = {p.name: p for p in sorted(dl.glob("*-nan.tif")) if p.name != nan_name}
    forensic = json.loads((ROOT / "evidence/s18_champion_forensic.json").read_text())
    for site in forensic["sites"]:
        cand = Path("/tmp/forensic") / (site["site"] + "-" + Path(site["artifact"]).name)
        if cand.is_file() and sha256_file(cand) == site["sha256"]:
            reg[f"forensic_{site['site']}"] = cand
    foot_idx = np.flatnonzero(foot.ravel())
    sample = np.sort(np.random.default_rng(19).choice(foot_idx, size=400_000, replace=False))
    uniq = {}
    for name, p in reg.items():
        ref = load_dots(p)
        uniq[name] = {"frac_our_dots_within3px": within_frac(dots, ref),
                      "spearman_binary_sample400k": float(spearmanr(
                          dots.ravel()[sample].astype(np.float64),
                          ref.ravel()[sample].astype(np.float64)).statistic),
                      "registry_dots": int(ref.sum()), "sha256": sha256_file(p)}
    worst_ov = max(uniq.items(), key=lambda kv: kv[1]["frac_our_dots_within3px"])
    worst_rho = max(uniq.items(), key=lambda kv: abs(kv[1]["spearman_binary_sample400k"]))
    uniq_pass = worst_ov[1]["frac_our_dots_within3px"] <= 0.70 and abs(worst_rho[1]["spearman_binary_sample400k"]) <= 0.90
    out = {
        "session": "S19B-RADLIN", "experiment": 3, "candidate": nan_name, "content_id": cid,
        "n_dots": n_final, "target_n": TARGET_N,
        "files": {"nan": nan_name, "allfinite": af_name, "zip": p_zip.name},
        "sha256": {"nan": sha256_file(p_nan), "allfinite": sha256_file(p_af), "zip": sha256_file(p_zip)},
        "validator_nan": v_nan, "validator_allfinite": v_af,
        "validator_pass": bool(v_nan["hard_checks_passed"] and v_af["hard_checks_passed"]),
        "surface_npz_sha256": stage["surface_npz_sha256"],
        "uniqueness": {"scope": stage["registry_scope"], "table": uniq,
                       "worst_by_overlap": {"raster": worst_ov[0], **worst_ov[1]},
                       "worst_by_spearman": {"raster": worst_rho[0], **worst_rho[1]},
                       "pass_strict": bool(uniq_pass)},
        "seconds": round(time.time() - t0, 1),
    }
    (ROOT / "evidence/s19b_radlin_candidate_build.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"candidate": nan_name, "content_id": cid, "n_dots": n_final,
                      "validator_pass": out["validator_pass"],
                      "worst_overlap": out["uniqueness"]["worst_by_overlap"],
                      "worst_spearman": out["uniqueness"]["worst_by_spearman"],
                      "uniqueness_pass": uniq_pass}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
