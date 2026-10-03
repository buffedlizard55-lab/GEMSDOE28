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
from shapely.geometry import LineString, Point  # noqa: E402

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


# --------------------------------------------------------------------------------------------
# the .bin-extension defect the 2026-10-03T18:49:01Z runner run hit
# --------------------------------------------------------------------------------------------
def test_payload_without_a_zip_suffix_is_still_recognised_as_a_zip(tmp_path):
    """ScienceBase URLs carry no file suffix, so fetch() names the payload .bin.

    The 2026-10-03T18:49:01Z runner run downloaded the right bytes (pin matched) but GDAL refused to
    open them, producing a committed clip with 0 records. The format must be decided by magic bytes.
    """
    zip_path = make_zip(tmp_path)
    bin_path = tmp_path / "payload.bin"
    bin_path.write_bytes(zip_path.read_bytes())
    usable, fmt = fel.resolve_payload_format(bin_path, "Shapefile_Full Study.zip")
    assert fmt == "zip"
    assert usable.suffix == ".zip"
    assert usable.exists()
    # the original is untouched, so the verified hash still refers to a real file
    assert bin_path.exists()
    assert hashlib.sha256(bin_path.read_bytes()).hexdigest() == hashlib.sha256(
        zip_path.read_bytes()).hexdigest()


def test_magic_bytes_win_over_a_misleading_pin_filename(tmp_path):
    zip_path = make_zip(tmp_path)
    odd = tmp_path / "payload.dat"
    odd.write_bytes(zip_path.read_bytes())
    usable, fmt = fel.resolve_payload_format(odd, "not_an_archive.tif")
    assert fmt == "zip"
    assert usable.suffix == ".zip"


def test_non_archive_payload_keeps_its_pin_suffix(tmp_path):
    tif = tmp_path / "layer.bin"
    tif.write_bytes(b"II*\x00" + b"\x00" * 60)
    usable, fmt = fel.resolve_payload_format(tif, "gb_conductance_surface_tp.tif")
    assert fmt == "tif"
    assert usable.suffix == ".tif"


def test_derived_run_on_a_dot_bin_payload_produces_records(tmp_path):
    """End-to-end regression: a .bin-named zip must still yield a non-empty clip."""
    zip_path = make_zip(tmp_path)
    payload = tmp_path / "sb_slip_tendency_shapefile_full.bin"
    payload.write_bytes(zip_path.read_bytes())
    out = tmp_path / "out"
    out.mkdir()
    pins = {"sb_slip_tendency_shapefile_full": {
        "url": payload.as_uri(),
        "bytes": payload.stat().st_size,
        "sha256": hashlib.sha256(payload.read_bytes()).hexdigest(),
        "filename": "Shapefile_Full Study.zip",
    }}
    saved = fel.DERIVED_SPECS
    fel.DERIVED_SPECS = [{"label": "sb_slip_tendency_shapefile_full",
                          "hypothesis": "H33-1", "stem": "clip"}]
    try:
        res = fel.build_sciencebase_derived(out, pins, None)
    finally:
        fel.DERIVED_SPECS = saved
    row = res["sb_slip_tendency_shapefile_full"]
    assert row["status"] == "DERIVED_WRITTEN", row
    assert row["payload_format"] == "zip"
    assert row["derived"]["n_records"] > 0, "the .bin regression must not produce an empty clip"
    assert (out / "commit" / "clip.json").exists()


def test_heat_flow_shaped_zip_clips_points_and_ignores_rasters(tmp_path):
    """The heat-flow release (Session 11) is a point shapefile plus grids and docs.

    Zip contents are known before the runner ever sees them from the official FGDC metadata
    (USGS_gbHeatFlowWells_wEstimates.shp + three USGS_gbHeatFlowMap_*.tif grids): the bridge must
    extract and clip the point layer and leave the rasters inside the archive.
    """
    payload = tmp_path / "heat_payload"
    payload.mkdir()
    df = gpd.GeoDataFrame(
        {"unique_id": ["in", "out"],
         "hf_meas": [120.5, 45.0],
         "hf_resid": [35.25, -12.0],
         "geometry": [Point(BBOX[0] + 5000, BBOX[1] + 5000),
                      Point(BBOX[0] - 40000, BBOX[1] + 5000)]},
        crs="EPSG:32611",
    )
    df.to_file(payload / "USGS_gbHeatFlowWells_wEstimates.shp")
    (payload / "USGS_gbHeatFlowMap_equalWts.tif").write_bytes(b"II*\x00" + b"\x00" * 64)
    (payload / "readme.txt").write_text("official release readme\n")
    zip_path = tmp_path / "heat.zip"
    with zipfile.ZipFile(zip_path, "w") as archive:
        for f in sorted(payload.iterdir()):
            archive.write(f, arcname=f.name)

    work = tmp_path / "work"
    work.mkdir()
    layers = fel._zip_vector_layers(zip_path, work)
    assert [p.name for p in layers] == ["USGS_gbHeatFlowWells_wEstimates.shp"]
    assert "USGS_gbHeatFlowMap_equalWts.tif" not in {p.name for p in work.iterdir()}

    res = run_derived(tmp_path, pins_for(zip_path, label="sb_heat_flow_zip"), "sb_heat_flow_zip")
    row = res["sb_heat_flow_zip"]
    assert row["status"] == "DERIVED_WRITTEN", row
    payload_json = json.loads((tmp_path / "out" / "commit" / "clip.json").read_text())
    assert [r["unique_id"] for r in payload_json["records"]] == ["in"]
    assert payload_json["records"][0]["hf_resid"] == 35.25
    fields = payload_json["schema"]["layers"]["USGS_gbHeatFlowWells_wEstimates.shp"][
        "attribute_fields"]
    assert {"hf_meas", "hf_resid"} <= set(fields)


def test_unreadable_layer_is_not_reported_as_written(tmp_path):
    """A payload GDAL cannot open must surface as LAYER_UNREADABLE, never DERIVED_WRITTEN."""
    junk = tmp_path / "release.zip"
    junk.write_bytes(b"PK\x03\x04" + b"\x00" * 200)     # zip magic, truncated archive
    res = run_derived(tmp_path, pins_for(junk), "sb_slip_tendency_shapefile_full")
    row = res["sb_slip_tendency_shapefile_full"]
    assert row["status"] in {"LAYER_UNREADABLE", "ARCHIVE_UNREADABLE", "NO_VECTOR_LAYER"}, row
    assert row["status"] != "DERIVED_WRITTEN"


# --------------------------------------------------------------------------------------------
# the runner must install what the clip path imports
# --------------------------------------------------------------------------------------------
def test_runner_installs_geopandas_for_read_dataframe():
    """The 2026-10-03T18:54:08Z run failed with 'geopandas is required to use
    pyogrio.read_dataframe()'. Guard the dependency so it cannot silently regress."""
    wf = (ROOT / ".github" / "workflows" / "fetch-gdr-external-layers.yml").read_text()
    install_line = next(line for line in wf.splitlines() if "pip install pyogrio" in line)
    for mod in ("pyogrio", "shapely", "pyproj", "pandas", "geopandas"):
        assert mod in install_line, f"{mod} missing from the runner install line"
    assert "Assert the readers this job depends on actually import" in wf


def test_workflow_fails_the_job_on_every_unusable_clip_status():
    wf = (ROOT / ".github" / "workflows" / "fetch-gdr-external-layers.yml").read_text()
    for status in ("PIN_MISMATCH", "LAYER_UNREADABLE", "DERIVED_EMPTY",
                   "NO_VECTOR_LAYER", "ARCHIVE_UNREADABLE"):
        assert status in wf, f"the job must fail loudly on {status}"
