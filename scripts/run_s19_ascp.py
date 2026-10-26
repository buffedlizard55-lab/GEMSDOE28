#!/usr/bin/env python3
"""Run the three frozen S19-ASCP experiments and write one final JSON card.

This script is single-use: a started marker prevents same-seed retuning. It loads
hash-verified shared holdout/metric/submission code through gems27.shared_template.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import binary_dilation, distance_transform_edt
from scipy.stats import rankdata
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import antislope_scarp, grid, heatflow_euler, oof_detector, packing, paths  # noqa: E402
from gems27.shared_template import load_shared, verify_assets  # noqa: E402

SESSION = "S19-ASCP"
DATE = "20261026"
TARGET_N = 37_654
STARTED = ROOT / "evidence/s19_ascp.started.json"
STAGE = ROOT / "evidence/s19_ascp_stage.json"
HOLDOUT = ROOT / "evidence/s19_ascp_holdout.json"
CARD = ROOT / "evidence/s19_ascp_run_card.json"
PREREG = ROOT / "knowledge/55_s19_preregistration.md"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_surface() -> tuple[np.ndarray, dict[str, np.ndarray]]:
    with rasterio.open(paths.LIDAR) as src:
        descriptions = tuple(src.descriptions)
        expected = ("ex_max", "ex_mean", "step_max", "lapneg_max", "lappos_max",
                    "downface_max", "upface_max", "cross_max", "relief", "coh100",
                    "strike", "valid")
        if descriptions != expected:
            raise ValueError(f"Unexpected LiDAR bands: {descriptions}")
        bands = [src.read(i) for i in (3, 4, 5, 6, 7, 8, 10, 12)]
    return antislope_scarp.build_surface(*bands)


def registry_paths() -> list[Path]:
    candidates = list((paths.DATA / "priority_repositories").rglob("*.tif"))
    candidates += list((ROOT / "docs/downloads").glob("*.tif"))
    skip = {sha256_file(paths.TEMPLATE), sha256_file(paths.LABELS)}
    seen, result = set(), []
    for path in sorted(candidates):
        digest = sha256_file(path)
        if digest in seen or digest in skip:
            continue
        try:
            with rasterio.open(path) as src:
                good = src.count == 1 and src.shape == grid.SHAPE and src.crs.to_epsg() == 32611
                good &= tuple(src.transform)[:6] == grid.TRANSFORM
            if good:
                seen.add(digest)
                result.append(path)
        except Exception:
            continue
    if len(result) < 20:
        raise ValueError(f"Registry unexpectedly small: {len(result)}")
    return result


def binary_corr(a: np.ndarray, b: np.ndarray, mask: np.ndarray) -> float:
    x, y = np.asarray(a[mask], bool), np.asarray(b[mask], bool)
    p, q = x.mean(), y.mean()
    if p in (0, 1) or q in (0, 1):
        return 0.0
    return float(((x & y).mean() - p * q) / np.sqrt(p * (1 - p) * q * (1 - q)))


def compare_registry(surface: np.ndarray, support: np.ndarray, dots: np.ndarray | None,
                     foot: np.ndarray, registry: list[Path]) -> dict:
    values = surface[foot].astype(np.float64)
    ranks = rankdata(values, method="average")
    mean, std = float(ranks.mean()), float(ranks.std())
    rows = []
    yy, xx = np.ogrid[-3:4, -3:4]
    structure = (yy * yy + xx * xx) <= 9
    for path in registry:
        with rasterio.open(path) as src:
            arr = src.read(1)
        ref = np.isfinite(arr) & (arr > 0) & foot
        p = float(ref[foot].mean())
        corr = 0.0 if p in (0, 1) else float(
            (ranks[ref[foot]].mean() - mean) * np.sqrt(p / (1 - p)) / std
        )
        halo = binary_dilation(ref, structure=structure)
        row = {
            "path": str(path.relative_to(ROOT)),
            "sha256": sha256_file(path),
            "surface_spearman": corr,
            "support_within_3px_fraction": float(halo[support].mean()) if support.any() else 0.0,
            "reference_positive_pixels": int(ref.sum()),
        }
        if dots is not None:
            row["final_spearman"] = binary_corr(dots, ref, foot)
            row["final_dots_within_3px_fraction"] = float(halo[dots].mean()) if dots.any() else 0.0
        rows.append(row)
    max_surface = max(rows, key=lambda x: abs(x["surface_spearman"]))
    max_support = max(rows, key=lambda x: x["support_within_3px_fraction"])
    out = {
        "members": len(rows), "rows": rows,
        "max_abs_surface_spearman": {**max_surface, "value": abs(max_surface["surface_spearman"])},
        "max_support_within_3px": max_support,
    }
    if dots is not None:
        max_final_corr = max(rows, key=lambda x: abs(x["final_spearman"]))
        max_final_overlap = max(rows, key=lambda x: x["final_dots_within_3px_fraction"])
        out.update({
            "max_abs_final_spearman": {**max_final_corr, "value": abs(max_final_corr["final_spearman"])},
            "max_final_dots_within_3px": max_final_overlap,
        })
    out["passed"] = bool(
        abs(max_surface["surface_spearman"]) <= 0.90
        and max_support["support_within_3px_fraction"] <= 0.70
        and (dots is None or (
            abs(out["max_abs_final_spearman"]["final_spearman"]) <= 0.90
            and out["max_final_dots_within_3px"]["final_dots_within_3px_fraction"] <= 0.70
        ))
    )
    return out


def emit_candidate(surface: np.ndarray, valid: np.ndarray, visible: np.ndarray,
                   foot: np.ndarray, n_target: int) -> np.ndarray:
    eligible = valid & foot & ~visible & (distance_transform_edt(~visible) > 2.0)
    ridge = oof_detector.ridge_nms(surface, eligible, sigma=1.0)
    return packing.prob_order_pack(surface, ridge, n_target=n_target, min_dist=2.8)


def baseline_prediction(fold: dict, foot: np.ndarray, labels: np.ndarray,
                        fields: dict, seed: int) -> np.ndarray:
    X = np.load(paths.PREPARED_FEATURES, mmap_mode="r")
    rc = np.argwhere(foot)
    y = fold["visible"][foot]
    train = fold["train"][foot]
    pos, neg = np.flatnonzero(train & y), np.flatnonzero(train & ~y)
    rng = np.random.default_rng(seed)
    chosen = np.sort(np.r_[pos, rng.choice(neg, min(len(neg), 10 * len(pos)), replace=False)])
    clf = HistGradientBoostingClassifier(max_iter=100, max_leaf_nodes=31, learning_rate=0.08,
                                         l2_regularization=5.0, random_state=seed)
    clf.fit(np.asarray(X[chosen], np.float32), y[chosen].astype(int))
    target = np.flatnonzero(fold["valid"][foot])
    scores = np.zeros(grid.SHAPE, np.float32)
    out = np.empty(len(target), np.float32)
    for start in range(0, len(target), 400_000):
        stop = min(start + 400_000, len(target))
        out[start:stop] = clf.predict_proba(np.asarray(X[target[start:stop]], np.float32))[:, 1]
    target_rc = rc[target]
    scores[target_rc[:, 0], target_rc[:, 1]] = out
    ridge = oof_detector.ridge_nms(scores, fold["valid"], sigma=1.0)
    base = oof_detector.build_oof_dotted_base(scores, ridge, fold["valid"], fold["visible"],
                                              budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=3.0)
    active = fold["valid"] & ~fold["visible"]
    base &= active & (distance_transform_edt(~fold["visible"]) > 1)
    added = heatflow_euler.select_corroborated_ridge_dots(
        scores, ridge, active, base, fold["visible"], fields["joint_mask"],
        score_mult=fields["score_mult"], k_cap=heatflow_euler.K_CAP_PER_CELL,
        min_dist_base=heatflow_euler.MIN_DIST_BASE_PX,
        min_dist_known=heatflow_euler.MIN_DIST_KNOWN_PX,
        thin_d=heatflow_euler.THIN_D_PX, rng_seed=seed + 50_000,
    )["added"]
    return base | added


def main() -> int:
    if STARTED.exists() or STAGE.exists() or HOLDOUT.exists() or CARD.exists():
        raise SystemExit("S19-ASCP already started; do not rerun or retune spent evidence")
    start = time.monotonic()
    shared_audit = verify_assets()
    if not shared_audit["passed"]:
        raise ValueError(shared_audit)
    shared = load_shared()
    prereg_hash = sha256_file(PREREG)
    STARTED.write_text(json.dumps({"session": SESSION, "started_utc": "2026-10-26",
        "preregistration_sha256": prereg_hash, "experiments": 3,
        "shared_manifest_sha256": shared_audit["manifest_sha256"]}, indent=2) + "\n")

    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS) & foot
    surface, legs = load_surface()
    valid = surface > 0
    holdout = shared.holdout.SegmentHoldout(foot, labels, buffer_px=15)

    # Experiment 1: canaries and continuous-surface registry comparison.
    canary = holdout.canary({**legs, "combined_surface": surface}, seed=20261026)
    registry = registry_paths()
    novelty_pre = compare_registry(surface, valid, None, foot, registry)
    stage = {"session": SESSION, "preregistration_sha256": prereg_hash,
             "shared_assets": shared_audit, "experiment_1": {"canary": canary,
             "registry": novelty_pre}, "experiments_used": 1}
    STAGE.write_text(json.dumps(stage, indent=2, allow_nan=False) + "\n")
    if not canary["passed"] or not novelty_pre["passed"]:
        raise SystemExit("Experiment 1 stop: leakage or duplicate threshold exceeded")

    # Experiment 2: fixed placement, final novelty and exact shared-writer output.
    full_dots = emit_candidate(surface, valid, labels, foot, TARGET_N)
    novelty_final = compare_registry(surface, valid, full_dots, foot, registry)
    stage["experiment_2"] = {"n_dots": int(full_dots.sum()), "registry": novelty_final}
    stage["experiments_used"] = 2
    STAGE.write_text(json.dumps(stage, indent=2, allow_nan=False) + "\n")
    if not novelty_final["passed"]:
        raise SystemExit("Experiment 2 stop: final duplicate threshold exceeded")
    pred = full_dots.astype(np.float32)
    cid = shared.submission.scored_content_id(pred, foot, labels)
    filename = shared.submission.make_filename("gems28", "s19-ascp", DATE, cid, "allfinite")
    output = ROOT / "docs/downloads" / filename
    shared.submission.write_submission(pred, paths.TEMPLATE, output, outside="zero")
    validator = shared.submission.check_variants(output, paths.TEMPLATE)
    if not validator["format_valid"] or not validator["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"]:
        raise ValueError("Exact output failed validation")
    stage["experiment_2"].update({"file": str(output.relative_to(ROOT)), "sha256": sha256_file(output),
                                  "content_id": cid, "validator": validator})
    STAGE.write_text(json.dumps(stage, indent=2, allow_nan=False) + "\n")

    # Experiment 3: one shared whole-component holdout, no tuning.
    fields = heatflow_euler.build_corroboration_fields(
        foot, hf_json_path=paths.SB_HEAT_FLOW_JSON, euler_csv_path=paths.EULER_CLUSTERS_CSV,
        lidar_path=paths.LIDAR)
    cand_preds, base_preds = [], []
    for i, fold in enumerate(holdout.folds):
        cap = int(round(TARGET_N * fold["valid"].sum() / foot.sum()))
        cand_preds.append(emit_candidate(surface, valid & fold["valid"], fold["visible"], foot, cap))
        base_preds.append(baseline_prediction(fold, foot, labels, fields, 20261026 + i))
        print(f"fold {i + 1}/4 complete in {time.monotonic()-start:.1f}s", flush=True)
    candidate = holdout.summarize(cand_preds, ci_draws=1999)
    baseline = holdout.summarize(base_preds, ci_draws=1999)
    cand_blocks, base_blocks, fold_gain = [], [], []
    for cp, bp, fold in zip(cand_preds, base_preds, holdout.folds):
        cscore, cb = holdout.score_fold(cp, fold)
        bscore, bb = holdout.score_fold(bp, fold)
        cand_blocks.append(cb)
        base_blocks.append(bb)
        fold_gain.append(cscore["dti"] - bscore["dti"])
    cb, bb = np.sum(cand_blocks, axis=0), np.sum(base_blocks, axis=0)
    yy, xx = np.nonzero(foot)
    nx = (foot.shape[1] + 99) // 100
    active_blocks = np.unique((yy // 100) * nx + xx // 100)
    gain_ci = shared.holdout.pooled_bootstrap(cb[active_blocks], paired=bb[active_blocks],
                                              resamples=1999, seed=20261026)
    gain = candidate["dti"] - baseline["dti"]
    gates = {"candidate_beats_baseline": gain > 0,
             "paired_gain_ci_lower_gt_zero": gain_ci[0] > 0,
             "positive_3_of_4_folds": sum(x > 0 for x in fold_gain) >= 3,
             "canary_passed": canary["passed"], "registry_passed": novelty_final["passed"],
             "validator_passed": validator["format_valid"]}
    gate_passed = all(gates.values())
    result = {"label": "HOLDOUT-DTI", "evaluator_version": shared.holdout.MTR_EVALUATOR_VERSION,
              "candidate": candidate, "baseline": baseline, "baseline_name": "visible-only 32-band H38-style detector",
              "paired_gain": gain, "paired_gain_ci95": gain_ci, "per_fold_gain": fold_gain,
              "withheld_positives": candidate["n_withheld_positive_pixels"], "gates": gates,
              "gate_passed": gate_passed, "seconds": round(time.monotonic()-start, 1)}
    HOLDOUT.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    note = f"S19 ASCP paired antislope LiDAR scarps; {int(full_dots.sum())} dots; " + ("holdout passed." if gate_passed else "holdout rejected; DO NOT SUBMIT.")
    card = {"session": SESSION,
            "hypothesis": "Paired crest/toe curvature plus antislope selectivity and coherence recovers subtle unmapped fault scarps.",
            "mechanism": "Fixed geometric mean of decoded LiDAR step, curvature-pair, uphill-facing and coherence legs; 2.8 px packing.",
            "non_fault_mimic": "Road cut, terrace or paleo-shoreline riser, channel bank, landslide, or mine bench.",
            "holdout": {"label": "HOLDOUT-DTI", "evaluator_version": shared.holdout.MTR_EVALUATOR_VERSION,
                        "withheld_positives": candidate["n_withheld_positive_pixels"],
                        "dti": candidate["dti"], "ci95": candidate["ci95"]["interval"],
                        "baseline_dti": baseline["dti"], "paired_gain": gain,
                        "paired_gain_ci95": gain_ci},
            "registry": {"members": novelty_final["members"],
                         "max_abs_surface_spearman": novelty_final["max_abs_surface_spearman"]["value"],
                         "max_surface_support_overlap_3px": novelty_final["max_support_within_3px"]["support_within_3px_fraction"],
                         "max_abs_final_spearman": novelty_final["max_abs_final_spearman"]["value"],
                         "max_final_overlap_3px": novelty_final["max_final_dots_within_3px"]["final_dots_within_3px_fraction"]},
            "raster_sha256": sha256_file(output),
            "validator": {"no_nan_inside": validator["checks"]["footprint_all_finite"]["pass"],
                          "no_nan_whole_array": validator["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"],
                          "range_0_1": validator["checks"]["footprint_range_0_1"]["pass"],
                          "crs_match": validator["checks"]["crs_epsg_32611"]["pass"],
                          "shape_match": validator["checks"]["shape_matches_template"]["pass"],
                          "transform_match": validator["checks"]["geotransform_matches_template"]["pass"]},
            "submission_name": f"GEMSDOE28-S19-ASCP-{cid}", "submission_file": str(output.relative_to(ROOT)),
            "note": note, "experiments_run": 3, "verdict": "promote" if gate_passed else "negative",
            "submission_ready": bool(gate_passed), "slot_selected": False,
            "limitations": ["Owner-mirrored LiDAR descriptors are hash-pinned but not organizer-authenticated.",
                            "Eight-connected raster components proxy expert fault segments.",
                            "Registry covers fresh priority rasters and local archive, not unknowable concurrent private outputs.",
                            "Local holdout performance is not an organizer score or guarantee."]}
    if len(note) > 140:
        raise AssertionError(f"note too long: {len(note)}")
    CARD.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    stage["experiments_used"] = 3
    stage["verdict"] = card["verdict"]
    STAGE.write_text(json.dumps(stage, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"file": filename, "holdout_dti": candidate["dti"],
                      "baseline_dti": baseline["dti"], "gain_ci95": gain_ci,
                      "verdict": card["verdict"], "seconds": result["seconds"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
