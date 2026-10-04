"""Label-free candidate screen for the H38-1 cross-field Euler/gravity/relief hypothesis.

The thresholds are frozen in knowledge/38_preregistration_H38-1.md. SI-0 Euler clusters are only
candidate contacts; this module does not identify faults or geothermal systems. It intentionally does
not load labels.tif or any holdout outcome.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterable

import numpy as np
from scipy.ndimage import distance_transform_edt

GRAVITY_BAND = 18  # 1-based training_features band; iso_grav_anom_hg
RELIEF_BAND = 9    # 1-based LiDAR descriptor band; local relief rank
LIDAR_VALID_BAND = 12
GRAVITY_QUANTILE = 0.80
RELIEF_QUANTILE = 0.50
GRAVITY_RADIUS_PX = 2.0  # 200 m on the 100 m competition grid
DEPTH_MAD_MAX_M = 60.0
MEDIAN_DEPTH_MAX_M = 400.0
N_SOLUTIONS_MIN = 8
MIN_CANDIDATES_FOR_HOLDOUT = 100
REQUIRED_CLUSTER_COLUMNS = (
    "row", "col", "median_depth_m", "depth_mad_m", "n_solutions",
)


def finite_in_footprint(values: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Return the valid population, excluding NaNs and large sentinel values."""
    if values.shape != footprint.shape:
        raise ValueError("feature and footprint shapes differ")
    return footprint & np.isfinite(values) & (np.abs(values) < 1.0e30)


def candidate_support_mask(
    gravity_gradient: np.ndarray,
    relief: np.ndarray,
    lidar_valid: np.ndarray,
    footprint: np.ndarray,
    *,
    gravity_quantile: float = GRAVITY_QUANTILE,
    relief_quantile: float = RELIEF_QUANTILE,
    radius_px: float = GRAVITY_RADIUS_PX,
) -> tuple[np.ndarray, dict]:
    """Return locations satisfying the preregistered independent-field conjunction.

    Gravity's quantile population is all finite in-footprint values. Relief's population is all
    LiDAR-valid in-footprint values. The gravity corridor is the Euclidean distance (in pixels) to
    any cell at or above the gravity quantile. Output is restricted to the competition footprint.
    """
    arrays = (gravity_gradient, relief, lidar_valid, footprint)
    if any(np.asarray(a).ndim != 2 for a in arrays):
        raise ValueError("all inputs must be two-dimensional")
    if len({np.asarray(a).shape for a in arrays}) != 1:
        raise ValueError("all inputs must use the same grid")
    if not (0.0 < gravity_quantile < 1.0 and 0.0 < relief_quantile < 1.0):
        raise ValueError("quantiles must be strictly between zero and one")
    if radius_px < 0:
        raise ValueError("radius_px must be non-negative")

    foot = np.asarray(footprint, dtype=bool)
    gravity = np.asarray(gravity_gradient)
    relief_arr = np.asarray(relief)
    lidar_ok = np.asarray(lidar_valid, dtype=bool)

    gravity_valid = finite_in_footprint(gravity, foot)
    relief_valid = foot & lidar_ok & np.isfinite(relief_arr)
    if not gravity_valid.any():
        raise ValueError("no finite gravity values within the footprint")
    if not relief_valid.any():
        raise ValueError("no valid LiDAR relief values within the footprint")

    gravity_threshold = float(np.quantile(gravity[gravity_valid], gravity_quantile, method="linear"))
    relief_threshold = float(np.quantile(relief_arr[relief_valid], relief_quantile, method="linear"))
    gravity_high = gravity_valid & (gravity >= gravity_threshold)
    if not gravity_high.any():
        raise ValueError("gravity threshold produced an empty high-gradient mask")
    distance_px = distance_transform_edt(~gravity_high)
    near_gravity = foot & (distance_px <= radius_px)
    low_relief = relief_valid & (relief_arr <= relief_threshold)
    support = near_gravity & low_relief

    audit = {
        "gravity_band_1based": GRAVITY_BAND,
        "gravity_feature": "iso_grav_anom_hg",
        "gravity_population": "finite (abs < 1e30) cells inside the finite template footprint",
        "gravity_quantile": float(gravity_quantile),
        "gravity_threshold": gravity_threshold,
        "gravity_valid_cells": int(gravity_valid.sum()),
        "gravity_high_cells": int(gravity_high.sum()),
        "gravity_corridor_radius_px": float(radius_px),
        "gravity_corridor_radius_m": float(radius_px * 100.0),
        "cells_near_gravity": int(near_gravity.sum()),
        "relief_band_1based": RELIEF_BAND,
        "relief_feature": "relief",
        "relief_population": "finite LiDAR-valid cells inside the finite template footprint",
        "relief_quantile": float(relief_quantile),
        "relief_threshold": relief_threshold,
        "relief_valid_cells": int(relief_valid.sum()),
        "cells_low_relief": int(low_relief.sum()),
        "joint_support_cells": int(support.sum()),
    }
    return support, audit


def _cluster_row_is_eligible(row: dict[str, str]) -> bool:
    try:
        mad = float(row["depth_mad_m"])
        depth = float(row["median_depth_m"])
        n_solutions = int(row["n_solutions"])
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"invalid Euler cluster row: {row}") from exc
    if not np.isfinite(mad) or not np.isfinite(depth) or mad < 0 or depth < 0:
        raise ValueError(f"non-finite or negative Euler statistic: {row}")
    return mad <= DEPTH_MAD_MAX_M and depth <= MEDIAN_DEPTH_MAX_M and n_solutions >= N_SOLUTIONS_MIN


def selected_cluster_rows(
    rows: Iterable[dict[str, str]],
    support: np.ndarray,
) -> tuple[list[dict[str, str]], dict]:
    """Select eligible cluster rows whose rounded centroid is inside the frozen support mask."""
    chosen: list[dict[str, str]] = []
    seen: set[tuple[int, int]] = set()
    n_rows = 0
    n_depth_eligible = 0
    h, w = support.shape
    for row in rows:
        n_rows += 1
        if not _cluster_row_is_eligible(row):
            continue
        n_depth_eligible += 1
        try:
            y_f, x_f = float(row["row"]), float(row["col"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"invalid Euler cluster coordinates: {row}") from exc
        if not np.isfinite(y_f) or not np.isfinite(x_f):
            raise ValueError(f"non-finite Euler cluster coordinates: {row}")
        y, x = int(round(y_f)), int(round(x_f))
        if not (0 <= y < h and 0 <= x < w):
            raise ValueError(f"Euler cluster lies outside grid at rounded row/col {(y, x)}")
        if (y, x) in seen:
            raise ValueError(f"duplicate rounded Euler cluster coordinate {(y, x)}")
        seen.add((y, x))
        if support[y, x]:
            chosen.append(row)
    return chosen, {
        "input_cluster_rows": n_rows,
        "depth_eligible_clusters": n_depth_eligible,
        "selected_clusters": len(chosen),
        "minimum_candidates_for_holdout": MIN_CANDIDATES_FOR_HOLDOUT,
        "sufficiency": "READY" if len(chosen) >= MIN_CANDIDATES_FOR_HOLDOUT else "INSUFFICIENT",
    }


def read_and_select_clusters(csv_path: Path | str, support: np.ndarray):
    """Read a cluster CSV, validate its schema and deterministically select candidates."""
    with Path(csv_path).open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames is None:
            raise ValueError("Euler cluster CSV is empty")
        missing = sorted(set(REQUIRED_CLUSTER_COLUMNS) - set(reader.fieldnames))
        if missing:
            raise ValueError(f"Euler cluster CSV missing required columns: {missing}")
        fields = list(reader.fieldnames)
        chosen, counts = selected_cluster_rows(reader, support)
    return fields, chosen, counts


def write_candidate_csv(path: Path | str, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    """Write selected source rows without modifying their coordinates or statistics."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
