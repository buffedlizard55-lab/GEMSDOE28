"""Hermetic tests for the H35-1 hydrothermal-conjunction module (Session 11).

All fixtures are synthetic; no rasters, no network, no seeds. The preregistered constants live in
knowledge/24 - these tests pin the behaviour the gate depends on, including the leakage guard that
the wellspring CSV's full-catalogue distance column is never read.
"""

import numpy as np
import pandas as pd
from scipy.ndimage import distance_transform_edt

from gems27 import hydrothermal as H


def _wellspring_csv(tmp_path, rows):
    path = tmp_path / "wellspring.csv"
    pd.DataFrame(rows).to_csv(path, index=False)
    return path


def test_hot_cells_use_either_leg_nan_safe_and_dedup_to_200m(tmp_path):
    path = _wellspring_csv(tmp_path, [
        {"temp_c": 78.0, "geothermquartz_c": float("nan"), "row": 10, "col": 10},  # temp leg
        {"temp_c": float("nan"), "geothermquartz_c": 150.0, "row": 20, "col": 20},  # qtz leg
        {"temp_c": 32.0, "geothermquartz_c": 96.0, "row": 50, "col": 50},  # neither
        {"temp_c": float("nan"), "geothermquartz_c": float("nan"), "row": 60, "col": 60},  # missing
        {"temp_c": 59.9, "geothermquartz_c": 129.9, "row": 70, "col": 70},  # just below both cuts
        {"temp_c": 200.0, "geothermquartz_c": 200.0, "row": 10, "col": 11},  # same 200 m cell as row 0
    ])
    out = H.load_hot_cells(path, (100, 100))
    assert out["n_rows"] == 6
    assert out["n_rows_hot"] == 3
    assert out["n_cells"] == 2, "rows 0, 1 and 5 are hot but 0+5 share one 200 m cell"
    assert out["hot"].sum() == 2


def test_hot_cells_never_read_the_full_catalogue_distance_column(tmp_path):
    """The CSV's dist_known_fault_px is measured vs the FULL catalogue (held-out systems
    included), so reading it inside a LOSFO cell would leak. usecols excludes it - prove it by
    feeding a CSV without that column at all."""
    path = _wellspring_csv(tmp_path, [
        {"temp_c": 80.0, "geothermquartz_c": 90.0, "row": 5, "col": 5},
    ])
    out = H.load_hot_cells(path, (20, 20))
    assert out["n_cells"] == 1
    # and a CSV that HAS the column must give identical results (the column is ignored)
    df = pd.read_csv(path)
    df["dist_known_fault_px"] = [0.0]
    path2 = tmp_path / "w2.csv"
    df.to_csv(path2, index=False)
    out2 = H.load_hot_cells(path2, (20, 20))
    assert out2["n_cells"] == out["n_cells"]


def test_thermal_proximity_radius_and_empty_grid():
    hot = np.zeros((30, 30), bool)
    hot[15, 15] = True
    prox = H.thermal_proximity(hot, 10.0)
    assert prox[15, 25] and not prox[15, 26]
    assert prox.sum() > 0
    assert not H.thermal_proximity(np.zeros((5, 5), bool)).any()


def test_alteration_halo_uses_valid_only_and_zeros_are_never_halo():
    rng = np.random.default_rng(0)
    thk = np.zeros((40, 40), np.uint8)
    uth = np.zeros((40, 40), np.uint8)
    thk[5:35, 5:35] = rng.integers(1, 255, size=(30, 30), dtype=np.uint8)
    uth[5:35, 5:35] = rng.integers(1, 255, size=(30, 30), dtype=np.uint8)
    out = H.alteration_halo(thk, uth)
    assert out["valid_frac"] == (30 * 30) / (40 * 40)
    assert out["thk_cut"] is not None and out["uth_cut"] is not None
    # zeros are nodata: no halo pixel may sit on a zero-ThK pixel
    assert not (out["halo"] & (thk == 0)).any()
    # halo pixels satisfy both quantile legs
    assert bool(((thk[out["halo"]] <= out["thk_cut"]) &
                 (uth[out["halo"]] >= out["uth_cut"])).all())
    assert out["halo"].sum() > 0
    # degenerate: no valid coverage -> no halo, cuts None
    empty = H.alteration_halo(np.zeros((4, 4), np.uint8), np.zeros((4, 4), np.uint8))
    assert not empty["halo"].any() and empty["thk_cut"] is None


def test_euler_halo_rounds_centroids_and_clips():
    halo = H.euler_halo(np.array([10.4, -50.0, 9999.0]), np.array([10.6, 5.0, 5.0]), (30, 30), 3.0)
    assert halo[10, 11] and halo[0, 5] and halo[29, 5]
    assert halo.sum() > 3


def test_subthreshold_partitions_candidate_ridge_and_contains_a_thinned_base():
    rng = np.random.default_rng(1)
    shape = (60, 60)
    fold = np.zeros(shape, bool)
    fold[:, 30:] = True
    known = np.zeros(shape, bool)
    known[40, 40] = True
    ridge = rng.random(shape) < 0.05
    prob = rng.random(shape).astype(np.float32)
    out = H.subthreshold_ridge(prob, ridge, fold, known, 0.0245)
    cand = ridge & fold & ~known
    assert (out["selected"] | out["subthreshold"] == cand).all()
    assert not (out["selected"] & out["subthreshold"]).any()
    assert out["selected"].sum() == min(out["k"], cand.sum())
    # the shipped base is a thinned subset of selected (thinning only drops)
    from gems27 import oof_detector, thinning

    base = thinning.dot_thin(out["selected"], 2.8)
    assert (base & ~out["selected"]).sum() == 0
    assert oof_detector.PRE_THIN_FRAC == 0.0245


def test_select_additions_respects_budget_spacing_far_field_and_thermal():
    shape = (80, 80)
    rng = np.random.default_rng(2)
    prob = rng.random(shape).astype(np.float64)
    sub = rng.random(shape) < 0.10
    base = np.zeros(shape, bool)
    base[20, 20] = True
    known = np.zeros(shape, bool)
    known[60:65, 60:65] = True
    thermal = np.zeros(shape, bool)
    thermal[10:30, 10:30] = True
    halo = rng.random(shape) < 0.2
    euler = np.zeros(shape, bool)
    res = H.select_additions(prob=prob, subthreshold=sub, base=base, known=known,
                             thermal=thermal, halo=halo, euler=euler, budget_dots=25)
    added = res["added"]
    assert res["info"]["n_selected"] <= 25
    assert added.sum() == res["info"]["n_added"] <= res["info"]["n_selected"]
    assert (added & ~sub).sum() == 0, "added dots must come from the sub-threshold pool"
    assert (added & ~thermal).sum() == 0, "primary requires thermal proximity"
    d_known = distance_transform_edt(~known)
    assert bool((d_known[added] >= 3.0).all()), "added dots must be far-field"
    d_base = distance_transform_edt(~base)
    assert bool((d_base[added] >= 2.8).all()), "added dots must clear base dots by 2.8 px"
    # determinism: same inputs -> identical outputs, ties broken by raster order
    res2 = H.select_additions(prob=prob, subthreshold=sub, base=base, known=known,
                              thermal=thermal, halo=halo, euler=euler, budget_dots=25)
    assert (res2["added"] == added).all()


def test_select_control_excludes_thermal_and_scores_by_probability_only():
    shape = (50, 50)
    rng = np.random.default_rng(3)
    prob = rng.random(shape).astype(np.float64)
    sub = rng.random(shape) < 0.15
    base = np.zeros(shape, bool)
    known = np.zeros(shape, bool)
    thermal = np.zeros(shape, bool)
    thermal[:, :25] = True
    halo = np.ones(shape, bool)  # bonuses must not leak into the control's ranking
    euler = np.ones(shape, bool)
    res = H.select_additions(prob=prob, subthreshold=sub, base=base, known=known,
                             thermal=thermal, halo=halo, euler=euler, budget_dots=10,
                             require_thermal=False)
    added = res["added"]
    assert (added & thermal).sum() == 0, "the direction control must avoid hot halos"
    # with uniform bonuses the ranking is by probability: every added dot beats every
    # eligible-but-unselected dot (up to thinning drops, which only remove)
    elig = sub & ~thermal
    ys, xs = np.nonzero(elig)
    assert added.sum() > 0
    assert prob[added].min() >= np.sort(prob[ys, xs])[-10:].min() - 1e-12


def test_frozen_defaults_match_the_preregistration():
    assert (H.TEMP_C_CUT, H.QTZ_C_CUT, H.DEDUP_PX, H.THERMAL_PX) == (60.0, 130.0, 2, 10.0)
    assert (H.THK_Q, H.UTH_Q, H.EULER_PX, H.FAR_PX) == (25.0, 75.0, 3.0, 3.0)
    assert (H.BUDGET_FRAC, H.THIN_D, H.BONUS) == (0.02, 2.8, 0.5)
