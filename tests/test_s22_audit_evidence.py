"""Keep the current audit's conclusions bound to the recorded evidence."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_priority_novelty_has_every_direction_and_preserves_score_separation():
    priority = load("evidence/s22_priority_audit.json")
    novelty = load("evidence/s22_focus_novelty.json")
    card = load("evidence/s22_audit_run_card.json")
    sites = {row["site"] for row in novelty["summary"]}
    pairs = novelty["comparisons"]
    assert priority["priority_inventory_retrieved"] is True
    assert priority["external_parallel_registry_complete"] is False
    assert len(sites) == 9 and len(pairs) == 72
    assert {(x["candidate_site"], x["reference_site"]) for x in pairs} == {
        (a, b) for a in sites for b in sites if a != b}
    assert all(x["complete"] and x["duplicate"] and x["candidate_within_3px_fraction"] > 0.70
               and -1 <= x["spearman_exact"] <= 1 for x in pairs)
    assert card["registry_correlations_overlaps"]["duplicate_pairs"] == len(pairs)
    assert card["registry_correlations_overlaps"]["complete_current_parallel_registry"] is False
    for summary in novelty["summary"]:
        repo = next(x for x in priority["repositories"] if x["repository"].endswith("/" + summary["site"]))
        raster = next(x for x in repo["priority_rasters"] if x["file"] == summary["filename"])
        assert raster["blob_verified"] and raster["sha256"] == summary["sha256"]
    assert novelty["forensics"]["champion_reconstruction_symmetric_difference"] == 0
    assert novelty["forensics"]["solo_removed_within_2px"] == 2545
    assert novelty["forensics"]["gem25_equals_gem30_inside_footprint"] is True


def test_current_run_card_is_negative_and_archive_failures_are_bound():
    card = load("evidence/s22_audit_run_card.json")
    audit = load("evidence/s22_download_audit.json")
    # docs/downloads/manifest.json is a live, mutable file (later sessions register new
    # candidates into it); this audit's pinned hash can only ever bind the exact bytes
    # it actually read at the time, which are preserved verbatim in this snapshot — the
    # same pattern already used for evidence/pr39_manifest_snapshot.json.
    manifest = ROOT / "evidence/pr59_s22_manifest_snapshot.json"
    assert audit["manifest_sha256"] == hashlib.sha256(manifest.read_bytes()).hexdigest()
    assert audit["status"] == "FAIL" and audit["check_count"] == 823
    assert set(audit["failures"]) == {"s22_archive_h40_vent_allfinite_outside_zero",
                                      "s22_archive_h41_spring_allfinite_outside_zero"}
    assert card["validator_outputs"]["archive_failures"] == audit["failures"]
    assert card["holdout_dti"]["dti"] is None and card["holdout_dti"]["ci95"] is None
    assert card["new_tiff_generated"] is False and card["raster_sha256"] is None
    assert card["experiments_run"] == 0 and card["slot_selected"] is False
    assert card["submission_ready"] is False and card["verdict"] == "negative"
    assert len(card["submission_note"]) <= 140
    assert load("docs/data/current_run_card_2026-10-26.json") == card


def test_public_leaderboard_observation_is_not_a_receipt():
    source = load("evidence/s22_official_source_review.json")
    leader = next(x for x in source["sources"] if x["id"] == "public_leaderboard")
    assert source["observed_utc"] == "2026-10-26T22:02:42Z"
    assert leader["top_public_score"] == 0.4437
    assert "not a submission-page receipt" in leader["observation"]
    page = (ROOT / "docs/cross-site-review.html").read_text()
    assert "0.4437" in page and "not an organizer receipt" in page
    assert "USER-REPORTED / UNVERIFIED" in page and "0.2778" in page


def test_hypotheses_are_not_implicitly_assigned():
    slate = load("registry/s22_audit_hypotheses.json")
    session = load("registry/s22_audit_session.json")
    assert session["lane"] is None and session["lane_assignment_source"] is None
    assert [h["rank"] for h in slate["hypotheses"]] == [1, 2, 3]
    assert all(h["non_fault_mimic"] and h["source"].startswith("https://")
               for h in slate["hypotheses"])
    assert "parallel registry is absent" in slate["novelty_limit"]


def test_tool_access_irregularity_is_disclosed_without_claiming_compliance():
    irregularities = load("registry/irregularities.json")["items"]
    disclosure = next(x for x in irregularities if x["id"] == "s22-one-off-research-tool-competition-access")
    assert "tool-mediated" in disclosure["issue"] and "not determined" in disclosure["issue"]
    assert "do not repeat" in disclosure["action"]
    sources = (ROOT / "docs/sources.html").read_text()
    assert "Competition-page access irregularity" in sources
    assert "Compliance is undetermined" in sources


def test_concurrent_sign_historical_record_is_reconciled_without_overwriting():
    historical = load("evidence/s22_run_card.json")
    emission = load("evidence/s22_emission.json")
    review = load("evidence/s22_sign_audit.json")
    novelty = load("evidence/s22_sign_final_dot_audit.json")
    assert historical["session"] == "S22-SIGN" and historical["submission_ready"] is False
    assert historical["canary"] == {} and historical["canary_pass"] is True
    assert review["canary"]["review_status"].startswith("FAIL")
    assert historical["holdout"]["withheld_positives"] == 60988
    assert sum(row["n_truth"] for row in emission["holdout"]["details"]) == 36596
    assert review["holdout"]["withheld_positives_summed_over_cells"] == 36596
    assert review["holdout"]["ci95"] is None
    assert novelty["local_reference_files"] == 46 and novelty["priority_reference_files"] == 9
    assert len(novelty["comparisons"]) == 55 and novelty["duplicate_comparisons"] == 0
    assert novelty["maximum_overlap"]["candidate_within_3px_fraction"] < 0.70
    candidate = ROOT / historical["submission_file"]
    assert hashlib.sha256(candidate.read_bytes()).hexdigest() == historical["raster_sha256"]
    assert novelty["candidate_sha256"] == historical["raster_sha256"]
    assert review["submission_ready"] is False and review["final_dots"]["complete_registry"] is False
    assert review["final_dots"]["surface_verified"] is False
    assert load("docs/data/s22_run_card.json") == historical
    assert load("docs/data/current_run_card_2026-10-26.json") == load("evidence/s22_audit_run_card.json")
    assert load("docs/data/current_run_card.json") == load("evidence/s28_validation_run_card.json")
    assert load("docs/data/current_run_card_2026-10-27.json") == load("evidence/s23_run_card.json")
    page = (ROOT / "docs/session22-result.html").read_text()
    assert "DO NOT SUBMIT" in page and "36,596" in page and "60,988" in page
    assert "empty canary object" in page and "95% CI not recorded" in page


def test_archived_sign_runner_is_blocked_and_original_is_snapshotted():
    import subprocess
    import sys

    review = load("evidence/s22_sign_audit.json")
    snapshot = ROOT / review["historical_runner_snapshot"]
    assert hashlib.sha256(snapshot.read_bytes()).hexdigest() == review["historical_runner_sha256"]
    assert review["historical_runner_sha256"] == "36c0df253b80932da41274ad86ed0fa806f77d1633255a1c5ecffe2b111d857f"
    result = subprocess.run([sys.executable, str(ROOT / "scripts/run_s22_candidate.py")],
                            capture_output=True, text=True, check=False)
    assert result.returncode != 0
    assert "BLOCKED" in result.stderr and "No experiment was run" in result.stderr


def test_sign_novelty_failure_replaces_prior_green_report(tmp_path, monkeypatch):
    monkeypatch.syspath_prepend(str(ROOT / "scripts"))
    import audit_s22_sign_novelty

    monkeypatch.setattr(audit_s22_sign_novelty, "ROOT", tmp_path)

    def fail():
        raise ValueError("candidate twin was modified")

    monkeypatch.setattr(audit_s22_sign_novelty, "audit", fail)
    report = tmp_path / "evidence/s22_sign_final_dot_audit.json"
    report.parent.mkdir()
    report.write_text('{"status":"COMPLETE_SCOPED"}')
    assert audit_s22_sign_novelty.main() == 1
    result = json.loads(report.read_text())
    assert result["status"] == "FAIL" and result["submission_ready"] is False
    assert "twin" in result["failure"]
