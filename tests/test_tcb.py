import numpy as np
import pytest

from gems27.tcb import (
    ORIENTATIONS,
    SCALES_PX,
    _shift_no_wrap,
    build_surface,
    fuse_surfaces,
    layer_surface,
    robust_standardize,
)


def test_shift_does_not_wrap_at_edges():
    a = np.arange(12, dtype=np.float32).reshape(3, 4)
    shifted = _shift_no_wrap(a, 1, 1)
    assert np.isnan(shifted[0]).all()
    assert np.isnan(shifted[:, 0]).all()
    np.testing.assert_array_equal(shifted[1:, 1:], a[:-1, :-1])


def test_single_layer_and_fusion_are_finite_and_masked():
    rng = np.random.default_rng(7)
    footprint = np.ones((64, 64), dtype=bool)
    raw = rng.normal(size=footprint.shape).astype(np.float32)
    raw[0, 0] = np.nan
    standardized = robust_standardize(raw, footprint)
    assert np.isfinite(standardized).all()
    surface = layer_surface(standardized, footprint)
    assert surface.shape == raw.shape
    assert np.isfinite(surface).all()
    assert surface.min() >= 0
    assert np.isfinite(fuse_surfaces({"rtp": surface, "tmi_hg": surface, "cond_surf": surface}, footprint)).all()


def test_build_surface_requires_exact_preregistered_layer_order():
    footprint = np.ones((32, 32), dtype=bool)
    layers = {name: np.ones(footprint.shape, dtype=np.float32) for name in ("rtp", "tmi_hg", "cond_surf")}
    surface, per_layer = build_surface(layers, footprint)
    assert tuple(per_layer) == ("rtp", "tmi_hg", "cond_surf")
    assert np.isfinite(surface).all()
    with pytest.raises(ValueError):
        build_surface({"rtp": layers["rtp"]}, footprint)


def test_operator_contract_is_fixed_and_unoriented():
    assert SCALES_PX == (2, 4, 8)
    assert len(ORIENTATIONS) == 4
    # The four representatives cover 0, 45, 90 and 135 degrees; reversing a
    # normal describes the same boundary and is intentionally not a fifth test.
    assert {tuple(o[:2]) for o in ORIENTATIONS} == {(0, 1), (1, 1), (1, 0), (1, -1)}
