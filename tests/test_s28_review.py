"""Regress the limited-registry novelty claim against the shared lattice audit."""
import copy
import json
from pathlib import Path

import pytest
from scripts.build_s25_page import panel as s25_panel
from scripts.build_s28_review import render

ROOT = Path(__file__).resolve().parents[1]


def test_correction_covers_candidate_and_rejects_old_claim():
    audit = json.loads((ROOT / "evidence/s28_pcse_lattice_audit.json").read_text())
    card = json.loads((ROOT / "evidence/s28_run_card.json").read_text())
    assert audit["inherited_candidate"]["sha256"] == card["historical_s25_sha256"]
    assert audit["inherited_candidate"]["final_dot_comparison"]["max_dot_overlap"] == 1.0
    assert audit["inherited_candidate"]["preplacement_surface_tested"] is False
    text = render(card, audit)
    assert "100.0%" in text and "OK TO SUBMIT: NO" in text
    s25 = s25_panel("downloads/")
    assert "DUPLICATE" in s25 and "omitted that control" in s25
    assert "UNIQUE + FORMAT-VALID" not in s25


def test_panel_fails_closed_if_evidence_is_inconsistent():
    audit = json.loads((ROOT / "evidence/s28_pcse_lattice_audit.json").read_text())
    card = json.loads((ROOT / "evidence/s28_run_card.json").read_text())
    for field, value in (("status", "PASS"), ("status", None)):
        bad = copy.deepcopy(audit)
        bad[field] = value
        with pytest.raises(ValueError):
            render(card, bad)
    bad = copy.deepcopy(card)
    bad["submission_ready"] = True
    with pytest.raises(ValueError):
        render(bad, audit)
    bad = copy.deepcopy(audit)
    bad["inherited_candidate"]["sha256"] = "0" * 64
    with pytest.raises(ValueError):
        render(card, bad)
