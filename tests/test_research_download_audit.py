"""A registered hash is not sufficient: inspect sibling research TIFFs and ZIPs."""
import hashlib
import json
import zipfile

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from scripts.audit_research_downloads import audit_research


@pytest.mark.parametrize("defect", [None, "range", "nan_inside", "inf", "shape", "crs", "transform",
                                    "bands", "outside", "catalogue", "zip_extra", "zip_different",
                                    "zip_missing", "note", "approval", "traversal", "corrupt",
                                    "missing", "manifest", "empty_manifest", "symlink"])
def test_research_audit_catches_defects_even_with_matching_hash(tmp_path, defect):
    transform = from_origin(0, 400, 100, 100)
    crs = rasterio.crs.CRS.from_epsg(32611)
    profile = dict(driver="GTiff", width=5, height=4, count=1, dtype="float32",
                   crs=crs, transform=transform, nodata=np.nan)
    footprint = np.ones((4, 5), dtype=bool)
    footprint[0, 0] = False
    catalogue = np.zeros((4, 5), dtype=bool)
    arr = np.zeros((4, 5), dtype="float32")
    arr[0, 0] = np.nan
    if defect in ("range", "nan_inside", "inf"):
        arr[1, 1] = {"range": 1.01, "nan_inside": np.nan, "inf": np.inf}[defect]
    if defect == "outside":
        arr[0, 0] = 0.0
    if defect == "catalogue":
        arr[1, 1], catalogue[1, 1] = 1.0, True
    if defect == "shape":
        profile["height"] = 3
        arr = arr[:3]
    if defect == "bands":
        profile["count"] = 2
    if defect == "crs":
        profile["crs"] = "EPSG:4326"
    if defect == "transform":
        profile["transform"] = from_origin(1, 400, 100, 100)
    tif = tmp_path / "research-123456abcdef-nan.tif"
    with rasterio.open(tif, "w", **profile) as dst:
        for band in range(1, profile["count"] + 1):
            dst.write(arr, band)
    if defect == "corrupt":
        tif.write_bytes(b"not a TIFF")
    if defect == "symlink":
        external = tmp_path.parent / (tmp_path.name + "-outside.tif")
        external.write_bytes(tif.read_bytes())
        tif.unlink()
        tif.symlink_to(external)
    zipped = tif.with_suffix(".zip")
    with zipfile.ZipFile(zipped, "w") as archive:
        archive.writestr(tif.name, b"wrong" if defect == "zip_different" else tif.read_bytes())
        if defect == "zip_extra":
            archive.writestr("second.tif", b"bad")
    entry = dict(file=tif.name, zip=zipped.name,
                 sha256_tif=hashlib.sha256(tif.read_bytes()).hexdigest(),
                 sha256_zip=hashlib.sha256(zipped.read_bytes()).hexdigest(),
                 note="Research only. Do not submit.")
    if defect == "note":
        entry["note"] = "x" * 141
    if defect == "approval":
        entry["ok_to_submit"] = True
    if defect == "traversal":
        entry["file"] = "../escape.tif"
    if defect == "missing":
        tif.unlink()
    if defect == "zip_missing":
        zipped.unlink()
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"research": entry}))
    if defect == "manifest":
        manifest.write_text("[]")
    if defect == "empty_manifest":
        manifest.write_text("{}")
    checks, names = audit_research(manifest, tmp_path, (crs, (4, 5), transform),
                                  footprint, catalogue)
    assert checks
    assert all(row["pass"] for row in checks) is (defect is None)
    if defect is None:
        assert names == {tif.name, zipped.name}
        assert len(checks) >= 10
