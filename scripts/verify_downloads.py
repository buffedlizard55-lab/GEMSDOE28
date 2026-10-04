#!/usr/bin/env python3
"""Independent local audit of all manual GeoTIFF/ZIP research downloads.

This script performs no network requests and never accesses DrivenData. It checks exact local hashes,
bytes, content-addressed names, single-band float32 format, template grid, inside-footprint finiteness
and [0,1] range, outside-footprint nodata convention, catalogue overlap, ZIP membership, and note length.
It does not prove organizer authenticity or guarantee the portal will accept a file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATA = Path(os.environ.get("GEMS_DATA_DIR", ROOT / "data"))
DEFAULT_DOWNLOADS = ROOT / "docs" / "downloads"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=str(DEFAULT_DATA))
    parser.add_argument("--downloads-dir", default=str(DEFAULT_DOWNLOADS))
    parser.add_argument("--template", default=None, help="defaults to data/sample_submission.tif")
    parser.add_argument("--manifest", default=None, help="defaults to docs/downloads/manifest.json")
    parser.add_argument("--out", default=str(ROOT / "evidence" / "submission_file_audit.json"))
    args = parser.parse_args()
    data_dir = Path(args.data_dir)
    downloads_dir = Path(args.downloads_dir)
    template_path = Path(args.template) if args.template else data_dir / "sample_submission.tif"
    manifest_path = Path(args.manifest) if args.manifest else downloads_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    labels_path = data_dir / "labels.tif"
    if not template_path.is_file() or not labels_path.is_file():
        raise SystemExit(f"Template or labels missing: {template_path}, {labels_path}")

    failures: list[str] = []
    checks: list[dict] = []

    def check(condition: bool, name: str, detail: str) -> None:
        checks.append({"check": name, "pass": bool(condition), "detail": detail})
        if not condition:
            failures.append(name)

    with rasterio.open(template_path) as template:
        template_array = template.read(1)
        footprint = np.isfinite(template_array)
        template_signature = (template.crs, template.shape, template.transform)
        template_info = {
            "path": str(template_path), "sha256": sha256_file(template_path),
            "crs": template.crs.to_string(), "shape": list(template.shape),
            "transform": list(tuple(template.transform)[:6]), "footprint_pixels": int(footprint.sum()),
        }
    with rasterio.open(labels_path) as label_ds:
        labels = label_ds.read(1)
        label_grid_ok = (label_ds.crs, label_ds.shape, label_ds.transform) == template_signature
        catalogue = np.isfinite(labels) & (labels > 0)
    check(label_grid_ok, "labels_grid_matches_template", f"{labels_path.name} grid matches {template_path.name}")
    check(int(footprint.sum()) == 5_167_373 and template_info["shape"] == [3730, 3292]
          and template_info["crs"] == "EPSG:32611", "expected_template_grid",
          f"{template_info['crs']} {template_info['shape']}; footprint={footprint.sum():,}")

    candidates = []
    for slot in ("primary", "secondary", "tertiary", "quaternary", "quinary_probe",
                 "conservative_alternative", "research_candidate"):
        item = manifest.get(slot)
        if isinstance(item, dict) and item.get("nan"):
            candidates.append((slot, item))
    check(bool(candidates), "manifest_candidates_present", f"{len(candidates)} candidate(s) listed")
    submission_names = [str(item.get("submission_name", "")).strip() for _, item in candidates]
    check(all(submission_names), "submission_names_present", f"{len(submission_names)} artifact(s) have a registered portal name")
    check(len(submission_names) == len(set(submission_names)), "submission_names_unique",
          f"{len(submission_names)} registered name(s), all distinct")

    for slot, item in candidates:
        submission_name = str(item.get("submission_name", "")).strip()
        content_token = str(item.get("content_id", ""))
        check(bool(submission_name and content_token and content_token in submission_name),
              f"{slot}_submission_name_content_id", submission_name)
        content_id = str(item.get("content_id", ""))
        nan_name = str(item["nan"])
        nan_path = downloads_dir / nan_name
        stem_check = bool(content_id and re.search(rf"-{re.escape(content_id)}-nan\.tif$", nan_name))
        check(stem_check, f"{slot}_content_addressed_name", nan_name)
        check(nan_path.is_file(), f"{slot}_nan_file_exists", nan_name)
        if not nan_path.is_file():
            continue
        actual_bytes = nan_path.stat().st_size
        actual_sha = sha256_file(nan_path)
        check(actual_bytes == item.get("bytes_nan"), f"{slot}_nan_byte_count", f"{actual_bytes} bytes")
        check(actual_sha == item.get("sha256_nan"), f"{slot}_nan_sha256", actual_sha)
        with rasterio.open(nan_path) as dataset:
            arr = dataset.read(1)
            grid_match = (dataset.crs, dataset.shape, dataset.transform) == template_signature
            one_band = dataset.count == 1 and dataset.dtypes[0] == "float32"
            nodata_is_nan = dataset.nodata is not None and np.isnan(dataset.nodata)
        check(grid_match, f"{slot}_nan_grid", "CRS/shape/transform equal the sample template")
        check(one_band, f"{slot}_nan_single_band_float32", f"count=1 dtype={arr.dtype}")
        inside = arr[footprint]
        outside = arr[~footprint]
        inside_finite = bool(np.isfinite(inside).all())
        inside_range = bool(inside_finite and inside.min() >= 0.0 and inside.max() <= 1.0)
        values_binary = bool(inside_finite and set(np.unique(inside).tolist()) <= {0.0, 1.0})
        outside_nan = bool(np.isnan(outside).all() and nodata_is_nan)
        overlap = int(((arr > 0) & catalogue & footprint).sum())
        emitted = int((inside == 1.0).sum()) if inside_finite else -1
        check(inside_finite, f"{slot}_nan_inside_finite", f"nonfinite inside={int((~np.isfinite(inside)).sum())}")
        check(inside_range, f"{slot}_nan_inside_0_1", f"finite inside range=[{np.nanmin(inside):g}, {np.nanmax(inside):g}]")
        check(values_binary, f"{slot}_nan_exact_binary", "inside values are exactly 0.0 or 1.0")
        check(outside_nan, f"{slot}_nan_outside_nan", f"outside NaN count={int(np.isnan(outside).sum())}/{outside.size}; nodata=NaN")
        check(emitted == item.get("emitted_px"), f"{slot}_nan_emitted_count", f"{emitted} cells equal 1.0")
        check(overlap == 0, f"{slot}_nan_no_catalogue_overlap", f"positive catalogue overlap={overlap}")
        check(not bool(np.isinf(arr).any()), f"{slot}_nan_no_infinities", "no infinity anywhere")

        allfinite_name = item.get("allfinite")
        if allfinite_name:
            fallback = downloads_dir / allfinite_name
            fallback_ok = fallback.is_file()
            check(fallback_ok, f"{slot}_allfinite_file_exists", str(allfinite_name))
            if fallback_ok:
                check(bool(re.search(rf"-{re.escape(content_id)}-allfinite\.tif$", allfinite_name)),
                      f"{slot}_allfinite_content_addressed_name", str(allfinite_name))
                check(fallback.stat().st_size == item.get("bytes_allfinite"),
                      f"{slot}_allfinite_byte_count", f"{fallback.stat().st_size} bytes")
                check(sha256_file(fallback) == item.get("sha256_allfinite"),
                      f"{slot}_allfinite_sha256", sha256_file(fallback))
                with rasterio.open(fallback) as dataset:
                    fallback_arr = dataset.read(1)
                    fallback_grid = (dataset.crs, dataset.shape, dataset.transform) == template_signature
                    fallback_type = dataset.count == 1 and dataset.dtypes[0] == "float32"
                    no_nodata = dataset.nodata is None
                fin = fallback_arr[footprint]
                fout = fallback_arr[~footprint]
                check(fallback_grid and fallback_type, f"{slot}_allfinite_grid_and_type", "single float32 band on exact template grid")
                check(bool(np.isfinite(fallback_arr).all() and np.isfinite(fin).all() and fin.min() >= 0 and fin.max() <= 1),
                      f"{slot}_allfinite_range", f"whole array finite; inside range=[{fin.min():g},{fin.max():g}]")
                check(bool((fout == 0).all() and no_nodata), f"{slot}_allfinite_outside_zero", "outside zero; no nodata tag")
                check(int((fin == 1.0).sum()) == item.get("emitted_px"), f"{slot}_allfinite_emitted_count", f"{int((fin == 1.0).sum())} cells equal 1.0")
                check(int(((fallback_arr > 0) & catalogue & footprint).sum()) == 0,
                      f"{slot}_allfinite_no_catalogue_overlap", "no positive known-catalogue overlap")

        zip_name = item.get("zip")
        if zip_name:
            zip_path = downloads_dir / zip_name
            zip_ok = zip_path.is_file()
            check(zip_ok, f"{slot}_zip_exists", str(zip_name))
            if zip_ok:
                check(zip_path.stat().st_size == item.get("bytes_zip"), f"{slot}_zip_byte_count", f"{zip_path.stat().st_size} bytes")
                check(sha256_file(zip_path) == item.get("sha256_zip"), f"{slot}_zip_sha256", sha256_file(zip_path))
                try:
                    with zipfile.ZipFile(zip_path) as archive:
                        members = archive.namelist()
                        one_tif = members == [nan_name]
                        byte_identical = one_tif and archive.read(nan_name) == nan_path.read_bytes()
                except (OSError, zipfile.BadZipFile):
                    one_tif = byte_identical = False
                check(one_tif, f"{slot}_zip_single_tif", f"members={members if 'members' in locals() else 'invalid zip'}")
                check(byte_identical, f"{slot}_zip_byte_identical", "single member matches the NaN TIFF byte-for-byte")

        note = str(item.get("note", ""))
        note_chars = len(note)
        check(0 < note_chars <= 200, f"{slot}_note_length", f"{note_chars} chars; max 200")
        note_file = item.get("note_file")
        if note_file:
            path = downloads_dir / note_file
            check(path.is_file() and path.read_text(encoding="utf-8").strip() == note,
                  f"{slot}_note_file_matches", str(note_file))

    names = [path.name for path in downloads_dir.glob("*.tif")]
    check(len(names) == len(set(names)), "all_tif_names_unique", f"{len(names)} unique GeoTIFF(s)")
    check(all(re.search(r"-[0-9a-f]{12}-(nan|allfinite)\.tif$", name) for name in names),
          "all_tif_names_content_addressed", "all downloaded GeoTIFF names contain a 12-hex content ID")

    report = {
        "checked_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "PASS" if not failures else "FAIL",
        "scope": "local format/grid/range/mask/hash audit only; no organizer authentication or portal acceptance claim",
        "network_access": "none",
        "template": template_info,
        "manifest_sha256": sha256_file(manifest_path),
        "checks": checks,
        "failures": failures,
        "check_count": len(checks),
    }
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    for row in checks:
        print(("PASS " if row["pass"] else "FAIL ") + row["check"] + ": " + row["detail"])
    print(json.dumps({"status": report["status"], "check_count": len(checks), "failures": failures,
                      "report": str(out_path)}, indent=2))
    print(f"\n{len(failures)} failure(s)")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
