import numpy as np
from scipy.ndimage import gaussian_filter

from gems27.euler import (
    align_and_cluster_solutions,
    cluster_feature_maps,
    magnetic_derivatives,
    solve_euler_windows,
)


def _synthetic_homogeneous_field(structural_index: int, shape=(41, 41), source=(20.0, 18.0), depth=12.0):
    h, w = shape
    row, col = np.mgrid[:h, :w]
    x = col.astype(float)
    y = -row.astype(float)
    xs, ys = source[1], -source[0]
    dx = x - xs
    dy = y - ys
    r2 = dx * dx + dy * dy + depth * depth
    if structural_index == 1:
        t = 1.0 / np.sqrt(r2) + 5.0
        gx = -dx / r2**1.5
        gy = -dy / r2**1.5
        gz = depth / r2**1.5
    elif structural_index == 0:
        t = np.arctan2(dx, depth) + np.arctan2(dy, depth) + 7.0
        gx = depth / (depth * depth + dx * dx)
        gy = depth / (depth * depth + dy * dy)
        gz = dx / (depth * depth + dx * dx) + dy / (depth * depth + dy * dy)
    else:
        raise ValueError(structural_index)
    return t.astype(np.float32), gx.astype(np.float32), gy.astype(np.float32), gz.astype(np.float32)


def test_si0_four_unknown_solution_recovers_depth_and_source():
    t, gx, gy, gz = _synthetic_homogeneous_field(0)
    result = solve_euler_windows(t, gx, gy, gz, np.ones(t.shape, bool), structural_index=0)
    assert result["stats"]["accepted_solutions"] > 0
    assert np.min(np.abs(result["depth_m"] - 1200.0)) < 1e-2
    assert np.min(np.hypot(result["row"] - 20.0, result["col"] - 18.0)) < 1e-2
    assert result["singular_values"].shape[1] == 4
    assert result["offset"].shape == result["depth_m"].shape
    assert np.isfinite(result["offset"]).all()
    assert np.all(result["relative_depth_se"] <= 0.15)


def test_euler_solution_is_invariant_to_constant_field_unit_conversion():
    t, gx, gy, gz = _synthetic_homogeneous_field(0)
    base = solve_euler_windows(t, gx, gy, gz, np.ones(t.shape, bool), structural_index=0)
    scale = 1000.0
    converted = solve_euler_windows(
        t * scale, gx * scale, gy * scale, gz * scale,
        np.ones(t.shape, bool), structural_index=0,
    )
    assert len(base["depth_m"]) == len(converted["depth_m"])
    np.testing.assert_allclose(converted["row"], base["row"], atol=1e-3, rtol=1e-6)
    np.testing.assert_allclose(converted["col"], base["col"], atol=1e-3, rtol=1e-6)
    np.testing.assert_allclose(converted["depth_m"], base["depth_m"], atol=1e-3, rtol=1e-6)


def test_si1_standard_si_times_t_term_recovers_depth():
    t, gx, gy, gz = _synthetic_homogeneous_field(1)
    result = solve_euler_windows(t, gx, gy, gz, np.ones(t.shape, bool), structural_index=1)
    assert result["stats"]["accepted_solutions"] > 0
    assert np.min(np.abs(result["depth_m"] - 1200.0)) < 0.5
    assert np.min(np.hypot(result["row"] - 20.0, result["col"] - 18.0)) < 0.1


def test_tiled_fourier_derivative_is_positive_down_and_keeps_only_valid_core():
    n = 128
    x = np.arange(n, dtype=np.float32)[None, :]
    field = np.broadcast_to(np.cos(2.0 * np.pi * x / 32.0), (n, n)).copy()
    valid = np.ones((n, n), dtype=bool)
    valid[40:42, 40:42] = False
    result = magnetic_derivatives(field, valid, tile_size=128, core_size=64)
    expected = (2.0 * np.pi / 32.0) * field * 1.0  # k * 100 m/cell, with 100 m cells
    core = np.s_[32:96, 32:96]
    ok = result.vertical_coverage[core]
    z = result.gz_down_per_cell[core][ok]
    e = expected[core][ok]
    corr = np.corrcoef(z.ravel(), e.ravel())[0, 1]
    assert corr > 0.98
    assert result.vertical_coverage.sum() == 64 * 64 - 4
    assert np.all(result.gz_down_per_cell[~result.vertical_coverage] == 0)
    assert not result.horizontal_coverage[40, 39]
    assert result.gx_east_per_cell[40, 39] == 0.0
    assert result.stats["valid_horizontal_derivative_cells"] == int(result.horizontal_coverage.sum())


def test_horizontal_differences_never_use_nearest_filled_nodata_neighbors():
    row, col = np.mgrid[:128, :128]
    field = (2.0 * col + 3.0 * row).astype(np.float32)
    valid = np.ones(field.shape, dtype=bool)
    valid[64, 64] = False
    result = magnetic_derivatives(field, valid)
    assert result.horizontal_coverage[50, 50]
    assert result.gx_east_per_cell[50, 50] == 2.0
    assert result.gy_north_per_cell[50, 50] == -3.0
    for rc in ((64, 63), (64, 65), (63, 64), (65, 64)):
        assert not result.horizontal_coverage[rc]
        assert result.gx_east_per_cell[rc] == 0.0
        assert result.gy_north_per_cell[rc] == 0.0


def test_euler_locations_not_gradient_ridge_peaks_are_clustered_and_depth_labeled():
    h = w = 32
    ridge = np.zeros((h, w), dtype=bool)
    ridge[15, 5:28] = True
    solutions = {
        "row": np.array([14.9, 15.2, 15.1, 15.0, 15.3]),
        "col": np.array([12.0, 13.0, 14.0, 15.0, 16.0]),
        "depth_m": np.array([700.0, 720.0, 710.0, 705.0, 715.0]),
        "depth_se_m": np.array([60.0, 62.0, 61.0, 59.0, 60.0]),
    }
    cluster_result = align_and_cluster_solutions(solutions, ridge)
    assert cluster_result["stats"]["aligned_solution_count"] == 5
    assert cluster_result["stats"]["retained_cluster_count"] == 1
    cluster = cluster_result["clusters"][0]
    assert abs(cluster["median_depth_m"] - 710.0) < 1e-6
    assert abs(cluster["col"] - 14.0) < 1e-6
    features, metadata = cluster_feature_maps(solutions, cluster_result, np.ones((h, w), bool))
    assert features.shape == (h, w, 3)
    assert metadata["feature_names"] == [
        "euler_si0_cluster_support", "euler_si0_shallow_support", "euler_si0_median_depth_norm"
    ]
    assert np.isfinite(features).all() and features.min() >= 0 and features.max() <= 1
    assert features[:, :3, :].sum() == 0.0
    raw_shallow = np.zeros((h, w), dtype=np.float32)
    rr = np.rint(solutions["row"]).astype(int)
    cc = np.rint(solutions["col"]).astype(int)
    weights = np.clip(1.0 - solutions["depth_m"] / 3000.0, 0.0, 1.0)
    np.add.at(raw_shallow, (rr, cc), weights)
    expected_shallow = np.clip(
        np.log1p(gaussian_filter(raw_shallow, sigma=2.0, mode="constant", cval=0.0)) / np.log1p(5.0),
        0.0, 1.0,
    )
    np.testing.assert_allclose(features[:, :, 1], expected_shallow, atol=1e-7, rtol=1e-6)
