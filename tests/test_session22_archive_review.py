import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_json(path):
    return json.loads((ROOT / path).read_text())


def sha256(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_session22_archive_audit_and_blocked_review_card_are_bound():
    audit = read_json("evidence/archive_audit_2026-10-26.json")
    preflight = read_json("evidence/session22_preflight.json")
    card = read_json("evidence/session22_review_run_card.json")

    assert audit["status"] == "PASS"
    assert audit["check_count"] == len(audit["checks"]) == 890
    assert audit["failures"] == []
    assert audit["archive_coverage"]["download_tif_count"] == 46
    assert audit["archive_coverage"]["registered_tif_count"] == 46
    assert audit["archive_coverage"]["unregistered_tif_count"] == 0
    assert audit["scope"].startswith("local format/grid/range/mask/hash audit only")
    assert audit["network_access"] == "none"
    assert audit["manifest_sha256"] == sha256("docs/downloads/manifest.json")

    assert preflight["status"] == "BLOCKED"
    assert preflight["experiment_allowed"] is False
    assert len(preflight["failures"]) == 4
    assert card["session"] == "G28-S22-ARCHIVE-REVIEW-20261026"
    assert card["status"] == "BLOCKED" and card["verdict"] == "blocked"
    assert card["submission_ready"] is False and card["slot_selected"] is False
    assert card["experiments_run"] == 0 and card["experiment_allowed"] is False
    assert card["new_tiff_generated"] is False
    assert card["holdout_dti"] is None and card["score_estimate"] is None
    assert card["archive_audit"]["report_sha256"] == sha256("evidence/archive_audit_2026-10-26.json")
    assert card["preflight"]["sha256"] == sha256("evidence/session22_preflight.json")
    assert card["preflight"]["blockers"] == preflight["failures"]
    assert card["historical_research_artifact"]["portal_submission_approved"] is False
    assert card["drivendata_accessed"] is False


def test_session22_report_ranks_five_distinct_leads_without_claiming_viability():
    report = (ROOT / "knowledge/62_s22_archive_review.md").read_text()
    for hypothesis in ("H43-2", "H43-4", "H33-3", "H33-2", "S21-H2"):
        assert hypothesis in report
    for required in (
        "Non-fault mimic/control",
        "Why it could find unmapped faults",
        "Proposal-only utility and cost",
        "not a fresh current availability check",
        "not currently viable",
        "none approved or currently runnable",
        "0.2778",
        "0.3195",
        "0.4413",
        "RESEARCH ONLY",
        "DO NOT SUBMIT",
        "No manual geological inspection was used as a release gate",
    ):
        assert required in report
    assert "https://www.sciencebase.gov/catalog/item/6297d2fad34ec53d276c5b28" in report
    assert "https://www.sciencebase.gov/catalog/item/62979746d34ec53d276c113b" in report
    assert "https://gdr.openei.org/files/1391/2m_temperature_probe_INGENIOUS_regional_data.zip" in report
    assert "https://www.osti.gov/servlets/purl/1724082" in report


def test_rendered_site_surfaces_audit_and_submission_decision_before_historical_cards():
    index = (ROOT / "docs/index.html").read_text()
    cross_site = (ROOT / "docs/cross-site-review.html").read_text()
    executive = (ROOT / "docs/executive-summary.html").read_text()

    audit_pos = index.index("Archive coverage audit PASS — 46/46 GeoTIFFs registered")
    s21_pos = index.index("SESSION 21 · S21-PUHGB")
    s20_pos = index.index("PARALLEL SESSION 20-NCHC")
    assert audit_pos < s21_pos < s20_pos
    assert "12 of 44 TIFFs" not in index + cross_site + executive
    assert "OK TO SUBMIT TO PORTAL: NO" in index
    assert "RESEARCH ONLY / DO NOT SUBMIT" in index
    assert "Archive audit PASS — 46/46 GeoTIFFs registered and checked" in cross_site
    assert "knowledge/62_s22_archive_review.md" in cross_site
    assert "Do not upload any repository TIFF" in executive
    assert "data/current_run_card_2026-10-26.json" in executive
