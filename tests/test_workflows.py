"""Guard rails for the GitHub Actions workflows and the external-layer fetch bridge.

The fetch workflow failed seven times with zero jobs and no logs because one `run: |` block contained
a multi-line shell string whose continuation lines were not indented, which makes the whole workflow
file invalid YAML. GitHub reports that only as "likely failed because of a workflow file issue".
These tests parse every workflow and exercise the fetch script's selection logic so the same class of
breakage cannot land silently again.
"""
import json
from pathlib import Path

import pytest
import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = sorted((ROOT / ".github" / "workflows").glob("*.yml"))


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_workflow_is_valid_yaml_with_jobs(path: Path):
    document = yaml.safe_load(path.read_text(encoding="utf-8"))
    assert isinstance(document, dict), f"{path.name} does not parse to a mapping"
    jobs = document.get("jobs")
    assert isinstance(jobs, dict) and jobs, f"{path.name} declares no jobs"
    for name, job in jobs.items():
        assert isinstance(job, dict), f"{path.name}:{name} is not a mapping"
        assert "runs-on" in job, f"{path.name}:{name} has no runs-on"
        assert job.get("steps"), f"{path.name}:{name} has no steps"


@pytest.mark.parametrize("path", WORKFLOWS, ids=lambda p: p.name)
def test_every_step_run_block_is_indented(path: Path):
    """A `run: |` body must stay indented; a column-1 line silently ends the block scalar."""
    lines = path.read_text(encoding="utf-8").splitlines()
    in_block = False
    key_indent = 0
    for number, line in enumerate(lines, start=1):
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        if in_block:
            if not stripped:
                continue
            if indent <= key_indent:
                in_block = False  # the block scalar ended with the key's sibling
            else:
                assert indent > key_indent, (
                    f"{path.name}:{number} ends a run: | block early - this is what broke "
                    f"fetch-gdr-external-layers.yml and made GitHub report a workflow-file error"
                )
                continue
        if stripped.startswith("run:"):
            in_block = stripped.endswith("|")
            key_indent = indent


def test_fetch_external_layers_selection_and_pins(tmp_path):
    from scripts import fetch_external_layers as bridge

    pins = {
        "gdr_paleo": {"url": "https://gdr.openei.org/files/1391/paleo_geothermal_regional.zip",
                      "bytes": 84008, "sha256": "f" * 64},
        "gdr_2m_probes": {"url": "https://gdr.openei.org/files/1391/2m_temperature_probe.zip",
                          "bytes": 1080530, "sha256": "a" * 64},
        "gdr_volcanics": {"url": "https://gdr.openei.org/files/1391/great_basin_q_volcanics.zip",
                          "bytes": 9898770, "sha256": "b" * 64},
    }
    pin_path = tmp_path / "pins.json"
    pin_path.write_text(json.dumps({"downloads": pins}), encoding="utf-8")
    loaded = bridge.load_pins(pin_path)
    assert set(loaded) == set(pins)
    assert bridge.selected_labels("volcanics,probes", loaded) == ["gdr_2m_probes", "gdr_volcanics"]
    assert bridge.selected_labels("all", loaded) == sorted(pins)
    assert bridge.selected_labels("gdr_paleo", loaded) == ["gdr_paleo"]
    assert bridge.load_pins(tmp_path / "absent.json") == {}


# --------------------------------------------------------------------------------------------
# Session 11: the heat-flow derived clip, the five-slice MT probes, and DEM-tile volume scoping
# --------------------------------------------------------------------------------------------

def test_sciencebase_checks_cover_all_five_mt_conductance_slices():
    """H33-2's column needs all five depth slices probed, not just the two pinned ones.

    Filenames verified live on the official ScienceBase item page 2026-10-03 (facet Raster records).
    """
    from scripts import fetch_external_layers as bridge

    by_label = {c["label"]: c for c in bridge.SCIENCEBASE_CHECKS}
    expected = {
        "sb_mt_conductance_surface": "gb_conductance_surface_tp.tif",
        "sb_mt_conductance_middle_crust": "gb_conductance_middle_crust_tp.tif",
        "sb_mt_conductance_lower_crust": "gb_conductance_lower_crust_tp.tif",
        "sb_mt_conductance_upper_mantle": "gb_conductance_upper_mantle_tp.tif",
        "sb_mt_conductance_mantle": "gb_conductance_mantle_tp.tif",
    }
    for label, filename in expected.items():
        assert label in by_label, f"{label} is not probed; the MT column is incomplete"
        assert by_label[label]["filename"] == filename
        assert by_label[label]["item"] == "62979746d34ec53d276c113b"
        assert by_label[label]["doi"] == "10.5066/P9TWT2LU"


def test_derived_specs_cover_the_heat_flow_release_with_a_distinct_stem():
    """DERIVED=all must clip the pin-verified heat-flow point coverage (H33-3/H35-2)."""
    from scripts import fetch_external_layers as bridge

    by_label = {s["label"]: s for s in bridge.DERIVED_SPECS}
    assert "sb_heat_flow_zip" in by_label
    assert by_label["sb_heat_flow_zip"]["stem"] == "sb_heat_flow_in_footprint"
    stems = [s["stem"] for s in bridge.DERIVED_SPECS]
    assert len(stems) == len(set(stems)), "two specs must never write the same derived files"
    pins = json.loads((ROOT / "registry" / "external_pins.json").read_text())["downloads"]
    assert pins["sb_heat_flow_zip"]["sha256"] == (
        "e7fd62c6963ab390963b3f19adf4dd14bf616e7267f2ae38ad6af1005c106918")
    assert pins["sb_heat_flow_zip"]["bytes"] == 130154244


def _dem_links_file(tmp_path, records):
    path = tmp_path / "dem_links.json"
    path.write_text(json.dumps({"records": records}), encoding="utf-8")
    return path


def test_dem_sizes_mode_never_raises_and_records_unreachable_tiles(tmp_path):
    """The H33-4/H35-3 volume scoping must be total: bad URLs are rows, not crashes."""
    from scripts import fetch_external_layers as bridge

    good = tmp_path / "tile.tif"
    good.write_bytes(b"II*\x00" + b"\x00" * 100)
    links = _dem_links_file(tmp_path, [
        {"tile": "x00y000", "project": "TEST", "url": good.as_uri()},
        {"tile": "x00y001", "project": "TEST", "url": "http://127.0.0.1:9/no_such_tile.tif"},
        {"tile": "x00y002", "project": "TEST", "url": "not a url at all !!!"},
    ])
    out = bridge.run_dem_sizes(links)
    assert out["status"] in {"SIZES_RECORDED", "SIZES_UNAVAILABLE"}
    assert set(out["rows"]) == {"x00y000", "x00y001", "x00y002"}
    assert out["rows"]["x00y001"]["status"] == "UNREACHABLE"
    assert out["rows"]["x00y002"]["status"] == "UNREACHABLE"
    assert out["summary"]["n_tiles"] == 3
    assert isinstance(out["summary"]["total_bytes"], int)
    assert isinstance(out["summary"]["exceeds_20gb_downrank_rule"], bool)


def test_dem_sizes_mode_aggregates_bytes_and_applies_the_20gb_rule(tmp_path, monkeypatch):
    from scripts import fetch_external_layers as bridge

    links = _dem_links_file(tmp_path, [
        {"tile": f"x{i:02d}", "project": "TEST", "url": f"https://example.invalid/{i}.tif"}
        for i in range(3)
    ])
    monkeypatch.setattr(
        bridge, "head_content_length",
        lambda url, timeout=30: {"url": url, "status": "HEAD_OK", "http_status": 200,
                                 "bytes": 10_000_000_000})
    out = bridge.run_dem_sizes(links)
    assert out["status"] == "SIZES_RECORDED"
    assert out["summary"] == {
        "n_tiles": 3, "n_sized": 3, "total_bytes": 30_000_000_000, "total_gb": 30.0,
        "exceeds_20gb_downrank_rule": True,
        "note": ("HEAD only; no tile bytes downloaded. knowledge/18 down-ranks H33-4/H35-3 if "
                 "the in-footprint volume exceeds ~20 GB."),
    }


def test_dem_sizes_mode_reports_a_missing_links_file_without_raising(tmp_path):
    from scripts import fetch_external_layers as bridge

    out = bridge.run_dem_sizes(tmp_path / "absent.json")
    assert out["status"] == "NO_DEM_LINKS"
    assert "error" in out


def test_fetch_workflow_passes_dem_sizes_and_mentions_the_heat_flow_clip():
    wf = (ROOT / ".github" / "workflows" / "fetch-gdr-external-layers.yml").read_text()
    assert "--dem-sizes data/dem_links.json" in wf
    assert "sb_heat_flow_in_footprint" in wf
    assert "10.5066/P9BZPVUC" in wf
