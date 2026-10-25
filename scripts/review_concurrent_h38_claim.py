#!/usr/bin/env python3
"""Read-only review of the concurrent H38 'new/unique/promote' claim, not an experiment.

No model, dot placement, raster emission or historical score rerun. One verified
registry duplicate is enough to stop; this never perturbs predictions to evade it.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
from scripts.audit_existing_submissions import read_values  # noqa: E402

from gems27 import grid  # noqa: E402
from gems27.shared_template import load_shared  # noqa: E402
from gems27.submission import sha256_file  # noqa: E402

BASE = "22cd17590460d8e76e180957f31f75d85dd3ec17"
CLAIM = "docs/data/run_card_gems28-h38-1-hf-euler-r30-r1_2026-10-25.json"


def main() -> int:
    claim = json.loads((ROOT / CLAIM).read_text())
    relative = claim["raster"]["file"]
    candidate = ROOT / relative
    if not candidate.resolve().is_relative_to(ROOT):
        raise ValueError("Claim raster escapes the repository")
    original = subprocess.check_output(["git", "show", BASE + ":" + relative], cwd=ROOT)
    before_sha = hashlib.sha256(original).hexdigest()
    template = ROOT / "data/sample_submission.tif"
    manifest = json.loads((ROOT / "docs/downloads/manifest.json").read_text())
    reference = ROOT / "docs/downloads" / manifest["primary"]["allfinite"]
    footprint = grid.load_footprint(template)
    values, base_values = (read_values(path, footprint, template) for path in (candidate, reference))
    shared = load_shared()
    correlation = shared.novelty.correlation(values[footprint], base_values[footprint])
    overlap = shared.novelty.dot_overlap((values > 0) & footprint, (base_values > 0) & footprint)
    duplicate = shared.novelty.is_duplicate(correlation, overlap["candidate_within_3px_of_reference"])
    legacy_path = "evidence/holdout_compare_gems28-h38-1_vs_h36-1_2026-10-25.json"
    legacy = json.loads((ROOT / legacy_path).read_text())
    report = {
        "label": "BYTE / NOVELTY / CLAIM AUDIT, not HOLDOUT-DTI",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "source_claim": CLAIM, "source_claim_sha256": sha256_file(ROOT / CLAIM),
        "source_claim_verdict": claim["submission"]["verdict"],
        "candidate": relative, "candidate_sha256": sha256_file(candidate),
        "session_base_commit": BASE, "candidate_sha256_at_session_base": before_sha,
        "already_present_byte_identically_at_session_base": before_sha == sha256_file(candidate),
        "reference": str(reference.relative_to(ROOT)), "reference_sha256": sha256_file(reference),
        "raw_final_raster_spearman": correlation,
        "raw_rank_scope": "Every footprint cell of the final binary rasters; NOT a reconstructed pre-placement continuous surface",
        "dot_overlap": overlap, "duplicate": duplicate,
        "original_preplacement_surface": "unavailable; no check backdated or reconstructed",
        "claimed_check_report": legacy_path, "claimed_check_report_sha256": sha256_file(ROOT / legacy_path),
        "claimed_check_own_verdict": legacy["verdict"],
        "protocol_comparable_holdout": False,
        "protocol_reason": "The inspected legacy runner scores fixed full-catalogue TIFFs with make_split; it does not retrain per fold or reconstruct visible-only catalogue features and is not the shared buffered evaluator.",
        "verdict": "negative", "promotion_eligible": False, "submission_ready": False,
        "experiments_run": 0, "new_raster_generated": False, "slot_selected": False,
        "reasons": [
            "Claimed new TIFF already exists byte-identically at this session's base commit",
            "Final-raster rank and all-dot overlap exceed the registry stop thresholds against an existing reference",
            "The claim's promote verdict contradicts its own linked check's negative verdict",
            "Legacy fixed-TIFF diagnostic is not the strict buffered, retrained promotion baseline",
        ],
        "historical_evidence_policy": "Original claimed run card and result retained unchanged for provenance; this later review supersedes readiness, not the recorded historical measurements.",
    }
    if (not report["already_present_byte_identically_at_session_base"] or not duplicate
            or report["claimed_check_own_verdict"] != "negative"):
        raise ValueError("Unexpected claim state: do not publish an assumed negative explanation")
    target = ROOT / "evidence/current_concurrent_claim_review.json"
    target.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
