#!/usr/bin/env python3
"""Build H31-1 Euler source-cluster features and run its frozen paired OOF gate.

The --features-only pass is label-free. Model fitting is restricted to the preregistered screen
160-169 and (only after a screen pass) confirmation 170-179. This script never writes a submission TIFF
and never contacts DrivenData. Protocol: knowledge/12_preregistration_H31-1_euler.md.
"""
from __future__ import annotations

# The repository's `src/` and `scripts/` modules are deliberately placed on sys.path below.
# ruff: noqa: E402
import argparse
import csv
import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
import scipy
import sklearn
from scipy.ndimage import distance_transform_edt
from scipy.spatial import cKDTree

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
from gems27 import euler, grid, holdout, links, metric, oof_detector, paths
from gems27.candidates import RULE, SPACING, dedupe_mutual, evidence_score
from gems27.graph import build_graph
from gems27.potential_edges import EDGE_FEATURE_NAMES
from run_h28_1_edge_holdout import (
    _input_hashes as h28_input_hashes,
)
from run_h28_1_edge_holdout import (
    distance_to,
    eval_set,
    load_or_build_edge_matrix,
    validate_prepared_feature_metadata,
)

PROTOCOL_PATH = ROOT / "knowledge" / "12_preregistration_H31-1_euler.md"
FEATURES = paths.PREPARED_FEATURES.parent / "h31_1_euler_features.npy"
FEATURE_META = paths.PREPARED_FEATURES.parent / "h31_1_euler_features.json"
COMBINED = paths.PREPARED_FEATURES.parent / "h31_1_combined_features.npy"
CLUSTER_CSV = ROOT / "evidence" / "h31_1_euler_clusters.csv"
FEATURE_AUDIT = ROOT / "evidence" / "h31_1_euler_feature_audit.json"
SCREEN = ROOT / "evidence" / "h31_1_euler_screen.json"
CONFIRM = ROOT / "evidence" / "h31_1_euler_confirm.json"
SEED_AUDIT = ROOT / "evidence" / "h31_1_seed_reuse_audit.json"
EXPECTED_TMI_BAND = 14
EXPECTED_TMI_NAME = "tmi"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _runtime_versions() -> dict[str, str]:
    return {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "rasterio": rasterio.__version__,
        "scikit_learn": sklearn.__version__,
    }


def _feature_implementation_hashes() -> dict[str, str]:
    """Pin every local helper that influences the label-free Euler feature build."""
    files = {
        "runner": Path(__file__).resolve(),
        "euler_module": ROOT / "src/gems27/euler.py",
        "oof_detector": ROOT / "src/gems27/oof_detector.py",
        "grid": ROOT / "src/gems27/grid.py",
        "paths": ROOT / "src/gems27/paths.py",
        "h28_evaluation_helpers": ROOT / "scripts/run_h28_1_edge_holdout.py",
    }
    return {name: sha256_file(path) for name, path in files.items()}


def _protocol_commit() -> str:
    """Return the commit that last changed the frozen protocol; empty means it is uncommitted."""
    relative = PROTOCOL_PATH.relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", relative],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    commit = result.stdout.strip()
    if not commit:
        return ""
    committed = subprocess.run(
        ["git", "show", f"{commit}:{relative}"], cwd=ROOT, check=True, capture_output=True
    ).stdout
    return commit if hashlib.sha256(committed).hexdigest() == sha256_file(PROTOCOL_PATH) else ""


def _metadata_fingerprint(meta: dict) -> str:
    """Recompute the self-hash written with the metadata's `sha256` slot set to null."""
    check = dict(meta)
    check["sha256"] = None
    payload = json.dumps(check, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def _seed_values(value) -> set[int]:
    """Recursively collect integer values under holdout seed keys from an evidence JSON value."""
    found: set[int] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"seed", "seeds", "holdout_seeds", "used_seeds"}:
                if isinstance(item, int) and not isinstance(item, bool):
                    found.add(item)
                elif isinstance(item, list):
                    found.update(x for x in item if isinstance(x, int) and not isinstance(x, bool))
            found.update(_seed_values(item))
    elif isinstance(value, list):
        for item in value:
            found.update(_seed_values(item))
    return found


def _write_single_use_claim(path: Path, record: dict) -> str:
    """Create a durable, exclusive seed claim; concurrent invocations cannot consume the same range."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = (json.dumps(record, indent=2) + "\n").encode("utf-8")
    try:
        descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise SystemExit(f"Single-use seed claim already exists; this range cannot be rerun: {path}") from exc
    with os.fdopen(descriptor, "wb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    return sha256_file(path)


def _assert_seed_range_unused(seeds: list[int], out_path: Path) -> dict:
    if not SEED_AUDIT.is_file():
        raise SystemExit("Missing evidence/h31_1_seed_reuse_audit.json; audit seed reuse before model fitting")
    audit = json.loads(SEED_AUDIT.read_text())
    if audit.get("sha256") != _metadata_fingerprint(audit):
        raise SystemExit("Seed-reuse audit failed its self-integrity check")
    expected = audit.get("planned_ranges", {}).get("screen" if seeds[0] == 160 else "confirmation", [])
    stage = "screen" if seeds[0] == 160 else "confirmation"
    if audit.get("status") != "PASS" or expected != seeds or audit.get("range_status", {}).get(stage) != "UNUSED":
        raise SystemExit("The saved seed-reuse audit is stale, failed, consumed, or does not match the requested frozen range")
    if (audit.get("protocol", {}).get("sha256") != sha256_file(PROTOCOL_PATH)
            or audit.get("protocol", {}).get("last_modifying_commit") != _protocol_commit()):
        raise SystemExit("Seed-reuse audit was made against a different or uncommitted preregistration")
    evidence_dir = ROOT / "evidence"
    recorded_hashes = audit.get("evidence_json_sha256_scanned", {})
    current_json = {path.name for path in evidence_dir.glob("*.json") if path != SEED_AUDIT}
    if set(recorded_hashes) != current_json:
        raise SystemExit("Seed audit is stale; the set of local evidence JSON files changed since scan")
    if audit.get("audit_script_sha256") != sha256_file(ROOT / "scripts/audit_euler_seed_reuse.py"):
        raise SystemExit("Seed audit was made by a different seed-audit implementation")
    for filename, expected_hash in recorded_hashes.items():
        path = evidence_dir / filename
        if not path.is_file() or sha256_file(path) != expected_hash:
            raise SystemExit(f"Seed audit is stale; evidence changed since scan: {filename}")
    prior = set(audit.get("previously_used_holdout_seeds", []))
    collision = prior.intersection(seeds)
    if collision:
        raise SystemExit(f"Requested holdout seeds already appear in the audited ledger: {sorted(collision)}")
    collisions = []
    for path in sorted((ROOT / "evidence").glob("*.json")):
        if path == SEED_AUDIT or path == out_path:
            continue
        try:
            record = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        overlap = _seed_values(record).intersection(seeds)
        if overlap:
            collisions.append({"file": path.name, "seeds": sorted(overlap)})
    if collisions:
        raise SystemExit(f"Seed reuse collision in current evidence; manual review required: {collisions}")
    return audit


def _array_mask_sha256(mask: np.ndarray) -> str:
    return hashlib.sha256(np.packbits(np.asarray(mask, dtype=np.uint8)).tobytes()).hexdigest()


def _write_cluster_csv(clusters: list[dict], transform, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ["cluster_id", "row", "col", "easting_m", "northing_m", "median_depth_m",
              "depth_mad_m", "depth_min_m", "depth_max_m", "n_solutions", "median_depth_se_m"]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for c in clusters:
            x, y = transform @ (c["col"] + 0.5, c["row"] + 0.5)
            writer.writerow({
                "cluster_id": c["cluster_id"], "row": f"{c['row']:.3f}", "col": f"{c['col']:.3f}",
                "easting_m": f"{x:.2f}", "northing_m": f"{y:.2f}",
                "median_depth_m": f"{c['median_depth_m']:.2f}", "depth_mad_m": f"{c['depth_mad_m']:.2f}",
                "depth_min_m": f"{c['depth_min_m']:.2f}", "depth_max_m": f"{c['depth_max_m']:.2f}",
                "n_solutions": c["n_solutions"], "median_depth_se_m": f"{c['median_depth_se_m']:.2f}",
            })


def _solution_depth_summary(solutions: dict) -> dict:
    depth = np.asarray(solutions["depth_m"], dtype=np.float64)
    se = np.asarray(solutions["depth_se_m"], dtype=np.float64)
    rel = np.asarray(solutions["relative_depth_se"], dtype=np.float64)
    cond = np.asarray(solutions["condition_number"], dtype=np.float64)
    if not len(depth):
        return {"n": 0}
    return {
        "n": int(len(depth)), "depth_m_p10": float(np.percentile(depth, 10)),
        "depth_m_median": float(np.median(depth)), "depth_m_p90": float(np.percentile(depth, 90)),
        "depth_se_m_median": float(np.median(se)), "relative_depth_se_median": float(np.median(rel)),
        "condition_number_median": float(np.median(cond)),
    }


def _cluster_centroid_stability(primary: dict, sensitivity: dict) -> dict:
    a, b = primary["clusters"], sensitivity["clusters"]
    if not a or not b:
        return {"primary_clusters": len(a), "sensitivity_clusters": len(b), "matched_primary_share_within_600m": None}
    a_xy = np.array([[c["col"], c["row"]] for c in a], dtype=np.float64) * 100.0
    b_xy = np.array([[c["col"], c["row"]] for c in b], dtype=np.float64) * 100.0
    dist, _ = cKDTree(b_xy).query(a_xy, k=1, workers=1)
    return {"primary_clusters": len(a), "sensitivity_clusters": len(b),
            "matched_primary_share_within_600m": float(np.mean(dist <= 600.0)),
            "median_nearest_centroid_distance_m": float(np.median(dist))}


def build_euler_features(*, force: bool = False) -> tuple[np.ndarray, dict]:
    """Create the label-free three-column SI-0 cluster feature matrix and audit all steps."""
    foot = grid.load_footprint(paths.TEMPLATE)
    feature_implementation = _feature_implementation_hashes()
    protocol_hash = sha256_file(PROTOCOL_PATH)
    protocol_commit = _protocol_commit()
    if not protocol_commit:
        raise SystemExit("Commit the byte-frozen H31-1 protocol before running any Euler window solve")
    input_hashes = h28_input_hashes()
    expected_shape = (int(foot.sum()), 3)
    solution_archive = paths.PREPARED_FEATURES.parent / "h31_1_euler_solutions_si0.npz"
    if FEATURES.exists() and FEATURE_META.exists() and CLUSTER_CSV.exists() and solution_archive.exists() \
            and FEATURE_AUDIT.exists() and not force:
        try:
            meta = json.loads(FEATURE_META.read_text())
            audit = json.loads(FEATURE_AUDIT.read_text())
            arr = np.load(FEATURES, mmap_mode="r")
            csv_meta = meta.get("cluster_table", {})
            solution_meta = meta.get("solution_archive", {})
            feature_meta = meta.get("feature_matrix", {})
            cache_ok = (
                bool(protocol_commit)
                and meta.get("protocol_commit") == protocol_commit
                and meta.get("protocol_sha256") == protocol_hash
                and meta.get("runtime_versions") == _runtime_versions()
                and meta.get("input_hashes") == input_hashes
                and meta.get("implementation") == feature_implementation
                and meta.get("data_sufficiency_gate", {}).get("passed") is True
                and arr.shape == expected_shape and arr.dtype == np.dtype("float32")
                and feature_meta.get("path") == str(FEATURES.relative_to(ROOT))
                and feature_meta.get("shape") == list(expected_shape)
                and feature_meta.get("dtype") == "float32"
                and sha256_file(FEATURES) == feature_meta.get("sha256")
                and np.isfinite(arr).all() and float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0
                and csv_meta.get("path") == str(CLUSTER_CSV.relative_to(ROOT))
                and csv_meta.get("rows") == meta.get("structural_indices", {}).get("0", {}).get("lineament_cluster_stats", {}).get("retained_cluster_count")
                and csv_meta.get("bytes") == CLUSTER_CSV.stat().st_size
                and csv_meta.get("sha256") == sha256_file(CLUSTER_CSV)
                and solution_meta.get("path") == str(solution_archive.relative_to(ROOT))
                and solution_meta.get("bytes") == solution_archive.stat().st_size
                and solution_meta.get("sha256") == sha256_file(solution_archive)
                and meta.get("sha256") == _metadata_fingerprint(meta)
                and audit == meta
                and audit.get("sha256") == _metadata_fingerprint(audit)
                and audit.get("feature_matrix", {}).get("sha256") == feature_meta.get("sha256")
            )
            if cache_ok:
                return arr, meta
        except (OSError, ValueError, KeyError, json.JSONDecodeError):
            pass

    with rasterio.open(paths.TEMPLATE) as template, rasterio.open(paths.TRAINING) as source:
        if (source.shape, source.crs, source.transform) != (template.shape, template.crs, template.transform):
            raise SystemExit("Magnetic source grid differs from template; refusing resampling")
        name = (source.descriptions[EXPECTED_TMI_BAND - 1] or "").split(" - ")[0].strip()
        tag_name = source.tags(EXPECTED_TMI_BAND).get("band_name", "")
        if name != EXPECTED_TMI_NAME or tag_name != EXPECTED_TMI_NAME:
            raise SystemExit(f"Expected TMI band {EXPECTED_TMI_BAND}/{EXPECTED_TMI_NAME}, found {name!r}/{tag_name!r}")
        field = source.read(EXPECTED_TMI_BAND, out_dtype="float32")
        nodata = source.nodata
        transform = source.transform
        crs = source.crs.to_string()
    valid = foot & np.isfinite(field) & (np.abs(field) < 1e30)
    if nodata is not None:
        valid &= field != np.float32(nodata)

    derivative = euler.magnetic_derivatives(field, valid, nodata=nodata)
    euler_valid = derivative.valid & derivative.horizontal_coverage & derivative.vertical_coverage
    horizontal_magnitude = np.hypot(derivative.gx_east_per_cell, derivative.gy_north_per_cell)
    lineaments = oof_detector.ridge_nms(horizontal_magnitude, euler_valid, sigma=1.0)

    si_solutions = {}
    si_clusters = {}
    for si in (0, 1, 2):
        solutions = euler.solve_euler_windows(
            field, derivative.gx_east_per_cell, derivative.gy_north_per_cell,
            derivative.gz_down_per_cell, euler_valid, structural_index=float(si),
            pixel_size_m=100.0, window_size=10, stride=4, max_condition_number=1e5,
            max_relative_depth_se=0.15, min_depth_m=100.0, max_depth_m=3000.0,
            source_tolerance_px=2.0,
        )
        si_solutions[si] = solutions
        si_clusters[si] = euler.align_and_cluster_solutions(
            solutions, lineaments, pixel_size_m=100.0, alignment_tolerance_m=200.0,
            cluster_eps_m=600.0, min_samples=4, max_depth_mad_m=500.0,
        )

    features_full, feature_description = euler.cluster_feature_maps(
        si_solutions[0], si_clusters[0], derivative.valid, sigma_px=2.0, max_depth_m=3000.0
    )
    flat = np.ascontiguousarray(features_full[foot], dtype=np.float32)
    if flat.shape != expected_shape:
        raise SystemExit(f"Euler features have shape {flat.shape}, expected {expected_shape}")
    partial = FEATURES.with_name(FEATURES.stem + ".partial.npy")
    np.save(partial, flat, allow_pickle=False)
    partial.replace(FEATURES)

    coverage_share = float(derivative.vertical_coverage.sum() / max(int(derivative.valid.sum()), 1))
    primary_solutions = si_solutions[0]
    primary_clusters = si_clusters[0]["clusters"]
    sufficiency = {
        "vertical_derivative_coverage_at_least_0_50": coverage_share >= 0.50,
        "accepted_si0_solutions_at_least_100": len(primary_solutions["row"]) >= 100,
        "retained_si0_clusters_at_least_10": len(primary_clusters) >= 10,
    }
    sufficiency["passed"] = all(sufficiency.values())
    feature_matrix_sha = sha256_file(FEATURES)
    feature_description["sha256"] = feature_matrix_sha
    _write_cluster_csv(primary_clusters, transform, CLUSTER_CSV)
    np.savez_compressed(
        solution_archive,
        row=primary_solutions["row"], col=primary_solutions["col"], depth_m=primary_solutions["depth_m"],
        depth_se_m=primary_solutions["depth_se_m"], relative_depth_se=primary_solutions["relative_depth_se"],
        condition_number=primary_solutions["condition_number"], residual_rms=primary_solutions["residual_rms"],
        singular_values=primary_solutions["singular_values"], offset=primary_solutions["offset"],
        window_row=primary_solutions["window_row"], window_col=primary_solutions["window_col"],
    )
    meta = {
        "schema": 1,
        "status": "label-free Euler source/depth transform; owner-mirror input",
        "checked_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "protocol_path": "knowledge/12_preregistration_H31-1_euler.md",
        "protocol_commit": protocol_commit,
        "protocol_sha256": protocol_hash,
        "runtime_versions": _runtime_versions(),
        "implementation": feature_implementation,
        "input_hashes": input_hashes,
        "grid": {"shape": list(foot.shape), "crs": crs, "transform": list(tuple(transform)[:6]),
                 "footprint_cells": int(foot.sum()), "valid_tmi_cells": int(derivative.valid.sum())},
        "magnetic_band": {"band_1based": EXPECTED_TMI_BAND, "name": name, "tag_name": tag_name,
                          "units": "not present in embedded owner-mirror tags"},
        "derivative": derivative.stats,
        "lineament_ridge_pixels": int(lineaments.sum()),
        "euler_parameters": {"window_size_px": 10, "stride_px": 4, "source_tolerance_px": 2.0,
                             "max_condition_number": 1e5, "max_relative_depth_se": 0.15,
                             "depth_m": [100.0, 3000.0], "candidate_lineament_alignment_m": 200.0,
                             "dbscan_eps_m": 600.0, "dbscan_min_samples": 4,
                             "max_cluster_depth_mad_m": 500.0},
        "structural_indices": {
            str(si): {"solution_summary": _solution_depth_summary(si_solutions[si]),
                      "solver_filters": si_solutions[si]["stats"],
                      "lineament_cluster_stats": si_clusters[si]["stats"]}
            for si in (0, 1, 2)
        },
        "si_cluster_centroid_stability": {
            "si1_vs_si0": _cluster_centroid_stability(si_clusters[0], si_clusters[1]),
            "si2_vs_si0": _cluster_centroid_stability(si_clusters[0], si_clusters[2]),
        },
        "si0_cluster_feature_description": feature_description,
        "data_sufficiency_gate": sufficiency,
        "feature_matrix": {"path": str(FEATURES.relative_to(ROOT)), "shape": list(flat.shape),
                           "dtype": str(flat.dtype), "feature_names": feature_description["feature_names"],
                           "sha256": feature_matrix_sha},
        "cluster_table": {"path": str(CLUSTER_CSV.relative_to(ROOT)), "rows": int(len(primary_clusters)),
                          "bytes": CLUSTER_CSV.stat().st_size, "sha256": sha256_file(CLUSTER_CSV)},
        "solution_archive": {"path": str(solution_archive.relative_to(ROOT)),
                             "bytes": solution_archive.stat().st_size, "sha256": sha256_file(solution_archive)},
        "interpretation_limits": [
            "The owner-mirror feature grid is 100 m, but USGS GeoDAWN metadata describes flight-line spacing of 200 m in Area 1 and 400 m in Area 2.",
            "No unit metadata was present for embedded TMI/derivative bands; Euler gradients here are all derived from one TMI band to avoid mixing uncalibrated component magnitudes.",
            "Euler SI=0 approximates a contact of effectively infinite depth extent; real faults may need SI=1/2 or a different source model. Euler does not estimate dip.",
            "Gradient ridges are used only as a lineament alignment mask. Euler least-squares source coordinates and clusters define the depth-labeled source hypotheses.",
            "Owner-mirror integrity and local grid agreement do not authenticate the bytes as the organizer's official files or prove licensing/coverage.",
        ],
        "sha256": None,
    }
    meta["sha256"] = hashlib.sha256(json.dumps(meta, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    FEATURE_META.write_text(json.dumps(meta, indent=2) + "\n")
    FEATURE_AUDIT.write_text(json.dumps(meta, indent=2) + "\n")
    return np.load(FEATURES, mmap_mode="r"), meta


def build_combined_features(foot: np.ndarray, euler_features: np.ndarray, *, force: bool = False) -> tuple[np.ndarray, dict]:
    edge_matrix, edge_meta = load_or_build_edge_matrix(foot, force=False)
    expected_shape = (int(foot.sum()), len(EDGE_FEATURE_NAMES) + 3)
    if euler_features.shape != (int(foot.sum()), 3):
        raise SystemExit("Euler feature matrix does not align to the row-major footprint")
    code_hash = sha256_file(Path(__file__).resolve())
    edge_hash = sha256_file(paths.PREPARED_FEATURES.parent / "h28_1_edge_features.npy")
    euler_hash = sha256_file(FEATURES)
    if COMBINED.exists() and not force:
        try:
            meta = json.loads(COMBINED.with_suffix(".json").read_text())
            arr = np.load(COMBINED, mmap_mode="r")
            expected_names = list(EDGE_FEATURE_NAMES) + [
                "euler_si0_cluster_support", "euler_si0_shallow_support", "euler_si0_median_depth_norm"
            ]
            if (meta.get("shape") == list(expected_shape) and meta.get("feature_names") == expected_names
                    and meta.get("inputs") == {"edge": edge_hash, "euler": euler_hash}
                    and meta.get("edge_feature_sha256") == edge_meta.get("sha256")
                    and meta.get("runner_sha256") == code_hash and sha256_file(COMBINED) == meta.get("sha256")
                    and arr.shape == expected_shape and arr.dtype == np.dtype("float32")
                    and np.isfinite(arr).all() and float(arr.min()) >= 0.0 and float(arr.max()) <= 1.0):
                return arr, meta
        except (OSError, ValueError, json.JSONDecodeError):
            pass
    partial = COMBINED.with_name(COMBINED.stem + ".partial.npy")
    mm = np.lib.format.open_memmap(partial, mode="w+", dtype=np.float32, shape=expected_shape)
    mm[:, :len(EDGE_FEATURE_NAMES)] = np.asarray(edge_matrix, dtype=np.float32)
    mm[:, len(EDGE_FEATURE_NAMES):] = np.asarray(euler_features, dtype=np.float32)
    mm.flush()
    if not np.isfinite(mm).all() or float(mm.min()) < 0.0 or float(mm.max()) > 1.0:
        del mm
        partial.unlink(missing_ok=True)
        raise SystemExit("Combined 41-column feature matrix must be finite and within [0,1]")
    del mm
    partial.replace(COMBINED)
    meta = {"schema": 1, "feature_names": list(EDGE_FEATURE_NAMES) + [
                "euler_si0_cluster_support", "euler_si0_shallow_support", "euler_si0_median_depth_norm"],
            "shape": list(expected_shape), "inputs": {"edge": edge_hash, "euler": euler_hash},
            "edge_feature_sha256": edge_meta["sha256"], "runner_sha256": code_hash,
            "sha256": sha256_file(COMBINED)}
    COMBINED.with_suffix(".json").write_text(json.dumps(meta, indent=2) + "\n")
    return np.load(COMBINED, mmap_mode="r"), meta


def _minimum_spacing_px(mask: np.ndarray) -> float | None:
    """Return the nearest distinct-pixel distance, or None when fewer than two dots exist."""
    points = np.argwhere(np.asarray(mask, dtype=bool))
    if len(points) < 2:
        return None
    distances, _ = cKDTree(points.astype(np.float64)).query(points, k=2, workers=1)
    return float(np.min(distances[:, 1]))


def _stage_summary(cells: list[dict]) -> dict:
    gains = [r["candidate"]["dti"] - r["control"]["dti"] for r in cells]
    seeds = sorted({int(r["seed"]) for r in cells})
    folds = sorted({r["fold"] for r in cells})
    by_seed = {str(seed): float(np.mean([g for g, r in zip(gains, cells) if r["seed"] == seed])) for seed in seeds}
    by_fold = {fold: float(np.mean([g for g, r in zip(gains, cells) if r["fold"] == fold])) for fold in folds}
    return {
        "mean_paired_gain": float(np.mean(gains)),
        "positive_seed_count": int(sum(v > 0 for v in by_seed.values())),
        "positive_fold_count": int(sum(v > 0 for v in by_fold.values())),
        "gain_by_seed": by_seed,
        "gain_by_fold": by_fold,
        "control_mean_dti": float(np.mean([r["control"]["dti"] for r in cells])),
        "candidate_mean_dti": float(np.mean([r["candidate"]["dti"] for r in cells])),
        "control_mean_dots": float(np.mean([r["control"]["dots"] for r in cells])),
        "candidate_mean_dots": float(np.mean([r["candidate"]["dots"] for r in cells])),
        "cells": int(len(cells)),
    }


def _validate_single_use_claim(report: dict) -> bool:
    """Verify a saved screen's exclusive claim file and every provenance link to the result."""
    info = report.get("single_use_seed_claim")
    if not isinstance(info, dict):
        return False
    claim_path = SCREEN.with_name(SCREEN.stem + ".started.json")
    expected_relative = claim_path.relative_to(ROOT).as_posix()
    if info.get("path") != expected_relative or not claim_path.is_file():
        return False
    if info.get("sha256") != sha256_file(claim_path):
        return False
    try:
        claim = json.loads(claim_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(
        claim.get("record_type") == "single-use holdout seed claim; existence consumes this range even if process is interrupted"
        and claim.get("stage") == "screen"
        and claim.get("seeds") == list(range(160, 170))
        and claim.get("protocol_commit") == report.get("protocol_commit")
        and claim.get("protocol_sha256") == report.get("protocol_sha256")
        and claim.get("seed_reuse_audit_sha256") == report.get("seed_reuse_audit_sha256")
        and claim.get("input_hashes") == report.get("input_hashes")
        and claim.get("feature_hashes") == report.get("feature_hashes")
        and claim.get("code_hashes") == report.get("code_hashes")
        and claim.get("runtime_versions") == report.get("runtime_versions")
    )


def _validate_passing_screen(report: dict) -> bool:
    """Recompute the frozen screen gate before confirmation; don't trust a lone `passed` flag."""
    if not isinstance(report, dict) or report.get("sha256") != _metadata_fingerprint(report):
        return False
    if report.get("stage") != "screen" or report.get("seeds") != list(range(160, 170)):
        return False
    cells = report.get("cells")
    if not isinstance(cells, list) or len(cells) != 40:
        return False
    expected_pairs = {(seed, name) for seed in range(160, 170) for name in holdout.FOLD_NAMES}
    observed_pairs = set()
    gains = []
    by_seed = {seed: [] for seed in range(160, 170)}
    by_fold = {name: [] for name in holdout.FOLD_NAMES}
    for cell in cells:
        try:
            seed = int(cell["seed"])
            fold_name = cell["fold"]
            n_truth = int(cell["n_truth"])
            control = float(cell["control"]["dti"])
            candidate = float(cell["candidate"]["dti"])
            control_dots = int(cell["control"]["dots"])
            candidate_dots = int(cell["candidate"]["dots"])
            spacing = cell["minimum_spacing_px"]
            control_spacing = float(spacing["control"])
            candidate_spacing = float(spacing["candidate"])
            checks = cell["checks"]
        except (KeyError, TypeError, ValueError):
            return False
        if not isinstance(fold_name, str) or fold_name not in by_fold or n_truth <= 0:
            return False
        if control_dots < 0 or candidate_dots < 0:
            return False
        if not np.isfinite([control, candidate, control_spacing, candidate_spacing]).all():
            return False
        if not (0 <= control <= 1 and 0 <= candidate <= 1 and control_spacing >= 1.5 and candidate_spacing >= 1.5):
            return False
        if not all(checks.get(key) is True for key in (
            "mask_contained_in_active_fold", "no_known_catalogue_overlap",
            "minimum_spacing_at_least_1_5_px", "nonempty_hidden_truth",
        )):
            return False
        pair = (seed, fold_name)
        if pair in observed_pairs:
            return False
        observed_pairs.add(pair)
        gain = candidate - control
        gains.append(gain)
        if seed in by_seed and fold_name in by_fold:
            by_seed[seed].append(gain)
            by_fold[fold_name].append(gain)
    if observed_pairs != expected_pairs or any(len(v) != 4 for v in by_seed.values()) or any(len(v) != 10 for v in by_fold.values()):
        return False
    mean_gain = float(np.mean(gains))
    positive_seed_count = sum(float(np.mean(v)) > 0 for v in by_seed.values())
    positive_fold_count = sum(float(np.mean(v)) > 0 for v in by_fold.values())
    summary = report.get("summary", {})
    gate = report.get("gate", {})
    try:
        reported_mean_gain = float(summary.get("mean_paired_gain", np.nan))
    except (TypeError, ValueError):
        return False
    return bool(
        summary.get("cells") == 40
        and np.isclose(reported_mean_gain, mean_gain, rtol=0, atol=1e-12)
        and summary.get("positive_seed_count") == positive_seed_count
        and summary.get("positive_fold_count") == positive_fold_count
        and mean_gain >= 0.001
        and positive_seed_count >= 8
        and positive_fold_count >= 3
        and all(gate.get(key) is True for key in (
            "mean_gain_at_least_0_001", "positive_fold_means_at_least_3_of_4",
            "positive_seed_means_at_least_8_of_10", "all_data_and_leakage_checks_pass", "passed"
        ))
        and report.get("status") == "screen pass; confirmation may proceed"
        and report.get("current_best_same_run_control") is True
        and report.get("feature_sufficiency", {}).get("passed") is True
        and report.get("probabilities_valid") is True
        and report.get("known_catalogue_overlap_pixels") == 0
        and report.get("grid_mask_violations") == 0
        and report.get("minimum_spacing_failures") == 0
        and report.get("empty_truth_cells") == 0
        and all(report.get("data_integrity_checks", {}).get(key) is True for key in (
            "probabilities_finite_in_0_1", "candidate_and_control_inside_active_fold",
            "zero_known_catalogue_overlap", "minimum_spacing_at_least_1_5_px",
            "nonempty_hidden_truth_every_cell",
        ))
        and report.get("submission_raster_written") is False
        and report.get("drivendata_access") is False
        and _validate_single_use_claim(report)
    )


def run_holdout(seeds: list[int], *, out_path: Path) -> dict:
    if seeds not in (list(range(160, 170)), list(range(170, 180))):
        raise SystemExit("Only preregistered seed ranges 160-169 (screen) and 170-179 (confirmation) are allowed")
    confirm = seeds[0] == 170
    protocol_commit = _protocol_commit()
    if not protocol_commit:
        raise SystemExit("Commit the frozen H31-1 protocol before fitting any holdout model")
    previous = None
    if confirm:
        if not SCREEN.is_file():
            raise SystemExit("Confirmation requires a passing saved screen at evidence/h31_1_euler_screen.json")
        previous = json.loads(SCREEN.read_text())
        if not _validate_passing_screen(previous):
            raise SystemExit("Confirmation requires a complete, internally consistent passing screen on seeds 160-169")
    claim_path = out_path.with_name(out_path.stem + ".started.json")
    if out_path.exists() or claim_path.exists():
        raise SystemExit(f"This seed range already has a final or start/claim record; reruns are prohibited: {out_path}")
    foot = grid.load_footprint(paths.TEMPLATE)
    validate_prepared_feature_metadata(foot)
    euler_features, feature_meta = build_euler_features(force=False)
    suff = feature_meta.get("data_sufficiency_gate", {})
    if not suff.get("passed"):
        raise SystemExit("Frozen H31-1 pre-fit data-sufficiency gate failed; no model was fit")
    edge_features, _ = load_or_build_edge_matrix(foot, force=False)
    combined, _ = build_combined_features(foot, euler_features, force=False)
    input_hashes = h28_input_hashes()
    input_hashes["labels"] = sha256_file(paths.LABELS)
    runtime_versions = _runtime_versions()
    feature_hashes = {
        "h28_edge": sha256_file(paths.PREPARED_FEATURES.parent / "h28_1_edge_features.npy"),
        "h28_edge_metadata": sha256_file(paths.PREPARED_FEATURES.parent / "h28_1_edge_features.json"),
        "euler": sha256_file(FEATURES),
        "euler_metadata": sha256_file(FEATURE_META),
        "combined": sha256_file(COMBINED),
        "combined_metadata": sha256_file(COMBINED.with_suffix(".json")),
    }
    code_hashes = {
        "runner": sha256_file(Path(__file__).resolve()),
        "h28_evaluation_helpers": sha256_file(ROOT / "scripts/run_h28_1_edge_holdout.py"),
        "euler_module": sha256_file(ROOT / "src/gems27/euler.py"),
        "oof_detector": sha256_file(ROOT / "src/gems27/oof_detector.py"),
        "holdout": sha256_file(ROOT / "src/gems27/holdout.py"),
        "metric": sha256_file(ROOT / "src/gems27/metric.py"),
        "grid": sha256_file(ROOT / "src/gems27/grid.py"),
        "links": sha256_file(ROOT / "src/gems27/links.py"),
        "candidates": sha256_file(ROOT / "src/gems27/candidates.py"),
        "graph": sha256_file(ROOT / "src/gems27/graph.py"),
        "paths": sha256_file(ROOT / "src/gems27/paths.py"),
        "thinning": sha256_file(ROOT / "src/gems27/thinning.py"),
        "potential_edges": sha256_file(ROOT / "src/gems27/potential_edges.py"),
    }
    if confirm:
        unchanged = (
            previous.get("protocol_commit") == protocol_commit
            and previous.get("protocol_sha256") == sha256_file(PROTOCOL_PATH)
            and previous.get("input_hashes") == input_hashes
            and previous.get("feature_hashes") == feature_hashes
            and previous.get("code_hashes") == code_hashes
            and previous.get("runtime_versions") == runtime_versions
        )
        if not unchanged:
            raise SystemExit("Confirmation blocked: protocol, input, feature, or code hashes differ from the passing screen")
    labels = grid.load_labels(paths.LABELS)
    if labels.shape != foot.shape or not np.isin(labels, (False, True, 0, 1)).all():
        raise SystemExit("Labels have wrong shape or non-binary values")
    fold = holdout.make_quadrant_folds(foot)
    _assert_seed_range_unused(seeds, out_path)

    claim = {
        "schema": 1,
        "record_type": "single-use holdout seed claim; existence consumes this range even if process is interrupted",
        "stage": "confirmation" if confirm else "screen",
        "seeds": seeds,
        "claimed_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "protocol_commit": protocol_commit,
        "protocol_sha256": sha256_file(PROTOCOL_PATH),
        "seed_reuse_audit_sha256": sha256_file(SEED_AUDIT),
        "input_hashes": input_hashes,
        "feature_hashes": feature_hashes,
        "code_hashes": code_hashes,
        "runtime_versions": runtime_versions,
    }
    claim_sha256 = _write_single_use_claim(claim_path, claim)
    start = time.time()
    print("Training paired H28-1 control OOF detector (38 columns)...", flush=True)
    control_oof = oof_detector.fit_predict_oof_probabilities(foot, labels, fold, extra_features=edge_features, seed=2026)
    print("Training H31-1 Euler candidate OOF detector (41 columns)...", flush=True)
    candidate_oof = oof_detector.fit_predict_oof_probabilities(foot, labels, fold, extra_features=combined, seed=2026)
    probs_ok = bool(
        np.isfinite(control_oof[foot]).all() and np.isfinite(candidate_oof[foot]).all()
        and np.all((control_oof[foot] >= 0) & (control_oof[foot] <= 1))
        and np.all((candidate_oof[foot] >= 0) & (candidate_oof[foot] <= 1))
    )
    if not probs_ok:
        raise SystemExit("Non-finite or out-of-range OOF probabilities")
    control_ridges = oof_detector.ridge_nms(control_oof, foot, sigma=1.0)
    candidate_ridges = oof_detector.ridge_nms(candidate_oof, foot, sigma=1.0)
    cells: list[dict] = []
    known_overlap = 0
    grid_violations = 0
    spacing_failures = 0
    empty_truth_cells = 0
    for seed in seeds:
        for fold_id in range(4):
            split = holdout.make_split(labels, fold, fold_id, seed)
            fm = split.fold_mask
            sl = holdout.crop(None, fm)
            hidden = split.hidden[sl]
            known = (split.known & fm)[sl]
            fold_crop = fm[sl]
            truth = hidden & fold_crop & ~known
            active = fold_crop & ~known
            truth_kernel = (
                metric.kernel_from_distance(distance_transform_edt(~truth))
                if truth.any() else np.zeros_like(truth, dtype=np.float64)
            )
            control_base = (
                oof_detector.build_oof_dotted_base(control_oof[sl], control_ridges[sl], fold_crop, known,
                                                   budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=1.5)
                & active
            )
            candidate_base = (
                oof_detector.build_oof_dotted_base(candidate_oof[sl], candidate_ridges[sl], fold_crop, known,
                                                   budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=1.5)
                & active
            )
            d_known = distance_to(known)
            control_pruned = control_base & (d_known > 1.0)
            candidate_pruned = candidate_base & (d_known > 1.0)
            d_control = distance_to(control_pruned)
            d_candidate = distance_to(candidate_pruned)
            graph = build_graph(split.known, with_edges=False)
            link_frame = links.generate_links(graph, region=fm, **RULE)
            link_scores = evidence_score(link_frame)
            selected_links = dedupe_mutual(link_frame[link_scores >= 3])
            topology = links.rasterize_links(selected_links, labels.shape, SPACING)[sl] & active
            control = control_pruned | (topology & (d_control >= metric.RADIUS_PX))
            candidate = candidate_pruned | (topology & (d_candidate >= metric.RADIUS_PX))
            cell_overlap = int((control & known).sum() + (candidate & known).sum())
            control_spacing = _minimum_spacing_px(control)
            candidate_spacing = _minimum_spacing_px(candidate)
            grid_ok = bool(
                control.shape == active.shape == candidate.shape
                and not (control & ~active).any()
                and not (candidate & ~active).any()
            )
            spacing_ok = bool(
                control_spacing is not None and candidate_spacing is not None
                and control_spacing >= 1.5 - 1e-9 and candidate_spacing >= 1.5 - 1e-9
            )
            truth_ok = bool(truth.any())
            known_overlap += cell_overlap
            grid_violations += int(not grid_ok)
            spacing_failures += int(not spacing_ok)
            empty_truth_cells += int(not truth_ok)
            cells.append({
                "seed": int(seed), "fold": split.name, "n_truth": int(truth.sum()),
                "topology_dots": int(topology.sum()),
                "minimum_spacing_px": {"control": control_spacing, "candidate": candidate_spacing},
                "checks": {
                    "mask_contained_in_active_fold": grid_ok,
                    "no_known_catalogue_overlap": cell_overlap == 0,
                    "minimum_spacing_at_least_1_5_px": spacing_ok,
                    "nonempty_hidden_truth": truth_ok,
                },
                "control": eval_set(control, truth, active, truth_kernel),
                "candidate": eval_set(candidate, truth, active, truth_kernel),
            })
        done = [c for c in cells if c["seed"] == seed]
        print(f"seed {seed} complete: paired ΔDTI={np.mean([c['candidate']['dti']-c['control']['dti'] for c in done]):+.6f}; "
              f"elapsed={time.time()-start:.0f}s", flush=True)
    summary = _stage_summary(cells)
    gate = {
        "mean_gain_at_least_0_001": summary["mean_paired_gain"] >= 0.001,
        "positive_fold_means_at_least_3_of_4": summary["positive_fold_count"] >= 3,
        "positive_seed_means_at_least_8_of_10": summary["positive_seed_count"] >= 8,
        "all_data_and_leakage_checks_pass": bool(
            probs_ok and known_overlap == 0 and grid_violations == 0
            and spacing_failures == 0 and empty_truth_cells == 0
        ),
    }
    gate["passed"] = all(gate.values())
    report = {
        "schema": 1,
        "hypothesis": "H31-1 depth-labeled magnetic Euler source solutions/clusters",
        "status": "screen pass; confirmation may proceed" if (not confirm and gate["passed"])
                  else "confirmation pass" if (confirm and gate["passed"])
                  else "frozen gate failed; not promoted",
        "checked_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "protocol_path": "knowledge/12_preregistration_H31-1_euler.md",
        "protocol_commit": protocol_commit,
        "protocol_sha256": sha256_file(PROTOCOL_PATH),
        "stage": "confirmation" if confirm else "screen",
        "seeds": seeds,
        "cells": cells,
        "summary": summary,
        "gate": gate,
        "control": "H28-1 six potential-edge features + T-v2 + H27-4 r1; same-run paired baseline",
        "candidate": "same recipe plus three SI-0 Euler cluster features; no new emission points",
        "current_best_same_run_control": True,
        "proxy_limit": "Catalogue-component hide-and-recover only; not organizer truth or competition performance.",
        "input_hashes": input_hashes,
        "feature_hashes": feature_hashes,
        "code_hashes": code_hashes,
        "runtime_versions": runtime_versions,
        "seed_reuse_audit_sha256": sha256_file(SEED_AUDIT),
        "single_use_seed_claim": {"path": str(claim_path.relative_to(ROOT)), "sha256": claim_sha256},
        "probabilities_valid": probs_ok,
        "known_catalogue_overlap_pixels": known_overlap,
        "grid_mask_violations": grid_violations,
        "minimum_spacing_failures": spacing_failures,
        "empty_truth_cells": empty_truth_cells,
        "data_integrity_checks": {
            "probabilities_finite_in_0_1": probs_ok,
            "candidate_and_control_inside_active_fold": grid_violations == 0,
            "zero_known_catalogue_overlap": known_overlap == 0,
            "minimum_spacing_at_least_1_5_px": spacing_failures == 0,
            "nonempty_hidden_truth_every_cell": empty_truth_cells == 0,
        },
        "feature_sufficiency": feature_meta["data_sufficiency_gate"],
        "feature_filter_diagnostics": {
            "derivative": feature_meta["derivative"],
            "si0_solver_filters": feature_meta["structural_indices"]["0"]["solver_filters"],
            "si0_cluster_stats": feature_meta["structural_indices"]["0"]["lineament_cluster_stats"],
        },
        "runtime_seconds": round(time.time() - start, 3),
        "submission_raster_written": False,
        "drivendata_access": False,
    }
    report["sha256"] = None
    report["sha256"] = _metadata_fingerprint(report)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"stage": report["stage"], "summary": summary, "gate": gate, "evidence": str(out_path)}, indent=2))
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--features-only", action="store_true", help="build/audit features; do not fit a model")
    parser.add_argument("--seeds", choices=("160-169", "170-179"), default=None)
    parser.add_argument("--confirm", action="store_true", help="required for the preregistered 170-179 confirm")
    parser.add_argument("--force-features", action="store_true")
    args = parser.parse_args()
    if args.features_only:
        if args.seeds is not None or args.confirm:
            raise SystemExit("--features-only cannot be combined with holdout seed options")
        features, meta = build_euler_features(force=args.force_features)
        print(json.dumps({"feature_shape": list(features.shape), "feature_sha256": meta["feature_matrix"]["sha256"],
                          "sufficiency": meta["data_sufficiency_gate"], "feature_audit": str(FEATURE_AUDIT),
                          "clusters_csv": str(CLUSTER_CSV)}, indent=2))
        return 0 if meta["data_sufficiency_gate"]["passed"] else 2
    if args.force_features:
        raise SystemExit("--force-features is only valid with --features-only")
    if args.seeds is None:
        raise SystemExit("Choose --seeds 160-169 (screen) or --seeds 170-179 --confirm")
    seeds = list(range(160, 170)) if args.seeds == "160-169" else list(range(170, 180))
    if (args.seeds == "170-179") != bool(args.confirm):
        raise SystemExit("--confirm is required exactly for --seeds 170-179")
    out = CONFIRM if args.confirm else SCREEN
    run_holdout(seeds, out_path=out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
