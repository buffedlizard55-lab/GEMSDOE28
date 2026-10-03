"""Hermetic tests for the H35-4 gravity-bench module (Session 11).

Synthetic fixtures only; no rasters, no network, no seeds. Pins the validity rules, the
quantile legs, and the bench/mesa partition the gate depends on.
"""

import numpy as np

from gems27 import gravity_bench as G


def test_training_valid_applies_the_frozen_sentinel_rule():
    a = np.array([[0.0, 1e29, 1e30, 1e31, np.inf, np.nan]])
    assert G.training_valid(a).tolist() == [[True, True, False, False, False, False]]


def test_lidar_valid_is_nonzero():
    assert G.lidar_valid(np.array([[0, 1, 255]], dtype=np.uint8)).tolist() == [[False, True, True]]


def test_bench_requires_gravity_step_and_relief_legs():
    shape = (40, 40)
    rng = np.random.default_rng(4)
    grav = rng.normal(size=shape)
    tmi = rng.normal(size=shape)
    step = rng.integers(0, 200, size=shape).astype(float)
    relief = rng.integers(0, 200, size=shape).astype(float)
    valid = np.full(shape, 255, dtype=np.uint8)
    foot = np.ones(shape, bool)
    out = G.bench_mesa(grav=grav, tmi=tmi, step=step, relief=relief, valid=valid, foot=foot)
    bench = out["bench"]
    assert bench.sum() > 0
    c = out["cuts"]
    assert bool((grav[bench] >= c["grav_hi"]).all())
    assert bool((step[bench] <= c["step_lo"]).all())
    assert bool((relief[bench] <= c["relief_lo"]).all())
    # bench and mesa are disjoint by construction
    assert not (bench & out["mesa"]).any()


def test_mesa_marks_strong_step_and_magnetic_rim_without_basement_step():
    shape = (30, 30)
    grav = np.zeros(shape)
    tmi = np.zeros(shape)
    step = np.zeros(shape)
    relief = np.zeros(shape)
    valid = np.full(shape, 255, dtype=np.uint8)
    foot = np.ones(shape, bool)
    # a crisp magnetic rim pixel with no gravity step must be mesa, never bench
    step[10, 10] = 250.0
    tmi[10, 10] = 500.0
    grav[10, 10] = -100.0
    out = G.bench_mesa(grav=grav, tmi=tmi, step=step, relief=relief, valid=valid, foot=foot)
    assert out["mesa"][10, 10]
    assert not out["bench"][10, 10]


def test_invalid_terrain_is_neither_bench_nor_mesa():
    shape = (20, 20)
    grav = np.full(shape, 999.0)
    tmi = np.zeros(shape)
    step = np.zeros(shape)
    relief = np.zeros(shape)
    valid = np.zeros(shape, dtype=np.uint8)
    valid[0, 0] = 255  # a single valid pixel keeps the quantiles defined
    foot = np.ones(shape, bool)
    out = G.bench_mesa(grav=grav, tmi=tmi, step=step, relief=relief, valid=valid, foot=foot)
    assert not out["bench"][1:, :].any()
    assert not out["mesa"][1:, :].any()


def test_degenerate_inputs_yield_empty_masks_not_crashes():
    foot = np.zeros((6, 6), bool)
    z = np.zeros((6, 6))
    out = G.bench_mesa(grav=z, tmi=z, step=z, relief=z,
                       valid=np.zeros((6, 6), dtype=np.uint8), foot=foot)
    assert not out["bench"].any() and not out["mesa"].any()
    assert out["fracs"]["bench"] == 0.0


def test_frozen_defaults_match_the_preregistration():
    assert (G.GRAV_BAND, G.TMI_BAND, G.STEP_BAND, G.RELIEF_BAND, G.VALID_BAND) == (18, 3, 3, 9, 12)
    assert (G.GRAV_Q, G.STEP_Q, G.RELIEF_Q) == (75.0, 50.0, 50.0)
    assert (G.MESA_STEP_Q, G.MESA_TMI_Q, G.MESA_GRAV_Q) == (90.0, 90.0, 50.0)
    assert (G.BUDGET_FRAC, G.THIN_D, G.FAR_PX) == (0.03, 2.8, 3.0)
