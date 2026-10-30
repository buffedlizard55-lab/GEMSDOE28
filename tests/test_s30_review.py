"""Automated fail-closed checks for the active S30 repository review."""
from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

import pytest
from scripts import build_s30_review

ROOT = Path(__file__).resolve().parents[1]


class PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.links: list[str] = []
        self.ids: list[str] = []
        self.row_headers: list[str] = []
        self._in_row_header = False
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if tag == "a" and values.get("href"):
            self.links.append(str(values["href"]))
        if values.get("id"):
            self.ids.append(str(values["id"]))
        if tag == "th" and values.get("scope") == "row":
            self._in_row_header = True

    def handle_endtag(self, tag: str) -> None:
        if tag == "th":
            self._in_row_header = False

    def handle_data(self, data: str) -> None:
        clean = " ".join(data.split())
        if clean:
            self.text.append(clean)
            if self._in_row_header:
                self.row_headers.append(clean)


def _load(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_s30_run_card_is_negative_and_has_required_audit_fields() -> None:
    card = _load("evidence/s30_run_card.json")
    assert card["branch"] == "arena/5a9fd894-gemsdoe28"
    assert card["submission_verdict"] == "negative"
    assert card["experiment_budget"]["experiments_run"] == 0
    assert card["experiment_budget"]["holdouts_run"] == 0
    assert card["experiment_budget"]["raster_emissions"] == 0
    assert card["hypothesis"]["id"] == "S30-MCR"
    assert card["hypothesis"]["named_non_fault_mimic"]
    assert card["holdout"]["label"] == "HOLDOUT-DTI"
    assert card["holdout"]["evaluator_version"]
    assert card["holdout"]["withheld_positives"] is None
    assert card["holdout"]["dti"] is None
    assert card["holdout"]["ci95"] is None
    assert card["holdout"]["alpha"] == 0.2
    assert card["holdout"]["beta"] == 0.8
    assert card["holdout"]["kernel"] == "300 m triangular"
    assert card["registry_uniqueness"]["s30_surface_rank_correlation"] is None
    assert card["registry_uniqueness"]["s30_final_dot_fraction_within_3px"] is None
    assert card["raster"]["new_tiff_generated"] is False
    assert card["raster"]["sha256"] is None
    assert card["raster"]["submission_name"] is None
    assert card["raster"]["validator_output"]["status"].startswith("NOT RUN")
    assert card["approval"]["ok_to_download"] is False
    assert card["approval"]["ok_to_submit"] is False
    assert card["approval"]["weekly_slot_selected"] is False
    assert card["approval"]["weekly_slot_spent"] is False
    assert card["score_claim_hygiene"]["leaderboard_score_estimate"] is None
    assert len(card["verification_passes"]) == 3
    assert all(item["status"].startswith("PASS") for item in card["verification_passes"])
    assert "747 passed" in card["verification_passes"][2]["pytest"]
    assert card["approval"]["submission_note_characters"] == len(card["approval"]["submission_note"])
    assert len(card["approval"]["submission_note"]) <= 140


def test_s30_preflight_and_source_snapshot_are_fail_closed() -> None:
    preflight = _load("evidence/s30_preflight.json")
    source = _load("evidence/s30_source_refresh.json")
    assert preflight["status"] == "BLOCKED"
    assert preflight["experiment_allowed"] is False
    assert preflight["submission_ready"] is False
    assert preflight["slot_selected"] is False
    assert preflight["elapsed_seconds"] > preflight["time_cap_seconds"]
    assert source["freshly_observed_count"] == 10
    assert source["source_count"] == 18
    assert len(source["focus_site_owner_repositories"]) == 9
    assert all(item["status"] == "observed" for item in source["focus_site_owner_repositories"])
    assert source["drivendata_contacted"] is False
    assert source["leaderboard_or_submission_receipts_checked"] is False


def test_s30_hypotheses_include_physics_mimics_cost_and_real_availability() -> None:
    slate = _load("registry/s30_hypotheses.json")
    assert 3 <= len(slate["hypotheses"]) <= 5
    assert [item["rank"] for item in slate["hypotheses"]] == [1, 2, 3]
    for item in slate["hypotheses"]:
        assert item["layers"]
        assert item["physical_signature"]
        assert item["why_it_may_find_catalogue_missing_faults"]
        assert item["difference_from_implemented_repo_work"]
        assert item["named_non_fault_mimic"]
        assert item["implementation_cost"]
        assert item["data_required"]
        assert item["data_obtainability_check"]
        assert item["expected_holdout_dti_improvement"].startswith("Unknown")
    assert slate["hypotheses"][0]["data_obtainability_check"]["required_local_cache_present"] is False
    assert "NOT VIABLE" in slate["hypotheses"][1]["data_obtainability_check"]["current_status"]
    assert "NOT VIABLE" in slate["hypotheses"][2]["data_obtainability_check"]["current_status"]


def test_nine_historical_score_claims_are_unverified_and_not_estimable() -> None:
    scorecard = _load("evidence/s23_scorecard.json")
    overlap = _load("evidence/s24_nine_site_overlap.json")
    expected = {
        "GEMSDOE24": 0.2477,
        "GEMSDOE25": 0.2600,
        "GEMSDOE27": 0.2449,
        "GEMSDOE28": 0.2710,
        "GEMSDOE30": 0.2600,
        "GEMSDOE31": 0.2708,
        "GEMSDOE32": 0.2778,
        "GEMSDOE33": 0.2632,
        "GEMSDOE36": 0.2750,
    }
    assert {site["site"]: site["highest_supplied_score"] for site in scorecard["sites"]} == expected
    assert len(scorecard["sites"]) == 9
    for site in scorecard["sites"]:
        assert "UNVERIFIED" in site["score_evidence_class"]
        assert site["estimated_leaderboard_score"] is None
        assert site["unique_under_requested_rule"] is False
        assert site["ok_to_submit"] is False
    assert overlap["pairs_total"] == 72
    assert overlap["pairs_over_0_70"] == 72
    assert all(value > 0.70 for value in overlap["pairwise_overlap"].values())


def test_gemsdoe32_02778_is_an_owner_claim_and_deletion_only_subset() -> None:
    forensic = _load("evidence/s15_champion_forensic.json")
    card = _load("evidence/s30_run_card.json")
    assert forensic["champion_subset_of_solo"] is True
    assert forensic["champion_equals_solo_minus_dcat_le2_exact"] is True
    assert forensic["symdiff_champion_vs_solo_minus_dcat_le2"] == 0
    assert forensic["removed_solo_to_champion"] == 2545
    assert forensic["added_solo_to_champion"] == 0
    assert card["gemdoe32_0_2778_analysis"]["claim_class"].startswith("OWNER-REPORTED")
    assert card["gemdoe32_0_2778_analysis"]["score_difference_vs_0_2708_claim"] == pytest.approx(0.007)


def test_s30_publisher_rejects_any_upload_unlock_or_raster_claim() -> None:
    card = _load("evidence/s30_run_card.json")
    preflight = _load("evidence/s30_preflight.json")
    source = _load("evidence/s30_source_refresh.json")
    slate = _load("registry/s30_hypotheses.json")
    scorecard = _load("evidence/s23_scorecard.json")
    overlap = _load("evidence/s24_nine_site_overlap.json")
    forensic = _load("evidence/s15_champion_forensic.json")
    build_s30_review.validate_records(card, preflight, source, slate, scorecard, overlap, forensic)
    for invalid in (
        {**card, "submission_verdict": "promote"},
        {**card, "approval": {**card["approval"], "ok_to_submit": True}},
        {**card, "raster": {**card["raster"], "new_tiff_generated": True}},
        {**card, "raster": {**card["raster"], "sha256": "f" * 64}},
        {**card, "holdout": {**card["holdout"], "dti": 0.5}},
    ):
        with pytest.raises(ValueError):
            build_s30_review.validate_records(
                invalid, preflight, source, slate, scorecard, overlap, forensic)


def test_generated_s30_page_is_clear_fail_closed_and_has_no_tif_links() -> None:
    build_s30_review.main()
    page = (ROOT / "docs/s30-review.html").read_text(encoding="utf-8")
    parser = PageParser()
    parser.feed(page)
    body = " ".join(parser.text)
    assert "NO NEW TIFF" in body
    assert "DOWNLOAD: NO FILE EXISTS" in body
    assert "SUBMIT: NO" in body
    assert "NOT ESTIMABLE" in body
    assert "USER-REPORTED / UNVERIFIED" in body
    assert "GEMSDOE32" in body and "0.0070" in body
    assert "72/72" in body
    assert "BLOCKED" in body
    assert "not freshly verified" in body
    assert "S30 current review" in page
    assert "s30-current-decision" in parser.ids
    assert len({site for site in parser.row_headers if site.startswith("GEMSDOE")}) == 9
    assert not any(re.search(r"\.tiff?(?:$|[?#])", link, re.IGNORECASE) for link in parser.links)
    assert (ROOT / "docs/data/s30_run_card.json").read_bytes() == (
        ROOT / "evidence/s30_run_card.json").read_bytes()
    for published in (
        "s30_preflight.json", "s30_source_refresh.json", "s30_hypotheses.json",
        "s30_scorecard.json", "s30_overlap_audit.json", "s30_gemsdoe32_forensic.json",
    ):
        assert (ROOT / "docs/data" / published).is_file()


def test_s30_overlay_is_first_and_supersedes_archived_panels() -> None:
    for relative in (
        "index.html", "executive-summary.html", "current-review.html",
        "docs/index.html", "docs/executive-summary.html", "docs/current-review.html",
        "docs/cross-site-review.html",
    ):
        page = (ROOT / relative).read_text(encoding="utf-8")
        assert page.count('id="s30-current-decision"') == 1
        assert 'data-submission-ready="false"' in page
        old_id = 'id="s29-lattice-decision"'
        if old_id in page:
            assert page.index('id="s30-current-decision"') < page.index(old_id)
        assert "literal 70%/3 px registry rule is binding" in page
    sources = (ROOT / "docs/sources.html").read_text(encoding="utf-8")
    assert 'href="s30-review.html">Current review' in sources


def test_review_workflows_rebuild_and_publish_s30_assets() -> None:
    ci = (ROOT / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    site = (ROOT / ".github/workflows/build-site.yml").read_text(encoding="utf-8")
    pages = (ROOT / ".github/workflows/pages.yml").read_text(encoding="utf-8")
    source = (ROOT / ".github/workflows/source-feed.yml").read_text(encoding="utf-8")
    assert "python scripts/build_active_review.py" in ci
    assert "scripts/build_s30_review.py" in site
    assert "python3 scripts/build_s30_review.py" in pages
    assert "s30-review.html" in pages
    assert "python scripts/build_active_review.py" in source
    assert "docs/data/s30_*.json" in source
