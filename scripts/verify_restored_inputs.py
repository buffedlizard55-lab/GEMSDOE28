#!/usr/bin/env python3
"""Fail-closed local hash/grid audit for the hash-pinned owner mirrors in registry/data_manifest.json.

No network calls are made. This validates local bytes and internal GeoTIFF consistency only; it does
not authenticate the owner mirrors as organizer downloads or prove the competition portal accepts them.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=os.environ.get("GEMS_DATA_DIR", str(ROOT / "data")))
    parser.add_argument("--manifest", default=str(ROOT / "registry" / "data_manifest.json"))
    parser.add_argument("--out", default=None, help="optional path to write the JSON report")
    args = parser.parse_args()
    data_dir = Path(args.data_dir).resolve()
    manifest_path = Path(args.manifest).resolve()
    manifest = json.loads(manifest_path.read_text())
    expected_manifest = json.loads((ROOT / "registry" / "data_manifest.json").read_text())
    if manifest != expected_manifest:
        raise SystemExit("Data manifest differs from the reviewed registry/data_manifest.json")
    copied_manifest = data_dir / "manifest.json"
    if copied_manifest.exists() and json.loads(copied_manifest.read_text()) != expected_manifest:
        raise SystemExit("data/manifest.json differs from the reviewed registry manifest")

    records = []
    errors = []
    for entry in manifest["files"]:
        path = data_dir / entry["dest"]
        if not path.is_file():
            errors.append(f"missing: {path}")
            continue
        size = path.stat().st_size
        digest = sha256_file(path)
        ok = size == entry["bytes"] and digest == entry["sha256"]
        records.append({"id": entry["id"], "path": str(path.relative_to(data_dir)),
                        "bytes": size, "sha256": digest, "pass": ok,
                        "provenance": entry["provenance"]})
        if not ok:
            errors.append(f"hash/size mismatch: {entry['id']}")
    if errors:
        raise SystemExit("Input hash audit failed: " + "; ".join(errors))

    template_path = data_dir / "sample_submission.tif"
    training_path = data_dir / "training_features.tif"
    labels_path = data_dir / "labels.tif"
    lidar_path = data_dir / "lidar_scarp_features_u8.tif"
    with rasterio.open(template_path) as t:
        foot = np.isfinite(t.read(1))
        ref = (t.shape, t.crs, t.transform)
        grid = {"shape": list(t.shape), "crs": t.crs.to_string(),
                "transform": list(tuple(t.transform)[:6]), "footprint_pixels": int(foot.sum())}
    with rasterio.open(training_path) as source:
        if (source.shape, source.crs, source.transform) != ref:
            raise SystemExit("Training GeoTIFF grid differs from sample template")
        if source.count != 19:
            raise SystemExit(f"Expected 19 training bands, got {source.count}")
        expected_names = ["mag_anom", "rtp", "tmi_hg", "geod_2ndinv", "iso_grav_anom_slope", "tc",
                          "geod_shearrate", "geod_dilaterate", "tmi_vg", "deq_n100a15", "iso_grav_anom_vg",
                          "det_elev", "iso_grav_anom", "tmi", "depth_to_base_surf", "ieq_n100a15",
                          "cond_surf", "iso_grav_anom_hg", "det_elev_slope"]
        actual_names = [(name or "").split(" - ")[0].strip() for name in source.descriptions]
        if actual_names != expected_names:
            raise SystemExit("Training band descriptions differ from the audited band order")
    for path in (labels_path,):
        with rasterio.open(path) as ds:
            if (ds.shape, ds.crs, ds.transform) != ref:
                raise SystemExit(f"{path.name} grid differs from sample template")
            a = ds.read(1)
            if not np.isfinite(a[foot]).all() or not np.isin(a[foot], (0, 1)).all():
                raise SystemExit(f"{path.name} has invalid in-footprint labels")
    with rasterio.open(lidar_path) as ds:
        if (ds.shape, ds.crs, ds.transform) != ref or ds.count != 12:
            raise SystemExit("LiDAR descriptor grid or band count differs from its pinned contract")

    prepared_path = data_dir / "prepared" / "features.npy"
    prepared_meta_path = data_dir / "prepared" / "features.json"
    if not prepared_path.is_file() or not prepared_meta_path.is_file():
        raise SystemExit("Prepared feature matrix/report missing; prepare_data.py did not finish")
    prepared_meta = json.loads(prepared_meta_path.read_text())
    prepared = np.load(prepared_path, mmap_mode="r")
    if (prepared.dtype != np.dtype("float32") or prepared.shape != (int(foot.sum()), 32)
            or sha256_file(prepared_path) != prepared_meta.get("sha256")
            or prepared_meta.get("inputs", {}).get("template") != sha256_file(template_path)
            or prepared_meta.get("inputs", {}).get("training_features") != sha256_file(training_path)):
        raise SystemExit("Prepared feature matrix shape, dtype or input hashes are inconsistent")

    report = {
        "status": "PASS: local hashes, grid, band order, and prepared matrix verified",
        "provenance_warning": manifest["provenance_warning"],
        "data_dir": str(data_dir),
        "files_verified": records,
        "grid": grid,
        "prepared_features": {
            "path": str(prepared_path.relative_to(data_dir)),
            "shape": list(prepared.shape), "dtype": str(prepared.dtype),
            "sha256": prepared_meta["sha256"],
        },
        "network_access": "none",
        "scope": "integrity-only local audit; not proof of organizer authenticity, coverage, licensing, or portal acceptance",
    }
    serialized = json.dumps(report, indent=2) + "\n"
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(serialized)
    print(serialized, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
