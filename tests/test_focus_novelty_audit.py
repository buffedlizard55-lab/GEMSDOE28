from pathlib import Path

import numpy as np
import pytest
from scipy.stats import spearmanr
from scripts.audit_focus_novelty import FOCUS, binary_spearman, compare, load_focus


def test_exact_binary_rank_matches_scipy_tie_handling():
    rng = np.random.default_rng(15)
    a = rng.random((30, 40)) < 0.15
    b = rng.random((30, 40)) < 0.08
    fp = rng.random((30, 40)) < 0.85
    assert binary_spearman(a, b, fp) == pytest.approx(spearmanr(a[fp], b[fp]).statistic, abs=1e-12)


def test_three_pixel_overlap_is_directional_and_inclusive():
    fp = np.ones((10, 10), bool)
    a, b = np.zeros_like(fp), np.zeros_like(fp)
    a[0, 0] = a[5, 5] = True
    b[0, 3] = True  # exactly 3 pixels from one candidate dot
    result = compare(a, b, fp)
    assert result["candidate_within_3px_fraction"] == 0.5
    assert compare(b, a, fp)["candidate_within_3px_fraction"] == 1.0
    assert result["duplicate"] is False
    assert compare(b, a, fp)["duplicate"] is True


def test_constant_raster_is_not_mistaken_for_proven_novelty():
    fp = np.ones((5, 5), bool)
    empty = np.zeros_like(fp)
    other = np.zeros_like(fp)
    other[0, 0] = True
    result = compare(other, empty, fp)
    assert result["spearman_exact"] is None
    assert result["candidate_within_3px_fraction"] is None
    assert result["complete"] is False


def test_focus_inventory_requires_verified_rows(monkeypatch):
    from scripts import audit_focus_novelty as module

    class Template:
        crs = "fake"
        shape = (2, 2)
        transform = "fake-transform"

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def read(self, *args):
            return np.ones(self.shape, np.uint8)

    monkeypatch.setattr(module.rasterio, "open", lambda *args: Template())
    monkeypatch.setattr(module, "load_footprint", lambda *args: np.ones((2, 2), bool))
    assert len(FOCUS) == 9
    with pytest.raises(ValueError, match="priority inventory incomplete"):
        load_focus({"priority_inventory_retrieved": False}, Path("unused"))
    with pytest.raises(ValueError, match="missing priority repository"):
        load_focus({"priority_inventory_retrieved": True, "repositories": []}, Path("unused"))
    first_site, filename = next(iter(FOCUS.items()))
    repo = {"repository": f"owner/{first_site}", "priority_rasters": [{"file": filename, "blob_verified": False}]}
    with pytest.raises(ValueError, match="missing or ambiguous verified raster"):
        load_focus({"priority_inventory_retrieved": True, "repositories": [repo]}, Path("unused"))
