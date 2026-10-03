"""End-to-end test of the runner-bridge derived-clip path in `scripts/fetch_external_layers.py`.

The sandbox cannot reach sciencebase.gov, but `fetch()` is plain `urllib`, so a `file://` pin
exercises the real code path: stream bytes, hash them, compare against the pin, open the archive,
find the vector layer, clip it to the competition footprint, write the derived table. A pin mismatch
and an archive with no vector layer are both checked, because those are the two failure modes that
must be loud rather than silent.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

gpd = pytest.importorskip("geopandas")
from shapely.geometry import LineString  # noqa: E402

_spec = importlib.util.spec_from_file_location(
    "fetch_external_layers", ROOT / "scripts" / "fetch_external_layers.py"
)
fel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(fel)  # type: ignore[union-attr]

BBOX = (243350.0, 4135550.0, 572550.0, 4508550.0)


def make_zip(tmp_path: Path, name: str = "seg", include_vector: bool = True) -> Path:
    """A zip shaped like an official release: one shapefile (or none) plus a readme."""
    payload = tmp_path / f"{name}_payload"
    payload.mkdir()
    if include_vector:
        df = gpd.GeoDataFrame(
            {"NAME": ["in", "out", "cross"],
             "Ts": [0.5, 0.1, float("nan")],
             "geometry": [
                 LineString([(BBOX[0] + 5000 + 250 * i, BBOX[1] + 5000) for i in range(20)]),
                 LineString([(BBOX[0] - 40000 + 250 * i, BBOX[1] + 5000) for i in range(20)]),
                 LineString([(BBOX[2] - 2000 + 3000 * i, BBOX[1] + 9000) for i in range(20)]),
             ]},
            crs="EPSG:32611",
        )
        df.to_file(payload / f"{name}.shp")
    (payload / "readme.txt").write_text("official release readme\n")
    zip_path = tmp_path / f"{name}.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        for f in sorted(payload.iterdir()):
            archive.write(f, arcname=f.name)
    return zip_path


def pins_for(zip_path: Path, label: str = "sb_slip_tendency_shapefile_full",
             sha_override: str | None = None) -> dict:
    return {label: {
        "url": zip_path.as_uri(),
        "bytes": zip_path.stat().st_size,
        "sha256": sha_override or hashlib.sha256(zip_path.read_bytes()).hexdigest(),
        "filename": zip_path.name,
    }}


def run_derived(tmp_path: Path, pins: dict, label: str) -> dict:
    out = tmp_path / "out"
    out.mkdir()
    saved = fel.DERIVED_SPECS
    fel.DERIVED_SPECS = [{"label": label, "hypothesis": "test", "stem": "clip"}]
    try:
        return fel.build_sciencebase_derived(out, pins, None)
    finally:
        fel.DERIVED_SPECS = saved


def test_derived_clip_writes_a_committable_table(tmp_path):
    zip_path = make_zip(tmp_path)
    res = run_derived(tmp_path, pins_for(zip_path), "sb_slip_tendency_shapefile_full")
    row = res["sb_slip_tendency_shapefile_full"]
    assert row["status"] == "DERIVED_WRITTEN", row
    assert row["pin_match"] is True
    commit = tmp_path / "out" / "commit"
    csv_path, json_path = commit / "clip.csv", commit / "clip.json"
    assert csv_path.exists() and json_path.exists()

    payload = json.loads(json_path.read_text())
    names = sorted(r["NAME"] for r in payload["records"])
    assert names == ["cross", "in"], "the feature wholly outside the footprint must be dropped"
    # NaN attribute -> JSON null (a bare NaN token would make the file invalid JSON)
    assert next(r for r in payload["records"] if r["NAME"] == "cross")["Ts"] is None
    # the committed JSON must be strictly valid JSON
    assert "NaN" not in json_path.read_text()

    lines = csv_path.read_text().splitlines()
    assert lines[0].startswith("fid,kind,part_index,n_vertices,length_m")
    assert len(lines) > 1
    assert row["committed_files"] == ["docs/data/clip.csv", "docs/data/clip.json"]


def test_pin_mismatch_is_loud_and_writes_nothing(tmp_path):
    zip_path = make_zip(tmp_path)
    res = run_derived(tmp_path, pins_for(zip_path, sha_override="0" * 64),
                      "sb_slip_tendency_shapefile_full")
    row = res["sb_slip_tendency_shapefile_full"]
    assert row["status"] == "PIN_MISMATCH"
    assert row["pinned_sha256"] == "0" * 64
    commit = tmp_path / "out" / "commit"
    assert not (commit / "clip.csv").exists()
    assert not (commit / "clip.json").exists()


def test_archive_without_a_vector_layer_is_reported(tmp_path):
    zip_path = make_zip(tmp_path, name="novector", include_vector=False)
    res = run_derived(tmp_path, pins_for(zip_path), "sb_slip_tendency_shapefile_full")
    assert res["sb_slip_tendency_shapefile_full"]["status"] == "NO_VECTOR_LAYER"


def test_label_without_a_pin_is_reported_not_guessed(tmp_path):
    res = run_derived(tmp_path, {}, "sb_slip_tendency_shapefile_full")
    assert res["sb_slip_tendency_shapefile_full"]["status"] == "NO_PIN"


def test_only_filter_selects_a_single_spec(tmp_path):
    zip_path = make_zip(tmp_path)
    out = tmp_path / "out"
    out.mkdir()
    saved = fel.DERIVED_SPECS
    fel.DERIVED_SPECS = [
        {"label": "a", "hypothesis": "x", "stem": "a"},
        {"label": "sb_slip_tendency_shapefile_full", "hypothesis": "y", "stem": "clip"},
    ]
    try:
        res = fel.build_sciencebase_derived(out, pins_for(zip_path), "a")
    finally:
        fel.DERIVED_SPECS = saved
    assert set(res) == {"a"}
    assert "sb_slip_tendency_shapefile_full" not in res


def test_zip_extraction_only_pulls_the_siblings_of_a_shapefile(tmp_path):
    zip_path = make_zip(tmp_path)
    work = tmp_path / "work"
    work.mkdir()
    layers = fel._zip_vector_layers(zip_path, work)
    assert len(layers) == 1
    assert layers[0].suffix == ".shp"
    extracted = {p.name for p in work.iterdir()}
    assert "readme.txt" not in extracted, "unrelated archive members must not be extracted"
    assert {"seg.shp", "seg.dbf", "seg.shx"} <= extracted


def test_repository_pin_file_covers_the_h33_1_release():
    """The committed pins must carry the runner-recorded hash, or the bridge has nothing to check."""
    pins_path = ROOT / "registry" / "external_pins.json"
    assert pins_path.exists()
    payload = json.loads(pins_path.read_text())
    row = payload["downloads"]["sb_slip_tendency_shapefile_full"]
    assert row["sha256"] == "5d6213f7763002d369c40b281c31d22113f9c48c482e10ca469e0f6f6b985163"
    assert row["bytes"] == 35912323
    assert row["doi"] == "10.5066/P9YL58W6"
    assert payload["drivendata_access"] is False
