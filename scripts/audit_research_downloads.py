"""Independently inspect sibling-manifest TIFF/ZIP bytes, not only their hashes.

This is an archive audit, not an evaluator/writer or an upload authorization.
It uses the caller's exact template footprint and grid, with no resampling.
"""
from __future__ import annotations

import hashlib
import json
import zipfile
from pathlib import Path

import numpy as np
import rasterio


def audit_research(path, downloads, template_signature, footprint, catalogue):
    rows, registered = [], set()
    downloads = Path(downloads).resolve()

    def check(ok, name, detail):
        rows.append({"check": name, "pass": bool(ok), "detail": str(detail)})

    def target(name):
        if (not isinstance(name, str) or Path(name).name != name
                or not (downloads / name).resolve().is_relative_to(downloads)):
            raise ValueError("unsafe research filename")
        return downloads / name

    try:
        manifest = json.loads(Path(path).read_text())
        if not isinstance(manifest, dict):
            raise ValueError("research manifest must be an object")
        entries = [(key, value) for key, value in manifest.items()
                   if isinstance(value, dict) and "file" in value]
        if not entries:
            raise ValueError("research manifest contains no file entries")
    except (OSError, ValueError, TypeError) as exc:
        check(False, "research_manifest_readable", exc)
        return rows, registered

    for slot, item in entries:
        prefix = str(slot) + "_"
        try:
            tif = target(item["file"])
            registered.add(tif.name)
            if tif.suffix != ".tif":
                raise ValueError("research file must be a TIFF")
            raw = tif.read_bytes()
            check(hashlib.sha256(raw).hexdigest() == item.get("sha256_tif"),
                  prefix + "exact_sha256", tif.name)
            with rasterio.open(tif) as ds:
                arr = ds.read(1)
                grid_ok = (ds.crs, ds.shape, ds.transform) == template_signature
                check(grid_ok, prefix + "grid", "Exact CRS, shape and transform match")
                check(ds.count == 1 and ds.dtypes == ("float32",),
                      prefix + "single_band_float32", ds.dtypes)
                if arr.shape == footprint.shape and arr.dtype.kind in "buif":
                    inside, outside = arr[footprint], arr[~footprint]
                    check(inside.size and np.isfinite(inside).all()
                          and (inside >= 0).all() and (inside <= 1).all(),
                          prefix + "inside_finite_0_1", "No NaN/Inf or out-of-range interior")
                    check(not np.isinf(arr).any(), prefix + "no_infinities", "Entire raster")
                    nan_nodata = ds.nodata is not None and np.isnan(ds.nodata)
                    check((nan_nodata and np.isnan(outside).all())
                          or (ds.nodata is None and np.isfinite(outside).all()
                              and (outside == 0).all()),
                          prefix + "outside_convention", "NaN with NaN tag or zero with no nodata")
                    check(grid_ok and catalogue is not None
                          and not ((arr > 0) & catalogue & footprint).any(),
                          prefix + "no_catalogue_overlap", "Aligned catalogue required")
                else:
                    check(False, prefix + "inside_finite_0_1", "Mismatched shape or non-real dtype")
            note = item.get("note")
            check(isinstance(note, str) and 0 < len(note) <= 140,
                  prefix + "note_140", "Research note must contain 1–140 characters")
            check(item.get("submission_ready", False) is False
                  and item.get("ok_to_submit", False) is False,
                  prefix + "not_approved", "Archive audit cannot authorize upload")
            if item.get("zip") is not None:
                zipped = target(item["zip"])
                registered.add(zipped.name)
                zip_raw = zipped.read_bytes()
                check(hashlib.sha256(zip_raw).hexdigest() == item.get("sha256_zip"),
                      prefix + "zip_sha256", zipped.name)
                with zipfile.ZipFile(zipped) as archive:
                    # Check size before reading to avoid decompressing unbounded content.
                    infos = archive.infolist()
                    one = (len(infos) == 1 and infos[0].filename == tif.name
                           and infos[0].file_size == len(raw) and not infos[0].is_dir())
                    check(one, prefix + "zip_single_tif", "Exactly the registered TIFF")
                    check(one and archive.read(infos[0]) == raw,
                          prefix + "zip_identical", "Exact uncompressed bytes")
        except (OSError, ValueError, TypeError, KeyError, RuntimeError,
                zipfile.BadZipFile, rasterio.errors.RasterioError) as exc:
            check(False, prefix + "readable_safe_artifacts", exc)
    return rows, registered
