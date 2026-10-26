#!/usr/bin/env python3
"""Run the three frozen S22-MOFR (H44-1 marker-offset) experiments and write one final JSON card.

Single-use: a started marker prevents same-seed retuning. Loads hash-verified shared
holdout/metric/novelty/submission code through gems27.shared_template; never forks it privately.
See knowledge/62_s22_mofr_preregistration.md for the frozen specification.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import rasterio
from sklearn.ensemble import HistGradientBoostingClassifier

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, marker_offset, oof_detector, paths  # noqa: E402
from gems27.shared_template import load_shared, verify_assets  # noqa: E402

SESSION = "S22-MOFR"
DATE = "20261026"
STARTED = ROOT / "evidence/s22_mofr.started.json"
STAGE = ROOT / "evidence/s22_mofr_stage.json"
CARD = ROOT / "evidence/s22_mofr_run_card.json"
PREREG = ROOT / "knowledge/62_s22_mofr_preregistration.md"


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


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


def build_registry_entries(registry: list[Path], foot: np.ndarray) -> list[dict]:
    entries = []
    for i, path in enumerate(registry):
        with rasterio.open(path) as src:
            arr = src.read(1)
        values = arr[foot].astype("<f4")
        entries.append({
            "id": f"reg-{i:03d}",
            "file": str(path.relative_to(ROOT)),
            "cache_path": str(path.relative_to(ROOT)),
            "footprint_sha256": hashlib.sha256(values.tobytes()).hexdigest(),
        })
    return entries


def baseline_prediction(fold: dict, foot: np.ndarray, seed: int) -> np.ndarray:
    """Fresh retrained visible-only HGB baseline (same family used by prior sessions)."""
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
                                              budget_frac=oof_detector.PRE_THIN_FRAC, thin_d=2.8)
    return base


def main() -> int:
    if STARTED.exists() or STAGE.exists() or CARD.exists():
        raise SystemExit("S22-MOFR already started; do not rerun or retune spent evidence")
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
    with rasterio.open(paths.TRAINING) as src:
        tmi_hg = src.read(marker_offset.TMI_BAND)
        grav_hg = src.read(marker_offset.GRAV_BAND)
    holdout = shared.holdout.SegmentHoldout(foot, labels, buffer_px=15)

    # ---------------- Experiment 1: canaries + pre-placement registry novelty ----------------
    print(f"[{time.monotonic()-start:.1f}s] experiment 1: canary + pre-placement registry", flush=True)
    mag_clean, mag_valid = marker_offset.clean_field(tmi_hg, foot)
    grav_clean, grav_valid = marker_offset.clean_field(grav_hg, foot)
    full_det_union = marker_offset.marker_offset_detector(tmi_hg, grav_hg, foot, np.zeros_like(foot),
                                                           require_both_fields=False)
    full_det_corr = marker_offset.marker_offset_detector(tmi_hg, grav_hg, foot, np.zeros_like(foot),
                                                          require_both_fields=True)
    canary_features = {
        "tmi_hg_abs_raw": np.abs(mag_clean),
        "iso_grav_anom_hg_abs_raw": np.abs(grav_clean),
        "marker_offset_support_union": full_det_union["support"],
        "marker_offset_support_corroborated": full_det_corr["support"],
    }
    canary = holdout.canary(canary_features, seed=20261026)
    registry = registry_paths()
    entries = build_registry_entries(registry, foot)
    novelty_pre = shared.novelty.compare_prospective_registry(
        full_det_union["support"], foot, entries, ROOT)
    stage = {"session": SESSION, "preregistration_sha256": prereg_hash,
             "shared_assets": shared_audit,
             "experiment_1": {
                 "canary": canary,
                 "full_map_diagnostics": {
                     "union_variant": {"mag_endpoints": full_det_union["mag_n_endpoints"],
                                        "mag_pairs": full_det_union["mag_n_pairs"],
                                        "grav_endpoints": full_det_union["grav_n_endpoints"],
                                        "grav_pairs": full_det_union["grav_n_pairs"],
                                        "bridge_px": full_det_union["n_bridge_px"]},
                     "corroborated_variant": {"bridge_px": full_det_corr["n_bridge_px"]},
                 },
                 "registry_novelty_pre_placement": {k: v for k, v in novelty_pre.items() if k != "rows"},
             },
             "experiments_used": 1}
    STAGE.write_text(json.dumps(stage, indent=2, allow_nan=False) + "\n")
    if not canary["passed"]:
        raise SystemExit("Experiment 1 stop: leakage canary failed (AUC > 0.90)")
    if not novelty_pre["method_lane_passed"]:
        raise SystemExit("Experiment 1 stop: pre-placement registry duplicate threshold exceeded")

    # ---------------- Experiment 2: final dot placement + exact-format validation ----------------
    print(f"[{time.monotonic()-start:.1f}s] experiment 2: final placement + validation", flush=True)
    variant_results = {}
    for name, det in (("union", full_det_union), ("corroborated", full_det_corr)):
        dots = det["bridge_mask"] & foot & ~labels
        if not dots.any():
            variant_results[name] = {"n_dots": 0, "skipped": "empty candidate set"}
            continue
        novelty_final = shared.novelty.compare_prospective_registry(
            det["support"], foot, entries, ROOT, dots=dots)
        variant_results[name] = {
            "n_dots": int(dots.sum()),
            "registry": {k: v for k, v in novelty_final.items() if k != "rows"},
            "passed": bool(novelty_final["method_lane_passed"]),
        }
    stage["experiment_2"] = {"variants": variant_results}
    stage["experiments_used"] = 2
    STAGE.write_text(json.dumps(stage, indent=2, allow_nan=False) + "\n")

    chosen = None
    for name in ("union", "corroborated"):
        v = variant_results.get(name, {})
        if v.get("passed") and v.get("n_dots", 0) > 0:
            chosen = name
            break
    if chosen is None:
        raise SystemExit("Experiment 2 stop: no variant both nonempty and registry-novel")

    chosen_det = full_det_union if chosen == "union" else full_det_corr
    pred = (chosen_det["bridge_mask"] & foot & ~labels).astype(np.float32)
    cid = shared.submission.scored_content_id(pred, foot, labels)
    filename = shared.submission.make_filename("gems28", f"s22-mofr-{chosen}", DATE, cid, "allfinite")
    output = ROOT / "docs/downloads" / filename
    shared.submission.write_submission(pred, paths.TEMPLATE, output, outside="zero")
    validator = shared.submission.check_variants(output, paths.TEMPLATE)
    if not validator["format_valid"] or not validator["checks"]["variant_strict_whole_array_no_nan_allowed"]["pass"]:
        raise ValueError("Exact output failed validation")
    stage["experiment_2"]["chosen_variant"] = chosen
    stage["experiment_2"]["file"] = str(output.relative_to(ROOT))
    stage["experiment_2"]["sha256"] = sha256_file(output)
    stage["experiment_2"]["content_id"] = cid
    stage["experiment_2"]["validator"] = validator
    STAGE.write_text(json.dumps(stage, indent=2, allow_nan=False) + "\n")

    # ---------------- Experiment 3: SegmentHoldout vs fresh retrained baseline ----------------
    # The marker-offset geometry reads no catalogue label anywhere (clean_field/skeleton_and_strike
    # only ever see the two raw potential-field rasters and the static footprint), so the SAME
    # full-map bridge_mask computed once in Experiment 1 is reused for every fold -- only the
    # eligible-placement window (fold["valid"] & ~fold["visible"]) changes per fold. This is both
    # more correct (one frozen geometry, not four independently re-derived ones) and avoids
    # recomputing the expensive skeleton/endpoint match four times.
    print(f"[{time.monotonic()-start:.1f}s] experiment 3: SegmentHoldout vs baseline", flush=True)
    cand_preds, base_preds = [], []
    for i, fold in enumerate(holdout.folds):
        cand = chosen_det["bridge_mask"] & fold["valid"] & ~fold["visible"]
        cand_preds.append(cand.astype(np.float32))
        base_preds.append(baseline_prediction(fold, foot, 20261026 + i).astype(np.float32))
        print(f"  fold {i + 1}/4 ({fold['name']}) complete in {time.monotonic()-start:.1f}s "
              f"(candidate={int(cand.sum())} px, baseline={int(base_preds[-1].sum())} px)", flush=True)

    candidate_summary = holdout.summarize(cand_preds, ci_draws=1999)
    baseline_summary = holdout.summarize(base_preds, ci_draws=1999)

    cand_blocks, base_blocks, fold_gain = [], [], []
    for cp, bp, fold in zip(cand_preds, base_preds, holdout.folds):
        cscore, cb = holdout.score_fold(cp.astype(np.float32), fold)
        bscore, bb = holdout.score_fold(bp.astype(np.float32), fold)
        cand_blocks.append(cb)
        base_blocks.append(bb)
        fold_gain.append(cscore["dti"] - bscore["dti"])
    cb_sum, bb_sum = np.sum(cand_blocks, axis=0), np.sum(base_blocks, axis=0)
    yy, xx = np.nonzero(foot)
    nx = (foot.shape[1] + 99) // 100
    active_blocks = np.unique((yy // 100) * nx + xx // 100)
    gain_ci = shared.holdout.pooled_bootstrap(cb_sum[active_blocks], paired=bb_sum[active_blocks],
                                              resamples=1999, seed=20261026)
    gain = candidate_summary["dti"] - baseline_summary["dti"]
    gates = {
        "candidate_beats_baseline": bool(gain > 0),
        "paired_gain_ci_lower_gt_zero": bool(gain_ci[0] > 0),
        "positive_3_of_4_folds": bool(sum(x > 0 for x in fold_gain) >= 3),
    }
    verdict = "promote" if all(gates.values()) else "negative"
    experiment_3 = {
        "candidate": candidate_summary,
        "baseline": baseline_summary,
        "paired_gain": gain,
        "paired_gain_ci95": gain_ci,
        "fold_gain": fold_gain,
        "gates": gates,
        "verdict": verdict,
    }
    stage["experiment_3"] = experiment_3
    stage["experiments_used"] = 3
    STAGE.write_text(json.dumps(stage, indent=2, allow_nan=False) + "\n")

    duration = time.monotonic() - start
    note = (
        f"S22-MOFR {chosen} marker-offset {int(pred.sum())}d | HOLDOUT-DTI "
        f"{candidate_summary['dti']:.4f} vs baseline {baseline_summary['dti']:.4f} | "
        f"verdict {verdict} | DO NOT SUBMIT"
    )[:140]

    card = {
        "session": SESSION,
        "hypothesis": "H44-1: potential-field (TMI/gravity horizontal-gradient) marker-offset "
                      "piercing-point realignment -- ridge-skeleton endpoint pairing across a "
                      "strike-compatible, bounded gap/offset gap, independent of the fault catalogue",
        "mechanism": "A concealed fault laterally displaces a basement-contact ridge in the "
                     "horizontal-gradient-magnitude field; matched endpoint pairs mark the inferred "
                     "trace exactly where the marker was offset.",
        "non_fault_mimic": "Intrusive-contact strike corners, crossing unrelated contacts, survey "
                           "flight-line/levelling seams, coincidental nearby contacts, and genuinely "
                           "inactive (pre-Quaternary) basement offsets.",
        "preregistration": str(PREREG.relative_to(ROOT)),
        "preregistration_sha256": prereg_hash,
        "shared_assets": shared_audit,
        "chosen_variant": chosen,
        "experiment_1": stage["experiment_1"],
        "experiment_2": {k: v for k, v in stage["experiment_2"].items()},
        "experiment_3": experiment_3,
        "holdout_dti": candidate_summary["dti"],
        "holdout_dti_ci95": candidate_summary["ci95"]["interval"],
        "baseline_dti": baseline_summary["dti"],
        "correlation_overlap_vs_registry": variant_results[chosen]["registry"],
        "raster_sha256": stage["experiment_2"]["sha256"],
        "validator": validator,
        "submission_name": f"GEMSDOE28-S22-MOFR-{chosen.upper()}-{cid}",
        "note": note[:140],
        "verdict": verdict,
        "submission_ready": False,
        "duration_seconds": duration,
        "label_discipline": "HOLDOUT-DTI values here are evaluator gems-segment-pooled-v1 on "
                             "SegmentHoldout seeds fixed by buffer_px=15/quadrant medians (no extra "
                             "seed sweep this session); never compared to another session's numbers.",
    }
    CARD.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"verdict": verdict, "holdout_dti": candidate_summary["dti"],
                      "baseline_dti": baseline_summary["dti"], "gain": gain, "gain_ci95": gain_ci,
                      "duration_s": duration}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
