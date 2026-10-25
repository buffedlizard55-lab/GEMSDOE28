import importlib.util
from pathlib import Path

import numpy as np
import pytest
from scipy.stats import spearmanr

from gems27 import extrapolated_trace as trace
from gems27 import metric, registry_compare


def test_linear_ridge_migration_projects_to_zero_height():
    shape = (40, 60)
    ridges = [np.zeros(shape, bool) for _ in range(3)]
    for r, col in zip(ridges, (20, 24, 28)):
        r[5:35, col] = True
    surface, meta = trace.extrapolate_ridges(*ridges, np.ones(shape), np.ones(shape, bool))
    assert meta["accepted"] == 30
    assert np.array_equal(np.argwhere(surface)[:, 1], np.full(30, 16))
    assert np.isfinite(surface).all() and surface.max() <= 1


def test_nonlinear_ridges_and_missing_levels_rejected():
    r = [np.zeros((40, 60), bool) for _ in range(3)]
    for mask, col in zip(r, (20, 24, 36)):
        mask[:, col] = True
    s, meta = trace.extrapolate_ridges(*r, np.ones(r[0].shape), np.ones_like(r[0]))
    assert not s.any() and meta["accepted"] == 0
    r[2][:] = False
    s, meta = trace.extrapolate_ridges(*r, np.ones(r[0].shape), np.ones_like(r[0]))
    assert not s.any() and meta["accepted"] == 0


def test_projection_does_not_wrap_off_grid():
    r = [np.zeros((15, 15), bool) for _ in range(3)]
    for mask, col in zip(r, (1, 5, 9)):
        mask[:, col] = True
    s, meta = trace.extrapolate_ridges(*r, np.ones(r[0].shape), np.ones_like(r[0]))
    assert not s.any() and meta["accepted"] == 0


@pytest.mark.parametrize("binary", [False, True])
def test_exact_spearman_matches_scipy_with_ties(binary):
    rng = np.random.default_rng(3)
    a = rng.integers(0, 8, 400).astype(float)
    b = rng.integers(0, 2 if binary else 7, 400).astype(float)
    ranks, norm = registry_compare.ranked_centered(a)
    assert registry_compare.spearman_against(ranks, norm, b) == pytest.approx(spearmanr(a, b).statistic)
    assert registry_compare.spearman_against(ranks, norm, np.zeros(400)) is None


def test_proximity_is_directed_and_includes_three_pixels():
    a = np.zeros((20, 20), bool)
    b = a.copy()
    a[5, 5] = a[15, 15] = True
    b[5, 8] = True
    assert registry_compare.within_fraction(a, b) == 0.5
    assert registry_compare.within_fraction(b, a) == 1.0
    assert registry_compare.within_fraction(a & False, b) is None


def harness():
    path = Path(__file__).resolve().parents[1] / "scripts/run_losfo_harness.py"
    spec = importlib.util.spec_from_file_location("losfo_harness_v2_test", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_shared_evaluator_empty_prediction_has_no_phantom_credit():
    p = np.zeros((10, 10), bool)
    g = p.copy()
    g[0, 0] = True  # scipy's all-True EDT formerly put phantom distance=1 here
    r = harness().eval_set(p, g, np.ones_like(p))
    assert r["tp"] == 0 and r["dti"] == 0 and r["n_truth"] == 1


def test_shared_evaluator_masks_truth_and_matches_metric():
    p = np.zeros((10, 10), bool)
    g = p.copy()
    p[0, 0] = g[0, 0] = True
    active = np.ones_like(p)
    active[0, 0] = False
    r = harness().eval_set(p, g, active)
    assert r["n_truth"] == r["dots"] == 0
    p[7, 7] = g[8, 7] = True
    r = harness().eval_set(p, g, active)
    ref = metric.dti_binary(p, g, valid=active)
    assert r["dti"] == ref["dti"] and r["tp"] == ref["TPw"]
