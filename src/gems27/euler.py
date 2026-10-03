"""Depth-labeled Euler-window solutions and clustered-source feature construction.

The module derives all Euler derivatives from one TMI field. It deliberately never assigns source
locations to maxima of a gradient raster; source coordinates come from the fitted Euler equations.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.fft import irfft2, rfft2
from scipy.ndimage import distance_transform_edt, gaussian_filter
from scipy.signal.windows import tukey
from scipy.spatial import cKDTree
from sklearn.cluster import DBSCAN


@dataclass(frozen=True)
class DerivativeResult:
    gx_east_per_cell: np.ndarray
    gy_north_per_cell: np.ndarray
    gz_down_per_cell: np.ndarray
    valid: np.ndarray
    horizontal_coverage: np.ndarray
    vertical_coverage: np.ndarray
    stats: dict


def _valid_values(field: np.ndarray, valid: np.ndarray, nodata: float | None) -> np.ndarray:
    out = np.asarray(valid, dtype=bool).copy() & np.isfinite(field) & (np.abs(field) < 1e30)
    if nodata is not None and np.isfinite(nodata):
        out &= np.asarray(field) != np.float32(nodata)
    return out


def _nearest_fill(field: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Nearest-valid context fill; the caller must keep filled cells out of scoring/windows."""
    if not valid.any():
        raise ValueError("Cannot fill a field with no valid cells")
    if valid.all():
        return np.asarray(field, dtype=np.float32).copy()
    indices = distance_transform_edt(~valid, return_distances=False, return_indices=True)
    filled = np.asarray(field[tuple(indices)], dtype=np.float32)
    del indices
    return filled


def magnetic_derivatives(
    field: np.ndarray,
    valid_mask: np.ndarray,
    *,
    nodata: float | None = None,
    pixel_size_m: float = 100.0,
    tile_size: int = 128,
    core_size: int = 64,
    min_tile_valid_fraction: float = 0.999,
    tukey_alpha: float = 0.25,
) -> DerivativeResult:
    """Derive east/north finite differences and a tiled Fourier downward derivative.

    Horizontal derivatives are centered differences and are marked covered only when the center and both
    neighbors in each axis are valid; one-sided or nodata-adjacent derivatives are not used in a solve.
    The vertical component is |k|T using angular wavenumber in radians per metre. It is multiplied by
    pixel_size_m so all gradient components are in field-units per grid cell. The retained central cores
    are separated by core_size pixels; tiles with less than the required valid fraction are skipped.
    Nearest-filled cells provide FFT context only and are never marked as valid observations.
    """
    raw = np.asarray(field, dtype=np.float32)
    valid = _valid_values(raw, np.asarray(valid_mask, dtype=bool), nodata)
    if raw.ndim != 2 or raw.shape != valid.shape:
        raise ValueError("field and valid_mask must be same-shape 2-D arrays")
    if tile_size <= 0 or core_size <= 0 or tile_size % 2 or tile_size < 2 * core_size:
        raise ValueError("tile_size must be even and at least twice core_size")
    if not (0.0 <= tukey_alpha <= 1.0 and 0.0 < min_tile_valid_fraction <= 1.0):
        raise ValueError("invalid Tukey alpha or valid-fraction threshold")
    if not valid.any():
        raise ValueError("no finite in-footprint magnetic field values")

    filled = _nearest_fill(raw, valid)
    gx = np.zeros(raw.shape, dtype=np.float32)
    gy = np.zeros(raw.shape, dtype=np.float32)
    horizontal_coverage = np.zeros(raw.shape, dtype=bool)
    if raw.shape[0] >= 3 and raw.shape[1] >= 3:
        x_valid = valid[:, 1:-1] & valid[:, :-2] & valid[:, 2:]
        y_valid = valid[1:-1, :] & valid[:-2, :] & valid[2:, :]
        gx[:, 1:-1] = (raw[:, 2:] - raw[:, :-2]) * np.float32(0.5)
        gy[1:-1, :] = -(raw[2:, :] - raw[:-2, :]) * np.float32(0.5)
        horizontal_coverage[1:-1, 1:-1] = x_valid[1:-1, :] & y_valid[:, 1:-1]
    gx[~horizontal_coverage] = 0.0
    gy[~horizontal_coverage] = 0.0

    height, width = raw.shape
    gz = np.zeros(raw.shape, dtype=np.float32)
    coverage = np.zeros(raw.shape, dtype=bool)
    window = tukey(tile_size, alpha=tukey_alpha).astype(np.float32)
    taper = np.outer(window, window).astype(np.float32)
    ky = 2.0 * np.pi * np.fft.fftfreq(tile_size, d=pixel_size_m)
    kx = 2.0 * np.pi * np.fft.rfftfreq(tile_size, d=pixel_size_m)
    wave_number = np.hypot(ky[:, None], kx[None, :]).astype(np.float32)
    margin = (tile_size - core_size) // 2
    core = (slice(margin, margin + core_size), slice(margin, margin + core_size))
    tile_count = 0
    accepted_tiles = 0
    threshold = int(np.ceil(min_tile_valid_fraction * tile_size * tile_size))

    for top in range(0, height - tile_size + 1, core_size):
        for left in range(0, width - tile_size + 1, core_size):
            tile_count += 1
            tile_valid = valid[top:top + tile_size, left:left + tile_size]
            if int(tile_valid.sum()) < threshold:
                continue
            tile = filled[top:top + tile_size, left:left + tile_size]
            spectrum = rfft2(tile * taper, workers=1)
            derivative = irfft2(spectrum * wave_number, s=(tile_size, tile_size), workers=1)
            r0, c0 = top + margin, left + margin
            r1, c1 = r0 + core_size, c0 + core_size
            core_valid = valid[r0:r1, c0:c1]
            target = gz[r0:r1, c0:c1]
            derivative_core = np.asarray(derivative[core], dtype=np.float32) * np.float32(pixel_size_m)
            target[core_valid] = derivative_core[core_valid]
            coverage[r0:r1, c0:c1] = core_valid
            accepted_tiles += 1

    stats = {
        "tile_size_px": int(tile_size),
        "core_size_px": int(core_size),
        "core_stride_px": int(core_size),
        "pixel_size_m": float(pixel_size_m),
        "tukey_alpha": float(tukey_alpha),
        "minimum_tile_valid_fraction": float(min_tile_valid_fraction),
        "tile_count": int(tile_count),
        "accepted_tiles": int(accepted_tiles),
        "valid_field_cells": int(valid.sum()),
        "valid_horizontal_derivative_cells": int(horizontal_coverage.sum()),
        "valid_vertical_derivative_cells": int(coverage.sum()),
        "vertical_coverage_share_of_valid_field": float(coverage.sum() / max(int(valid.sum()), 1)),
        "sign_convention": "positive north=-dT/drow; positive downward gz=|k|T in source-field units/m multiplied by 100 m/cell; source units unverified",
    }
    return DerivativeResult(gx, gy, gz, valid, horizontal_coverage, coverage, stats)


def _box_sum_stride(values: np.ndarray, window_size: int, stride: int) -> np.ndarray:
    """Summed-area-table box sums at top-left starts 0, stride, 2*stride, ... ."""
    a = np.asarray(values)
    h, w = a.shape
    if window_size > h or window_size > w:
        return np.empty((0, 0), dtype=np.float64)
    sat = np.zeros((h + 1, w + 1), dtype=np.float64)
    sat[1:, 1:] = np.cumsum(np.cumsum(a, axis=0, dtype=np.float64), axis=1, dtype=np.float64)
    sums = sat[window_size:, window_size:] - sat[:-window_size, window_size:]
    sums -= sat[window_size:, :-window_size]
    sums += sat[:-window_size, :-window_size]
    result = sums[::stride, ::stride].copy()
    del sat, sums
    return result


def _empty_solution() -> dict[str, np.ndarray | dict]:
    return {
        "row": np.empty(0, dtype=np.float64),
        "col": np.empty(0, dtype=np.float64),
        "depth_m": np.empty(0, dtype=np.float64),
        "window_row": np.empty(0, dtype=np.int32),
        "window_col": np.empty(0, dtype=np.int32),
        "condition_number": np.empty(0, dtype=np.float64),
        "relative_depth_se": np.empty(0, dtype=np.float64),
        "depth_se_m": np.empty(0, dtype=np.float64),
        "residual_rms": np.empty(0, dtype=np.float64),
        "singular_values": np.empty((0, 4), dtype=np.float64),
        "offset": np.empty(0, dtype=np.float64),
        "stats": {},
    }


def solve_euler_windows(
    field: np.ndarray,
    gx: np.ndarray,
    gy: np.ndarray,
    gz: np.ndarray,
    valid: np.ndarray,
    *,
    structural_index: float = 0.0,
    pixel_size_m: float = 100.0,
    window_size: int = 10,
    stride: int = 4,
    max_condition_number: float = 1e5,
    max_relative_depth_se: float = 0.15,
    min_depth_m: float = 100.0,
    max_depth_m: float = 3000.0,
    source_tolerance_px: float = 2.0,
) -> dict[str, np.ndarray | dict]:
    """Batch least-squares Euler deconvolution in 10x10 moving windows.

    For SI=0 the fitted fourth coefficient is the constant A offset. For SI>0 the standard SI*T term is
    included in the right-hand side and the fourth coefficient represents the corresponding base level.
    The normal-equation columns are scaled to unit norm before solving; uncertainty uses the residual
    variance and inverse normal matrix. Only fully valid windows are considered.
    """
    arrays = [np.asarray(x, dtype=np.float32) for x in (field, gx, gy, gz)]
    tmi, gxe, gyn, gzd = arrays
    mask = np.asarray(valid, dtype=bool)
    if tmi.ndim != 2 or any(a.shape != tmi.shape for a in arrays[1:]) or mask.shape != tmi.shape:
        raise ValueError("field, gradients and valid mask must be same-shape 2-D arrays")
    if structural_index < 0:
        raise ValueError("structural_index must be non-negative")
    if window_size < 4 or stride < 1:
        raise ValueError("window_size must be >=4 and stride >=1")
    if not np.isfinite(np.stack([tmi[mask], gxe[mask], gyn[mask], gzd[mask]], axis=0)).all():
        raise ValueError("non-finite values occur inside the valid Euler mask")

    h, w = tmi.shape
    if window_size > h or window_size > w:
        return _empty_solution()
    rows = np.arange(0, h - window_size + 1, stride, dtype=np.int32)
    cols = np.arange(0, w - window_size + 1, stride, dtype=np.int32)
    nr, nc = len(rows), len(cols)
    if not nr or not nc:
        return _empty_solution()
    n_obs = int(window_size * window_size)
    moments = np.zeros((nr, nc, 4, 4), dtype=np.float64)

    # Build the symmetric normal matrix for columns [east gradient, north gradient,
    # downward gradient, SI-0 offset/base-level coefficient].
    sums = {
        "gx": _box_sum_stride(gxe, window_size, stride),
        "gy": _box_sum_stride(gyn, window_size, stride),
        "gz": _box_sum_stride(gzd, window_size, stride),
    }
    for i, j in ((0, 0), (0, 1), (0, 2), (1, 1), (1, 2), (2, 2)):
        left = (gxe, gyn, gzd)[i]
        right = (gxe, gyn, gzd)[j]
        block = _box_sum_stride(left * right, window_size, stride)
        moments[:, :, i, j] = block
        moments[:, :, j, i] = block
        del block
    for axis, name in enumerate(("gx", "gy", "gz")):
        moments[:, :, axis, 3] = sums[name]
        moments[:, :, 3, axis] = sums[name]
        del sums[name]
    moments[:, :, 3, 3] = float(n_obs)
    del sums

    # Use centered map coordinates in pixel units, so solved x/y remain well-scaled.
    xcoord = np.arange(w, dtype=np.float32) - np.float32((w - 1) / 2.0)
    ycoord = np.float32((h - 1) / 2.0) - np.arange(h, dtype=np.float32)
    base_rhs = gxe * xcoord[None, :] + gyn * ycoord[:, None]
    win_valid_count = _box_sum_stride(mask.astype(np.float32), window_size, stride)
    win_valid = win_valid_count == float(n_obs)
    del win_valid_count

    column_norm = np.sqrt(np.maximum(np.diagonal(moments, axis1=2, axis2=3), 1e-30))
    scaled_moments = moments / (column_norm[:, :, :, None] * column_norm[:, :, None, :])
    eigvals = np.linalg.eigvalsh(scaled_moments)
    min_eig = eigvals[:, :, 0]
    max_eig = eigvals[:, :, -1]
    condition = np.full((nr, nc), np.inf, dtype=np.float64)
    positive_eigs = (min_eig > 1e-12) & np.isfinite(max_eig)
    condition[positive_eigs] = np.sqrt(max_eig[positive_eigs] / min_eig[positive_eigs])
    well_conditioned = win_valid & positive_eigs & (condition <= max_condition_number)
    good_flat = np.flatnonzero(well_conditioned.ravel())
    if good_flat.size == 0:
        result = _empty_solution()
        result["stats"] = {
            "structural_index": float(structural_index),
            "window_count": int(nr * nc),
            "fully_valid_windows": int(win_valid.sum()),
            "condition_pass_windows": 0,
            "depth_pass_windows": 0,
            "relative_se_pass_windows": 0,
            "source_window_pass_windows": 0,
            "accepted_solutions": 0,
            "window_size_px": int(window_size),
            "stride_px": int(stride),
        }
        return result

    # SI>0 uses the standard SI*T term; SI=0 leaves the independently fitted offset A.
    b = base_rhs + np.float32(structural_index) * np.where(mask, tmi, 0.0)
    rhs = np.empty((nr, nc, 4), dtype=np.float64)
    rhs[:, :, 0] = _box_sum_stride(gxe * b, window_size, stride)
    rhs[:, :, 1] = _box_sum_stride(gyn * b, window_size, stride)
    rhs[:, :, 2] = _box_sum_stride(gzd * b, window_size, stride)
    rhs[:, :, 3] = _box_sum_stride(b, window_size, stride)
    y2 = _box_sum_stride(b * b, window_size, stride)

    flat_norm = column_norm.reshape(-1, 4)[good_flat]
    flat_scaled = scaled_moments.reshape(-1, 4, 4)[good_flat]
    flat_rhs = rhs.reshape(-1, 4)[good_flat] / flat_norm
    beta_scaled = np.linalg.solve(flat_scaled, flat_rhs[..., None])[..., 0]
    beta = beta_scaled / flat_norm
    flat_rhs_original = rhs.reshape(-1, 4)[good_flat]
    rss = y2.ravel()[good_flat] - np.einsum("ij,ij->i", beta, flat_rhs_original)
    rss = np.maximum(rss, 0.0)
    variance = rss / max(n_obs - 4, 1)
    inverse_scaled = np.linalg.inv(flat_scaled)
    z_var = variance * inverse_scaled[:, 2, 2] / np.square(flat_norm[:, 2])
    depth_se_px = np.sqrt(np.maximum(z_var, 0.0))
    relative_se = depth_se_px / np.maximum(np.abs(beta[:, 2]), 1e-12)
    depth_m = beta[:, 2] * pixel_size_m

    wr_idx, wc_idx = np.unravel_index(good_flat, (nr, nc))
    top_row = rows[wr_idx]
    top_col = cols[wc_idx]
    source_col = beta[:, 0] + (w - 1) / 2.0
    source_row = (h - 1) / 2.0 - beta[:, 1]
    depth_pass = np.isfinite(depth_m) & (depth_m >= min_depth_m) & (depth_m <= max_depth_m)
    uncertainty_pass = np.isfinite(relative_se) & (relative_se <= max_relative_depth_se)
    x_pass = ((source_col >= top_col - source_tolerance_px)
              & (source_col <= top_col + window_size - 1 + source_tolerance_px))
    y_pass = ((source_row >= top_row - source_tolerance_px)
              & (source_row <= top_row + window_size - 1 + source_tolerance_px))
    source_pass = x_pass & y_pass
    accepted = depth_pass & uncertainty_pass & source_pass
    selected = np.flatnonzero(accepted)
    singular_values = np.sqrt(np.maximum(eigvals.reshape(-1, 4)[good_flat], 0.0))
    residual_rms = np.sqrt(rss / n_obs)
    result = {
        "row": source_row[selected].astype(np.float64),
        "col": source_col[selected].astype(np.float64),
        "depth_m": depth_m[selected].astype(np.float64),
        "window_row": top_row[selected].astype(np.int32),
        "window_col": top_col[selected].astype(np.int32),
        "condition_number": condition.ravel()[good_flat][selected].astype(np.float64),
        "relative_depth_se": relative_se[selected].astype(np.float64),
        "depth_se_m": (depth_se_px[selected] * pixel_size_m).astype(np.float64),
        "residual_rms": residual_rms[selected].astype(np.float64),
        "singular_values": singular_values[selected].astype(np.float64),
        "offset": beta[selected, 3].astype(np.float64),
        "stats": {
            "structural_index": float(structural_index),
            "window_count": int(nr * nc),
            "fully_valid_windows": int(win_valid.sum()),
            "condition_pass_windows": int(good_flat.size),
            "depth_pass_windows": int(depth_pass.sum()),
            "relative_se_pass_windows_after_depth": int((depth_pass & uncertainty_pass).sum()),
            "source_window_pass_windows_after_previous": int(accepted.sum()),
            "accepted_solutions": int(selected.size),
            "window_size_px": int(window_size),
            "stride_px": int(stride),
            "max_condition_number": float(max_condition_number),
            "max_relative_depth_se": float(max_relative_depth_se),
            "depth_range_m": [float(min_depth_m), float(max_depth_m)],
            "source_tolerance_px": float(source_tolerance_px),
        },
    }
    del moments, scaled_moments, eigvals, rhs, y2, b, base_rhs, inverse_scaled
    return result


def align_and_cluster_solutions(
    solutions: dict,
    lineament_mask: np.ndarray,
    *,
    pixel_size_m: float = 100.0,
    alignment_tolerance_m: float = 200.0,
    cluster_eps_m: float = 600.0,
    min_samples: int = 4,
    max_depth_mad_m: float = 500.0,
) -> dict:
    """Filter Euler-derived source coordinates by a ridge mask, then spatially cluster them."""
    ridge = np.asarray(lineament_mask, dtype=bool)
    rows = np.asarray(solutions["row"], dtype=np.float64)
    cols = np.asarray(solutions["col"], dtype=np.float64)
    depths = np.asarray(solutions["depth_m"], dtype=np.float64)
    if ridge.ndim != 2 or not (rows.shape == cols.shape == depths.shape):
        raise ValueError("lineament mask or solution array shape mismatch")
    ridge_rc = np.argwhere(ridge)
    if not len(ridge_rc) or not len(rows):
        return {"clusters": [], "aligned_indices": np.empty(0, np.int64),
                "stats": {"solution_count": int(len(rows)), "lineament_pixels": int(len(ridge_rc)),
                          "aligned_solution_count": 0, "dbscan_cluster_count": 0,
                          "retained_cluster_count": 0}}
    line_xy_m = ridge_rc[:, [1, 0]].astype(np.float64) * pixel_size_m
    tree = cKDTree(line_xy_m)
    source_xy_m = np.column_stack((cols, rows)) * pixel_size_m
    distances, _ = tree.query(source_xy_m, k=1, workers=1)
    aligned = np.flatnonzero(distances <= alignment_tolerance_m + 1e-9)
    if len(aligned) < min_samples:
        return {"clusters": [], "aligned_indices": aligned,
                "stats": {"solution_count": int(len(rows)), "lineament_pixels": int(len(ridge_rc)),
                          "aligned_solution_count": int(len(aligned)), "dbscan_cluster_count": 0,
                          "retained_cluster_count": 0}}
    labels = DBSCAN(eps=cluster_eps_m, min_samples=min_samples, algorithm="kd_tree", n_jobs=1).fit_predict(
        source_xy_m[aligned]
    )
    cluster_ids = np.unique(labels[labels >= 0])
    clusters = []
    for cluster_id in cluster_ids:
        member_local = np.flatnonzero(labels == cluster_id)
        member_indices = aligned[member_local]
        cluster_depths = depths[member_indices]
        med_depth = float(np.median(cluster_depths))
        mad_depth = float(np.median(np.abs(cluster_depths - med_depth)))
        if mad_depth > max_depth_mad_m:
            continue
        clusters.append({
            "cluster_id": int(cluster_id),
            "member_indices": member_indices.astype(np.int64),
            "n_solutions": int(len(member_indices)),
            "row": float(np.median(rows[member_indices])),
            "col": float(np.median(cols[member_indices])),
            "median_depth_m": med_depth,
            "depth_mad_m": mad_depth,
            "depth_min_m": float(np.min(cluster_depths)),
            "depth_max_m": float(np.max(cluster_depths)),
            "median_depth_se_m": float(np.median(np.asarray(solutions["depth_se_m"])[member_indices])),
        })
    return {
        "clusters": clusters,
        "aligned_indices": aligned.astype(np.int64),
        "stats": {
            "solution_count": int(len(rows)),
            "lineament_pixels": int(len(ridge_rc)),
            "alignment_tolerance_m": float(alignment_tolerance_m),
            "aligned_solution_count": int(len(aligned)),
            "dbscan_cluster_count": int(len(cluster_ids)),
            "retained_cluster_count": int(len(clusters)),
            "cluster_eps_m": float(cluster_eps_m),
            "min_samples": int(min_samples),
            "max_depth_mad_m": float(max_depth_mad_m),
        },
    }


def cluster_feature_maps(
    solutions: dict,
    cluster_result: dict,
    valid: np.ndarray,
    *,
    sigma_px: float = 2.0,
    max_depth_m: float = 3000.0,
) -> tuple[np.ndarray, dict]:
    """Create the three preregistered normalized, smoothed raster features from retained clusters."""
    mask = np.asarray(valid, dtype=bool)
    h, w = mask.shape
    count = np.zeros((h, w), dtype=np.float32)
    shallow = np.zeros((h, w), dtype=np.float32)
    depth_num = np.zeros((h, w), dtype=np.float32)
    depth_den = np.zeros((h, w), dtype=np.float32)
    source_rows = np.asarray(solutions["row"], dtype=np.float64)
    source_cols = np.asarray(solutions["col"], dtype=np.float64)
    retained_members = 0
    for cluster in cluster_result["clusters"]:
        members = np.asarray(cluster["member_indices"], dtype=np.int64)
        if not len(members):
            continue
        rr = np.rint(source_rows[members]).astype(np.int64)
        cc = np.rint(source_cols[members]).astype(np.int64)
        inside = (rr >= 0) & (rr < h) & (cc >= 0) & (cc < w)
        inside &= mask[np.clip(rr, 0, h - 1), np.clip(cc, 0, w - 1)]
        rr, cc = rr[inside], cc[inside]
        if not len(rr):
            continue
        member_depths_m = np.asarray(solutions["depth_m"], dtype=np.float64)[members][inside]
        shallow_weights = np.clip(1.0 - member_depths_m / max_depth_m, 0.0, 1.0).astype(np.float32)
        cluster_depth_km = np.float32(cluster["median_depth_m"] / 1000.0)
        np.add.at(count, (rr, cc), 1.0)
        np.add.at(shallow, (rr, cc), shallow_weights)
        np.add.at(depth_num, (rr, cc), cluster_depth_km)
        np.add.at(depth_den, (rr, cc), 1.0)
        retained_members += int(len(rr))

    smooth_count = gaussian_filter(count, sigma=sigma_px, mode="constant", cval=0.0)
    smooth_shallow = gaussian_filter(shallow, sigma=sigma_px, mode="constant", cval=0.0)
    smooth_depth_num = gaussian_filter(depth_num, sigma=sigma_px, mode="constant", cval=0.0)
    smooth_depth_den = gaussian_filter(depth_den, sigma=sigma_px, mode="constant", cval=0.0)
    support_feature = np.clip(np.log1p(smooth_count) / np.log1p(5.0), 0.0, 1.0)
    shallow_feature = np.clip(np.log1p(smooth_shallow) / np.log1p(5.0), 0.0, 1.0)
    depth_feature = np.zeros((h, w), dtype=np.float32)
    has_depth = smooth_depth_den > 1e-12
    depth_feature[has_depth] = smooth_depth_num[has_depth] / smooth_depth_den[has_depth] / 3.0
    features = np.stack((support_feature, shallow_feature, np.clip(depth_feature, 0, 1)), axis=-1).astype(np.float32)
    features[~mask] = 0.0
    if not np.isfinite(features).all() or features.min() < 0.0 or features.max() > 1.0:
        raise ValueError("Euler cluster feature values escaped finite [0,1]")
    names = ["euler_si0_cluster_support", "euler_si0_shallow_support", "euler_si0_median_depth_norm"]
    return features, {
        "feature_names": names,
        "shape": list(features.shape),
        "dtype": str(features.dtype),
        "sigma_px": float(sigma_px),
        "max_depth_m": float(max_depth_m),
        "retained_member_solutions": int(retained_members),
        "cluster_count": int(len(cluster_result["clusters"])),
        "values": "finite [0,1]; outside/invalid zero",
        "sha256": None,
    }
