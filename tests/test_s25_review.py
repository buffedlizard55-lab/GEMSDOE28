import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_s25_review_is_negative_and_reports_no_experiment_or_tiff():
    card = load("evidence/s25_repository_review_run_card.json")
    assert card["schema"] == "gems28-repository-review-v1"
    assert card["branch"] == "arena/965e7dda-gemsdoe28"
    assert card["verdict"] == "negative"
    assert card["experiments_run"] == 0
    assert card["new_tiff_generated"] is False
    assert card["submission_ready"] is False
    assert card["submission"]["ok_to_download"] is False
    assert card["submission"]["ok_to_submit"] is False
    assert card["submission"]["slot_selected"] is False
    assert card["submission"]["slots_spent"] == 0
    assert len(card["submission"]["note"]) == card["submission"]["note_characters"] <= 140
    assert card["raster"]["path"] is None
    assert card["raster"]["sha256"] is None
    assert card["estimated_leaderboard_score"] is None
    assert card["holdout"]["label"] == "HOLDOUT-DTI"
    assert card["holdout"]["status"].startswith("NOT RUN")
    assert card["holdout"]["dti"] is None
    assert card["holdout"]["ci95"] is None
    assert card["holdout"]["withheld_positives"] is None
    assert card["feature_canaries"]["status"].startswith("NOT RUN")
    assert card["validator"]["status"].startswith("NOT RUN")
    assert all(card["validator"][key] is None for key in (
        "no_nan_inside_footprint", "values_within_0_1", "crs_matches_template",
        "shape_matches_template", "transform_matches_template", "single_band",
    ))


def test_s25_preflight_is_exact_fail_closed_evidence():
    card = load("evidence/s25_repository_review_run_card.json")
    preflight = load("evidence/s25_preflight.json")
    assert card["preflight"]["full_observation"] == "evidence/s25_preflight.json"
    assert card["preflight"]["checked_at_utc"] == preflight["checked_at_utc"]
    assert preflight["status"] == "BLOCKED"
    assert preflight["experiment_allowed"] is False
    assert preflight["submission_ready"] is False
    assert preflight["slot_selected"] is False
    assert preflight["time_cap_seconds"] == 7200
    assert any("Wall-clock budget exhausted" in item for item in preflight["failures"])
    assert any("Missing complete shared parallel-run registry" in item for item in preflight["failures"])
    assert len(preflight["shared_template"]["failures"]) == 9
    assert preflight["shared_template"]["passed"] is False


def test_s25_report_and_readme_keep_current_branch_separate_from_history():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    report = (ROOT / "knowledge/69_repository_review_2026-10-28.md").read_text(encoding="utf-8")
    assert readme.startswith("# S29 · 2026-10-29 UTC")
    assert "# S28 · 2026-10-29 UTC" in readme
    assert "NO NEW TIFF · NO FILE APPROVED · OK TO SUBMIT: NO" in readme
    assert "# S27 · 2026-10-28 UTC" in readme
    assert "# S26 · 2026-10-28 UTC — prior checkout review" in readme
    assert "arena/95d8129d-gemsdoe28" in readme
    assert "arena/965e7dda-gemsdoe28" in readme
    assert "knowledge/69_repository_review_2026-10-28.md" in readme
    assert "evidence/s25_repository_review_run_card.json" in readme
    assert "# S24 · 2026-10-27 UTC — historical repository review" in readme
    assert "655 passed, 6 skipped" in report
    assert "six skipped cases depend on absent data and do not count as passes" in report
    assert "USER-REPORTED / UNVERIFIED" in report
    assert "No competition site, leaderboard, account allowance, receipt, external source, or DEM was queried" in report
    for official_url in (
        "https://www.drivendata.org/competitions/306/competition-doe-gems/",
        "https://www.drivendata.org/competitions/306/competition-doe-gems/page/967/",
        "https://github.com/drivendataorg/gems-prize-reference-solution",
        "https://www.usgs.gov/3d-elevation-program",
        "https://epsg.io/32611",
    ):
        assert official_url in report
