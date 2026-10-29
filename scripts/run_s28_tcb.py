#!/usr/bin/env python3
"""Run S28-TCB once under the shared hide-and-recover protocol.

TCB is the top untried proposal carried forward from the prior session: a
catalogue-free two-sided directional texture-covariance change in RTP, TMI
horizontal gradient, and surface conductivity.  This runner deliberately does
not select a weekly slot and never calls the competition site.

The run is fail-closed:

* the restored, hash-pinned prepared feature cache supplies the three layers;
* every feature is tested alone by the shared leakage canary;
* the continuous surface is compared before any dots are placed;
* the final binary dots are compared against the current nine-site artifact
  audit plus the registered spacing-five calibration control;
* a TIFF is written only if the candidate beats the paired random-K control,
  clears the literal novelty rule, and passes the shared writer checks.

A negative result is a complete deliverable.  A holdout value is always labeled
HOLDOUT-DTI; it is not a leaderboard prediction.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems27 import paths, submission  # noqa: E402
from gems27.tcb import build_surface  # noqa: E402

LAYER_NAMES = ("rtp", "tmi_hg", "cond_surf")
K_DOTS = 37_654
BUFFER_PX = 15
EVALUATOR_VERSION = "gems-segment-pooled-v1"
RUN_ID = "S28-TCB-20261029"
AUDIT_PATH = ROOT / "evidence/s28_priority_repository_audit.json"
CONTROL_PATH = ROOT / "data/s23/lattice.tif"
CONTROL_FILE = "inputs/calibration/13gems_20261001_r13-lattice-s5_v2_nan-outside.tif"
CONTROL_SOURCE = (
    "https://github.com/buffedlizard55-lab/GEMSDOE24/blob/"
    "07345ea0604953d7efb858d9cfbc21e20c7aca0b/"
    + CONTROL_FILE
)
OUT_PATH = ROOT / "evidence/s28_tcb_run_card.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def read_cached_layers(footprint: np.ndarray) -> tuple[dict[str, np.ndarray], dict]:
    """Materialize only the three named columns from the verified cache."""
    meta = json.loads(paths.PREPARED_META.read_text(encoding="utf-8"))
    array = np.load(paths.PREPARED_FEATURES, mmap_mode="r", allow_pickle=False)
    if array.dtype != np.dtype("float32") or array.shape[0] != int(footprint.sum()):
        raise ValueError("Prepared feature cache shape/dtype does not match the template footprint")
    if meta.get("sha256") != sha256_file(paths.PREPARED_FEATURES):
        raise ValueError("Prepared feature cache SHA-256 differs from its metadata")
    names = meta.get("names")
    if not isinstance(names, list) or len(names) != array.shape[1]:
        raise ValueError("Prepared feature cache names are malformed")
    columns = {name: names.index(name) for name in LAYER_NAMES}
    index = np.flatnonzero(footprint.ravel())
    layers: dict[str, np.ndarray] = {}
    for name in LAYER_NAMES:
        full = np.full(footprint.shape, np.nan, dtype=np.float32)
        full.ravel()[index] = np.asarray(array[:, columns[name]], dtype=np.float32)
        layers[name] = full
    return layers, {
        "metadata": str(paths.PREPARED_META.relative_to(ROOT)),
        "array": str(paths.PREPARED_FEATURES.relative_to(ROOT)),
        "sha256": meta["sha256"],
        "shape": list(array.shape),
        "names": list(LAYER_NAMES),
        "missingness": {name: meta.get("missingness", {}).get("bands", {}).get(name) for name in LAYER_NAMES},
    }


def read_footprint_and_catalogue() -> tuple[np.ndarray, np.ndarray]:
    with rasterio.open(paths.TEMPLATE) as template, rasterio.open(paths.LABELS) as labels:
        footprint = np.isfinite(template.read(1))
        if (labels.shape, labels.crs, labels.transform) != (
            template.shape,
            template.crs,
            template.transform,
        ):
            raise ValueError("Labels and sample template do not share the trusted grid")
        label_values = labels.read(1)
        catalogue = np.isfinite(label_values) & (label_values > 0.5)
    if int(footprint.sum()) != 5_167_373:
        raise ValueError("Unexpected competition footprint size")
    return footprint, footprint & catalogue


def current_registry(footprint: np.ndarray) -> tuple[list[dict], dict]:
    """Build a current nine-site artifact registry from the pinned GitHub audit."""
    audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    if audit.get("priority_inventory_retrieved") is not True:
        raise ValueError("Nine-site priority audit is not complete")
    entries: list[dict] = []
    seen = set()
    for repository in audit["repositories"]:
        for item in repository["priority_rasters"]:
            local_path = item["local_path"]
            path = (ROOT / local_path).resolve()
            if not path.is_relative_to(ROOT) or not path.is_file():
                raise ValueError(f"Priority artifact is absent: {local_path}")
            if item["sha256"] in seen:
                continue
            seen.add(item["sha256"])
            entries.append(
                {
                    "id": f"{repository['repository']}:{item['file']}",
                    "file": item["file"],
                    "cache_path": local_path,
                    "sha256": item["sha256"],
                    "footprint_sha256": item["footprint_values_sha256"],
                }
            )
    if not CONTROL_PATH.is_file() or sha256_file(CONTROL_PATH) != "b4570b406efec198eb2f4d142ad8d0d6184b14b66f2f52b5c4d697f0647dc9b2":
        raise ValueError("Pinned spacing-five calibration control is missing or changed")
    with rasterio.open(CONTROL_PATH) as control:
        control_values = control.read(1)[footprint].astype("<f4")
    control_footprint_sha = hashlib.sha256(control_values.tobytes()).hexdigest()
    entries.append(
        {
            "id": "shared-calibration-spacing-five",
            "file": CONTROL_FILE,
            "cache_path": str(CONTROL_PATH.relative_to(ROOT)),
            "sha256": sha256_file(CONTROL_PATH),
            "footprint_sha256": control_footprint_sha,
            "source": CONTROL_SOURCE,
        }
    )
    return entries, {
        "scope": "latest selected artifacts from the nine requested repositories plus one pinned calibration control",
        "complete_for_requested_sites": True,
        "external_parallel_registry_complete": False,
        "artifact_count": len(entries),
        "control": CONTROL_SOURCE,
        "limitation": "This is not a synchronized registry of unpublished or unseen parallel-session rasters; literal control failures remain binding.",
    }


def place_dots(shared, surface: np.ndarray, footprint: np.ndarray, catalogue: np.ndarray) -> np.ndarray:
    eligible = footprint & ~catalogue
    nms = shared.metric.ridge_nms(surface, eligible, sigma=1.0)
    return shared.metric.select_top_positive(surface, nms & eligible, K_DOTS).astype(bool)


def random_control(ho, footprint: np.ndarray, seed: int = 20261029) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    predictions = []
    for fold in ho.folds:
        eligible = footprint & ~fold["visible"]
        ids = np.flatnonzero(eligible.ravel())
        if len(ids) < K_DOTS:
            raise ValueError("Random-K control has fewer eligible cells than the fixed budget")
        mask = np.zeros(footprint.size, dtype=bool)
        mask[rng.choice(ids, size=K_DOTS, replace=False)] = True
        predictions.append(mask.reshape(footprint.shape))
    return predictions


def feature_canary(ho, per_layer: dict[str, np.ndarray], surface: np.ndarray) -> dict:
    return ho.canary({**per_layer, "tcb_fused_surface": surface}, seed=20261029)


def make_run_card(*, result: dict, started: str, runtime: float) -> dict:
    return {
        "run_card_schema": "s28-tcb-v1",
        "run_id": RUN_ID,
        "branch": "arena/09c38505-gemsdoe28",
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "started_at_utc": started,
        "hypothesis": "S26-TCB: a concealed damage zone changes directional texture covariance across a boundary even when broad field amplitude is weak.",
        "layers": list(LAYER_NAMES),
        "mechanism": "Side-specific mean-removed tangent covariance at 2, 4, and 8 pixels, four unoriented normals; geometric-mean fusion across RTP, TMI-HG, and conductivity.",
        "named_non_fault_mimic": "Depositional facies or intrusive contacts, airborne leveling seams, and raster resampling can create the same covariance discontinuity.",
        "evaluator": {
            "label": "HOLDOUT-DTI",
            "version": EVALUATOR_VERSION,
            "buffer_m": BUFFER_PX * 100,
            "alpha": 0.2,
            "beta": 0.8,
            "triangular_kernel_radius_m": 300,
            "whole_segments_hidden": True,
            "visible_fault_mask": "pixel-exact",
            "catalogue_features": "none; the TCB surface is label-free",
        },
        "holdout": result.get("holdout"),
        "random_k_control": result.get("random_k_control"),
        "paired_vs_random_k": result.get("paired_vs_random_k"),
        "frozen_s25_reference": result.get("frozen_s25_reference"),
        "feature_canaries": result.get("feature_canaries"),
        "registry": result.get("registry"),
        "surface_before_placement": result.get("surface_before_placement"),
        "final_dots": result.get("final_dots"),
        "raster_sha256": result.get("raster_sha256"),
        "validator": result.get("validator"),
        "submission_name": result.get("submission_name"),
        "note": result.get("note"),
        "estimated_leaderboard_score": None,
        "estimate_status": "Unavailable; no organizer receipt or validated transfer calibration maps this HOLDOUT-DTI to the hidden leaderboard.",
        "verdict": result.get("verdict", "negative"),
        "submission_ready": False,
        "ok_to_submit": False,
        "ok_to_download_new_submission": False,
        "new_tiff_generated": bool(result.get("new_tiff_generated", False)),
        "experiments_run": 1,
        "experiment_cap": 3,
        "time_cap_seconds": 7200,
        "slot_selected": False,
        "submission_slots_spent": 0,
        "runtime_seconds": round(runtime, 1),
        "limitations": result.get("limitations", []),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=OUT_PATH)
    args = parser.parse_args(argv)
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    t0 = time.monotonic()
    result: dict = {"new_tiff_generated": False, "raster_sha256": None, "validator": None, "submission_name": None, "note": None}
    try:
        shared = __import__("gems27.shared_template", fromlist=["load_shared"]).load_shared(ROOT)
        footprint, catalogue = read_footprint_and_catalogue()
        layers, cache = read_cached_layers(footprint)
        surface, per_layer = build_surface(layers, footprint)
        entries, registry_meta = current_registry(footprint)
        surface_registry = shared.novelty.compare_registry(
            surface,
            footprint,
            entries,
            ROOT,
            template_path=paths.TEMPLATE,
            sample_size=200_000,
        )
        result["cache"] = cache
        result["registry"] = {
            **registry_meta,
            "entries": entries,
            "surface_comparison": surface_registry,
        }
        # The canary happens before trusting the fused surface for placement.
        ho = shared.holdout.SegmentHoldout(footprint, catalogue, buffer_px=BUFFER_PX)
        canary = feature_canary(ho, per_layer, surface)
        result["feature_canaries"] = canary
        predictions = []
        final = None
        final_registry = None
        if surface_registry["passed"] and canary["passed"]:
            final = place_dots(shared, surface, footprint, catalogue)
            entries_for_final = entries
            final_registry = shared.novelty.compare_registry(
                surface,
                footprint,
                entries_for_final,
                ROOT,
                dots=final,
                template_path=paths.TEMPLATE,
                sample_size=200_000,
            )
            if not final_registry["passed"]:
                result["final_dots"] = {
                    "placed_in_memory": True,
                    "dots": int(final.sum()),
                    "comparison": final_registry,
                    "status": "DUPLICATE_STOP; no TIFF serialized",
                }
            else:
                for fold in ho.folds:
                    eligible = footprint & ~fold["visible"]
                    # The surface is label-free; only the pixel-exact visible mask
                    # controls which cells can be emitted in the fold.
                    nms = shared.metric.ridge_nms(surface, eligible, sigma=1.0)
                    predictions.append(shared.metric.select_top_positive(surface, nms & eligible, K_DOTS).astype(bool))
                final_values = np.where(final, np.float32(1.0), np.float32(0.0))
                cid = submission.scored_content_id(final_values, footprint, catalogue)
                name = submission.make_filename("gems28", "s28-tcb-k37654", "20261029", cid, "nan")
                path = ROOT / "docs/downloads" / name
                submission.write_geotiff(final_values, paths.TEMPLATE, path, outside="nan")
                validator = submission.verify_geotiff(path, paths.TEMPLATE)
                result["new_tiff_generated"] = bool(validator["hard_checks_passed"])
                result["raster_sha256"] = validator["sha256"]
                result["validator"] = validator
                result["submission_name"] = name
                result["note"] = submission.make_note("S28-TCB", "directional covariance boundary", cid, family="GEMSDOE28")
                result["final_dots"] = {"placed_in_memory": True, "dots": int(final.sum()), "comparison": final_registry}
        else:
            result["final_dots"] = {"placed_in_memory": False, "status": "STOP before placement: surface novelty or leakage canary failed"}

        random_predictions = random_control(ho, footprint)
        if not predictions and final is not None:
            # A duplicate final is still evaluated scientifically so the negative
            # result is useful; no file is written and no slot is selected.
            for fold in ho.folds:
                eligible = footprint & ~fold["visible"]
                nms = shared.metric.ridge_nms(surface, eligible, sigma=1.0)
                predictions.append(shared.metric.select_top_positive(surface, nms & eligible, K_DOTS).astype(bool))
        if predictions:
            holdout = ho.summarize(predictions)
            control = ho.summarize(random_predictions)
            paired = ho.compare_paired(predictions, random_predictions)
        else:
            holdout = control = paired = None
        result["holdout"] = holdout
        result["random_k_control"] = control
        result["paired_vs_random_k"] = paired
        frozen = json.loads((ROOT / "evidence/s25_pcse_holdout.json").read_text(encoding="utf-8"))
        result["frozen_s25_reference"] = {
            "label": "HOLDOUT-DTI",
            "evaluator_version": frozen["holdout"]["evaluator_version"],
            "dti": frozen["holdout"]["dti"],
            "ci95": frozen["holdout"]["ci95"]["interval"],
            "withheld_positives": frozen["holdout"]["n_withheld_positive_pixels"],
            "status": "historical same-protocol PCSE reference; not a leaderboard score",
        }
        result["surface_before_placement"] = {
            "status": "PASS" if surface_registry["passed"] else "DUPLICATE_STOP",
            "comparison": surface_registry,
        }
        result["limitations"] = [
            "The nine-site registry snapshot is complete only for the selected published artifacts available to this checkout; it is not a synchronized registry of unseen parallel sessions.",
            "The literal spacing-five calibration control is retained. Any final-dot overlap failure is binding; no registry-aware relocation or budget tuning is performed.",
            "HOLDOUT-DTI uses catalogue-internal withheld components and is not a calibrated hidden-leaderboard estimate.",
            "No organizer-authenticated inputs or score receipt were available; restored bytes are owner-supplied GitHub mirrors with hash pins.",
        ]
        # Promotion is intentionally stricter than format validity.
        result["verdict"] = "promote" if (
            result["new_tiff_generated"]
            and holdout is not None
            and paired is not None
            and paired["ci95_strictly_positive"]
            and canary["passed"]
            and surface_registry["passed"]
            and bool(final_registry and final_registry["passed"])
        ) else "negative"
    except Exception as exc:  # The run card must replace any stale green result.
        result["verdict"] = "negative"
        result["error"] = {"type": type(exc).__name__, "message": str(exc)}
        result["limitations"] = ["Run stopped before a scientifically valid candidate was approved; inspect the error and do not infer a score."]
    card = make_run_card(result=result, started=started, runtime=time.monotonic() - t0)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(json.dumps({
        "out": str(args.out),
        "verdict": card["verdict"],
        "new_tiff_generated": card["new_tiff_generated"],
        "holdout_dti": (card["holdout"] or {}).get("dti") if isinstance(card.get("holdout"), dict) else None,
        "surface_status": (card["surface_before_placement"] or {}).get("status") if isinstance(card.get("surface_before_placement"), dict) else None,
        "runtime_seconds": card["runtime_seconds"],
    }, indent=2))
    return 0 if card["verdict"] == "promote" else 1


if __name__ == "__main__":
    raise SystemExit(main())
