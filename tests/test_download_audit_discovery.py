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


def _write_template_pair(data, profile, footprint):
    template = np.zeros((4, 5), dtype="float32")
    template[~footprint] = np.nan
    with rasterio.open(data / "sample_submission.tif", "w", **profile) as dst:
        dst.write(template, 1)
    with rasterio.open(data / "labels.tif", "w", **profile) as dst:
        dst.write(np.zeros((4, 5), dtype="float32"), 1)


def _run_synthetic_audit(tmp_path, monkeypatch, manifest_data):
    data = tmp_path / "data"
    downloads = tmp_path / "downloads"
    data.mkdir()
    downloads.mkdir()
    footprint = np.ones((4, 5), dtype=bool)
    footprint[0, 0] = False
    profile = dict(driver="GTiff", height=4, width=5, count=1, dtype="float32",
                   crs="EPSG:32611", transform=from_origin(243350, 4508550, 100, 100), nodata=np.nan)
    _write_template_pair(data, profile, footprint)

    for entry in manifest_data.get("legacy_archive", {}).get("entries", []):
        variant = entry["variant"]
        actual_nodata_tag = entry.get("actual_nodata_tag", entry["nodata_tag"])
        nodata = np.nan if actual_nodata_tag == "nan" else None
        candidate_profile = dict(profile, nodata=nodata)
        arr = np.zeros((4, 5), dtype="float32")
        if variant == "nan":
            arr[~footprint] = np.nan
        if entry.get("defect") == "outside":
            arr[~footprint] = 0.0 if variant == "nan" else np.nan
        if entry.get("defect") == "inside":
            arr[0, 1] = np.nan
        with rasterio.open(downloads / entry["filename"], "w", **candidate_profile) as dst:
            dst.write(arr, 1)
        path = downloads / entry["filename"]
        entry["bytes"] = path.stat().st_size
        entry["sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
        entry["footprint_pixels"] = int(footprint.sum())
        entry["emitted_px"] = 0
        entry["catalogue_overlap_px"] = 0

    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps(manifest_data))
    report = tmp_path / "audit.json"
    monkeypatch.setattr(sys, "argv", ["audit", "--data-dir", str(data),
                        "--downloads-dir", str(downloads), "--manifest", str(manifest),
                        "--out", str(report)])
    verify_downloads.main()
    return json.loads(report.read_text())


def test_filename_style_nan_variant_uses_nan_footprint_semantics(tmp_path, monkeypatch):
    data = tmp_path / "data"
    downloads = tmp_path / "downloads"
    data.mkdir()
    downloads.mkdir()
    footprint = np.ones((4, 5), dtype=bool)
    footprint[0, 0] = False
    profile = dict(driver="GTiff", height=4, width=5, count=1, dtype="float32",
                   crs="EPSG:32611", transform=from_origin(243350, 4508550, 100, 100), nodata=np.nan)
    _write_template_pair(data, profile, footprint)
    filename = "future-123456abcdef-nan.tif"
    arr = np.zeros((4, 5), dtype="float32")
    arr[~footprint] = np.nan
    with rasterio.open(downloads / filename, "w", **profile) as dst:
        dst.write(arr, 1)
    candidate = {"filename": filename, "variant": "nan", "nodata_tag": "nan",
                 "emitted_px": 0, "footprint_pixels": int(footprint.sum()),
                 "catalogue_overlap_px": 0,
                 "sha256": hashlib.sha256((downloads / filename).read_bytes()).hexdigest(),
                 "note": "Research only; do not submit."}
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"future_candidate": candidate}))
    report = tmp_path / "audit.json"
    monkeypatch.setattr(sys, "argv", ["audit", "--data-dir", str(data),
                        "--downloads-dir", str(downloads), "--manifest", str(manifest),
                        "--out", str(report)])
    assert verify_downloads.main() == 1  # expected-template-grid and archive-slot checks fail
    result = json.loads(report.read_text())
    checks = {row["check"]: row["pass"] for row in result["checks"]}
    assert checks["future_outside_nan"] is True
    assert checks["future_inside_finite"] is True
    assert checks["future_inside_0_1"] is True
    assert checks["future_exact_sha256"] is True
    assert checks["all_tifs_registered_for_audit"] is True


@pytest.mark.parametrize(
    ("variant", "nodata_tag", "defect", "failed_suffix"),
    [
        ("nan", "nan", None, None),
        ("allfinite", "none", None, None),
        # These two legacy all-finite maps carry a NaN nodata tag but contain
        # only finite values and zero outside the template footprint.
        ("allfinite", "nan", None, None),
        ("nan", "nan", "outside", "outside_nan"),
        ("allfinite", "nan", "outside", "strict_whole_array_0_1"),
        ("allfinite", "none", "wrong_nodata", "nodata_tag_matches"),
        ("nan", "nan", "inside", "inside_finite"),
    ],
)
def test_legacy_archive_variant_audit(tmp_path, monkeypatch, variant, nodata_tag, defect, failed_suffix):
    entry = {
        "id": f"synthetic_{variant}_123456abcdef",
        "content_id": "123456abcdef",
        "filename": f"synthetic-123456abcdef-{variant}.tif",
        "variant": variant,
        "nodata_tag": nodata_tag,
        "footprint_pixels": 19,
        "emitted_px": 0,
        "catalogue_overlap_px": 0,
        "disposition": "research_only_not_submission_approved",
        "submission_ready": False,
        "provenance_status": "local_records_not_independent_authentication",
        "source_records": ["tests/test_download_audit_discovery.py"],
        "defect": defect,
    }
    if defect == "wrong_nodata":
        entry["actual_nodata_tag"] = "nan"
    manifest_data = {"legacy_archive": {"expected_entry_count": 1, "entries": [entry]}}
    result = _run_synthetic_audit(tmp_path, monkeypatch, manifest_data)
    checks = {row["check"]: row["pass"] for row in result["checks"]}
    prefix = "legacy_archive_" + entry["id"]
    if failed_suffix is None:
        assert all(value for key, value in checks.items() if key.startswith(prefix + "_"))
    else:
        assert checks[f"{prefix}_{failed_suffix}"] is False
    assert checks["all_tifs_registered_for_audit"] is True
