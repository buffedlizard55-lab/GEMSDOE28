#!/usr/bin/env python3
"""Assemble the negative S23 audit, never a candidate or a submission selector.

All source observations are already local. No model is fitted, no raster is
written and no leaderboard projection is inferred from a catalogue holdout.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

try:
    from scripts import site_s23
except ModuleNotFoundError:
    import site_s23

ROOT = Path(__file__).resolve().parents[1]

# These are precisely the owner's supplied result claims for the nine sites.
# They are NOT authenticated by a GitHub filename, matching bytes or local DTI.
SCORES = {
    "GEMSDOE24": [0.2477, 0.0859],
    "GEMSDOE25": [0.2600, 0.0742],
    "GEMSDOE27": [0.2449, 0.2190, 0.2250],
    "GEMSDOE28": [0.2708, 0.2649, 0.2710, 0.2707, 0.0217, 0.0206],
    "GEMSDOE30": [0.2600, 0.1462],
    "GEMSDOE31": [0.2708],
    "GEMSDOE32": [0.2778],
    "GEMSDOE33": [0.2632, 0.0963],
    "GEMSDOE36": [0.2750, 0.1647],
}
EXPLANATIONS = {
    "GEMSDOE24": "Dense d1.5 thinning of the H19-5 ridge family; not an independent detector.",
    "GEMSDOE25": "D2.8 thinning; exact footprint-dot equality to GEMSDOE30's historical best.",
    "GEMSDOE27": "D1.5 family plus gap-closure dots; the supplied result does not show an improvement over its parent.",
    "GEMSDOE28": "Rung30 variant is highest among the supplied GEMSDOE28 claims, but remains in the H19-5 family.",
    "GEMSDOE30": "Exact footprint-dot equality to GEMSDOE25's historical best despite different packaging/naming.",
    "GEMSDOE31": "Solo parent: GEMSDOE32 is exactly this dot set with catalogue-distance <=2 px dots removed.",
    "GEMSDOE32": "Highest supplied historical claim; exact reconstruction is solo minus 2,545 catalogue-adjacent dots, not a new detector.",
    "GEMSDOE33": "Analog-tip/stepover variant; geometric overlap crosses the literal duplicate threshold.",
    "GEMSDOE36": "Contains every champion dot plus 1,200 extras; its name alone is not evidence of an independent PINN.",
}


def load(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def save(path, value):
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(value, indent=2, allow_nan=False) + "\n")


def main():
    geometry = load("evidence/s23_registry_feasibility.json")
    inventory = load("evidence/s23_priority_audit.json")
    focus = load("evidence/s23_focus_novelty.json")
    preflight = load("evidence/s23_preflight.json")
    if (geometry["status"] != "DUPLICATE_STOP" or preflight["experiment_allowed"]
            or not inventory["priority_inventory_retrieved"]
            or len(focus["summary"]) != 9 or len(focus["comparisons"]) != 72):
        raise ValueError("Unexpected evidence state; do not silently turn the stopped audit into promotion")
    for path, expected in geometry["code_sha256"].items():
        if sha(path) != expected:
            raise ValueError("Stale geometry code pin: " + path)
    if load("evidence/s23_download_audit.json")["manifest_sha256"] != sha("docs/downloads/manifest.json"):
        raise ValueError("Stale download audit: rerun it against the current manifest")
    if load("registry/current_session.json")["registry_geometry_audit"]["sha256"] != sha("evidence/s23_registry_feasibility.json"):
        raise ValueError("Session configuration does not bind this geometry audit")
    rows = []
    for item in focus["summary"]:
        site = item["site"]
        source_repo = next(r for r in inventory["repositories"] if r["repository"].endswith("/" + site))
        rows.append({
            "site": site,
            "highest_supplied_score": max(SCORES[site]),
            "all_supplied_score_claims": SCORES[site],
            "score_evidence_class": "USER-REPORTED / UNVERIFIED; no organizer receipt",
            "estimated_leaderboard_score": None,
            "estimate_status": "Not estimable reliably from available evidence; no validated hidden-score calibration.",
            "file": item["filename"], "source": item["source"], "commit": item["commit"],
            "sha256": item["sha256"], "dots": item["positive_pixels"],
            "max_overlap_vs_other_eight": item["max_overlap"]["candidate_within_3px_fraction"],
            "max_overlap_reference": item["max_overlap"]["reference_site"],
            "unique_under_requested_rule": not item["duplicate_vs_other_eight"],
            "format_checks_passed": item["hard_checks_passed"], "format_failures": item["hard_failures"],
            "published_raster_paths_in_repo": len(source_repo["all_raster_paths"]),
            "selected_historical_variants_verified": len(source_repo["priority_rasters"]),
            "interpretation": EXPLANATIONS[site],
            "download_status": "Historical reference bytes only; not a new submission recommendation",
            "ok_to_submit": False,
        })
    scorecard = {
        "observed_utc": inventory["observed_utc"],
        "scope": "Nine highest historical result claims supplied by the owner, pinned to the observed repo commits. Not an organizer-reconciled live ranking or complete parallel registry.",
        "sites": rows,
        "best_supplied_site": max(rows, key=lambda r: r["highest_supplied_score"])["site"],
        "forensics": focus["forensics"],
        "geological_experiments_run": 0,
        "organizer_confirmed_scores": [],
        "recommendation": "No file is approved to submit. Do not copy or rename a historical raster as a new entry.",
    }
    save("evidence/s23_scorecard.json", scorecard)
    inherited = geometry["inherited_candidate"]
    compare = inherited["final_dot_comparison"]["rows"][0]
    evidence_paths = [
        "evidence/s23_priority_audit.json", "evidence/s23_focus_novelty.json",
        "evidence/s23_registry_feasibility.json", "evidence/s23_scorecard.json",
        "evidence/s23_official_source_review.json", "evidence/s23_preflight.json",
        "evidence/s23_shared_template_contract.json", "registry/protocol_assets.json",
        "registry/current_session.json", "registry/s23_hypotheses.json",
        "knowledge/66_s23_preregistration.md", "evidence/data_preparation.json",
        "evidence/s23_download_audit.json", "evidence/s23_s22c_reassessment.json",
        "docs/downloads/manifest.json", "evidence/snapshots/s23_source_feed.json", "registry/irregularities.json",
        "evidence/s23_optional_restore.json", "registry/data_manifest.json",
    ]
    feed = load("evidence/snapshots/s23_source_feed.json")
    archive = load("evidence/s23_download_audit.json")
    card = {
        "schema": "gems28-negative-audit-v1",
        "session_id": "G28-S23-20261027",
        "date_utc": "2026-10-27",
        "branch": "arena/a774f0a0-gemsdoe28",
        "lane": None,
        "lane_status": "No method paragraph supplied; no external/exclusive lane invented. Read-only registry/preflight audit only.",
        "hypothesis": "Proposed PCSE: catalogue-missing displacement might preserve cross-scale odd/even step phase even where gradient amplitude is weak. UNIMPLEMENTED and UNTESTED.",
        "mechanism": "Oriented cross-profile first/second derivative energy and scale-consistent polarity; no finding of a fault or geothermal vent is claimed.",
        "non_fault_mimic": "Terrace risers, paleoshorelines, road cuts and unfaulted lithologic contacts.",
        "holdout": {
            "label": "HOLDOUT-DTI",
            "status": "NOT RUN: preflight/registry stop before a geological experiment",
            "evaluator_version": "gems-segment-pooled-v1 (pinned shared SegmentHoldout, available but not run on a new model)",
            "dti": None, "ci95": None, "withheld_positives": None,
            "baseline_dti": None, "paired_gain": None, "paired_gain_ci95": None,
            "alpha": 0.2, "beta": 0.8, "kernel": "triangular", "kernel_m": 300,
        },
        "feature_names": [], "feature_canaries": {},
        "canary_status": "No model features implemented/tested; an empty result is NOT a canary pass.",
        "registry": {
            "complete": False,
            "scope": "Nine historical focus files plus one sufficient rejecting comparator from the pinned shared registry; not a synchronized global parallel registry.",
            "control_sha256": geometry["control"]["sha256"],
            "manifest_sha256": geometry["control"]["shared_registry_sha256"],
            "preplacement_surface": "NOT AVAILABLE / NOT TESTED; no new placement performed",
            "inherited_candidate_sha256": inherited["sha256"],
            "inherited_final_raw_spearman": compare["raw_spearman"],
            "inherited_final_kernel_spearman_sample200k": compare["kernel_spearman"],
            "inherited_final_within_3px_fraction": compare["candidate_dot_overlap_within_3px"],
            "inherited_duplicate": inherited["duplicate_under_literal_rule"],
            "bounds": geometry["bounds"],
        },
        "raster_sha256": None,
        "validator": {
            "status": "NOT RUN ON A NEW TIFF: no new file exists",
            "no_nan_inside": None, "range_0_1": None, "crs_match": None,
            "shape_match": None, "transform_match": None, "single_band": None,
            "inherited_only_format_valid": inherited["format_validator"]["format_valid"],
            "inherited_only_sha256": inherited["sha256"],
            "inherited_scope": "Historical file passes shared format checks but fails novelty; format does not authorize upload.",
        },
        "submission_name": None,
        "note": "S23 audit: no new TIFF; inherited S22C fails literal registry rule. No weekly slot selected.",
        "submission_note": "S23 audit: no new TIFF; inherited S22C fails literal registry rule. No weekly slot selected.",
        "estimated_leaderboard_score": None,
        "estimate_status": "Unavailable; withdraw the historical ratio projection from current recommendations. No organizer receipt or validated transfer calibration.",
        "verdict": "negative", "submission_ready": False, "ok_to_submit": False,
        "ok_to_download_new_submission": False, "new_tiff_generated": False,
        "experiments_run": 0, "experiment_cap": 3, "time_cap_seconds": 7200,
        "slot_selected": False, "submission_slots_spent": 0, "weekly_cap": None,
        "scientific_work_stopped_at": "Registry/preflight; no model fitted, no new surface, no new dots, no budget tuning around lattice holes.",
        "evidence_sha256": {p: sha(p) for p in evidence_paths},
        "implementation_sha256": {p: sha(p) for p in [
            "scripts/finalize_s23_audit.py", "scripts/audit_registry_feasibility.py",
            "src/gems27/registry_feasibility.py", "src/gems27/cache_contract.py",
            "scripts/prepare_data.py", "scripts/check_run_preflight.py",
            "scripts/audit_shared_template.py", "scripts/build_site.py", "scripts/site_s23.py",
            "scripts/finalize_s22c.py",
        ]},
        "historical_snapshot_sha256": {p: sha(p) for p in [
            "evidence/snapshots/pre_s23_current_session.json",
            "evidence/snapshots/pre_s23_protocol_assets.json",
            "evidence/snapshots/pre_s23_download_manifest.json",
            "evidence/snapshots/pre_s23_finalize_s22c.py",
            "evidence/snapshots/pre_s23_audit_shared_template.py",
        ]},
        "source_feed_observation": {
            "snapshot": "evidence/snapshots/s23_source_feed.json",
            "checked_at_utc": feed["checked_at_utc"], "status": feed["status"],
            "source_count": feed["source_count"], "freshly_observed_count": feed["freshly_observed_count"],
            "scope": "GitHub metadata only for freshly observed entries; not new scientific-content verification. Old dated non-GitHub observations are retained, not refreshed.",
        },
        "archive_audit": {
            "status": archive["status"], "check_count": archive["check_count"],
            "failures": archive["failures"],
            "scope": "51 historical TIFFs registered, not 51 files approved. Two legacy allfinite variants retain NaN nodata metadata; not repaired/renamed as new candidates. Earlier portal-error causation remains unknown.",
        },
        "limitations": [
            "The requested unique submission and top-candidate holdout were not completed: the literal overlap gate is infeasible at 37,654 dots and the inherited lane is a measured duplicate.",
            "A smaller budget is not universally impossible, but selecting cells to avoid this calibration lattice would evade the rule rather than establish a geological strategy.",
            "Explicit assigned lane, synchronized complete registry, strict comparable frozen best, current authenticated weekly allowance and organizer receipts are unavailable.",
            "Input integrity is checked against owner mirrors, not authenticated organizer downloads; official non-GitHub hosts and new DEM tiles are outside runtime network access.",
            "Synthetic shared-tool tests are software validation only; they do not establish a new HOLDOUT-DTI or a higher leaderboard score.",
            "Optional legacy input restoration hit the GitHub REST rate limit after nine existing inputs were re-verified; five input-dependent tests remain skipped, not passed.",
        ],
    }
    assert len(card["note"]) <= 140
    save("evidence/s23_run_card.json", card)
    for path in ["docs/data/s23_run_card.json", "docs/data/current_run_card.json", "docs/data/current_run_card_2026-10-27.json"]:
        save(path, card)
    save("docs/data/s23_scorecard.json", scorecard)
    (ROOT / "docs/data/s23_scorecard.csv").write_text(site_s23.score_csv(scorecard), newline="")
    print(json.dumps({"verdict": "negative", "sites": len(rows), "new_tiff_generated": False,
                      "submission_ready": False, "geological_experiments_run": 0,
                      "run_card": "evidence/s23_run_card.json"}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
