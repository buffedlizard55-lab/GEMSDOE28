"""Tests for the H33-1 kinematic favourability score and its committed data precondition.

The data-precondition tests read the real runner-produced clip, so they fail loudly if the bridge
regresses (an empty clip, a missing TS/TD field) rather than letting a dead arm be "validated".
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems27 import grid  # noqa: E402
from gems27 import kinematics as K  # noqa: E402

CLIP = ROOT / "docs" / "data" / "sb_slip_tendency_in_footprint.json"


@pytest.fixture(scope="module")
def seg():
    if not CLIP.exists():
        pytest.skip("runner bridge has not produced the clip yet")
    return K.load_segments(CLIP)


# --------------------------------------------------------------------------------------------
# units: the metre/pixel confusion that made coverage come back 0.0
# --------------------------------------------------------------------------------------------
def test_xy_to_rc_is_the_exact_inverse_of_rc_to_xy():
    rows = np.array([0, 1, 100, 1864, 3729])
    cols = np.array([0, 1, 50, 1645, 3291])
    x, y = grid.rc_to_xy(rows, cols)
    rb, cb = grid.xy_to_rc(x, y)
    assert np.allclose(rb, rows) and np.allclose(cb, cols)
    # pixel centre, not pixel corner
    x0, y0 = grid.rc_to_xy(np.array([0]), np.array([0]))
    assert float(x0[0]) == pytest.approx(grid.TRANSFORM[2] + 50.0)
    assert float(y0[0]) == pytest.approx(grid.TRANSFORM[5] - 50.0)


def test_trace_is_in_pixel_space_not_metres(seg):
    """A metre-valued trace spans ~330,000 units; a pixel-valued one spans ~3,700."""
    tr = seg["trace_colrow"]
    assert tr[:, 0].max() < grid.SHAPE[1] + 50, "trace looks like metres, not pixels"
    assert tr[:, 1].max() < grid.SHAPE[0] + 50
    assert tr[:, 0].min() > -50 and tr[:, 1].min() > -50


def test_densify_samples_in_pixels_not_metres():
    """At 0.5 px a 6 km (60 px) segment must yield ~120 points, not ~12,000."""
    part = np.array([[0.0, 0.0], [60.0, 0.0]])
    out = K.densify(part, step_px=0.5)
    assert len(out) == pytest.approx(121, abs=2)
    assert np.allclose(out[-1], part[-1])


def test_densify_keeps_endpoints_and_never_shrinks():
    part = np.array([[10.0, 20.0], [10.7, 20.2], [40.0, 55.0]])
    out = K.densify(part, step_px=0.5)
    assert np.allclose(out[0], part[0]) and np.allclose(out[-1], part[-1])
    assert len(out) >= len(part)


# --------------------------------------------------------------------------------------------
# strike conventions
# --------------------------------------------------------------------------------------------
def test_circular_strike_difference_folds_undirected_lines():
    assert K.circular_strike_difference(179.0, 1.0) == pytest.approx(2.0)
    assert K.circular_strike_difference(10.0, 170.0) == pytest.approx(20.0)
    assert K.circular_strike_difference(0.0, 90.0) == pytest.approx(90.0)
    assert K.circular_strike_difference(45.0, 45.0) == pytest.approx(0.0)
    # never exceeds 90: line directions have no sign
    d = K.circular_strike_difference(np.arange(0, 180, 7.0), 12.0)
    assert d.max() <= 90.0 + 1e-9


def test_geometric_strike_is_azimuth_from_north_clockwise():
    # due north (row decreases), due east (col increases)
    assert K.geometric_strike(np.array([[0.0, 0.0], [0.0, -10.0]])) == pytest.approx(0.0)
    assert K.geometric_strike(np.array([[0.0, 0.0], [10.0, 0.0]])) == pytest.approx(90.0)
    # south is the same *undirected line* as north, so it folds to 0, not 180
    assert K.geometric_strike(np.array([[0.0, 0.0], [0.0, 10.0]])) == pytest.approx(0.0)
    assert K.geometric_strike(np.array([[0.0, 0.0], [-10.0, 0.0]])) == pytest.approx(90.0)
    assert K.geometric_strike(np.array([[0.0, 0.0], [10.0, -10.0]])) == pytest.approx(45.0)
    assert K.geometric_strike(np.array([[5.0, 5.0]])) is None          # too short
    assert K.geometric_strike(np.array([[0.0, 0.0], [0.0, 0.0]])) is None  # degenerate
    # the result is always a line direction in [0, 180)
    rng = np.random.default_rng(7)
    pts = rng.uniform(-50, 50, size=(400, 2, 2))
    out = np.array([K.geometric_strike(p) for p in pts])
    out = out[np.isfinite(out)]
    assert len(out) > 300 and out.min() >= 0.0 and out.max() < 180.0


def test_geometric_strike_matches_the_source_attribute_convention(seg):
    """Independently re-derive the check recorded in the module docstring."""
    doc = json.loads(CLIP.read_text())
    diffs = []
    for rec in doc["records"][:4000]:
        src = rec.get("Strike")
        if src is None or not np.isfinite(src):
            continue
        px = K._part_to_pixel(np.asarray(rec["parts"][0], float))
        g = K.geometric_strike(px)
        if g is None:
            continue
        diffs.append(K.circular_strike_difference(g, float(src) % 180.0))
    assert len(diffs) > 1000
    # median agreement must stay near the 4.27 deg measured when the convention was established
    assert float(np.median(diffs)) < 10.0, f"strike convention drifted: median {np.median(diffs):.2f}"


# --------------------------------------------------------------------------------------------
# the frozen score
# --------------------------------------------------------------------------------------------
def test_percentile_rank_bounds_and_nan_passthrough():
    ref = np.array([1.0, 2.0, 3.0, 4.0])
    r = K.percentile_rank(np.array([0.5, 1.0, 2.5, 4.0, 9.0, np.nan]), ref)
    assert 0.0 <= np.nanmin(r) and np.nanmax(r) <= 1.0
    assert np.isnan(r[-1])
    # strictly increasing strictly inside the reference range ...
    assert r[0] < r[1] < r[2] < r[3]
    # ... and saturating at 1.0 for anything at or above the maximum (ties are expected)
    assert r[3] == r[4] == 1.0
    assert K.percentile_rank(np.array([5.0]), np.array([np.nan, 1.0]))[0] == 1.0
    assert np.isnan(K.percentile_rank(np.array([5.0]), np.array([np.nan]))[0])


def test_borrow_rejects_segments_outside_the_strike_tolerance(seg):
    """A dot beside a mapped fault oriented 90 deg away must stay neutral."""
    tr = seg["trace_colrow"]
    mid = tr[len(tr) // 2]
    near_strike = float(seg["strike"][seg["trace_owner"][len(tr) // 2]])
    ts_ok, td_ok = K.borrow_kinematics(np.array([[mid[0], mid[1]]]),
                                       np.array([near_strike]), seg)
    assert np.isfinite(ts_ok[0]) and np.isfinite(td_ok[0])
    perp = (near_strike + 90.0) % 180.0
    ts_no, td_no = K.borrow_kinematics(np.array([[mid[0], mid[1]]]), np.array([perp]), seg)
    assert np.isnan(ts_no[0]) and np.isnan(td_no[0])


def test_borrow_returns_nan_for_a_dot_far_from_every_segment(seg):
    far = np.array([[-5000.0, -5000.0]])
    ts, td = K.borrow_kinematics(far, np.array([45.0]), seg)
    assert np.isnan(ts[0]) and np.isnan(td[0])


def _synthetic_seg(gap_px: float = 30.0):
    """Two isolated, identically oriented north-trending segments with very different TS.

    `gap_px` controls their separation, so a test can put the second segment either well outside
    or just inside the frozen 10 px borrow radius.
    """
    a = np.array([[0.0, 0.0], [0.0, -1.0]])
    b = np.array([[gap_px, 0.0], [gap_px, -1.0]])
    return {"trace_colrow": np.vstack([a, b]),
            "trace_owner": np.array([0, 0, 1, 1], dtype=np.int32),
            "strike": np.array([0.0, 0.0]),
            "TS": np.array([0.10, 0.90]),
            "TD": np.array([0.20, 0.80]),
            "n_segments": 2}


def test_borrow_returns_exactly_the_coincident_segment_when_it_is_alone():
    """With the other segment outside the radius, the borrow must reproduce its values exactly."""
    s = _synthetic_seg(gap_px=30.0)          # 30 px away: outside SEGMENT_MAX_PX
    on_a, td_a = K.borrow_kinematics(np.array([[0.0, -0.5]]), np.array([0.0]), s)
    assert on_a[0] == pytest.approx(0.10)
    assert td_a[0] == pytest.approx(0.20)
    on_b, td_b = K.borrow_kinematics(np.array([[30.0, -0.5]]), np.array([0.0]), s)
    assert on_b[0] == pytest.approx(0.90) and td_b[0] == pytest.approx(0.80)


def test_borrow_blends_and_is_monotonic_between_two_segments_in_range():
    """Both segments inside the radius -> a genuine inverse-distance blend."""
    s = _synthetic_seg(gap_px=8.0)           # 8 px apart: both within SEGMENT_MAX_PX
    xs = [0.0, 2.0, 4.0, 6.0, 8.0]
    vals = [K.borrow_kinematics(np.array([[x, -0.5]]), np.array([0.0]), s)[0][0] for x in xs]
    assert all(np.isfinite(vals))
    # not exactly 0.10 / 0.90 at the ends: the dot sits 0.5 px from A's densified vertices, so B
    # still contributes a little. The endpoints must be strongly biased, and the trend monotonic.
    assert vals[0] < 0.20
    assert vals[-1] > 0.80
    assert all(b > a for a, b in zip(vals, vals[1:]))   # strictly monotonic A -> B
    mid = vals[len(vals) // 2]
    assert 0.10 < mid < 0.90


def test_borrow_respects_the_frozen_neighbour_cap_and_radius():
    """Beyond SEGMENT_MAX_PX from *every* segment nothing is borrowed, however well oriented."""
    s = _synthetic_seg(gap_px=8.0)
    beyond = 8.0 + K.SEGMENT_MAX_PX + 0.5     # past the farther of the two segments
    far, _ = K.borrow_kinematics(np.array([[beyond, -0.5]]), np.array([0.0]), s)
    assert np.isnan(far[0])
    just_inside, _ = K.borrow_kinematics(np.array([[beyond - 1.0, -0.5]]), np.array([0.0]), s)
    assert np.isfinite(just_inside[0])


def test_borrow_ignores_a_well_oriented_segment_that_is_too_far():
    """Radius is a hard gate: perfect strike agreement at 11 px must still yield neutral."""
    one = {"trace_colrow": np.array([[0.0, 0.0], [0.0, -1.0]]),
           "trace_owner": np.array([0, 0], dtype=np.int32),
           "strike": np.array([0.0]), "TS": np.array([0.42]), "TD": np.array([0.77]),
           "n_segments": 1}
    at_limit, _ = K.borrow_kinematics(np.array([[K.SEGMENT_MAX_PX - 0.25, -0.5]]), np.array([0.0]), one)
    past_limit, _ = K.borrow_kinematics(np.array([[K.SEGMENT_MAX_PX + 0.25, -0.5]]), np.array([0.0]), one)
    assert at_limit[0] == pytest.approx(0.42)
    assert np.isnan(past_limit[0])


def test_favourability_neutral_default_and_coverage_bounds(seg):
    geod_ref = np.linspace(0.0, 100.0, 1000)
    tr = seg["trace_colrow"]
    owner = seg["trace_owner"]
    idx = np.linspace(0, len(tr) - 1, 200).astype(int)
    dots = tr[idx]
    strikes = seg["strike"][owner[idx]]
    fav, cov = K.favourability(dots, strikes, seg, np.full(len(dots), 50.0), geod_ref)
    assert 0.0 <= cov <= 1.0
    finite = fav[np.isfinite(fav)]
    assert len(finite) and finite.min() >= 0.0 and finite.max() <= 1.0
    # a dot with no neighbour must be NaN, never 0.0 - 0.0 would look prunable
    far, far_cov = K.favourability(np.array([[-9000.0, -9000.0]]), np.array([10.0]), seg,
                                   np.array([50.0]), geod_ref)
    assert np.isnan(far[0]) and far_cov == 0.0


def test_favourability_is_deterministic_and_seed_independent(seg):
    """The frozen score must not drift with fold or seed: it has no random component."""
    geod_ref = np.linspace(0.0, 100.0, 500)
    tr = seg["trace_colrow"]
    owner = seg["trace_owner"]
    idx = np.linspace(0, len(tr) - 1, 100).astype(int)
    dots, strikes = tr[idx], seg["strike"][owner[idx]]
    a, ca = K.favourability(dots, strikes, seg, np.full(len(dots), 40.0), geod_ref)
    b, cb = K.favourability(dots, strikes, seg, np.full(len(dots), 40.0), geod_ref)
    assert ca == cb
    assert np.array_equal(a[np.isfinite(a)], b[np.isfinite(b)])


# --------------------------------------------------------------------------------------------
# the committed data precondition (knowledge/19 section 0)
# --------------------------------------------------------------------------------------------
def test_committed_clip_satisfies_the_frozen_data_precondition():
    assert CLIP.exists(), "runner bridge has not produced docs/data/sb_slip_tendency_in_footprint.json"
    doc = json.loads(CLIP.read_text())
    layer = next(iter(doc["schema"]["layers"].values()))
    fields = layer["attribute_fields"]
    assert "TS" in fields and "TD" in fields, "slip/dilation-tendency fields missing"
    assert layer["n_features_in_bbox"] > 0
    assert len(doc["records"]) == layer["n_features_in_bbox"]
    assert layer["target_crs"] == "EPSG:32611"
    assert tuple(layer["bbox_32611"]) == (243350.0, 4135550.0, 572550.0, 4508550.0)


def test_load_segments_drops_records_without_both_tendencies():
    """A missing measurement must not be silently read as the least favourable value."""
    doc = {"schema": {"layers": {"x": {"attribute_fields": {"TS": "float", "TD": "float"}}}},
           "records": [
               {"parts": [[[0.0, 0.0], [100.0, 0.0]]], "TS": 0.3, "TD": 0.6, "Strike": 90.0},
               {"parts": [[[0.0, 0.0], [0.0, 100.0]]], "TS": None, "TD": 0.6, "Strike": 0.0},
               {"parts": [[[0.0, 0.0], [100.0, 100.0]]], "TS": 0.2, "TD": None, "Strike": 45.0},
           ]}
    tmp = Path("/tmp/_kin_test_clip.json")
    tmp.write_text(json.dumps(doc))
    s = K.load_segments(tmp)
    assert s["n_segments"] == 1 and s["n_records_dropped"] == 2


def test_load_segments_raises_on_an_empty_clip():
    tmp = Path("/tmp/_kin_empty_clip.json")
    tmp.write_text(json.dumps({"schema": {"layers": {"x": {"attribute_fields": {}}}}, "records": []}))
    with pytest.raises(ValueError, match="no usable"):
        K.load_segments(tmp)
