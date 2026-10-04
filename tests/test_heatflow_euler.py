"""Unit tests for src/gems27/heatflow_euler.py (Session 14 H38 corroboration)."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest
from scipy.ndimage import distance_transform_edt

from gems27 import grid, heatflow_euler, paths


def test_load_heatflow_residual_cells_synthetic(tmp_path: Path) -> None:
    foot = np.zeros((20, 20), dtype=bool)
    foot[2:18, 2:18] = True
    # Pick two valid grid coordinates and convert to UTM (x, y)
    x0, y0 = grid.rc_to_xy(np.array([5, 10, 19]), np.array([6, 12, 19]))
    payload = {
        "schema": {
            "layers": {
                heatflow_euler.HF_LAYER_NAME: {
                    "attribute_fields": {heatflow_euler.HF_RESID_COL: {"sample": 60.0}}
                }
            }
        },
        "records": [
            {
                "source_layer": heatflow_euler.HF_LAYER_NAME,
                "parts": [[[float(x0[0]), float(y0[0])]]],
                "hf_resid": 80.0,
            },
            {
                "source_layer": heatflow_euler.HF_LAYER_NAME,
                "parts": [[[float(x0[1]), float(y0[1])]]],
                "hf_resid": 20.0,
            },
            {
                # Outside footprint (row 19, col 19)
                "source_layer": heatflow_euler.HF_LAYER_NAME,
                "parts": [[[float(x0[2]), float(y0[2])]]],
                "hf_resid": 150.0,
            },
        ],
    }
    p = tmp_path / "hf.json"
    p.write_text(json.dumps(payload), encoding="utf-8")
    res = heatflow_euler.load_heatflow_residual_cells(p, foot, resid_min=50.0)
    assert res["n_in_bbox"] == 3
    assert res["n_in_footprint"] == 2
    assert res["n_records_above_cut"] == 1
    assert res["n_cells_100m"] == 1
    assert bool(res["mask"][5, 6]) is True
    assert bool(res["mask"][10, 12]) is False


def test_load_euler_contact_clusters_synthetic(tmp_path: Path) -> None:
    p = tmp_path / "euler.csv"
    p.write_text(
        "cluster_id,row,col,median_depth_m,depth_mad_m,n_solutions\n"
        "0,4.2,5.8,250.0,35.0,12\n"
        "1,8.0,9.0,650.0,20.0,15\n"
        "2,11.0,12.0,200.0,85.0,10\n"
        "3,14.0,15.0,200.0,30.0,5\n",
        encoding="utf-8",
    )
    res = heatflow_euler.load_euler_contact_clusters(p, (20, 20))
    assert res["n_total_clusters"] == 4
    assert res["n_kept_clusters"] == 1
    assert res["n_cells_100m"] == 1
    assert bool(res["mask"][4, 6]) is True


def test_select_corroborated_ridge_dots_invariants() -> None:
    H, W = 60, 60
    active = np.ones((H, W), dtype=bool)
    known = np.zeros((H, W), dtype=bool)
    known[5, 5] = True
    base = np.zeros((H, W), dtype=bool)
    base[10, 10] = True

    ridge = np.zeros((H, W), dtype=bool)
    ridge[25, 10:50] = True
    ridge[40, 10:50] = True

    prob = np.linspace(0.1, 0.9, H * W).reshape(H, W)
    cond_mask = np.zeros((H, W), dtype=bool)
    cond_mask[25, 10:50] = True
    score_mult = 1.0 + 0.5 * cond_mask.astype(float)

    out = heatflow_euler.select_corroborated_ridge_dots(
        prob,
        ridge,
        active,
        base,
        known,
        cond_mask,
        score_mult=score_mult,
        k_cap=20,
        min_dist_base=2.8,
        min_dist_known=3.0,
        thin_d=2.8,
        rng_seed=42,
    )
    added = out["added"]
    ctrl_sub = out["control_sub_ridge"]
    ctrl_rand = out["control_random"]

    assert out["n_added"] > 0
    assert out["n_control_sub_ridge"] > 0
    assert out["n_control_random"] == out["n_added"]
    assert not (added & base).any()
    assert not (added & known).any()
    assert not (ctrl_rand & base).any()
    assert not (ctrl_rand & known).any()
    assert (added & cond_mask).sum() == out["n_added"]
    assert (ctrl_sub & cond_mask).sum() == 0
    d_kn = distance_transform_edt(~known)
    d_b = distance_transform_edt(~base)
    assert float(d_kn[added].min()) >= 3.0 - 1e-6
    assert float(d_b[added].min()) >= 2.8 - 1e-6


@pytest.mark.skipif(
    not (paths.REPO / "docs/data/sb_heat_flow_in_footprint.json").is_file()
    or not paths.TEMPLATE.is_file(),
    reason="Real footprint or sb_heat_flow_in_footprint.json unavailable",
)
def test_real_heatflow_and_euler_corroboration_fields() -> None:
    foot = grid.load_footprint(paths.TEMPLATE)
    fields = heatflow_euler.build_corroboration_fields(
        foot,
        hf_json_path=paths.REPO / "docs/data/sb_heat_flow_in_footprint.json",
        euler_csv_path=paths.EVIDENCE / "h31_1_euler_clusters.csv",
        lidar_path=paths.LIDAR,
    )
    meta = fields["meta"]
    assert meta["heatflow"]["n_in_bbox"] == 2108
    assert meta["heatflow"]["n_in_footprint"] == 1546
    assert meta["heatflow"]["n_records_above_cut"] == 753
    assert meta["euler"]["n_total_clusters"] == 6309
    assert meta["euler"]["n_kept_clusters"] == 1435
    assert fields["score_mult"].shape == foot.shape
    assert set(np.unique(fields["score_mult"])).issubset({1.0, 1.5, 2.0})


def test_harness_h36_1_and_h38_synthetic() -> None:
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "run_losfo_harness", paths.REPO / "scripts" / "run_losfo_harness.py"
    )
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    H, W = 80, 80
    fm = np.ones((H, W), dtype=bool)
    known = np.zeros((H, W), dtype=bool)
    known[5, 5:20] = True
    # Hidden truth sits >= 8 px from known (row 50)
    hidden = np.zeros((H, W), dtype=bool)
    hidden[50, 10:70] = True
    active = fm & ~known

    prob = np.linspace(0.05, 0.95, H * W).reshape(H, W)
    ridge = np.zeros((H, W), dtype=bool)
    ridge[6, 5:20] = True  # within 1 px of known -> pruned by blind_r1 with zero TP loss!
    ridge[50, 10:70] = True
    ridge[30, 10:70] = True

    from gems27 import oof_detector

    base_d28 = (
        oof_detector.build_oof_dotted_base(
            prob, ridge, fm, known, budget_frac=0.20, thin_d=2.8
        )
        & active
    )
    r_base = mod.eval_set(base_d28, hidden, active)
    h36 = mod.h36_1_farfield_arms(prob, ridge, fm, known, base_d28, active, hidden, 265, 0)
    # Since hidden is at row 50 and known is at row 5, blind_r1 cannot remove any TP!
    assert abs(h36["base"]["tp"] - h36["h27_4_blind_r1_d280"]["tp"]) < 1e-9

    fields = {
        "joint_mask": np.ones((H, W), dtype=bool),
        "hf_halo": np.ones((H, W), dtype=bool),
        "euler_halo": np.ones((H, W), dtype=bool),
        "low_relief_euler_mask": np.ones((H, W), dtype=bool),
        "score_mult": np.full((H, W), 2.0, dtype=np.float64),
        "meta": {"test": True},
    }
    sl = (slice(0, H), slice(0, W))
    h38 = mod.h38_corroboration_arms(
        prob, ridge, fm, known, base_d28, active, hidden, fields, sl, 265, 0, r_base
    )
    assert "h38_1_joint" in h38
    assert "h38_1a_heatflow" in h38
    assert "h38_1b_euler_lineament" in h38
    assert "h38_2_low_relief_euler" in h38
    assert "h38_1_joint_on_r30_r1" in h38

    cells = [
        {
            "seed": 265,
            "fold": "NW",
            "h36_1": {"losfo": h36, "leaky": h36},
            "h38": h38,
        }
    ]
    s36 = mod.summarize_h36_1_farfield(cells)
    s38 = mod.summarize_h38_corroboration(cells, fields["meta"])
    assert s36["detectors"]["losfo"]["F4_h27_4_blind_r1_vs_base"]["exact_zero_tp_loss_all_cells"]
    assert "h38_1_joint" in s38["arms"]

