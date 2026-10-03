"""Unit tests for the H32-1 structural-step transform (label-free, deterministic, in [0, 1])."""

from __future__ import annotations

import numpy as np
import pytest

from gems27.structural_step import STRUCT_STEP_FEATURE_NAMES, structural_step_features


def _synthetic(shape=(80, 90), step_col=45):
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[: shape[0], : shape[1]]
    depth = np.where(xx < step_col, 500.0, 1500.0) + 20.0 * rng.standard_normal(shape)
    cond = np.where(xx < step_col, 0.2, 0.9) + 0.05 * rng.standard_normal(shape)
    strain = 0.3 + 0.1 * np.sin(yy / 7.0) + 0.02 * rng.standard_normal(shape)
    valid = np.ones(shape, bool)
    return depth.astype(np.float32), cond.astype(np.float32), strain.astype(np.float32), valid


def test_shapes_names_and_range():
    depth, cond, strain, valid = _synthetic()
    out = structural_step_features(depth, cond, strain, valid)
    assert out.shape == (len(STRUCT_STEP_FEATURE_NAMES),) + depth.shape
    assert out.dtype == np.float32
    assert np.isfinite(out).all()
    assert out.min() >= 0.0 and out.max() <= 1.0


def test_step_edge_is_detected_at_the_interface():
    depth, cond, strain, valid = _synthetic(step_col=45)
    out = structural_step_features(depth, cond, strain, valid)
    cb_step = out[STRUCT_STEP_FEATURE_NAMES.index("struct_cb_step_1000m")]
    column_energy = cb_step.mean(axis=0)
    # the strongest 1 km step must sit next to the synthetic interface at column 45
    assert abs(int(np.argmax(column_energy)) - 45) <= 3
    far = column_energy[:30].mean()
    assert column_energy.max() > 3.0 * far


def test_orientation_agreement_requires_both_fields():
    depth, cond, strain, valid = _synthetic()
    out = structural_step_features(depth, cond, strain, valid)
    agree = out[STRUCT_STEP_FEATURE_NAMES.index("struct_cb_cond_orientation_agreement_1000m")]
    concord = out[STRUCT_STEP_FEATURE_NAMES.index("struct_cb_cond_concordance_1000m")]
    # outside the strong-gradient band both agreement columns are exactly zero
    assert agree[agree > 0].size > 0
    assert np.all(agree[concord == 0.0] == 0.0)
    assert agree.max() <= 1.0


def test_invalid_cells_are_zero_and_inputs_untouched():
    depth, cond, strain, valid = _synthetic()
    valid = valid.copy()
    valid[:10, :] = False
    before = (depth.copy(), cond.copy(), strain.copy())
    out = structural_step_features(depth, cond, strain, valid)
    assert np.all(out[:, :10, :] == 0.0)
    assert np.all(out[:, ~valid] == 0.0)
    assert np.array_equal(depth, before[0]) and np.array_equal(cond, before[1])
    assert np.array_equal(strain, before[2])


def test_deterministic_repeat_run():
    depth, cond, strain, valid = _synthetic()
    a = structural_step_features(depth, cond, strain, valid)
    b = structural_step_features(depth, cond, strain, valid)
    assert np.array_equal(a, b)


def test_rejects_empty_or_mismatched_inputs():
    depth, cond, strain, valid = _synthetic()
    with pytest.raises(ValueError):
        structural_step_features(depth, cond[:-1], strain, valid)
    with pytest.raises(ValueError):
        structural_step_features(depth, cond, strain, np.zeros_like(valid))
    with pytest.raises(ValueError):
        structural_step_features(depth, cond, strain, valid, sigmas_px=(3.0, -1.0))
