#!/usr/bin/env python3
"""S15 finalize: assemble the run card + manifest slot + note/checks files from evidence.

Verdict rule (knowledge/47 §4/§6, parallel-run protocol point 5): `promote` (to the separate
selector step; never a slot spend by this session) iff ALL of: LOSFO gate passed,
uniqueness passed (surface Spearman <= 0.90 and <= 70% dots within 3 px vs every registry
raster), and both GeoTIFF variants pass every hard validator check. Otherwise `negative`.
Negative results are deliverables: the TIF stays downloadable for inspection, banner-marked
DO NOT SUBMIT everywhere this script writes text.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(name: str) -> dict:
    return json.loads((ROOT / "evidence" / name).read_text())


def main() -> int:
    gate = load("s15_h39_1_losfo_gate.json")["s15_depthslice_h39_1"]
    build = load("s15_candidate_build.json")
    canary = load("s15_canary.json")
    cid = build["content_id"]
    gate_pass = bool(gate["gate_passed"])
    uniq_pass = bool(build["uniqueness_pass"])
    val_pass = bool(build["verify_nan"]["hard_checks_passed"]
                    and build["verify_allfinite"]["hard_checks_passed"])
    verdict = "promote" if (gate_pass and uniq_pass and val_pass) else "negative"
    reasons = []
    if not gate_pass:
        reasons.append(f"LOSFO gate FAILED (pooled dDTI {gate['pooled_delta_dti_d1_minus_d0']:+.6f})")
    if not uniq_pass:
        reasons.append("uniqueness FAILED vs registry")
    if not val_pass:
        reasons.append("validator hard check FAILED")

    submission_name = f"GEMSDOE28-h39-1-depthslice-persist-b2-{cid}"
    delta = gate["pooled_delta_dti_d1_minus_d0"]
    if verdict == "promote":
        note = (f"28GEMSDOE H39-1 depthslice B2 | LOSFO dDTI {delta:+.4f} (290-294) gate PASS; "
                f"UNSCORED | id {cid}")
    else:
        note = (f"28GEMSDOE H39-1 depthslice B2 | LOSFO GATE FAIL dDTI {delta:+.4f} (290-294) "
                f"DO NOT SUBMIT | id {cid}")
    assert len(note) <= 140, (len(note), note)

    dl = ROOT / "docs/downloads"
    note_name = f"note-gemsdoe28-h39-1-{cid}.txt"
    (dl / note_name).write_text(note + "\n")
    checks_name = f"checks-{build['nan_tif'].removesuffix('.tif')}.json"
    (dl / checks_name).write_text(json.dumps({
        "content_id": cid, "note": note, "note_chars": len(note),
        "variants": {"nan": build["verify_nan"], "allfinite": build["verify_allfinite"]},
        "uniqueness_vs_registry": build["uniqueness_vs_registry"],
        "spearman_probD1_vs_probD0_sample400k": build["spearman_probD1_vs_probD0_sample400k"],
    }, indent=2) + "\n")

    worst = max(build["uniqueness_vs_registry"].items(),
                key=lambda kv: kv[1]["frac_our_dots_within3px"])
    run_card = {
        "session": "S15 (2026-10-25), branch arena/5ac802ba-gemsdoe28, lane H39-1 (knowledge/47 §3)",
        "hypothesis": "Depth-persistent potential-field lineaments (TMI/gravity upward-continued "
                      "1-2 km) mark basement faults buried under cover that the surface-scarp "
                      "catalogue omits; adding them as detector bands + persistence-weighted "
                      "ranking raises far-field DTI at the champion's budget.",
        "mechanism": "Upward continuation exp(-|k|h) attenuates shallow sources; HG ridges "
                     "persisting to 2 km indicate deep-rooted contacts. 5 label-free bands "
                     "appended to the frozen 32-band GBDT; candidates ranked by "
                     "prob*(0.5+persist_rank); dot_thin(2.8); build-time d_cat>2px exclusion.",
        "named_nonfault_mimic": "Basement lithologic contacts and mafic dike swarms (deep-persistent "
                                "magnetic lineaments with zero Quaternary slip); GeoDAWN flight-line striping.",
        "holdout_dti": {
            "label": "HOLDOUT-DTI (not an organizer score)",
            "evaluator": gate["evaluator"],
            "seeds": "290-294 (20 paired cells)",
            "n_withheld_positives_pooled_cell_truth_px": gate["n_withheld_positives_pooled_cell_truth_px"],
            "d0_pooled_dti": gate["arms_pooled"]["d0"]["pooled_dti"],
            "d1_pooled_dti": gate["arms_pooled"]["d1"]["pooled_dti"],
            "pooled_delta_dti": delta,
            "mean_paired_delta_dti": gate["mean_paired_delta_dti"],
            "ci95_paired_bootstrap": gate["ci95_paired_bootstrap_10k_seed290"],
            "d1nw_mean_paired_delta_dti": gate["mean_paired_delta_dti_d1nw_minus_d0"],
            "cells_positive": f"{gate['cells_positive']}/20",
            "per_seed_mean_delta": gate["per_seed_mean_delta"],
            "per_fold_mean_delta": gate["per_fold_mean_delta"],
            "credit_per_dot_d0": gate["arms_pooled"]["d0"]["credit_per_dot"],
            "credit_per_dot_d1": gate["arms_pooled"]["d1"]["credit_per_dot"],
            "tau_at_d0": gate["tau_at_d0_pooled_dti"],
            "gate": gate["gate"], "gate_passed": gate_pass,
            "canary_single_feature_aucs": canary["single_feature_auc_vs_hidden_systems"],
        },
        "organizer_confirmed_scores": "none (no submission-page receipt exists for any file here; "
                                      "0.2778/0.2750/0.2708/0.2600 are OWNER-REPORTED)",
        "correlation_overlap_vs_registry": {
            "spearman_probD1_vs_probD0_sample400k": build["spearman_probD1_vs_probD0_sample400k"],
            "worst_registry_raster_by_dot_overlap": {"raster": worst[0],
                                                     "frac_our_dots_within3px": worst[1]["frac_our_dots_within3px"],
                                                     "spearman_vs_binary": worst[1]["spearman_probD1_vs_binary_sample400k"]},
            "full_table": build["uniqueness_vs_registry"],
            "thresholds": {"rank_corr_max": 0.90, "dots_within3px_max": 0.70},
            "uniqueness_pass": uniq_pass,
        },
        "raster_sha256": {"nan": build["sha256_nan"], "allfinite": build["sha256_allfinite"],
                          "zip": build["sha256_zip"]},
        "validator_output": {
            "nan_hard_checks_passed": build["verify_nan"]["hard_checks_passed"],
            "allfinite_hard_checks_passed": build["verify_allfinite"]["hard_checks_passed"],
            "summary": "no NaN inside footprint; values exactly {0,1} in [0,1]; CRS EPSG:32611, "
                       "shape 3730x3292, transform = template; 0 dots on catalogue; "
                       f"{build['emitted_px']} emitted px (min d_cat {build['min_d_cat_of_dots_px']:.2f} px)",
            "detail_file": f"docs/downloads/{checks_name}",
        },
        "submission_name": submission_name,
        "note_le140": note,
        "candidate_files": {"nan": build["nan_tif"], "allfinite": build["allfinite_tif"],
                            "zip": build["zip"]},
        "verdict": verdict,
        "verdict_reasons": reasons or ["all gates passed"],
        "slot_spent_by_this_session": False,
        "experiments_used": "3 of 3 (Exp1 canary, Exp2 LOSFO gate 290-294, Exp3 build)",
    }
    (ROOT / "evidence/s15_run_card.json").write_text(json.dumps(run_card, indent=2) + "\n")

    manifest_path = dl / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["s15_candidate"] = {
        "slug": build["slug"],
        "hypothesis": "H39-1 depth-sliced potential-field lineaments (TMI/gravity upward "
                      "continued 1-2 km) + persistence-weighted re-detection, d_cat>2px build hygiene",
        "content_id": cid,
        "nan": build["nan_tif"], "allfinite": build["allfinite_tif"], "zip": build["zip"],
        "sha256_nan": build["sha256_nan"], "sha256_allfinite": build["sha256_allfinite"],
        "sha256_zip": build["sha256_zip"],
        "bytes_nan": build["bytes_nan"], "bytes_allfinite": build["bytes_allfinite"],
        "bytes_zip": build["bytes_zip"], "emitted_px": build["emitted_px"],
        "format_verified": val_pass,
        "status": ("UNSCORED" if verdict == "promote" else "DO NOT SUBMIT — HOLDOUT GATE FAILED")
                  + f"; HOLDOUT-DTI LOSFO seeds 290-294 pooled dDTI {delta:+.6f} "
                  f"(95% CI [{gate['ci95_paired_bootstrap_10k_seed290'][0]:+.4f}, "
                  f"{gate['ci95_paired_bootstrap_10k_seed290'][1]:+.4f}], "
                  f"{gate['cells_positive']}/20 cells); uniqueness "
                  f"{'PASS' if uniq_pass else 'FAIL'} (worst {worst[1]['frac_our_dots_within3px']:.1%} "
                  f"dots within 3px of {worst[0]}); verdict {verdict}; "
                  "research/inspection only, no slot spent, selector step separate.",
        "note": note, "note_file": note_name,
        "submission_name": submission_name,
        "run_card": "evidence/s15_run_card.json",
        "holdout_evidence": "evidence/s15_h39_1_losfo_gate.json",
        "holdout_preregistration": "knowledge/47_s15_hypotheses_and_preregistration_H39-1.md",
        "holdout_seeds": "290-294",
        "verdict": verdict,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"verdict": verdict, "reasons": reasons, "note": note,
                      "submission_name": submission_name}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
