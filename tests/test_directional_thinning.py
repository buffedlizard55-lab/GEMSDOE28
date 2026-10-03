"""Tests for the directional (anisotropic) Poisson-disk thinning function (H37-1)."""
from __future__ import annotations

import numpy as np
import pytest

from gems27.thinning import directional_dot_thin, dot_thin


def _diagonal_ridge(length: int = 30, thickness: int = 1) -> np.ndarray:
    """Return a 1-px-wide diagonal ridge of given pixel-length."""
    H = length + 4
    W = length + 4
    m = np.zeros((H, W), bool)
    for i in range(length):
        m[i + 2, i + 2] = True
    return m


def test_directional_dot_thin_subset_of_input() -> None:
    m = _diagonal_ridge(30)
    sx = np.ones_like(m, np.float32)
    sy = np.zeros_like(m, np.float32)
    out = directional_dot_thin(m, sx, sy, 3.0, 2.0)
    assert out.shape == m.shape
    assert out.sum() <= m.sum()
    # Every kept pixel must lie on the input mask.
    assert (out & ~m).sum() == 0


def test_directional_dot_thin_anisotropy_changes_count() -> None:
    """Swapping the ellipse orientation should change the kept-dot count on an asymmetric ridge."""
    # A non-trivially-curved mask: a horizontal ridge plus a short oblique branch.
    H, W = 30, 60
    m = np.zeros((H, W), bool)
    for c in range(5, 55):
        m[15, c] = True
    for r in range(10, 21):
        m[r, 30] = True
    sx_h = np.ones_like(m, np.float32)
    sy_h = np.zeros_like(m, np.float32)
    sx_v = np.zeros_like(m, np.float32)
    sy_v = np.ones_like(m, np.float32)
    n_h = int(directional_dot_thin(m, sx_h, sy_h, 4.0, 2.0).sum())
    n_v = int(directional_dot_thin(m, sx_v, sy_v, 4.0, 2.0).sum())
    # The asymmetry should be visible: rotating the strike by 90 degrees must change the count.
    assert n_h != n_v, f"anisotropy had no effect: n_h={n_h} n_v={n_v}"
    assert n_h > 0 and n_v > 0


def test_directional_dot_thin_symmetric_matches_dot_thin_when_ellipse_is_circle() -> None:
    """a_along == a_across reproduces ``dot_thin`` exactly for any strike vector."""
    m = _diagonal_ridge(40)
    sx = np.full_like(m, 0.7071, np.float32)
    sy = np.full_like(m, 0.7071, np.float32)
    for d in (2.0, 2.8, 3.0, 3.5):
        ours = directional_dot_thin(m, sx, sy, d, d)
        theirs = dot_thin(m, d)
        assert ours.sum() == theirs.sum(), f"mismatch at d={d}"


def test_directional_dot_thin_zero_threshold_returns_input() -> None:
    m = _diagonal_ridge(10)
    sx = np.ones_like(m, np.float32)
    sy = np.zeros_like(m, np.float32)
    # a_along <= 1 and a_across <= 1 short-circuit to mask.copy()
    out = directional_dot_thin(m, sx, sy, 1.0, 1.0)
    assert out.sum() == m.sum()


def test_directional_dot_thin_2d_shape_required() -> None:
    with pytest.raises(ValueError):
        directional_dot_thin(np.array([True, False]), np.zeros(2), np.zeros(2), 2.0, 2.0)


def test_directional_dot_thin_shape_mismatch_rejected() -> None:
    m = _diagonal_ridge(10)
    sx = np.zeros(m.shape, np.float32)
    sy_bad = np.zeros((m.shape[0], m.shape[1] + 1), np.float32)
    with pytest.raises(ValueError):
        directional_dot_thin(m, sx, sy_bad, 2.0, 2.0)


def test_directional_dot_thin_deterministic() -> None:
    m = _diagonal_ridge(40)
    sx = np.full_like(m, 0.7071, np.float32)
    sy = np.full_like(m, 0.7071, np.float32)
    out1 = directional_dot_thin(m, sx, sy, 3.5, 2.0)
    out2 = directional_dot_thin(m, sx, sy, 3.5, 2.0)
    assert (out1 == out2).all()