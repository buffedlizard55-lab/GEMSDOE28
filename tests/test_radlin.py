"""S19-RADLIN surface: frozen transform behaviour on synthetic fields."""
import numpy as np
import pytest

from gems27.radlin import oriented_line_means, radiometric_lineament_surface


def test_lineament_fires_on_low_thk_line_not_on_background():
    rng = np.random.default_rng(1)
    thk = rng.integers(150, 220, size=(61, 61)).astype(np.uint8)
    thk[30, 5:56] = 20  # 5.1 km low-ThK line
    valid = np.ones((61, 61), bool)
    out = radiometric_lineament_surface(thk, valid)
    score = out["score"]
    assert score.dtype == np.float32 and score.min() >= 0.0 and score.max() <= 1.0
    assert score[30, 30] > 0.0, "line centre must earn lineament score"
    assert score[5, 5] == 0.0, "uniform background is not a ridge"
    assert out["meta"]["ridge_px"] > 0


def test_constant_field_has_no_lineaments():
    thk = np.full((31, 31), 100, dtype=np.uint8)
    valid = np.ones((31, 31), bool)
    with pytest.raises(ValueError):
        radiometric_lineament_surface(thk, valid)  # degenerate p95<=p5, not silent zeros


def test_invalid_pixels_are_zero_and_nodata_excluded():
    rng = np.random.default_rng(0)
    thk = rng.integers(50, 220, size=(41, 41)).astype(np.uint8)
    valid = np.ones((41, 41), bool)
    valid[:10] = False
    thk[:5] = 0  # nodata inside the valid block is also excluded
    out = radiometric_lineament_surface(thk, valid)
    assert (out["score"][:10] == 0).all() and (out["bonus"][:10] == 0).all()
    assert np.isfinite(out["score"]).all() and np.isfinite(out["bonus"]).all()


def test_shape_and_empty_valid_errors():
    with pytest.raises(ValueError):
        radiometric_lineament_surface(np.zeros((4, 4), np.uint8), np.zeros((4, 5), bool))
    with pytest.raises(ValueError):
        radiometric_lineament_surface(np.zeros((4, 4), np.uint8), np.zeros((4, 4), bool))


def test_oriented_line_means_anisotropy_direction():
    img = np.zeros((41, 41), np.float32)
    img[20, :] = 1.0  # E-W line: E-W orientation mean is the max at the centre
    mx, mean = oriented_line_means(img, half_px=10)
    assert mx[20, 20] > mean[20, 20] > 0.0
    assert mx[0, 0] == 0.0
