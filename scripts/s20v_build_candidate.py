#!/usr/bin/env python3
"""S20 Experiment 3: build the full-grid vesselness candidate GeoTIFFs (knowledge/59).

Recipe identical to the gate cells, with the full catalogue as the visible set: ridge of the
cached label-free vesselness surface, pool restricted to d_cat > 2 px, top-K by vesselness with K
budget-searched so dot_thin(2.8) lands within +/-1% of 37,654 dots. Writes NaN-outside +
all-finite variants + single-member ZIP via the shared submission writer, verifies both variants
by independent re-read, and checks final-dot uniqueness (fraction within 3 px) against every
registry raster (docs/downloads/*-nan.tif + byte-verified champion/GEMSDOE36 forensic copies).
Does NOT decide the verdict (scripts/s20v_finalize.py does, from gate + uniqueness + validator).
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, oof_detector, paths, submission, thinning  # noqa: E402

TARGET_N = 37_654
DATE = "20261026"
SLUG = "s20-vesselness-lidarstep"
REGISTRY_EXTRA = {
    "champion_GEMSDOE32_e5eb6e7e": Path("/tmp/gems-mirrors/GEMSDOE32/docs/downloads/gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif"),
    "site36_GEMSDOE36_9b9ea4e6": Path("/tmp/gems-mirrors/GEMSDOE36/docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif"),
}
EXTRA_SHA = {"champion_GEMSDOE32_e5eb6e7e": "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
             "site36_GEMSDOE36_9b9ea4e6": "e15891020b9c57056ac7fa874a5e506fbd6ed9314a4ea8e73af0753887a3708a"}


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


def within_frac(ours: np.ndarray, ref: np.ndarray, r: float = 3.0) -> float:
    y, x = np.nonzero(ours)
    yb, xb = np.nonzero(ref)
    if len(y) == 0 or len(yb) == 0:
        return 0.0
    d, _ = cKDTree(np.c_[yb, xb].astype(float)).query(np.c_[y, x].astype(float), workers=1)
    return float((d <= r).mean())


def main() -> int:
    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS) & foot
    d_cat = distance_transform_edt(~labels)
    V = np.load(paths.DATA / "prepared/s20_vesselness.npy")
    with rasterio.open(paths.LIDAR) as s:
        lidar_valid = (s.read(12) > 0) & foot
    ridge = oof_detector.ridge_nms(V, lidar_valid, sigma=1.0)

    pool = ridge & foot & ~labels & (d_cat > 2.0)
    ys, xs = np.nonzero(pool)
    order = np.argsort(-V[ys, xs].astype(np.float64), kind="stable")
    ys, xs = ys[order], xs[order]
    print(f"ridge pool (d_cat>2): {len(ys):,} px", flush=True)

    def emit(k: int) -> np.ndarray:
        raw = np.zeros(foot.shape, bool)
        raw[ys[:k], xs[:k]] = True
        return thinning.dot_thin(raw, 2.8)

    lo, hi, best = 10_000, len(ys), None
    for it in range(10):
        k = (lo + hi) // 2
        trial = emit(k)
        n = int(trial.sum())
        print(f"  budget search it={it} k={k:,} -> N={n:,}", flush=True)
        if best is None or abs(n - TARGET_N) < abs(int(best.sum()) - TARGET_N):
            best = trial
        if abs(n - TARGET_N) <= 0.01 * TARGET_N:
            break
        if n < TARGET_N:
            lo = k
        else:
            hi = k
    dots = best & foot & ~labels & (d_cat > 2.0)
    n_final = int(dots.sum())
    assert not (dots & labels).any() and float(d_cat[dots].min()) > 2.0
    print(f"final dots: {n_final:,} (target {TARGET_N:,})", flush=True)

    pred = np.where(dots, 1.0, 0.0).astype(np.float32)
    cid = submission.scored_content_id(pred, foot, labels)
    nan_name = submission.make_filename("gems28", SLUG, DATE, cid, "nan")
    af_name = submission.make_filename("gems28", SLUG, DATE, cid, "allfinite")
    dl = ROOT / "docs/downloads"
    p_nan = submission.write_geotiff(pred, paths.TEMPLATE, dl / nan_name, outside="nan")
    p_af = submission.write_geotiff(pred, paths.TEMPLATE, dl / af_name, outside="zero")
    p_zip = submission.zip_single(p_nan)
    v_nan = submission.verify_geotiff(p_nan, paths.TEMPLATE)
    v_af = submission.verify_geotiff(p_af, paths.TEMPLATE)

    registry = {p.name: p for p in sorted(dl.glob("*-nan.tif")) if p.name != nan_name}
    for key, p in REGISTRY_EXTRA.items():
        if p.is_file() and sha256_file(p) == EXTRA_SHA[key]:
            registry[key] = p
    uniq = {}
    for name, p in registry.items():
        ref = load_dots(p)
        uniq[name] = {"frac_our_dots_within3px": within_frac(dots, ref),
                      "registry_dots": int(ref.sum())}
    worst = max(uniq.items(), key=lambda kv: kv[1]["frac_our_dots_within3px"]) if uniq else (None, {})
    holdout = json.loads((ROOT / "evidence/s20v_holdout.json").read_text())
    pre_ok = bool((holdout.get("preplacement") or {}).get("pass"))
    out = {"candidate": nan_name, "allfinite": af_name, "zip": p_zip.name, "content_id": cid,
           "slug": SLUG, "date": DATE, "n_dots": n_final, "target_n": TARGET_N,
           "sha256": {"nan": sha256_file(p_nan), "allfinite": sha256_file(p_af),
                      "zip": sha256_file(p_zip)},
           "bytes": {"nan": p_nan.stat().st_size, "allfinite": p_af.stat().st_size,
                     "zip": p_zip.stat().st_size},
           "validator_nan": v_nan, "validator_allfinite": v_af,
           "preplacement_pass_from_exp2": pre_ok,
           "worst_registry_raster_by_dot_overlap": ({"raster": worst[0], **worst[1]} if worst[0] else None),
           "uniqueness_table": uniq,
           "uniqueness_pass": bool(pre_ok and worst[1].get("frac_our_dots_within3px", 1.0) <= 0.70),
           "seconds": round(time.time() - t0, 1)}
    (ROOT / "evidence/s20v_candidate_build.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({"candidate": nan_name, "n_dots": n_final, "content_id": cid,
                      "validator_nan_pass": v_nan["hard_checks_passed"],
                      "validator_allfinite_pass": v_af["hard_checks_passed"],
                      "worst_overlap": out["worst_registry_raster_by_dot_overlap"],
                      "uniqueness_pass": out["uniqueness_pass"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
