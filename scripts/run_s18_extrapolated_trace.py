#!/usr/bin/env python3
"""Execute frozen S18-MXTP stages; duplicate-stop is terminal, not a retuning signal.

See knowledge/52_s18_preregistration.md. Uses shared evaluator and writer; never uploads.
The holdout stage is a separate explicit command only after the uniqueness stage passes.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import (  # noqa: E402
    extrapolated_trace, grid, holdout, losfo, packing, paths, registry_compare, submission,
)


def save(obj, path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")


def compare(surface, support, foot, registry):
    ranks, norm = registry_compare.ranked_centered(surface[foot])
    out = []
    for entry in registry["entries"]:
        if entry["status"] != "included":
            continue
        path = ROOT / entry["local_path"]
        if submission.sha256_file(path) != entry["sha256"]:
            raise ValueError(f"Registry changed: {path}")
        with rasterio.open(path) as src:
            ref = src.read(1)
        if not np.isfinite(ref[foot]).all():
            out.append({"raster_sha256": entry["sha256"], "path": entry["path"],
                        "status": "nonfinite_reference_inside", "spearman": None,
                        "within_3px_fraction": None, "duplicate": False})
            continue
        rho = registry_compare.spearman_against(ranks, norm, ref[foot])
        overlap = registry_compare.within_fraction(support, foot & (ref > 0))
        duplicate = (rho is not None and rho > 0.90) or (overlap is not None and overlap > 0.70)
        row = {"raster_sha256": entry["sha256"], "path": entry["path"],
               "repo": entry["repo"], "spearman": rho, "within_3px_fraction": overlap,
               "reference_positive_pixels": int(np.count_nonzero(ref[foot] > 0)),
               "status": "compared" if rho is not None else "undefined_constant_correlation",
               "duplicate": bool(duplicate)}
        out.append(row)
    return out


def feature_canaries(surfaces, labels, foot):
    folds = holdout.make_quadrant_folds(foot)
    systems, n = losfo.fault_systems(labels, losfo.DEFAULT_DILATE_PX)
    table = losfo.system_table(systems, n, foot)
    assignment = losfo.assign_systems_to_folds(table, folds, 4, seed=310)
    hidden = np.isin(systems, np.flatnonzero(assignment >= 0) + 1) & foot
    negpool = np.flatnonzero((foot & ~labels & (distance_transform_edt(~hidden) > 6)).ravel())
    rng = np.random.default_rng(310)
    negatives = rng.choice(negpool, size=min(250_000, len(negpool)), replace=False)
    y = np.r_[np.ones(hidden.sum()), np.zeros(len(negatives))]
    results = {}
    for name, surface in surfaces.items():
        scores = np.r_[surface[hidden], surface.ravel()[negatives]]
        auc = float(roc_auc_score(y, scores))
        results[name] = {"auc": auc, "max_auc_1mauc": max(auc, 1-auc)}
    return {"diagnostic": "feature-alone ROC-AUC, not HOLDOUT-DTI or a competition score",
            "seed": 310, "withheld_positive_pixels": int(hidden.sum()),
            "sampled_negatives": int(len(negatives)), "features": results,
            "passed": all(x["max_auc_1mauc"] <= 0.90 for x in results.values())}


def main():
    started = time.monotonic()
    frozen = ROOT / "knowledge/52_s18_preregistration.md"
    dest = ROOT / "evidence/s18_stage_result.json"
    if dest.exists():
        raise SystemExit("Frozen experiment already executed. Do not overwrite or retune.")
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    registry_path = ROOT / "evidence/s18_registry_snapshot.json"
    registry = json.loads(registry_path.read_text())
    if not registry["complete_within_declared_scope"]:
        raise SystemExit("Registry acquisition incomplete; no experiment.")
    meta = json.loads(paths.PREPARED_META.read_text())
    if submission.sha256_file(paths.PREPARED_FEATURES) != meta["sha256"]:
        raise ValueError("prepared cache hash mismatch")
    cache = np.load(paths.PREPARED_FEATURES, mmap_mode="r")
    surfaces, geometry = extrapolated_trace.build_from_cache(cache, meta["names"], foot)
    np.save(paths.DATA / "prepared/s18_surface.npy", surfaces["combined"])
    canaries = feature_canaries(surfaces, labels, foot)
    surface = surfaces["combined"]
    support = foot & (surface >= 0.25)
    report = {"session": "S18-MXTP", "preregistration_sha256": submission.sha256_file(frozen),
              "feature_cache_sha256": meta["sha256"], "registry_sha256": submission.sha256_file(registry_path),
              "geometry": geometry, "canaries": canaries,
              "surface_sha256": submission.sha256_file(paths.DATA / "prepared/s18_surface.npy"),
              "surface_support_pixels": int(support.sum()), "surface": [], "dots": [],
              "experiments_used": 1, "status": "canary_failed", "raster": None,
              "holdout": None, "submission_ready": False, "slot_selected": False}
    if canaries["passed"]:
        report["surface"] = compare(surface, support, foot, registry)
        dup = any(r["duplicate"] for r in report["surface"])
        report["status"] = "duplicate_stop_before_placement" if dup else "surface_passed"
        # Do not continue after a duplicate or incomplete/undefined registry comparison.
        complete = all(r["status"] == "compared" for r in report["surface"])
        if not dup and not complete:
            report["status"] = "registry_comparison_incomplete_stop"
        if not dup and complete:
            report["experiments_used"] = 2
            eligible = support & (distance_transform_edt(~labels) > 2)
            dots = packing.prob_order_pack(surface, eligible, n_target=37_654, min_dist=2.8)
            report["dots"] = compare(dots.astype(np.float32), dots, foot, registry)
            dup = any(r["duplicate"] for r in report["dots"])
            report["status"] = "duplicate_stop_final_dots" if dup else "unique_research_tiff_holdout_pending"
            if not dup and all(r["status"] == "compared" for r in report["dots"]):
                cid = submission.scored_content_id(dots, foot, labels)
                filename = submission.make_filename("gems28", "s18-mxtp", "20261025", cid, "allfinite")
                path = paths.DOCS / "downloads" / filename
                submission.write_geotiff(dots, paths.TEMPLATE, path, outside="zero")
                report["raster"] = {"path": str(path.relative_to(ROOT)),
                                     "sha256": submission.sha256_file(path),
                                     "validator": submission.verify_geotiff(path, paths.TEMPLATE)}
    report["seconds"] = round(time.monotonic() - started, 1)
    save(report, dest)
    print(json.dumps({k: report[k] for k in ("status", "experiments_used", "seconds", "surface_support_pixels", "canaries", "raster")}, indent=2))
    print("surface duplicate count:", sum(r["duplicate"] for r in report["surface"]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
