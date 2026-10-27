"""Current S23 authority must not turn archived bytes or a format PASS into approval."""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

import pytest
from scripts import site_s23

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SCORES = {24: .2477, 25: .2600, 27: .2449, 28: .2710, 30: .2600,
          31: .2708, 32: .2778, 33: .2632, 36: .2750}


def load(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def test_current_card_reports_an_uncompleted_tiff_not_a_fabricated_negative_model():
    card = load("evidence/s23_run_card.json")
    assert card["session_id"] == "G28-S23-20261027"
    assert card["verdict"] == "negative" and card["experiments_run"] == 0
    for key in ("submission_ready", "ok_to_submit", "new_tiff_generated", "slot_selected"):
        assert card[key] is False
    assert card["submission_slots_spent"] == 0 and card["weekly_cap"] is None
    assert card["raster_sha256"] is None and card["submission_name"] is None
    assert card["estimated_leaderboard_score"] is None and len(card["note"]) <= 140
    assert card["holdout"]["dti"] is None and card["holdout"]["ci95"] is None
    assert card["holdout"]["withheld_positives"] is None
    assert card["feature_canaries"] == {} and "NOT" in card["canary_status"]
    assert card["validator"]["no_nan_inside"] is None
    assert card["validator"]["inherited_only_format_valid"] is True
    assert card["registry"]["inherited_duplicate"] is True
    assert card["registry"]["complete"] is False
    assert card["registry"]["inherited_final_within_3px_fraction"] > .99
    assert abs(card["registry"]["inherited_final_raw_spearman"]) < .001


@pytest.mark.parametrize("field", ["evidence_sha256", "implementation_sha256", "historical_snapshot_sha256"])
def test_current_evidence_code_and_historical_snapshots_are_byte_bound(field):
    archived_s23_implementations = {
        "scripts/build_site.py": "evidence/snapshots/pre_s24_build_site.py",
        "scripts/site_s23.py": "evidence/snapshots/pre_s24_site_s23.py",
    }
    for relative, expected in load("evidence/s23_run_card.json")[field].items():
        target = (ROOT / relative).resolve()
        assert target.is_relative_to(ROOT)
        assert re.fullmatch(r"[0-9a-f]{64}", expected)
        audited_path = (archived_s23_implementations.get(relative, relative)
                        if field == "implementation_sha256" else relative)
        assert sha(audited_path) == expected, relative
        if audited_path != relative:
            assert sha(relative) != expected, f"{relative} must remain a later implementation"


def test_all_current_aliases_agree_without_rewriting_the_historical_day():
    current = (ROOT / "evidence/s23_run_card.json").read_bytes()
    for relative in ["docs/data/current_run_card.json", "docs/data/current_run_card_2026-10-27.json",
                     "docs/data/s23_run_card.json", "data/current_run_card.json",
                     "data/current_run_card_2026-10-27.json"]:
        assert (ROOT / relative).read_bytes() == current
    assert load("docs/data/current_run_card_2026-10-26.json") == load("evidence/s22_audit_run_card.json")
    assert load("docs/data/run_card_s22c.json") == load("evidence/s22c_run_card.json")
    assert load("evidence/s22c_run_card.json")["verdict"] == "promote"  # Preserved source claim.
    manifest = load("docs/downloads/manifest.json")
    assert manifest["s22c_candidate"]["verdict"] == "negative"  # Current reassessment.
    assert manifest["s22c_candidate"]["source_claim_verdict"] == "promote"
    assert manifest["current_run"]["run_card"] == "evidence/s23_run_card.json"


def test_every_site_claim_is_labelled_and_no_estimate_or_new_file_is_invented():
    rows = load("evidence/s23_scorecard.json")["sites"]
    assert len(rows) == 9
    assert {r["site"] for r in rows} == {f"GEMSDOE{n}" for n in SCORES}
    for row in rows:
        assert row["highest_supplied_score"] == SCORES[int(row["site"][7:])]
        assert row["highest_supplied_score"] == max(row["all_supplied_score_claims"])
        assert "USER-REPORTED / UNVERIFIED" in row["score_evidence_class"]
        assert row["estimated_leaderboard_score"] is None
        assert row["unique_under_requested_rule"] is False and row["ok_to_submit"] is False
        assert row["max_overlap_vs_other_eight"] > .70
        assert "/blob/" + row["commit"] + "/" in row["source"]
        assert re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
    assert sum(r["selected_historical_variants_verified"] for r in rows) == 28


def test_csv_exports_exactly_the_labelled_json_rows_not_fake_score_estimates():
    scorecard = load("evidence/s23_scorecard.json")
    actual = (DOCS / "data/s23_scorecard.csv").read_bytes()
    assert actual == site_s23.score_csv(scorecard).encode()
    records = list(csv.DictReader(io.StringIO(actual.decode())))
    assert len(records) == 9
    for expected, record in zip(scorecard["sites"], records):
        assert record["site"] == expected["site"]
        assert record["historical_reference_file"] == expected["file"]
        assert float(record["highest_supplied_result"]) == expected["highest_supplied_score"]
        assert record["sha256"] == expected["sha256"]
        assert record["estimated_leaderboard_score"] == "UNAVAILABLE"
        assert record["unique_under_requested_rule"] == "NO" and record["ok_to_submit"] == "NO"


def test_geometry_bounds_and_pixel_forensics_are_not_model_performance():
    audit = load("evidence/s23_registry_feasibility.json")
    b = audit["bounds"]
    assert audit["status"] == "DUPLICATE_STOP" and "GEOMETRY-AUDIT" in audit["label"]
    assert b["uncovered_pixels"] == b["footprint_pixels"] - b["covered_pixels"] == 6649
    assert b["unspaced_overlap_lower_bound"] == (37654 - 6649) / 37654
    assert b["spacing"]["uncovered_dot_capacity_upper_bound"] == 3603
    assert b["spacing"]["overlap_lower_bound"] == (37654 - 3603) / 37654
    assert b["required_uncovered_dots_to_pass"] == 11297
    assert b["max_budget_not_ruled_out_by_pixel_count"] == 22163
    assert audit["inherited_candidate"]["preplacement_surface_tested"] is False
    focus = load("evidence/s23_focus_novelty.json")
    assert len(focus["comparisons"]) == 72
    assert all(r["duplicate"] and r["complete"] for r in focus["comparisons"])
    forensic = focus["forensics"]
    assert forensic["champion_reconstruction_symmetric_difference"] == 0
    assert forensic["solo_pixels"] - forensic["solo_removed_within_2px"] == forensic["champion_pixels"]
    assert forensic["gem25_equals_gem30_inside_footprint"] is True
    assert forensic["gem36_champion_dots_missing"] == 0
    assert forensic["gem36_additional_dots"] == 1200


def test_fake_positive_card_cannot_unlock_this_negative_audit_renderer():
    text = site_s23.notice({"verdict": "promote", "submission_ready": True, "slot_selected": True})
    assert 'data-submission-ready="false"' in text
    assert 'disabled aria-disabled="true"' in text and "NO FILE APPROVED" in text
    assert not re.search(r'href="[^"]+\.tif', text)


def test_empty_canary_guard_is_exercised_as_software_not_a_feature_pass():
    software = load("evidence/s23_shared_template_contract.json")
    assert software["passed"] is True and "SOFTWARE CONTRACT" in software["label"]
    for key in ("empty_canary_rejected", "canary_rejects_deliberate_leak", "canary_rejects_inverted_leak"):
        assert software["checks"][key] is True
    assert software["experiments_run"] == 0 and software["new_raster_generated"] is False


def test_unobtainable_dem_is_not_ranked_as_a_viable_experiment():
    slate = load("registry/s23_hypotheses.json")
    assert [h["rank"] for h in slate["hypotheses"]] == [1, 2, 3, 4]
    assert slate["geological_experiments_run"] == 0
    for hypothesis in slate["hypotheses"]:
        assert hypothesis["expected_dti_improvement"] is None
        assert hypothesis["physical_signature"] and hypothesis["non_fault_mimic"]
    assert slate["hypotheses"][-1]["viable_data_only"] is False
    assert "NOT VIABLE" in slate["hypotheses"][-1]["status"]


def test_partial_feed_never_refreshes_an_unattempted_official_source():
    feed = load("evidence/snapshots/s23_source_feed.json")
    assert feed["freshly_observed_count"] == 10 and feed["source_count"] == 18
    assert feed["status"] == "partial-or-unavailable"
    observed = [s for s in feed["sources"] if s["status"] == "observed"]
    assert len(observed) == 10
    for source in feed["sources"]:
        if not source["request_attempted"]:
            assert source["status"] != "observed"
            if "last_successful_observation" in source:
                assert source["last_successful_observation"]["checked_at_utc"] != feed["checked_at_utc"]


def test_old_finalizer_cannot_restore_promotion_or_overwrite_historical_evidence():
    paths = ["docs/downloads/manifest.json", "evidence/s22c_run_card.json", "evidence/s23_run_card.json"]
    before = {p: sha(p) for p in paths}
    result = subprocess.run([sys.executable, "-S", str(ROOT / "scripts/finalize_s22c.py")],
                            capture_output=True, text=True, check=False)
    assert result.returncode == 1, result.stderr
    assert json.loads(result.stdout)["status"] == "BLOCKED_HISTORICAL_DUPLICATE"
    assert before == {p: sha(p) for p in paths}
    review = load("evidence/s23_s22c_reassessment.json")
    assert sha(review["historical_finalizer_snapshot"]) == review["historical_finalizer_sha256"]
    assert sha(review["source_claim"]) == review["source_claim_sha256"]


class PageLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids, self.refs = [], []

    def handle_starttag(self, tag, attrs):
        row = dict(attrs)
        if "id" in row:
            self.ids.append(row["id"])
        for name in ("href", "src"):
            if row.get(name):
                self.refs.append(row[name])


@pytest.mark.parametrize("page", sorted(p.name for p in DOCS.glob("*.html")))
def test_all_pages_lead_with_one_current_lock_and_have_working_local_links(page):
    path = DOCS / page
    text = path.read_text()
    parser = PageLinks()
    parser.feed(text)
    assert parser.ids.count("current-submission") == 1
    assert len(parser.ids) == len(set(parser.ids)), page
    assert text.index('id="current-submission"') < text.index("Submission download locked")
    assert "S23 audit: no new TIFF" in text
    for ref in parser.refs:
        url = urlsplit(ref)
        if url.scheme or url.netloc:
            prefix = "https://github.com/buffedlizard55-lab/GEMSDOE28/blob/main/"
            if ref.startswith(prefix):
                assert (ROOT / unquote(urlsplit(ref[len(prefix):]).path)).is_file(), (page, ref)
            continue
        target = (path.parent / unquote(url.path)).resolve() if url.path else path
        assert target.is_file(), (page, ref)
        if url.fragment and target.suffix == ".html":
            target_parser = PageLinks()
            target_parser.feed(target.read_text())
            assert unquote(url.fragment) in target_parser.ids, (page, ref)
