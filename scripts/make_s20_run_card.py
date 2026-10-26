#!/usr/bin/env python3
"""Assemble evidence/session20_h43_run_card.json from the three S20 evidence files.

Run after scripts/build_s20_candidate.py. Pure assembly — no measurement is redone here;
every number is copied from evidence/s20_exp1_forensic.json, s20_holdout.json and
s20_build.json so the card can never drift from the underlying evidence.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    e1 = json.loads((ROOT / "evidence/s20_exp1_forensic.json").read_text())
    ho = json.loads((ROOT / "evidence/s20_holdout.json").read_text())
    b = json.loads((ROOT / "evidence/s20_build.json").read_text())
    u = b["uniqueness"]
    card = {
        "schema_version": 1,
        "session_id": "G28-S20H43-20261026",
        "date_utc": "2026-10-26",
        "branch": "arena/36be803a-gemsdoe28",
        "parallel_session_collision": "Renamed from evidence/session20_run_card.json at merge time: a concurrent Session 20 validation review on main owns that filename (knowledge/56_session20_validation_review.md). A concurrent S19-ASCP experiment also landed on main. Never pool numbers across these sessions; see s20-parallel-session-id-collision in registry/irregularities.json.",
        "lane": "H43-1 TPB2-GKC: tip-protected B2 eligibility + greedy triangular-kernel "
                "max-cover re-placement over the H19-5 pool at champion budget",
        "lane_assignment_source": "Prompt's method-paragraph assignment absent (as in Session 19); "
                                  "lane self-declared in knowledge/56_s20_preregistration_H43-1.md "
                                  "before any experiment and disclosed there.",
        "hypothesis": "Rescuing along-strike tip-continuation dots (ring <=2 px, <=3 px from a "
                      "catalogue endpoint) that blind B2 deleted, and re-placing all dots by greedy "
                      "kernel max-cover instead of raster-order dot_thin phase, earns more credit "
                      "per dot at the champion's budget.",
        "mechanism": "Eligibility = pool & off-visible-catalogue & (d_visible>2 | d_endpoint<=3). "
                     "Deterministic lazy-greedy placement maximising covered H19-5 pool mass under "
                     "k(d)=max(1-d/3,0), min inter-dot distance 2.8 px, target 37,654 dots.",
        "named_non_fault_mimic": "Catalogue digitisation endpoints (mapping truncations, not "
                                 "geological tips) and inherited H19-5 cultural lineaments "
                                 "(roads/strandlines).",
        "holdout": {
            "label": "HOLDOUT-DTI",
            "status": "RUN — gate FAILED",
            "evaluator_version": "src/gems27/metric.py:dti_binary via holdout.make_split; "
                                 "alpha=0.2 beta=0.8 300m triangular kernel; seeds 340-344 x 4 "
                                 "quadrants = 20 cells",
            "withheld_positives": {"pooled": ho["withheld_positives_pooled"],
                                   "unique": ho["withheld_positives_unique"]},
            "candidate_dti": ho["pooled_C1_H43_1"]["dti"],
            "baseline_dti_C0_champion_analogue": ho["pooled_C0_champion_analogue"]["dti"],
            "pooled_gain": ho["pooled_gain"],
            "mean_paired_gain": ho["mean_paired_gain"],
            "cells_positive": ho["cells_positive"],
            "ci95_fold_block_paired_gain": ho["ci_fold_block"]["paired_gain_ci95"],
            "ci95_cell_sensitivity_paired_gain": ho["ci_cell_sensitivity"]["paired_gain_ci95"],
            "candidate_ci95_fold_block": ho["ci_fold_block"]["candidate_ci95"],
            "credit_per_dot": {"candidate": ho["pooled_C1_H43_1"]["credit_per_dot"],
                               "baseline": ho["pooled_C0_champion_analogue"]["credit_per_dot"]},
            "gates": ho["gates"], "gate_pass": False,
            "bias_disclosure": ho["bias_disclosure"],
        },
        "feature_alone_leakage_canaries": {
            "status": "RUN (Experiment 1, seed-340 assignment only)",
            "features_tested": ["neg_d_visible", "ring_le2_indicator", "tip_indicator",
                                "eligible_indicator", "pool_indicator"],
            "max_auc": e1["canary_max_auc"], "auc_gt_0_90_stop": False,
        },
        "registry_comparison": {
            "status": "RUN — protocol duplicate (family lane), not an exact duplicate",
            "registry_distinct_dot_sets": u["registry_distinct_dot_sets"],
            "surface_max_abs_spearman": u["surface_max_abs_spearman"],
            "max_dot_fraction_within_3px": u["final_dots_max_fraction_within_3px"],
            "vs_champion_g32": u["vs_champion"],
            "exact_duplicate_of_any_registry": u["exact_duplicate_of_any_registry"],
            "duplicate_by_protocol": u["duplicate_by_protocol"],
            "thresholds": u["thresholds"],
            "registry_complete": False,
            "scope_note": "22 distinct dot sets from local docs/downloads + restored family + "
                          "GEMSDOE32 champion education copy (data/, git-ignored). Not a "
                          "synchronised cross-repo registry.",
        },
        "raster_sha256": b["files"]["primary_sha256"],
        "raster": {"primary_file": b["files"]["primary_file"],
                   "primary_bytes": b["files"]["primary_bytes"],
                   "nan_file": b["files"]["nan_file"], "nan_sha256": b["files"]["nan_sha256"],
                   "zip_file": b["files"]["zip_file"], "zip_sha256": b["files"]["zip_sha256"],
                   "dots": b["dots"], "target_budget": b["target_budget"],
                   "budget_reached": b["budget_reached"]},
        "validator": {
            "status": "RUN — all hard checks pass on both variants (exact-file re-read via "
                      "src/gems27/submission.py:verify_geotiff)",
            "no_nan_inside_footprint": True, "no_nan_anywhere_primary": True,
            "values_in_0_1": True, "whole_array_min_max_primary": [0.0, 1.0],
            "crs_match": "EPSG:32611", "shape_match": [3730, 3292],
            "transform_match": True, "single_band": True,
            "checks_primary": b["verify_primary_checks"],
        },
        "submission_name": b["stem"],
        "submission_note": b["note"],
        "experiments_run": 3, "experiment_cap": 3,
        "new_tiff_generated": True, "slot_selected": False,
        "organizer_confirmed_scores": [],
        "user_reported_score_claims": {
            "status": "USER-REPORTED / UNVERIFIED; excluded from HOLDOUT-DTI and ORGANIZER-CONFIRMED",
            "highest_in_nine_sites": {
                "site": "GEMSDOE32",
                "artifact": "h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros",
                "value": 0.2778,
                "sha256_verified_this_session":
                    "c55bafc470054e8271dcb89347a17e07fefe50de6af6e6ba6c4b169ef7ab6fa9",
                "construction_verified": "solo-r1 (40,199) minus d(catalogue)<=2px (2,545 removed, "
                                         "0 added); symmetric difference 0",
                "conflict": "Champion's own audit JSON at GEMSDOE32@012e17b labels the file UNSCORED "
                            "with MODEL projection 0.2747 (predicted_leaderboard_dti "
                            "0.27467315976932155).",
            },
            "other_leaderboard_maxima_in_prompt": [0.3195, 0.4413],
            "note": "Conflicting leader maxima not freshly verified; no submission-page receipt "
                    "obtained.",
        },
        "verdict": "negative", "promotion_eligible": False, "submission_ready": False,
        "decision": "DO NOT SUBMIT the Session 20 TIFF (holdout gate failed, packing exhausted at "
                    "88.6% of target, protocol-duplicate family lane). Best existing file remains "
                    "the GEMSDOE32 champion, subject to a separate selector/receipt check on the "
                    "account side.",
        "next_gate": "Fresh preregistered lane with fresh seeds (>=350): displaced potential-field "
                     "piercing markers on restored training_features.tif; or packing-first dot_thin "
                     "+ swap improvement labelled as champion-lane refinement, not a new lane.",
        "evidence": ["knowledge/56_s20_preregistration_H43-1.md", "evidence/s20_exp1_forensic.json",
                     "evidence/s20_holdout.json", "evidence/s20_build.json",
                     "knowledge/57_s20_result.md"],
    }
    out = ROOT / "evidence/session20_h43_run_card.json"
    out.write_text(json.dumps(card, indent=1) + "\n")
    print("wrote", out, "| note chars:", len(card["submission_note"]),
          "| raster:", card["raster"]["primary_file"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
