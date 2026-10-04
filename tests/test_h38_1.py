import numpy as np
import pytest

from gems27.h38_1 import candidate_support_mask, selected_cluster_rows


def test_candidate_support_uses_independent_gradient_corridor_and_valid_low_relief():
    footprint = np.ones((5, 5), dtype=bool)
    gravity = np.arange(25, dtype=np.float32).reshape(5, 5)
    relief = np.full((5, 5), 10, dtype=np.uint8)
    relief[0, 0] = 250  # above the lower-half cutoff
    lidar_valid = np.ones((5, 5), dtype=bool)
    lidar_valid[3, 3] = False

    support, audit = candidate_support_mask(
        gravity, relief, lidar_valid, footprint,
        gravity_quantile=0.80, relief_quantile=0.50, radius_px=1.0,
    )

    # The P80 gravity cells are in the last row; the one-pixel Euclidean corridor includes row 3.
    assert audit["gravity_threshold"] == pytest.approx(19.2)
    assert audit["gravity_high_cells"] == 5
    assert support[3, 0]
    assert not support[2, 0]
    assert not support[3, 3]  # LiDAR invalid even though within the gravity corridor
    assert not support[0, 0]  # low-relief condition fails
    assert support[4, 0]  # row 4 is within both masks
    assert audit["joint_support_cells"] == int(support.sum())


def test_candidate_support_excludes_outside_footprint_and_bad_gravity():
    footprint = np.ones((4, 4), dtype=bool)
    footprint[:, 0] = False
    gravity = np.arange(16, dtype=np.float32).reshape(4, 4)
    gravity[1, 1] = np.nan
    relief = np.ones((4, 4), dtype=np.uint8)
    valid = np.ones((4, 4), dtype=bool)
    valid[2, 2] = False

    support, audit = candidate_support_mask(gravity, relief, valid, footprint, radius_px=0.0)
    assert not support[:, 0].any()
    assert not support[2, 2]
    assert audit["gravity_valid_cells"] == int((footprint & np.isfinite(gravity)).sum())
    assert audit["relief_valid_cells"] == int((footprint & valid).sum())


def test_candidate_support_rejects_grid_mismatch_and_empty_population():
    with pytest.raises(ValueError, match="same grid"):
        candidate_support_mask(np.ones((2, 2)), np.ones((2, 3)), np.ones((2, 2)), np.ones((2, 2)))
    with pytest.raises(ValueError, match="no valid LiDAR"):
        candidate_support_mask(np.ones((2, 2)), np.ones((2, 2)), np.zeros((2, 2)), np.ones((2, 2)))


def _cluster(row, col, mad=60, depth=400, n=8):
    return {
        "row": str(row), "col": str(col), "median_depth_m": str(depth),
        "depth_mad_m": str(mad), "n_solutions": str(n),
    }


def test_euler_selection_keeps_inclusive_depth_limits_and_spatial_conjunction():
    support = np.zeros((4, 4), dtype=bool)
    support[1, 2] = True
    rows = [
        _cluster(1, 2),                  # all inclusive limits pass
        _cluster(1, 3),                  # spatial condition fails
        _cluster(1, 2, mad=60.01),       # depth MAD fails
        _cluster(1, 2, depth=400.01),     # depth fails
        _cluster(1, 2, n=7),             # solution support fails
    ]
    chosen, counts = selected_cluster_rows(rows, support)
    assert len(chosen) == 1
    assert chosen[0]["row"] == "1"
    assert counts == {
        "input_cluster_rows": 5,
        "depth_eligible_clusters": 2,
        "selected_clusters": 1,
        "minimum_candidates_for_holdout": 100,
        "sufficiency": "INSUFFICIENT",
    }


def test_euler_selection_rejects_duplicate_rounded_coordinates_and_out_of_grid():
    support = np.ones((4, 4), dtype=bool)
    with pytest.raises(ValueError, match="duplicate"):
        selected_cluster_rows([_cluster(1.1, 2.1), _cluster(1.2, 2.2)], support)
    with pytest.raises(ValueError, match="outside grid"):
        selected_cluster_rows([_cluster(10, 2)], support)
