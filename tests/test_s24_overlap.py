"""Unit checks for the S24 nine-site overlap helper (geometry only; no score is computed here)."""
import importlib.util
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("audit_s24", ROOT / "scripts" / "audit_s24_nine_site_overlap.py")
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


def _grid(points, shape=(20, 20)):
    m = np.zeros(shape, bool)
    for r, c in points:
        m[r, c] = True
    return m


def test_within3_is_directional_and_uses_3px_radius():
    a = _grid([(5, 5), (5, 15)])
    b = _grid([(5, 8)])            # 3 px from (5,5), 7 px from (5,15)
    # a's dot (5,5) is 3 px from b; a's dot (5,15) is 7 px from b -> 1 of 2 dots.
    assert audit.within3(a, b) == 0.5
    # b's single dot (5,8) is exactly 3 px from a's (5,5) -> counts (boundary inclusive).
    assert audit.within3(b, a) == 1.0


def test_within3_empty_inputs_are_zero_not_nan():
    a = _grid([(1, 1)])
    empty = np.zeros_like(a)
    assert audit.within3(a, empty) == 0.0
    assert audit.within3(empty, a) == 0.0


def test_identical_sets_overlap_fully():
    a = _grid([(3, 3), (10, 10)])
    assert audit.within3(a, a.copy()) == 1.0
