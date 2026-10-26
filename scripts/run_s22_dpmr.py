#!/usr/bin/env python3
"""Run the frozen S22 displaced piercing-marker lane in three fail-closed stages.

Preregistration: knowledge/62_s22_preregistration.md.  This runner never logs in to
DrivenData, uploads a file, selects a weekly slot, or changes frozen parameters after
observing holdout results.
"""
from __future__ import annotations

import argparse
import gc
import hashlib
import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from gems27 import grid, heatflow_euler, paths, piercing_markers, submission  # noqa: E402
from gems27.shared_template import verify_assets  # noqa: E402

# Import the verified shared package only after checking its immutable pins.
SHARED_CHECK = verify_assets(ROOT)
if not SHARED_CHECK["passed"]:
    raise RuntimeError("Pinned shared evaluator/writer integrity failed")
sys.path.insert(0, str(ROOT / "data/shared_template/src"))
from gems import holdout as shared_holdout  # noqa: E402
from gems import novelty as shared_novelty  # noqa: E402
from gems import submission as shared_submission  # noqa: E402

PREREG = ROOT / "knowledge/62_s22_preregistration.md"
SNAPSHOT = ROOT / "evidence/s22_registry_snapshot.json"
REGISTRY_MANIFEST = ROOT / "evidence/s22_registry_manifest.json"
STARTED = ROOT / "evidence/s22_dpmr.started.json"
EXP1 = ROOT / "evidence/s22_dpmr_exp1_surface.json"
EXP2 = ROOT / "evidence/s22_dpmr_exp2_holdout.json"
EXP3 = ROOT / "evidence/s22_dpmr_exp3_emission.json"
RUN_CARD = ROOT / "evidence/s22_dpmr_run_card.json"
CACHE = ROOT / "data/s22_dpmr"
SURFACE_PATH = CACHE / "surface.npy"
FINAL_PATH = CACHE / "final_prediction.npy"
TARGET_DOTS = 37_654
BUFFER_PX = 15
BOOTSTRAP_DRAWS = 1999
BOOTSTRAP_SEED = 20261036


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def save_json(value: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, allow_nan=False, default=float) + "\n")


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_inputs() -> tuple[np.ndarray, np.ndarray, dict, np.ndarray]:
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS) & foot
    metadata = json.loads(paths.PREPARED_META.read_text(encoding="utf-8"))
    if sha256_file(paths.PREPARED_FEATURES) != metadata["sha256"]:
        raise RuntimeError("Prepared feature cache hash mismatch")
    matrix = np.load(paths.PREPARED_FEATURES, mmap_mode="r", allow_pickle=False)
    if list(matrix.shape) != metadata["shape"] or matrix.dtype != np.float32:
        raise RuntimeError("Prepared feature cache contract mismatch")
    return foot, labels, metadata, matrix


def unpack_feature(matrix: np.ndarray, metadata: dict, footprint: np.ndarray, name: str) -> np.ndarray:
    names = metadata["names"]
    if name not in names:
        raise KeyError(f"Prepared feature missing: {name}")
    result = np.full(footprint.shape, np.nan, dtype=np.float32)
    result[footprint] = np.asarray(matrix[:, names.index(name)], dtype=np.float32)
    return result


def normalize_registry(footprint: np.ndarray) -> dict:
    """Deduplicate the frozen pre-run snapshot by exact in-footprint values.

    Published NaN-outside/all-finite twins become one comparison member.  Invalid
    inside values are converted only in an explicitly flagged comparison cache;
    original Git-pinned bytes and hashes remain in the snapshot.
    """
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    if not snapshot.get("complete_within_declared_scope"):
        raise RuntimeError("The frozen nine-site registry snapshot is incomplete")
    normalized_dir = CACHE / "registry_normalized"
    normalized_dir.mkdir(parents=True, exist_ok=True)
    unique: dict[str, dict] = {}
    exclusions: list[dict] = []
    for entry in snapshot["entries"]:
        if entry.get("status") != "included":
            exclusions.append({"path": entry.get("path"), "reason": entry.get("status")})
            continue
        source = ROOT / entry["local_path"]
        with rasterio.open(source) as dataset:
            values = dataset.read(1)
            if values.shape != footprint.shape:
                exclusions.append({"path": entry.get("path"), "reason": "shape mismatch"})
                continue
        inside = np.asarray(values[footprint], dtype=np.float32)
        nonfinite = int((~np.isfinite(inside)).sum())
        out_of_range = int((np.isfinite(inside) & ((inside < 0) | (inside > 1))).sum())
        normalized = np.nan_to_num(values, nan=0.0, posinf=1.0, neginf=0.0).astype(np.float32)
        normalized = np.clip(normalized, 0.0, 1.0)
        normalized[~footprint] = 0.0
        footprint_sha = hashlib.sha256(normalized[footprint].astype("<f4").tobytes()).hexdigest()
        if footprint_sha in unique:
            unique[footprint_sha]["aliases"].append(
                {"repo": entry.get("repo"), "path": entry.get("path"), "sha256": entry.get("sha256")}
            )
            continue
        target = normalized_dir / f"{footprint_sha}.tif"
        profile = None
        with rasterio.open(paths.TEMPLATE) as template:
            profile = template.profile.copy()
        profile.update(driver="GTiff", dtype="float32", count=1, nodata=None, compress="lzw")
        with rasterio.open(target, "w", **profile) as destination:
            destination.write(normalized, 1)
        unique[footprint_sha] = {
            "id": f"s22-registry-{len(unique) + 1:03d}",
            "file": entry.get("path", source.name),
            "cache_path": str(target.relative_to(ROOT)),
            "footprint_sha256": footprint_sha,
            "source_raster_sha256": entry.get("sha256"),
            "source_repo": entry.get("repo"),
            "inside_nonfinite_replaced_for_comparison": nonfinite,
            "inside_out_of_range_clipped_for_comparison": out_of_range,
            "aliases": [],
        }
    members = list(unique.values())
    manifest = {
        "schema": 1,
        "generated_utc": utc_now(),
        "session": "S22-DPMR",
        "snapshot_path": str(SNAPSHOT.relative_to(ROOT)),
        "snapshot_sha256": sha256_file(SNAPSHOT),
        "scope": snapshot["scope"],
        "complete_within_declared_scope": True,
        "global_parallel_registry_complete": False,
        "source_entries": len(snapshot["entries"]),
        "unique_footprint_rasters": len(members),
        "excluded": exclusions,
        "members": members,
    }
    save_json(manifest, REGISTRY_MANIFEST)
    manifest["manifest_sha256"] = sha256_file(REGISTRY_MANIFEST)
    return manifest


def placement(surface: np.ndarray, domain: np.ndarray, visible: np.ndarray, target: int) -> np.ndarray:
    distance_visible = distance_transform_edt(~visible) if visible.any() else np.full(domain.shape, np.inf)
    eligible = domain & (distance_visible > 2.0)
    return piercing_markers.greedy_place(surface, eligible, target)


def registry_summary(result: dict) -> dict:
    rows = result["rows"]
    worst_corr = max(
        (
            (abs(row[key]), row["registry_id"], key)
            for row in rows
            for key in ("raw_spearman", "kernel_spearman")
            if row[key] is not None
        ),
        default=(None, None, None),
    )
    worst_overlap = max(
        (
            (row["candidate_dot_overlap_within_3px"], row["registry_id"])
            for row in rows
            if row["candidate_dot_overlap_within_3px"] is not None
        ),
        default=(None, None),
    )
    return {
        "passed": result["passed"],
        "registry_unique_rasters": result["registry_unique_rasters"],
        "max_abs_rank_correlation": result["max_abs_rank_correlation"],
        "max_rank_member": worst_corr[1],
        "max_rank_statistic": worst_corr[2],
        "max_dot_overlap_within_3px": result["max_dot_overlap"],
        "max_overlap_member": worst_overlap[1],
        "rows": rows,
    }


def run_exp1() -> int:
    if EXP1.exists() or STARTED.exists():
        raise SystemExit("S22 Experiment 1 already started; refusing an implicit rerun")
    CACHE.mkdir(parents=True, exist_ok=True)
    started = time.monotonic()
    start_record = {
        "session": "S22-DPMR",
        "started_utc": utc_now(),
        "preregistration": str(PREREG.relative_to(ROOT)),
        "preregistration_sha256": sha256_file(PREREG),
        "base_commit": "2c839d10f57ec9b074829e93c84bc39935f52896",
        "implementation_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
        "maximum_experiments": 3,
        "maximum_seconds": 7200,
        "shared_assets": SHARED_CHECK,
        "slot_selected": False,
    }
    save_json(start_record, STARTED)
    foot, labels, metadata, matrix = load_inputs()
    rtp = unpack_feature(matrix, metadata, foot, "rtp")
    gravity = unpack_feature(matrix, metadata, foot, "iso_grav_anom")
    del matrix
    print("[Exp 1/3] Building deterministic displaced-marker surface...", flush=True)
    surfaces, transform_metadata = piercing_markers.build_surface(rtp, gravity, foot)
    del rtp, gravity
    np.save(SURFACE_PATH, surfaces["candidate"], allow_pickle=False)

    context = shared_holdout.SegmentHoldout(foot, labels, buffer_px=BUFFER_PX)
    print("[Exp 1/3] Running every feature alone through the shared leakage canary...", flush=True)
    canary = context.canary(surfaces, seed=BOOTSTRAP_SEED)
    manifest = normalize_registry(foot)
    members = manifest["members"]
    prospective = piercing_markers.greedy_place(surfaces["candidate"], foot, TARGET_DOTS)
    print(
        f"[Exp 1/3] Pre-placement surface + {int(prospective.sum())} prospective dots vs "
        f"{len(members)} unique registry rasters...",
        flush=True,
    )
    novelty = shared_novelty.compare_registry(
        surfaces["candidate"], foot, members, ROOT, dots=prospective, sample_size=200_000
    )
    novelty_compact = registry_summary(novelty)
    stopped = None
    if not canary["passed"]:
        stopped = "leakage-canary"
    elif not novelty["passed"]:
        stopped = "duplicate-surface-or-prospective-dots"
    result = {
        "experiment": 1,
        "session": "S22-DPMR",
        "label": "LEAKAGE-CANARY / REGISTRY NOVELTY — NOT A SCORE",
        "generated_utc": utc_now(),
        "elapsed_seconds": time.monotonic() - started,
        "inputs": {
            "prepared_features_sha256": metadata["sha256"],
            "prepared_features_names": metadata["names"],
            "template_sha256": sha256_file(paths.TEMPLATE),
            "labels_sha256": sha256_file(paths.LABELS),
        },
        "transform": transform_metadata,
        "surface_path_ignored_cache": str(SURFACE_PATH.relative_to(ROOT)),
        "surface_sha256": sha256_file(SURFACE_PATH),
        "canary": canary,
        "registry_manifest": str(REGISTRY_MANIFEST.relative_to(ROOT)),
        "registry_manifest_sha256": manifest["manifest_sha256"],
        "preplacement": novelty_compact,
        "prospective_dots": int(prospective.sum()),
        "passed": stopped is None,
        "stopped_reason": stopped,
        "submission_slot_spent": False,
    }
    save_json(result, EXP1)
    print(json.dumps({"passed": result["passed"], "stopped_reason": stopped,
                      "canary_passed": canary["passed"],
                      "max_abs_spearman": novelty_compact["max_abs_rank_correlation"],
                      "max_3px_overlap": novelty_compact["max_dot_overlap_within_3px"],
                      "elapsed_seconds": result["elapsed_seconds"]}, indent=2), flush=True)
    return 0 if result["passed"] else 2


def active_block_ids(footprint: np.ndarray) -> np.ndarray:
    yy, xx = np.nonzero(footprint)
    columns = (footprint.shape[1] + 99) // 100
    return np.unique((yy // 100) * columns + xx // 100)


def score_predictions(context, predictions, active_blocks):
    summary = context.summarize(predictions, ci_draws=BOOTSTRAP_DRAWS)
    block_rows = []
    for prediction, fold in zip(predictions, context.folds, strict=True):
        _, blocks = context.score_fold(prediction, fold)
        block_rows.append(blocks)
    return summary, np.sum(block_rows, axis=0)[active_blocks]


def run_exp2() -> int:
    if not EXP1.exists() or not json.loads(EXP1.read_text())["passed"]:
        raise SystemExit("Experiment 1 did not pass; S22 lane is stopped")
    if EXP2.exists():
        raise SystemExit("S22 Experiment 2 already recorded; refusing an implicit rerun")
    started = time.monotonic()
    foot, labels, _, _ = load_inputs()
    surface = np.load(SURFACE_PATH, allow_pickle=False)
    context = shared_holdout.SegmentHoldout(foot, labels, buffer_px=BUFFER_PX)
    candidate_predictions = []
    allocations = []
    print("[Exp 2/3] Placing fold-local visible-only candidate dots...", flush=True)
    for fold in context.folds:
        target = int(round(TARGET_DOTS * int(fold["valid"].sum()) / int(foot.sum())))
        pred = placement(surface, fold["valid"], fold["visible"], target)
        candidate_predictions.append(pred.astype(np.float32))
        allocations.append({"fold": fold["name"], "target": target, "emitted": int(pred.sum()),
                            "visible_overlap": int((pred & fold["visible"]).sum())})

    # Reuse the already-tested S20 baseline constructor verbatim, rather than forking it.
    from scripts.run_s20_nchc import baseline_b0_and_b1_32band_fold

    hf = heatflow_euler.load_heatflow_residual_cells(paths.SB_HEAT_FLOW_JSON, foot)
    euler = heatflow_euler.load_euler_contact_clusters(paths.EULER_CLUSTERS_CSV, foot.shape)
    hf_halo = distance_transform_edt(~hf["mask"]) <= heatflow_euler.HF_RADIUS_PX
    euler_halo = distance_transform_edt(~euler["mask"]) <= heatflow_euler.EULER_RADIUS_PX
    fields = {
        "joint_mask": (hf_halo | euler_halo) & foot,
        "score_mult": (
            1.0
            + heatflow_euler.BONUS_HF * hf_halo.astype(np.float32)
            + heatflow_euler.BONUS_EULER * euler_halo.astype(np.float32)
        ).astype(np.float32),
    }
    del hf_halo, euler_halo, hf, euler
    baseline_b0, baseline_b1 = [], []
    print("[Exp 2/3] Recomputing visible-only B0 H38 and B1 champion-analogue baselines...", flush=True)
    for fold in context.folds:
        b0, b1 = baseline_b0_and_b1_32band_fold(fold, foot, fields)
        baseline_b0.append(b0)
        baseline_b1.append(b1)
        gc.collect()
    del fields

    blocks = active_block_ids(foot)
    candidate_summary, candidate_blocks = score_predictions(context, candidate_predictions, blocks)
    b0_summary, b0_blocks = score_predictions(context, baseline_b0, blocks)
    b1_summary, b1_blocks = score_predictions(context, baseline_b1, blocks)
    paired_b0 = shared_holdout.pooled_bootstrap(
        candidate_blocks, paired=b0_blocks, resamples=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED
    )
    paired_b1 = shared_holdout.pooled_bootstrap(
        candidate_blocks, paired=b1_blocks, resamples=BOOTSTRAP_DRAWS, seed=BOOTSTRAP_SEED + 1
    )
    delta_b0 = float(candidate_summary["dti"] - b0_summary["dti"])
    delta_b1 = float(candidate_summary["dti"] - b1_summary["dti"])
    fold_wins_b0 = sum(
        a["dti"] > b["dti"]
        for a, b in zip(candidate_summary["folds"], b0_summary["folds"], strict=True)
    )
    gate = bool(delta_b0 > 0 and paired_b0[0] > 0)
    result = {
        "experiment": 2,
        "session": "S22-DPMR",
        "generated_utc": utc_now(),
        "elapsed_seconds": time.monotonic() - started,
        "label": "HOLDOUT-DTI",
        "evaluator_version": shared_holdout.MTR_EVALUATOR_VERSION,
        "shared_evaluate_holdout_sha256": next(
            row["sha256"] for row in SHARED_CHECK["files"] if row["id"] == "template-evaluate_holdout"
        ),
        "shared_evaluator_note": (
            "The pinned evaluate_holdout.py is a hypothesis-specific runner, so this lane imports its "
            "hash-identical gems.holdout.SegmentHoldout authority; no private metric/evaluator fork."
        ),
        "candidate": candidate_summary,
        "candidate_allocations": allocations,
        "primary_baseline_b0_visible_only_32band_h38": b0_summary,
        "secondary_baseline_b1_visible_only_d28_b2_champion_analogue": b1_summary,
        "paired_vs_b0": {
            "delta_dti": delta_b0,
            "ci95": paired_b0,
            "folds_improved": f"{fold_wins_b0}/4",
            "passed_positive_ci95": gate,
        },
        "paired_vs_b1": {
            "delta_dti": delta_b1,
            "ci95": paired_b1,
        },
        "gate_passed": gate,
        "verdict": "promote-to-selector" if gate else "negative",
        "submission_slot_spent": False,
        "limitations": [
            "Mapped-fault hide-and-recover is a local proxy, not organizer hidden truth.",
            "The deterministic physical candidate is not trained per fold; catalogue is used only for visible-only placement masking.",
            "No leaderboard score or organizer receipt was observed.",
        ],
    }
    save_json(result, EXP2)
    print(json.dumps({"candidate_holdout_dti": candidate_summary["dti"],
                      "candidate_ci95": candidate_summary["ci95"]["interval"],
                      "baseline_b0_dti": b0_summary["dti"], "delta_b0": delta_b0,
                      "paired_delta_ci95": paired_b0, "gate_passed": gate,
                      "elapsed_seconds": result["elapsed_seconds"]}, indent=2), flush=True)
    return 0


def call_shared_writer(prediction: Path, output: Path, outside: str) -> dict:
    script = ROOT / "data/shared_template/scripts/submission_writer.py"
    process = subprocess.run(
        [sys.executable, str(script), str(prediction), str(output), "--template", str(paths.TEMPLATE),
         "--outside", outside],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(process.stdout)


def make_run_card(exp1: dict, exp2: dict, exp3: dict) -> dict:
    canaries = {
        name: row["pooled_auc"] for name, row in exp1["canary"]["features"].items()
    }
    candidate = exp2["candidate"]
    b1 = exp2["secondary_baseline_b1_visible_only_d28_b2_champion_analogue"]
    delta_ci = exp2["paired_vs_b1"]["ci95"]
    anchor = 0.2778
    estimate = anchor * candidate["dti"] / b1["dti"] if b1["dti"] > 0 else None
    estimate_range = (
        [
            max(0.0, anchor * (b1["dti"] + delta_ci[0]) / b1["dti"]),
            max(0.0, anchor * (b1["dti"] + delta_ci[1]) / b1["dti"]),
        ]
        if b1["dti"] > 0
        else None
    )
    scientific_pass = bool(
        exp1["passed"] and exp2["gate_passed"] and exp3["registry"]["passed"]
        and exp3["validator"]["allfinite_shared"]["format_valid"]
        and exp3["validator"]["allfinite_local"]["hard_checks_passed"]
    )
    reasons = []
    if not exp2["gate_passed"]:
        reasons.append("paired HOLDOUT-DTI superiority gate failed")
    if not exp3["registry"]["passed"]:
        reasons.append("strict registry duplicate gate failed")
    if not exp3["validator"]["allfinite_shared"]["format_valid"]:
        reasons.append("shared exact-file format gate failed")
    if not exp3["validator"]["allfinite_local"]["hard_checks_passed"]:
        reasons.append("independent local exact-file gate failed")
    if not exp3["registry_global_parallel_complete"]:
        reasons.append("registry is complete only within the pinned nine-site/local scope")
    if scientific_pass:
        reasons.append("separate authenticated weekly-slot selector has not run")
    registry_manifest = json.loads(REGISTRY_MANIFEST.read_text())
    return {
        "schema_version": 1,
        "session": "S22-DPMR",
        "execution_provenance": {
            "preregistration_commit": "9b703e59283ad8f4fac86ec37d2e91f5c6d9c64e",
            "transform_and_registry_commit": "3450ff2d85140e71fb1452347d8fd32cb4c8fa5d",
            "experiment_1_head": "c9f2f07eb2bda5e58d10e598e7900665d4340164",
            "experiment_2_head": "36742be55e4e6c19708ba5f81af6e865842d929b",
            "experiment_3_head": "fd1cd19444e4c82fb955e2843e3605135be0ab22",
            "void_startup": "evidence/s22_dpmr_exp2_void_import.json",
        },
        "lane": "Displaced potential-field piercing-marker registration (self-assigned; no external exclusivity claimed)",
        "hypothesis": (
            "A concealed fault offsets pre-existing magnetic/density marker patterns; a common non-zero "
            "cross-corridor registration shift identifies the fault plane rather than the marker contact."
        ),
        "mechanism": (
            "Two-scale opposite-side patch NCC gain at a common ±200–600 m along-strike displacement "
            "in RTP and isostatic gravity, followed by 2.8 px catalogue-clear placement."
        ),
        "non_fault_mimic": "Intrusive or branching lithologic contacts, survey seams, and chance repeated potential-field texture.",
        "feature_canaries": canaries,
        "holdout": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": candidate["evaluator_version"],
            "dti": candidate["dti"],
            "ci95": candidate["ci95"]["interval"],
            "withheld_positives": candidate["n_withheld_positive_pixels"],
            "paired_gain_vs_baseline": exp2["paired_vs_b0"]["delta_dti"],
            "paired_gain_ci95": exp2["paired_vs_b0"]["ci95"],
            "baseline_dti": exp2["primary_baseline_b0_visible_only_32band_h38"]["dti"],
            "baseline_sha256": sha256_file(
                ROOT / "docs/downloads/gems28-h38-1-hf-euler-r30-r1-20261003-56a9f473edc7-allfinite.tif"
            ),
            "raster_sha256": exp3["files"]["allfinite_sha256"],
            "whole_segments": True,
            "buffered": True,
            "visible_only_features": True,
            "pixel_exact_visible_mask": True,
            "pooled": True,
            "alpha": 0.2,
            "beta": 0.8,
            "kernel_m": 300,
            "kernel": "triangular",
        },
        "registry": {
            "complete": False,
            "complete_within_declared_scope": True,
            "scope": registry_manifest["scope"],
            "manifest_sha256": sha256_file(REGISTRY_MANIFEST),
            "members": [row["footprint_sha256"] for row in registry_manifest["members"]],
            "surface_max_abs_spearman": exp1["preplacement"]["max_abs_rank_correlation"],
            "surface_prospective_max_overlap_3px": exp1["preplacement"]["max_dot_overlap_within_3px"],
            "final_max_abs_spearman": exp3["registry"]["max_abs_rank_correlation"],
            "final_max_overlap_3px": exp3["registry"]["max_dot_overlap_within_3px"],
            "surface": [
                {"raster_sha256": row["footprint_sha256"],
                 "spearman": row["raw_spearman"],
                 "within_3px_fraction": row["candidate_dot_overlap_within_3px"]}
                for row in exp1["preplacement"]["rows"]
            ],
            "dots": [
                {"raster_sha256": row["footprint_sha256"],
                 "spearman": row["raw_spearman"],
                 "within_3px_fraction": row["candidate_dot_overlap_within_3px"]}
                for row in exp3["registry"]["rows"]
            ],
        },
        "raster_sha256": exp3["files"]["allfinite_sha256"],
        "validator": exp3["validator_summary"],
        "submission_name": exp3["submission_name"],
        "note": exp3["note"],
        "note_chars": len(exp3["note"]),
        "files": exp3["files"],
        "score_estimate": {
            "label": "MODEL PROJECTION — NOT A SCORE",
            "estimate": estimate,
            "range": estimate_range,
            "method": "0.2778 owner-reported anchor × candidate/champion-analogue HOLDOUT-DTI on identical folds",
            "anchor": "GEMSDOE32 0.2778 USER-REPORTED / UNVERIFIED; no receipt",
        },
        "validator_output": exp3["validator"],
        "verdict": "promote" if scientific_pass else "negative",
        "ok_to_download": True,
        "ok_to_submit": False,
        "submission_ready": False,
        "slot_selected": False,
        "slots_spent": 0,
        "reasons": reasons,
        "experiments_run": 3,
    }


def run_exp3() -> int:
    if not EXP2.exists():
        raise SystemExit("Experiment 2 is missing; refusing final emission")
    if EXP3.exists() or RUN_CARD.exists():
        raise SystemExit("S22 Experiment 3 already recorded; refusing an implicit rerun")
    exp1 = json.loads(EXP1.read_text())
    exp2 = json.loads(EXP2.read_text())
    if not exp1["passed"]:
        raise SystemExit("Experiment 1 drift/leakage stop forbids final placement")
    started = time.monotonic()
    foot, labels, _, _ = load_inputs()
    surface = np.load(SURFACE_PATH, allow_pickle=False)
    final = placement(surface, foot, labels, TARGET_DOTS)
    if int(final.sum()) != TARGET_DOTS:
        raise RuntimeError(f"Frozen placement emitted {int(final.sum())}, expected {TARGET_DOTS}")
    if (final & labels).any() or (final & ~foot).any():
        raise RuntimeError("Final candidate violates catalogue/footprint exclusion")
    manifest = json.loads(REGISTRY_MANIFEST.read_text())
    print(f"[Exp 3/3] Final-dot uniqueness vs {len(manifest['members'])} registry rasters...", flush=True)
    novelty = shared_novelty.compare_registry(
        surface, foot, manifest["members"], ROOT, dots=final, sample_size=200_000
    )
    compact_novelty = registry_summary(novelty)
    if not novelty["passed"]:
        result = {
            "experiment": 3,
            "session": "S22-DPMR",
            "generated_utc": utc_now(),
            "elapsed_seconds": time.monotonic() - started,
            "registry": compact_novelty,
            "verdict": "negative-duplicate-stop",
            "tif_written": False,
            "submission_slot_spent": False,
        }
        save_json(result, EXP3)
        print(json.dumps(result, indent=2), flush=True)
        return 2

    np.save(FINAL_PATH, final.astype(np.float32), allow_pickle=False)
    content_id = shared_submission.scored_content_id(final.astype(np.float32), foot, labels)
    stem = f"gems28-s22-dpmr-20261026-{content_id}"
    downloads = ROOT / "docs/downloads"
    allfinite = downloads / f"{stem}-allfinite.tif"
    nan_file = downloads / f"{stem}-nan.tif"
    print("[Exp 3/3] Writing exact GeoTIFFs through the pinned shared submission_writer.py...", flush=True)
    allfinite_shared = call_shared_writer(FINAL_PATH, allfinite, "zero")
    nan_shared = call_shared_writer(FINAL_PATH, nan_file, "nan")
    zip_path = shared_submission.zip_single(nan_file, downloads / f"{stem}-nan.zip")
    allfinite_local = submission.verify_geotiff(allfinite, paths.TEMPLATE)
    nan_local = submission.verify_geotiff(nan_file, paths.TEMPLATE)
    note = (
        f"S22 DPMR displaced RTP+gravity markers {TARGET_DOTS}d | HOLDOUT "
        f"{exp2['candidate']['dti']:.4f} vs {exp2['primary_baseline_b0_visible_only_32band_h38']['dti']:.4f} | "
        f"{'SELECTOR PENDING' if exp2['gate_passed'] else 'NEGATIVE DO NOT SUBMIT'}"
    )
    if len(note) > 140:
        raise AssertionError(f"Note has {len(note)} characters")
    (downloads / f"note-{stem}.txt").write_text(note + "\n", encoding="utf-8")
    validator_summary = {
        "raster_sha256": sha256_file(allfinite),
        "no_nan_inside": allfinite_local["checks"]["inside_footprint_all_finite"]["pass"],
        "range_0_1": allfinite_local["checks"]["inside_footprint_in_0_1"]["pass"],
        "crs_match": allfinite_local["checks"]["grid_matches_template"]["pass"],
        "shape_match": allfinite_local["checks"]["grid_matches_template"]["pass"],
        "transform_match": allfinite_local["checks"]["grid_matches_template"]["pass"],
        "single_band": allfinite_local["checks"]["single_band_float32"]["pass"],
        "whole_array_all_finite": bool(allfinite_shared["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"]),
        "catalogue_overlap_pixels": int((final & labels).sum()),
    }
    format_pass = bool(
        allfinite_shared["format_valid"] and nan_shared["format_valid"]
        and allfinite_local["hard_checks_passed"] and nan_local["hard_checks_passed"]
    )
    result = {
        "experiment": 3,
        "session": "S22-DPMR",
        "generated_utc": utc_now(),
        "elapsed_seconds": time.monotonic() - started,
        "registry": compact_novelty,
        "registry_global_parallel_complete": manifest["global_parallel_registry_complete"],
        "validator": {
            "allfinite_shared": allfinite_shared,
            "nan_shared": nan_shared,
            "allfinite_local": allfinite_local,
            "nan_local": nan_local,
        },
        "validator_summary": validator_summary,
        "format_pass": format_pass,
        "files": {
            "allfinite": allfinite.name,
            "allfinite_sha256": sha256_file(allfinite),
            "allfinite_bytes": allfinite.stat().st_size,
            "nan": nan_file.name,
            "nan_sha256": sha256_file(nan_file),
            "nan_bytes": nan_file.stat().st_size,
            "zip": zip_path.name,
            "zip_sha256": sha256_file(zip_path),
            "zip_bytes": zip_path.stat().st_size,
            "positive_pixels": int(final.sum()),
            "content_id": content_id,
        },
        "submission_name": f"GEMSDOE28-S22-DPMR-{content_id}",
        "note": note,
        "verdict": "promote-to-selector" if exp2["gate_passed"] and format_pass else "negative",
        "ok_to_submit": False,
        "slot_selected": False,
        "submission_slot_spent": False,
    }
    save_json(result, EXP3)
    card = make_run_card(exp1, exp2, result)
    save_json(card, RUN_CARD)
    save_json(card, ROOT / "docs/data/run_card_s22.json")
    save_json({"validator": result["validator"], "registry": compact_novelty,
               "verdict": card["verdict"], "ok_to_submit": False},
              downloads / f"checks-{stem}.json")
    print(json.dumps({"verdict": card["verdict"], "ok_to_submit": False,
                      "file": allfinite.name, "sha256": card["raster_sha256"],
                      "dots": int(final.sum()), "max_3px_overlap": compact_novelty["max_dot_overlap_within_3px"],
                      "format_pass": format_pass, "elapsed_seconds": result["elapsed_seconds"]}, indent=2), flush=True)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("stage", choices=("1", "2", "3"))
    args = parser.parse_args(argv)
    return {"1": run_exp1, "2": run_exp2, "3": run_exp3}[args.stage]()


if __name__ == "__main__":
    raise SystemExit(main())
