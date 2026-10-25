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


# --- H42-1 (Session 18): vector field + relocation -------------------------------------------

def test_vector_field_points_from_shallow_to_deep_ridge():
    valid = np.ones((60, 120), bool)
    hgs = _hg(valid.shape, [40, 44, 48])  # ridge migrates +8 px in +x
    vy, vx, coh = migration.migration_vector_from_hg_levels(hgs, valid)
    assert float(vx[30, 40]) > 3.0 and abs(float(vy[30, 40])) < 1.5
    assert np.isfinite(vy).all() and np.isfinite(vx).all()
    assert float(np.hypot(vx, vy).max()) <= migration.CLIP_PX + 1e-5


def test_vector_field_stationary_ridge_is_zero():
    valid = np.ones((60, 120), bool)
    hgs = _hg(valid.shape, [60, 60, 60])
    vy, vx, _ = migration.migration_vector_from_hg_levels(hgs, valid)
    assert abs(float(vx[30, 60])) < 1.0 and abs(float(vy[30, 60])) < 1.0
    # far outside the corridor the field is exactly 0 (no invented displacement)
    assert float(vx[30, 5]) == 0.0 and float(vy[30, 5]) == 0.0


def _reloc_fixture():
    shape = (40, 60)
    dots = np.zeros(shape, bool)
    dots[20, 30] = True   # will move up-dip (-x) under phys
    dots[10, 10] = True   # zero vector: stays
    dots[30, 50] = True   # target blocked: stays
    vy = np.zeros(shape, np.float32)
    vx = np.zeros(shape, np.float32)
    vx[20, 30] = 4.0      # migration +x; depth = ref -> phys shift -4 capped to -3
    vx[30, 50] = 4.0
    depth = np.full(shape, 2000.0, np.float32)
    blocked = np.zeros(shape, bool)
    blocked[30, 47] = True  # phys target of the third dot (50 - 3)
    allowed = np.ones(shape, bool)
    return dots, vy, vx, depth, blocked, allowed


def test_relocate_phys_moves_updip_capped_and_respects_blocked():
    dots, vy, vx, depth, blocked, allowed = _reloc_fixture()
    out, st = migration.relocate_dots(dots, vy, vx, depth, blocked, allowed, mode="phys")
    assert out[20, 27] and not out[20, 30]          # moved -3 (cap), not -4
    assert out[10, 10]                              # unmoved
    assert out[30, 50] and not out[30, 47]          # blocked target -> stayed
    assert st["n_moved_ge1px"] == 1 and st["n_out_pre_thin"] == 3
    assert st["n_stayed_after_blocked_move"] == 1


def test_relocate_anti_moves_opposite_and_rand_is_deterministic():
    dots, vy, vx, depth, blocked, allowed = _reloc_fixture()
    out_a, _ = migration.relocate_dots(dots, vy, vx, depth, blocked, allowed, mode="anti")
    assert out_a[20, 33] and not out_a[20, 27]      # opposite sign
    out_r1, st_r = migration.relocate_dots(dots, vy, vx, depth, blocked, allowed,
                                           mode="rand", seed=7)
    out_r2, _ = migration.relocate_dots(dots, vy, vx, depth, blocked, allowed,
                                        mode="rand", seed=7)
    assert np.array_equal(out_r1, out_r2)           # seeded determinism
    ys, xs = np.nonzero(out_r1)
    assert len(ys) == 3 and not out_r1[20, 27]      # rotated away from phys target


def test_relocate_zero_depth_never_moves_and_bad_mode_raises():
    dots, vy, vx, depth, blocked, allowed = _reloc_fixture()
    out, st = migration.relocate_dots(dots, vy, vx, np.zeros_like(depth),
                                      blocked, allowed, mode="phys")
    assert np.array_equal(out, dots) and st["n_moved_ge1px"] == 0
    try:
        migration.relocate_dots(dots, vy, vx, depth, blocked, allowed, mode="bogus")
    except ValueError:
        pass
    else:
        raise AssertionError("bad mode must raise")


def test_shift_magnitude_scales_and_caps():
    vy = np.zeros((3, 3), np.float32)
    vx = np.full((3, 3), 12.0, np.float32)
    half = migration.shift_magnitude(vy, vx, np.full((3, 3), 1000.0, np.float32))
    assert np.allclose(half, 3.0)  # 12 * 0.5 = 6 -> capped at CAP_PX=3
    quarter = migration.shift_magnitude(vy, vx, np.full((3, 3), 250.0, np.float32))
    assert np.allclose(quarter, 1.5)
