#!/usr/bin/env python3
"""Build the frozen, label-free H38-1 Euler × gravity × low-relief candidate list.

This is an evidence-preparation step only. It never opens labels.tif, allocates holdout seeds, fits a
model, scores a prediction, contacts a network service, or builds a submission raster. Its rule is
specified in knowledge/38_preregistration_H38-1.md.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, h38_1, paths  # noqa: E402


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(tmp, path)


def validate_grid(reference: rasterio.io.DatasetReader, dataset: rasterio.io.DatasetReader, label: str) -> None:
    if dataset.crs != reference.crs:
        raise ValueError(f"{label} CRS differs from the template")
    if dataset.shape != reference.shape:
        raise ValueError(f"{label} shape differs from the template")
    if dataset.transform != reference.transform:
        raise ValueError(f"{label} geotransform differs from the template")


def expected_description(dataset: rasterio.io.DatasetReader, band: int, token: str, label: str) -> str:
    description = dataset.descriptions[band - 1]
    if description is None or not description.lower().startswith(token.lower()):
        raise ValueError(f"{label} band {band} description is {description!r}, expected {token!r}")
    return description


def build(args: argparse.Namespace) -> dict:
    feature_path = Path(args.training_features)
    template_path = Path(args.template)
    lidar_path = Path(args.lidar)
    clusters_path = Path(args.euler_clusters)
    candidate_path = Path(args.candidate_csv)
    audit_path = Path(args.audit_json)
    input_paths = [feature_path, template_path, lidar_path, clusters_path]
    missing = [str(p) for p in input_paths if not p.is_file()]
    if missing:
        raise FileNotFoundError(f"required local data/evidence missing: {missing}")

    with rasterio.open(template_path) as template_ds:
        footprint = grid.load_footprint(template_path)
        for path in (feature_path, lidar_path):
            with rasterio.open(path) as ds:
                validate_grid(template_ds, ds, path.name)

    with rasterio.open(feature_path) as ds:
        if ds.count < h38_1.GRAVITY_BAND:
            raise ValueError("training feature raster does not contain the frozen gravity band")
        gravity_desc = expected_description(ds, h38_1.GRAVITY_BAND,
                                            "iso_grav_anom_hg", "training features")
        gravity = ds.read(h38_1.GRAVITY_BAND)

    with rasterio.open(lidar_path) as ds:
        if ds.count < h38_1.LIDAR_VALID_BAND:
            raise ValueError("LiDAR descriptor raster does not contain the frozen bands")
        relief_desc = expected_description(ds, h38_1.RELIEF_BAND, "relief", "LiDAR descriptors")
        valid_desc = expected_description(ds, h38_1.LIDAR_VALID_BAND, "valid", "LiDAR descriptors")
        relief = ds.read(h38_1.RELIEF_BAND)
        validity = ds.read(h38_1.LIDAR_VALID_BAND)
    if validity.dtype != np.uint8:
        raise ValueError(f"LiDAR validity band must be uint8 fraction, got {validity.dtype}")

    support, support_audit = h38_1.candidate_support_mask(
        gravity, relief, validity > 0, footprint,
    )
    fields, chosen, cluster_audit = h38_1.read_and_select_clusters(clusters_path, support)
    h38_1.write_candidate_csv(candidate_path, fields, chosen)

    files = {
        "template": {"path": str(template_path.relative_to(ROOT)) if template_path.is_relative_to(ROOT)
                     else str(template_path), "sha256": sha256_file(template_path)},
        "training_features": {"path": str(feature_path.relative_to(ROOT)) if feature_path.is_relative_to(ROOT)
                              else str(feature_path), "sha256": sha256_file(feature_path)},
        "lidar_descriptors": {"path": str(lidar_path.relative_to(ROOT)) if lidar_path.is_relative_to(ROOT)
                              else str(lidar_path), "sha256": sha256_file(lidar_path)},
        "euler_clusters": {"path": str(clusters_path.relative_to(ROOT)) if clusters_path.is_relative_to(ROOT)
                           else str(clusters_path), "sha256": sha256_file(clusters_path)},
    }
    output_rel = candidate_path.relative_to(ROOT).as_posix() if candidate_path.is_relative_to(ROOT) else str(candidate_path)
    record = {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": cluster_audit["sufficiency"],
        "hypothesis": "H38-1: shallow SI-0 Euler contact candidate within 200 m of a high gravity-gradient cell and in low local relief",
        "interpretation": "label-free data-support audit only; not a holdout result, fault identification, or score estimate",
        "labels_read": False,
        "holdout_seeds_allocated": False,
        "network_access": "none",
        "data_authentication": "input rasters restored from hash-pinned owner mirrors; hashes establish byte integrity only, not organizer provenance",
        "grid": {
            "crs": "EPSG:32611",
            "shape": list(footprint.shape),
            "pixel_size_m": 100,
            "footprint_cells": int(footprint.sum()),
        },
        "rule": {
            "euler": "SI-0 cluster row and col rounded to nearest grid cell; depth_mad_m <= 60 m; median_depth_m <= 400 m; n_solutions >= 8",
            "gravity": f"training_features band {h38_1.GRAVITY_BAND} ({gravity_desc}); threshold is the {h38_1.GRAVITY_QUANTILE:.0%} linear quantile of finite in-footprint values; candidate centroid within {h38_1.GRAVITY_RADIUS_PX:g} pixels ({h38_1.GRAVITY_RADIUS_PX * 100:g} m) of any threshold-exceeding cell",
            "relief": f"LiDAR band {h38_1.RELIEF_BAND} ({relief_desc}); value <= {h38_1.RELIEF_QUANTILE:.0%} linear quantile over valid in-footprint cells; validity band {h38_1.LIDAR_VALID_BAND} ({valid_desc}) > 0",
            "minimum_candidate_count_for_holdout": h38_1.MIN_CANDIDATES_FOR_HOLDOUT,
        },
        "support": support_audit,
        "clusters": cluster_audit,
        "inputs": files,
        "outputs": {
            "candidate_csv": {"path": output_rel, "sha256": sha256_file(candidate_path),
                              "row_count": len(chosen)},
            "builder_sha256": sha256_file(Path(__file__).resolve()),
            "module_sha256": sha256_file(ROOT / "src" / "gems27" / "h38_1.py"),
        },
        "score_or_labels_used_to_choose_thresholds": False,
    }
    atomic_json(audit_path, record)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--training-features", type=Path, default=paths.TRAINING)
    parser.add_argument("--template", type=Path, default=paths.TEMPLATE)
    parser.add_argument("--lidar", type=Path, default=paths.LIDAR)
    parser.add_argument("--euler-clusters", type=Path,
                        default=paths.EVIDENCE / "h31_1_euler_clusters.csv")
    parser.add_argument("--candidate-csv", type=Path,
                        default=paths.EVIDENCE / "h38_1_candidate_clusters.csv")
    parser.add_argument("--audit-json", type=Path,
                        default=paths.EVIDENCE / "h38_1_sufficiency_audit.json")
    args = parser.parse_args()
    record = build(args)
    print(json.dumps({
        "status": record["status"],
        "candidate_clusters": record["clusters"]["selected_clusters"],
        "minimum_for_holdout": h38_1.MIN_CANDIDATES_FOR_HOLDOUT,
        "gravity_threshold": record["support"]["gravity_threshold"],
        "relief_threshold": record["support"]["relief_threshold"],
        "candidate_csv": record["outputs"]["candidate_csv"],
        "audit": str(args.audit_json),
    }, indent=2))
    return 0 if record["status"] == "READY" else 3


if __name__ == "__main__":
    raise SystemExit(main())
