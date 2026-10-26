from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree

from gems27.piercing_markers import build_surface, greedy_place, realized_offset, shift_nearest


def test_realized_offset_and_nearest_shift() -> None:
    assert realized_offset((0, 1), 4) == (0, 4)
    assert realized_offset((1, 0), -2) == (-2, 0)
    assert realized_offset((1, 1), 3) == (2, 2)
    a = np.arange(12).reshape(3, 4)
    shifted = shift_nearest(a, 1, -1)
    assert shifted.shape == a.shape
    assert shifted[1, 1] == a[0, 2]
    assert shifted[0, -1] == a[0, -1]


def test_greedy_place_is_deterministic_spaced_and_eligible() -> None:
    score = np.ones((20, 20), dtype=np.float32)
    eligible = np.ones_like(score, dtype=bool)
    eligible[:2, :] = False
    first = greedy_place(score, eligible, 20)
    second = greedy_place(score, eligible, 20)
    assert np.array_equal(first, second)
    assert first.sum() == 20
    assert not first[:2].any()
    points = np.argwhere(first)
    distances = cKDTree(points).query(points, k=2)[0][:, 1]
    assert np.all(distances >= 2.8)


def test_greedy_place_never_invents_zero_evidence() -> None:
    score = np.zeros((9, 9), dtype=np.float32)
    score[4, 4] = 0.5
    placed = greedy_place(score, np.ones_like(score, bool), 10)
    assert placed.sum() == 1
    assert placed[4, 4]


def test_shifted_piercing_marker_creates_finite_bounded_corridor_surface() -> None:
    height = width = 72
    yy, xx = np.mgrid[:height, :width]
    marker = np.sin(yy * 0.42) + 0.45 * np.sin(yy * 0.91 + 0.3)
    shifted = np.sin((yy - 4) * 0.42) + 0.45 * np.sin((yy - 4) * 0.91 + 0.3)
    rtp = np.where(xx < width // 2, marker, shifted).astype(np.float32)
    gravity = np.where(xx < width // 2, 0.8 * marker, 0.8 * shifted).astype(np.float32)
    # Add a broad non-marker trend; band-pass processing should not dominate on it.
    rtp += (xx / width * 0.2).astype(np.float32)
    gravity += (yy / height * 0.1).astype(np.float32)
    footprint = np.ones((height, width), dtype=bool)

    surfaces, metadata = build_surface(rtp, gravity, footprint)
    candidate = surfaces["candidate"]
    assert candidate.shape == footprint.shape
    assert np.isfinite(candidate).all()
    assert candidate.min() >= 0.0
    assert candidate.max() <= 1.0
    assert metadata["positive_surface_pixels"] > 0
    # The cross-fault registration response must be present at the synthetic offset boundary.
    corridor = candidate[:, width // 2 - 5 : width // 2 + 6]
    assert float(np.quantile(corridor, 0.95)) > 0.05
