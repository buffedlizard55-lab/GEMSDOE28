#!/usr/bin/env python3
"""Publish this blocked review's truthful run card; never synthesize missing evidence."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27.promotion import promotion_gate  # noqa: E402


def main() -> int:
    evidence_files = ["registry/current_session.json", "registry/protocol_assets.json",
                      "evidence/current_archive_format_audit.json", "evidence/current_review.json",
                      "evidence/current_concurrent_claim_review.json", "docs/downloads/manifest.json",
                      "scripts/review_concurrent_h38_claim.py",
                      "evidence/current_input_audit.json", "evidence/current_preflight.json",
                      "evidence/priority_repository_audit.json", "evidence/current_submission_audit.json",
                      "evidence/shared_template_contract.json", "evidence/official_reference_audit.json",
                      "src/gems27/promotion.py", "src/gems27/submission.py", "src/gems27/shared_template.py",
                      "scripts/audit_priority_repositories.py", "scripts/audit_existing_submissions.py",
                      "scripts/audit_shared_template.py", "scripts/check_run_preflight.py",
                      "scripts/record_current_review.py"]
    evidence_hashes = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in evidence_files}
    session = json.loads((ROOT / "registry/current_session.json").read_text())
    if session["lane"] is not None or session["experiments_run"] != 0:
        raise SystemExit("This recorder is only for the blocked no-experiment review, not a scientific runner")
    archive = json.loads((ROOT / "evidence/current_submission_audit.json").read_text())
    concurrent = json.loads((ROOT / "evidence/current_concurrent_claim_review.json").read_text())
    card = {
        "schema_version": 2, "session_id": session["session_id"], "lane": None,
        "hypothesis": "No assigned method. G28-A51-A is a ranked proposal only, not an executed hypothesis.",
        "mechanism": "Not run: no new geological model, dot placement, or submission TIFF.",
        "non_fault_mimic": "Intrusive cross-cutting contacts or survey-registration seams could mimic the top proposal.",
        "holdout": {"label": "HOLDOUT-DTI", "status": "NOT RUN", "evaluator_version": None,
                    "withheld_positives": None, "dti": None, "ci95": None,
                    "paired_gain_ci95": None, "baseline_sha256": None,
                    "available_shared_evaluator_version": "gems-segment-pooled-v1",
                    "scope": "Shared software tested; no geological result, CI or hidden-score forecast exists for this run."},
        "feature_canaries": {},
        "registry": {"complete": False, "surface": None, "dots": None,
                     "scope": "No new candidate. Archived primary comparisons are separate, not backdated pre-placement evidence."},
        "raster_sha256": None,
        "validator": {"status": "NOT RUN: no new raster", "no_nan_inside": None,
                      "range_0_1": None, "crs_match": None, "shape_match": None,
                      "transform_match": None, "single_band": None},
        "submission_name": None,
        "note": "Blocked: no assigned lane or comparable strict baseline; archive primary is a duplicate. No new TIFF or slot.",
        "experiments_run": 0, "new_raster_generated": False,
        "organizer_confirmed_scores": [],
        "archive_audit": {"role": "Existing reference only, DO NOT SUBMIT; not a new deliverable TIFF",
                          "file": archive["archived_file"], "raster_sha256": archive["raster_sha256"],
                          "format_valid": archive["format_validator"]["hard_checks_passed"],
                          "final_dot_unique": archive["final_dots"]["passed"],
                          "max_within_3px_fraction": archive["final_dots"]["max_dot_overlap"],
                          "max_abs_rank_correlation": archive["final_dots"]["max_abs_rank_correlation"],
                          "new_surface_check": "NOT RUN"},
        "concurrent_archive_claim_audit": {
            "role": "H38-1 historical reference, not this run's candidate",
            "byte_identical_to_session_base": concurrent["already_present_byte_identically_at_session_base"],
            "raw_final_raster_spearman": concurrent["raw_final_raster_spearman"],
            "within_3px_fraction": concurrent["dot_overlap"]["candidate_within_3px_of_reference"],
            "verdict": "negative", "new_surface_check": "NOT RUN"},
        "evidence_sha256": evidence_hashes,
    }
    card.update(promotion_gate(card))
    for relative in ("evidence/current_run_card.json", "docs/data/run_card_2026-10-25.json"):
        (ROOT / relative).write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"verdict": card["verdict"], "submission_ready": card["submission_ready"],
                      "experiments_run": 0, "note_chars": len(card["note"]),
                      "files": ["evidence/current_run_card.json", "docs/data/run_card_2026-10-25.json"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
