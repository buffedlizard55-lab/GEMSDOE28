#!/usr/bin/env python3
"""S22 Experiment 3 — final full-footprint candidate build (frozen recipe, knowledge/62).

Trains the lane (32 base + 32 context) on ALL public labels, predicts the footprint, emits
ridge-restricted 2.8px-spaced dots outside the <=2px catalogue ring at the 37,654 budget,
validates with the shared writer/verifier, and audits uniqueness vs the snapshot registry.
No H19-5/champion dots or surface are read by the model or the emission pool; registry rasters
are read only for the post-hoc uniqueness comparison.
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
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems27 import grid, paths, submission  # noqa: E402
from gems27.oof_detector import ridge_nms  # noqa: E402
from run_s22_holdout import greedy_emit  # noqa: E402

T0 = time.time()
BUDGET = 37_654
SEED = 360


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


def dotset_sha(dots: np.ndarray) -> str:
    return hashlib.sha256(np.argwhere(dots).astype(np.int32).tobytes()).hexdigest()


def main() -> int:
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    H, W = foot.shape
    foot_flat = np.flatnonzero(foot.ravel())
    pos_of_flat = -np.ones(H * W, dtype=np.int32)
    pos_of_flat[foot_flat] = np.arange(len(foot_flat), dtype=np.int32)
    d_cat = distance_transform_edt(~labels)

    Xb = np.load(paths.PREPARED_FEATURES, mmap_mode="r")
    Xc = np.load(paths.PREPARED_FEATURES.parent / "context_s22.npy", mmap_mode="r")

    def assemble(rows: np.ndarray) -> np.ndarray:
        return np.concatenate([np.asarray(Xb[rows], dtype=np.float32),
                               np.asarray(Xc[rows], dtype=np.float32)], axis=1)

    rng = np.random.default_rng(SEED)
    pos_flat = np.flatnonzero(labels.ravel())
    neg_flat = np.flatnonzero((foot & ~labels).ravel() & (d_cat.ravel() >= 3))
    pos_s = rng.choice(pos_flat, size=min(40_000, len(pos_flat)), replace=False)
    neg_s = rng.choice(neg_flat, size=min(120_000, len(neg_flat)), replace=False)
    joint = np.sort(np.r_[pos_s, neg_s])
    rows = pos_of_flat[joint]
    y = np.isin(joint, pos_s).astype(int)
    log("train rows", len(rows), "pos", int(y.sum()))

    clf = HistGradientBoostingClassifier(
        max_iter=250, learning_rate=0.06, max_leaf_nodes=63,
        min_samples_leaf=40, l2_regularization=1.0, random_state=SEED)
    clf.fit(assemble(rows), y)
    log("fit done")

    all_rows = np.arange(len(foot_flat), dtype=np.int64)
    probs = np.empty(len(all_rows), dtype=np.float32)
    for s0 in range(0, len(all_rows), 200_000):
        idx = all_rows[s0:s0 + 200_000]
        probs[s0:s0 + 200_000] = clf.predict_proba(assemble(idx))[:, 1]
        log("predicted", s0 + len(idx), "/", len(all_rows))
    surface = np.zeros((H, W), dtype=np.float32)
    rr, cc = np.divmod(foot_flat, W)
    surface[rr, cc] = probs
    del probs, clf
    surf_path = paths.PREPARED_FEATURES.parent / "s22_surface.npy"
    np.save(surf_path, surface)
    log("surface saved", surf_path)

    ridge = ridge_nms(surface, foot, sigma=1.0)
    allowed = foot & ~labels & (d_cat > 2)
    dots, stats = greedy_emit(surface, allowed, ridge, BUDGET)
    n_dots = int(dots.sum())
    assert int((dots & labels).sum()) == 0
    min_dcat = float(d_cat[dots].min())
    assert min_dcat > 2.0, min_dcat
    dsha = dotset_sha(dots)
    cid = dsha[:12]
    log("dots", n_dots, stats, "min_dcat", min_dcat, "dotset", dsha)

    stem = f"gems28-s22-ctxhgb-20261026-{cid}"
    dl = ROOT / "docs/downloads"
    pred = dots.astype(np.float32)
    nan_tif = submission.write_geotiff(pred, paths.TEMPLATE, dl / f"{stem}-nan.tif", outside="nan")
    fin_tif = submission.write_geotiff(pred, paths.TEMPLATE, dl / f"{stem}-allfinite.tif", outside="zero")
    zip_path = submission.zip_single(nan_tif, dl / f"{stem}-nan.zip")
    ver_nan = submission.verify_geotiff(nan_tif, paths.TEMPLATE)
    ver_fin = submission.verify_geotiff(fin_tif, paths.TEMPLATE)
    log("validator nan", ver_nan["hard_checks_passed"], "allfinite", ver_fin["hard_checks_passed"])

    # ---------- uniqueness vs snapshot registry (post-hoc comparison only) ----------
    scratch = ROOT / "evidence/_scratch/registry32"
    seen_dotsets: dict[str, str] = {}
    candidates = sorted(dl.glob("*-allfinite.tif")) + [
        scratch / "champion32_zeros.tif", scratch / "pinn36_zeros.tif",
        scratch / "best30.tif", scratch / "best31.tif", scratch / "best33.tif",
        paths.DOTTED_D2_8, paths.DOTTED_0_2477, paths.H19_5,
    ]
    our_flat_rows = np.sort(rng.choice(len(foot_flat), size=200_000, replace=False)) \
        if False else np.sort(np.random.default_rng(22).choice(len(foot_flat), size=200_000, replace=False))
    sample_flats = foot_flat[our_flat_rows]
    surf_sample = surface.ravel()[sample_flats].astype(np.float64)
    comparisons = []
    for p in candidates:
        if not p.is_file() or stem in p.name:
            continue
        with rasterio.open(p) as ds:
            a = ds.read(1)
        reg = np.isfinite(a) & (a > 0)
        rsha = dotset_sha(reg)
        if rsha in seen_dotsets or rsha == dsha:
            continue
        seen_dotsets[rsha] = p.name
        d_reg = distance_transform_edt(~reg)
        frac = float((d_reg[dots] <= 3).mean())
        reg_sample = a.ravel()[sample_flats].astype(np.float64)
        ok = np.isfinite(reg_sample)
        rho = float(spearmanr(surf_sample[ok], reg_sample[ok]).statistic) if ok.sum() > 1000 else None
        comparisons.append({
            "file": p.name, "dotset_sha256": rsha, "registry_dots": int(reg.sum()),
            "frac_our_dots_within3px": frac,
            "jaccard_exact": float((dots & reg).sum() / max((dots | reg).sum(), 1)),
            "spearman_surface_vs_registry_sample200k": rho,
        })
        del a, reg, d_reg
    comparisons.sort(key=lambda c: -c["frac_our_dots_within3px"])
    worst_overlap = comparisons[0] if comparisons else None
    worst_rho = max((c for c in comparisons if c["spearman_surface_vs_registry_sample200k"] is not None),
                    key=lambda c: abs(c["spearman_surface_vs_registry_sample200k"]), default=None)
    champ_cmp = next((c for c in comparisons if c["file"] == "champion32_zeros.tif"), None)
    log("registry distinct dotsets", len(comparisons), "worst overlap", worst_overlap)
    log("vs champion", champ_cmp)

    build = {
        "experiment": "S22 Exp3 final candidate build (frozen knowledge/62)",
        "date_utc": "2026-10-26",
        "content_id": cid,
        "dotset_sha256": dsha,
        "n_dots": n_dots,
        "emission_stats": stats,
        "min_dist_to_catalogue_px": min_dcat,
        "dots_on_catalogue": 0,
        "train": {"pos_sampled": int(len(pos_s)), "neg_sampled": int(len(neg_s)), "seed": SEED,
                  "features": "32 base + 32 S22 context", "labels": "all public catalogue pixels"},
        "files": {
            "allfinite_primary": {"name": fin_tif.name, "sha256": submission.sha256_file(fin_tif),
                                  "bytes": fin_tif.stat().st_size},
            "nan_twin": {"name": nan_tif.name, "sha256": submission.sha256_file(nan_tif),
                         "bytes": nan_tif.stat().st_size},
            "zip": {"name": zip_path.name, "sha256": submission.sha256_file(zip_path),
                    "bytes": zip_path.stat().st_size},
        },
        "validator": {"nan": ver_nan, "allfinite": ver_fin},
        "uniqueness": {
            "registry_distinct_dotsets": len(comparisons),
            "worst_overlap3px": worst_overlap,
            "worst_abs_spearman": worst_rho,
            "vs_GEMSDOE32_champion": champ_cmp,
            "comparisons": comparisons,
            "thresholds": {"abs_spearman_max": 0.90, "overlap3px_max": 0.70},
            "pass": bool(worst_overlap and worst_overlap["frac_our_dots_within3px"] <= 0.70
                         and (worst_rho is None or abs(worst_rho["spearman_surface_vs_registry_sample200k"]) <= 0.90)),
        },
        "runtime_s": time.time() - T0,
    }
    (ROOT / "evidence/s22_candidate_build.json").write_text(json.dumps(build, indent=2, default=str) + "\n")
    checks = {
        "candidate": stem,
        "validator_allfinite": ver_fin,
        "validator_nan": ver_nan,
        "n_dots": n_dots,
        "dotset_sha256": dsha,
        "uniqueness_worst_overlap3px": worst_overlap,
        "uniqueness_vs_champion": champ_cmp,
    }
    (dl / f"checks-{stem}.json").write_text(json.dumps(checks, indent=2, default=str) + "\n")
    log("BUILD DONE", stem)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
