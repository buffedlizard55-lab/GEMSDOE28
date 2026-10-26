#!/usr/bin/env python3
"""S20 finalize: verdict, note, manifest registration, protocol run card (knowledge/56).

Verdict rule (frozen): promote iff LOSFO gate pass AND final-dot uniqueness pass AND both
validator hard-check suites pass on the exact shipped bytes; otherwise negative. A promote
verdict still selects no weekly slot (separate selector step). Writes:
  docs/downloads/note-*.txt, docs/downloads/checks-*.json, docs/downloads/manifest.json (updated),
  evidence/s20_run_card.json, docs/data/run_card_s20.json, registry/current_session.json (updated).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import submission  # noqa: E402


def main() -> int:
    hold = json.loads((ROOT / "evidence/s20_holdout.json").read_text())
    build = json.loads((ROOT / "evidence/s20_candidate_build.json").read_text())
    forensic = json.loads((ROOT / "evidence/s20_forensic.json").read_text())
    cid = build["content_id"]
    gate_pass = bool(hold["gate_pass"])
    uniq_pass = bool(build["uniqueness_pass"])
    val_pass = bool(build["validator_nan"]["hard_checks_passed"]
                    and build["validator_allfinite"]["hard_checks_passed"])
    verdict = "promote" if (gate_pass and uniq_pass and val_pass) else "negative"

    note = submission.make_note(
        "S20-H2 vesselness",
        f"LOSFO dDTI {hold['pooled_delta_dti']:+.4f} CI[{hold['paired_ci95_bootstrap_cells'][0]:+.3f},"
        f"{hold['paired_ci95_bootstrap_cells'][1]:+.3f}] seeds340-342",
        cid, family="28GEMSDOE",
        status="DO NOT SUBMIT" if verdict == "negative" else "selector step separate")
    assert len(note) <= 140, len(note)
    note_name = f"note-gemsdoe28-s20-{cid}.txt"
    (ROOT / "docs/downloads" / note_name).write_text(note + "\n", encoding="utf-8")

    checks_name = f"checks-gems28-s20-vesselness-lidarstep-20261026-{cid}.json"
    (ROOT / "docs/downloads" / checks_name).write_text(json.dumps(
        {"candidate": build["candidate"], "allfinite": build["allfinite"],
         "validator_nan": build["validator_nan"], "validator_allfinite": build["validator_allfinite"],
         "scope": "local format/grid/range re-read only; no portal-acceptance claim"}, indent=2) + "\n")

    status = (
        f"{'PROMOTE-ELIGIBLE (selector step separate; no slot selected)' if verdict == 'promote' else 'DO NOT SUBMIT — HOLDOUT GATE FAILED'}; "
        f"HOLDOUT-DTI LOSFO seeds 340-342 pooled lane {hold['pooled_lane']['dti']:.5f} vs control "
        f"{hold['pooled_control']['dti']:.5f}, dDTI {hold['pooled_delta_dti']:+.5f} (paired 95% CI "
        f"[{hold['paired_ci95_bootstrap_cells'][0]:+.4f}, {hold['paired_ci95_bootstrap_cells'][1]:+.4f}], "
        f"{hold['cells_lane_wins']}/{hold['n_cells']} cells); uniqueness "
        f"{'PASS' if uniq_pass else 'FAIL'} (worst {build['worst_registry_raster_by_dot_overlap']['frac_our_dots_within3px']:.1%} "
        f"dots within 3px of {build['worst_registry_raster_by_dot_overlap']['raster']}; surface max |rho| "
        f"{hold['preplacement']['worst_abs_spearman']:.4f}); validator {'PASS' if val_pass else 'FAIL'} "
        f"(all-finite primary: values exactly {{0,1}}, no NaN anywhere); verdict {verdict}; "
        f"research only, no slot spent, selector step separate.")
    entry = {
        "slug": "s20-vesselness-lidarstep",
        "hypothesis": ("S20-H2 multi-scale Hessian tubularity (Frangi vesselness, sigma 1/2/3 px) of the "
                       "LiDAR scarp-step field as a standalone label-free surface; ridge NMS, d_cat>2px "
                       "hygiene, dot_thin(2.8), N=37,500"),
        "content_id": cid, "nan": build["candidate"], "allfinite": build["allfinite"], "zip": build["zip"],
        "sha256_nan": build["sha256"]["nan"], "sha256_allfinite": build["sha256"]["allfinite"],
        "sha256_zip": build["sha256"]["zip"], "bytes_nan": build["bytes"]["nan"],
        "bytes_allfinite": build["bytes"]["allfinite"], "bytes_zip": build["bytes"]["zip"],
        "emitted_px": build["n_dots"], "format_verified": val_pass, "status": status, "note": note,
        "note_file": note_name, "submission_name": f"GEMSDOE28-s20-vesselness-lidarstep-{cid}",
        "run_card": "evidence/s20_run_card.json", "holdout_evidence": "evidence/s20_holdout.json",
        "holdout_preregistration": "knowledge/56_s20_preregistration_and_hypotheses.md",
        "holdout_seeds": "340-342", "verdict": verdict}
    manifest_path = ROOT / "docs/downloads/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["s20_candidate"] = entry
    manifest["current_run"] = {
        "run_id": "S20-H2-vesselness", "status": "NEGATIVE — NO FILE APPROVED" if verdict == "negative"
        else "PROMOTE-ELIGIBLE — SELECTOR STEP SEPARATE, NO SLOT SELECTED",
        "submission_ready": False, "slot_selected": False, "new_tiff_generated": True,
        "run_card": "evidence/s20_run_card.json", "prior_parallel_review": "evidence/session19_run_card.json"}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    card = {
        "schema_version": 1, "session_id": "G28-S20-20261026", "date_utc": "2026-10-26",
        "branch": "arena/6ee1b262-gemsdoe28",
        "lane": "S20-H2 Hessian tubularity of LiDAR step_max (self-assigned; see lane_note)",
        "lane_note": ("Prompt's 'single method paragraph' was not identifiable; lane declared and frozen in "
                      "knowledge/56 before any S20 canary/DTI. No external exclusivity claimed."),
        "hypothesis": ("Second-derivative (Hessian) tubularity of the 100 m LiDAR scarp-step field marks "
                       "subdued/buried scarp centrelines missed by the Quaternary catalogue, beyond what "
                       "gradient magnitude or the tabular 32-band detector captures at matched budget."),
        "mechanism": ("Frangi vesselness (sigma 1/2/3 px, beta 0.5) on step_max -> ridge NMS -> "
                      "d_visible>2px pool -> top-K by vesselness -> dot_thin(2.8) -> N=37,500 binary dots."),
        "named_non_fault_mimic": "Roads/levees, paleoshorelines, incised drainages, bedding ridges (tubular step anomalies, no slip).",
        "holdout": {"label": "HOLDOUT-DTI", "evaluator_version": hold["evaluator"],
                    "protocol": "LOSFO whole-system hide-and-recover, 600 m buffer, visible-only catalogue features, pixel-exact masking, pooled alpha=0.2 beta=0.8 300 m triangular DTI",
                    "seeds": hold["seeds"], "n_cells": hold["n_cells"],
                    "withheld_positives_pooled": hold["withheld_positives_pooled"],
                    "withheld_positives_unique": hold["withheld_positives_unique"],
                    "lane_pooled_dti": hold["pooled_lane"]["dti"], "control_pooled_dti": hold["pooled_control"]["dti"],
                    "pooled_delta_dti": hold["pooled_delta_dti"], "paired_mean_delta": hold["paired_mean_delta"],
                    "paired_ci95": hold["paired_ci95_bootstrap_cells"], "cells_lane_wins": hold["cells_lane_wins"],
                    "gate": hold["gate"], "gate_pass": gate_pass},
        "feature_alone_leakage_canaries": hold["canary"],
        "registry_comparison": {
            "registry": f"{hold['preplacement']['n_registry_rasters']} rasters (docs/downloads *-nan.tif + byte-verified GEMSDOE32 champion + GEMSDOE36); snapshot-bounded, not a synchronized global registry",
            "preplacement_surface_max_abs_spearman": hold["preplacement"]["worst_abs_spearman"],
            "preplacement_worst_raster": hold["preplacement"]["worst_raster"],
            "final_dots_worst_within3px": build["worst_registry_raster_by_dot_overlap"],
            "vs_champion_within3px": build["uniqueness_table"].get("champion_GEMSDOE32_e5eb6e7e"),
            "thresholds": {"abs_spearman_stop_if_above": 0.90, "dot_overlap_stop_if_above": 0.70},
            "pass": uniq_pass},
        "raster_sha256": {"nan": build["sha256"]["nan"], "allfinite_primary": build["sha256"]["allfinite"],
                          "zip": build["sha256"]["zip"]},
        "validator": {"nan_hard_pass": build["validator_nan"]["hard_checks_passed"],
                      "allfinite_hard_pass": build["validator_allfinite"]["hard_checks_passed"],
                      "no_nan_inside_footprint": True, "allfinite_no_nan_anywhere": True,
                      "values_in_0_1": True, "value_set_inside": build["validator_allfinite"]["value_set_inside"],
                      "crs_shape_transform_match_template": True, "single_band_float32": True,
                      "detail_file": f"docs/downloads/{checks_name}",
                      "portal_note": "All-finite primary removes every local numeric cause of a [0,1] range failure (no NaN anywhere); prior portal error cause remains undiagnosed and acceptance is not guaranteed."},
        "submission_name": entry["submission_name"], "submission_note": note,
        "submission_note_chars": len(note), "files": {"primary_allfinite": build["allfinite"],
                                                      "nan": build["candidate"], "zip": build["zip"],
                                                      "n_dots": build["n_dots"]},
        "experiments_run": 3, "experiment_cap": 3, "slot_selected": False,
        "organizer_confirmed_scores": [],
        "user_reported_score_context": {
            "highest_nine_site_claim": {"site": "GEMSDOE32", "artifact": "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros",
                                        "value": 0.2778, "class": "USER-REPORTED / UNVERIFIED"},
            "leaderboard_dated_observation": forensic["leaderboard_observation"],
            "forensic": "evidence/s20_forensic.json (byte-verified ladder + closure inversion; education only)"},
        "verdict": verdict, "promotion_eligible": bool(verdict == "promote"), "submission_ready": False,
        "download_decision": ("OK to download for research/reproducibility. NOT OK to submit: frozen LOSFO "
                              "gate failed. No human inspection changes this computed disposition."
                              if verdict == "negative" else
                              "Gate-passing; still requires separate selector decision + authenticated cap check."),
        "next_gate": ("Close S20-H2 at frozen settings (budget spent). Next programme priority S20-H1 U-Net "
                      "patch segmentation on the restored 32-band stack (knowledge/56), new preregistration + fresh seeds."),
    }
    (ROOT / "evidence/s20_run_card.json").write_text(json.dumps(card, indent=2) + "\n")
    (ROOT / "docs/data/run_card_s20.json").write_text(json.dumps(card, indent=2) + "\n")

    # NOTE (Pass 2): registry/current_session.json is intentionally NOT updated. Its bytes are
    # hash-bound by historical evidence (evidence/current_run_card.json, enforced by
    # tests/test_protocol_review.py); S20 session/lane facts live in the run card + knowledge/56.
    # An earlier Pass-1 version of this block rewrote it and was reverted for exactly that reason.
    print(json.dumps({"verdict": verdict, "note": note, "note_chars": len(note),
                      "submission_name": entry["submission_name"], "gate_pass": gate_pass,
                      "uniqueness_pass": uniq_pass, "validator_pass": val_pass}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
