"""Synthetic tests for H40-1 migration bands: a ridge that moves must be signed,
a ridge that does not move must be ~0, and coherence must peak on the corridor."""
import numpy as np

from gems27 import migration


def _hg(shape, centres):
    """HG-like field: one Gaussian ridge per level, centred at the given columns."""
    y, x = np.mgrid[0 : shape[0], 0 : shape[1]]
    return [np.exp(-((x - c) ** 2) / (2 * 1.5**2)) * np.ones_like(y, float) for c in centres]


def test_migrating_ridge_has_signed_offset():
    valid = np.ones((60, 120), bool)
    hgs = _hg(valid.shape, [40, 44, 48])  # ridge migrates +8 px in +x across levels
    gy = np.zeros(valid.shape)
    gx = np.ones(valid.shape)  # normal = +x
    signed, coh = migration.migration_bands_from_hg_levels(hgs, (gy, gx), valid)
    mid = signed[30, 40]
    assert mid > 3.0, f"signed migration at shallow ridge should be >3 px, got {mid}"
    # coherence = mean_l exp(-d_l/2): at the shallow ridge d=(0,4,8) -> 0.384; the
    # mid-level ridge pixel is closer to all three ridges, so coherence is higher there.
    assert abs(float(coh[30, 40]) - (1.0 + np.exp(-2.0) + np.exp(-4.0)) / 3.0) < 0.05
    assert coh[30, 44] > coh[30, 40]
    assert np.isfinite(signed).all() and float(np.abs(signed).max()) <= migration.CLIP_PX


def test_stationary_ridge_has_no_migration():
    valid = np.ones((60, 120), bool)
    hgs = _hg(valid.shape, [60, 60, 60])
    gy = np.zeros(valid.shape)
    gx = np.ones(valid.shape)
    signed, coh = migration.migration_bands_from_hg_levels(hgs, (gy, gx), valid)
    assert abs(float(signed[30, 60])) < 1.0
    assert coh[30, 60] > 0.9  # ridge present at every level, on the pixel


def test_opposite_dip_flips_sign():
    valid = np.ones((60, 120), bool)
    hgs = _hg(valid.shape, [80, 76, 72])
    gy = np.zeros(valid.shape)
    gx = np.ones(valid.shape)
    signed, _ = migration.migration_bands_from_hg_levels(hgs, (gy, gx), valid)
    assert float(signed[30, 80]) < -3.0


def test_band_names_frozen():
    assert migration.BAND_NAMES == [
        "tmi_signed_migration_px", "tmi_migration_coherence",
        "grav_signed_migration_px", "grav_migration_coherence",
    ]
