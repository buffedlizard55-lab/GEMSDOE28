#!/usr/bin/env python3
"""Independent local audit of all manual GeoTIFF/ZIP research downloads.

This script performs no network requests and never accesses DrivenData. It checks exact local hashes,
bytes, content-addressed names, single-band float32 format, template grid, inside-footprint finiteness
and [0,1] range, variant-specific outside-footprint/nodata semantics, catalogue overlap, ZIP membership,
and note length. It does not prove organizer authenticity or guarantee portal acceptance.
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
        try:
            template_label = str(template_path.resolve().relative_to(ROOT))
        except ValueError:
            template_label = str(template_path)
        template_info = {
            "path": template_label, "sha256": sha256_file(template_path),
            "crs": template.crs.to_string(), "shape": list(template.shape),
            "transform": list(tuple(template.transform)[:6]), "footprint_pixels": int(footprint.sum()),
        }
    with rasterio.open(labels_path) as label_ds:
        labels = label_ds.read(1)
        label_grid_ok = (label_ds.crs, label_ds.shape, label_ds.transform) == template_signature
        catalogue = np.isfinite(labels) & (labels > 0)
        catalogue_pixels = int(catalogue.sum())
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

    def audit_named_variant(prefix: str, item: dict, *, archive_entry: bool = False) -> np.ndarray | None:
        """Audit a filename-style TIFF using its declared footprint/nodata variant."""
        filename = str(item.get("filename", ""))
        variant = item.get("variant", "allfinite")
        variant_ok = variant in {"nan", "allfinite"}
        check(variant_ok, f"{prefix}_variant", str(variant))
        if not variant_ok:
            variant = "allfinite"

        safe_name = bool(filename and Path(filename).name == filename)
        match = re.fullmatch(r".+-([0-9a-f]{12})-(nan|allfinite)\.tif", filename)
        check(safe_name and match is not None, f"{prefix}_safe_content_addressed_name", filename)
        if match:
            check(match.group(2) == variant, f"{prefix}_filename_variant_matches", filename)
            registered_cid = item.get("content_id")
            if registered_cid is not None:
                check(registered_cid == match.group(1), f"{prefix}_content_id_matches_filename", filename)
        path = downloads_dir / filename if safe_name else downloads_dir / "__invalid__"
        check(path.is_file(), f"{prefix}_file_exists", filename)
        if not path.is_file():
            return None

        actual_bytes = path.stat().st_size
        actual_sha = sha256_file(path)
        expected_sha = item.get("sha256")
        check(isinstance(expected_sha, str) and bool(re.fullmatch(r"[0-9a-f]{64}", expected_sha))
              and actual_sha == expected_sha, f"{prefix}_exact_sha256", actual_sha)
        if item.get("bytes") is not None or archive_entry:
            check(isinstance(item.get("bytes"), int) and not isinstance(item.get("bytes"), bool)
                  and actual_bytes == item.get("bytes"), f"{prefix}_byte_count", f"{actual_bytes} bytes")

        with rasterio.open(path) as src:
            arr = src.read(1)
            grid_match = (src.crs, src.shape, src.transform) == template_signature
            one_band_float32 = src.count == 1 and src.dtypes[0] == "float32"
            if src.nodata is None:
                observed_nodata = "none"
            elif np.isnan(src.nodata):
                observed_nodata = "nan"
            else:
                observed_nodata = "other"
        check(grid_match, f"{prefix}_exact_grid", "CRS/shape/transform match template")
        check(one_band_float32, f"{prefix}_single_band_float32", f"dtype={arr.dtype}")

        expected_nodata = item.get("nodata_tag", "nan" if variant == "nan" else "none")
        check(expected_nodata in {"nan", "none"} and observed_nodata == expected_nodata,
              f"{prefix}_nodata_tag_matches", f"registered={expected_nodata}; actual={observed_nodata}")
        inside = arr[footprint]
        outside = arr[~footprint]
        inside_finite = bool(np.isfinite(inside).all())
        inside_range = bool(inside_finite and inside.min() >= 0.0 and inside.max() <= 1.0)
        inside_binary = bool(inside_finite and np.isin(inside, [0.0, 1.0]).all())
        emitted = int((inside == 1.0).sum()) if inside_finite else -1
        overlap = int(((arr > 0) & catalogue & footprint).sum())
        check(inside_finite, f"{prefix}_inside_finite", "all template-footprint cells are finite")
        if item.get("footprint_pixels") is not None or archive_entry:
            check(isinstance(item.get("footprint_pixels"), int)
                  and not isinstance(item.get("footprint_pixels"), bool)
                  and int(footprint.sum()) == item.get("footprint_pixels"),
                  f"{prefix}_footprint_pixel_count", f"template footprint={int(footprint.sum())} cells")
        check(inside_range, f"{prefix}_inside_0_1", "finite template-footprint values lie in [0,1]")
        check(inside_binary, f"{prefix}_inside_exact_binary", "inside values are exactly 0 or 1")
        check(not bool(np.isinf(arr).any()), f"{prefix}_no_infinities", "no infinity anywhere")
        check(overlap == 0, f"{prefix}_no_catalogue_overlap", f"positive catalogue overlap={overlap}")
        if item.get("catalogue_overlap_px") is not None or archive_entry:
            check(isinstance(item.get("catalogue_overlap_px"), int)
                  and not isinstance(item.get("catalogue_overlap_px"), bool)
                  and overlap == item.get("catalogue_overlap_px"),
                  f"{prefix}_catalogue_overlap_count", f"positive catalogue overlap={overlap}")
        if item.get("emitted_px") is not None or archive_entry:
            check(isinstance(item.get("emitted_px"), int) and not isinstance(item.get("emitted_px"), bool)
                  and emitted == item.get("emitted_px"), f"{prefix}_emitted_count",
                  f"{emitted} inside-footprint cells equal 1.0")

        if variant == "nan":
            outside_ok = bool(np.isnan(outside).all() and observed_nodata == "nan")
            check(outside_ok, f"{prefix}_outside_nan", "outside footprint is NaN and nodata tag is NaN")
        else:
            whole_range = bool(np.isfinite(arr).all() and arr.min() >= 0.0 and arr.max() <= 1.0)
            outside_zero = bool((outside == 0.0).all())
            check(whole_range, f"{prefix}_strict_whole_array_0_1",
                  "all array values, including outside-footprint cells, are finite and in [0,1]")
            check(outside_zero, f"{prefix}_outside_zero", "outside-footprint cells are exactly zero")
            check(observed_nodata in {"none", "nan"}, f"{prefix}_allfinite_nodata_metadata",
                  f"all pixels are finite; nodata tag is {observed_nodata} (explicitly registered)")
        return arr

    # Audit every filename-style artifact, including future/concurrent sessions.
    # A hardcoded s18_candidate here silently omitted s19_candidate.
    for slot, current in manifest.items():
        if not isinstance(current, dict) or "filename" not in current:
            continue
        prefix = slot.removesuffix("_candidate")
        audit_named_variant(prefix, current)
        note = current.get("note")
        check(isinstance(note, str) and 0 < len(note) <= 140, f"{prefix}_note_140", str(note))
        if current.get("verdict") == "negative":
            check(current.get("submission_ready") is False,
                  f"{prefix}_rejected_not_approved", str(current.get("status")))

    legacy = manifest.get("legacy_archive", {})
    legacy = legacy if isinstance(legacy, dict) else {}
    archive_entries = legacy.get("entries", [])
    archive_entries = archive_entries if isinstance(archive_entries, list) else []
    expected_archive_count = legacy.get("expected_entry_count")
    check(isinstance(expected_archive_count, int) and not isinstance(expected_archive_count, bool)
          and len(archive_entries) == expected_archive_count,
          "legacy_archive_expected_entry_count",
          f"registered={len(archive_entries)}; expected={expected_archive_count}")
    archive_ids = [entry.get("id") for entry in archive_entries if isinstance(entry, dict)]
    check(len(archive_ids) == len(archive_entries) and len(archive_ids) == len(set(archive_ids)),
          "legacy_archive_ids_unique", f"{len(archive_ids)} archive entry ID(s)")
    archive_filenames = [entry.get("filename") for entry in archive_entries if isinstance(entry, dict)]
    check(len(archive_filenames) == len(archive_entries)
          and len(archive_filenames) == len(set(archive_filenames)),
          "legacy_archive_filenames_unique", f"{len(archive_filenames)} archive TIFF reference(s)")
    expected_pair_count = legacy.get("expected_pair_count")
    pair_groups: dict[str, list[tuple[dict, str | None]]] = {}
    for entry in archive_entries:
        if not isinstance(entry, dict):
            check(False, "legacy_archive_entry_object", repr(entry))
            continue
        entry_id = str(entry.get("id", "entry"))
        prefix = "legacy_archive_" + re.sub(r"[^A-Za-z0-9_]+", "_", entry_id).strip("_")
        array = audit_named_variant(prefix, entry, archive_entry=True)
        check(entry.get("disposition") == "research_only_not_submission_approved",
              f"{prefix}_research_only", str(entry.get("disposition")))
        check(entry.get("submission_ready") is False, f"{prefix}_not_submission_ready",
              str(entry.get("submission_ready")))
        check(entry.get("provenance_status") == "local_records_not_independent_authentication",
              f"{prefix}_provenance_disclosure", str(entry.get("provenance_status")))
        source_records = entry.get("source_records")
        sources_ok = isinstance(source_records, list) and bool(source_records)
        if sources_ok:
            for source_record in source_records:
                if not isinstance(source_record, str):
                    sources_ok = False
                    break
                source_path = (ROOT / source_record).resolve()
                if not source_path.is_relative_to(ROOT.resolve()) or not source_path.is_file():
                    sources_ok = False
                    break
        check(sources_ok, f"{prefix}_local_source_records_exist",
              ", ".join(str(value) for value in source_records) if isinstance(source_records, list)
              else "source_records must be a nonempty list")
        pair_id = entry.get("pair_id")
        if expected_pair_count is not None:
            check(isinstance(pair_id, str) and bool(pair_id), f"{prefix}_pair_id", str(pair_id))
            if isinstance(pair_id, str) and pair_id:
                inside_digest = (hashlib.sha256(array[footprint].tobytes()).hexdigest()
                                 if array is not None else None)
                pair_groups.setdefault(pair_id, []).append((entry, inside_digest))

    if expected_pair_count is not None:
        check(isinstance(expected_pair_count, int) and not isinstance(expected_pair_count, bool)
              and len(pair_groups) == expected_pair_count,
              "legacy_archive_expected_pair_count",
              f"registered={len(pair_groups)}; expected={expected_pair_count}")
        for pair_id, members in pair_groups.items():
            pair_prefix = "legacy_archive_pair_" + re.sub(r"[^A-Za-z0-9_]+", "_", pair_id).strip("_")
            variants = [item.get("variant") for item, _ in members]
            variants_ok = (len(variants) == 2 and variants.count("nan") == 1
                           and variants.count("allfinite") == 1)
            check(variants_ok, f"{pair_prefix}_variant_membership",
                  ", ".join(str(variant) for variant in variants))
            content_ids = {item.get("content_id") for item, _ in members}
            check(len(content_ids) == 1, f"{pair_prefix}_content_id_consistency", repr(content_ids))
            inside_digests = [digest for _, digest in members]
            check(len(inside_digests) == 2 and None not in inside_digests
                  and len(set(inside_digests)) == 1, f"{pair_prefix}_same_inside_footprint_bytes",
                  "NaN and all-finite variants encode the same ordered template-footprint values")

    names = [path.name for path in downloads_dir.glob("*.tif")]
    registered_references = []
    for item in manifest.values():
        if isinstance(item, dict):
            # A single filename-style candidate can name its all-finite TIFF via
            # both `filename` and `allfinite`; count that alias only once.
            item_references = {
                item[key] for key in ("nan", "allfinite", "filename")
                if isinstance(item.get(key), str)
            }
            registered_references.extend(sorted(item_references))
    registered_references.extend(
        entry["filename"] for entry in archive_entries
        if isinstance(entry, dict) and isinstance(entry.get("filename"), str)
    )
    registered_names = set(registered_references)
    unregistered = sorted(set(names) - registered_names)
    check(len(registered_references) == len(registered_names), "manifest_tif_references_unique",
          f"{len(registered_references)} registered TIFF references; {len(registered_names)} unique")
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
        "labels": {"path": str(labels_path), "sha256": sha256_file(labels_path),
                   "catalogue_positive_pixels": catalogue_pixels},
        "archive_coverage": {
            "download_tif_count": len(names),
            "registered_tif_count": len(registered_names),
            "unregistered_tif_count": len(unregistered),
            "unregistered_files": unregistered,
            "legacy_archive_entry_count": len(archive_entries),
            "legacy_archive_expected_entry_count": expected_archive_count,
            "legacy_archive_pair_count": len(pair_groups),
            "legacy_archive_expected_pair_count": expected_pair_count,
        },
        "manifest_sha256": sha256_file(manifest_path),
        "validator_sha256": sha256_file(Path(__file__).resolve()),
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
