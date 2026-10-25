#!/usr/bin/env python3
"""S18 Experiment 3 (knowledge/52): build the H39-5 candidate GeoTIFF package.

Full-fit 32-band detector -> ridge NMS -> prob-ranked pool -> dot_thin(2.8)
with build-time d_cat > 2 px, budget-searched to within 5% of the champion's
37,654 dots; then the frozen 35% migration-extrapolated swap
(migration.extrap_swap, eligibility vs the full catalogue). Validates both
NaN-outside and all-finite variants with the shared verify_geotiff and checks
final dots vs every registry raster (docs/downloads/*-nan.tif + byte-verified
/tmp/forensic champion/GEMSDOE36 education copies when present).
Writes evidence/s18_candidate_build.json. Does NOT decide the verdict
(finalize_s18 does, from gate + uniqueness + validator).
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
from gems27 import grid, migration, oof_detector, paths, submission, thinning  # noqa: E402

TARGET_N = 37_654
DATE = "20261025"
REGISTRY_EXTRA = {
    "champion_e5eb6e7e_GEMSDOE32": Path("/tmp/forensic/champion_e5eb6e7e_zeros.tif"),
    "gems36_9b9ea4e6_GEMSDOE36": Path("/tmp/forensic/gems36_9b9ea4e6_zeros.tif"),
}
EXTRA_SHA = {
    "champion_e5eb6e7e_GEMSDOE32": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
    "gems36_9b9ea4e6_GEMSDOE36": "e15891020b9c57056ac7fa874a5e506fbd6ed9314a4ea8e73af0753887a3708a",
}


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while c := f.read(1 << 20):
            h.update(c)
    return h.hexdigest()


def within_frac(ours, ref, r=3.0):
    y, x = np.nonzero(ours)
    yb, xb = np.nonzero(ref)
    if len(y) == 0 or len(yb) == 0:
        return 0.0
    d, _ = cKDTree(np.c_[yb, xb].astype(float)).query(np.c_[y, x].astype(float), workers=1)
    return float((d <= r).mean())


def load_dots(p):
    with rasterio.open(p) as s:
        a = s.read(1)
    return np.isfinite(a) & (a > 0)


def main() -> int:
    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS) & foot
    d_cat = distance_transform_edt(~labels)
    z = np.load(paths.DATA / "prepared/extrap_surfaces.npz")
    surface, disp = z["extrap_surface_union"], z["disp_mag_union"]

    print("full-fit detector (32 bands) ...", flush=True)
    prob = oof_detector.fit_predict_full_probabilities(foot, labels)
    print(f"detector done ({time.time()-t0:.0f}s)", flush=True)

    ridge = oof_detector.ridge_nms(prob, foot, sigma=1.0)
    pool_all = ridge & foot & ~labels & (d_cat > 2.0)
    ys, xs = np.nonzero(pool_all)
    order = np.argsort(-prob[ys, xs].astype(np.float64), kind="stable")
    ys, xs = ys[order], xs[order]
    print(f"ridge pool (d_cat>2): {len(ys):,} px", flush=True)

    def emit(k):
        raw = np.zeros(foot.shape, bool)
        raw[ys[:k], xs[:k]] = True
        return thinning.dot_thin(raw, 2.8)

    lo, hi, best = 10_000, len(ys), None
    for it in range(9):
        k = (lo + hi) // 2
        dots_try = emit(k)
        n = int(dots_try.sum())
        print(f"  budget search it={it} k={k:,} -> N={n:,}", flush=True)
        if best is None or abs(n - TARGET_N) < abs(int(best.sum()) - TARGET_N):
            best = dots_try
        if abs(n - TARGET_N) <= 0.01 * TARGET_N:
            break
        if n < TARGET_N:
            lo = k
        else:
            hi = k
    base = best
    elig = (foot & ~labels & (d_cat > 2.0) & (surface > 0)
            & (disp >= migration.EXTRAP_MIN_DISP_PX))
    dots, sinfo = migration.extrap_swap(base, prob, surface, elig)
    n_final = int(dots.sum())
    print(f"swap: {sinfo}", flush=True)
    assert not (dots & labels).any() and float(d_cat[dots].min()) > 2.0

    pred = np.where(dots, 1.0, 0.0).astype(np.float32)
    cid = submission.scored_content_id(pred, foot, labels)
    slug = "h39-5-extrap-swap35"
    nan_name = submission.make_filename("gems28", slug, DATE, cid, "nan")
    af_name = submission.make_filename("gems28", slug, DATE, cid, "allfinite")
    dl = ROOT / "docs/downloads"
    p_nan = submission.write_geotiff(pred, paths.TEMPLATE, dl / nan_name, outside="nan")
    p_af = submission.write_geotiff(pred, paths.TEMPLATE, dl / af_name, outside="zero")
    p_zip = submission.zip_single(p_nan)
    v_nan = submission.verify_geotiff(p_nan, paths.TEMPLATE)
    v_af = submission.verify_geotiff(p_af, paths.TEMPLATE)

    registry = {p.name: p for p in sorted(dl.glob("*-nan.tif")) if p.name != nan_name}
    for k_, v in REGISTRY_EXTRA.items():
        if v.is_file() and sha256_file(v) == EXTRA_SHA[k_]:
            registry[k_] = v
    rng = np.random.default_rng(18)
    foot_idx = np.flatnonzero(foot.ravel())
    sample = np.sort(rng.choice(foot_idx, size=400_000, replace=False))
    spearman_lane_vs_prob = float(spearmanr(
        surface.ravel()[sample].astype(np.float64),
        prob.ravel()[sample].astype(np.float64)).statistic)
    uniq = {}
    for name, p in registry.items():
        ref = load_dots(p)
        uniq[name] = {"frac_our_dots_within3px": within_frac(dots, ref),
                      "registry_dots": int(ref.sum())}
    worst = max(uniq.items(), key=lambda kv: kv[1]["frac_our_dots_within3px"]) if uniq else (None, {})
    canary = json.loads((ROOT / "evidence/s18_canary.json").read_text())
    surf_pass = bool(canary["preplacement_uniqueness"]["surface_spearman_pass_le_0.90"])
    out = {
        "candidate": nan_name, "content_id": cid, "n_dots": n_final, "target_n": TARGET_N,
        "n_base_before_swap": int(base.sum()), "swap": sinfo,
        "files": {"nan": nan_name, "allfinite": af_name, "zip": p_zip.name},
        "sha256": {"nan": sha256_file(p_nan), "allfinite": sha256_file(p_af),
                   "zip": sha256_file(p_zip)},
        "validator_nan": v_nan, "validator_allfinite": v_af,
        "spearman_lane_surface_vs_detector_prob_sample400k": spearman_lane_vs_prob,
        "preplacement_surface_spearman_pass_from_exp1": surf_pass,
        "worst_registry_raster_by_dot_overlap": {"raster": worst[0], **worst[1]} if worst[0] else None,
        "uniqueness_table": uniq,
        "uniqueness_pass_strict": bool(
            surf_pass and worst[1].get("frac_our_dots_within3px", 1) <= 0.70),
        "seconds": round(time.time() - t0, 1),
    }
    outp = ROOT / "evidence/s18_candidate_build.json"
    outp.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"candidate": nan_name, "n_dots": n_final, "swap": sinfo,
                      "spearman_lane_vs_prob": spearman_lane_vs_prob,
                      "worst": out["worst_registry_raster_by_dot_overlap"],
                      "uniqueness_pass_strict": out["uniqueness_pass_strict"],
                      "validator_nan_pass": v_nan["hard_checks_passed"],
                      "validator_allfinite_pass": v_af["hard_checks_passed"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
