"""S29 decision regression: the candidate file, its gate, its holdout, and the no-slot decision must agree.

Reads only tracked evidence and docs files (no git-ignored data), so it runs in CI.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "evidence/s29_candidate_run_card.json").read_text(encoding="utf-8"))
GATE_B = json.loads((ROOT / "evidence/s29_gate_B_holeconstrained.json").read_text(encoding="utf-8"))
GATE_A = json.loads((ROOT / "evidence/s29_gate_A_dense.json").read_text(encoding="utf-8"))
E2 = json.loads((ROOT / "evidence/s29_b_holdout.json").read_text(encoding="utf-8"))


def test_no_slot_and_not_ok_to_submit():
    assert CARD["weekly_slot_selected"] is False
    assert CARD["submit_ok"] is False
    assert E2["decision"]["slot_allowed"] is False
    assert E2["B_holdout"]["dti"] < E2["comparable_best_HOLDOUT_DTI"]


def test_candidate_hash_matches_run_card_and_is_present():
    entry = CARD["candidate_files"]["B_unique_gate_pass_NOT_approved"]
    path = ROOT / entry["path"]
    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == entry["sha256"]
    assert CARD["experiments"][1]["raster_sha256"] == entry["sha256"]


def test_gate_results_follow_the_literal_rule():
    assert GATE_B["lane_protocol_passed"] is True
    assert GATE_B["flagged_duplicates"] == []
    assert GATE_B["max_candidate_within_3px_any_convention"] <= 0.70
    assert GATE_B["references_checked"] == 87
    assert all(abs(r["raw_spearman"]) <= 0.90 for r in GATE_B["rows"] if r.get("raw_spearman") is not None)
    assert GATE_A["lane_protocol_passed"] is False
    assert "registry-039" in GATE_A["flagged_duplicates"]


def test_submission_note_is_within_portal_limit():
    note = CARD["experiments"][1]["submission_note"]
    assert len(note) <= 140
    assert CARD["experiments"][1]["submission_note_length"] == len(note)


def test_guide_states_not_approved():
    html = (ROOT / "docs/s29-submission-guide.html").read_text(encoding="utf-8")
    assert "OK TO SUBMIT: NO" in html
    assert "gems29-s29-hole-k20000-20261029-b68117a828cc-nan.tif" in html
