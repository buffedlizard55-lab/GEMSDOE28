#!/usr/bin/env python3
"""S18 Experiment 3 (knowledge/52): build the H42-1 candidate GeoTIFF package.

Full-fit frozen 32-band detector -> ridge NMS -> probability-ranked top-budget pool
(d_cat > 2 px build hygiene) -> dot_thin(2.8) at the champion's budget -> H42-1 up-dip
relocation (phys) -> dot_thin(2.8). Writes nan + allfinite(zeros) + single-member zip via
src/gems27/submission.py and evidence/s18_candidate_build.json with (a) binding uniqueness
vs the ten owner-reported scored rasters of the nine focus sites (binary phi + within-3px +
surface Spearman) and (b) a disclosed overlap table vs every other local download.
Does NOT decide the verdict (scripts/finalize_s18.py does, from gate + uniqueness + validator).
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
DL = ROOT / "docs/downloads"
SCORED_REGISTRY = [
    ("champion_e5eb6e7e_GEMSDOE32_owner_reported_0.2778", Path("/tmp/forensic/champion_e5eb6e7e_zeros.tif")),
    ("gems36_9b9ea4e6_GEMSDOE36_owner_reported_0.2750", Path("/tmp/forensic/gems36_9b9ea4e6_zeros.tif")),
    ("solo_8acb75e1_GEMSDOE28_31_owner_reported_0.2708",
     DL / "gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"),
    ("rung30_b531dae0_GEMSDOE28_owner_reported_0.2710",
     DL / "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif"),
    ("hfeuler_56a9f473_GEMSDOE28_owner_reported_0.2707",
     DL / "gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif"),
    ("prethin_31e35eee_GEMSDOE28_owner_reported_0.2649",
     DL / "gems28-h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan.tif"),
    ("analog_cb490425_GEMSDOE33_owner_reported_0.2632", Path("/tmp/forensic/gems33_analog_cb490425.tif")),
    ("d28_e56ea318_GEMSDOE25_30_owner_reported_0.2600", paths.DOTTED_D2_8),
    ("d15_989f5950_GEMSDOE24_owner_reported_0.2477", paths.DOTTED_0_2477),
    ("tv2_5512495c_GEMSDOE27_owner_reported_0.2449",
     DL / "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif"),
]


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


def binary_phi(ours: np.ndarray, ref: np.ndarray, mask: np.ndarray) -> float:
    """Pearson phi on binary rasters over the footprint (= Spearman for binary variables)."""
    a = ours[mask]
    b = ref[mask]
    tp = float((a & b).sum())
    fp = float((a & ~b).sum())
    fn = float((~a & b).sum())
    tn = float((~a & ~b).sum())
    den = np.sqrt((tp + fp) * (tp + fn) * (tn + fp) * (tn + fn))
    return float((tp * tn - fp * fn) / den) if den > 0 else 0.0


def main() -> int:
    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS) & foot
    d_cat = distance_transform_edt(~labels)
    vec = np.load(paths.DATA / "prepared/migration_vectors.npz")
    depth = migration.read_depth_to_base(paths.TRAINING, foot)

    print("full-fit frozen 32-band detector ...", flush=True)
    prob = oof_detector.fit_predict_full_probabilities(foot, labels)
    print(f"detector done ({time.time()-t0:.0f}s)", flush=True)

    ridge = oof_detector.ridge_nms(prob, foot, sigma=1.0)
    pool_all = ridge & foot & ~labels & (d_cat > 2.0)
    ys, xs = np.nonzero(pool_all)
    svals = prob[ys, xs]
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
    base_dots = best
    base_pred = np.where(base_dots, 1.0, 0.0).astype(np.float32)
    v_base = base_pred[foot & ~labels].astype("<f4").copy()
    v_base[v_base == 0] = 0
    base_scored_sha256 = hashlib.sha256(v_base.tobytes()).hexdigest()

    blocked = labels | (d_cat <= 2.0)
    rel, rel_stats = migration.relocate_dots(base_dots, vec["vy"], vec["vx"], depth,
                                              blocked, foot, mode="phys", seed=0)
    dots = thinning.dot_thin(rel, 2.8) & foot & ~labels
    rel_stats["n_after_final_thin"] = int(dots.sum())
    print(f"relocation: {rel_stats}", flush=True)
    assert not (dots & labels).any() and float(d_cat[dots].min()) > 2.0

    pred = np.where(dots, 1.0, 0.0).astype(np.float32)
    cid = submission.scored_content_id(pred, foot, labels)
    slug = "h42-1-migx-reloc-b1"
    nan_name = submission.make_filename("gems28", slug, DATE, cid, "nan")
    af_name = submission.make_filename("gems28", slug, DATE, cid, "allfinite")
    p_nan = submission.write_geotiff(pred, paths.TEMPLATE, DL / nan_name, outside="nan")
    p_af = submission.write_geotiff(pred, paths.TEMPLATE, DL / af_name, outside="zero")
    p_zip = submission.zip_single(p_nan)
    v_nan = submission.verify_geotiff(p_nan, paths.TEMPLATE)
    v_af = submission.verify_geotiff(p_af, paths.TEMPLATE)

    rng = np.random.default_rng(18)
    foot_idx = np.flatnonzero(foot.ravel())
    sample = np.sort(rng.choice(foot_idx, size=400_000, replace=False))
    s_prob = prob.ravel()[sample].astype(np.float64)

    scored = {}
    binding_files = set()
    for name, p in SCORED_REGISTRY:
        if not p.is_file():
            scored[name] = {"missing": True, "path": str(p)}
            continue
        binding_files.add(p.name)
        ref = load_dots(p) & foot
        scored[name] = {
            "file": p.name, "sha256": submission.sha256_file(p),
            "registry_dots": int(ref.sum()),
            "binary_phi_footprint": binary_phi(dots, ref, foot),
            "frac_our_dots_within3px": within_frac(dots, ref),
            "frac_base_dots_within3px_pre_relocation": within_frac(base_dots, ref),
            "spearman_prob_vs_binary_sample400k": float(
                spearmanr(s_prob, ref.ravel()[sample].astype(np.float64)).statistic),
        }
        print(f"  scored-uniq vs {name}: phi={scored[name]['binary_phi_footprint']:.3f} "
              f"within3={scored[name]['frac_our_dots_within3px']:.3f}", flush=True)
    binding_pass = all(
        (not v.get("missing")) and abs(v["binary_phi_footprint"]) <= 0.90
        and v["frac_our_dots_within3px"] <= 0.70
        and abs(v["spearman_prob_vs_binary_sample400k"]) <= 0.90
        for v in scored.values())

    disclosed = {}
    for p in sorted(DL.glob("*-nan.tif")):
        if p.name in binding_files or p.name == nan_name:
            continue
        ref = load_dots(p) & foot
        disclosed[p.name] = {"frac_our_dots_within3px": within_frac(dots, ref),
                             "registry_dots": int(ref.sum())}
    worst_disclosed = max(disclosed.items(), key=lambda kv: kv[1]["frac_our_dots_within3px"],
                          default=(None, {"frac_our_dots_within3px": 0.0}))

    out = {
        "experiment": "S18 Exp3 build (knowledge/52)",
        "content_id": cid, "slug": slug, "date": DATE,
        "nan_tif": nan_name, "allfinite_tif": af_name, "zip": p_zip.name,
        "sha256_nan": submission.sha256_file(p_nan),
        "sha256_allfinite": submission.sha256_file(p_af),
        "sha256_zip": submission.sha256_file(p_zip),
        "bytes_nan": p_nan.stat().st_size, "bytes_allfinite": p_af.stat().st_size,
        "bytes_zip": p_zip.stat().st_size,
        "emitted_px": int(dots.sum()), "base_px_pre_relocation": int(base_dots.sum()),
        "target_px": TARGET_N,
        "base_scored_sha256_full": base_scored_sha256,
        "relocation": rel_stats,
        "min_d_cat_of_dots_px": float(d_cat[dots].min()),
        "on_catalogue_dots": int((dots & labels).sum()),
        "verify_nan": v_nan, "verify_allfinite": v_af,
        "uniqueness_scored_registry_binding": scored,
        "uniqueness_binding_pass": bool(binding_pass),
        "uniqueness_disclosed_other_downloads_within3px": disclosed,
        "worst_disclosed_other_download": {"raster": worst_disclosed[0],
                                           **worst_disclosed[1]},
        "uniqueness_protocol": ("binding: vs every scored focus-site raster, binary phi <= 0.90 AND "
                                "frac dots within 3px <= 0.70 AND surface Spearman <= 0.90 "
                                "(knowledge/52); all other downloads disclosed, not binding"),
        "seconds": round(time.time() - t0, 1),
        "code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    (ROOT / "evidence/s18_candidate_build.json").write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps({k: out[k] for k in ("content_id", "nan_tif", "emitted_px",
                                           "uniqueness_binding_pass", "relocation")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
