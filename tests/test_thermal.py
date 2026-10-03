"""Unit tests for the GDR-1391 hydrothermal-discharge layer (`src/gems27/thermal.py`).

The load-bearing properties are: (1) the catalogue-derived column can never reach an arm, (2) the
table is registered on the competition grid, (3) `marginal_credit` does not double count truth pixels
already credited by the base emission, and (4) `sites_mask` filters on the right variable.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from scipy.ndimage import distance_transform_edt

from gems27 import grid, paths, thermal


def _frame(rows, cols, temps):
    xs, ys = grid.rc_to_xy(np.asarray(rows, float), np.asarray(cols, float))
    return pd.DataFrame({
        "layer": ["well_temperature_20220808"] * len(rows),
        "name": ["site"] * len(rows),
        "thermalclass": ["Hot"] * len(rows),
        "row": rows, "col": cols,
        "utm_x": xs, "utm_y": ys,
        "dist_known_fault_px": np.zeros(len(rows)),
        "temp_c": temps,
        "geothermquartz_c": list(temps), "geothermchalc_c": [np.nan] * len(rows),
        "geothermcat_c": [np.nan] * len(rows),
    })


def test_audit_frame_registration_accepts_consistent_coordinates():
    df = _frame([10, 2000], [30, 1500], [25.0, 80.0])
    a = thermal.audit_frame(df)
    assert a["registration_ok"] is True
    assert a["max_abs_row_residual_px"] <= 1.0
    assert a["max_abs_col_residual_px"] <= 1.0
    assert a["n_records_raw"] == 2


def test_audit_frame_rejects_misregistration():
    df = _frame([10, 2000], [30, 1500], [25.0, 80.0])
    df.loc[1, "col"] = df.loc[1, "col"] + 40  # 4 km off the geotransform
    a = thermal.audit_frame(df)
    assert a["registration_ok"] is False


def test_audit_frame_requires_columns():
    df = _frame([1], [1], [10.0]).drop(columns=["utm_y"])
    with pytest.raises(thermal.ThermalDataError, match="missing required columns"):
        thermal.audit_frame(df)


def test_load_sites_drops_the_catalogue_derived_column(tmp_path):
    df = _frame([10, 2000], [30, 1500], [25.0, 80.0])
    p = tmp_path / "sites.csv"
    df.to_csv(p, index=False)
    sites = thermal.load_sites(p)
    assert "dist_known_fault_px" not in sites.columns
    assert len(sites) == 2
    assert not any(c in sites.columns for c in thermal.CATALOGUE_DERIVED_COLUMNS)


def test_load_sites_dedupes_and_takes_the_maximum(tmp_path):
    df = pd.concat([_frame([10], [30], [25.0]), _frame([10], [30], [61.0])], ignore_index=True)
    p = tmp_path / "sites.csv"
    df.to_csv(p, index=False)
    sites = thermal.load_sites(p)
    assert len(sites) == 1
    assert sites.loc[0, "temp_c"] == pytest.approx(61.0)
    assert sites.loc[0, "n_records"] == 2


def test_sites_mask_threshold_and_cutoff():
    rng = np.random.default_rng(0)
    foot = np.zeros(grid.SHAPE, bool)
    foot[0:50, 0:50] = True
    rows = [5, 6, 7]
    cols = [5, 6, 7]
    df = _frame(rows, cols, [10.0, 30.0, 70.0])
    sites = df.drop(columns=["dist_known_fault_px"])[list(thermal.SITE_COLUMNS)]
    sites["row"] = rows
    sites["col"] = cols
    m_all = thermal.sites_mask(sites, foot, temp_c_min=None)
    assert int(m_all.sum()) == 3
    m_20 = thermal.sites_mask(sites, foot, temp_c_min=20.0)
    assert int(m_20.sum()) == 2
    m_50 = thermal.sites_mask(sites, foot, temp_c_min=50.0)
    assert int(m_50.sum()) == 1
    # outside the footprint is clipped away
    assert int(m_all[29, 29]) == 0
    assert rng is not None


def test_marginal_credit_is_an_increment_not_a_recount():
    base = np.zeros((60, 60), bool)
    base[30, 30] = True
    adds = np.zeros((60, 60), bool)
    adds[30, 31] = True  # 1 px from the base dot -> nearly no new credit
    truth = np.zeros((60, 60), bool)
    truth[30, 30] = True
    assert thermal.marginal_credit(base, adds, truth) == pytest.approx(0.0, abs=1e-6)
    # a dot right on the truth pixel adds real credit
    adds2 = np.zeros((60, 60), bool)
    adds2[45, 45] = True
    truth2 = np.zeros((60, 60), bool)
    truth2[45, 45] = True
    assert thermal.marginal_credit(base, adds2, truth2) == pytest.approx(1.0, abs=1e-6)


def test_marginal_credit_matches_brute_force():
    rng = np.random.default_rng(7)
    base = rng.random((40, 40)) > 0.99
    adds = rng.random((40, 40)) > 0.99
    truth = rng.random((40, 40)) > 0.98
    if not truth.any():
        truth[10, 10] = True
    got = thermal.marginal_credit(base, adds, truth)
    d0 = distance_transform_edt(~base)[truth]
    d1 = distance_transform_edt(~(base | adds))[truth]
    k0 = np.maximum(1.0 - d0 / grid.KERNEL_RADIUS_PX, 0.0)
    k1 = np.maximum(1.0 - d1 / grid.KERNEL_RADIUS_PX, 0.0)
    assert got == pytest.approx(float(k1.sum() - k0.sum()), rel=0, abs=1e-9)


def test_stratify_splits_on_distance():
    dots = np.zeros((40, 40), bool)
    dots[10, 10] = True
    dots[30, 30] = True
    mask = np.zeros((40, 40), bool)
    mask[10, 10] = True
    near, far = thermal.stratify(dots, mask, near_px=3)
    assert near.shape[0] == 1 and tuple(near[0]) == (10, 10)
    assert far.shape[0] == 1 and tuple(far[0]) == (30, 30)


def test_real_table_is_registered_when_present():
    if not paths.WELLSPRING.is_file():
        pytest.skip("GDR well/spring table not restored in this checkout")
    sites = thermal.load_sites(paths.WELLSPRING)
    audit = sites.attrs["audit"]
    assert audit["registration_ok"] is True
    assert audit["n_records_raw"] > 20_000
    assert len(sites) > 10_000
    assert "dist_known_fault_px" not in sites.columns
    assert sites["row"].between(0, grid.SHAPE[0] - 1).all()
    assert sites["col"].between(0, grid.SHAPE[1] - 1).all()
