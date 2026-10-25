#!/usr/bin/env python3
"""S16 Experiment 3 (knowledge/49): build the H40-1 candidate GeoTIFF package.

Full-fit D1 detector (32 frozen bands + 4 migration bands) -> ridge NMS ->
prob-ranked top-budget pool -> dot_thin(2.8), build-time d_cat > 2 px exclusion
(the champion's disclosed hygiene; never applied inside the LOSFO gate).
Budget binary-searched to within 5% of the champion's 37,654 dots.
Also fits full-fit D0 for the surface Spearman uniqueness check, and checks
final dots vs every registry raster (docs/downloads/*-nan.tif + /tmp/forensic
champion/GEMSDOE36 education copies). Writes evidence/s16_candidate_build.json.
Does NOT decide the verdict (finalize script does, from gate + uniqueness).
"""
from __future__ import annotations

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
from gems27 import grid, oof_detector, paths, submission, thinning  # noqa: E402

TARGET_N = 37_654
DATE = "20261025"
REGISTRY_EXTRA = {
    "champion_e5eb6e7e_GEMSDOE32": Path("/tmp/forensic/champion_e5eb6e7e_zeros.tif"),
    "gems36_9b9ea4e6_GEMSDOE36": Path("/tmp/forensic/gems36_9b9ea4e6_zeros.tif"),
}


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
    extra = np.load(paths.DATA / "prepared/migration_extra.npy", mmap_mode="r")

    print("full-fit D1 (32+4 bands) ...", flush=True)
    prob_d1 = oof_detector.fit_predict_full_probabilities(foot, labels, extra=extra)
    print(f"D1 done ({time.time()-t0:.0f}s); full-fit D0 ...", flush=True)
    prob_d0 = oof_detector.fit_predict_full_probabilities(foot, labels)
    print(f"D0 done ({time.time()-t0:.0f}s)", flush=True)

    ridge = oof_detector.ridge_nms(prob_d1, foot, sigma=1.0)
    pool_all = ridge & foot & ~labels & (d_cat > 2.0)
    ys, xs = np.nonzero(pool_all)
    svals = prob_d1[ys, xs]
    order = np.argsort(-svals, kind="stable")
    ys, xs = ys[order], xs[order]
    print(f"ridge pool (d_cat>2): {len(ys):,} px", flush=True)

    def emit(k):
        raw = np.zeros(foot.shape, bool)
        raw[ys[:k], xs[:k]] = True
        return thinning.dot_thin(raw, 2.8)

    lo, hi, best = 10_000, len(ys), None
    for it in range(9):
        k = (lo + hi) // 2
        dots = emit(k)
        n = int(dots.sum())
        print(f"  budget search it={it} k={k:,} -> N={n:,}", flush=True)
        if best is None or abs(n - TARGET_N) < abs(int(best.sum()) - TARGET_N):
            best = dots
        if abs(n - TARGET_N) <= 0.01 * TARGET_N:
            break
        if n < TARGET_N:
            lo = k
        else:
            hi = k
    dots = best
    n_final = int(dots.sum())
    assert not (dots & labels).any() and float(d_cat[dots].min()) > 2.0

    pred = np.where(dots, 1.0, 0.0).astype(np.float32)
    cid = submission.scored_content_id(pred, foot, labels)
    slug = "h40-1-migration-b1"
    nan_name = submission.make_filename("gems28", slug, DATE, cid, "nan")
    af_name = submission.make_filename("gems28", slug, DATE, cid, "allfinite")
    dl = ROOT / "docs/downloads"
    p_nan = submission.write_geotiff(pred, paths.TEMPLATE, dl / nan_name, outside="nan")
    p_af = submission.write_geotiff(pred, paths.TEMPLATE, dl / af_name, outside="zero")
    p_zip = submission.zip_single(p_nan)
    v_nan = submission.verify_geotiff(p_nan, paths.TEMPLATE)
    v_af = submission.verify_geotiff(p_af, paths.TEMPLATE)

    registry = {p.name: p for p in sorted(dl.glob("*-nan.tif")) if p.name != nan_name}
    registry.update({k: v for k, v in REGISTRY_EXTRA.items() if v.is_file()})
    rng = np.random.default_rng(16)
    foot_idx = np.flatnonzero(foot.ravel())
    sample = np.sort(rng.choice(foot_idx, size=400_000, replace=False))
    spearman_surface = float(spearmanr(prob_d1.ravel()[sample].astype(np.float64),
                                       prob_d0.ravel()[sample].astype(np.float64)).statistic)
    uniq = {}
    for name, p in registry.items():
        ref = load_dots(p)
        uniq[name] = {"frac_our_dots_within3px": within_frac(dots, ref), "registry_dots": int(ref.sum())}
    worst = max(uniq.items(), key=lambda kv: kv[1]["frac_our_dots_within3px"]) if uniq else (None, {})
    out = {
        "candidate": nan_name, "content_id": cid, "n_dots": n_final, "target_n": TARGET_N,
        "files": {"nan": nan_name, "allfinite": af_name, "zip": p_zip.name},
        "validator_nan": v_nan, "validator_allfinite": v_af,
        "spearman_probD1_vs_probD0_sample400k": spearman_surface,
        "worst_registry_raster_by_dot_overlap": {"raster": worst[0], **worst[1]} if worst[0] else None,
        "uniqueness_table": uniq,
        "uniqueness_pass_strict": bool(spearman_surface <= 0.90 and worst[1].get("frac_our_dots_within3px", 1) <= 0.70),
        "seconds": round(time.time() - t0, 1),
    }
    outp = ROOT / "evidence/s16_candidate_build.json"
    outp.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"candidate": nan_name, "n_dots": n_final, "spearman_surface": spearman_surface,
                      "worst": out["worst_registry_raster_by_dot_overlap"],
                      "uniqueness_pass_strict": out["uniqueness_pass_strict"],
                      "validator_nan_pass": v_nan["hard_checks_passed"],
                      "validator_allfinite_pass": v_af["hard_checks_passed"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
