"""Known-answer tests for the S30 nine-site byte audit and its decision builder.

These use synthetic rasters with analytically known overlap, correlation and format results,
so they run without the restored competition data.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


audit = _load("audit_nine_site_bytes", "scripts/audit_nine_site_bytes.py")
builder = _load("build_s30_review", "scripts/build_s30_review.py")


def test_within_radius_known_answer():
    b = np.zeros((20, 20), dtype=bool)
    b[10, 10] = True
    a = np.zeros((20, 20), dtype=bool)
    a[10, 13] = True  # exactly 3 px away: inside the 3-px radius
    a[10, 14] = True  # 4 px away: outside
    assert audit.within_radius(a, b) == pytest.approx(0.5)


def test_within_radius_empty_sets():
    empty = np.zeros((5, 5), dtype=bool)
    some = empty.copy()
    some[2, 2] = True
    assert audit.within_radius(some, empty) == 0.0
    assert audit.within_radius(empty, some) == 0.0


def test_phi_identical_and_complement():
    rng = np.random.default_rng(0)
    x = rng.random((30, 30)) > 0.5
    footprint = np.ones_like(x, dtype=bool)
    assert audit.phi(x, x, footprint) == pytest.approx(1.0)
    assert audit.phi(x, ~x, footprint) == pytest.approx(-1.0)


def test_read_binary_format_and_range(tmp_path: Path):
    shape = (4, 5)
    arr = np.zeros(shape, dtype="float32")
    arr[1, 1] = 1.0
    arr[2, 3] = 1.0
    arr[0, 4] = np.nan  # outside-footprint style NaN
    path = tmp_path / "t.tif"
    with rasterio.open(
        path, "w", driver="GTiff", height=shape[0], width=shape[1], count=1, dtype="float32",
        crs="EPSG:32611", transform=from_origin(243350.0, 4508550.0, 100.0, 100.0), nodata=np.nan,
    ) as dst:
        dst.write(arr, 1)
    finite, positive, record = audit.read_binary(path)
    assert record["count"] == 1
    assert record["dtype"] == "float32"
    assert record["nan_pixels"] == 1
    assert record["positive_pixels"] == 2
    assert record["in_0_1_all_finite"] is True
    # Synthetic grid is not the competition grid, so the grid match must be False.
    assert record["format_matches_grid"] is False
    assert int(positive.sum()) == 2


def test_decision_fails_closed_for_overlapping_sites():
    """Two sites with identical dots must be flagged as not unique and not OK to submit."""
    overlap = {"A": {"B": 1.0}, "B": {"A": 1.0}}
    phi = {"A": {"B": 1.0}, "B": {"A": 1.0}}
    files = {
        s: {
            "status": "READ",
            "file": f"{s}/x.tif",
            "sha256": "0" * 64,
            "claimed_score": 0.1,
            "positive_pixels": 10,
            "format_matches_grid": True,
            "in_0_1_all_finite": True,
            "nan_pixels": 0,
        }
        for s in ("A", "B")
    }
    rows = builder.site_rows({"files": files, "overlap_3px": overlap, "phi_footprint": phi})
    assert all(r["unique_under_lane_rule"] is False for r in rows)
    assert all(r["ok_to_download_and_submit"] is False for r in rows)
    assert {r["identical_to"][0] for r in rows} == {"B", "A"}
