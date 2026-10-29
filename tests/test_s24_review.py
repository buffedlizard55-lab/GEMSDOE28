import hashlib
import json
import subprocess
import sys
from pathlib import Path

from scripts import site_s23

ROOT = Path(__file__).resolve().parents[1]


def load(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def test_s24_run_card_is_a_negative_read_only_disposition():
    card = load("evidence/s24_repository_review_run_card.json")
    assert card["session_id"] == "G28-S24-20261027"
    assert card["branch"] == "arena/79bafcec-gemsdoe28"
    assert card["verdict"] == "negative"
    assert card["new_tiff_generated"] is False
    assert card["new_holdout_run"] is False
    assert card["experiments_run"] == 0
    assert card["slot_selected"] is False
    assert card["submission_ready"] is False
    assert card["ok_to_download_new_submission"] is False
    assert card["ok_to_submit"] is False
    assert card["raster_sha256"] is None
    assert card["submission_name"] is None
    assert len(card["note"]) == card["note_character_count"] <= 140
    assert card["holdout"]["label"] == "HOLDOUT-DTI"
    assert card["holdout"]["status"].startswith("NOT RUN")
    assert card["holdout"]["dti"] is None
    assert card["holdout"]["ci95"] is None
    assert card["holdout"]["withheld_positives"] is None
    assert card["canary_status"].startswith("NOT RUN")
    assert card["validator"]["status"].startswith("NOT RUN ON A NEW TIFF")
    assert card["validator"]["no_nan_inside_footprint"] is None
    assert card["validator"]["values_within_0_1"] is None
    assert card["validator"]["crs_matches_template"] is None
    assert card["validator"]["shape_matches_template"] is None
    assert card["validator"]["transform_matches_template"] is None
    assert card["estimated_leaderboard_score"] is None
    assert (ROOT / card["verification_record"]).is_file()


def test_s24_registry_numbers_are_labelled_and_stop_on_overlap():
    card = load("evidence/s24_repository_review_run_card.json")
    registry = card["registry"]
    comparison = registry["final_dot_comparison"]
    bounds = registry["calibration_lattice_geometry_bound"]
    assert "GEOMETRY-AUDIT" in comparison["label"]
    assert comparison["duplicate_stop"] is True
    assert comparison["candidate_dots_within_3px_fraction"] > comparison["overlap_limit"]
    assert abs(comparison["raw_spearman"]) < comparison["rank_limit"]
    assert abs(comparison["sampled_kernel_spearman"]) < comparison["rank_limit"]
    assert "GEOMETRY-AUDIT" in bounds["label"]
    assert bounds["coverage_fraction"] == 1 - bounds["uncovered_pixels"] / bounds["footprint_pixels"]
    assert bounds["unspaced_minimum_overlap_fraction"] == (
        bounds["candidate_budget"] - bounds["uncovered_pixels"]
    ) / bounds["candidate_budget"]
    assert bounds["minimum_overlap_fraction_with_spacing_2_8px"] > comparison["overlap_limit"]
    assert "not proof that every smaller budget is impossible" in bounds["interpretation"]
    assert registry["preplacement_surface_tested"] is False
    assert registry["complete"] is False


def test_s24_preflight_and_feed_snapshots_are_exactly_hash_bound():
    card = load("evidence/s24_repository_review_run_card.json")
    for relative, expected in card["historical_s23_implementation_snapshots"].items():
        actual = hashlib.sha256((ROOT / relative).read_bytes()).hexdigest()
        assert actual == expected
    preflight_spec = card["preflight"]
    preflight_path = ROOT / preflight_spec["path"]
    assert hashlib.sha256(preflight_path.read_bytes()).hexdigest() == preflight_spec["sha256"]
    preflight = json.loads(preflight_path.read_text())
    assert preflight["status"] == "BLOCKED"
    assert preflight["experiment_allowed"] is False
    assert len(preflight["failures"]) >= 10
    feed = card["source_feed_observation"]
    feed_path = ROOT / feed["snapshot"]
    assert feed_path.is_file()
    snapshot = json.loads(feed_path.read_text())
    assert snapshot["checked_at_utc"] == feed["checked_at_utc"]
    assert snapshot["source_count"] == feed["source_count"]
    assert snapshot["freshly_observed_count"] == feed["freshly_observed_count"]
    assert sum(row["status"] == "fetch-failed" for row in snapshot["sources"]) == feed["failed_count"]
    assert set(feed["failed_ids"]) == {
        row["id"] for row in snapshot["sources"] if row["status"] == "fetch-failed"
    }
    assert feed["snapshot_sha256"] == hashlib.sha256(feed_path.read_bytes()).hexdigest()


def test_readme_read_first_and_s24_page_remain_locked():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    # Current S27 active-branch review leads; S26 and S25 records remain historical.
    assert "# S27 · 2026-10-28 UTC — active branch review" in readme
    assert "# S26 · 2026-10-28 UTC — prior checkout review" in readme
    assert "# S25 · 2026-10-28 UTC — prior PCSE experiment" in readme
    assert "# S25 · 2026-10-28 UTC — repository review" in readme
    assert "# S24 · 2026-10-27 UTC — historical repository review" in readme
    assert "knowledge/70_checkout_validation_followup_2026-10-28.md" in readme
    assert "evidence/review_2026-10-28.json" in readme
    assert "arena/7504de16-gemsdoe28" in readme
    assert "scripts/verify_downloads.py` exited 1 / FAIL CLOSED" in readme
    assert "NO NEW TIFF · NOT OK TO DOWNLOAD OR SUBMIT" in readme
    assert "knowledge/68_s24_repository_review.md" in readme
    assert "evidence/s24_repository_review_run_card.json" in readme

    rendered = site_s23.session24_review(load("evidence/s24_repository_review_run_card.json"))
    assert "No new TIFF." in rendered
    assert "DUPLICATE_STOP" in rendered
    assert "USER-REPORTED / UNVERIFIED" in rendered
    assert "No DrivenData page" in rendered
    assert not any(f'href="{name}' in rendered for name in [
        "downloads/", "../docs/downloads/", "gems28-s22-ctxhgb-"
    ])


def test_static_site_builder_publishes_latest_review_and_run_card():
    proc = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_site.py")],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    result = json.loads(proc.stdout)
    assert result["status"] == "built"
    assert result["external_requests"] == 0
    page = (ROOT / "docs/session24-review.html").read_text(encoding="utf-8")
    assert "Latest review" in page
    assert "NOT READY TO SUBMIT" in page
    assert "JSON run card" in page
    assert 'data-submission-ready="false"' in page
    assert '<button class="button" type="button" disabled' in page
    assert (ROOT / "docs/data/s24_repository_review_run_card.json").read_bytes() == (
        ROOT / "evidence/s24_repository_review_run_card.json"
    ).read_bytes()
    workflow = (ROOT / ".github/workflows/build-site.yml").read_text()
    assert workflow.count("'evidence/s24_repository_review_run_card.json'") == 2
    assert "docs/data/s24_repository_review_run_card.json" in workflow.splitlines()[-1]
    # Keep add-on decision panels current after this test rebuilds the base site.
    overlay = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "build_active_review.py")],
        cwd=ROOT, capture_output=True, text=True, check=False,
    )
    assert overlay.returncode == 0, overlay.stderr


def test_parallel_s24_geometry_card_is_separate_and_does_not_request_rule_override():
    card = load("evidence/s24_run_card.json")
    assert card["schema"] == "run-card-v1"
    assert card["verdict"] == "negative"
    assert card["ok_to_download"] is False and card["ok_to_submit"] is False
    assert "No active choice requested" in card["decision_required"]
    assert "shared, versioned protocol decision" in card["decision_required"]
    assert card["leaderboard_observation"]["label"] == "ORGANIZER-PUBLIC (public page, not a receipt)"
    assert card["raster_sha256"]["new_candidate"] is None
