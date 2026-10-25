#!/usr/bin/env python3
"""S18 finalize: verdict from frozen gate + uniqueness + validator (knowledge/52).

Writes docs/downloads/manifest.json slot `s18_h39_5_candidate`, the portal note file,
evidence/s18_h39_5_run_card.json and docs/data/run_card_s18_2026-10-25.json.
Verdict `promote` (to the separate selector step only; never slot-approved)
requires gate_passed AND uniqueness_pass_strict AND both validators pass;
anything else is `negative` and the file is banner-marked DO NOT SUBMIT.
All numbers are read from the evidence files, never restated by hand here.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        while c := f.read(1 << 20):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    gate = json.loads((ROOT / "evidence/s18_h39_5_losfo_gate.json").read_text())
    build = json.loads((ROOT / "evidence/s18_candidate_build.json").read_text())
    canary = json.loads((ROOT / "evidence/s18_canary.json").read_text())
    dl = ROOT / "docs/downloads"
    nan_name, af_name, zip_name = build["files"]["nan"], build["files"]["allfinite"], build["files"]["zip"]
    cid = build["content_id"]
    validators_ok = bool(build["validator_nan"]["hard_checks_passed"]
                         and build["validator_allfinite"]["hard_checks_passed"])
    promote = bool(gate["gate_passed"] and build["uniqueness_pass_strict"] and validators_ok)
    verdict = "promote" if promote else "negative"

    d = gate["pooled_delta_dti"]
    lo, hi = gate["ci95_paired_bootstrap"]
    worst = build["worst_registry_raster_by_dot_overlap"] or {}
    gate_word = "PASS" if gate["gate_passed"] else "FAIL"
    uniq_word = "PASS" if build["uniqueness_pass_strict"] else "FAIL"
    tail = "promote-to-selector UNSCORED" if promote else "DO NOT SUBMIT"
    note = (f"28GEMSDOE H39-5 extrap35 | LOSFO dDTI {d:+.4f} CI[{lo:+.3f},{hi:+.3f}] "
            f"gate {gate_word} uniq {uniq_word} {tail} | id {cid}")
    assert len(note) <= 140, len(note)
    note_file = f"note-gemsdoe28-h39-5-{cid}.txt"
    (dl / note_file).write_text(note + "\n")

    failed_gates = [k for k, v in gate["gate"].items() if not v]
    status = (
        f"{'PROMOTE TO SELECTOR (not slot-approved)' if promote else 'DO NOT SUBMIT'}; "
        f"HOLDOUT-DTI LOSFO seeds 310-314 pooled dDTI {d:+.6f} "
        f"(paired 95% CI [{lo:+.4f}, {hi:+.4f}], {gate['cells_positive']}/20 cells; "
        f"gate {gate_word}{(' (' + ', '.join(failed_gates) + ')') if failed_gates else ''}); "
        f"uniqueness {uniq_word} (worst {worst.get('frac_our_dots_within3px', 0):.1%} dots within "
        f"3px of {worst.get('raster')}; lane-surface |Spearman| max "
        f"{canary['preplacement_uniqueness']['worst_abs_spearman']['value']:.4f}); "
        f"validator {'PASS' if validators_ok else 'FAIL'} (values exactly {{0,1}} inside, "
        f"no NaN inside footprint; all-finite variant has no NaN anywhere); "
        f"verdict {verdict}; UNSCORED, no organizer receipt, no slot spent, "
        f"selector step separate."
    )
    slot = {
        "slug": "h39-5-extrap-swap35",
        "hypothesis": ("H39-5 migration-extrapolated placement: weakest 35% of the frozen "
                       "32-band detector emission replaced 1-for-1 by TMI/gravity "
                       "shallow-minus-migration-vector positions (knowledge/52)"),
        "content_id": cid,
        "nan": nan_name, "allfinite": af_name, "zip": zip_name,
        "sha256_nan": sha256_file(dl / nan_name), "sha256_allfinite": sha256_file(dl / af_name),
        "sha256_zip": sha256_file(dl / zip_name),
        "bytes_nan": (dl / nan_name).stat().st_size, "bytes_allfinite": (dl / af_name).stat().st_size,
        "bytes_zip": (dl / zip_name).stat().st_size,
        "emitted_px": build["n_dots"], "format_verified": validators_ok,
        "status": status, "note": note, "note_file": note_file,
        "submission_name": f"GEMSDOE28-h39-5-extrap-swap35-{cid}",
        "run_card": "evidence/s18_h39_5_run_card.json",
        "holdout_evidence": "evidence/s18_h39_5_losfo_gate.json",
        "holdout_preregistration": "knowledge/52_preregistration_H39-5_extrapolated.md",
        "holdout_seeds": "310-314", "verdict": verdict,
    }
    manifest_path = dl / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["s18_h39_5_candidate"] = slot
    manifest["generated_utc"] = "2026-10-25T00:00:00Z"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    champion_row = build["uniqueness_table"].get("champion_e5eb6e7e_GEMSDOE32")
    failures = [f"frozen LOSFO gate component {k} failed" for k in failed_gates]
    if not build["uniqueness_pass_strict"]:
        failures.append(
            f"uniqueness: {worst.get('frac_our_dots_within3px', 0):.1%} of final dots within "
            f"3px of {worst.get('raster')} (limit 70%) and/or surface Spearman > 0.90")
    if not validators_ok:
        failures.append("validator hard checks failed (see evidence/s18_candidate_build.json)")

    card = {
        "session": "S18 (2026-10-25), branch arena/f149a461-gemsdoe28, lane H39-5 (knowledge/52)",
        "hypothesis": ("A dipping buried fault's surface projection lies up-dip of its "
                       "potential-field edge; placing dots at migration-extrapolated "
                       "positions (shallow HG ridge minus its 0->2 km migration vector, "
                       "TMI + gravity) earns credit on concealed faults the scarp-based "
                       "catalogue omits, at the champion's budget and hygiene."),
        "mechanism": ("Upward continuation exp(-|k|h) at 0/1/2 km; HG ridges via shared "
                      "ridge_nms; v = nearest 2 km ridge px - shallow px; extrapolated "
                      "position = shallow - v; score = 3-level coherence * clip(HG0/p99,0,1); "
                      "frozen 32-band detector emission, weakest 35% swapped 1-for-1 for "
                      "eligible (|v|>=2px, d_cat>2px) extrapolated px at >=2.8px spacing."),
        "named_nonfault_mimic": ("Dipping lithologic contact / mafic dike swarm (migrates "
                                 "identically, zero Quaternary slip); GeoDAWN flight-line striping."),
        "holdout_dti": {
            "label": "HOLDOUT-DTI (not an organizer score)",
            "evaluator": gate["evaluator"], "seeds": "310-314 (20 paired cells)",
            "n_withheld_positives_pooled_cell_truth_px": gate["n_withheld_positives_pooled_cell_truth_px"],
            "d0_pooled_dti": gate["d0_pooled"]["dti"], "d1_pooled_dti": gate["d1_pooled"]["dti"],
            "pooled_delta_dti": gate["pooled_delta_dti"],
            "mean_paired_delta_dti": gate["mean_paired_delta_dti"],
            "ci95_paired_bootstrap": gate["ci95_paired_bootstrap"],
            "cells_positive": f"{gate['cells_positive']}/20",
            "per_seed_mean_delta": gate["per_seed_mean_delta"],
            "per_fold_mean_delta": gate["per_fold_mean_delta"],
            "credit_per_dot_d0": gate["d0_pooled"]["credit_per_dot"],
            "credit_per_dot_d1": gate["d1_pooled"]["credit_per_dot"],
            "swap_totals": gate["swap_totals"],
            "gate": gate["gate"], "gate_passed": gate["gate_passed"],
            "canary_single_feature_aucs": {
                k: v["canary_max_auc_1mauc"]
                for k, v in canary["single_feature_auc_vs_hidden_systems"].items()},
            "canary_pass": canary["canary_pass"],
        },
        "organizer_confirmed_scores": ("none (no submission-page receipt exists for any file "
                                        "here; 0.2778/0.2750/0.2708/0.2600 are OWNER-REPORTED)"),
        "correlation_overlap_vs_registry": {
            "preplacement_lane_surface_worst_abs_spearman_vs_registry_binary":
                canary["preplacement_uniqueness"]["worst_abs_spearman"],
            "preplacement_pool_worst_overlap":
                canary["preplacement_uniqueness"]["worst_pool_overlap"],
            "spearman_lane_surface_vs_detector_prob_sample400k":
                build["spearman_lane_surface_vs_detector_prob_sample400k"],
            "worst_registry_raster_by_final_dot_overlap": worst,
            "vs_scored_champion_e5eb6e7e": champion_row,
            "uniqueness_pass_strict": build["uniqueness_pass_strict"],
            "full_table_final_dots": build["uniqueness_table"],
            "full_table_preplacement": canary["preplacement_uniqueness"]["table"],
            "thresholds": {"rank_corr_max": 0.90, "dots_within3px_max": 0.70},
        },
        "raster_sha256": {"nan": slot["sha256_nan"], "allfinite": slot["sha256_allfinite"],
                          "zip": slot["sha256_zip"]},
        "validator": {
            "nan_hard_pass": build["validator_nan"]["hard_checks_passed"],
            "allfinite_hard_pass": build["validator_allfinite"]["hard_checks_passed"],
            "nan_hard_failures": build["validator_nan"]["hard_failures"],
            "allfinite_hard_failures": build["validator_allfinite"]["hard_failures"],
            "value_set_inside": build["validator_allfinite"]["value_set_inside"],
            "no_nan_inside_footprint": build["validator_nan"]["checks"]["inside_footprint_all_finite"]["pass"],
            "values_in_0_1": build["validator_nan"]["checks"]["inside_footprint_in_0_1"]["pass"],
            "crs_shape_transform_match": build["validator_nan"]["checks"]["grid_matches_template"]["pass"],
            "single_band": build["validator_nan"]["checks"]["single_band_float32"]["pass"],
        },
        "submission_name": slot["submission_name"], "note": note, "note_chars": len(note),
        "candidate_files": {"nan": nan_name, "allfinite": af_name, "zip": zip_name},
        "experiments_run": 3, "verdict": verdict,
        "submission_ready": False, "slot_selected": False,
        "selector_promotion": bool(promote),
        "failures": failures,
        "scope": ("Promotion is to a separate selector step within the weekly cap; this "
                  "session spent no slot and uploaded nothing. A negative verdict means "
                  "the TIF is inspection-only. HOLDOUT-DTI is a local proxy, never an "
                  "organizer score; no projection is written as a score."),
    }
    (ROOT / "evidence/s18_h39_5_run_card.json").write_text(json.dumps(card, indent=2) + "\n")
    (ROOT / "docs/data/run_card_s18_2026-10-25.json").write_text(json.dumps(card, indent=2) + "\n")
    print(json.dumps({"verdict": verdict, "note": note, "note_chars": len(note),
                      "submission_name": slot["submission_name"], "failures": failures}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
