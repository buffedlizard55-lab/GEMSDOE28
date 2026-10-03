"""Tests for the leave-fault-system-out (LOSFO) far-field holdout protocol.

The point of these tests is the *no-leakage* property: the protocol is worthless if held-out truth
can be reached from what the detector was allowed to see. Every geometric invariant below is checked
on synthetic grids with known geometry, so a regression in the buffer logic fails loudly instead of
silently inflating a hypothesis gate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
from scipy.ndimage import distance_transform_edt

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import losfo  # noqa: E402


def two_traces(h=200, w=200):
    """Two well-separated 1-D traces: one 'mapped', one 'unmapped'."""
    labels = np.zeros((h, w), bool)
    labels[40, 20:120] = True          # trace A
    labels[150, 60:160] = True         # trace B, 110 px from A
    return labels


# --------------------------------------------------------------------------------------------
# system grouping
# --------------------------------------------------------------------------------------------
def test_fault_systems_gives_every_catalogue_pixel_exactly_one_id():
    labels = two_traces()
    sg, n = losfo.fault_systems(labels, dilate_px=3)
    assert n == 2
    assert (sg > 0).sum() == labels.sum()
    assert set(np.unique(sg[labels])) == {1, 2}


def test_dilation_merges_en_echelon_segments_into_one_system():
    labels = np.zeros((200, 200), bool)
    labels[50, 20:60] = True
    labels[52, 62:100] = True      # 2 px step-over: same structure
    sg_small, n_small = losfo.fault_systems(labels, dilate_px=0)
    sg_big, n_big = losfo.fault_systems(labels, dilate_px=3)
    assert n_small == 2, "without dilation the two segments are separate"
    assert n_big == 1, "with 300 m dilation they are one system"
    assert (sg_big > 0).sum() == labels.sum()


def test_empty_labels_gives_zero_systems():
    sg, n = losfo.fault_systems(np.zeros((50, 50), bool))
    assert n == 0
    assert not sg.any()


def test_system_table_reports_size_and_centroid():
    labels = np.zeros((100, 100), bool)
    labels[30, 10:20] = True
    sg, n = losfo.fault_systems(labels, dilate_px=0)
    tab = losfo.system_table(sg, n, np.ones((100, 100), bool))
    assert len(tab) == 1
    assert tab["n_px"][0] == 10
    assert tab["cy"][0] == pytest.approx(30.0)
    assert tab["cx"][0] == pytest.approx(14.5)
    assert bool(tab["in_footprint"][0])


def test_system_table_marks_out_of_footprint_systems():
    labels = np.zeros((100, 100), bool)
    labels[30, 10:20] = True
    labels[70, 60:70] = True
    sg, n = losfo.fault_systems(labels, dilate_px=0)
    foot = np.zeros((100, 100), bool)
    foot[:50, :] = True
    tab = losfo.system_table(sg, n, foot)
    assert sorted(tab["in_footprint"].tolist()) == [False, True]


# --------------------------------------------------------------------------------------------
# fold assignment
# --------------------------------------------------------------------------------------------
def test_holdout_assignment_is_deterministic_and_covers_every_fold():
    labels = np.zeros((400, 400), bool)
    rng = np.random.default_rng(3)
    for _ in range(40):
        y, x = int(rng.integers(10, 380)), int(rng.integers(10, 300))
        labels[y, x:x + 25] = True
    foot = np.ones_like(labels, bool)
    sg, n = losfo.fault_systems(labels, dilate_px=3)
    tab = losfo.system_table(sg, n, foot)
    yy, xx = np.nonzero(foot)
    ym, xm = int(np.median(yy)), int(np.median(xx))
    gy, gx = np.ogrid[: labels.shape[0], : labels.shape[1]]
    fold = np.full(labels.shape, -1, np.int8)
    fold[(gy < ym) & (gx < xm)] = 0
    fold[(gy < ym) & (gx >= xm)] = 1
    fold[(gy >= ym) & (gx < xm)] = 2
    fold[(gy >= ym) & (gx >= xm)] = 3

    a = losfo.assign_systems_to_folds(tab, fold, 4, seed=99)
    b = losfo.assign_systems_to_folds(tab, fold, 4, seed=99)
    assert np.array_equal(a, b), "assignment must be reproducible for a fixed seed"
    c = losfo.assign_systems_to_folds(tab, fold, 4, seed=100)
    assert not np.array_equal(a, c), "a different seed must draw a different sample"
    assert set(np.unique(a[a >= 0])) == {0, 1, 2, 3}
    assert np.isin(a, -1).sum() + (a >= 0).sum() == len(tab)


def test_held_out_share_is_close_to_the_registered_fraction():
    labels = np.zeros((400, 400), bool)
    rng = np.random.default_rng(5)
    for _ in range(40):
        y, x = int(rng.integers(10, 380)), int(rng.integers(10, 300))
        labels[y, x:x + 25] = True
    sg, n = losfo.fault_systems(labels, dilate_px=3)
    tab = losfo.system_table(sg, n, np.ones_like(labels, bool))
    fold = np.zeros(labels.shape, np.int8)
    fold[:200, :] = 0
    fold[200:, :] = 1
    a = losfo.assign_systems_to_folds(tab, fold, 2, seed=7)
    frac = (a >= 0).mean()
    assert abs(frac - losfo.HOLDOUT_FRACTION) < 0.05


def test_empty_system_table_assignment():
    tab = losfo.system_table(np.zeros((20, 20), np.int32), 0, np.ones((20, 20), bool))
    out = losfo.assign_systems_to_folds(tab, np.zeros((20, 20), np.int8), 4, seed=1)
    assert out.size == 0


# --------------------------------------------------------------------------------------------
# the no-leakage invariant
# --------------------------------------------------------------------------------------------
def test_held_out_truth_is_at_least_buffer_px_from_every_known_pixel():
    labels = two_traces()
    sg, n = losfo.fault_systems(labels, dilate_px=3)
    fold = np.zeros(labels.shape, np.int8)
    fold[:100, :] = 0
    fold[100:, :] = 1
    hold = np.array([-1, 1], np.int8)      # hold out the southern trace only
    sp = losfo.build_losfo_split(labels, sg, hold, fold, 1, seed=0, fold_names=["N", "S"], buffer_px=6)
    assert sp.hidden.sum() == 100                      # the whole southern trace
    assert sp.known.sum() == 100                       # the northern trace stays known
    assert not (sp.hidden & sp.known).any()
    d = distance_transform_edt(~sp.known)
    assert d[sp.hidden].min() >= 6, "held-out truth must be outside the buffer around itself"
    assert sp.min_dist_hidden_to_known >= 6


def test_masked_labels_remove_the_buffer_around_every_held_out_system():
    labels = two_traces()
    sg, n = losfo.fault_systems(labels, dilate_px=3)
    hold = np.array([-1, 1], np.int8)
    masked = losfo.masked_labels(labels, sg, hold, buffer_px=6)
    assert masked.sum() == 100
    assert not (masked & (sg == 2)).any(), "the held-out system must be absent from training labels"
    # and the unmasked labels still contain it
    assert (labels & (sg == 2)).sum() == 100


def test_no_holdout_means_labels_unchanged():
    labels = two_traces()
    sg, _ = losfo.fault_systems(labels, dilate_px=3)
    masked = losfo.masked_labels(labels, sg, np.array([-1, -1], np.int8), buffer_px=6)
    assert np.array_equal(masked, labels)


def test_all_fold_separations_are_reported_for_every_fold():
    labels = two_traces()
    sg, n = losfo.fault_systems(labels, dilate_px=3)
    fold = np.zeros(labels.shape, np.int8)
    fold[:100, :] = 0
    fold[100:, :] = 1
    hold = np.array([0, 1], np.int8)      # hold out one system in each fold
    seps = []
    for f in (0, 1):
        sp = losfo.build_losfo_split(labels, sg, hold, fold, f, seed=0, fold_names=["N", "S"])
        seps.append(sp.min_dist_hidden_to_known)
    assert all(s >= losfo.DEFAULT_BUFFER_PX for s in seps), seps


def test_credit_on_matches_the_official_kernel():
    pred = np.zeros((50, 50), bool)
    pred[25, 25] = True
    truth = np.zeros((50, 50), bool)
    truth[25, 25:28] = True               # d = 0, 1, 2 px -> k = 1, 2/3, 1/3
    assert losfo.credit_on(pred, truth) == pytest.approx(1.0 + 2 / 3 + 1 / 3)
    assert losfo.credit_on(np.zeros((50, 50), bool), truth) == 0.0
    assert losfo.credit_on(pred, np.zeros((50, 50), bool)) == 0.0


# --------------------------------------------------------------------------------------------
# the committed diagnostic is internally consistent (run scripts/run_losfo_harness.py first)
# --------------------------------------------------------------------------------------------
import json  # noqa: E402

EVIDENCE = Path(__file__).resolve().parents[1] / "evidence" / "losfo_farfield_diagnostic.json"


@pytest.mark.skipif(not EVIDENCE.exists(), reason="run scripts/run_losfo_harness.py first")
def test_committed_diagnostic_holds_truth_genuinely_off_catalogue():
    d = json.loads(EVIDENCE.read_text())
    ff = d["far_field_check"]
    # the whole point of the protocol: truth must be at least the buffer away from known pixels
    assert ff["min_dist_truth_to_known_px_over_cells"] >= d["meta"]["buffer_px"]
    # and it must be spread well beyond that floor, not piled against it
    assert ff["median_dist_truth_to_known_px_over_cells"] > (
        3 * ff["min_dist_truth_to_known_px_over_cells"])
    assert "NOT A PROMOTION GATE" in d["kind"].upper()


@pytest.mark.skipif(not EVIDENCE.exists(), reason="run scripts/run_losfo_harness.py first")
def test_committed_diagnostic_reports_its_own_uncertainty():
    d = json.loads(EVIDENCE.read_text())
    ratios = [v["losfo_tp"] / v["leaky_tp"] for v in d["per_fold"].values() if v["leaky_tp"]]
    assert len(ratios) == 4
    spread = max(ratios) - min(ratios)
    # if the per-fold spread is this wide the aggregate ratio must not be presented as precise;
    # this assertion documents that the spread is material, so a future tightening is a real change
    assert spread > 0.10, ratios
    # and the pooled ratio must be reproducible from the arm totals
    arms = d["arms"]
    assert arms["losfo"]["sum_tp"] / arms["leaky"]["sum_tp"] == pytest.approx(
        d["ratios"]["credit_losfo_over_leaky"], rel=1e-9)


@pytest.mark.skipif(not EVIDENCE.exists(), reason="run scripts/run_losfo_harness.py first")
def test_committed_diagnostic_used_a_dedicated_seed_decade():
    d = json.loads(EVIDENCE.read_text())
    # 210-219 is reserved for this diagnostic; 160-199 belong to consumed H31/H32 gates
    assert all(210 <= s <= 219 for s in d["seeds"]), d["seeds"]
    assert not (set(d["seeds"]) & set(range(100, 210)))
