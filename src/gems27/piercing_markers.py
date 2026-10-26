"""Displaced potential-field piercing-marker registration (Session 22).

The transform is deliberately label- and catalogue-free.  It scores a corridor when
band-pass patches on opposite sides match better after a non-zero along-strike shift
than under an undisplaced continuation.  See ``knowledge/62_s22_preregistration.md``.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter, uniform_filter

FAULT_STRIKES: tuple[tuple[int, int], ...] = ((0, 1), (1, 1), (1, 0), (1, -1))
SHIFT_DISTANCES_PX: tuple[int, ...] = (-6, -4, -2, 2, 4, 6)
BANDPASS_SCALES: tuple[tuple[float, float], ...] = ((1.0, 8.0), (2.0, 12.0))
SIDE_OFFSET_PX = 3.0
NCC_WINDOW_PX = 9
MIN_SPACING_PX = 2.8


@dataclass
class PatchMap:
    """Band-pass field and precomputed local statistics/support."""

    band: np.ndarray
    support: np.ndarray
    local_mean: np.ndarray
    local_var: np.ndarray


def nearest_fill(values: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Nearest-fill a finite physical field for boundary-clean filtering."""
    values = np.asarray(values, dtype=np.float32)
    valid = np.asarray(valid, dtype=bool) & np.isfinite(values)
    if values.ndim != 2 or valid.shape != values.shape or not valid.any():
        raise ValueError("nearest_fill requires an aligned nonempty finite 2-D support")
    if valid.all():
        return values.copy()
    indices = distance_transform_edt(~valid, return_distances=False, return_indices=True)
    return values[tuple(indices)].astype(np.float32, copy=False)


def robust_standardize(values: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """Median/IQR scaling clipped to [-5,5], with no label-derived quantities."""
    values = np.asarray(values, dtype=np.float32)
    mask = np.asarray(mask, dtype=bool) & np.isfinite(values)
    if values.ndim != 2 or mask.shape != values.shape or not mask.any():
        raise ValueError("robust_standardize requires finite values on a nonempty mask")
    q25, median, q75 = np.percentile(values[mask], [25.0, 50.0, 75.0])
    scale = max(float(q75 - q25) / 1.349, 1e-6)
    return np.clip((values - float(median)) / scale, -5.0, 5.0).astype(np.float32)


def robust_unit(values: np.ndarray, mask: np.ndarray, quantile: float = 99.0) -> np.ndarray:
    """Scale a nonnegative support field to [0,1] by a fixed robust upper quantile."""
    values = np.maximum(np.asarray(values, dtype=np.float32), 0.0)
    mask = np.asarray(mask, dtype=bool) & np.isfinite(values)
    if values.ndim != 2 or mask.shape != values.shape or not mask.any():
        raise ValueError("robust_unit requires finite values on a nonempty mask")
    high = float(np.percentile(values[mask], quantile))
    out = np.zeros_like(values, dtype=np.float32)
    if high > 1e-12:
        out[mask] = np.clip(values[mask] / high, 0.0, 1.0)
    return out


def prepare_patch_maps(values: np.ndarray, footprint: np.ndarray) -> list[PatchMap]:
    """Create the two frozen band-pass scales and local NCC moments for one modality."""
    footprint = np.asarray(footprint, dtype=bool)
    filled = nearest_fill(values, footprint & np.isfinite(values))
    field = robust_standardize(filled, footprint)
    maps: list[PatchMap] = []
    for fine_sigma, broad_sigma in BANDPASS_SCALES:
        fine = gaussian_filter(field, fine_sigma, mode="nearest")
        broad = gaussian_filter(field, broad_sigma, mode="nearest")
        band = (fine - broad).astype(np.float32)
        del fine, broad
        gy, gx = np.gradient(band)
        support = robust_unit(np.hypot(gx, gy), footprint)
        del gy, gx
        mean = uniform_filter(band, size=NCC_WINDOW_PX, mode="nearest")
        second = uniform_filter(band * band, size=NCC_WINDOW_PX, mode="nearest")
        variance = np.maximum(second - mean * mean, 0.0).astype(np.float32)
        del second
        maps.append(PatchMap(band=band, support=support, local_mean=mean, local_var=variance))
    return maps


def realized_offset(direction: tuple[int, int], distance_px: float) -> tuple[int, int]:
    """Integer grid offset nearest to a requested Euclidean distance along a direction."""
    dy, dx = direction
    norm = float(np.hypot(dy, dx))
    if norm == 0 or not np.isfinite(distance_px):
        raise ValueError("A nonzero direction and finite distance are required")
    return int(round(distance_px * dy / norm)), int(round(distance_px * dx / norm))


def shift_nearest(values: np.ndarray, dy: int, dx: int) -> np.ndarray:
    """Integer translate with nearest-edge extension; positive offsets move content down/right."""
    values = np.asarray(values)
    if values.ndim != 2:
        raise ValueError("shift_nearest requires a 2-D array")
    rows = np.clip(np.arange(values.shape[0], dtype=np.int32) - int(dy), 0, values.shape[0] - 1)
    cols = np.clip(np.arange(values.shape[1], dtype=np.int32) - int(dx), 0, values.shape[1] - 1)
    return values[np.ix_(rows, cols)]


def _ncc_for_offsets(patch: PatchMap, left_offset: tuple[int, int], right_offset: tuple[int, int]) -> np.ndarray:
    """Local normalized correlation using shifted precomputed first/second moments."""
    ay, ax = left_offset
    by, bx = right_offset
    left = shift_nearest(patch.band, ay, ax)
    right = shift_nearest(patch.band, by, bx)
    mean_left = shift_nearest(patch.local_mean, ay, ax)
    mean_right = shift_nearest(patch.local_mean, by, bx)
    var_left = shift_nearest(patch.local_var, ay, ax)
    var_right = shift_nearest(patch.local_var, by, bx)
    cross = uniform_filter(left * right, size=NCC_WINDOW_PX, mode="nearest")
    denominator = np.sqrt(np.maximum(var_left * var_right, 0.0))
    result = np.zeros_like(cross, dtype=np.float32)
    stable = denominator > 1e-6
    result[stable] = np.clip(
        (cross[stable] - mean_left[stable] * mean_right[stable]) / denominator[stable],
        -1.0,
        1.0,
    )
    return result


def iter_shift_evidence(patch: PatchMap, strike: tuple[int, int]) -> Iterator[tuple[int, np.ndarray]]:
    """Yield evidence for every frozen non-zero displacement at one scale/orientation."""
    sy, sx = strike
    normal = (-sx, sy)
    left_offset = realized_offset(normal, SIDE_OFFSET_PX)
    right_base = realized_offset(normal, -SIDE_OFFSET_PX)
    ncc_zero = _ncc_for_offsets(patch, left_offset, right_base)
    left_support = shift_nearest(patch.support, *left_offset)
    for distance in SHIFT_DISTANCES_PX:
        along = realized_offset(strike, float(distance))
        right_offset = (right_base[0] + along[0], right_base[1] + along[1])
        ncc_shifted = _ncc_for_offsets(patch, left_offset, right_offset)
        right_support = shift_nearest(patch.support, *right_offset)
        gain = np.maximum(ncc_shifted - ncc_zero, 0.0)
        evidence = gain * np.sqrt(np.maximum(left_support * right_support, 0.0))
        yield distance, np.clip(evidence, 0.0, 1.0).astype(np.float32)


def _persistent_by_shift(scale_maps: list[PatchMap], strike: tuple[int, int]) -> list[np.ndarray]:
    if len(scale_maps) != 2:
        raise ValueError("The frozen S22 transform requires exactly two band-pass scales")
    first = [(distance, evidence.astype(np.float16)) for distance, evidence in iter_shift_evidence(scale_maps[0], strike)]
    output: list[np.ndarray] = []
    for (distance_a, evidence_a), (distance_b, evidence_b) in zip(
        first, iter_shift_evidence(scale_maps[1], strike), strict=True
    ):
        if distance_a != distance_b:
            raise AssertionError("Frozen displacement order changed between scales")
        persistent = np.sqrt(
            evidence_a.astype(np.float32) * np.maximum(evidence_b, 0.0)
        ).astype(np.float32)
        output.append(persistent)
    return output


def build_surface(
    rtp: np.ndarray,
    iso_gravity: np.ndarray,
    footprint: np.ndarray,
) -> tuple[dict[str, np.ndarray], dict]:
    """Build magnetic, gravity and fused displaced-marker evidence surfaces."""
    footprint = np.asarray(footprint, dtype=bool)
    if rtp.shape != footprint.shape or iso_gravity.shape != footprint.shape or not footprint.any():
        raise ValueError("Physical fields and footprint must be aligned nonempty 2-D grids")
    magnetic_maps = prepare_patch_maps(rtp, footprint)
    gravity_maps = prepare_patch_maps(iso_gravity, footprint)
    magnetic_max = np.zeros(footprint.shape, dtype=np.float32)
    gravity_max = np.zeros(footprint.shape, dtype=np.float32)
    fused_max = np.zeros(footprint.shape, dtype=np.float32)
    realized: list[dict] = []

    for strike in FAULT_STRIKES:
        magnetic = _persistent_by_shift(magnetic_maps, strike)
        gravity = _persistent_by_shift(gravity_maps, strike)
        for distance, mag, grav in zip(SHIFT_DISTANCES_PX, magnetic, gravity, strict=True):
            magnetic_max = np.maximum(magnetic_max, mag)
            gravity_max = np.maximum(gravity_max, grav)
            fused = 0.70 * np.sqrt(np.maximum(mag * grav, 0.0)) + 0.30 * np.maximum(mag, grav)
            fused_max = np.maximum(fused_max, fused.astype(np.float32))
            realized.append(
                {
                    "strike": list(strike),
                    "requested_shift_px": distance,
                    "realized_shift": list(realized_offset(strike, float(distance))),
                }
            )
        del magnetic, gravity

    for surface in (magnetic_max, gravity_max, fused_max):
        surface[~footprint] = 0.0
    fused_scaled = robust_unit(fused_max, footprint, quantile=99.5)
    return {
        "magnetic_displacement": magnetic_max,
        "gravity_displacement": gravity_max,
        "candidate": fused_scaled,
    }, {
        "fault_strikes": [list(v) for v in FAULT_STRIKES],
        "requested_shifts_px": list(SHIFT_DISTANCES_PX),
        "side_offset_px": SIDE_OFFSET_PX,
        "ncc_window_px": NCC_WINDOW_PX,
        "bandpass_scales": [list(v) for v in BANDPASS_SCALES],
        "realized_integer_offsets": realized,
        "surface_range": [float(fused_scaled[footprint].min()), float(fused_scaled[footprint].max())],
        "positive_surface_pixels": int((fused_scaled[footprint] > 0).sum()),
    }


def greedy_place(
    surface: np.ndarray,
    eligible: np.ndarray,
    target: int,
    *,
    min_spacing_px: float = MIN_SPACING_PX,
) -> np.ndarray:
    """Stable score-ordered Poisson placement without reading any prior raster."""
    surface = np.asarray(surface, dtype=np.float32)
    eligible = np.asarray(eligible, dtype=bool)
    if surface.ndim != 2 or eligible.shape != surface.shape:
        raise ValueError("surface and eligibility must be aligned 2-D grids")
    if target < 0 or not np.isfinite(min_spacing_px) or min_spacing_px <= 0:
        raise ValueError("target must be nonnegative and spacing positive")
    allowed = np.flatnonzero(eligible.ravel() & np.isfinite(surface.ravel()) & (surface.ravel() > 0))
    out = np.zeros(surface.shape, dtype=bool)
    if target == 0 or not len(allowed):
        return out
    # Stable sorting makes row-major index the declared tie-break.
    order = allowed[np.argsort(-surface.ravel()[allowed], kind="stable")]
    blocked = np.zeros(surface.size, dtype=bool)
    radius = int(np.ceil(min_spacing_px))
    offsets = [
        (dy, dx)
        for dy in range(-radius, radius + 1)
        for dx in range(-radius, radius + 1)
        if dy * dy + dx * dx < min_spacing_px * min_spacing_px
    ]
    selected: list[int] = []
    height, width = surface.shape
    for flat in order:
        flat = int(flat)
        if blocked[flat]:
            continue
        selected.append(flat)
        row, col = divmod(flat, width)
        for dy, dx in offsets:
            yy, xx = row + dy, col + dx
            if 0 <= yy < height and 0 <= xx < width:
                blocked[yy * width + xx] = True
        if len(selected) == target:
            break
    if selected:
        out.ravel()[np.asarray(selected, dtype=np.int64)] = True
    return out
