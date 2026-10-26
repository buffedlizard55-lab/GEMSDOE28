"""S20-H2 vesselness: synthetic ridge/blob/step behaviour + contract checks (knowledge/56)."""

import numpy as np
import pytest

from gems27.vesselness import frangi_vesselness


def _ridge(shape=(64, 64)):
    y, x = np.mgrid[0 : shape[0], 0 : shape[1]]
    return np.exp(-((x - 32.0) ** 2) / (2 * 2.0**2)) * 100.0  # vertical bright ridge at col 32


def _blob(shape=(64, 64)):
    y, x = np.mgrid[0 : shape[0], 0 : shape[1]]
    return np.exp(-(((x - 32.0) ** 2 + (y - 32.0) ** 2)) / (2 * 4.0**2)) * 100.0


def test_ridge_centreline_beats_blob_centre():
    valid = np.ones((64, 64), bool)
    v_ridge = frangi_vesselness(_ridge(), valid)
    v_blob = frangi_vesselness(_blob(), valid)
    assert v_ridge[32, 32] > 0.5
    assert v_blob[32, 32] < v_ridge[32, 32]
    # Ridge response decays away from the centreline.
    assert v_ridge[32, 32] > v_ridge[32, 45]


def test_flat_and_dark_ridge_are_zero():
    valid = np.ones((32, 32), bool)
    assert frangi_vesselness(np.full((32, 32), 7.0), valid).max() == 0.0
    dark = 100.0 - _ridge((64, 64))  # dark trough on bright background: lambda2 > 0 at centre
    v = frangi_vesselness(dark, np.ones((64, 64), bool))
    assert v[32, 32] < 0.05


def test_contract_range_mask_and_determinism():
    field = _ridge()
    valid = np.ones((64, 64), bool)
    valid[:10, :] = False
    field[0, 0] = np.nan
    a = frangi_vesselness(field, valid)
    b = frangi_vesselness(field, valid)
    assert a.dtype == np.float32
    assert np.isfinite(a).all() and a.min() >= 0.0 and a.max() <= 1.0
    assert (a[~valid] == 0).all()
    assert np.array_equal(a, b)


def test_invalid_inputs_raise():
    with pytest.raises(ValueError):
        frangi_vesselness(np.zeros((8, 8)), np.zeros((8, 8), bool))
    with pytest.raises(ValueError):
        frangi_vesselness(np.zeros((8, 8)), np.ones((8, 9), bool))
    with pytest.raises(ValueError):
        frangi_vesselness(np.zeros((8, 8)), np.ones((8, 8), bool), sigmas_px=(0.0,))
