"""Structural-step coherence of the conductivity / conductive-base / strain group (H32-1).

Geological idea
---------------
The shipped detector is a *row-wise* gradient-boosted classifier: every footprint pixel is an
independent row of 32 (or 38) scalar band values. It therefore cannot represent a spatial derivative
of a band, only the band's value. H28-1 exploited that gap for the magnetics/gravity pair. H32-1
applies the same, already-validated pattern to the *subsurface-structure* group:

* ``depth_to_base_surf``  - depth to the conductive base surface (competition band 14),
* ``cond_surf``           - surface conductivity (competition band 16),
* ``geod_2ndinv``         - second invariant of the geodetic strain-rate tensor (band 3).

A fault that displaces the conductive base, or that bounds a conductive basin fill, produces a
*step* in the depth surface: a localized ridge of |grad| with a characteristic inflection across the
trace. Such a structure can be blind at the surface, which is exactly the class the Quaternary
surface-rupture catalogue is expected to miss, and which the competition's hidden expert labels are
described as containing. Nothing here claims that the band's physical derivation is known beyond its
embedded description; the derivative ridge is a *candidate blind-structure signature*, not an
established interpretation.

Determinism: no randomness, no labels, no scores. Inputs are read-only; outside the valid mask every
feature is exactly 0.0 and all outputs are finite float32 in [0, 1].
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter, laplace

from .potential_edges import _nearest_fill, _robust_unit_scale

STRUCT_STEP_FEATURE_NAMES = (
    "struct_cb_step_300m",
    "struct_cb_step_1000m",
    "struct_cb_curvature_1000m",
    "struct_cb_cond_concordance_1000m",
    "struct_cb_cond_orientation_agreement_1000m",
    "struct_strain_step_1000m",
)


def structural_step_features(
    depth_to_base: np.ndarray,
    cond_surf: np.ndarray,
    strain_2ndinv: np.ndarray,
    valid: np.ndarray,
    *,
    pixel_size_m: float = 100.0,
    sigmas_px: tuple[float, float] = (3.0, 10.0),
) -> np.ndarray:
    """Return six finite, zero-outside-mask structural-step features.

    ``sigmas_px=(3, 10)`` is 300 m and 1 km Gaussian smoothing on the 100 m competition grid, the
    same scales H28-1 used for the potential fields. Gradient magnitudes are independently
    robust-scaled at the in-footprint 5th/95th percentiles. The concordance and orientation-agreement
    columns are zero unless *both* 1 km gradient magnitudes are at or above their own in-footprint
    10th percentile, so a single noisy field cannot manufacture agreement.
    """
    cb = np.asarray(depth_to_base, dtype=np.float32)
    cond = np.asarray(cond_surf, dtype=np.float32)
    strain = np.asarray(strain_2ndinv, dtype=np.float32)
    mask = np.asarray(valid, dtype=bool)
    if cb.ndim != 2 or cb.shape != cond.shape or cb.shape != strain.shape or cb.shape != mask.shape:
        raise ValueError("depth_to_base, cond_surf, strain_2ndinv and valid must be same-shape 2-D")
    if cb.shape[0] < 2 or cb.shape[1] < 2:
        raise ValueError("gradients require each spatial dimension to be at least 2")
    if not np.isfinite(pixel_size_m) or pixel_size_m <= 0:
        raise ValueError("pixel_size_m must be finite and positive")
    if len(sigmas_px) != 2 or any(not np.isfinite(s) or s <= 0 for s in sigmas_px):
        raise ValueError("sigmas_px must contain two finite positive values")

    mask = mask & np.isfinite(cb) & np.isfinite(cond) & np.isfinite(strain)
    if not np.any(mask):
        raise ValueError("no cell is valid in all three structural inputs")
    cb_filled = _nearest_fill(cb, mask)
    cond_filled = _nearest_fill(cond, mask)
    strain_filled = _nearest_fill(strain, mask)

    cb_norms: list[np.ndarray] = []
    cond_norms: list[np.ndarray] = []
    cb_gradients: tuple[np.ndarray, np.ndarray] | None = None
    cond_gradients: tuple[np.ndarray, np.ndarray] | None = None
    cb_magnitudes: np.ndarray | None = None
    cond_magnitudes: np.ndarray | None = None

    for sigma in sigmas_px:
        cb_smooth = gaussian_filter(cb_filled, sigma=float(sigma), mode="nearest")
        cond_smooth = gaussian_filter(cond_filled, sigma=float(sigma), mode="nearest")
        strain_smooth = gaussian_filter(strain_filled, sigma=float(sigma), mode="nearest")
        cb_gy, cb_gx = np.gradient(cb_smooth, pixel_size_m, pixel_size_m)
        cond_gy, cond_gx = np.gradient(cond_smooth, pixel_size_m, pixel_size_m)
        cb_magnitude = np.hypot(cb_gx, cb_gy)
        cond_magnitude = np.hypot(cond_gx, cond_gy)
        cb_norms.append(_robust_unit_scale(cb_magnitude, mask))
        cond_norms.append(_robust_unit_scale(cond_magnitude, mask))
        if sigma == sigmas_px[-1]:
            cb_gradients = (cb_gx, cb_gy)
            cond_gradients = (cond_gx, cond_gy)
            cb_magnitudes = cb_magnitude
            cond_magnitudes = cond_magnitude
        if sigma == sigmas_px[-1]:
            curvature = np.abs(laplace(cb_smooth))
            strain_step = _robust_unit_scale(
                np.hypot(*np.gradient(strain_smooth, pixel_size_m, pixel_size_m)), mask
            )

    assert cb_gradients is not None and cond_gradients is not None
    assert cb_magnitudes is not None and cond_magnitudes is not None
    cb_gx, cb_gy = cb_gradients
    cond_gx, cond_gy = cond_gradients
    cb_threshold = float(np.percentile(cb_magnitudes[mask], 10.0))
    cond_threshold = float(np.percentile(cond_magnitudes[mask], 10.0))
    strong = mask & (cb_magnitudes >= cb_threshold) & (cond_magnitudes >= cond_threshold)

    cb_denom = np.maximum(cb_magnitudes, np.finfo(np.float32).tiny)
    cond_denom = np.maximum(cond_magnitudes, np.finfo(np.float32).tiny)
    orientation = np.zeros(mask.shape, dtype=np.float32)
    orientation[strong] = np.clip(
        np.abs(
            (cb_gx[strong] / cb_denom[strong]) * (cond_gx[strong] / cond_denom[strong])
            + (cb_gy[strong] / cb_denom[strong]) * (cond_gy[strong] / cond_denom[strong])
        ),
        0.0,
        1.0,
    )
    concordance = np.zeros(mask.shape, dtype=np.float32)
    concordance[strong] = np.minimum(cb_norms[-1][strong], cond_norms[-1][strong])

    stack = np.stack(
        (cb_norms[0], cb_norms[1], _robust_unit_scale(curvature, mask), concordance, orientation,
         strain_step),
        axis=0,
    ).astype(np.float32, copy=False)
    stack[:, ~mask] = 0.0
    if not np.isfinite(stack).all():
        raise ValueError("structural-step transform produced non-finite values")
    return stack
