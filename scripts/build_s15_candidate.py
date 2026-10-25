#!/usr/bin/env python3
"""S15 Experiment 3 (knowledge/47 §6): build the H39-1 candidate GeoTIFF package.

Full-fit D1 detector (32 frozen bands + 5 depth-slice bands) -> ridge NMS ->
persistence-weighted top-budget pool -> dot_thin(2.8), with the disclosed build-time
catalogue-flank exclusion d_cat > 2 px (the champion's hygiene, §1 of knowledge/47; never
applied inside the LOSFO gate). Budget is binary-searched so the final count lands within
5% of the champion's 37,654 dots. Also fits full-fit D0 for the surface-correlation
uniqueness check. Writes nan + allfinite(zeros) + single-member zip via
src/gems27/submission.py and evidence/s15_candidate_build.json. Does NOT edit the downloads
manifest and does NOT decide the verdict (scripts/finalize_s15.py does, from the gate +
uniqueness + validator outputs).
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
from gems27 import grid, oof_detector, paths, submission, thinning  # noqa: E402

TARGET_N = 37_654
DATE = "20261025"
REGISTRY_EXTRA = {
    "champion_e5eb6e7e_GEMSDOE32": Path("/tmp/forensic/champion_e5eb6e7e_zeros.tif"),
    "gems36_9b9ea4e6_GEMSDOE36": Path("/tmp/forensic/gems36_9b9ea4e6_zeros.tif"),
}


def within_frac(ours: np.ndarray, ref: np.ndarray, r: float = 3.0) -> float:
    y, x = np.nonzero(ours)
    yb, xb = np.nonzero(ref)
    if len(y) == 0 or len(yb) == 0:
        return 0.0
    d, _ = cKDTree(np.c_[yb, xb].astype(float)).query(np.c_[y, x].astype(float), workers=1)
    return float((d <= r).mean())


def load_dots(p: Path) -> np.ndarray:
    with rasterio.open(p) as s:
        a = s.read(1)
    return np.isfinite(a) & (a > 0)


def main() -> int:
    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS) & foot
    d_cat = distance_transform_edt(~labels)
    extra = np.load(paths.DATA / "prepared/depthslice_extra.npy", mmap_mode="r")
    persist_rank = np.load(paths.DATA / "prepared/depthslice_persist_rank01.npy")

    print("full-fit D1 (32+5 bands) ...", flush=True)
    prob_d1 = oof_detector.fit_predict_full_probabilities(foot, labels, extra=extra)
    print(f"D1 done ({time.time()-t0:.0f}s); full-fit D0 ...", flush=True)
    prob_d0 = oof_detector.fit_predict_full_probabilities(foot, labels)
    print(f"D0 done ({time.time()-t0:.0f}s)", flush=True)

    ridge = oof_detector.ridge_nms(prob_d1, foot, sigma=1.0)
    score = (prob_d1 * (0.5 + persist_rank)).astype(np.float32)
    pool_all = ridge & foot & ~labels & (d_cat > 2.0)
    ys, xs = np.nonzero(pool_all)
    svals = score[ys, xs]
    order = np.argsort(-svals, kind="stable")
    ys, xs = ys[order], xs[order]
    print(f"ridge pool (d_cat>2): {len(ys):,} px", flush=True)

    def emit(k: int) -> np.ndarray:
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
    slug = "h39-1-depthslice-persist-b2"
    nan_name = submission.make_filename("gems28", slug, DATE, cid, "nan")
    af_name = submission.make_filename("gems28", slug, DATE, cid, "allfinite")
    dl = ROOT / "docs/downloads"
    p_nan = submission.write_geotiff(pred, paths.TEMPLATE, dl / nan_name, outside="nan")
    p_af = submission.write_geotiff(pred, paths.TEMPLATE, dl / af_name, outside="zero")
    p_zip = submission.zip_single(p_nan)
    v_nan = submission.verify_geotiff(p_nan, paths.TEMPLATE)
    v_af = submission.verify_geotiff(p_af, paths.TEMPLATE)

    # --- uniqueness vs registry (existing downloads + education copies of external bests) ---
    registry = {p.name: p for p in sorted(dl.glob("*-nan.tif")) if p.name != nan_name}
    registry.update({k: v for k, v in REGISTRY_EXTRA.items() if v.is_file()})
    rng = np.random.default_rng(15)
    foot_idx = np.flatnonzero(foot.ravel())
    sample = np.sort(rng.choice(foot_idx, size=400_000, replace=False))
    s_d1 = prob_d1.ravel()[sample].astype(np.float64)
    uniq = {}
    for name, p in registry.items():
        ref = load_dots(p)
        uniq[name] = {
            "frac_our_dots_within3px": within_frac(dots, ref),
            "spearman_probD1_vs_binary_sample400k":
                float(spearmanr(s_d1, ref.ravel()[sample].astype(np.float64)).statistic),
            "registry_dots": int(ref.sum()),
        }
        print(f"  uniq vs {name}: within3={uniq[name]['frac_our_dots_within3px']:.3f}", flush=True)
    spear_d1_d0 = float(spearmanr(s_d1, prob_d0.ravel()[sample].astype(np.float64)).statistic)

    out = {
        "experiment": "S15 Exp3 build (knowledge/47 §6)",
        "content_id": cid, "slug": slug, "date": DATE,
        "nan_tif": nan_name, "allfinite_tif": af_name, "zip": p_zip.name,
        "sha256_nan": submission.sha256_file(p_nan), "sha256_allfinite": submission.sha256_file(p_af),
        "sha256_zip": submission.sha256_file(p_zip),
        "bytes_nan": p_nan.stat().st_size, "bytes_allfinite": p_af.stat().st_size,
        "bytes_zip": p_zip.stat().st_size,
        "emitted_px": n_final, "target_px": TARGET_N,
        "min_d_cat_of_dots_px": float(d_cat[dots].min()),
        "on_catalogue_dots": int((dots & labels).sum()),
        "verify_nan": v_nan, "verify_allfinite": v_af,
        "spearman_probD1_vs_probD0_sample400k": spear_d1_d0,
        "uniqueness_vs_registry": uniq,
        "uniqueness_protocol": "duplicate iff spearman > 0.90 OR frac_our_dots_within3px > 0.70 "
                               "against ANY single registry raster (checked on surface and dots)",
        "uniqueness_pass": all(v["frac_our_dots_within3px"] <= 0.70
                               and abs(v["spearman_probD1_vs_binary_sample400k"]) <= 0.90
                               for v in uniq.values()) and abs(spear_d1_d0) <= 0.90,
        "seconds": round(time.time() - t0, 1),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (ROOT / "evidence/s15_candidate_build.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("content_id", "nan_tif", "emitted_px",
                                           "uniqueness_pass", "spearman_probD1_vs_probD0_sample400k")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
