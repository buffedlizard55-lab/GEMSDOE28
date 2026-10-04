import hashlib
import json

from scripts import audit_holdout_seed_range as seed_audit


def _digest(record):
    return hashlib.sha256(
        json.dumps(record, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def test_seed_values_finds_numeric_lists_strings_and_ranges():
    values = seed_audit.seed_values({
        "seeds": [260, "265-267"],
        "nested": {"seed_range": "268–269"},
        "seed_start": 270,
        "seed_end": 271,
        "not_a_seed": 266,
    })
    assert {row["seed"] for row in values} == {260, 265, 266, 267, 268, 269, 270, 271}


def test_audit_is_local_exact_range_and_excludes_claim_and_output(tmp_path, monkeypatch):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    monkeypatch.setattr(seed_audit, "ROOT", tmp_path)
    monkeypatch.setattr(seed_audit, "EVIDENCE", evidence)
    monkeypatch.setattr(seed_audit, "git_text", lambda *args: "arena/test" if args[0] == "branch" else "abc123")

    claim_path = evidence / "claim.json"
    claim_path.write_text(json.dumps({"status": "RESERVED", "seeds": [265, 266, 267, 268, 269]}))
    output_path = evidence / "seed-audit.json"
    (evidence / "noncolliding.json").write_text(json.dumps({"seeds": [260, 261, 262, 263, 264]}))
    report = seed_audit.audit(265, 269, claim_path, output_path)
    assert report["status"] == "PASS_LOCAL_SCAN"
    assert report["target_range"] == [265, 266, 267, 268, 269]
    assert report["local_seed_references"] == []
    assert report["claim"]["valid_for_exact_range"] is True
    assert "claim.json" not in report["scanned_evidence_sha256"]
    assert "seed-audit.json" not in report["scanned_evidence_sha256"]
    assert report["scope"].startswith("local evidence/*.json only")
    recorded = report.pop("sha256")
    assert recorded == _digest(report)


def test_audit_fails_on_range_collision_and_unreadable_json(tmp_path, monkeypatch):
    evidence = tmp_path / "evidence"
    evidence.mkdir()
    monkeypatch.setattr(seed_audit, "ROOT", tmp_path)
    monkeypatch.setattr(seed_audit, "EVIDENCE", evidence)
    monkeypatch.setattr(seed_audit, "git_text", lambda *args: "arena/test" if args[0] == "branch" else "abc123")
    claim_path = evidence / "claim.json"
    claim_path.write_text(json.dumps({"status": "RESERVED", "seeds": [265, 266, 267, 268, 269]}))
    (evidence / "collision.json").write_text(json.dumps({"seed_range": "264-266"}))
    (evidence / "unreadable.json").write_text("{")

    report = seed_audit.audit(265, 269, claim_path, evidence / "report.json")
    assert report["status"] == "FAIL"
    assert report["collisions_excluding_exact_claim"][0]["file"] == "collision.json"
    assert report["unreadable_json"] == ["unreadable.json"]
