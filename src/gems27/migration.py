"""Continuation-height ridge migration bands (H40-1, Session 16; knowledge/49).

A dipping subsurface boundary (fault, contact, dike) does not project to the same
map position at every observation height: upward-continuing the field by h attenuates
short wavelengths as exp(-|k|h) (Blakely 1995), and the horizontal-gradient (HG)
ridge of a dipping edge shifts laterally, systematically, in the dip direction.
A vertical edge does not move; a shallow noise ridge vanishes instead of moving.
H39-1 (depthslice.py) encoded only HG *magnitudes* and a persistence ratio at each
pixel. This module encodes the ridge *geometry* depthslice never used:

  {tmi,grav}_signed_migration_px  signed distance the shallow HG ridge travels to
      reach the 2 km HG ridge, projected on the local field-gradient normal
      (px, clipped [-12, 12]), Gaussian-smoothed (sigma=2) along the shallow ridge
      and 0 away from any ridge corridor.
  {tmi,grav}_migration_coherence mean over the 0/1/2 km levels of exp(-d_l / 2),
      d_l = distance (px) to that level's HG ridge. In [0, 1]; 1 on a ridge that
      exists at every level.

Label-free: no function here reads labels or any catalogue-derived raster.
Named non-fault mimic: a dipping lithologic contact / mafic dike migrates
identically with zero Quaternary slip (knowledge/49).
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

from . import depthslice, oof_detector

BAND_NAMES = [
    "tmi_signed_migration_px",
    "tmi_migration_coherence",
    "grav_signed_migration_px",
    "grav_migration_coherence",
]
LEVELS_M = (0.0, 1000.0, 2000.0)
CLIP_PX = 12.0


def ridge_at(hg: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """1-px HG ridge mask via the repo's shared directional NMS (not a fork)."""
    return oof_detector.ridge_nms(np.asarray(hg, dtype=np.float32), np.asarray(valid, bool), sigma=1.0)


def migration_bands_from_hg_levels(
    hg_levels: list[np.ndarray], grad_normal: tuple[np.ndarray, np.ndarray], valid: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """(signed_migration_px, coherence) from HG magnitudes at increasing heights.

    `grad_normal` is (gy, gx) of the mid-level field (unit normal is derived here).
    Deterministic; pure function of its inputs (synthetic-tested in tests/test_migration.py).
    """
    if len(hg_levels) < 2:
        raise ValueError("need at least two continuation levels")
    valid = np.asarray(valid, bool)
    ridges = [ridge_at(h, valid) for h in hg_levels]
    dists = [distance_transform_edt(~r) for r in ridges]
    coherence = np.mean([np.exp(-d / 2.0) for d in dists], axis=0)

    shallow, deep = ridges[0], ridges[-1]
    # Nearest deep-ridge pixel for every shallow-ridge pixel (EDT indices on ~deep).
    inds = distance_transform_edt(~deep, return_distances=False, return_indices=True)
    ys, xs = np.nonzero(shallow & valid)
    vy = inds[0][ys, xs].astype(np.float64) - ys
    vx = inds[1][ys, xs].astype(np.float64) - xs
    gy, gx = (np.asarray(g, dtype=np.float64) for g in grad_normal)
    nrm = np.hypot(gx[ys, xs], gy[ys, xs])
    ok = nrm > 0
    signed_vals = np.zeros(len(ys))
    signed_vals[ok] = (vx[ok] * gx[ys[ok], xs[ok]] + vy[ok] * gy[ys[ok], xs[ok]]) / nrm[ok]

    sparse = np.zeros(valid.shape, dtype=np.float64)
    sparse[ys, xs] = np.clip(signed_vals, -CLIP_PX, CLIP_PX)
    weight = gaussian_filter((shallow & valid).astype(np.float64), 2.0)
    smooth = gaussian_filter(sparse, 2.0)
    signed = np.where(weight > 0.05, smooth / np.maximum(weight, 1e-12), 0.0)
    signed = np.clip(signed, -CLIP_PX, CLIP_PX)
    return signed.astype(np.float32), coherence.astype(np.float32)


def _field_bands(field_filled: np.ndarray, valid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ups = [gaussian_filter(field_filled, 1.0)]
    ups += [depthslice.upward_continue(field_filled, h) for h in LEVELS_M[1:]]
    hgs = [depthslice.hg_mag(u) for u in ups]
    gy, gx = np.gradient(ups[1], depthslice.grid.PIXEL_M)
    return migration_bands_from_hg_levels(hgs, (gy, gx), valid)


def build_migration_bands(training_path, foot: np.ndarray) -> dict:
    """Build the 4 frozen H40-1 bands from training bands 14 (tmi) and 13 (iso_grav_anom)."""
    foot = np.asarray(foot, bool)
    tmi, tmi_valid = depthslice._read_band(training_path, 14, "tmi", foot)
    grav, grav_valid = depthslice._read_band(training_path, 13, "iso_grav_anom", foot)
    tmi_s, tmi_c = _field_bands(tmi, foot)
    grav_s, grav_c = _field_bands(grav, foot)
    bands = {
        "tmi_signed_migration_px": tmi_s,
        "tmi_migration_coherence": tmi_c,
        "grav_signed_migration_px": grav_s,
        "grav_migration_coherence": grav_c,
    }
    return {
        "names": list(BAND_NAMES),
        "bands": {k: np.where(foot, v, 0.0).astype(np.float32) for k, v in bands.items()},
        "valid_frac": {"tmi": float(tmi_valid[foot].mean()), "iso_grav_anom": float(grav_valid[foot].mean())},
    }


def bands_to_footprint_matrix(built: dict, foot: np.ndarray) -> np.ndarray:
    """(n_footprint, 4) float32 matrix in row-major footprint order (oof_detector contract)."""
    foot = np.asarray(foot, bool)
    return np.column_stack([built["bands"][n][foot] for n in built["names"]]).astype(np.float32)
