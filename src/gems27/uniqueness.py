"""Dot-level uniqueness checks for competition rasters (protocol gate, session S30).

Gate definitions (from the parallel-run protocol in the repository README):
  * DUPLICATE if more than 70% of a candidate's dots lie within 3 px (Euclidean) of one registry raster's dots.
  * DUPLICATE if rank correlation with a registry raster exceeds 0.90 (checked on the raster values inside
    the footprint; for a binary dot raster the rank correlation is structurally tied and reported as such).

All functions operate on the competition grid (grid.SHAPE, footprint from grid.load_footprint).
"""
from __future__ import annotations

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from scipy.stats import spearmanr

from . import grid

OVERLAP_RADIUS_PX = 3.0
DUPLICATE_OVERLAP = 0.70
DUPLICATE_RANK_CORR = 0.90


def load_values(path, footprint: np.ndarray) -> np.ndarray:
    """Return the raster values inside the footprint as float64, NaN-safe (NaN/outside are dropped by caller)."""
    with rasterio.open(path) as src:
        if src.shape != footprint.shape:
            raise ValueError(f"{path}: shape {src.shape} != grid {footprint.shape}")
        arr = src.read(1).astype(np.float64)
    return arr


def dot_mask(values: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Binary dot set: finite values > 0.5 inside the footprint. Raises if any inside value is outside [0,1]."""
    inside = values[footprint]
    finite = np.isfinite(inside)
    if not finite.all():
        raise ValueError("non-finite values inside the footprint")
    if inside.min() < 0.0 or inside.max() > 1.0:
        raise ValueError("values outside [0,1] inside the footprint")
    return (np.where(np.isfinite(values), values, 0.0) > 0.5) & footprint


def registry_dot_mask(values: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Dot set of a REGISTRY reference raster: non-finite cells count as no dot (format defects are logged
    elsewhere); finite cells > 0.5 inside the footprint are dots. Never used to validate a candidate."""
    v = np.where(np.isfinite(values), values, 0.0)
    return (v > 0.5) & footprint


def distance_to_dots(dots: np.ndarray) -> np.ndarray:
    """Euclidean distance (pixels) from every grid cell to the nearest dot. Empty dot set -> +inf."""
    if not dots.any():
        return np.full(dots.shape, np.inf)
    return distance_transform_edt(~dots)


def fraction_within(candidate: np.ndarray, reference: np.ndarray, radius: float = OVERLAP_RADIUS_PX) -> float:
    """Fraction of candidate dots lying within `radius` px of at least one reference dot."""
    n = int(candidate.sum())
    if n == 0:
        return 0.0
    d = distance_to_dots(reference)
    return float(np.mean(d[candidate] <= radius))


def rank_correlation(a_values: np.ndarray, b_values: np.ndarray, footprint: np.ndarray) -> float:
    """Spearman rank correlation of two rasters inside the footprint (binary inputs give tied ranks)."""
    a = a_values[footprint]
    b = b_values[footprint]
    rho, _ = spearmanr(a, b)
    return float(rho)


def is_duplicate(overlap: float, rank_corr: float | None = None) -> bool:
    if overlap > DUPLICATE_OVERLAP:
        return True
    return rank_corr is not None and abs(rank_corr) > DUPLICATE_RANK_CORR


__all__ = [
    "OVERLAP_RADIUS_PX", "DUPLICATE_OVERLAP", "DUPLICATE_RANK_CORR", "load_values", "dot_mask", "registry_dot_mask",
    "distance_to_dots", "fraction_within", "rank_correlation", "is_duplicate", "grid",
]
