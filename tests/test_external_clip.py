"""Tests for `src/gems27/external_clip.py` (official-release -> in-footprint derived table).

The clip is the step that turns a byte-verified official release into something a session can read
without reaching the science host, so the invariants that matter are: nothing outside the footprint
leaks in, part endpoints survive thinning, attributes are copied verbatim (none invented), and the
reader path works end to end on a real shapefile.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gems27 import external_clip as ec  # noqa: E402

pyogrio = pytest.importorskip("pyogrio")
gpd = pytest.importorskip("geopandas")
shapely = pytest.importorskip("shapely")
from shapely.geometry import LineString, MultiLineString, Point, Polygon  # noqa: E402

BBOX = ec.BBOX_32611   # (243350, 4135550, 572550, 4508550)


def inside(x0: float, y0: float, dx: float = 5000.0, dy: float = 0.0, n: int = 20) -> LineString:
    return LineString([(x0 + dx * i / (n - 1), y0 + dy * i / (n - 1)) for i in range(n)])


# --------------------------------------------------------------------------------------------
# vertex thinning
# --------------------------------------------------------------------------------------------
def test_thin_ring_always_keeps_both_endpoints():
    coords = np.array([[0.0, 0.0], [50.0, 0.0], [100.0, 0.0], [150.0, 0.0], [200.0, 0.0]])
    out = ec.thin_ring(coords, step_m=120.0)
    assert np.allclose(out[0], coords[0])
    assert np.allclose(out[-1], coords[-1])
    assert out.shape[0] < coords.shape[0], "a 50 m-spaced line thinned at 120 m must lose vertices"


def test_thin_ring_is_a_noop_for_short_lines_and_zero_step():
    coords = np.array([[0.0, 0.0], [10.0, 0.0]])
    assert np.array_equal(ec.thin_ring(coords, 500.0), coords)
    long = np.array([[float(i * 10), 0.0] for i in range(10)])
    assert np.array_equal(ec.thin_ring(long, 0.0), long)


def test_thin_ring_never_emits_consecutive_duplicates():
    coords = np.array([[0.0, 0.0], [1.0, 0.0], [2.0, 0.0], [2.0, 0.0], [1000.0, 0.0]])
    out = ec.thin_ring(coords, step_m=500.0)
    assert not np.any(np.all(np.isclose(out[1:], out[:-1], atol=1e-9), axis=1))


# --------------------------------------------------------------------------------------------
# geometry walking
# --------------------------------------------------------------------------------------------
def test_iter_parts_handles_every_geometry_type():
    cases = {
        "LineString": LineString([(0, 0), (1, 1)]),
        "MultiLineString": MultiLineString([[(0, 0), (1, 1)], [(2, 2), (3, 3)]]),
        "Polygon": Polygon([(0, 0), (4, 0), (4, 4), (0, 4)]),
        "Point": Point(1, 1),
    }
    expected = {"LineString": 1, "MultiLineString": 2, "Polygon": 1, "Point": 1}
    for name, geom in cases.items():
        parts = list(ec.iter_parts(geom))
        assert len(parts) == expected[name], name
        assert all(p[1].ndim == 2 and p[1].shape[1] == 2 for p in parts)


def test_bbox_rejection_is_correct_at_the_edges():
    left = (BBOX[0] - 100, BBOX[1], BBOX[0] - 10, BBOX[3])
    touching = (BBOX[0] - 100, BBOX[1], BBOX[0], BBOX[3])
    inside_bb = (BBOX[0] + 10, BBOX[1] + 10, BBOX[0] + 20, BBOX[1] + 20)
    assert ec.intersects_bbox(left, BBOX) is False
    assert ec.intersects_bbox(touching, BBOX) is True
    assert ec.intersects_bbox(inside_bb, BBOX) is True
    assert ec.intersects_bbox(None, BBOX) is False


# --------------------------------------------------------------------------------------------
# records + schema from a real GeoDataFrame
# --------------------------------------------------------------------------------------------
def make_frame(tmp_path, crs="EPSG:32611", geographic=False):
    """Line-only frame written to a real shapefile.

    A shapefile layer cannot mix geometry types (pyogrio raises FeatureError on a Point in an ARC
    layer), so point handling is exercised separately on an in-memory GeoDataFrame below.
    """
    if geographic:
        # Real lon/lat inside the Great Basin footprint, produced by transforming the UTM anchors.
        from pyproj import Transformer
        tr = Transformer.from_crs("EPSG:32611", "EPSG:4326", always_xy=True)
        anchors = [(BBOX[0] + 5000, BBOX[1] + 5000, 5000.0),
                   (BBOX[0] - 40000, BBOX[1] + 5000, 5000.0),
                   (BBOX[2] - 2000, BBOX[1] + 9000, 60000.0)]
        geoms = []
        for x0, y0, dx in anchors:
            pts = [tr.transform(x0 + dx * i / 19, y0) for i in range(20)]
            geoms.append(LineString(pts))
    else:
        geoms = [
            inside(BBOX[0] + 5000, BBOX[1] + 5000),                   # fully inside
            inside(BBOX[0] - 40000, BBOX[1] + 5000),                  # fully outside
            inside(BBOX[2] - 2000, BBOX[1] + 9000, dx=60000),         # crosses the east edge
        ]
    df = gpd.GeoDataFrame(
        {"NAME": ["a", "b", "c"], "Ts": [0.5, 0.1, 0.9], "n": [1, 2, 3], "geometry": geoms},
        crs=crs,
    )
    path = tmp_path / "seg.shp"
    df.to_file(path)
    return df, path


def make_point_frame():
    """In-memory frame with a point feature (no file: shapefiles cannot mix geometry types)."""
    return gpd.GeoDataFrame(
        {"NAME": ["p_in", "p_out"], "Ts": [np.nan, 0.3], "n": [4, 5],
         "geometry": [Point(BBOX[0] + 20000, BBOX[1] + 20000),
                      Point(BBOX[0] - 40000, BBOX[1] + 20000)]},
        crs="EPSG:32611",
    )


def test_records_clip_to_the_competition_footprint(tmp_path):
    df, _ = make_frame(tmp_path)
    records, schema = ec.records_from_frame(df)
    names = sorted(r["NAME"] for r in records)
    assert "b" not in names, "the feature entirely outside the bbox must be dropped"
    assert names == ["a", "c"], names
    assert schema["n_features_in_source"] == 3
    assert schema["n_features_in_bbox"] == len(records)


def test_point_features_are_clipped_and_null_attributes_preserved():
    df = make_point_frame()
    records, schema = ec.records_from_frame(df)
    assert [r["NAME"] for r in records] == ["p_in"]
    assert records[0]["Ts"] is None, "a NaN attribute must become null, not a fabricated value"
    assert records[0]["kinds"] == ["Point"]
    assert schema["n_features_in_source"] == 2


def test_attributes_are_copied_verbatim_and_none_invented(tmp_path):
    df, _ = make_frame(tmp_path)
    records, schema = ec.records_from_frame(df)
    by_name = {r["NAME"]: r for r in records}
    assert by_name["a"]["Ts"] == pytest.approx(0.5)
    assert by_name["a"]["n"] == 1
    assert set(schema["attribute_fields"]) == {"NAME", "Ts", "n"}
    for r in records:
        assert set(r) >= {"fid", "kinds", "parts", "length_m", "n_vertices_raw", "n_vertices_kept"}


def test_keep_fields_restricts_the_output(tmp_path):
    df, _ = make_frame(tmp_path)
    records, schema = ec.records_from_frame(df, keep_fields=["Ts"])
    assert set(schema["attribute_fields"]) == {"Ts"}
    assert all("NAME" not in r for r in records)


def test_all_emitted_coordinates_lie_within_the_bbox(tmp_path):
    df, _ = make_frame(tmp_path)
    records, _ = ec.records_from_frame(df, vertex_step_m=0.0)
    for r in records:
        for part in r["parts"]:
            arr = np.asarray(part, float)
            if arr.size == 0:
                continue
            # the crossing feature is clipped by *rejection*, not by cutting, so it may exceed the
            # east edge; every fully-contained feature must be strictly inside
            if r["NAME"] != "c":
                assert arr[:, 0].min() >= BBOX[0] - 1e-6
                assert arr[:, 0].max() <= BBOX[2] + 1e-6
                assert arr[:, 1].min() >= BBOX[1] - 1e-6
                assert arr[:, 1].max() <= BBOX[3] + 1e-6


def test_vertex_retention_is_reported_and_below_one_when_thinning(tmp_path):
    df, _ = make_frame(tmp_path)
    _, loose = ec.records_from_frame(df, vertex_step_m=1000.0)
    _, exact = ec.records_from_frame(df, vertex_step_m=0.0)
    assert loose["vertex_retention"] < 1.0
    assert exact["vertex_retention"] == pytest.approx(1.0)
    assert loose["kept_vertices"] < exact["kept_vertices"]


# --------------------------------------------------------------------------------------------
# the reader path (pyogrio) end to end
# --------------------------------------------------------------------------------------------
def test_clip_and_clip_report_reads_a_real_shapefile(tmp_path):
    _, path = make_frame(tmp_path)
    records, schema = ec.clip_and_clip_report(str(path), vertex_step_m=0.0)
    assert schema["source_feature_count"] == 3
    assert schema["source_geometry_type"] in ("LineString", "Unknown", "Mixed")
    assert schema["source_crs"]
    assert len(records) == schema["n_features_in_bbox"]


def test_reprojection_to_32611_lands_inside_the_footprint(tmp_path):
    """A release shipped in geographic coordinates must still clip correctly after reprojection."""
    df, path = make_frame(tmp_path, crs="EPSG:4326", geographic=True)
    # lon/lat coordinates are ~-118..37, so nothing is in the UTM bbox before reprojection
    records_raw, _ = ec.records_from_frame(df)
    assert records_raw == []
    records, schema = ec.clip_and_clip_report(str(path), vertex_step_m=0.0)
    assert schema["source_crs"]
    assert len(records) > 0, "after reprojection to EPSG:32611 the features must be found"
    for r in records:
        arr = np.asarray([pt for part in r["parts"] for pt in part], float)
        if arr.size and r["NAME"] != "c":
            assert arr[:, 0].min() >= BBOX[0] - 1.0


def test_write_derived_produces_readable_csv_and_json(tmp_path):
    df, _ = make_frame(tmp_path)
    records, schema = ec.records_from_frame(df)
    csv_path = tmp_path / "out.csv"
    json_path = tmp_path / "out.json"
    report = ec.write_derived(records, schema, str(csv_path), str(json_path))
    assert report["n_records"] == len(records)
    payload = json.loads(json_path.read_text())
    assert payload["schema"]["n_features_in_bbox"] == len(records)
    header = csv_path.read_text().splitlines()[0].split(",")
    assert header[:5] == ["fid", "kind", "part_index", "n_vertices", "length_m"]
    assert len(csv_path.read_text().splitlines()) - 1 == report["n_parts"]
