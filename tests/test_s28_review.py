"""S28 evidence coherence; these tests do not certify geological performance."""
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(path):
    return json.loads((ROOT / path).read_text())


def module(name):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


def test_s28_card_binds_evidence_and_does_not_claim_experiment():
    card = load("evidence/s28_run_card.json")
    assert card["branch"] == "arena/cc67fd6a-gemsdoe28"
    assert card["verdict"] == "negative"
    assert not card["ok_to_submit"] and not card["slot_selected"]
    assert not card["new_raster_generated"] and card["experiments_run"] == 0
    assert card["raster_sha256"] is None
    assert card["holdout"]["dti"] is None and card["holdout"]["ci95"] is None
    assert card["estimated_leaderboard_score"] is None
    assert card["organizer_confirmed_scores"] == []
    assert len(card["note"]) <= 140
    for path, digest in card["evidence_sha256"].items():
        assert hashlib.sha256((ROOT / path).read_bytes()).hexdigest() == digest


def test_nine_leaders_checked_by_shared_comparator():
    evidence = load("evidence/s28_priority_novelty.json")
    assert len(evidence["leaders"]) == 9
    for leader in evidence["leaders"]:
        check = leader["final_dots"]
        assert check["registry_unique_rasters"] == 8
        assert len(check["rows"]) == 8
        assert all(row["registry_id"] != leader["site"] for row in check["rows"])
        assert check["passed"] is False
        assert any(row["duplicate"] for row in check["rows"])
        assert check["max_dot_overlap"] > 0.7
        assert leader["estimated_leaderboard_score"] is None
        assert leader["score_label"] == "USER-REPORTED / UNVERIFIED"
        assert leader["ok_to_submit"] is False
    assert evidence["forensic"]["champion_equals_solo_minus_catalogue_distance_le_2px"]
    assert evidence["forensic"]["removed_solo_to_champion"] == 2545
    assert evidence["forensic"]["added_solo_to_champion"] == 0
    assert not evidence["forensic"]["causal_score_improvement_proven"]


def test_select_leaders_handles_misleading_allfinite_metadata():
    mod = module("audit_s28_priority_novelty")
    inventory = load("evidence/s28_priority_repository_audit.json")
    leaders = mod.select_leaders(inventory)
    assert len(leaders) == 9
    assert all(l["raster"]["path"].endswith(("-nan.tif", "-nanoutside.tif")) for l in leaders)
    # The historical allfinite filename can carry a NaN tag; select the named
    # NaN variant explicitly rather than trust a metadata-derived variant label.
    repo = next(r for r in inventory["repositories"] if r["repository"].endswith("/GEMSDOE31"))
    repo["priority_rasters"] += [dict(leaders[5]["raster"])]
    with pytest.raises(ValueError, match="exactly one"):
        mod.select_leaders(inventory)


def test_s28_build_idempotent_and_visible_on_entrypoints():
    mod = module("build_s28_review")
    base = "<html><main><section>Earlier record</section></main></html>"
    once = mod.inject(base, mod.render_panel())
    twice = mod.inject(once, mod.render_panel())
    assert once == twice
    with pytest.raises(ValueError, match="Missing main"):
        mod.inject("<body></body>", mod.render_panel())
    for path in ("docs/index.html", "docs/executive-summary.html", "index.html", "executive-summary.html"):
        text = (ROOT / path).read_text()
        assert text.count('id="s28-current-decision"') == 1
        assert text.index('id="s28-current-decision"') < text.index('id="s27-current-decision"')
    summary = (ROOT / "docs/s28-review.html").read_text()
    assert "Estimated leaderboard score" in summary
    assert "Exactly how submission will work once approved" in summary
    assert (ROOT / "README.md").read_text().startswith("# S28 · 2026-10-29 UTC")
    assert load("docs/data/s28_run_card.json") == load("evidence/s28_run_card.json")
