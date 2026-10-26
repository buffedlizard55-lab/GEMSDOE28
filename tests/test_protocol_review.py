"""Regression checks for the current no-slot review and read-only shared tools."""
from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest
from scripts import check_run_preflight
from scripts.site_current import current_notice

from gems27.shared_template import load_shared, verify_assets

ROOT = Path(__file__).resolve().parents[1]


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value) + "\n")
    return {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


@pytest.fixture()
def shared_fixture(tmp_path):
    sources = {"__init__": "", "validator": "VALUE = 1\n", "metric": "VALUE = 7\n",
               "holdout": "from .metric import VALUE\n", "novelty": "VALUE = 3\n",
               "submission": "VALUE = 2\n"}
    entries = []
    for name, text in sources.items():
        destination = Path("shared_template/src/gems") / (name + ".py")
        path = tmp_path / "data" / destination
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        entries.append({"id": name, "dest": str(destination), "bytes": len(text.encode()),
                        "sha256": hashlib.sha256(text.encode()).hexdigest()})
    write_json(tmp_path / "registry/protocol_assets.json", {"source": "synthetic fixture only", "files": entries})
    return tmp_path


def test_read_only_shared_import_verifies_before_reusing_module(shared_fixture):
    root = shared_fixture
    first = load_shared(root)
    assert first.holdout.VALUE == 7
    assert load_shared(root) is first
    path = root / "data/shared_template/src/gems/metric.py"
    path.write_text("VALUE = 9000\n")
    assert not verify_assets(root)["passed"]
    with pytest.raises(ValueError, match="integrity"):
        load_shared(root)  # Cannot silently keep a previously imported good module.


def test_missing_asset_fails_verification(shared_fixture):
    (shared_fixture / "data/shared_template/src/gems/novelty.py").unlink()
    assert not verify_assets(shared_fixture)["passed"]


@pytest.mark.parametrize("destination", ["../outside.py", "/outside.py"])
def test_shared_destination_must_stay_inside_data(shared_fixture, destination):
    pin = shared_fixture / "registry/protocol_assets.json"
    value = json.loads(pin.read_text())
    value["files"][0]["dest"] = destination
    pin.write_text(json.dumps(value))
    with pytest.raises(ValueError, match="escapes"):
        verify_assets(shared_fixture)


def test_shared_symlink_must_not_escape_data(shared_fixture):
    target = shared_fixture / "data/shared_template/src/gems/metric.py"
    target.unlink()
    outside = shared_fixture / "outside.py"
    outside.write_text("VALUE = 7\n")
    target.symlink_to(outside)
    with pytest.raises(ValueError, match="escapes"):
        verify_assets(shared_fixture)


def valid_config(root):
    array_path = root / "data/prepared/features.npy"
    array_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(array_path, np.zeros((3, 32), np.float32))
    write_json(root / "data/prepared/features.json",
               {"sha256": hashlib.sha256(array_path.read_bytes()).hexdigest(),
                "names": [f"feature_{i}" for i in range(32)], "shape": [3, 32]})
    raster = root / "data/reference.tif"
    raster.write_bytes(b"reference fixture identity, not a real raster")
    registry = write_json(root / "registry/parallel.json",
                          {"complete": True, "members": [{"path": str(raster),
                           "sha256": hashlib.sha256(raster.read_bytes()).hexdigest()}]})
    baseline = write_json(root / "evidence/baseline.json",
                          {"label": "HOLDOUT-DTI", "evaluator_version": "gems-segment-pooled-v1",
                           "retrained_per_fold": True, "visible_only_catalogue_features": True,
                           "pooled": True, "whole_segments_buffered": True,
                           "dti": 0.1, "ci95": [0.05, 0.2], "withheld_positives": 10})
    return {"lane": "synthetic prerequisite fixture", "lane_assignment_source": "fixture only",
            "cached_features": "data/prepared/features.npy", "cached_features_metadata": "data/prepared/features.json",
            "required_parallel_registry": registry, "frozen_protocol_comparable_best": baseline,
            "started_at_utc": (datetime.now(timezone.utc) - timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "experiments_run": 0, "experiment_cap": 3, "time_cap_seconds": 7200}


def test_preflight_is_not_a_submission_gate(shared_fixture, monkeypatch):
    monkeypatch.setattr(check_run_preflight, "FOOTPRINT_PX", 3)
    result = check_run_preflight.preflight(valid_config(shared_fixture), root=shared_fixture)
    assert result["experiment_allowed"], result["failures"]
    assert result["submission_ready"] is False and result["slot_selected"] is False
    assert "scope" in result  # Prerequisites, NOT authenticity of a TIFF or result.


@pytest.mark.parametrize("field,value", [("lane", None), ("lane", " "),
    ("lane_assignment_source", {}), ("required_parallel_registry", "registry/parallel.json"),
    ("frozen_protocol_comparable_best", {}), ("experiments_run", 3),
    ("experiments_run", True), ("experiment_cap", 4), ("time_cap_seconds", 7201),
    ("time_cap_seconds", True), ("started_at_utc", None),
    ("started_at_utc", "2000-01-01T00:00:00Z"), ("started_at_utc", "2999-01-01T00:00:00Z"),
    ("started_at_utc", "2026-10-25T00:00:00"), ("slot_selected", True)])
def test_preflight_missing_or_bad_prerequisites_stop(shared_fixture, monkeypatch, field, value):
    monkeypatch.setattr(check_run_preflight, "FOOTPRINT_PX", 3)
    config = valid_config(shared_fixture)
    config[field] = value
    result = check_run_preflight.preflight(config, root=shared_fixture)
    assert not result["experiment_allowed"]


def test_preflight_rejects_corrupt_cache_and_referenced_evidence(shared_fixture, monkeypatch):
    monkeypatch.setattr(check_run_preflight, "FOOTPRINT_PX", 3)
    config = valid_config(shared_fixture)
    (shared_fixture / "data/prepared/features.npy").write_bytes(b"broken")
    result = check_run_preflight.preflight(config, root=shared_fixture)
    assert not result["experiment_allowed"]
    config = valid_config(shared_fixture)
    (shared_fixture / "evidence/baseline.json").write_text('{}')
    assert not check_run_preflight.preflight(config, root=shared_fixture)["experiment_allowed"]


def test_preflight_rejects_weak_protocol_and_duplicate_registry_members(shared_fixture, monkeypatch):
    monkeypatch.setattr(check_run_preflight, "FOOTPRINT_PX", 3)
    config = valid_config(shared_fixture)
    path = shared_fixture / "evidence/baseline.json"
    value = json.loads(path.read_text())
    value["retrained_per_fold"] = False
    config["frozen_protocol_comparable_best"] = write_json(path, value)
    assert not check_run_preflight.preflight(config, root=shared_fixture)["experiment_allowed"]
    config = valid_config(shared_fixture)
    path = shared_fixture / "registry/parallel.json"
    value = json.loads(path.read_text())
    value["members"] *= 2
    config["required_parallel_registry"] = write_json(path, value)
    assert not check_run_preflight.preflight(config, root=shared_fixture)["experiment_allowed"]


def test_notice_ignores_forged_submission_ready_flag():
    notice = current_notice({"submission_ready": True, "verdict": "promote"})
    assert 'data-submission-ready="false"' in notice
    assert "Submission download locked" in notice
    assert 'disabled aria-disabled="true"' in notice
    assert ".tif" not in notice.lower()


def test_prior_a51_review_card_is_preserved_and_session22_card_is_current():
    # The G28-A51 review card is a historical, hash-bound record. Its old session
    # pointer is intentionally superseded by the archive-review-only Session 22.
    card = json.loads((ROOT / "evidence/current_run_card.json").read_text())
    assert card["session_id"] == "G28-A51-20261025"
    assert card["lane"] is None and card["raster_sha256"] is None
    assert card["holdout"]["dti"] is None and card["holdout"]["ci95"] is None
    assert card["experiments_run"] == 0 and card["new_raster_generated"] is False
    assert card["submission_ready"] is False and card["verdict"] == "negative"
    assert len(card["note"]) <= 140
    for path, expected in card["evidence_sha256"].items():
        if path == "registry/current_session.json":
            assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected
            continue
        snapshots = {
            "docs/downloads/manifest.json": "evidence/pr39_manifest_snapshot.json",
            "scripts/check_run_preflight.py": "evidence/snapshots/pr39_check_run_preflight.py",
        }
        observed = ROOT / snapshots.get(path, path)
        assert hashlib.sha256(observed.read_bytes()).hexdigest() == expected, path
    # The older MXTP experiment and the new archive-only review have separate cards.
    assert json.loads((ROOT / "docs/data/run_card_2026-10-25.json").read_text()) == json.loads(
        (ROOT / "evidence/s18_mxtp_run_card.json").read_text())
    session22 = json.loads((ROOT / "evidence/session22_review_run_card.json").read_text())
    assert session22["session"] == "G28-S22-ARCHIVE-REVIEW-20261026"
    assert session22["experiments_run"] == 0 and session22["new_tiff_generated"] is False


def test_priority_audit_is_not_called_a_complete_parallel_registry():
    audit = json.loads((ROOT / "evidence/priority_repository_audit.json").read_text())
    assert len(audit["repositories"]) == 9
    assert audit["priority_inventory_retrieved"] is True
    assert audit["external_parallel_registry_complete"] is False
    assert audit["organizer_confirmed_scores"] == []
    for repo in audit["repositories"]:
        assert len(repo["commit"]) == 40
        assert all(row["blob_verified"] for row in repo["priority_rasters"])


def test_current_pages_cannot_recommend_historical_primary():
    for name in ("index.html", "executive-summary.html", "submission-review.html"):
        text = (ROOT / "docs" / name).read_text()
        assert "Submission download locked" in text
        assert "If you submit anything" not in text
        assert "Human submission checklist" not in text
        assert "OK TO DOWNLOAD AND SUBMIT" not in text
    assert "SUPERSEDED · DO NOT SUBMIT THESE FILES" in (ROOT / "docs/archive.html").read_text()
    review = json.loads((ROOT / "evidence/current_review.json").read_text())
    assert len(review["hypotheses"]) == 4
    assert all("Proposed only" in h["status"] for h in review["hypotheses"])


def test_notice_remains_locked_even_for_a_complete_evidence_schema():
    # A complete schema alone never authenticates evidence or chooses a slot.
    from tests.test_promotion import complete_card

    card = deepcopy(complete_card())
    card["submission_ready"] = True
    notice = current_notice(card)
    assert "Evidence schema eligible; no slot selected" in notice
    assert 'data-submission-ready="false"' in notice


def test_unlisted_shared_source_must_not_be_executed(shared_fixture):
    pin = shared_fixture / "registry/protocol_assets.json"
    value = json.loads(pin.read_text())
    value["files"] = [row for row in value["files"] if row["id"] != "metric"]
    pin.write_text(json.dumps(value))
    assert not verify_assets(shared_fixture)["passed"]
    with pytest.raises(ValueError, match="integrity"):
        load_shared(shared_fixture)


@pytest.mark.parametrize("manifest", [[], {}, {"source": "test", "files": [None]}])
def test_malformed_shared_manifest_is_a_validation_error(shared_fixture, manifest):
    pin = shared_fixture / "registry/protocol_assets.json"
    pin.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="Malformed"):
        verify_assets(shared_fixture)


def test_verified_source_not_stale_bytecode_is_executed(shared_fixture):
    import py_compile

    path = shared_fixture / "data/shared_template/src/gems/metric.py"
    path.write_text("VALUE = 9\n")  # same byte length as the verified original
    py_compile.compile(str(path), doraise=True, invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
    path.write_text("VALUE = 7\n")
    # CPython's mtime/size cache header can accept that stale pyc, but our loader
    # must compile the hash-verified source bytes directly.
    assert load_shared(shared_fixture).metric.VALUE == 7


def test_empty_cache_is_a_negative_preflight_not_an_eof_exception(shared_fixture, monkeypatch):
    monkeypatch.setattr(check_run_preflight, "FOOTPRINT_PX", 3)
    config = valid_config(shared_fixture)
    (shared_fixture / "data/prepared/features.npy").write_bytes(b"")
    result = check_run_preflight.preflight(config, root=shared_fixture)
    assert result["experiment_allowed"] is False
    assert any("Cached feature stack" in failure for failure in result["failures"])


def test_missing_priority_artifact_does_not_claim_inventory_complete(tmp_path, monkeypatch):
    from scripts import audit_priority_repositories as audit

    template = tmp_path / "reference.txt"
    template.write_text("mock identity; no raster operation in this test")
    def missing_one(name, directory, template):
        return {"commit": "a" * 40, "priority_rasters": [],
                "missing_requested_identities": ["missing"] if name == "GEMSDOE24" else []}
    monkeypatch.setattr(audit, "inspect_repository", missing_one)
    out = tmp_path / "audit.json"
    assert audit.main(["--template", str(template), "--out", str(out)]) == 1
    report = json.loads(out.read_text())
    assert report["priority_inventory_retrieved"] is False
    assert report["errors"][0]["missing"] == ["missing"]


def test_concurrent_h38_claim_is_rejected_without_rewriting_its_original_card():
    report = json.loads((ROOT / "evidence/current_concurrent_claim_review.json").read_text())
    assert report["already_present_byte_identically_at_session_base"] is True
    assert report["candidate_sha256"] == report["candidate_sha256_at_session_base"]
    assert report["candidate_sha256"] == hashlib.sha256((ROOT / report["candidate"]).read_bytes()).hexdigest()
    assert abs(report["raw_final_raster_spearman"]) > 0.90
    assert report["dot_overlap"]["candidate_within_3px_of_reference"] > 0.70
    assert report["source_claim_verdict"] == "promote"  # Retained historical contradiction.
    assert report["claimed_check_own_verdict"] == "negative"
    assert report["protocol_comparable_holdout"] is False
    assert report["verdict"] == "negative" and report["promotion_eligible"] is False
    assert report["experiments_run"] == 0 and report["new_raster_generated"] is False
    for path_key, hash_key in (("source_claim", "source_claim_sha256"),
                               ("claimed_check_report", "claimed_check_report_sha256")):
        assert hashlib.sha256((ROOT / report[path_key]).read_bytes()).hexdigest() == report[hash_key]
    assert "Concurrent H38-1 claim: rejected" in (ROOT / "docs/submission-review.html").read_text()


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -float("inf")])
def test_preflight_rejects_hash_pinned_nonfinite_cache(shared_fixture, monkeypatch, bad):
    root = shared_fixture
    config = valid_config(root)
    monkeypatch.setattr(check_run_preflight, "FOOTPRINT_PX", 3)
    path = root / config["cached_features"]
    array = np.zeros((3, 32), np.float32)
    array[-1, -1] = bad
    np.save(path, array)
    meta_path = root / config["cached_features_metadata"]
    meta = json.loads(meta_path.read_text())
    meta["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    write_json(meta_path, meta)
    result = check_run_preflight.preflight(config, root=root)
    assert result["experiment_allowed"] is False
    assert "Cached feature stack contains NaN or infinity" in result["failures"]


@pytest.mark.parametrize("text", ['{"lane":"a","lane":"b"}', '{"x":1e999}'])
def test_preflight_cli_rejects_ambiguous_json(tmp_path, capsys, text):
    path = tmp_path / "session.json"
    path.write_text(text)
    assert check_run_preflight.main(["--config", str(path)]) == 2
    assert json.loads(capsys.readouterr().out)["experiment_allowed"] is False
