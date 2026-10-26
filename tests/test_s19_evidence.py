from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(path: str):
    return json.loads((ROOT / path).read_text())


def test_s19_card_is_complete_negative_and_note_bounded() -> None:
    card = load("evidence/s19_ascp_run_card.json")
    assert card["session"] == "S19-ASCP"
    assert card["experiments_run"] == 3
    assert card["verdict"] == "negative"
    assert card["submission_ready"] is False and card["slot_selected"] is False
    assert len(card["note"]) <= 140 and "DO NOT SUBMIT" in card["note"]
    assert card["holdout"]["evaluator_version"] == "gems-segment-pooled-v1"
    assert card["holdout"]["withheld_positives"] == 60988
    assert card["holdout"]["paired_gain_ci95"][1] < 0
    assert card["registry"]["max_abs_surface_spearman"] <= 0.90
    assert card["registry"]["max_final_overlap_3px"] <= 0.70
    assert all(card["validator"].values())


def test_s19_exact_overlap_supersedes_conservative_preliminary_screen() -> None:
    exact = load("evidence/s19_exact_registry_overlap.json")
    card = load("evidence/s19_ascp_run_card.json")
    assert exact["passed"] is True and exact["members"] == card["registry"]["members"]
    assert card["registry"]["max_surface_support_overlap_3px"] == exact["max_surface_support"][
        "surface_support_within_euclidean_3px_fraction"
    ]
    assert card["registry"]["max_final_overlap_3px"] == exact["max_final_overlap"][
        "final_dots_within_euclidean_3px_fraction"
    ]
    assert "exact Euclidean" in card["registry"]["distance_definition"]


def test_s19_site_explains_all_nine_priority_sites_and_decision() -> None:
    page = (ROOT / "docs/session19-result.html").read_text()
    for site in ("GEMSDOE24", "GEMSDOE25", "GEMSDOE27", "GEMSDOE28", "GEMSDOE30",
                 "GEMSDOE31", "GEMSDOE32", "GEMSDOE33", "GEMSDOE36"):
        assert site in page
    assert "submit none of them today" in page
    assert "None is recommended for upload" in page


def test_s19_exact_tiff_hash_and_numeric_contract() -> None:
    import numpy as np
    import rasterio

    card = load("evidence/s19_ascp_run_card.json")
    path = ROOT / card["submission_file"]
    assert hashlib.sha256(path.read_bytes()).hexdigest() == card["raster_sha256"]
    with rasterio.open(path) as src:
        arr = src.read(1)
        assert src.count == 1 and src.dtypes == ("float32",)
        assert src.crs.to_epsg() == 32611 and src.shape == (3730, 3292)
        assert tuple(src.transform)[:6] == (100.0, 0.0, 243350.0, 0.0, -100.0, 4508550.0)
    assert np.isfinite(arr).all()
    assert set(np.unique(arr)) == {0.0, 1.0}
    assert int((arr > 0).sum()) == 37654
