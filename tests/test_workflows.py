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
