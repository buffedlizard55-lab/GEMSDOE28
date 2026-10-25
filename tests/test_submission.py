import zipfile

import numpy as np
import pytest
import rasterio
from rasterio.transform import Affine

from gems27 import grid, submission


@pytest.fixture()
def tiny_template(tmp_path, monkeypatch):
    # small synthetic template with the same semantics (NaN outside, nodata NaN, LZW)
    H, W = 40, 50
    foot = np.zeros((H, W), bool)
    foot[5:35, 8:45] = True
    arr = np.where(foot, 0.0, np.nan).astype("float32")
    path = tmp_path / "tpl.tif"
    prof = dict(driver="GTiff", dtype="float32", count=1, height=H, width=W, crs="EPSG:32611",
                transform=Affine(100, 0, 243350, 0, -100, 4508550), nodata=np.nan, compress="lzw")
    with rasterio.open(path, "w", **prof) as d:
        d.write(arr, 1)
    monkeypatch.setattr(grid, "FOOTPRINT_PX", int(foot.sum()))
    monkeypatch.setattr(grid, "SHAPE", (H, W))
    monkeypatch.setattr(grid, "BOUNDS", (243350.0, 4508550.0 - H * 100, 243350.0 + W * 100, 4508550.0))
    return path, foot


def test_write_and_verify_nan_and_zero_variants(tiny_template, tmp_path):
    tpl, foot = tiny_template
    pred = np.zeros(foot.shape, "float32")
    pred[10, 10:20] = 1.0
    pred[20, 20] = 0.5
    p_nan = submission.write_geotiff(pred, tpl, tmp_path / "a-nan.tif", outside="nan")
    p_zero = submission.write_geotiff(pred, tpl, tmp_path / "a-allfinite.tif", outside="zero")
    r1 = submission.verify_geotiff(p_nan, tpl)
    r2 = submission.verify_geotiff(p_zero, tpl)
    assert r1["hard_checks_passed"], r1["hard_failures"]
    assert r2["hard_checks_passed"], r2["hard_failures"]
    assert r1["variant"] == "nan" and r2["variant"] == "allfinite"
    with rasterio.open(p_nan) as s:
        a = s.read(1)
        assert s.nodata is not None and np.isnan(s.nodata)
        assert np.isnan(a[~foot]).all() and np.isfinite(a[foot]).all()
    with rasterio.open(p_zero) as s:
        a = s.read(1)
        assert s.nodata is None and np.isfinite(a).all() and a.min() >= 0 and a.max() <= 1


@pytest.mark.parametrize("bad", [1.0000001, -0.0000001, np.nan, np.inf])
def test_writer_refuses_out_of_range_or_nonfinite(tiny_template, tmp_path, bad):
    tpl, foot = tiny_template
    pred = np.zeros(foot.shape, "float32")
    pred[10, 10] = bad
    with pytest.raises(ValueError):
        submission.write_geotiff(pred, tpl, tmp_path / "bad.tif")


def test_zip_contains_exactly_one_identical_tif(tiny_template, tmp_path):
    tpl, foot = tiny_template
    p = submission.write_geotiff(np.zeros(foot.shape, "float32"), tpl, tmp_path / "z-nan.tif")
    z = submission.zip_single(p)
    import zipfile
    with zipfile.ZipFile(z) as zf:
        assert zf.namelist() == [p.name]
        assert zf.read(p.name) == p.read_bytes()


def test_note_length_and_filename():
    note = submission.make_note("T-v1", "x" * 400, "abcdef123456")
    assert len(note) <= 200 and note.endswith("not yet live-scored")
    fn = submission.make_filename("gems27", "Topo gap/closure d1.5", "20261002", "abcdef123456", "nan")
    assert fn == "gems27-topo-gap-closure-d1-5-20261002-abcdef123456-nan.tif"


def test_content_id_ignores_catalogue_pixels():
    foot = np.ones((5, 5), bool)
    cat = np.zeros((5, 5), bool)
    cat[2, 2] = True
    a = np.zeros((5, 5), "float32")
    b = a.copy()
    b[2, 2] = 1.0
    assert submission.scored_content_id(a, foot, cat) == submission.scored_content_id(b, foot, cat)


def test_template_with_shifted_grid_is_rejected(tiny_template, tmp_path):
    tpl, foot = tiny_template
    with rasterio.open(tpl, 'r+') as dst:
        dst.transform = Affine(100, 0, 243450, 0, -100, 4508550)
    with pytest.raises(ValueError, match='geotransform'):
        submission.write_geotiff(np.zeros(foot.shape), tpl, tmp_path / 'wrong-grid.tif')


def test_verifier_rejects_invalid_template(tiny_template, tmp_path):
    tpl, foot = tiny_template
    output = submission.write_geotiff(np.zeros(foot.shape), tpl, tmp_path / 'valid.tif')
    with rasterio.open(tpl, 'r+') as dst:
        dst.crs = 'EPSG:4326'
    with pytest.raises(ValueError, match='CRS/shape'):
        submission.verify_geotiff(output, tpl)


def test_new_notes_follow_stricter_parallel_protocol():
    note = submission.make_note("new", "a" * 400, "abcdef123456", family="GEMSDOE28")
    assert 0 < len(note) <= 140


@pytest.mark.parametrize("pred", [np.zeros((40, 50), np.complex64),
                                  np.full((40, 50), "0", dtype="U1")])
def test_writer_rejects_non_real_or_text_predictions(tiny_template, tmp_path, pred):
    template, _ = tiny_template
    with pytest.raises(ValueError, match="real numeric"):
        submission.write_geotiff(pred, template, tmp_path / "invalid.tif")


def test_writer_never_overwrites_template(tiny_template):
    template, footprint = tiny_template
    before = template.read_bytes()
    with pytest.raises(ValueError, match="overwrite"):
        submission.write_geotiff(np.zeros(footprint.shape), template, template)
    assert template.read_bytes() == before


def test_writer_preserves_previous_output_if_disk_validation_fails(tiny_template, tmp_path, monkeypatch):
    template, footprint = tiny_template
    output = tmp_path / "existing.tif"
    output.write_bytes(b"previous artifact must survive")
    monkeypatch.setattr(submission, "verify_geotiff", lambda *args: {
        "hard_checks_passed": False, "hard_failures": ["injected validation failure"]})
    with pytest.raises(ValueError, match="serialized"):
        submission.write_geotiff(np.zeros(footprint.shape), template, output)
    assert output.read_bytes() == b"previous artifact must survive"
    assert not list(tmp_path.glob(".existing-*.tif"))


def test_verifier_returns_negative_for_wrong_shape_instead_of_crashing(tiny_template, tmp_path):
    template, _ = tiny_template
    with rasterio.open(template) as source:
        profile = source.profile.copy()
    profile.update(width=7, height=8)
    output = tmp_path / "wrong-shape.tif"
    with rasterio.open(output, "w", **profile) as dst:
        dst.write(np.zeros((8, 7), np.float32), 1)
    result = submission.verify_geotiff(output, template)
    assert not result["hard_checks_passed"]
    assert "grid_matches_template" in result["hard_failures"]


def test_numeric_nodata_sentinel_does_not_pass_as_allfinite(tiny_template, tmp_path):
    template, footprint = tiny_template
    path = submission.write_geotiff(np.zeros(footprint.shape), template, tmp_path / "numeric-nodata.tif", outside="zero")
    with rasterio.open(path, "r+") as dst:
        dst.nodata = 0
    result = submission.verify_geotiff(path, template)
    assert not result["hard_checks_passed"]
    assert "nodata_convention" in result["hard_failures"]


def test_bad_nan_raster_report_can_be_strict_json(tiny_template, tmp_path):
    import json

    template, footprint = tiny_template
    path = submission.write_geotiff(np.zeros(footprint.shape), template, tmp_path / "bad-interior.tif")
    with rasterio.open(path, "r+") as dst:
        values = dst.read(1)
        values[10, 10] = np.nan
        dst.write(values, 1)
    result = submission.verify_geotiff(path, template)
    assert not result["hard_checks_passed"]
    assert result["nonfinite_inside_px"] == 1
    json.dumps(result, allow_nan=False)


def test_zip_cannot_destroy_source_tiff(tiny_template, tmp_path):
    template, footprint = tiny_template
    path = submission.write_geotiff(np.zeros(footprint.shape), template, tmp_path / "source.tif")
    before = path.read_bytes()
    with pytest.raises(ValueError, match="distinct"):
        submission.zip_single(path, path)
    assert path.read_bytes() == before


def test_empty_footprint_and_shape_mismatch_fail_clearly():
    with pytest.raises(ValueError, match="aligned"):
        submission.check_probabilities(np.zeros((3, 3)), np.zeros((3, 3), bool))
    with pytest.raises(ValueError, match="aligned"):
        submission.check_probabilities(np.zeros((3, 3)), np.ones((2, 2), bool))


def test_zip_cannot_destroy_hardlinked_source(tiny_template, tmp_path):
    template, footprint = tiny_template
    source = submission.write_geotiff(np.zeros(footprint.shape), template, tmp_path / "original.tif")
    alias = tmp_path / "hardlink.zip"
    alias.hardlink_to(source)
    before = source.read_bytes()
    with pytest.raises(ValueError, match="distinct"):
        submission.zip_single(source, alias)
    assert source.read_bytes() == before


def test_zip_preserves_previous_output_on_packaging_failure(tiny_template, tmp_path, monkeypatch):
    template, footprint = tiny_template
    source = submission.write_geotiff(np.zeros(footprint.shape), template, tmp_path / "source.tif")
    output = tmp_path / "existing.zip"
    output.write_bytes(b"previous archive must survive")
    def fail_write(*args, **kwargs):
        raise OSError("injected packaging failure")
    monkeypatch.setattr(zipfile.ZipFile, "writestr", fail_write)
    with pytest.raises(OSError, match="injected"):
        submission.zip_single(source, output)
    assert output.read_bytes() == b"previous archive must survive"
    assert not list(tmp_path.glob(".existing-*.zip"))


def test_independent_verifier_rejects_complex_raster(tiny_template, tmp_path):
    import json

    template, footprint = tiny_template
    with rasterio.open(template) as source:
        profile = source.profile.copy()
    profile.update(dtype="complex64", nodata=None)
    path = tmp_path / "complex.tif"
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(np.zeros(footprint.shape, np.complex64), 1)
    result = submission.verify_geotiff(path, template)
    assert not result["hard_checks_passed"]
    assert "single_band_float32" in result["hard_failures"]
    json.dumps(result, allow_nan=False)
