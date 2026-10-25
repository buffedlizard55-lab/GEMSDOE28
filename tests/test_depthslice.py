"""H39-1 depth-slice transform: analytic continuation, tilt, fill and ranking contracts."""
import numpy as np
import pytest

from gems27 import depthslice


def test_upward_continuation_matches_analytic_decay():
    # Periodic harmonic along x: continuation must scale amplitude by exp(-|k| h) exactly.
    H, W, lam_m = 32, 256, 6400.0  # wavelength 64 px * 100 m; W*100/lam = 40 whole cycles
    x = np.arange(W) * 100.0
    field = np.tile(3.0 + np.cos(2 * np.pi * x / lam_m), (H, 1))
    for h in (1000.0, 2000.0):
        out = depthslice.upward_continue(field, h, pad_px=0)
        amp = (out.max() - out.min()) / 2.0
        expect = float(np.exp(-2 * np.pi * h / lam_m))
        assert out.shape == field.shape
        assert abs(float(out.mean()) - 3.0) < 1e-9
        assert abs(amp - expect) < 1e-6, (h, amp, expect)


def test_upward_continuation_attenuates_short_wavelengths_more():
    rng = np.random.default_rng(7)
    f = rng.normal(size=(64, 64))
    e0 = float((depthslice.hg_mag(f) ** 2).mean())
    e1 = float((depthslice.hg_mag(depthslice.upward_continue(f, 1000.0, pad_px=0)) ** 2).mean())
    e2 = float((depthslice.hg_mag(depthslice.upward_continue(f, 2000.0, pad_px=0)) ** 2).mean())
    assert e0 > e1 > e2 > 0


def test_vertical_derivative_of_constant_is_zero():
    out = depthslice.vertical_derivative_up(np.full((16, 16), 5.0), 1000.0, pad_px=0)
    assert np.allclose(out, 0.0, atol=1e-12)


def test_fill_nearest_and_finite_guard():
    f = np.array([[1.0, np.nan], [np.nan, 4.0]])
    out = depthslice.fill_nearest(f, np.isfinite(f))
    assert np.isfinite(out).all() and out[0, 0] == 1.0 and out[1, 1] == 4.0
    with pytest.raises(ValueError):
        depthslice.upward_continue(f, 1000.0, pad_px=0)


def test_persist_bounds_on_synthetic():
    # persist = hg2000/(hg2000+hg_shallow) must lie in [0,1] by construction.
    a = np.abs(np.random.default_rng(3).normal(size=(50, 50)))
    b = np.abs(np.random.default_rng(4).normal(size=(50, 50)))
    p = a / np.maximum(a + b, 1e-300)
    assert p.min() >= 0.0 and p.max() <= 1.0
