"""S31 session artifacts: gate/build/holdout consistency and fail-closed labels."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str) -> dict:
    return json.loads((ROOT / "evidence" / name).read_text())


def test_gate_sha_matches_candidate_bytes():
    gate = _load("s31_midband_gate.json")
    path = ROOT / gate["path"]
    assert path.is_file(), "candidate file must exist"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == gate["sha256"]


def test_gate_decision_is_fail_closed_and_positive():
    gate = _load("s31_midband_gate.json")
    v = gate["verdict"]
    assert gate["validator_hard_checks_passed"] and gate["no_nan_inside_footprint"]
    assert gate["values_in_01"] and gate["unique_under_70pct_3px"] and gate["lane_ok"]
    assert v["ok_to_download"] is True
    assert "NOT ESTABLISHED" in v["score"]


def test_projection_is_never_a_score():
    gate = _load("s31_midband_gate.json")
    build = _load("s31_build.json")
    # Out-of-range composition must be declared NOT ESTIMABLE in both records.
    assert gate["projection"]["estimable"] is False
    assert build["projection"]["estimable"] is False
    assert "NOT ESTIMABLE" in gate["projection"]["verdict"]
    assert "NOT ESTIMABLE" in build["projection"]["verdict"]


def test_holdout_canary_passed_and_build_rule_recorded():
    hold = _load("s31_holdout.json")
    build = _load("s31_build.json")
    assert all(c["pass_below_0p90"] for c in hold["leakage_canary"].values())
    frozen = build["frozen_rule"]
    assert frozen["selected"] == "mid:fill_mid_random"
    amendment = frozen.get("post_hoc_amendment")
    assert amendment and "no prior arm beat its matched band control" in amendment["reason"]


def test_summary_page_candidate_row_matches_gate():
    gate = _load("s31_midband_gate.json")
    html = (ROOT / "docs" / "s31-midband-executive-summary.html").read_text()
    assert gate["file"] in html
    assert gate["sha256"][:32] in html
    assert "data-submission-ready=\"true\"" in html
    assert "OK to download and submit" in html


def test_run_card_labels_present():
    card = _load("s31_midband_run_card.json")
    assert card["projection"]["label"].startswith("PROJECTION")
    assert card["holdout"]["label"] == "HOLDOUT-DTI"
    assert card["verdict"].startswith("promote")
    assert card["experiments_used"] <= card["experiment_cap"]
