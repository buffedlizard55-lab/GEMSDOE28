"""Audit frozen evidence without model fits, new seeds, or external requests."""
import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
from scripts.evaluate_s18_holdout import confidence_intervals, pooled

from gems27 import promotion

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


def test_s18_sources_are_bound_and_no_spent_runner_was_reformatted():
    for path, digest in load("evidence/s18_source_hashes.json")["files"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest, path
    started = load("evidence/s18_holdout.started.json")
    result = load("evidence/s18_holdout.json")
    assert started["evaluator_hashes"] == result["evaluator_hashes"]
    assert started["baseline_sha256"] == result["baseline_sha256"]
    stage = load("evidence/s18_stage_result.json")
    assert stage["preregistration_sha256"] == hashlib.sha256(
        (ROOT / "knowledge/52_s18_preregistration.md").read_bytes()).hexdigest()


def test_s18_exact_file_and_negative_gate_are_not_confused():
    card = load("evidence/s18_mxtp_run_card.json")
    assert card == load("docs/data/run_card_s18.json") == load("docs/data/run_card_2026-10-25.json")
    path = ROOT / "docs" / card["download"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == card["raster_sha256"]
    assert card["validator_full"]["hard_checks_passed"] is True
    assert card["validator"]["no_nan_anywhere"] and card["validator"]["range_0_1"]
    assert card["verdict"] == "negative" and card["submission_ready"] is False
    assert card["slot_selected"] is False and card["organizer_receipt"] is None
    limits = card["strict_protocol_limitations"]
    assert all(limits[key] is False for key in (
        "upstream_template_api_equivalence_established", "exclusive_external_lane_assignment_confirmed",
        "global_parallel_registry_complete", "certified_global_best_baseline"))
    provenance = load("evidence/s18_writer_provenance.json")
    assert provenance["artifact_sha256"] == card["raster_sha256"]
    assert provenance["post_merge_validator_sha256"] == hashlib.sha256(
        (ROOT / "src/gems27/submission.py").read_bytes()).hexdigest()
    assert len(card["note"]) <= 140 and "DO NOT SUBMIT" in card["note"]
    gate = promotion.promotion_gate(card)
    assert gate["failures"] == ["no positive paired gain CI over frozen current best"]
    assert gate["verdict"] == "negative"


def test_s18_every_declared_member_compared_before_and_after_placement():
    card = load("evidence/s18_mxtp_run_card.json")
    snapshot = load("evidence/s18_registry_snapshot.json")
    registry = card["registry"]
    identities = {x["sha256"] for x in snapshot["entries"] if x["status"] == "included"}
    assert len(identities) == 166 and snapshot["complete_within_declared_scope"]
    assert registry["manifest_sha256"] == hashlib.sha256(
        (ROOT / "evidence/s18_registry_snapshot.json").read_bytes()).hexdigest()
    assert len(registry["members"]) == len(identities)
    for phase in ("surface", "dots"):
        rows = registry[phase]
        assert len(rows) == len(identities)
        assert {x["raster_sha256"] for x in rows} == identities
        assert all(x["spearman"] <= 0.90 and x["within_3px_fraction"] <= 0.70 for x in rows)
        assert not any(x["duplicate"] for x in rows)
    assert registry["global_parallel_registry_verified"] is False


def test_s18_pooled_results_and_block_intervals_reproduce_without_training():
    result = load("evidence/s18_holdout.json")
    cells = result["cells"]
    for arm in ("candidate", "baseline"):
        assert pooled([r[arm] for r in cells]) == result[f"{arm}_pooled"]
    assert confidence_intervals(cells) == result["ci"]
    assert len(cells) == 20 and result["seeds"] == list(range(310, 315))
    assert result["withheld_positives"] == 76869
    assert result["unique_withheld_positive_pixels"] == 45155
    assert all(c["candidate_on_visible"] == c["baseline_on_visible"] == 0 for c in cells)
    assert all(c["minimum_hidden_to_visible_px"] > 6 for c in cells)
    assert result["ci"]["paired_gain_ci95"][1] < 0 and result["gate_passed"] is False


def test_s18_bootstrap_identical_arms_has_zero_paired_gain():
    cells = []
    for fold_id in range(4):
        for seed in range(3):
            r = {"tp": float(3 + fold_id), "fp": 9.0, "n_truth": 25, "dots": 12}
            cells.append({"fold_id": fold_id, "seed": seed, "candidate": r, "baseline": r.copy()})
    ci = confidence_intervals(cells)
    assert ci["paired_gain_ci95"] == [0.0, 0.0]


def test_s18_latest_download_is_visible_before_historical_downloads():
    card = load("evidence/s18_mxtp_run_card.json")
    for page in ("index.html", "executive-summary.html", "session18-result.html"):
        html = (ROOT / "docs" / page).read_text()
        assert html.index(card["download"]) < html.index("Prior-run context")
        assert "Download NEW unique research TIFF — DO NOT SUBMIT" in html
        assert "0.02038" in html and "76,869" in html and "45,155" in html
        assert 'data/run_card_2026-10-25.json' in html
        assert "unique submission generated this session" not in html
        assert "Whether to submit is your decision" not in html
    summary = (ROOT / "docs/executive-summary.html").read_text()
    assert "three submissions per week" in summary and "four weekly slots" not in summary


@pytest.mark.requires_rasters
def test_s18_raster_independent_reopen_matches_current_report():
    import rasterio

    from gems27 import grid, paths, submission

    card = load("evidence/s18_mxtp_run_card.json")
    path = ROOT / "docs" / card["download"]
    audit = submission.verify_geotiff(path, paths.TEMPLATE)
    assert audit == card["validator_full"]
    with rasterio.open(path) as src:
        a = src.read(1)
    assert np.isfinite(a).all() and np.isin(a, [0, 1]).all()
    assert np.count_nonzero(a) == card["dot_count"] == 11082
    assert not np.any(a[grid.load_labels(paths.LABELS)])
