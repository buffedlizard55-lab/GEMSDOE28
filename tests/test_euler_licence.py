"""Tests for the H37-3 positive emission licence helpers (knowledge/34).

The arm is preregistered, so these tests lock the *mechanics* (spacing, exclusions, determinism,
count matching) rather than the thresholds; the thresholds are asserted only as the frozen constants
so that any change has to be deliberate.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from run_losfo_harness import (  # noqa: E402
    load_licence_mask,
    pack_licence_dots,
    random_matched_dots,
)

CSV = Path(__file__).resolve().parents[1] / "evidence" / "h31_1_euler_clusters.csv"


def test_frozen_licence_rule_finds_1435_candidates():
    mask, n = load_licence_mask(CSV, (3730, 3292))
    assert n == 1435, f"frozen rule changed: {n} candidates (preregistration says 1435)"
    assert int(mask.sum()) == 1435


def test_licence_dots_respect_spacing_and_exclude_base():
    cand = np.zeros((60, 60), bool)
    cand[5, 5] = cand[5, 8] = cand[30, 30] = True   # two within 3 px, one far away
    base = np.zeros((60, 60), bool)
    base[5, 9] = True                               # blocks the (5,8) candidate, keeps (5,5) (d=4 px)
    out = pack_licence_dots(cand, base, 2.8)
    assert out[5, 5] and out[30, 30] and not out[5, 8]
    assert not (out & base).any()


def test_random_matched_dots_matches_count_and_spacing_and_is_deterministic():
    pool = np.zeros((80, 80), bool)
    pool[10:70, 10:70] = True
    base = np.zeros((80, 80), bool)
    base[40, 40] = True
    a = random_matched_dots(pool, base, 25, 2.8, seed=7)
    b = random_matched_dots(pool, base, 25, 2.8, seed=7)
    c = random_matched_dots(pool, base, 25, 2.8, seed=8)
    assert int(a.sum()) == 25 and int((a & base).sum()) == 0
    assert np.array_equal(a, b) and not np.array_equal(a, c)
    ys, xs = np.nonzero(a)
    from scipy.spatial import cKDTree
    d, _ = cKDTree(np.column_stack([ys, xs])).query(np.column_stack([ys, xs]), k=2)
    assert d[:, 1].min() >= 2.8
