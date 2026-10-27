"""S19B-RADLIN evidence locks: gate passed, uniqueness failed, verdict negative."""
import hashlib
import json
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]


def load(rel):
    return json.loads((ROOT / rel).read_text())


def test_s19_preregistration_frozen_lanes_gates_and_ranking():
    text = (ROOT / "knowledge/57_s19b_radlin_preregistration.md").read_text()
    for needle in ("S19B-RADLIN", "ThK", "320", "H39-2",
                   "0.90", "70", "DO NOT SUBMIT"):
        assert needle in text
    result = (ROOT / "knowledge/58_s19b_radlin_result.md").read_text()
    assert "negative" in result and "DO NOT SUBMIT" in result


def test_s19_run_card_verdict_negative_despite_passed_gate():
    card = load("evidence/s19b_radlin_run_card.json")
    assert card["session"] == "S19B-RADLIN"
    assert card["verdict"] == "negative"
    assert card["submission_ready"] is False
    assert card["slot_selected"] is False
    assert card["holdout"]["gate_passed"] is True
    assert card["registry"]["pass_strict"] is False
    assert card["validator"]["hard_checks_passed"] is True
    assert len(card["note"]) <= 140 and len(card["submission_name"]) > 0
    h = card["holdout"]
    assert h["dti"] > h["baseline_dti"] and h["paired_gain_ci95"][0] > 0
    assert h["withheld_positives"] == 74025 and h["seeds"] == [320, 321, 322, 323, 324]
    fin = card["registry"]["final"]
    assert fin["worst_by_overlap"]["frac_our_dots_within3px"] > 0.70
    assert card["registry"]["scored_focus_max_overlap"] < 0.70


def test_s19_holdout_evidence_matches_run_card():
    ev = load("evidence/s19b_radlin_holdout.json")
    card = load("evidence/s19b_radlin_run_card.json")
    assert ev["gate_passed"] is True
    assert abs(ev["candidate_pooled"]["dti"] - card["holdout"]["dti"]) < 1e-9
    assert len(ev["cells"]) == 20 and len(ev["seeds"]) == 5
    surf = load("evidence/s19b_radlin_surface.json")
    assert surf["passed"] is True
    aucs = [f["auc"] for f in surf["canary"]["features"].values()]
    assert all(0.40 <= v <= 0.90 for v in aucs)
    assert abs(surf["preplacement"]["worst_by_spearman"]["spearman_surface_sample400k"]) <= 0.90


def test_s19_candidate_raster_independent_reopen():
    card = load("evidence/s19b_radlin_run_card.json")
    path = ROOT / "docs" / "downloads" / Path(card["download"]).name
    assert hashlib.sha256(path.read_bytes()).hexdigest() == card["raster_sha256"]
    with rasterio.open(path) as ds:
        assert ds.count == 1 and str(ds.crs) == "EPSG:32611"
        assert (ds.width, ds.height) == (3292, 3730)
        a = ds.read(1)
    assert np.isfinite(a).all() and set(np.unique(a).tolist()) <= {0.0, 1.0}
    assert int((a > 0).sum()) == card["dot_count"] == 37654


def test_s19_site_pages_carry_decision_and_nine_site_table():
    idx = (ROOT / "docs/index.html").read_text()
    s19 = load("evidence/s19b_radlin_run_card.json")
    assert "S23 audit: no new TIFF" in idx
    assert s19["download"].split("/")[-1] not in idx
    page = (ROOT / "docs/session19b-result.html").read_text()
    assert s19["download"].split("/")[-1] in page
    assert "93.4%" in page and "DO NOT SUBMIT" in page
    for site in ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
                 "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"):
        assert site in page
    assert "0.2778" in page and "no file approved" in page
    manifest = load("docs/downloads/manifest.json")
    assert manifest["current_run"]["run_id"] == "G28-S23-20261027"
    assert manifest["s19b_candidate"]["verdict"] == "negative"
    assert any(r["run_id"] == "S19B-RADLIN" for r in manifest["parallel_runs"])
