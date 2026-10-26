"""Every filename-style research artifact must be audited, not just S18."""
import hashlib
import json
import sys

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from scripts import verify_downloads


@pytest.mark.parametrize("defect", [None, "range", "missing", "hash", "note", "approval", "orphan"])
def test_future_filename_slot_is_audited(tmp_path, monkeypatch, defect):
    profile = dict(driver="GTiff", height=4, width=5, count=1, dtype="float32",
                   crs="EPSG:32611", transform=from_origin(243350, 4508550, 100, 100))
    data = tmp_path / "data"
    downloads = tmp_path / "downloads"
    data.mkdir()
    downloads.mkdir()
    for name in ("sample_submission.tif", "labels.tif"):
        with rasterio.open(data / name, "w", **profile) as dst:
            dst.write(np.zeros((4, 5), dtype="float32"), 1)
    filename = "future-123456abcdef-allfinite.tif"
    path = downloads / filename
    arr = np.zeros((4, 5), dtype="float32")
    if defect == "range":
        arr[-1, -1] = 1.01
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(arr, 1)
    entry = dict(filename=filename, sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                 verdict="negative", submission_ready=False, note="Research only; do not submit.")
    if defect == "hash":
        entry["sha256"] = "0" * 64
    if defect == "note":
        entry["note"] = "x" * 141
    if defect == "approval":
        entry["submission_ready"] = True
    if defect == "missing":
        path.unlink()
    if defect == "orphan":
        (downloads / "unregistered-abcdef123456-allfinite.tif").write_bytes(path.read_bytes())
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"future_candidate": entry}))
    report = tmp_path / "audit.json"
    monkeypatch.setattr(sys, "argv", ["audit", "--data-dir", str(data),
                        "--downloads-dir", str(downloads), "--manifest", str(manifest),
                        "--out", str(report)])
    # Synthetic grid and absence of legacy twin entries intentionally fail unrelated checks.
    assert verify_downloads.main() == 1
    result = json.loads(report.read_text())
    checks = {c["check"]: c["pass"] for c in result["checks"]}
    expected = {"range": "strict_whole_array_0_1", "missing": "file_exists",
                "hash": "exact_sha256", "note": "note_140", "approval": "rejected_not_approved"}
    if defect == "orphan":
        assert checks["all_tifs_registered_for_audit"] is False
    elif defect is None:
        assert all(v for k, v in checks.items() if k.startswith("future_"))
        assert "future_exact_sha256" in checks
    else:
        assert checks["future_" + expected[defect]] is False


@pytest.mark.parametrize("defect", ["different-pixels", "nan-shape", "fallback-shape", "corrupt-fallback"])
def test_twin_variants_are_identical_and_bad_files_fail_closed(tmp_path, monkeypatch, defect):
    profile = dict(driver="GTiff", height=4, width=5, count=1, dtype="float32",
                   crs="EPSG:32611", transform=from_origin(243350, 4508550, 100, 100))
    data, downloads = tmp_path / "data", tmp_path / "downloads"
    data.mkdir()
    downloads.mkdir()
    for name in ("sample_submission.tif", "labels.tif"):
        with rasterio.open(data / name, "w", **profile) as dst:
            dst.write(np.zeros((4, 5), dtype="float32"), 1)
    token = "abcdef123456"
    nan_name, finite_name = f"test-{token}-nan.tif", f"test-{token}-allfinite.tif"
    nan_path, finite_path = downloads / nan_name, downloads / finite_name
    a = np.zeros((4, 5), dtype="float32")
    a[1, 1] = 1.0
    b = a.copy()
    if defect == "different-pixels":
        b[1, 1], b[1, 2] = 0.0, 1.0
    nan_profile = {**profile, "nodata": np.nan}
    if defect == "nan-shape":
        nan_profile["height"] = 3
    with rasterio.open(nan_path, "w", **nan_profile) as dst:
        dst.write(a[:nan_profile["height"]], 1)
    finite_profile = dict(profile)
    if defect == "fallback-shape":
        finite_profile["height"] = 3
    with rasterio.open(finite_path, "w", **finite_profile) as dst:
        dst.write(b[:finite_profile["height"]], 1)
    if defect == "corrupt-fallback":
        finite_path.write_bytes(b"not a tiff")
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()  # noqa: E731
    entry = dict(content_id=token, submission_name=f"research-{token}", nan=nan_name,
                 allfinite=finite_name, bytes_nan=nan_path.stat().st_size, sha256_nan=digest(nan_path),
                 bytes_allfinite=finite_path.stat().st_size, sha256_allfinite=digest(finite_path),
                 emitted_px=1, note="Research only; do not submit.")
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"test_candidate": entry}))
    report = tmp_path / "audit.json"
    monkeypatch.setattr(sys, "argv", ["audit", "--data-dir", str(data), "--downloads-dir", str(downloads),
                                     "--manifest", str(manifest), "--out", str(report)])
    assert verify_downloads.main() == 1
    checks = {c["check"]: c["pass"] for c in json.loads(report.read_text())["checks"]}
    failure = {"different-pixels": "variant_footprint_values_equal", "nan-shape": "nan_grid",
               "fallback-shape": "allfinite_grid_and_type", "corrupt-fallback": "allfinite_readable"}[defect]
    assert checks["test_candidate_" + failure] is False


def test_missing_inputs_replace_an_old_green_report(tmp_path, monkeypatch):
    data, downloads = tmp_path / "data", tmp_path / "downloads"
    data.mkdir()
    downloads.mkdir()
    (downloads / "manifest.json").write_text("{}")
    report = tmp_path / "audit.json"
    report.write_text('{"status":"PASS"}')
    monkeypatch.setattr(sys, "argv", ["audit", "--data-dir", str(data), "--downloads-dir", str(downloads),
                                     "--out", str(report)])
    assert verify_downloads.main() == 1
    result = json.loads(report.read_text())
    assert result["status"] == "FAIL" and result["failures"] == ["inputs_readable"]


def test_misaligned_label_shape_records_failures_instead_of_crashing(tmp_path, monkeypatch):
    profile = dict(driver="GTiff", height=4, width=5, count=1, dtype="float32",
                   crs="EPSG:32611", transform=from_origin(243350, 4508550, 100, 100))
    data, downloads = tmp_path / "data", tmp_path / "downloads"
    data.mkdir()
    downloads.mkdir()
    with rasterio.open(data / "sample_submission.tif", "w", **profile) as dst:
        dst.write(np.zeros((4, 5), dtype="float32"), 1)
    with rasterio.open(data / "labels.tif", "w", **{**profile, "height": 3}) as dst:
        dst.write(np.zeros((3, 5), dtype="float32"), 1)
    filename = "future-123456abcdef-allfinite.tif"
    path = downloads / filename
    with rasterio.open(path, "w", **profile) as dst:
        dst.write(np.zeros((4, 5), dtype="float32"), 1)
    (downloads / "manifest.json").write_text(json.dumps({"future_candidate": {
        "filename": filename, "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "verdict": "negative", "submission_ready": False, "note": "DO NOT SUBMIT"}}))
    report = tmp_path / "audit.json"
    monkeypatch.setattr(sys, "argv", ["audit", "--data-dir", str(data), "--downloads-dir", str(downloads),
                                     "--out", str(report)])
    assert verify_downloads.main() == 1
    result = json.loads(report.read_text())
    assert result["status"] == "FAIL"
    assert "labels_grid_matches_template" in result["failures"]
    assert "future_no_catalogue_predictions" in result["failures"]
