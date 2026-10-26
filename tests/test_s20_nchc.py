"""Unit tests for Session 20 lane S20-NCHC (src/gems27/s20_nchc.py)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from gems27 import s20_nchc


def test_feature_name_count_and_no_raw_levels() -> None:
    assert len(s20_nchc.S20_FEATURE_NAMES) == 28
    assert len(set(s20_nchc.S20_FEATURE_NAMES)) == 28
    raw_levels = {"det_elev", "rtp", "tmi", "iso_grav_anom", "depth_to_base_surf", "cond_surf", "tc"}
    assert raw_levels.isdisjoint(s20_nchc.S20_FEATURE_NAMES)


def test_frangi_director_cardinal_and_diagonal_strikes() -> None:
    yy, xx = np.mgrid[0:81, 0:81].astype(np.float32)
    foot = np.ones((81, 81), dtype=bool)
    c = 40

    # 1. N-S fault step: field steps across x (strike = 0 deg -> cos2 = +1, sin2 = 0)
    f_ns = np.tanh((xx - 40.0) / 2.0)
    tub_ns, c2_ns, s2_ns = s20_nchc.frangi_tubular_and_director(f_ns, foot, 2.0)
    assert tub_ns[c, c] > 0.8
    assert c2_ns[c, c] > 0.98
    assert abs(float(s2_ns[c, c])) < 0.05

    # 2. E-W stripe step: field steps across y (strike = 90 deg -> cos2 = -1, sin2 = 0)
    f_ew = np.tanh((yy - 40.0) / 2.0)
    tub_ew, c2_ew, s2_ew = s20_nchc.frangi_tubular_and_director(f_ew, foot, 2.0)
    assert tub_ew[c, c] > 0.8
    assert c2_ew[c, c] < -0.98
    assert abs(float(s2_ew[c, c])) < 0.05

    # E-W flight-line diagnostic fires on E-W step and vanishes on N-S step
    ew_diag_on_ew = float(tub_ew[c, c] * max(0.0, -float(c2_ew[c, c])) ** 2)
    ew_diag_on_ns = float(tub_ns[c, c] * max(0.0, -float(c2_ns[c, c])) ** 2)
    assert ew_diag_on_ew > 0.75
    assert ew_diag_on_ns == 0.0

    # 3. NE-SW fault step: along NE (+x, -y) -> x + y = const -> steps across (x + y - 80)
    f_ne = np.tanh((xx + yy - 80.0) / 2.8)
    _, c2_ne, s2_ne = s20_nchc.frangi_tubular_and_director(f_ne, foot, 2.0)
    assert abs(float(c2_ne[c, c])) < 0.05
    assert s2_ne[c, c] > 0.98

    # 4. NW-SE fault step: along SE (+x, +y) -> x - y = const -> steps across (x - y)
    f_nw = np.tanh((xx - yy) / 2.8)
    _, c2_nw, s2_nw = s20_nchc.frangi_tubular_and_director(f_nw, foot, 2.0)
    assert abs(float(c2_nw[c, c])) < 0.05
    assert s2_nw[c, c] < -0.98


def test_nematic_concordance_coaligned_vs_orthogonal_and_blind_fault() -> None:
    foot = np.ones((5, 5), dtype=bool)
    w_hi = np.full((5, 5), 0.9, dtype=np.float32)
    w_zero = np.zeros((5, 5), dtype=np.float32)
    c_ns = np.ones((5, 5), dtype=np.float32)
    c_ew = -np.ones((5, 5), dtype=np.float32)
    s_zero = np.zeros((5, 5), dtype=np.float32)

    # Co-aligned blind fault (mag + grav strong N-S; em_cb + topo zero under playa)
    nem_co, harm_co = s20_nchc.nematic_concordance_and_harmonic(
        [w_hi, w_hi, w_zero, w_zero],
        [c_ns, c_ns, c_ns, c_ns],
        [s_zero, s_zero, s_zero, s_zero],
        foot,
    )
    assert np.allclose(nem_co, 1.0, atol=1e-4)
    assert np.allclose(harm_co, 0.9, atol=1e-4)

    # Orthogonal conflict (mag N-S vs grav E-W) -> nematic order cancels to ~0
    nem_orth, _ = s20_nchc.nematic_concordance_and_harmonic(
        [w_hi, w_hi, w_zero, w_zero],
        [c_ns, c_ew, c_ns, c_ns],
        [s_zero, s_zero, s_zero, s_zero],
        foot,
    )
    assert np.allclose(nem_orth, 0.0, atol=1e-4)


def test_wellspring_plumes_never_read_dist_known_fault_px(tmp_path: Path) -> None:
    foot = np.ones((40, 40), dtype=bool)
    csv_a = tmp_path / "ws_no_dist.csv"
    pd.DataFrame({
        "row": [10, 25],
        "col": [12, 30],
        "temp_c": [72.0, 18.0],
        "geothermquartz_c": [145.0, np.nan],
        "geothermchalc_c": [np.nan, 40.0],
    }).to_csv(csv_a, index=False)

    csv_b = tmp_path / "ws_poison_dist.csv"
    pd.DataFrame({
        "row": [10, 25],
        "col": [12, 30],
        "temp_c": [72.0, 18.0],
        "geothermquartz_c": [145.0, np.nan],
        "geothermchalc_c": [np.nan, 40.0],
        "dist_known_fault_px": [0.0, 999999.0],
    }).to_csv(csv_b, index=False)

    d_a, t_a, _ = s20_nchc.load_wellspring_plumes(csv_a, foot, sigma_px=4.0)
    d_b, t_b, _ = s20_nchc.load_wellspring_plumes(csv_b, foot, sigma_px=4.0)
    assert np.array_equal(d_a, d_b)
    assert np.array_equal(t_a, t_b)
    assert d_a[10, 12] > 0.5
    assert t_a[10, 12] > 0.5


def test_fold_isolation_zero_leakage_from_withheld_truth() -> None:
    rng = np.random.default_rng(123)
    H, W = 50, 50
    foot = np.ones((H, W), dtype=bool)
    X_foot = rng.normal(size=(H * W, 28)).astype(np.float32)

    train_mask = np.zeros((H, W), dtype=bool)
    train_mask[:25, :] = True
    eval_mask = ~train_mask

    visible = np.zeros((H, W), dtype=bool)
    visible[5:20, 10] = True
    visible[30:40, 15] = True
    # Boost feature 0 on faults so model learns a real signal
    X_2d = X_foot.reshape(H, W, 28)
    X_2d[visible, 0] += 3.0

    # Variant A: zero withheld faults; Variant B: dense withheld faults in eval quadrant
    pos_a = visible.copy()
    pos_b = visible.copy()
    pos_b[28:48, 35] = True

    prob_a, _ = s20_nchc.fit_predict_prior_calibrated_hgb(X_foot, foot, train_mask, pos_a, seed=340, max_neg=500)
    prob_b, _ = s20_nchc.fit_predict_prior_calibrated_hgb(X_foot, foot, train_mask, pos_b, seed=340, max_neg=500)
    assert np.array_equal(prob_a, prob_b)

    pred_a, info_a = s20_nchc.allocate_corridor_submodular(prob_a, eval_mask, visible, budget_frac=0.02)
    pred_b, info_b = s20_nchc.allocate_corridor_submodular(prob_b, eval_mask, visible, budget_frac=0.02)
    assert np.array_equal(pred_a, pred_b)
    assert info_a["n_selected"] > 0
    # Verify B=2 clearance from visible catalogue strictly holds
    from scipy.ndimage import distance_transform_edt
    d_vis = distance_transform_edt(~visible)
    assert not np.any((pred_a > 0) & (d_vis <= 2.0))
