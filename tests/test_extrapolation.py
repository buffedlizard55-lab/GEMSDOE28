"""Synthetic tests for H39-5 migration-extrapolated placement (knowledge/52).

A ridge migrating +8 px in +x across continuation levels must extrapolate to
shallow - v (8 px in -x from the shallow ridge); a stationary ridge must
extrapolate onto itself; the frozen swap must be count-matched, spacing-safe,
and must only ever place novel dots on eligible pixels.
"""
import numpy as np

from gems27 import migration


def _hg(shape, centres):
    y, x = np.mgrid[0:shape[0], 0:shape[1]]
    return [np.exp(-((x - c) ** 2) / (2 * 1.5**2)) * np.ones_like(y, float) for c in centres]


def test_extrapolated_position_is_shallow_minus_v():
    valid = np.ones((60, 120), bool)
    hgs = _hg(valid.shape, [40, 44, 48])  # v = +8 px in +x
    surf, disp = migration.extrapolated_surface_from_hg_levels(hgs, valid)
    # extrapolated ridge should sit at x ~= 40 - 8 = 32, not on 40/44/48
    col = int(np.argmax(surf[30]))
    assert abs(col - 32) <= 1, f"extrapolated ridge at x={col}, expected ~32"
    assert abs(float(disp[30, col]) - 8.0) <= 1.0
    assert surf[30, 40] == 0.0  # nothing left on the shallow ridge itself
    assert np.isfinite(surf).all() and float(surf.max()) <= 1.0


def test_stationary_ridge_extrapolates_onto_itself():
    valid = np.ones((60, 120), bool)
    hgs = _hg(valid.shape, [60, 60, 60])
    surf, disp = migration.extrapolated_surface_from_hg_levels(hgs, valid)
    assert int(np.argmax(surf[30])) == 60
    assert float(disp[30, 60]) <= 1.0


def test_opposite_dip_extrapolates_the_other_way():
    valid = np.ones((60, 120), bool)
    hgs = _hg(valid.shape, [80, 76, 72])  # v = -8 px in +x
    surf, _ = migration.extrapolated_surface_from_hg_levels(hgs, valid)
    assert abs(int(np.argmax(surf[30])) - 88) <= 1


def test_extrap_band_names_and_constants_frozen():
    assert migration.EXTRAP_BAND_NAMES == [
        "tmi_extrap_surface", "grav_extrap_surface", "extrap_surface_union"]
    assert migration.EXTRAP_MIN_DISP_PX == 2.0
    assert migration.EXTRAP_SWAP_FRAC == 0.35


def test_swap_count_matched_spacing_and_eligibility():
    rng = np.random.default_rng(0)
    shape = (80, 80)
    base = np.zeros(shape, bool)
    pts = [(10 + 6 * i, 10 + 6 * j) for i in range(10) for j in range(10)]
    for y, x in pts:
        base[y, x] = True
    prob = rng.random(shape)
    surface = np.zeros(shape)
    eligible = np.zeros(shape, bool)
    pool = [(13 + 6 * i, 13 + 6 * j) for i in range(9) for j in range(9)]
    for k, (y, x) in enumerate(pool):
        surface[y, x] = 1.0 - k * 0.001
        eligible[y, x] = True
    out, info = migration.extrap_swap(base, prob, surface, eligible)
    assert info["n_base"] == 100 and info["target_swap"] == 35
    assert info["n_final"] == 100, info  # count matched (swap + backfill)
    novel = out & ~base
    assert novel.sum() == info["n_swapped"] > 0
    assert (eligible[novel]).all()  # novel dots only on eligible pixels
    # spacing: no two final dots closer than 2.8 px, except pairs inherited
    # from the base grid (6 px apart here, so the rule applies to all pairs)
    from scipy.spatial import cKDTree
    ys, xs = np.nonzero(out)
    d, _ = cKDTree(np.c_[ys, xs].astype(float)).query(np.c_[ys, xs].astype(float), k=2)
    assert float(d[:, 1].min()) >= 2.8 - 1e-9


def test_swap_backfills_when_pool_is_empty():
    shape = (40, 40)
    base = np.zeros(shape, bool)
    for i in range(5):
        for j in range(5):
            base[5 + 6 * i, 5 + 6 * j] = True
    out, info = migration.extrap_swap(base, np.ones(shape), np.zeros(shape),
                                      np.zeros(shape, bool))
    assert info["n_swapped"] == 0
    assert info["n_final"] == info["n_base"]  # fully backfilled
    assert (out == base).all()
