"""S18-MXTP: label-free linear-in-height ridge-locus extrapolation.

This is an empirical contact-location hypothesis, NOT a dip inversion. Superposed
sources, remanent magnetization, and dipping lithologic contacts can mimic a fault.
Uses the existing physical feature cache, Fourier continuation and ridge extractor.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter
from scipy.stats import rankdata

from . import depthslice, migration


def extrapolate_ridges(r1, r2, r3, strength, valid, *, min_shift=2.0, max_shift=12.0,
                       max_residual=3.0):
    """Splat q0=2q1-q2 using nearest-ridge matches at equal height increments.

    q3 must agree with 2q2-q1. No clipping to grid edges: out-of-grid q0 is discarded.
    Returns sparse confidence and diagnostics; deterministic tie policy is SciPy EDT's.
    """
    arrays = [np.asarray(x) for x in (r1, r2, r3, strength, valid)]
    if any(x.ndim != 2 or x.shape != arrays[0].shape for x in arrays):
        raise ValueError("equal-shaped 2-D grids required")
    r1, r2, r3, strength, valid = arrays
    valid = valid.astype(bool)
    ridges = [r.astype(bool) & valid for r in (r1, r2, r3)]
    out = np.zeros(valid.shape, np.float32)
    if not all(r.any() for r in ridges):
        return out, {"q1_count": int(ridges[0].sum()), "accepted": 0}
    if not np.isfinite(strength[valid]).all():
        raise ValueError("strength must be finite on valid cells")
    y1, x1 = np.nonzero(ridges[0])
    nearest2 = distance_transform_edt(~ridges[1], return_distances=False, return_indices=True)
    y2, x2 = nearest2[:, y1, x1]
    del nearest2
    nearest3 = distance_transform_edt(~ridges[2], return_distances=False, return_indices=True)
    y3, x3 = nearest3[:, y2, x2]
    del nearest3
    shift = np.hypot(y2 - y1, x2 - x1)
    residual = np.hypot(y3 - (2 * y2 - y1), x3 - (2 * x2 - x1))
    y0, x0 = 2 * y1 - y2, 2 * x1 - x2
    h, w = valid.shape
    ok = ((shift >= min_shift) & (shift <= max_shift) & (residual <= max_residual)
          & (y0 >= 0) & (x0 >= 0) & (y0 < h) & (x0 < w))
    # Evaluate valid only after bounds checks, never wrap negative indices.
    at = np.flatnonzero(ok)
    at = at[valid[y0[at], x0[at]]]
    ranks = rankdata(strength[y1, x1], method="average") / len(y1)
    conf = ranks * np.exp(-residual / max_residual)
    np.maximum.at(out, (y0[at], x0[at]), conf[at].astype(np.float32))
    return out, {"q1_count": int(len(y1)), "accepted": int(len(at)),
                 "distinct_positions": int(np.count_nonzero(out))}


def field_surface(field, foot):
    foot = np.asarray(foot, bool)
    field = depthslice.fill_nearest(field, foot & np.isfinite(field))
    inner = foot & (distance_transform_edt(foot) > 32)
    ridges = []
    strength = None
    for height in (1000.0, 2000.0, 3000.0):
        hg = depthslice.hg_mag(depthslice.upward_continue(field, height))
        ridges.append(migration.ridge_at(hg, inner))
        if strength is None:
            strength = hg
    sparse, meta = extrapolate_ridges(*ridges, strength, inner)
    surface = gaussian_filter(sparse, 0.75).astype(np.float32)
    surface[~inner] = 0
    if surface.max() > 0:
        surface /= surface.max()
    return surface, meta


def build_from_cache(cache, names, foot):
    """Use prepared raw physical columns, never a catalogue feature or old submission."""
    foot = np.asarray(foot, bool)
    if cache.shape[0] != int(foot.sum()) or len(names) != cache.shape[1]:
        raise ValueError("feature cache shape mismatch")
    surfaces, meta = {}, {}
    for name in ("tmi", "iso_grav_anom"):
        field = np.full(foot.shape, np.nan, np.float32)
        field[foot] = cache[:, names.index(name)]
        surfaces[name], meta[name] = field_surface(field, foot)
    surfaces["combined"] = np.maximum(surfaces["tmi"], surfaces["iso_grav_anom"])
    return surfaces, meta
