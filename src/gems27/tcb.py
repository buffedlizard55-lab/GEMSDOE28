"""S28-TCB: two-sided directional texture-covariance boundary operator.

This module deliberately contains no catalogue access.  It works on aligned,
label-free raster layers and returns a continuous surface.  The hypothesis is
that a concealed damage zone can juxtapose materials with different directional
texture even when the amplitude of a magnetic or conductivity edge is weak.

The operator is intentionally fixed before evaluation:

* layers are robustly standardized after normalized Gaussian filling of source
  nodata cells;
* four unoriented boundary normals (cardinal and diagonal) are tested;
* at each of three fixed scales, each side's covariance is computed from three
  tangent samples after that side's local mean is removed;
* the score is the largest mean absolute correlation change over the three
  scales, then a geometric-mean fusion of RTP, TMI horizontal gradient, and
  surface conductivity.

This is a geological hypothesis, not a geothermal-vent detector.  Lithologic
contacts, intrusions, survey seams, and resampling can mimic the signal.
"""
from __future__ import annotations

from collections.abc import Mapping

import numpy as np
from scipy.ndimage import gaussian_filter

# These are a preregistered operator contract, not tuned from holdout results.
SCALES_PX: tuple[int, ...] = (2, 4, 8)
# (normal dy, normal dx, tangent dy, tangent dx), four unoriented normals.
ORIENTATIONS: tuple[tuple[int, int, int, int], ...] = (
    (0, 1, -1, 0),
    (1, 1, -1, 1),
    (1, 0, 0, 1),
    (1, -1, 1, 1),
)
EPSILON = np.float32(1.0e-6)


def _shift_no_wrap(array: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """Shift a 2-D array without the wraparound artifact of ``numpy.roll``."""
    array = np.asarray(array)
    if array.ndim != 2:
        raise ValueError("TCB shifts require a 2-D array")
    result = np.full(array.shape, np.nan, dtype=np.float32)
    h, w = array.shape
    source_y = slice(max(0, -dy), min(h, h - dy) if dy >= 0 else h)
    source_x = slice(max(0, -dx), min(w, w - dx) if dx >= 0 else w)
    dest_y = slice(max(0, dy), min(h, h + dy) if dy <= 0 else h)
    dest_x = slice(max(0, dx), min(w, w + dx) if dx <= 0 else w)
    if source_y.stop > source_y.start and source_x.stop > source_x.start:
        result[dest_y, dest_x] = array[source_y, source_x]
    return result


def robust_standardize(raw: np.ndarray, footprint: np.ndarray, *, fill_sigma: float = 3.0) -> np.ndarray:
    """Fill source nodata by normalized convolution and robustly standardize."""
    raw = np.asarray(raw, dtype=np.float32)
    footprint = np.asarray(footprint, dtype=bool)
    if raw.ndim != 2 or raw.shape != footprint.shape or not footprint.any():
        raise ValueError("TCB layer and nonempty footprint must be aligned 2-D arrays")
    valid = footprint & np.isfinite(raw)
    weights = valid.astype(np.float32)
    values = np.where(valid, raw, 0.0).astype(np.float32)
    numerator = gaussian_filter(values, fill_sigma, mode="nearest")
    denominator = gaussian_filter(weights, fill_sigma, mode="nearest")
    filled = numerator / np.maximum(denominator, np.float32(1.0e-6))
    filled = np.where(valid, raw, filled).astype(np.float32)
    sample = filled[footprint]
    median = np.float32(np.median(sample))
    mad = np.float32(1.4826 * np.median(np.abs(sample - median)))
    scale = mad if np.isfinite(mad) and mad > 0 else np.float32(np.std(sample) or 1.0)
    standardized = ((filled - median) / scale).astype(np.float32)
    # Keep the footprint boundary as missing during shifted-neighbourhood
    # calculations; treating the exterior as a physical zero would create a
    # false covariance change around the data border.
    return np.where(footprint, standardized, np.float32(np.nan)).astype(np.float32)


def _side_correlation(center: np.ndarray, tangent_minus: np.ndarray, tangent_plus: np.ndarray) -> np.ndarray:
    """Correlation of two tangent samples after side-local mean removal."""
    local_mean = (center + tangent_minus + tangent_plus) / np.float32(3.0)
    a = tangent_minus - local_mean
    b = tangent_plus - local_mean
    variance = (a * a + b * b + (center - local_mean) ** 2) / np.float32(3.0)
    return (a * b / (variance + EPSILON)).astype(np.float32)


def layer_surface(standardized: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Return the fixed TCB surface for one robustly standardized layer."""
    standardized = np.asarray(standardized, dtype=np.float32)
    footprint = np.asarray(footprint, dtype=bool)
    if standardized.shape != footprint.shape or not np.isfinite(standardized[footprint]).all():
        raise ValueError("TCB standardized input must be finite inside the footprint")
    best = np.zeros(standardized.shape, dtype=np.float32)
    for ndy, ndx, tdy, tdx in ORIENTATIONS:
        accumulated = np.zeros(standardized.shape, dtype=np.float32)
        supported = np.ones(standardized.shape, dtype=bool)
        for scale in SCALES_PX:
            normal_y, normal_x = ndy * scale, ndx * scale
            tangent_y, tangent_x = tdy * scale, tdx * scale
            plus_center = _shift_no_wrap(standardized, normal_y, normal_x)
            minus_center = _shift_no_wrap(standardized, -normal_y, -normal_x)
            plus_minus = _shift_no_wrap(
                standardized, normal_y - tangent_y, normal_x - tangent_x
            )
            plus_plus = _shift_no_wrap(
                standardized, normal_y + tangent_y, normal_x + tangent_x
            )
            minus_minus = _shift_no_wrap(
                standardized, -normal_y - tangent_y, -normal_x - tangent_x
            )
            minus_plus = _shift_no_wrap(
                standardized, -normal_y + tangent_y, -normal_x + tangent_x
            )
            finite = np.isfinite(
                np.stack(
                    (plus_center, minus_center, plus_minus, plus_plus, minus_minus, minus_plus),
                    axis=0,
                )
            ).all(axis=0)
            plus_corr = _side_correlation(plus_center, plus_minus, plus_plus)
            minus_corr = _side_correlation(minus_center, minus_minus, minus_plus)
            accumulated += np.where(finite, np.abs(plus_corr - minus_corr), 0.0)
            supported &= finite
        mean_change = accumulated / np.float32(len(SCALES_PX))
        best = np.maximum(best, np.where(supported, mean_change, 0.0))
    return np.where(footprint, np.clip(best, 0.0, 2.0), 0.0).astype(np.float32)


def robust_unit(surface: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Put one layer surface on a reproducible robust [0,1] scale."""
    surface = np.asarray(surface, dtype=np.float32)
    footprint = np.asarray(footprint, dtype=bool)
    if surface.shape != footprint.shape or not np.isfinite(surface[footprint]).all():
        raise ValueError("TCB surface and footprint must be aligned and finite inside")
    values = surface[footprint]
    upper = np.float32(np.percentile(values, 99.0))
    scale = upper if np.isfinite(upper) and upper > 0 else np.float32(1.0)
    return np.where(footprint, np.clip(surface / scale, 0.0, 1.0), 0.0).astype(np.float32)


def fuse_surfaces(surfaces: Mapping[str, np.ndarray], footprint: np.ndarray) -> np.ndarray:
    """Fuse the three preregistered layers by geometric mean."""
    footprint = np.asarray(footprint, dtype=bool)
    required = ("rtp", "tmi_hg", "cond_surf")
    if tuple(surfaces) != required:
        raise ValueError(f"TCB requires layers in order {required}")
    units = [robust_unit(surfaces[name], footprint) for name in required]
    fused = np.cbrt(units[0] * units[1] * units[2]).astype(np.float32)
    return np.where(footprint, fused, 0.0).astype(np.float32)


def build_surface(layers: Mapping[str, np.ndarray], footprint: np.ndarray) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Build the fixed TCB fused surface and its single-layer diagnostics."""
    footprint = np.asarray(footprint, dtype=bool)
    if tuple(layers) != ("rtp", "tmi_hg", "cond_surf"):
        raise ValueError("TCB layer mapping must contain rtp, tmi_hg, cond_surf in order")
    standardized = {
        name: robust_standardize(layers[name], footprint) for name in ("rtp", "tmi_hg", "cond_surf")
    }
    per_layer = {name: layer_surface(standardized[name], footprint) for name in standardized}
    return fuse_surfaces(per_layer, footprint), per_layer
