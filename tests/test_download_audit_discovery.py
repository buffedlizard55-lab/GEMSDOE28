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
