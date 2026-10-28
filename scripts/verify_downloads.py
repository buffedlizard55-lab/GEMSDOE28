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
    labels_path = data_dir / "labels.tif"

    def fail_early(reason: str) -> int:
        # Replace any prior green report, even when required inputs are unreadable.
        report = {"checked_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                  "status": "FAIL", "scope": "input validation failed; no TIFF was approved",
                  "network_access": "none", "checks": [{"check": "inputs_readable", "pass": False,
                                                          "detail": reason}],
                  "failures": ["inputs_readable"], "check_count": 1}
        output = Path(args.out)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
        print(f"FAIL inputs_readable: {reason}")
        return 1

    try:
        manifest = json.loads(manifest_path.read_text())
        if not isinstance(manifest, dict):
            raise ValueError("manifest must be an object")
        if not template_path.is_file() or not labels_path.is_file():
            raise ValueError(f"template or labels missing: {template_path}, {labels_path}")
    except (OSError, ValueError) as exc:
        return fail_early(str(exc))

    failures: list[str] = []
    checks: list[dict] = []

    def check(condition: bool, name: str, detail: str) -> None:
        checks.append({"check": name, "pass": bool(condition), "detail": detail})
        if not condition:
            failures.append(name)

    try:
        with rasterio.open(template_path) as template:
            template_array = template.read(1)
            footprint = np.isfinite(template_array)
            if not footprint.any() or template.crs is None:
                raise ValueError("template needs a CRS and a nonempty finite footprint")
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
    except (OSError, rasterio.errors.RasterioError, IndexError, ValueError) as exc:
        return fail_early(str(exc))
    check(label_grid_ok, "labels_grid_matches_template", f"{labels_path.name} grid matches {template_path.name}")
    check(int(footprint.sum()) == 5_167_373 and template_info["shape"] == [3730, 3292]
          and template_info["crs"] == "EPSG:32611", "expected_template_grid",
          f"{template_info['crs']} {template_info['shape']}; footprint={footprint.sum():,}")

    # Audit every manifest slot that names a NaN-variant GeoTIFF. The slot list
    # was previously hardcoded ("s15_candidate", "s16_candidate", ...), which
    # silently skipped Session 18's s18_candidate: a green 307-check audit that
    # never touched the newest file. Enumerating the manifest fixes the class
    # of bug, not just this instance (Session 18, knowledge/53).
    candidates = [(slot, item) for slot, item in manifest.items()
                  if isinstance(item, dict) and item.get("nan")]
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
        if item.get("archive_only") is True:
            check(item.get("submission_ready") is False and item.get("verdict") == "negative",
                  f"{slot}_research_archive_not_approved", "Archived research is never upload approval")
        content_id = str(item.get("content_id", ""))
        nan_name = str(item["nan"])
        safe_nan = Path(nan_name).name == nan_name and nan_name.endswith(".tif")
        check(safe_nan, f"{slot}_nan_safe_filename", nan_name)
        if not safe_nan:
            continue
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
        try:
            with rasterio.open(nan_path) as dataset:
                arr = dataset.read(1)
                grid_match = (dataset.crs, dataset.shape, dataset.transform) == template_signature
                one_band = dataset.count == 1 and dataset.dtypes[0] == "float32"
                nodata_is_nan = dataset.nodata is not None and np.isnan(dataset.nodata)
        except (OSError, rasterio.errors.RasterioError, IndexError, ValueError) as exc:
            check(False, f"{slot}_nan_readable", str(exc))
            continue
        check(grid_match, f"{slot}_nan_grid", "CRS/shape/transform equal the sample template")
        check(one_band, f"{slot}_nan_single_band_float32", f"count=1 dtype={arr.dtype}")
        if arr.shape != footprint.shape:
            # Do not index a mismatched array or silently resample it.
            continue
        inside = arr[footprint]
        outside = arr[~footprint]
        inside_finite = bool(np.isfinite(inside).all())
        inside_range = bool(inside_finite and inside.min() >= 0.0 and inside.max() <= 1.0)
        values_binary = bool(inside_finite and set(np.unique(inside).tolist()) <= {0.0, 1.0})
        outside_nan = bool(np.isnan(outside).all() and nodata_is_nan)
        overlap = int(((arr > 0) & catalogue & footprint).sum()) if label_grid_ok else None
        emitted = int((inside == 1.0).sum()) if inside_finite else -1
        check(inside_finite, f"{slot}_nan_inside_finite", f"nonfinite inside={int((~np.isfinite(inside)).sum())}")
        check(inside_range, f"{slot}_nan_inside_0_1", f"finite inside range=[{np.nanmin(inside):g}, {np.nanmax(inside):g}]")
        check(values_binary, f"{slot}_nan_exact_binary", "inside values are exactly 0.0 or 1.0")
        check(outside_nan, f"{slot}_nan_outside_nan", f"outside NaN count={int(np.isnan(outside).sum())}/{outside.size}; nodata=NaN")
        check(emitted == item.get("emitted_px"), f"{slot}_nan_emitted_count", f"{emitted} cells equal 1.0")
        check(overlap == 0, f"{slot}_nan_no_catalogue_overlap", f"positive catalogue overlap={overlap}")
        check(not bool(np.isinf(arr).any()), f"{slot}_nan_no_infinities", "no infinity anywhere")

        allfinite_name = item.get("allfinite")
        safe_fallback = False
        if allfinite_name:
            safe_fallback = (isinstance(allfinite_name, str) and Path(allfinite_name).name == allfinite_name
                             and allfinite_name.endswith(".tif"))
            check(safe_fallback, f"{slot}_allfinite_safe_filename", str(allfinite_name))
            fallback = downloads_dir / allfinite_name if safe_fallback else downloads_dir / "__invalid__"
            fallback_ok = safe_fallback and fallback.is_file()
            check(fallback_ok, f"{slot}_allfinite_file_exists", str(allfinite_name))
            if fallback_ok:
                check(bool(re.search(rf"-{re.escape(content_id)}-allfinite\.tif$", allfinite_name)),
                      f"{slot}_allfinite_content_addressed_name", str(allfinite_name))
                check(fallback.stat().st_size == item.get("bytes_allfinite"),
                      f"{slot}_allfinite_byte_count", f"{fallback.stat().st_size} bytes")
                check(sha256_file(fallback) == item.get("sha256_allfinite"),
                      f"{slot}_allfinite_sha256", sha256_file(fallback))
                try:
                    with rasterio.open(fallback) as dataset:
                        fallback_arr = dataset.read(1)
                        fallback_grid = (dataset.crs, dataset.shape, dataset.transform) == template_signature
                        fallback_type = dataset.count == 1 and dataset.dtypes[0] == "float32"
                        no_nodata = dataset.nodata is None
                except (OSError, rasterio.errors.RasterioError, IndexError, ValueError) as exc:
                    check(False, f"{slot}_allfinite_readable", str(exc))
                    continue
                if fallback_arr.shape != footprint.shape:
                    check(False, f"{slot}_allfinite_grid_and_type", "fallback shape differs from template")
                    continue
                fin = fallback_arr[footprint]
                fout = fallback_arr[~footprint]
                check(fallback_grid and fallback_type, f"{slot}_allfinite_grid_and_type", "single float32 band on exact template grid")
                check(bool(np.isfinite(fallback_arr).all() and np.isfinite(fin).all() and fin.min() >= 0 and fin.max() <= 1),
                      f"{slot}_allfinite_range", f"whole array finite; inside range=[{fin.min():g},{fin.max():g}]")
                check(bool((fout == 0).all() and no_nodata), f"{slot}_allfinite_outside_zero", "outside zero; no nodata tag")
                check(int((fin == 1.0).sum()) == item.get("emitted_px"), f"{slot}_allfinite_emitted_count", f"{int((fin == 1.0).sum())} cells equal 1.0")
                check(bool(np.array_equal(inside, fin)), f"{slot}_variant_footprint_values_equal",
                      "NaN and all-finite variants contain identical prediction values on every footprint cell")
                check(label_grid_ok and int(((fallback_arr > 0) & catalogue & footprint).sum()) == 0,
                      f"{slot}_allfinite_no_catalogue_overlap", "requires aligned labels and no positive known-catalogue overlap")

        zip_name = item.get("zip")
        if zip_name:
            safe_zip = (isinstance(zip_name, str) and Path(zip_name).name == zip_name
                        and zip_name.endswith(".zip"))
            check(safe_zip, f"{slot}_zip_safe_filename", str(zip_name))
            zip_path = downloads_dir / zip_name if safe_zip else downloads_dir / "__invalid__"
            zip_ok = safe_zip and zip_path.is_file()
            check(zip_ok, f"{slot}_zip_exists", str(zip_name))
            if zip_ok:
                check(zip_path.stat().st_size == item.get("bytes_zip"), f"{slot}_zip_byte_count", f"{zip_path.stat().st_size} bytes")
                check(sha256_file(zip_path) == item.get("sha256_zip"), f"{slot}_zip_sha256", sha256_file(zip_path))
                members = []
                zip_member = item.get("zip_member", nan_name)
                valid_member = zip_member == nan_name or (safe_fallback and zip_member == allfinite_name)
                member_path = downloads_dir / zip_member if valid_member else downloads_dir / "__invalid__"
                try:
                    with zipfile.ZipFile(zip_path) as archive:
                        members = archive.namelist()
                        one_tif = bool(valid_member and members == [zip_member])
                        byte_identical = one_tif and member_path.is_file() and archive.read(zip_member) == member_path.read_bytes()
                except (OSError, zipfile.BadZipFile):
                    one_tif = byte_identical = False
                check(one_tif, f"{slot}_zip_single_tif", f"members={members}")
                check(byte_identical, f"{slot}_zip_byte_identical", "single member matches the registered TIFF byte-for-byte")

        note = str(item.get("note", ""))
        note_chars = len(note)
        check(0 < note_chars <= 200, f"{slot}_note_length", f"{note_chars} chars; max 200")
        note_file = item.get("note_file")
        if note_file:
            safe_note = isinstance(note_file, str) and Path(note_file).name == note_file
            path = downloads_dir / note_file if safe_note else downloads_dir / "__invalid__"
            check(safe_note and path.is_file() and path.read_text(encoding="utf-8").strip() == note,
                  f"{slot}_note_file_matches", str(note_file))

    # Audit every filename-style artifact, including future/concurrent sessions.
    # A hardcoded s18_candidate here silently omitted s19_candidate.
    for slot, current in manifest.items():
        if not isinstance(current, dict) or "filename" not in current:
            continue
        prefix = slot.removesuffix("_candidate")
        filename = str(current.get("filename", ""))
        safe_name = bool(filename and Path(filename).name == filename and filename.endswith(".tif"))
        check(safe_name, f"{prefix}_safe_filename", filename)
        path = downloads_dir / filename if safe_name else downloads_dir / "__invalid__"
        check(path.is_file(), f"{prefix}_file_exists", filename)
        if path.is_file():
            check(sha256_file(path) == current.get("sha256"), f"{prefix}_exact_sha256", sha256_file(path))
            try:
                with rasterio.open(path) as src:
                    arr = src.read(1)
                    check((src.crs, src.shape, src.transform) == template_signature,
                          f"{prefix}_exact_grid", "CRS/shape/transform match template")
                    check(src.count == 1 and src.dtypes[0] == "float32", f"{prefix}_single_band_float32", str(src.dtypes))
            except (OSError, rasterio.errors.RasterioError, IndexError, ValueError) as exc:
                check(False, f"{prefix}_readable", str(exc))
                continue
            if arr.shape != footprint.shape:
                # Grid failure has already been recorded; do not mask/resize it.
                continue
            check(np.isfinite(arr).all() and ((arr >= 0) & (arr <= 1)).all(),
                  f"{prefix}_strict_whole_array_0_1", "No NaN/infinity or out-of-range value anywhere")
            check((arr[~footprint] == 0).all(), f"{prefix}_zero_outside_footprint", "zeros outside footprint")
            check(label_grid_ok and not ((arr > 0) & catalogue & footprint).any(),
                  f"{prefix}_no_catalogue_predictions", "requires aligned labels and no catalogue dots")
        note = current.get("note")
        check(isinstance(note, str) and 0 < len(note) <= 140, f"{prefix}_note_140", str(note))
        if current.get("verdict") == "negative":
            check(current.get("submission_ready") is False,
                  f"{prefix}_rejected_not_approved", str(current.get("status")))

    names = [path.name for path in downloads_dir.glob("*.tif")]
    registered_names = {
        item[key] for item in manifest.values() if isinstance(item, dict)
        for key in ("nan", "allfinite", "filename") if isinstance(item.get(key), str)
    }
    # S27: research-only artifacts registered in a sibling manifest. Read it instead of editing
    # docs/downloads/manifest.json, whose bytes are hash-bound by the S23 evidence record.
    research_path = downloads_dir / "s25_research_manifest.json"
    if research_path.is_file():
        research = json.loads(research_path.read_text())
        for item in research.values():
            if isinstance(item, dict) and isinstance(item.get("file"), str):
                registered_names.add(item["file"])
                if isinstance(item.get("zip"), str):
                    registered_names.add(item["zip"])
                target = downloads_dir / item["file"]
                check(target.is_file() and sha256_file(target) == item.get("sha256_tif"),
                      "s25_research_sha256_matches_registry", item["file"])
    unregistered = sorted(set(names) - registered_names)
    check(not unregistered, "all_tifs_registered_for_audit",
          "Unregistered TIFFs (not fully audited): " + ", ".join(unregistered))
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
