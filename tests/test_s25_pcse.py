"""S25 PCSE decision is pinned to its evidence: hashes, grid, range, note length, and NO-submit wording."""
import hashlib
import json
import re
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
CARD = json.loads((ROOT / "evidence/s25_pcse_run_card.json").read_text())
MANIFEST = json.loads((ROOT / "docs/downloads/s25_research_manifest.json").read_text())["s25_pcse_research"]
TIF = ROOT / "docs/downloads" / CARD["submission"]["name"]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_tif_bytes_match_run_card_and_manifest():
    assert TIF.is_file()
    assert sha(TIF) == CARD["submission"]["sha256_tif"] == MANIFEST["sha256_tif"]
    zip_path = ROOT / "docs/downloads" / CARD["submission"]["zip"]
    assert sha(zip_path) == CARD["submission"]["sha256_zip"] == MANIFEST["sha256_zip"]


def test_tif_grid_range_and_footprint():
    with rasterio.open(ROOT / "data/sample_submission.tif") as t, rasterio.open(TIF) as s:
        foot = np.isfinite(t.read(1))
        assert s.crs.to_epsg() == 32611 and s.count == 1 and s.dtypes == ("float32",)
        assert s.shape == t.shape and tuple(s.transform)[:6] == tuple(t.transform)[:6]
        a = s.read(1)
        inside = a[foot]
        assert np.isfinite(inside).all()
        assert inside.min() >= 0.0 and inside.max() <= 1.0
        assert not np.isinf(a).any()
        assert np.isnan(a[~foot]).all()


def test_note_is_short_and_unsubmittable_wording():
    note = MANIFEST["note"]
    assert len(note) <= 140
    assert "NOT for submission" in note
    assert MANIFEST["organizer_score"] is None
    for rel in ("docs/s25/index.html", "docs/index.html", "index.html"):
        page = (ROOT / rel).read_text(encoding="utf-8")
        assert "OK to submit: NO" in page or "OK TO SUBMIT: NO" in page, rel
        assert not re.search(r"OK to submit:\s*</td><td>\s*YES", page), rel


def test_holdout_numbers_are_labelled_and_consistent():
    hd = CARD["holdout_dti"]
    assert hd["label"] == "HOLDOUT-DTI"
    assert CARD["evaluator"] == "gems-segment-pooled-v1"
    assert hd["n_withheld_positive_pixels"] == 60988
    assert hd["ci95"]["interval"][0] <= hd["value"] <= hd["ci95"]["interval"][1]
    assert CARD["control_random_k_holdout_dti"]["value"] > hd["value"]
    assert CARD["novelty"]["any_duplicate_flag"] is False
    assert CARD["canary"]["passed"] is True
