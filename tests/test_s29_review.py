"""Fail-closed checks for the S29 decision: no TIFF, no approval, consistent evidence."""
import copy
import json
from pathlib import Path

import pytest
from scripts import build_s29_review as s29

ROOT = Path(__file__).resolve().parents[1]


def _json(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def test_run_card_is_fail_closed():
    card = _json("evidence/s29_run_card.json")
    assert card["ok_to_submit"] is False
    assert card["slot_selected"] is False
    assert card["new_tiff_generated"] is False
    assert card["raster_sha256"] is None
    assert card["submission_name"] is None and card["submission_note"] is None
    assert card["verdict"] == "negative"
    assert card["experiments_run"] == 3 and card["experiment_cap"] == 3


def test_panel_refuses_approved_or_slot_selected_card():
    card = _json("evidence/s29_run_card.json")
    for key, bad in (("ok_to_submit", True), ("slot_selected", True), ("new_tiff_generated", True),
                     ("raster_sha256", "a" * 64), ("submission_name", "x")):
        broken = copy.deepcopy(card)
        broken[key] = bad
        with pytest.raises(ValueError):
            s29.panel(broken, "data/s29_run_card.json", "s29-review.html")


def test_panel_states_no_file_approved():
    card = _json("evidence/s29_run_card.json")
    html = s29.panel(card, "data/s29_run_card.json", "s29-review.html")
    assert "NO FILE APPROVED · OK TO SUBMIT: NO" in html
    assert 'data-submission-ready="false"' in html


def test_dispersion_verdict_override_is_recorded():
    card = _json("evidence/s29_dispersion_run_card.json")
    assert card["verdict"] == "negative"
    assert card["verdict_auto_at_run"] == "promote"
    assert card["verdict_superseded_by"] == "evidence/s29_ridge_control_run_card.json"


def test_lattice_audit_matches_probe_and_lane_rule():
    audit = _json("evidence/s29_lattice_overlap_audit.json")
    assert audit["coverage"]["footprint_cells"] == 5167373
    assert audit["coverage"]["uncovered_cells"] == 6649
    assert audit["summary"]["historical_rasters_checked"] == 52
    assert audit["summary"]["lane_duplicate_vs_lattice"] == 52
    for budget in audit["random_placement_null"].values():
        assert budget["exceeds_lane_threshold"] is True


def test_controls_match_run_card_references():
    null = _json("evidence/s29_null_controls.json")
    disp = _json("evidence/s29_dispersion_run_card.json")
    ridge = _json("evidence/s29_ridge_control_run_card.json")
    assert disp["random_k"]["dti"] == null["controls"]["random_k"]["dti"]
    assert ridge["reference_random_k_holdout_dti"] == null["controls"]["random_k"]["dti"]
    assert ridge["reference_lattice_subset_holdout_dti"] == null["controls"]["lattice_subset"]["dti"]
