"""S22C evidence binding (renamed from S22 at merge): run card, manifest, shipped bytes and site pages must agree."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
STEM = "gems28-s22-ctxhgb-20261026-e23dabcec6e2"


def _card():
    return json.loads((ROOT / "evidence/s22c_run_card.json").read_text())


def test_s22_run_card_gate_and_identity():
    card = _card()
    assert card["verdict"] == "promote"  # frozen S22 gate (knowledge/62) passed
    assert card["submission_ready"] is False and card["slot_selected"] is False
    assert card["experiments_run"] == 3 and card["experiment_cap"] == 3
    h = card["holdout"]
    assert h["label"] == "HOLDOUT-DTI" and h["seeds"] == [360, 361, 362]
    assert h["dti"] > h["baseline_dti"] > h["control_dti"]
    assert 0 < h["paired_gain_ci95"][0] < h["paired_gain"] < h["paired_gain_ci95"][1]
    assert h["paired_gain_vs_control"] > 0
    assert h["buffered"] is False  # quadrant protocol, honestly flagged for promotion_gate
    assert len(card["note"]) == card["note_chars"] <= 140
    assert "DO NOT SUBMIT" not in card["note"]  # note is descriptive; lock lives in submission_ready
    assert max(abs(a - 0.5) + 0.5 for a in card["feature_canaries"].values()) <= 0.90
    champ = card["registry"]["vs_GEMSDOE32_champion"]
    assert champ["frac_our_dots_within3px"] <= 0.70
    assert abs(champ["spearman_surface_vs_registry_sample200k"]) <= 0.90
    assert card["registry"]["complete"] is False  # snapshot-bounded, never over-claimed
    v = card["validator"]
    assert v["no_nan_whole_array"] and v["range_0_1"] and v["value_set_inside"] == [0.0, 1.0]
    assert v["crs_match"] and v["shape_match"] and v["transform_match"] and v["single_band"]


def test_s22_shipped_bytes_match_card_and_manifest():
    card = _card()
    tif = DOCS / "downloads" / f"{STEM}-allfinite.tif"
    assert tif.is_file()
    assert hashlib.sha256(tif.read_bytes()).hexdigest() == card["raster_sha256"]
    assert (DOCS / "downloads" / f"{STEM}-nan.tif").is_file()
    assert (DOCS / "downloads" / f"{STEM}-nan.zip").is_file()
    manifest = json.loads((DOCS / "downloads/manifest.json").read_text())
    slot = manifest["s22c_candidate"]
    assert slot["content_id"] == "e23dabcec6e2"
    assert slot["sha256_allfinite"] == card["raster_sha256"]
    assert slot["emitted_px"] == card["n_dots"] == 37_654
    assert slot["note"] == card["note"]
    assert slot["submission_ready"] is False and slot["slot_selected"] is False
    note_file = DOCS / "downloads" / slot["note_file"]
    assert note_file.read_text(encoding="utf-8").strip() == slot["note"]


def test_s22_holdout_evidence_cells():
    hold = json.loads((ROOT / "evidence/s22c_holdout.json").read_text())
    assert hold["label"] == "HOLDOUT-DTI" and hold["n_cells"] == 12
    assert all(c["lane"]["dti"] > c["dotted_b2"]["dti"] for c in hold["cells"])
    assert all(c["lane"]["dti"] > c["control"]["dti"] for c in hold["cells"])
    assert hold["gate"] == {"canary_pass": True, "delta_vs_base_gt0": True,
                            "delta_vs_base_ci_lower_gt0": True, "delta_vs_control_gt0": True}
    fore = json.loads((ROOT / "evidence/s22c_forensic.json").read_text())
    lin = fore["champion_lineage"]
    assert lin["symdiff_recomputed_champion_vs_fetched_GEMSDOE32_bytes"] == 0
    f25 = fore["files"]["GEMSDOE25_best_dotted_d2.8_reported_0.2600"]["dotset_sha256"]
    f30 = fore["files"]["GEMSDOE30_best_d28_poisson_reported_0.2600"]["dotset_sha256"]
    assert f25 == f30  # identical dot-sets under two site names


def test_s22_site_pages_rendered_and_fail_closed_on_slot():
    card = _card()
    assert json.loads((DOCS / "data/run_card_s22c.json").read_text()) == card
    page = (DOCS / "session22c-result.html").read_text()
    assert f"downloads/{STEM}-allfinite.tif" in page
    assert 'data-submission-ready="false"' in page and "NO SLOT SPENT" in page
    assert "HOLDOUT-DTI" in page and "MODEL" in page and "0.4437" in page
    for page_name in ("index.html", "executive-summary.html"):
        text = (DOCS / page_name).read_text()
        assert "session22c-result.html" in text
        assert f"downloads/{STEM}-allfinite.tif" in text
        assert "e23dabcec6e2" in text
    root_index = (ROOT / "index.html").read_text()
    assert f"docs/downloads/{STEM}-allfinite.tif" in root_index
