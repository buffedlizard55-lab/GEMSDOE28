"""Regression checks for the frozen S22-DPMR negative result and public disposition."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_s22_scientific_gates_are_bound_and_negative() -> None:
    exp1 = load("evidence/s22_dpmr_exp1_surface.json")
    exp2 = load("evidence/s22_dpmr_exp2_holdout.json")
    exp3 = load("evidence/s22_dpmr_exp3_emission.json")
    card = load("evidence/s22_dpmr_run_card.json")

    assert exp1["passed"] is True and exp1["canary"]["passed"] is True
    assert exp1["preplacement"]["max_abs_rank_correlation"] <= 0.90
    assert exp1["preplacement"]["max_dot_overlap_within_3px"] <= 0.70
    for feature in exp1["canary"]["features"].values():
        assert max(feature["pooled_auc"], 1.0 - feature["pooled_auc"]) <= 0.90

    candidate = exp2["candidate"]
    assert candidate["evaluator_version"] == "gems-segment-pooled-v1"
    assert candidate["n_withheld_positive_pixels"] == 60_988
    assert candidate["ci95"]["interval"][0] <= candidate["dti"] <= candidate["ci95"]["interval"][1]
    assert exp2["paired_vs_b0"]["delta_dti"] < 0
    assert exp2["paired_vs_b0"]["ci95"][1] < 0
    assert exp2["paired_vs_b0"]["folds_improved"] == "0/4"
    assert exp2["gate_passed"] is False and exp2["verdict"] == "negative"

    assert exp3["registry"]["passed"] is True and exp3["format_pass"] is True
    assert exp3["registry"]["max_abs_rank_correlation"] <= 0.90
    assert exp3["registry"]["max_dot_overlap_within_3px"] <= 0.70
    assert card["verdict"] == "negative"
    assert card["submission_ready"] is False and card["slot_selected"] is False
    assert card["slots_spent"] == 0 and card["experiments_run"] == 3


def test_s22_exact_file_hash_manifest_and_validator() -> None:
    card = load("evidence/s22_dpmr_run_card.json")
    manifest = load("docs/downloads/manifest.json")
    item = manifest["s22_candidate"]
    raster = ROOT / "docs/downloads" / card["files"]["allfinite"]

    assert raster.is_file()
    assert sha256(raster) == card["raster_sha256"] == item["sha256_allfinite"]
    assert raster.stat().st_size == item["bytes_allfinite"] == 826_126
    assert item["emitted_px"] == card["files"]["positive_pixels"] == 37_654
    assert item["content_id"] in item["submission_name"]
    assert item["verdict"] == "negative" and item["submission_ready"] is False
    assert manifest["current_run"]["run_id"] == "S22-DPMR"

    validator = card["validator"]
    assert validator["raster_sha256"] == sha256(raster)
    for check in (
        "no_nan_inside",
        "range_0_1",
        "crs_match",
        "shape_match",
        "transform_match",
        "single_band",
        "whole_array_all_finite",
    ):
        assert validator[check] is True
    assert validator["catalogue_overlap_pixels"] == 0


def test_s22_run_card_projection_and_public_copy_are_unambiguous() -> None:
    card = load("evidence/s22_dpmr_run_card.json")
    assert card == load("docs/data/run_card_s22.json")
    assert card == load("docs/data/current_run_card_2026-10-26.json")
    assert card["score_estimate"]["label"] == "MODEL PROJECTION — NOT A SCORE"
    assert "USER-REPORTED / UNVERIFIED" in card["score_estimate"]["anchor"]
    assert card["ok_to_download"] is True and card["ok_to_submit"] is False
    assert 0 < len(card["note"]) <= 140

    for path in ("docs/index.html", "docs/executive-summary.html", "docs/session22-result.html"):
        text = (ROOT / path).read_text(encoding="utf-8")
        assert "gems28-s22-dpmr-20261026-ecf809d55d2a-allfinite.tif" in text
        assert "DO NOT SUBMIT" in text
        assert "OK TO SUBMIT TO PORTAL: NO" in text or "NO FILE APPROVED" in text
        assert "MODEL PROJECTION" in text and "NOT A SCORE" in text


def test_s22_archive_audit_covers_every_tiff() -> None:
    audit = load("evidence/s22_download_audit.json")
    assert audit["status"] == "PASS" and audit["failures"] == []
    assert audit["check_count"] == 723
    s22_checks = [row for row in audit["checks"] if row["check"].startswith("s22_candidate_")]
    assert len(s22_checks) == 30 and all(row["pass"] for row in s22_checks)
    coverage = next(row for row in audit["checks"] if row["check"] == "all_tifs_registered_for_audit")
    assert coverage["pass"] is True
