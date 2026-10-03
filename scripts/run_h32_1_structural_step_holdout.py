#!/usr/bin/env python3
"""Frozen H32-1 screen: structural-step coherence of the conductivity/conductive-base/strain group.

Protocol: knowledge/14_preregistration_H32-1.md (must match the committed Git blob exactly).
Control: the H28-1 arm (32 prepared + six potential-field edge features) with the frozen
T-v2 + H27-4 r1 recipe. Candidate: the same arm plus six H32-1 structural-step columns.
Seeds 170-179, one run. This script writes one evidence JSON and a disposable feature cache; it never
writes or replaces submission rasters and never contacts DrivenData.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import run_h28_1_edge_holdout as h28  # noqa: E402  (frozen, reused verbatim)
from gems27 import grid, holdout, links, metric, oof_detector, paths, structural_step  # noqa: E402
from gems27.candidates import RULE, SPACING, dedupe_mutual, evidence_score  # noqa: E402
from gems27.graph import build_graph  # noqa: E402

PREREG = REPO / "knowledge" / "14_preregistration_H32-1.md"
EXPECTED_INPUTS = {  # 1-based competition band numbers and embedded-description prefixes
    "depth_to_base_surf": (15, "depth_to_base_surf"),
    "cond_surf": (17, "cond_surf"),
    "geod_2ndinv": (4, "geod_2ndinv"),
}
PARAMETERS = {
    "pixel_size_m": 100.0,
    "sigmas_px": [3.0, 10.0],
    "gradient_percentiles": [5, 95],
    "orientation_threshold_percentile": 10,
    "outside_mask": 0.0,
}


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def assert_preregistration_committed() -> dict:
    """Refuse to run unless the working protocol bytes equal the committed Git blob."""
    rel = str(PREREG.relative_to(REPO))
    try:
        committed = subprocess.run(
            ["git", "-C", str(REPO), "show", f"HEAD:{rel}"],
            check=True, capture_output=True,
        ).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as exc:
        raise SystemExit(f"cannot read committed protocol {rel}: {exc}") from exc
    working = PREREG.read_bytes()
    if committed != working:
        raise SystemExit(
            "the working H32-1 protocol does not match the committed blob; "
            "commit the protocol before running the screen"
        )
    return {"path": rel, "sha256": sha256_file(PREREG)}


def build_structural_matrix(foot: np.ndarray) -> tuple[np.ndarray, dict]:
    out_dir = paths.PREPARED_FEATURES.parent
    matrix_path = out_dir / "h32_1_structural_step_features.npy"
    metadata_path = out_dir / "h32_1_structural_step_features.json"
    expected_shape = (int(foot.sum()), len(structural_step.STRUCT_STEP_FEATURE_NAMES))
    if matrix_path.exists() and metadata_path.exists():
        meta = json.loads(metadata_path.read_text())
        arr = np.load(matrix_path, mmap_mode="r")
        if (meta.get("feature_names") == list(structural_step.STRUCT_STEP_FEATURE_NAMES)
                and meta.get("parameters") == PARAMETERS
                and meta.get("shape") == list(expected_shape)
                and arr.shape == expected_shape
                and "values_min" in meta and "values_max" in meta
                and sha256_file(matrix_path) == meta.get("sha256")):
            return arr, meta

    with rasterio.open(paths.TEMPLATE) as template, rasterio.open(paths.TRAINING) as source:
        if (source.shape != template.shape or source.crs != template.crs
                or source.transform != template.transform):
            raise SystemExit("training grid differs from the competition grid; refusing to resample")
        descriptions = tuple((d or "").split(" - ")[0].strip() for d in source.descriptions)
        for _name, (band, prefix) in EXPECTED_INPUTS.items():
            if descriptions[band - 1] != prefix:
                raise SystemExit(
                    f"expected band {band} {prefix!r}, found {descriptions[band - 1]!r}"
                )
        arrays = {
            name: source.read(band, out_dtype="float32") for name, (band, _) in EXPECTED_INPUTS.items()
        }
        nodata = source.nodata

    valid = foot.copy()
    for _name, arr in arrays.items():
        valid &= np.isfinite(arr) & (np.abs(arr) < 1e30)
        if nodata is not None:
            valid &= arr != np.float32(nodata)
    if int(valid.sum()) < int(0.95 * foot.sum()):
        raise SystemExit(
            f"only {int(valid.sum()):,}/{int(foot.sum()):,} footprint cells are valid in all three bands"
        )

    stack = structural_step.structural_step_features(
        arrays["depth_to_base_surf"], arrays["cond_surf"], arrays["geod_2ndinv"], valid,
        pixel_size_m=PARAMETERS["pixel_size_m"], sigmas_px=tuple(PARAMETERS["sigmas_px"]),
    )
    matrix = np.ascontiguousarray(stack[:, foot].T, dtype=np.float32)
    if matrix.shape != expected_shape or not np.isfinite(matrix).all():
        raise SystemExit(f"invalid H32-1 matrix: shape={matrix.shape}")
    if float(matrix.min()) < 0.0 or float(matrix.max()) > 1.0:
        raise SystemExit("H32-1 feature scaling escaped [0, 1]")
    partial = matrix_path.with_suffix(".partial.npy")
    np.save(partial, matrix, allow_pickle=False)
    partial.replace(matrix_path)
    meta = {
        "schema": 1,
        "feature_names": list(structural_step.STRUCT_STEP_FEATURE_NAMES),
        "shape": list(matrix.shape),
        "grid_shape": list(foot.shape),
        "crs": f"EPSG:{grid.CRS_EPSG}",
        "source_bands": {k: {"band": b, "description": d} for k, (b, d) in EXPECTED_INPUTS.items()},
        "valid_cells": int(valid.sum()),
        "values_min": float(matrix.min()),
        "values_max": float(matrix.max()),
        "parameters": PARAMETERS,
        "sha256": sha256_file(matrix_path),
    }
    metadata_path.write_text(json.dumps(meta, indent=2) + "\n")
    return np.load(matrix_path, mmap_mode="r"), meta


def parse_seeds(value: str) -> list[int]:
    start, sep, end = value.partition("-")
    if not start.isdigit() or (sep and not end.isdigit()):
        raise argparse.ArgumentTypeError("seeds must be an integer or inclusive range")
    seeds = list(range(int(start), int(end) + 1)) if sep else [int(start)]
    if not seeds or len(seeds) > 100:
        raise argparse.ArgumentTypeError("seed range must contain 1 to 100 seeds")
    return seeds


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--seeds", default="170-179", type=parse_seeds)
    ap.add_argument("--out", default=str(paths.EVIDENCE / "h32_1_structural_step_holdout.json"))
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    out_path = Path(args.out)
    if out_path.exists() and not args.overwrite:
        raise SystemExit(f"{out_path} exists; use --overwrite only for a documented rerun")

    started = time.time()
    prereg = assert_preregistration_committed()
    code_hashes = {
        "runner": sha256_file(Path(__file__).resolve()),
        "transform": sha256_file(REPO / "src/gems27/structural_step.py"),
        "control_runner": sha256_file(REPO / "scripts/run_h28_1_edge_holdout.py"),
    }

    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    if labels.shape != foot.shape:
        raise SystemExit("labels and footprint disagree")
    fold = holdout.make_quadrant_folds(foot)
    prepared_check = h28.validate_prepared_feature_metadata(foot)

    print("Loading frozen H28-1 control features...", flush=True)
    edge_matrix, edge_meta = h28.load_or_build_edge_matrix(foot, force=False)
    print("Building H32-1 structural-step features...", flush=True)
    struct_matrix, struct_meta = build_structural_matrix(foot)
    candidate_matrix = np.ascontiguousarray(
        np.hstack([np.asarray(edge_matrix), np.asarray(struct_matrix)]), dtype=np.float32
    )
    del struct_matrix
    if candidate_matrix.shape != (int(foot.sum()), 12):
        raise SystemExit(f"candidate matrix has shape {candidate_matrix.shape}, expected 12 columns")
    if float(candidate_matrix.min()) < 0.0 or float(candidate_matrix.max()) > 1.0:
        raise SystemExit("candidate feature values escaped [0, 1]")

    print("Training control 4-fold OOF detector (38 bands)...", flush=True)
    control_oof = oof_detector.fit_predict_oof_probabilities(
        foot, labels, fold, extra_features=edge_matrix, seed=2026
    )
    print("Training candidate 4-fold OOF detector (44 bands)...", flush=True)
    candidate_oof = oof_detector.fit_predict_oof_probabilities(
        foot, labels, fold, extra_features=candidate_matrix, seed=2026
    )
    probabilities_valid = bool(
        np.isfinite(control_oof[foot]).all() and np.isfinite(candidate_oof[foot]).all()
        and np.all((control_oof[foot] >= 0) & (control_oof[foot] <= 1))
        and np.all((candidate_oof[foot] >= 0) & (candidate_oof[foot] <= 1))
    )
    if not probabilities_valid:
        raise SystemExit("OOF classifier produced invalid probabilities")
    control_ridges = oof_detector.ridge_nms(control_oof, foot, sigma=1.0)
    candidate_ridges = oof_detector.ridge_nms(candidate_oof, foot, sigma=1.0)

    cells: list[dict] = []
    known_overlap = 0
    for seed in args.seeds:
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
                if truth.any() else np.zeros_like(truth, float)
            )
            predictions = {}
            for name, oof, ridges in (
                ("control", control_oof, control_ridges),
                ("candidate", candidate_oof, candidate_ridges),
            ):
                dotted = (
                    oof_detector.build_oof_dotted_base(
                        oof[sl], ridges[sl], fold_crop, known,
                        budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=1.5,
                    ) & active
                )
                d_known = h28.distance_to(known)
                pruned = dotted & (d_known > 1.0)
                graph = build_graph(split.known, with_edges=False)
                link_frame = links.generate_links(graph, region=fm, **RULE)
                link_evidence = evidence_score(link_frame)
                selected_links = dedupe_mutual(link_frame[link_evidence >= 3])
                topology = links.rasterize_links(selected_links, labels.shape, SPACING)[sl] & active
                d_pruned = h28.distance_to(pruned)
                predictions[name] = pruned | (topology & (d_pruned >= metric.RADIUS_PX))
            overlap = sum(int((p & known).sum()) for p in predictions.values())
            known_overlap += overlap
            if overlap:
                raise SystemExit(f"prediction overlaps known catalogue by {overlap} pixels")
            row = {"seed": seed, "fold": split.name, "n_truth": int(truth.sum())}
            for name, prediction in predictions.items():
                row[name] = h28.eval_set(prediction, truth, active, truth_kernel)
            cells.append(row)
        print(f"seed {seed} done at {time.time() - started:.0f}s", flush=True)

    deltas = [c["candidate"]["dti"] - c["control"]["dti"] for c in cells]
    by_seed = {
        str(s): float(np.mean([c["candidate"]["dti"] - c["control"]["dti"]
                               for c in cells if c["seed"] == s]))
        for s in args.seeds
    }
    by_fold = {
        name: float(np.mean([c["candidate"]["dti"] - c["control"]["dti"]
                             for c in cells if c["fold"] == name]))
        for name in holdout.FOLD_NAMES
    }
    data_checks = {
        "footprint_cells": int(foot.sum()),
        "label_positive_cells": int(labels[foot].sum()),
        "control_feature_columns": int(edge_matrix.shape[1]) if edge_matrix.ndim == 2 else None,
        "candidate_feature_columns": int(candidate_matrix.shape[1]),
        "structural_valid_cells": int(struct_meta["valid_cells"]),
        "structural_valid_fraction": float(struct_meta["valid_cells"] / int(foot.sum())),
        "all_probabilities_finite_and_in_0_1": probabilities_valid,
        "structural_values_finite_and_in_0_1": bool(
            0.0 <= float(struct_meta["values_min"]) and float(struct_meta["values_max"]) <= 1.0
        ),
        "source_band_descriptions": struct_meta["source_bands"],
        "control_source_band_descriptions": edge_meta["source_bands"],
        "prepared_feature_metadata": prepared_check,
        "known_catalogue_overlap_pixels": known_overlap,
        "cells": len(cells),
        "protocol_sha256": prereg["sha256"],
    }
    gate = {
        "mean_gain_at_least_0_001": bool(float(np.mean(deltas)) >= 0.001),
        "at_least_3_of_4_folds_improve": bool(sum(v > 0 for v in by_fold.values()) >= 3),
        "at_least_8_of_10_seeds_improve": bool(
            len(args.seeds) == 10 and sum(v > 0 for v in by_seed.values()) >= 8
        ),
        "exactly_preregistered_seeds": bool(args.seeds == list(range(170, 180))),
        "data_checks_passed": bool(
            probabilities_valid
            and known_overlap == 0
            and len(cells) == len(args.seeds) * 4
            and int(struct_meta["valid_cells"]) >= int(0.95 * foot.sum())
            and candidate_matrix.shape[1] == 12
        ),
    }
    gate["pass"] = all(gate.values())
    summary = {
        name: {
            "mean_dti": float(np.mean([c[name]["dti"] for c in cells])),
            "mean_dots": float(np.mean([c[name]["dots"] for c in cells])),
            "mean_tp": float(np.mean([c[name]["tp"] for c in cells])),
            "mean_fp": float(np.mean([c[name]["fp"] for c in cells])),
        }
        for name in ("control", "candidate")
    }
    result = {
        "preregistration": "knowledge/14_preregistration_H32-1.md",
        "candidate": "H32-1 structural-step coherence (depth-to-base / conductivity / strain)",
        "seeds": args.seeds,
        "fold_names": holdout.FOLD_NAMES,
        "code_sha256": code_hashes,
        "protocol": prereg,
        "control_feature_cache": edge_meta,
        "structural_feature_cache": {k: v for k, v in struct_meta.items() if k != "feature_names"},
        "data_checks": data_checks,
        "variants": summary,
        "candidate_minus_control_mean_gain": float(np.mean(deltas)),
        "gain_by_seed": by_seed,
        "gain_by_fold": by_fold,
        "positive_seed_count": int(sum(v > 0 for v in by_seed.values())),
        "improved_fold_count": int(sum(v > 0 for v in by_fold.values())),
        "gate": gate,
        "cell_results": cells,
        "seconds": time.time() - started,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({"mean_gain": result["candidate_minus_control_mean_gain"],
                      "by_fold": by_fold, "by_seed": by_seed, "gate": gate,
                      "variants": summary}, indent=2))
    print("wrote", out_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
