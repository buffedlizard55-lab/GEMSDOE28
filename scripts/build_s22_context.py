#!/usr/bin/env python3
"""S22 context-feature builder (frozen in knowledge/62 before any canary/DTI).

Reads the shared prepared matrix (data/prepared/features.npy) and writes 32 label-free
multi-scale spatial-context features, footprint-ordered float16, to
data/prepared/context_s22.npy (+ .json). No labels, catalogue, or prior submission is read.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, paths  # noqa: E402

T0 = time.time()


def log(*a):
    print(f"[{time.time() - T0:7.1f}s]", *a, flush=True)


CTX_BANDS = ["tmi_hg", "iso_grav_anom_hg", "cond_surf", "det_elev", "det_elev_slope",
             "lidar_step_max", "lidar_ex_max", "lidar_lappos_max", "lidar_coh100", "lidar_relief"]
TENSOR_BANDS = ["lidar_step_max", "tmi_hg"]


def main() -> int:
    meta = json.loads(paths.PREPARED_META.read_text())
    names = meta["names"]
    X = np.load(paths.PREPARED_FEATURES, mmap_mode="r")
    foot = grid.load_footprint(paths.TEMPLATE)
    H, W = foot.shape
    foot_flat = np.flatnonzero(foot.ravel())
    assert len(foot_flat) == X.shape[0]

    rng = np.random.default_rng(7)
    sample_rows = np.sort(rng.choice(len(foot_flat), size=200_000, replace=False))

    out_path = paths.PREPARED_FEATURES.parent / "context_s22.npy"
    ctx_names: list[str] = []
    for b in CTX_BANDS:
        ctx_names += [f"ctx_{b}_g2", f"ctx_{b}_g5", f"ctx_{b}_grad_g2"]
    for b in TENSOR_BANDS:
        ctx_names += [f"ctx_{b}_tensor_coherence"]
    out = np.lib.format.open_memmap(out_path.with_suffix(".partial.npy"), mode="w+",
                                    dtype=np.float16, shape=(len(foot_flat), len(ctx_names)))

    def band_grid(j: int):
        g = np.full(H * W, np.nan, dtype=np.float32)
        g[foot_flat] = np.asarray(X[:, j], dtype=np.float32)
        return g.reshape(H, W)

    def standardised_filled(j: int):
        samp = np.asarray(X[sample_rows, j], dtype=np.float64)
        med = np.nanmedian(samp)
        q25, q75 = np.nanpercentile(samp, [25, 75])
        iqr = max(q75 - q25, 1e-9)
        g = band_grid(j)
        valid = np.isfinite(g)
        gs = np.clip(((g - med) / iqr).astype(np.float32), -30, 30)
        inds = distance_transform_edt(~valid, return_distances=False, return_indices=True)
        filled = gs[tuple(inds)]
        del inds
        return filled, valid

    col = 0
    std_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}
    for b in CTX_BANDS:
        j = names.index(b)
        filled, valid = standardised_filled(j)
        std_cache[b] = (filled, valid)
        g2 = gaussian_filter(filled, 2.0)
        g5 = gaussian_filter(filled, 5.0)
        gy, gx = np.gradient(g2)
        grad = np.hypot(gx, gy).astype(np.float32)
        del gy, gx
        for arr in (g2, g5, grad):
            v = arr.ravel()[foot_flat].astype(np.float32)
            v[~valid.ravel()[foot_flat]] = np.nan
            out[:, col] = np.clip(v, -60000, 60000).astype(np.float16)
            col += 1
        log("band", b, "cols", col)
        del g2, g5, grad

    for b in TENSOR_BANDS:
        filled, valid = std_cache[b]
        sm = gaussian_filter(filled, 1.0)
        gy, gx = np.gradient(sm)
        del sm
        jxx = gaussian_filter(gx * gx, 2.0)
        jyy = gaussian_filter(gy * gy, 2.0)
        jxy = gaussian_filter(gx * gy, 2.0)
        del gy, gx
        diff = np.sqrt((jxx - jyy) ** 2 + 4.0 * jxy ** 2)
        coh = ((diff / (jxx + jyy + 1e-12)) ** 2).astype(np.float32)
        coh[~np.isfinite(coh)] = 0.0
        del jxx, jyy, jxy, diff
        v = coh.ravel()[foot_flat]
        v[~valid.ravel()[foot_flat]] = np.nan
        out[:, col] = v.astype(np.float16)
        col += 1
        log("tensor", b, "cols", col)
        del coh

    assert col == len(ctx_names) == 32, (col, len(ctx_names))
    out.flush()
    del out
    out_path.with_suffix(".partial.npy").replace(out_path)

    h = hashlib.sha256()
    with open(out_path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    cmeta = {
        "schema": "s22-context-v1 (frozen in knowledge/62)",
        "names": ctx_names,
        "shape": [int(len(foot_flat)), int(len(ctx_names))],
        "dtype": "float16",
        "source_features_sha256": meta.get("sha256"),
        "sha256": h.hexdigest(),
        "note": "Label-free context only: Gaussian pyramid sigma2/sigma5 + |grad sigma2| of 10 bands; "
                "structure-tensor coherence of lidar_step_max and tmi_hg. NaN where base band invalid.",
    }
    (paths.PREPARED_FEATURES.parent / "context_s22.json").write_text(json.dumps(cmeta, indent=2) + "\n")
    log("done", json.dumps(cmeta)[:300])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
