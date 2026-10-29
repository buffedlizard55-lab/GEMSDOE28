"""The latest report must not inherit stale checkout authorization or mutate dated cards."""
import copy
import hashlib
import json
from pathlib import Path

import pytest
from scripts import build_current_review

ROOT = Path(__file__).resolve().parents[1]


def inputs():
    return [json.loads((ROOT / path).read_text()) for path in
            ("evidence/s28_validation_run_card.json", "evidence/s23_scorecard.json", "registry/s26_hypotheses.json")]


def test_latest_card_is_negative_and_binds_fresh_evidence():
    card, _, _ = inputs()
    assert card["branch"] == "arena/ff60f579-gemsdoe28"
    assert card["new_tiff_generated"] is False
    assert card["experiments_run"] == card["submission_slots_spent"] == 0
    assert card["holdout"]["dti"] is None
    assert card["validator"]["no_nan_inside_footprint"] is None
    assert card["estimated_leaderboard_score"] is None
    assert 0 < len(card["submission_note"]) <= 140
    assert card["restoration"]["cache_missingness_passed"] is True
    assert card["restoration"]["shared_assets_passed"] is True
    assert len(card["preflight"]["failures"]) == 5
    for relative, digest in card["evidence_sha256"].items():
        assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative
    for relative in ("docs/data/current_run_card.json", "data/current_run_card.json"):
        assert (ROOT / relative).read_bytes() == (ROOT / "evidence/s28_validation_run_card.json").read_bytes()


@pytest.mark.parametrize("field,value", [("ok_to_submit", True), ("slot_selected", True),
                                         ("new_tiff_generated", True), ("submission_ready", True),
                                         ("raster_sha256", "0" * 64), ("verdict", "promote")])
def test_review_renderer_cannot_unlock_a_submission(field, value):
    card, scores, hypotheses = inputs()
    card[field] = value
    with pytest.raises(ValueError, match="negative"):
        build_current_review.render(card, scores, hypotheses)


def test_renderer_escapes_untrusted_text_and_is_idempotent():
    card, scores, hypotheses = copy.deepcopy(inputs())
    card["branch"] = '<script>alert("x")</script>'
    section = build_current_review.render(card, scores, hypotheses)
    assert "<script>" not in section and "&lt;script&gt;" in section
    assert section.count('<th scope="row">GEMSDOE') == 9
    assert section.count("USER-REPORTED / UNVERIFIED") == 9
    assert "0.2778" in section and "Estimated leaderboard score" in section
    page = "<html><main>old report</main></html>"
    first = build_current_review.inject(page, section)
    assert build_current_review.inject(first, section) == first


def test_current_overlay_preserves_dated_history_and_build_is_offline(capsys):
    historical = [ROOT / p for p in ("docs/data/current_run_card_2026-10-27.json",
                                     "data/current_run_card_2026-10-27.json",
                                     "docs/data/current_run_card_2026-10-26.json")]
    before = [path.read_bytes() for path in historical]
    assert build_current_review.main() == 0
    assert [path.read_bytes() for path in historical] == before
    first = (ROOT / "docs/current-review.html").read_bytes()
    assert build_current_review.main() == 0
    assert (ROOT / "docs/current-review.html").read_bytes() == first
    metadata = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert all(row["network_requests"] == 0 and row["submission_ready"] is False for row in metadata)


def test_pages_verifies_distinct_current_and_historical_digests():
    workflow = (ROOT / ".github/workflows/pages.yml").read_text()
    assert "EXPECTED_HISTORICAL_CARD_SHA256" in workflow
    assert "expected_hash" in workflow
    assert "if path.endswith('current_run_card_2026-10-27.json')" in workflow
    assert "sha256sum docs/data/current_run_card.json" in workflow
    assert "sha256sum docs/data/current_run_card_2026-10-27.json" in workflow


@pytest.mark.parametrize("defect", ["cache", "shared", "experiment", "holdout", "estimate", "unique", "duplicate_row"])
def test_renderer_rejects_evidence_that_contradicts_its_narrative(defect):
    card, scores, hypotheses = inputs()
    if defect == "cache":
        card["restoration"]["cache_missingness_passed"] = False
    elif defect == "shared":
        card["restoration"]["shared_assets_passed"] = False
    elif defect == "experiment":
        card["experiments_run"] = 1
    elif defect == "holdout":
        card["holdout"]["dti"] = 0.5
    elif defect == "estimate":
        scores["sites"][0]["estimated_leaderboard_score"] = 0.5
    elif defect == "unique":
        scores["sites"][0]["unique_under_requested_rule"] = True
    else:
        scores["sites"][0] = scores["sites"][1]
    with pytest.raises(ValueError):
        build_current_review.render(card, scores, hypotheses)
