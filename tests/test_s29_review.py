"""Fail-closed presentation tests for the current S29 review."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_s29_card_is_negative_and_published_copy_is_exact() -> None:
    card_bytes = (ROOT / "evidence/s29_run_card.json").read_bytes()
    card = json.loads(card_bytes)
    assert json.loads((ROOT / "docs/data/s29_run_card.json").read_bytes()) == card
    assert card["verdict"] == "negative"
    assert card["new_tiff_generated"] is False
    assert card["submission_ready"] is False
    assert card["ok_to_download_and_submit"] is False
    assert card["slot_selected"] is False
    assert card["raster_sha256"] is None
    assert card["submission_name"] is None
    assert card["score_estimate"] is None


def test_nine_site_review_is_explicitly_historical_and_not_a_download_recommendation() -> None:
    page = (ROOT / "docs/s29-review.html").read_text(encoding="utf-8")
    rows = [
        "GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
        "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36",
    ]
    assert page.count('<tr><th scope="row">GEMSDOE') == len(rows)
    assert all(site in page for site in rows)
    assert "USER-REPORTED / UNVERIFIED" in page
    assert "Estimated leaderboard score:</strong> unavailable" in page
    assert "No approved TIFF to download" in page
    assert 'data-submission-ready="false"' in page
    assert "DO NOT SUBMIT" in page


def test_s29_overlay_precedes_historical_banner_on_entry_pages() -> None:
    for relative in ("index.html", "executive-summary.html", "docs/index.html", "docs/executive-summary.html"):
        page = (ROOT / relative).read_text(encoding="utf-8")
        assert page.index('id="s29-current-decision"') < page.index('id="s28-current-decision"')
        assert "No approved TIFF to download" in page
        assert 'data-submission-ready="false"' in page


def test_s29_builder_panel_keeps_submission_locked() -> None:
    import sys

    sys.path.insert(0, str(ROOT / "scripts"))
    import build_s29_review

    original = json.loads((ROOT / "evidence/s29_run_card.json").read_text(encoding="utf-8"))
    assert "NO FILE APPROVED" in build_s29_review.panel("card.json", "review.html")
    build_s29_review.validate_card(original)
    invalid = dict(original, submission_ready=True)
    try:
        build_s29_review.validate_card(invalid)
    except ValueError:
        pass
    else:
        raise AssertionError("builder accepted an upload-ready card without a selector review")
    assert original["note_character_count"] == len(original["note"])
    assert original["candidate_slate"][0]["id"] == "MCR"
