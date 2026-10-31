#!/usr/bin/env python3
"""S31 EXP-2a: family-calibrated score projection (labelled PROJECTION, never a score).

Training rows: nine-site registry rasters with an owner-reported public score recorded in the
session prompt or registry/live_scores.json. Every file is read from data/registry_tifs/ and its
SHA-256 is recomputed here; rows whose bytes are absent are dropped (fail-closed).

Features (measured from bytes, catalogue = data/labels.tif):
  n_k            dots / 1000
  frac_near3     fraction of dots <= 3 px of catalogue
  frac_mid36     fraction of dots in (3, 6] px
  frac_far12     fraction of dots > 12 px from catalogue

Model family (frozen before projection):
  PRIMARY  = high-score family subset (reported >= 0.20, 13 rows), single feature frac_mid36
             (fraction of dots in (3, 6] px of catalogue). Chosen by exhaustive LOO R^2 search
             over feature subsets of size 1-3 on the family subset; best LOO R^2 = 0.555.
  GLOBAL   = all 18 rows, 4 z-scored features; REJECTED (LOO R^2 = -1.07, worse than the mean).
If PRIMARY LOO R^2 <= 0 the projection is declared NOT ESTIMABLE (gate (c) fails closed).
CI: residual bootstrap (2,000 resamples). A projection is never written as a score.
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
from gems27 import grid  # noqa: E402

# (repo subdir under data/registry_tifs, filename, owner-reported score, source of the report)
ROWS = [
    ("GEMSDOE24", "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-nan.tif", 0.2477, "task statement"),
    ("GEMSDOE25", "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif", 0.2600, "task statement"),
    ("GEMSDOE27", "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif", 0.2449, "task statement"),
    ("GEMSDOE27", "gems27-h29-hydrothermal-piedmont-celf-20261025-511898747886-allfinite.tif", 0.2190, "task statement"),
    ("GEMSDOE27", "gems27-h31-drcg-wl-celf28-20261026-cf8e1bbef244-allfinite.tif", 0.2250, "task statement"),
    ("GEMSDOE28", "gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif", 0.2708, "task statement"),
    ("GEMSDOE28", "gems28-h32-1-prethin-tip-euler-d2-8-20261003-31e35eee884e-nan.tif", 0.2649, "task statement"),
    ("GEMSDOE28", "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-nan.tif", 0.2710, "task statement"),
    ("GEMSDOE28", "gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-nan.tif", 0.2707, "task statement"),
    ("GEMSDOE28", "gems28-s18-mxtp-20261025-3e95505c011a-allfinite.tif", 0.0217, "task statement"),
    ("GEMSDOE28", "gems28-s21-puhgb-20261026-16bbf281ba9b-allfinite.tif", 0.0206, "task statement"),
    ("GEMSDOE30", "gems30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif", 0.2600, "task statement"),
    ("GEMSDOE30", "gems30-MSDB1-edge44090-20261025-e7856ec3f14a.tif", 0.1462, "task statement"),
    ("GEMSDOE32", "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif", 0.2778, "task statement"),
    ("GEMSDOE33", "gems33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif", 0.2632, "task statement"),
    ("GEMSDOE33", "gemsdoe33-s33-seisdil-strain-seismicity-37654-20261026-3463540a7e02-zeros.tif", 0.0963, "task statement"),
    ("GEMSDOE36", "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif", 0.2750, "task statement"),
    ("GEMSDOE36", "gemsdoe36-kpl36-exp3-20261026-fc869911e88c-zeros.tif", 0.1647, "task statement"),
]
FEATURE_NAMES = ["n_k", "frac_near3", "frac_mid36", "frac_far12"]


def resolve(subdir: str, fname: str) -> Path | None:
    base = ROOT / "data/registry_tifs" / subdir
    exact = base / fname
    if exact.exists():
        return exact
    hits = sorted(base.glob("*" + fname.split("-", 1)[-1]))
    return hits[0] if hits else None


def features_of(path: Path, foot: np.ndarray, dist_cat: np.ndarray) -> dict | None:
    with rasterio.open(path) as s:
        if s.shape != foot.shape:
            return None
        v = s.read(1).astype(np.float64)
    inside = v[foot]
    if not np.isfinite(inside).all() or inside.min() < 0 or inside.max() > 1:
        return None
    dots = (np.where(np.isfinite(v), v, 0.0) > 0.5) & foot
    n = int(dots.sum())
    if n == 0:
        return None
    d = dist_cat[dots]
    return {
        "n": n,
        "n_k": n / 1000.0,
        "frac_near3": float(np.mean(d <= 3.0)),
        "frac_mid36": float(np.mean((d > 3.0) & (d <= 6.0))),
        "frac_far12": float(np.mean(d > 12.0)),
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def ols(X: np.ndarray, y: np.ndarray) -> np.ndarray:
    return np.linalg.lstsq(X, y, rcond=None)[0]


def main() -> int:
    foot = grid.load_footprint(ROOT / "data/sample_submission.tif")
    labels = grid.load_labels(ROOT / "data/labels.tif")
    dist_cat = distance_transform_edt(~labels)

    rows, missing = [], []
    for subdir, fname, score, source in ROWS:
        p = resolve(subdir, fname)
        if p is None:
            missing.append(f"{subdir}/{fname}")
            continue
        f = features_of(p, foot, dist_cat)
        if f is None:
            missing.append(f"{subdir}/{fname} (format/off-grid)")
            continue
        f.update({"site": subdir, "file": p.name, "reported": score, "report_source": source})
        rows.append(f)

    out = {
        "schema": 1, "session": "S31", "experiment": "EXP-2a calibration",
        "label": "PROJECTION calibrated on OWNER-REPORTED scores (task statement); NOT a score, NOT organizer-confirmed",
        "rows_used": len(rows), "rows_missing": missing,
        "model_selection": "exhaustive LOO R^2 over subsets of size 1-3, family subset (reported >= 0.20)",
    }

    # PRIMARY model: family subset, single feature frac_mid36 (pre-registered as the search winner).
    fam = [r for r in rows if r["reported"] >= 0.20]
    Xf = np.array([[r["frac_mid36"]] for r in fam])
    yf = np.array([r["reported"] for r in fam])
    Xf1 = np.column_stack([np.ones(len(yf)), Xf])
    beta_f = ols(Xf1, yf)
    pred_f = Xf1 @ beta_f
    loo_f = np.empty(len(yf))
    for i in range(len(yf)):
        m = np.ones(len(yf), bool); m[i] = False
        b_i = ols(Xf1[m], yf[m])
        loo_f[i] = yf[i] - (Xf1[i] @ b_i)
    loo_r2_primary = 1.0 - float((loo_f ** 2).sum()) / float(((yf - yf.mean()) ** 2).sum())
    resid_f = yf - pred_f
    rng = np.random.default_rng(31)
    boots_f = np.array([ols(Xf1[rng.integers(0, len(yf), len(yf))], yf) for _ in range(2000)])

    # GLOBAL model: all rows, four features (recorded as REJECTED for the record).
    X = np.array([[r[n] for n in FEATURE_NAMES] for r in rows])
    y = np.array([r["reported"] for r in rows])
    Xz = (X - X.mean(0)) / np.where(X.std(0) > 0, X.std(0), 1.0)
    X1 = np.column_stack([np.ones(len(y)), Xz])
    beta_g = ols(X1, y)
    pred_g = X1 @ beta_g
    loo_g = np.empty(len(y))
    for i in range(len(y)):
        m = np.ones(len(y), bool); m[i] = False
        b_i = ols(X1[m], y[m])
        loo_g[i] = y[i] - (X1[i] @ b_i)
    loo_r2_global = 1.0 - float((loo_g ** 2).sum()) / float(((y - y.mean()) ** 2).sum())

    out.update({
        "primary": {
            "subset": "reported >= 0.20", "n_rows": len(yf), "feature": "frac_mid36",
            "loo_r2": loo_r2_primary, "usable": bool(loo_r2_primary > 0.0),
            "coefficients": {"intercept": float(beta_f[0]), "frac_mid36": float(beta_f[1])},
            "coef_bootstrap_ci95": {"intercept": [float(np.percentile(boots_f[:, 0], 2.5)), float(np.percentile(boots_f[:, 0], 97.5))],
                                    "frac_mid36": [float(np.percentile(boots_f[:, 1], 2.5)), float(np.percentile(boots_f[:, 1], 97.5))]},
            "resid_std": float(resid_f.std(ddof=1)),
        },
        "global": {"n_rows": len(y), "loo_r2": loo_r2_global, "rejected": bool(loo_r2_global <= 0),
                   "coefficients": dict(zip(["intercept"] + FEATURE_NAMES, [float(b) for b in beta_g]))},
        "family_rows": [{k: r[k] for k in ("site", "file", "reported", "n", "frac_near3", "frac_mid36", "frac_far12", "sha256")}
                        for r in fam],
        "all_rows": [{k: r[k] for k in ("site", "file", "reported", "n", "frac_near3", "frac_mid36", "frac_far12", "sha256")}
                     for r in rows],
    })

    def project(frac_mid36: float) -> dict:
        """PRIMARY-model projection with residual-bootstrap CI; NOT ESTIMABLE if unusable."""
        if loo_r2_primary <= 0.0:
            return {"estimable": False}
        mu = float(beta_f[0] + beta_f[1] * frac_mid36)
        samples = mu + rng.choice(resid_f, size=(2000,), replace=True)
        return {"estimable": True, "projected_mean": mu,
                "ci95": [float(np.percentile(samples, 2.5)), float(np.percentile(samples, 97.5))]}

    out["in_sample_projection_check"] = {
        f"{r['site']}/{r['file']}": {**project(r["frac_mid36"]), "reported": r["reported"]} for r in fam}
    out["project_fn_note"] = "project(frac_mid36); stored coefficients in evidence/s31_calibration.npz"
    np.savez(ROOT / "evidence" / "s31_calibration.npz",
             beta_primary=beta_f, resid_primary=resid_f,
             loo_r2_primary=np.array([loo_r2_primary]))
    (ROOT / "evidence" / "s31_calibration.json").write_text(json.dumps(out, indent=1) + "\n")
    print(json.dumps({"rows_used": out["rows_used"], "rows_missing": out["rows_missing"],
                      "primary_loo_r2": loo_r2_primary, "primary_coef": out["primary"]["coefficients"],
                      "global_loo_r2": loo_r2_global}, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
