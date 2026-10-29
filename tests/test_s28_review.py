import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_s28_snapshot_is_negative_and_dated():
    card = json.loads((ROOT / "evidence/s28_run_card.json").read_text())
    preflight = json.loads((ROOT / card["preflight"]).read_text())
    assert card["submission_ready"] is False and card["slot_selected"] is False
    assert card["raster_sha256"] is None and card["holdout"]["dti"] is None
    assert preflight["status"] == "BLOCKED" and preflight["shared_template"]["passed"]
    assert len(preflight["failures"]) == 5


def test_s28_panel_is_reproducible_and_fails_closed(tmp_path):
    from scripts.build_s27_review import inject_s28

    page = tmp_path / "index.html"
    page.write_text("<main></main>")
    section = '<section id="s28-checkout-decision">NO FILE</section>'
    inject_s28(page, section)
    inject_s28(page, section)
    assert page.read_text().count('id="s28-checkout-decision"') == 1
