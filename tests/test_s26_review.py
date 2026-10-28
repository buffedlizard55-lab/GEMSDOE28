import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_s26_card_is_review_only_and_binds_existing_tif():
    card = load("evidence/s26_run_card.json")
    assert card["branch"] == "arena/95d8129d-gemsdoe28"
    assert card["experiment_this_review"]["status"] == "NO EXPERIMENT RUN"
    assert card["verdict"] == "negative"
    assert card["raster"]["generated_this_review"] is False
    assert card["raster"]["ok_to_submit"] is False
    assert card["raster"]["ok_to_download"] == "YES, for audit/research only"
    assert card["raster"]["note_characters"] == len(card["raster"]["note"]) <= 140
    path = ROOT / card["raster"]["existing_research_artifact"]
    assert path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == card["raster"]["sha256"]
    holdout = card["prior_tested_artifact"]["holdout_dti"]
    assert holdout["label"] == "HOLDOUT-DTI (prior S25 result)"
    assert holdout["withheld_positive_pixels"] == 60988
    assert holdout["ci95"] == [0.03802875957795745, 0.052519021758899796]
    assert card["score_estimate"] is None


def test_s26_preflight_and_exact_download_audit_fail_closed():
    preflight = load("evidence/s26_preflight.json")
    audit = load("evidence/s26_download_audit.json")
    assert preflight["status"] == "BLOCKED"
    assert preflight["experiment_allowed"] is False
    assert preflight["slot_selected"] is False
    assert any("explicit assigned method lane" in failure for failure in preflight["failures"])
    assert audit["status"] == "FAIL"
    assert audit["scope"] == "input validation failed; no TIFF was approved"
    assert "sample_submission.tif" in audit["checks"][0]["detail"]
    assert "labels.tif" in audit["checks"][0]["detail"]


def test_s26_hypothesis_registry_has_four_untried_laned_candidates():
    data = load("registry/s26_hypotheses.json")
    assert data["top_candidate"] == "S26-TCB"
    assert data["top_candidate_holdout_status"].startswith("NOT RUN")
    assert len(data["hypotheses"]) == 4
    for item in data["hypotheses"]:
        assert item["status"].startswith("UNTESTED")
        assert item["physical_signature"]
        assert item["non_fault_mimic"]
        assert item["expected_improvement"].endswith("Not a numeric prediction.")
        assert item["implementation_cost"]
    for item in data["hypotheses"][2:]:
        assert item["official_sources"]
        assert "NOT OBTAINABLE IN THIS RUNTIME" in item["data_obtainability"]


def test_executive_pages_show_existing_tif_is_review_only_and_link_current_review():
    for relative in ("docs/index.html", "docs/executive-summary.html", "index.html", "executive-summary.html"):
        page = (ROOT / relative).read_text(encoding="utf-8")
        assert "Download (review only)" in page
        assert "Fresh exact-file audit (S26 checkout)" in page
        assert "FAIL CLOSED" in page
        assert "OK to submit?</strong></td><td><strong>NO" in page
        assert "knowledge/71_s26_review_2026-10-28.md" in page
        assert "registry/s26_hypotheses.json" in page
