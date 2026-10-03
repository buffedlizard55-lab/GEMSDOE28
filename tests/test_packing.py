"""Tests for the metric-aware packing module (`src/gems27/packing.py`)."""
from __future__ import annotations

import itertools

import numpy as np

from gems27 import packing


def _brute_force_best(candidates: np.ndarray, weight: np.ndarray, n: int) -> float:
    idx = list(zip(*np.nonzero(candidates)))
    best = 0.0
    for combo in itertools.combinations(idx, n):
        sel = np.zeros_like(candidates, bool)
        for y, x in combo:
            sel[y, x] = True
        best = max(best, packing.coverage_of(sel, weight))
    return best


def test_output_is_subset_and_count_bounded():
    rng = np.random.default_rng(0)
    cand = rng.random((40, 40)) < 0.2
    weight = rng.random((40, 40)).astype(np.float32)
    out = packing.coverage_greedy(cand, weight, 25)
    assert out.dtype == bool
    assert not (out & ~cand).any()
    assert out.sum() <= 25


def test_deterministic():
    rng = np.random.default_rng(7)
    cand = rng.random((30, 30)) < 0.3
    weight = rng.random((30, 30)).astype(np.float32)
    a = packing.coverage_greedy(cand, weight, 12)
    b = packing.coverage_greedy(cand, weight, 12)
    assert np.array_equal(a, b)


def test_matches_or_beats_simulated_annealing_free_reference():
    """Greedy coverage must be within the (1 - 1/e) bound of the brute-force optimum on a small case."""
    rng = np.random.default_rng(11)
    cand = np.zeros((14, 14), bool)
    picks = rng.choice(14 * 14, size=24, replace=False)
    cand.ravel()[picks] = True
    weight = rng.random((14, 14)).astype(np.float32)
    n = 4
    greedy = packing.coverage_greedy(cand, weight, n)
    g_val = packing.coverage_of(greedy, weight)
    opt = _brute_force_best(cand, weight, n)
    assert opt > 0
    assert g_val >= (1 - 1 / np.e) * opt - 1e-5
    assert g_val <= opt + 1e-5


def test_zero_weight_stops_early():
    cand = np.zeros((10, 10), bool)
    cand[2:8, 2:8] = True
    weight = np.zeros((10, 10), np.float32)
    out = packing.coverage_greedy(cand, weight, 5)
    assert out.sum() == 0


def test_prefers_high_weight_cluster():
    cand = np.ones((21, 21), bool)
    weight = np.zeros((21, 21), np.float32)
    weight[3:7, 3:7] = 1.0
    weight[16:19, 16:19] = 0.25
    out = packing.coverage_greedy(cand, weight, 3)
    assert out.sum() == 3
    near_strong = out[1:9, 1:9].sum()
    assert near_strong >= 2, "greedy must concentrate on the stronger field"


def test_spacing_emerges_from_the_objective():
    """The pair chosen must be the pair that maximises coverage, not the pair that is nearest."""
    cand = np.zeros((11, 11), bool)
    cand[0, 0] = cand[0, 2] = cand[0, 5] = True
    weight = np.zeros((11, 11), np.float32)
    weight[0, 0:8] = 1.0
    out = packing.coverage_greedy(cand, weight, 2)
    assert out.sum() == 2
    assert packing.coverage_of(out, weight) == _brute_force_best(cand, weight, 2)
