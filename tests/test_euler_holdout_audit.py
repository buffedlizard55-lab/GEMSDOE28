import hashlib
import json

import numpy as np
import pytest
from affine import Affine
from scripts import audit_euler_seed_reuse as seed_audit
from scripts import run_euler_cluster_holdout as runner


def _sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _make_seed_audit(tmp_path, monkeypatch, prior):
    root = tmp_path
    evidence = root / "evidence"
    evidence.mkdir()
    protocol = root / "protocol.md"
    protocol.write_text("frozen protocol\n")
    scripts = root / "scripts"
    scripts.mkdir()
    audit_script = scripts / "audit_euler_seed_reuse.py"
    audit_script.write_text("# test seed-audit implementation\n")
    prior_path = evidence / "prior.json"
    prior_path.write_text(json.dumps(prior))
    output_path = evidence / "seed_audit.json"
    record = {
        "status": "PASS",
        "planned_ranges": {
            "screen": list(range(160, 170)),
            "confirmation": list(range(170, 180)),
        },
        "range_status": {"screen": "UNUSED", "confirmation": "UNUSED"},
        "previously_used_holdout_seeds": list(range(100, 160)),
        "evidence_json_sha256_scanned": {prior_path.name: _sha(prior_path)},
        "audit_script_sha256": _sha(audit_script),
        "protocol": {"sha256": _sha(protocol), "last_modifying_commit": "frozen-commit"},
    }
    record["sha256"] = None
    record["sha256"] = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    output_path.write_text(json.dumps(record))
    monkeypatch.setattr(runner, "ROOT", root)
    monkeypatch.setattr(runner, "SEED_AUDIT", output_path)
    monkeypatch.setattr(runner, "PROTOCOL_PATH", protocol)
    monkeypatch.setattr(runner, "_protocol_commit", lambda: "frozen-commit")
    return evidence, output_path


def test_cluster_csv_uses_unix_line_endings(tmp_path):
    path = tmp_path / "clusters.csv"
    cluster = {
        "cluster_id": 0, "row": 2.0, "col": 1.0, "median_depth_m": 300.0,
        "depth_mad_m": 10.0, "depth_min_m": 280.0, "depth_max_m": 320.0,
        "n_solutions": 4, "median_depth_se_m": 20.0,
    }
    runner._write_cluster_csv([cluster], Affine.identity(), path)
    assert b"\\r" not in path.read_bytes()


def test_single_use_claim_is_exclusive_and_persisted(tmp_path):
    claim_path = tmp_path / "evidence" / "screen.started.json"
    record = {"stage": "screen", "seeds": list(range(160, 170))}
    digest = runner._write_single_use_claim(claim_path, record)
    assert json.loads(claim_path.read_text()) == record
    assert digest == _sha(claim_path)
    with pytest.raises(SystemExit, match="cannot be rerun"):
        runner._write_single_use_claim(claim_path, record)


def test_metadata_fingerprint_uses_null_sha_slot():
    meta = {"schema": 1, "value": [1, 2, 3], "sha256": None}
    meta["sha256"] = runner._metadata_fingerprint(meta)
    assert runner._metadata_fingerprint(meta) == meta["sha256"]
    meta["value"].append(4)
    assert runner._metadata_fingerprint(meta) != meta["sha256"]


def test_seed_scanners_recurse_and_ignore_boolean_values():
    nested = {"seeds": [160, 161], "cells": [{"seed": 170}, {"more": {"used_seeds": [179, True]}}]}
    assert runner._seed_values(nested) == {160, 161, 170, 179}
    assert seed_audit.find_seeds(nested) == {160, 161, 170, 179}
    assert seed_audit.find_seeds([{"seed": 100}, {"seeds": [159]}]) == {100, 159}


def test_seed_range_audit_accepts_only_frozen_unused_screen(tmp_path, monkeypatch):
    _make_seed_audit(tmp_path, monkeypatch, {"seeds": [100, 101]})
    result = runner._assert_seed_range_unused(list(range(160, 170)), tmp_path / "evidence/screen.json")
    assert result["status"] == "PASS"


def test_seed_range_audit_rejects_collision_even_if_seed_ledger_is_stale(tmp_path, monkeypatch):
    evidence, output = _make_seed_audit(tmp_path, monkeypatch, {"seeds": [100, 101]})
    collision_path = evidence / "unexpected.json"
    collision_path.write_text(json.dumps({"seeds": [160]}))
    audit = json.loads(output.read_text())
    audit["evidence_json_sha256_scanned"][collision_path.name] = _sha(collision_path)
    audit["sha256"] = None
    audit["sha256"] = hashlib.sha256(json.dumps(audit, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    output.write_text(json.dumps(audit))
    with pytest.raises(SystemExit, match="collision"):
        runner._assert_seed_range_unused(list(range(160, 170)), evidence / "screen.json")


def test_seed_range_audit_rejects_unscanned_evidence_json(tmp_path, monkeypatch):
    evidence, _ = _make_seed_audit(tmp_path, monkeypatch, {"seeds": [100, 101]})
    (evidence / "new_record.json").write_text(json.dumps({"no_seed": True}))
    with pytest.raises(SystemExit, match="set of local evidence JSON"):
        runner._assert_seed_range_unused(list(range(160, 170)), evidence / "screen.json")


def test_seed_range_audit_rejects_changed_scanned_evidence(tmp_path, monkeypatch):
    evidence, _ = _make_seed_audit(tmp_path, monkeypatch, {"seeds": [100, 101]})
    (evidence / "prior.json").write_text(json.dumps({"seeds": [100, 101, 102]}))
    with pytest.raises(SystemExit, match="stale"):
        runner._assert_seed_range_unused(list(range(160, 170)), evidence / "screen.json")


def test_minimum_spacing_helper_uses_euclidean_pixel_distance():
    points = np.zeros((5, 5), dtype=bool)
    points[0, 0] = True
    points[1, 1] = True
    assert runner._minimum_spacing_px(points) == pytest.approx(np.sqrt(2.0))
    points[1, 1] = False
    assert runner._minimum_spacing_px(points) is None


def test_passing_screen_revalidation_recomputes_complete_paired_gate(tmp_path, monkeypatch):
    evidence_dir = tmp_path / "evidence"
    evidence_dir.mkdir()
    screen_path = evidence_dir / "h31_1_euler_screen.json"
    claim_path = evidence_dir / "h31_1_euler_screen.started.json"
    monkeypatch.setattr(runner, "ROOT", tmp_path)
    monkeypatch.setattr(runner, "SCREEN", screen_path)
    cells = [
        {
            "seed": seed,
            "fold": fold,
            "n_truth": 10,
            "minimum_spacing_px": {"control": 2.0, "candidate": 2.0},
            "checks": {
                "mask_contained_in_active_fold": True,
                "no_known_catalogue_overlap": True,
                "minimum_spacing_at_least_1_5_px": True,
                "nonempty_hidden_truth": True,
            },
            "control": {"dti": 0.10, "dots": 100},
            "candidate": {"dti": 0.102, "dots": 100},
        }
        for seed in range(160, 170)
        for fold in runner.holdout.FOLD_NAMES
    ]
    summary = runner._stage_summary(cells)
    report = {
        "stage": "screen",
        "status": "screen pass; confirmation may proceed",
        "protocol_commit": "frozen-protocol-commit",
        "protocol_sha256": "frozen-protocol-sha256",
        "seed_reuse_audit_sha256": "seed-audit-sha256",
        "input_hashes": {"labels": "labels-sha256"},
        "feature_hashes": {"euler": "features-sha256"},
        "code_hashes": {"runner": "runner-sha256"},
        "runtime_versions": {"python": "test"},
        "current_best_same_run_control": True,
        "feature_sufficiency": {"passed": True},
        "seeds": list(range(160, 170)),
        "cells": cells,
        "summary": summary,
        "gate": {
            "mean_gain_at_least_0_001": True,
            "positive_fold_means_at_least_3_of_4": True,
            "positive_seed_means_at_least_8_of_10": True,
            "all_data_and_leakage_checks_pass": True,
            "passed": True,
        },
        "probabilities_valid": True,
        "known_catalogue_overlap_pixels": 0,
        "grid_mask_violations": 0,
        "minimum_spacing_failures": 0,
        "empty_truth_cells": 0,
        "data_integrity_checks": {
            "probabilities_finite_in_0_1": True,
            "candidate_and_control_inside_active_fold": True,
            "zero_known_catalogue_overlap": True,
            "minimum_spacing_at_least_1_5_px": True,
            "nonempty_hidden_truth_every_cell": True,
        },
        "submission_raster_written": False,
        "drivendata_access": False,
    }
    claim = {
        "record_type": "single-use holdout seed claim; existence consumes this range even if process is interrupted",
        "stage": "screen",
        "seeds": list(range(160, 170)),
        "protocol_commit": report["protocol_commit"],
        "protocol_sha256": report["protocol_sha256"],
        "seed_reuse_audit_sha256": report["seed_reuse_audit_sha256"],
        "input_hashes": report["input_hashes"],
        "feature_hashes": report["feature_hashes"],
        "code_hashes": report["code_hashes"],
        "runtime_versions": report["runtime_versions"],
    }
    claim_path.write_text(json.dumps(claim))
    report["single_use_seed_claim"] = {
        "path": claim_path.relative_to(tmp_path).as_posix(),
        "sha256": _sha(claim_path),
    }
    report["sha256"] = None
    report["sha256"] = runner._metadata_fingerprint(report)
    assert runner._validate_passing_screen(report)
    report["cells"][0]["minimum_spacing_px"]["candidate"] = 1.0
    report["cells"][0]["checks"]["minimum_spacing_at_least_1_5_px"] = False
    report["sha256"] = None
    report["sha256"] = runner._metadata_fingerprint(report)
    assert not runner._validate_passing_screen(report)
    report["cells"][0]["minimum_spacing_px"]["candidate"] = 2.0
    report["cells"][0]["checks"]["minimum_spacing_at_least_1_5_px"] = True
    report["sha256"] = None
    report["sha256"] = runner._metadata_fingerprint(report)
    assert runner._validate_passing_screen(report)
    claim["seeds"] = [160]
    claim_path.write_text(json.dumps(claim))
    assert not runner._validate_passing_screen(report)
    claim["seeds"] = list(range(160, 170))
    claim_path.write_text(json.dumps(claim))
    report["single_use_seed_claim"]["sha256"] = _sha(claim_path)
    report["cells"].pop()
    report["sha256"] = None
    report["sha256"] = runner._metadata_fingerprint(report)
    assert not runner._validate_passing_screen(report)
