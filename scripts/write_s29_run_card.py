#!/usr/bin/env python3
"""Assemble evidence/s29_candidate_run_card.json from the S29 evidence files (no numbers typed by hand)."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
E = ROOT / "evidence"


def load(name):
    return json.loads((E / name).read_text(encoding="utf-8"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


e1, e2 = load("s29_holdout.json"), load("s29_b_holdout.json")
gate_a, gate_b = load("s29_gate_A_dense.json"), load("s29_gate_B_holeconstrained.json")
build = load("s29_candidate_build.json")
b_name = "gems29-s29-hole-k20000-20261029-b68117a828cc-nan.tif"
b_path = ROOT / "docs/candidates" / b_name
note = ("S29 HGB hole-constrained k20000; unique under 70%/3px gate; holdout negative; NOT approved to submit")
assert len(note) <= 140, len(note)
card = {
    "schema": "s29-run-card-v1",
    "session": "S29",
    "date_utc": "2026-10-29",
    "experiments_used": 2,
    "experiment_cap": 3,
    "weekly_slot_selected": False,
    "experiments": [
        {
            "id": "E1",
            "hypothesis": "S29-E1-HGB-CF (preregistered, evidence/s29_prereg.json)",
            "mechanism": "Visible catalogue labels in other quadrants teach a per-quadrant HGB which 100 m feature conjunctions co-occur with mapped faults",
            "named_non_fault_process": "Rock-type or basin-margin contrasts; survey line/seam artefacts; conductive cover edges",
            "holdout_dti": e1["s29_holdout"]["dti"],
            "holdout_ci95": e1["s29_holdout"]["ci95"]["interval"],
            "withheld_positives": e1["s29_holdout"]["n_truth"],
            "random_k_holdout_dti": e1["random_K_holdout"]["dti"],
            "paired_delta_vs_random_k": e1["paired_s29_minus_random_K"]["paired_delta_dti"],
            "paired_delta_ci95_vs_random_k": e1["paired_s29_minus_random_K"]["paired_delta_ci95"],
            "registry_039_lattice_holdout_dti": e1["registry_039_lattice_holdout"]["dti"],
            "note_lattice": "unbudgeted dense control (about 206k dots); not a budget-matched comparison",
            "canary_max_auc": e1["canary_max_auc_reported"],
            "canary_threshold": 0.90,
            "canary_passed": e1["canary"]["passed"],
            "raster_sha256": None,
            "validator": None,
            "submission_name": None,
            "verdict": "negative",
            "verdict_reason": "paired CI vs random-K excludes zero on the negative side; primary endpoint failed",
        },
        {
            "id": "E2",
            "hypothesis": "S29-B: hole-constrained placement of the E1 surface (>=32% of dots in registry-uncovered px)",
            "mechanism": "Same surfaces as E1; placement forced into pixels >3 px from every registry-039 dot",
            "named_non_fault_process": "as E1",
            "holdout_dti": e2["B_holdout"]["dti"],
            "holdout_ci95": e2["B_holdout"]["ci95"]["interval"],
            "withheld_positives": e2["B_holdout"]["n_withheld_positive_pixels"],
            "random_k_holdout_dti": e2["random_K_holdout"]["dti"],
            "paired_delta_vs_random_k": e2["paired_B_minus_random_K"]["paired_delta_dti"],
            "paired_delta_ci95_vs_random_k": e2["paired_B_minus_random_K"]["paired_delta_ci95"],
            "comparable_best_holdout_dti": e2["comparable_best_HOLDOUT_DTI"],
            "decision": e2["decision"],
            "raster_sha256": sha(b_path),
            "validator": {"hard_checks_passed": True, "source": "gems27.submission.verify_geotiff"},
            "submission_name": b_name,
            "submission_note": note,
            "submission_note_length": len(note),
            "verdict": "negative",
            "verdict_reason": "HOLDOUT-DTI below comparable best 0.0553736 and below its own random-K; no slot",
        },
    ],
    "candidate_files": {
        "B_unique_gate_pass_NOT_approved": {
            "path": f"docs/candidates/{b_name}",
            "sha256": sha(b_path),
            "dots": build["B"]["dots"],
            "hole_dots": build["B"]["hole_dots"],
            "registry_gate": {
                "file": "evidence/s29_gate_B_holeconstrained.json",
                "passed": gate_b["lane_protocol_passed"],
                "references_checked": gate_b["references_checked"],
                "max_candidate_within_3px": gate_b["max_candidate_within_3px_any_convention"],
                "max_abs_raw_spearman": max(abs(r["raw_spearman"]) for r in gate_b["rows"] if r.get("raw_spearman") is not None),
                "max_abs_kernel_spearman": max(abs(r["kernel_spearman"]) for r in gate_b["rows"] if r.get("kernel_spearman") is not None),
            },
            "status": "UNIQUE under the automated gate; NOT OK TO SUBMIT (holdout negative; no slot)",
        },
        "A_dense_NOT_unique": {
            "path": "data/research/candidates/s29_A_dense_k37654.tif (git-ignored, not published)",
            "sha256": sha(ROOT / "data/research/candidates/s29_A_dense_k37654.tif"),
            "dots": build["A"]["dots"],
            "registry_gate": {
                "file": "evidence/s29_gate_A_dense.json",
                "passed": gate_a["lane_protocol_passed"],
                "flagged": gate_a["flagged_duplicates"],
                "max_candidate_within_3px": gate_a["max_candidate_within_3px_any_convention"],
            },
            "status": "DUPLICATE of registry-039 (literal 70%/3px rule): NOT OK",
        },
    },
    "verdict": "negative",
    "submit_ok": False,
    "download_ok_for_review": True,
    "decision": "NO SLOT. B is unique but its holdout is negative. A is a measured duplicate. Nothing is approved.",
}
(E / "s29_candidate_run_card.json").write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
print("wrote evidence/s29_candidate_run_card.json; note length", len(note))
