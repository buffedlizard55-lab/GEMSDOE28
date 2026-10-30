import numpy as np
import pytest

from gems27 import uniqueness as u


def _foot(h=20, w=30):
    f = np.zeros((h, w), bool)
    f[2:18, 3:27] = True
    return f


def test_dot_mask_binary_and_range():
    f = _foot()
    v = np.zeros(f.shape)
    v[5, 5] = 1.0
    v[0, 0] = np.nan  # outside footprint (row 0 is not in f) is allowed to be NaN
    d = u.dot_mask(v, f)
    assert d.sum() == 1 and d[5, 5]


def test_dot_mask_rejects_out_of_range_inside():
    f = _foot()
    v = np.zeros(f.shape)
    v[5, 5] = 1.5
    with pytest.raises(ValueError):
        u.dot_mask(v, f)


def test_dot_mask_rejects_nan_inside():
    f = _foot()
    v = np.zeros(f.shape)
    v[4, 4] = np.nan
    with pytest.raises(ValueError):
        u.dot_mask(v, f)


def test_fraction_within_radius():
    ref = np.zeros((20, 30), bool)
    ref[10, 10] = True
    cand = np.zeros_like(ref)
    cand[10, 13] = True   # exactly 3 px away -> within
    cand[10, 14] = True   # 4 px away -> not within
    assert u.fraction_within(cand, ref, radius=3.0) == pytest.approx(0.5)


def test_identical_is_full_overlap_and_duplicate():
    ref = np.zeros((20, 30), bool)
    ref[3:7, 4] = True
    frac = u.fraction_within(ref.copy(), ref)
    assert frac == 1.0
    assert u.is_duplicate(frac)


def test_disjoint_far_is_unique():
    ref = np.zeros((20, 30), bool)
    ref[0, 0] = True
    cand = np.zeros_like(ref)
    cand[19, 29] = True
    assert u.fraction_within(cand, ref) == 0.0
    assert not u.is_duplicate(0.0)


def test_threshold_is_strict_70_percent():
    assert not u.is_duplicate(0.70)
    assert u.is_duplicate(0.7001)


def test_empty_reference_gives_no_overlap():
    cand = np.zeros((4, 4), bool)
    cand[1, 1] = True
    assert u.fraction_within(cand, np.zeros((4, 4), bool)) == 0.0
