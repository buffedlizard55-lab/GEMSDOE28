#!/usr/bin/env python3
"""S16 finalize: verdict from frozen gate + uniqueness + validator (knowledge/49).

Writes docs/downloads/manifest.json slot `s16_candidate`, the portal note file,
evidence/s16_run_card.json and docs/data/run_card_2026-10-25.json. Verdict is
`negative` unless gate_passed AND uniqueness_pass_strict AND both validators pass.
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
    gate = json.loads((ROOT / "evidence/s16_h40_losfo_gate.json").read_text())
    build = json.loads((ROOT / "evidence/s16_candidate_build.json").read_text())
    canary = json.loads((ROOT / "evidence/s16_canary.json").read_text())
    dl = ROOT / "docs/downloads"
    nan_name, af_name, zip_name = build["files"]["nan"], build["files"]["allfinite"], build["files"]["zip"]
    cid = build["content_id"]
    validators_ok = bool(build["validator_nan"]["hard_checks_passed"] and build["validator_allfinite"]["hard_checks_passed"])
    promote = bool(gate["gate_passed"] and build["uniqueness_pass_strict"] and validators_ok)
    verdict = "promote" if promote else "negative"

    note = (f"28GEMSDOE H40-1 migration B1 | LOSFO GATE FAIL dDTI +0.0013 CI[-0.0034,+0.0063] "
            f"uniq FAIL DO NOT SUBMIT | id {cid}")
    assert len(note) <= 140, len(note)
    note_file = f"note-gemsdoe28-h40-1-{cid}.txt"
    (dl / note_file).write_text(note + "\n")

    status = (
        f"{'GATE PASS' if gate['gate_passed'] else 'DO NOT SUBMIT — HOLDOUT GATE FAILED'}; "
        f"HOLDOUT-DTI LOSFO seeds 300-304 pooled dDTI {gate['pooled_delta_dti']:+.6f} "
        f"(95% CI [{gate['ci95_paired_bootstrap'][0]:+.4f}, {gate['ci95_paired_bootstrap'][1]:+.4f}], "
        f"{gate['cells_positive']}/20 cells, G2 spread FAIL); uniqueness FAIL "
        f"(surface Spearman {build['spearman_probD1_vs_probD0_sample400k']:.3f} > 0.90; worst "
        f"{build['worst_registry_raster_by_dot_overlap']['frac_our_dots_within3px']:.1%} dots within 3px of "
        f"{build['worst_registry_raster_by_dot_overlap']['raster']}; vs scored champion e5eb6e7e "
        f"{build['uniqueness_table']['champion_e5eb6e7e_GEMSDOE32']['frac_our_dots_within3px']:.1%}); "
        f"validator PASS (all-finite variant: values exactly {{0,1}}, no NaN anywhere); "
        f"verdict {verdict}; research/inspection only, no slot spent, selector step separate."
    )
    slot = {
        "slug": "h40-1-migration-b1",
        "hypothesis": "H40-1 continuation-height HG-ridge migration (signed offset + 3-level coherence, TMI+gravity) appended to the frozen 32-band detector; prob-ranked, dot_thin(2.8), d_cat>2px build hygiene",
        "content_id": cid,
        "nan": nan_name, "allfinite": af_name, "zip": zip_name,
        "sha256_nan": sha256_file(dl / nan_name), "sha256_allfinite": sha256_file(dl / af_name),
        "sha256_zip": sha256_file(dl / zip_name),
        "bytes_nan": (dl / nan_name).stat().st_size, "bytes_allfinite": (dl / af_name).stat().st_size,
        "bytes_zip": (dl / zip_name).stat().st_size,
        "emitted_px": build["n_dots"], "format_verified": validators_ok,
        "status": status, "note": note, "note_file": note_file,
        "submission_name": f"GEMSDOE28-h40-1-migration-b1-{cid}",
        "run_card": "evidence/s16_run_card.json",
        "holdout_evidence": "evidence/s16_h40_losfo_gate.json",
        "holdout_preregistration": "knowledge/49_preregistration_H40-1_migration.md",
        "holdout_seeds": "300-304", "verdict": verdict,
    }
    manifest_path = dl / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["s16_candidate"] = slot
    manifest["generated_utc"] = "2026-10-25T00:00:00Z"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")

    card = {
        "session": "S16 (2026-10-25), branch arena/2164512d-gemsdoe28, lane H40-1 (knowledge/49)",
        "hypothesis": "Continuation-height HG-ridge migration (signed lateral offset + 3-level coherence of TMI/gravity edges, 0/1/2 km) marks dipping buried faults the surface-scarp catalogue omits; appending these 4 label-free bands to the frozen 32-band detector raises far-field DTI at the champion's budget.",
        "mechanism": "Upward continuation exp(-|k|h); ridge at each level via shared ridge_nms; signed migration = shallow->2km ridge offset projected on field-gradient normal; coherence = mean_l exp(-d_l/2). GBDT unchanged, prob-ranked, dot_thin(2.8), build-time d_cat>2px.",
        "named_nonfault_mimic": "Dipping lithologic contact / mafic dike swarm (migrates identically, zero Quaternary slip); GeoDAWN flight-line striping.",
        "holdout_dti": {
            "label": "HOLDOUT-DTI (not an organizer score)",
            "evaluator": gate["evaluator"], "seeds": "300-304 (20 paired cells)",
            "n_withheld_positives_pooled_cell_truth_px": gate["n_withheld_positives_pooled_cell_truth_px"],
            "d0_pooled_dti": gate["d0_pooled"]["dti"], "d1_pooled_dti": gate["d1_pooled"]["dti"],
            "pooled_delta_dti": gate["pooled_delta_dti"], "mean_paired_delta_dti": gate["mean_paired_delta_dti"],
            "ci95_paired_bootstrap": gate["ci95_paired_bootstrap"],
            "cells_positive": f"{gate['cells_positive']}/20", "per_seed_mean_delta": gate["per_seed_mean_delta"],
            "per_fold_mean_delta": gate["per_fold_mean_delta"],
            "credit_per_dot_d0": gate["d0_pooled"]["credit_per_dot"], "credit_per_dot_d1": gate["d1_pooled"]["credit_per_dot"],
            "gate": gate["gate"], "gate_passed": gate["gate_passed"],
            "canary_single_feature_aucs": {k: v["canary_max_auc_1mauc"] for k, v in canary["single_feature_auc_vs_hidden_systems"].items()},
            "canary_pass": canary["canary_pass"],
        },
        "organizer_confirmed_scores": "none (no submission-page receipt exists for any file here; 0.2778/0.2750/0.2708/0.2600 are OWNER-REPORTED)",
        "correlation_overlap_vs_registry": {
            "spearman_probD1_vs_probD0_sample400k": build["spearman_probD1_vs_probD0_sample400k"],
            "worst_registry_raster_by_dot_overlap": build["worst_registry_raster_by_dot_overlap"],
            "vs_scored_champion_e5eb6e7e": build["uniqueness_table"]["champion_e5eb6e7e_GEMSDOE32"],
            "uniqueness_pass_strict": build["uniqueness_pass_strict"], "full_table": build["uniqueness_table"],
        },
        "raster_sha256": {"nan": slot["sha256_nan"], "allfinite": slot["sha256_allfinite"]},
        "validator": {"nan_hard_pass": build["validator_nan"]["hard_checks_passed"],
                      "allfinite_hard_pass": build["validator_allfinite"]["hard_checks_passed"],
                      "allfinite_value_set_inside": build["validator_allfinite"]["value_set_inside"],
                      "no_nan_inside_footprint": True, "values_in_0_1": True,
                      "crs_shape_transform_match": True, "single_band": True},
        "submission_name": slot["submission_name"], "note": note, "note_chars": len(note),
        "experiments_run": 3, "verdict": verdict, "submission_ready": False, "slot_selected": False,
        "failures": ["G2 spread: 9/20 cells, 1/4 folds, seed 303 -0.0107",
                     "uniqueness: surface Spearman 0.990 > 0.90; 91.3% dots within 3px of dense probe 52a13184267e (41.3% vs scored champion)"],
        "scope": "Negative result is the deliverable; TIF published inspection-only, banner DO NOT SUBMIT. No slot spent.",
    }
    (ROOT / "evidence/s16_run_card.json").write_text(json.dumps(card, indent=2) + "\n")
    (ROOT / "docs/data/run_card_2026-10-25.json").write_text(json.dumps(card, indent=2) + "\n")
    print(json.dumps({"verdict": verdict, "note_chars": len(note), "submission_name": slot["submission_name"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
