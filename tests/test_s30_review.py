from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import build_s30_review as s30  # noqa: E402


def records() -> tuple[dict, dict]:
    return s30.load_json(s30.CARD), s30.load_json(s30.SCORECARD)


def test_s30_records_are_strict_json_and_fail_closed() -> None:
    card, scorecard = records()
    s30.validate_records(card, scorecard)
    assert card["verdict"] == "negative"
    assert card["new_tiff_generated"] is False
    assert card["ok_to_download_and_submit"] is False
    assert card["slot_selected"] is False
    assert card["submission_name"] is None
    assert card["submission_note_character_count"] <= 140
    assert card["holdout"]["label"] == "HOLDOUT-DTI"
    assert card["holdout"]["status"].startswith("NOT RUN")
    assert card["holdout"]["dti"] is None
    assert card["holdout"]["ci95"] is None


def test_scorecard_has_all_nine_sites_but_no_estimates_or_downloads() -> None:
    _, scorecard = records()
    assert [row["site"] for row in scorecard["rows"]] == s30.EXPECTED_SITES
    assert scorecard["pairwise_comparisons"] == 72
    assert scorecard["complete_global_registry"] is False
    assert scorecard["all_nine_historical_files_flagged_duplicate_under_70_percent_3px_rule"] is True
    assert all(row["score_estimate"] is None for row in scorecard["rows"])
    assert all(row["current_file_to_download"] is None for row in scorecard["rows"])
    assert all(row["duplicate_under_requested_rule"] is True for row in scorecard["rows"])


def test_panel_visibly_locks_download_and_contains_no_tiff_link() -> None:
    card, _ = records()
    panel = s30.render_panel("data/s30_run_card.json", "data/s30_scorecard.json", "s30-review.html", card)
    assert 'data-submission-ready="false"' in panel
    assert "OK TO DOWNLOAD AND SUBMIT: NO" in panel
    assert "disabled" in panel
    assert "No approved TIFF to download" in panel
    assert not any(token in panel.lower() for token in ("href=\"download.tif", ".tif\"", ".tiff\""))


def test_standalone_review_has_nine_rows_four_hypotheses_and_procedure() -> None:
    card, scorecard = records()
    page = s30.render_page(card, scorecard)
    assert page.count("USER-REPORTED / UNVERIFIED") >= 9
    assert page.count("<article class=\"card\">") == 4
    assert "HOLDOUT-DTI improvement" in page
    assert "New submission form" in page
    assert "no human geological inspector" in page.lower()
    assert "NO FILE APPROVED" in page
    assert "Predicted values must be in range" not in page  # explained, not diagnosed as a current portal cause


def test_publisher_rejects_any_approval_or_claimed_holdout() -> None:
    card, scorecard = records()
    bad = json.loads(json.dumps(card))
    bad["submission_ready"] = True
    with pytest.raises(ValueError, match="negative, no-file, no-slot"):
        s30.validate_records(bad, scorecard)

    bad = json.loads(json.dumps(card))
    bad["holdout"]["dti"] = 0.3
    with pytest.raises(ValueError, match="NOT RUN"):
        s30.validate_records(bad, scorecard)


def test_panel_injection_is_idempotent(tmp_path: Path) -> None:
    card, _ = records()
    page = tmp_path / "entry.html"
    page.write_text("<!doctype html><html><body><main><section>old</section></main></body></html>")
    panel = s30.render_panel("run.json", "scorecard.json", "review.html", card)
    s30.inject(page, panel, "run.json", "scorecard.json")
    first = page.read_text()
    s30.inject(page, panel, "run.json", "scorecard.json")
    second = page.read_text()
    assert first == second
    assert second.count('id="s30-current-decision"') == 1
    assert second.index('id="s30-current-decision"') < second.index("old")
