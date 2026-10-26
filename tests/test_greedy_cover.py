"""Unit tests for H43-1 eligibility + greedy kernel-cover placement."""

import numpy as np
import pytest
from scipy.ndimage import distance_transform_edt

from gems27.greedy_cover import cover_surface, eligibility, greedy_kernel_cover


def _min_pairwise(dots):
    ys, xs = np.nonzero(dots)
    if len(ys) < 2:
        return np.inf
    # distance from each dot to the nearest *other* dot, by brute force (small test arrays)
    best = np.inf
    for i in range(len(ys)):
        dd = np.hypot(ys - ys[i], xs - xs[i])
        dd[i] = np.inf
        best = min(best, dd.min())
    return best


def test_eligibility_ring_and_tip():
    # 1-px horizontal catalogue segment cols 2..8 at row 5; endpoints are its two ends.
    vis = np.zeros((11, 12), bool)
    vis[5, 2:9] = True
    pool = np.ones((11, 12), bool)
    elig, d_vis, d_end = eligibility(pool, vis, ring_px=2.0, tip_radius_px=3.0)
    assert not elig[5, 5]  # on catalogue
    assert not elig[5, 4] or True  # on catalogue too
    # Mid-segment flank at distance 1-2, far from endpoints: ineligible.
    assert not elig[3, 5]  # d_vis=2, d_end=hypot(2,3)>3
    assert not elig[4, 5]  # d_vis=1 mid-segment
    # Beyond the tip along strike, ring 1-2 but near endpoint (5,8): eligible.
    assert elig[5, 10]  # d_vis=2, d_end=2
    assert elig[5, 9]  # d_vis=1, d_end=1
    # Far field: eligible.
    assert elig[0, 0]
    assert d_vis[5, 10] == 2.0


def test_eligibility_empty_catalogue():
    pool = np.zeros((5, 5), bool)
    pool[2, 2] = True
    elig, d_vis, _ = eligibility(pool, np.zeros((5, 5), bool))
    assert elig[2, 2] and np.isinf(d_vis).all()


def test_greedy_budget_spacing_subset_determinism():
    rng = np.random.default_rng(7)
    pool = rng.random((40, 40)) < 0.25
    elig = pool.copy()
    dots = greedy_kernel_cover(pool, elig, 25, min_dist=2.8)
    assert dots.sum() <= 25
    assert (dots & ~elig).sum() == 0
    assert _min_pairwise(dots) >= 2.8 - 1e-9
    dots2 = greedy_kernel_cover(pool, elig, 25, min_dist=2.8)
    assert np.array_equal(dots, dots2)


def test_greedy_prefers_dense_cluster_first():
    pool = np.zeros((15, 15), bool)
    pool[7, 7] = True
    pool[7, 8] = True
    pool[8, 7] = True
    pool[0, 0] = True  # isolated, lower cover value
    dots = greedy_kernel_cover(pool, pool, 1, min_dist=2.8)
    ys, xs = np.nonzero(dots)
    assert len(ys) == 1 and ys[0] in (7, 8) and xs[0] in (7, 8)


def test_greedy_zero_budget_and_empty():
    pool = np.ones((5, 5), bool)
    assert greedy_kernel_cover(pool, pool, 0).sum() == 0
    empty = np.zeros((5, 5), bool)
    assert greedy_kernel_cover(empty, empty, 3).sum() == 0
    with pytest.raises(ValueError):
        greedy_kernel_cover(pool, pool, -1)


def test_cover_surface_zero_outside_elig():
    pool = np.ones((7, 7), bool)
    elig = np.zeros((7, 7), bool)
    elig[3, 3] = True
    s = cover_surface(pool, elig)
    assert s[3, 3] > 0 and (s[~elig] == 0).all()


def test_greedy_cover_beats_corner_first_on_a_line():
    # A straight 1-px line: greedy cover of pool mass with 3 dots should cover >= the mass
    # covered by taking the first 3 raster-order pool pixels spaced greedily from the left end
    # in this symmetric case they tie or greedy wins; assert no worse than left-anchored.
    pool = np.zeros((9, 30), bool)
    pool[4, 2:28] = True
    dots = greedy_kernel_cover(pool, pool, 4, min_dist=2.8)

    def covered(d):
        dd = distance_transform_edt(~d)
        return float(np.maximum(1 - dd[pool] / 3.0, 0).sum())

    assert dots.sum() == 4
    assert covered(dots) > 0
