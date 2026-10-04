#!/usr/bin/env python3
"""Apply the frozen H38-1 decision gates to a LOSFO run; do not retune from its cells."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

import numpy as np
from scipy.stats import t as student_t

ROOT = Path(__file__).resolve().parents[1]
SEEDS = list(range(265, 270))
FOLDS = ["NW", "NE_LidarGapHeavy", "SW", "SE"]
ARM_NAME = "H38-1 shallow Euler × gravity × low-relief licence"
PREREG = "knowledge/38_preregistration_H38-1.md"
LIVE_BAR = 0.0548
BEST_FARFIELD_ADD_ARM = 0.0005763894914862378
MIN_CANDIDATES = 100
MIN_ADDITIONS = 200
THIN_D_PX = 2.8
DILATE_PX = 3
BUFFER_PX = 6
METRIC_ALPHA = 0.2
METRIC_BETA = 0.8
METRIC_EPS = 1e-7
BASE_EULER_RULE = "depth_mad_m <= 60 and median_depth_m <= 400 and n_solutions >= 8"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def runtime_versions() -> dict[str, str]:
    packages = {"numpy": "numpy", "scipy": "scipy", "scikit_learn": "scikit-learn", "rasterio": "rasterio"}
    return {"python": sys.version.split()[0], **{key: metadata.version(name) for key, name in packages.items()}}


def claim_fingerprint(claim: dict) -> str:
    immutable_keys = (
        "schema", "arm_name", "seeds", "reserved_utc", "protocol_commit", "protocol_branch",
        "preregistration", "preregistration_sha256", "candidate_csv", "candidate_csv_sha256",
        "candidate_count", "sufficiency_audit", "sufficiency_audit_sha256", "pre_run_seed_audit",
        "input_sha256", "code_sha256", "runtime_versions", "baseline", "result_paths",
    )
    stable = {key: claim.get(key) for key in immutable_keys}
    return hashlib.sha256(json.dumps(stable, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def _finite(value) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError):
        return False


def _json_default(value):
    """Serialize NumPy scalar/array values without silently stringifying evidence."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _dti_matches_arm_metrics(metrics: dict, truth_count: int) -> bool:
    try:
        tp = float(metrics["tp"])
        fp = float(metrics["fp"])
        reported = float(metrics["dti"])
    except (KeyError, TypeError, ValueError):
        return False
    if truth_count <= 0 or tp < 0 or tp > truth_count + 1e-9 or fp < 0:
        return False
    denominator = tp + METRIC_ALPHA * fp + METRIC_BETA * (truth_count - tp) + METRIC_EPS
    return denominator > 0 and math.isclose(reported, tp / denominator, abs_tol=1e-12)


def evaluate(raw: dict, claim: dict, sufficiency_audit: dict, benchmark: dict) -> dict:
    """Pure gate calculation used by the CLI and synthetic regression tests."""
    if claim.get("status") not in {"RUNNING", "CONSUMED", "FAILED"}:
        raise ValueError("claim must represent a started single-use holdout")
    if raw.get("seeds") != SEEDS:
        raise ValueError(f"raw run seeds differ from the preregistered range: {raw.get('seeds')}")
    if claim.get("seeds") != SEEDS or claim.get("arm_name") != ARM_NAME:
        raise ValueError("claim seeds or arm differ from the frozen preregistration")
    if raw.get("euler_licence") is None:
        raise ValueError("raw holdout has no H38-1 candidate arm")
    licence = raw["euler_licence"]
    inp = licence.get("input", {})
    if licence.get("arm_name") != ARM_NAME or inp.get("name") != ARM_NAME:
        raise ValueError("raw holdout arm name differs from the preregistration")
    if licence.get("preregistration") != PREREG or inp.get("preregistration") != PREREG:
        raise ValueError("raw holdout references the wrong preregistration")
    if inp.get("csv") != claim.get("candidate_csv"):
        raise ValueError("raw holdout candidate path differs from the single-use claim")
    if inp.get("csv_sha256") != claim.get("candidate_csv_sha256"):
        raise ValueError("candidate CSV hash differs from the single-use claim")
    if inp.get("base_euler_rule") != BASE_EULER_RULE:
        raise ValueError("raw holdout Euler eligibility rule differs from the preregistration")
    if not (_finite(inp.get("thin_d_px")) and math.isclose(float(inp["thin_d_px"]), THIN_D_PX)
            and _finite(raw.get("thin_d_px")) and math.isclose(float(raw["thin_d_px"]), THIN_D_PX)):
        raise ValueError("raw holdout spacing differs from the frozen 2.8-pixel protocol")
    candidate_count = int(sufficiency_audit.get("clusters", {}).get("selected_clusters", -1))
    if candidate_count != claim.get("candidate_count") or candidate_count != inp.get("n_candidate_clusters"):
        raise ValueError("candidate count differs across builder, claim, and holdout")
    if candidate_count < MIN_CANDIDATES or sufficiency_audit.get("status") != "READY":
        raise ValueError("candidate support did not clear the frozen pre-run sufficiency floor")

    cells = raw.get("cells")
    if not isinstance(cells, list) or len(cells) != 20 or licence.get("n_cells") != 20:
        raise ValueError("expected exactly 20 paired LOSFO cells")
    pairs = {(row.get("seed"), row.get("fold")) for row in cells}
    expected_pairs = {(seed, fold) for seed in SEEDS for fold in FOLDS}
    if pairs != expected_pairs:
        raise ValueError("holdout cell set is not the frozen 5-seed × 4-fold panel")

    deltas = []
    random_deltas = []
    delta_tp = 0.0
    added = 0
    controls = 0
    per_seed = {str(seed): [] for seed in SEEDS}
    per_fold = {fold: [] for fold in FOLDS}
    cell_integrity = []
    cell_metric_integrity = []
    cell_farfield_distances = []
    for cell in cells:
        if not isinstance(cell, dict):
            raise ValueError("malformed holdout cell record")
        euler = cell.get("euler") or {}
        base = cell.get("losfo") or {}
        candidate_metrics = euler.get("licence") or {}
        random_metrics = euler.get("random_control") or {}
        delta = euler.get("delta_dti_licence")
        random_delta = euler.get("delta_dti_random")
        delta_credit = euler.get("delta_tp_licence")
        random_credit = euler.get("delta_tp_random")
        n_added = euler.get("added_dots")
        n_control = euler.get("control_dots")
        base_dti = base.get("dti")
        truth = cell.get("n_truth")
        min_dist = cell.get("min_dist_truth_to_known_px")
        scored_values = (
            delta, random_delta, delta_credit, random_credit, base_dti, truth, min_dist,
            candidate_metrics.get("dti"), candidate_metrics.get("tp"), candidate_metrics.get("fp"),
            candidate_metrics.get("dots"), candidate_metrics.get("n_truth"),
            random_metrics.get("dti"), random_metrics.get("tp"), random_metrics.get("fp"),
            random_metrics.get("dots"), random_metrics.get("n_truth"),
            base.get("tp"), base.get("fp"), base.get("dots"), base.get("n_truth"),
        )
        if not all(_finite(value) for value in scored_values):
            raise ValueError("non-finite or missing score value in a holdout cell")
        if type(n_added) is not int or type(n_control) is not int or n_added != n_control:
            raise ValueError("candidate and matched-random addition counts are not exactly matched")
        if (type(candidate_metrics.get("dots")) is not int or type(random_metrics.get("dots")) is not int
                or type(base.get("dots")) is not int or type(truth) is not int):
            raise ValueError("dot counts and held-out truth count must be integers")
        if n_added < 0 or truth <= 0 or min_dist < 8.0:
            raise ValueError("negative additions, empty held-out truth, or insufficient far-field separation")
        metric_match = (
            _dti_matches_arm_metrics(base, truth)
            and _dti_matches_arm_metrics(candidate_metrics, truth)
            and _dti_matches_arm_metrics(random_metrics, truth)
            and math.isclose(float(delta), float(candidate_metrics["dti"]) - float(base_dti), abs_tol=1e-12)
            and math.isclose(float(random_delta), float(random_metrics["dti"]) - float(base_dti), abs_tol=1e-12)
            and math.isclose(float(delta_credit), float(candidate_metrics["tp"]) - float(base["tp"]), abs_tol=1e-9)
            and math.isclose(float(random_credit), float(random_metrics["tp"]) - float(base["tp"]), abs_tol=1e-9)
            and candidate_metrics.get("n_truth") == random_metrics.get("n_truth") == base.get("n_truth") == truth
            and candidate_metrics["dots"] - base["dots"] == n_added
            and random_metrics["dots"] - base["dots"] == n_control
        )
        cell_metric_integrity.append(bool(metric_match))
        flags = euler.get("integrity") or {}
        cell_integrity.append(bool(flags) and all(flags.get(key) == 0 for key in (
            "licence_base_overlap_px", "licence_visible_catalogue_overlap_px",
            "random_base_overlap_px", "random_visible_catalogue_overlap_px",
        )))
        deltas.append(float(delta))
        random_deltas.append(float(random_delta))
        cell_farfield_distances.append(float(min_dist))
        delta_tp += float(delta_credit)
        added += n_added
        controls += n_control
        per_seed[str(cell["seed"])].append(float(delta))
        per_fold[str(cell["fold"])].append(float(delta))

    candidate_vs_random = np.asarray(deltas) - np.asarray(random_deltas)
    mean_delta = float(np.mean(deltas))
    std_delta = float(np.std(deltas, ddof=1))
    ci_half = float(student_t.ppf(0.975, df=19) * std_delta / math.sqrt(20))
    mean_vs_random = float(np.mean(candidate_vs_random))
    credit_per_dot = float(delta_tp / added) if added else None
    seed_means = {key: float(np.mean(values)) for key, values in per_seed.items()}
    fold_means = {key: float(np.mean(values)) for key, values in per_fold.items()}
    positive_cells = sum(value > 0 for value in deltas)
    positive_vs_random_cells = sum(value > 0 for value in candidate_vs_random)
    positive_seed_means = sum(value > 0 for value in seed_means.values())
    positive_fold_means = sum(value > 0 for value in fold_means.values())
    benchmark_delta = float(benchmark["mean_delta_dti_licence_vs_base"])
    claimed_benchmark = float(claim.get("baseline", {}).get("mean_delta_dti_licence_vs_base", float("nan")))
    if (not math.isclose(benchmark_delta, BEST_FARFIELD_ADD_ARM, abs_tol=1e-15)
            or not math.isclose(claimed_benchmark, BEST_FARFIELD_ADD_ARM, abs_tol=1e-15)):
        raise ValueError("H37-3 comparison value differs from the frozen far-field benchmark")
    far_field_check = raw.get("far_field_check", {})
    min_farfield_value = far_field_check.get("min_dist_truth_to_known_px_over_cells")
    min_farfield_match = (
        _finite(min_farfield_value)
        and math.isclose(float(min_farfield_value), min(cell_farfield_distances), abs_tol=1e-12)
        and all(distance >= 8.0 for distance in cell_farfield_distances)
    )
    code = raw.get("code_sha256", {})
    expected_code = claim.get("code_sha256", {})
    code_match = all(code.get(raw_key) == expected_code.get(claim_key) for raw_key, claim_key in (
        ("runner", "scripts/run_losfo_harness.py"),
        ("losfo", "src/gems27/losfo.py"),
        ("oof_detector", "src/gems27/oof_detector.py"),
        ("metric", "src/gems27/metric.py"),
        ("thinning", "src/gems27/thinning.py"),
        ("holdout", "src/gems27/holdout.py"),
        ("grid", "src/gems27/grid.py"),
        ("paths", "src/gems27/paths.py"),
        ("packing", "src/gems27/packing.py"),
    ))
    runtime_match = raw.get("runtime_versions") == claim.get("runtime_versions")
    run_meta = raw.get("meta", {})
    runner_settings_match = (
        raw.get("thin_d_px") == THIN_D_PX
        and run_meta.get("dilate_px") == DILATE_PX
        and run_meta.get("buffer_px") == BUFFER_PX
        and inp.get("thin_d_px") == THIN_D_PX
        and inp.get("base_euler_rule") == BASE_EULER_RULE
        and licence.get("tau_live_bar") == LIVE_BAR
        and len(cells) == licence.get("n_cells") == 20
    )
    licence_summary = licence
    aggregate_match = (
        licence_summary.get("added_dots_total") == added
        and licence_summary.get("control_dots_total") == controls
        and licence_summary.get("n_cells") == len(cells)
        and _finite(licence_summary.get("mean_delta_dti_licence_vs_base"))
        and math.isclose(float(licence_summary["mean_delta_dti_licence_vs_base"]), mean_delta, abs_tol=1e-12)
        and _finite(licence_summary.get("mean_delta_dti_random_vs_base"))
        and math.isclose(float(licence_summary["mean_delta_dti_random_vs_base"]), float(np.mean(random_deltas)), abs_tol=1e-12)
        and _finite(licence_summary.get("mean_delta_dti_licence_vs_random"))
        and math.isclose(float(licence_summary["mean_delta_dti_licence_vs_random"]), mean_vs_random, abs_tol=1e-12)
        and _finite(licence_summary.get("credit_per_added_dot"))
        and math.isclose(float(licence_summary["credit_per_added_dot"]), credit_per_dot, abs_tol=1e-12)
    )
    integrity = {
        "exact_seeds_and_cells": raw.get("seeds") == SEEDS and pairs == expected_pairs,
        "frozen_run_settings": runner_settings_match,
        "runner_aggregate_matches_cell_metrics": aggregate_match,
        "runtime_versions_match_claim": runtime_match,
        "per_cell_no_candidate_or_control_overlap": all(cell_integrity),
        "exact_arm_and_preregistration": licence.get("arm_name") == ARM_NAME and licence.get("preregistration") == PREREG,
        "candidate_hash_matches_claim": inp.get("csv_sha256") == claim.get("candidate_csv_sha256"),
        "candidate_count_matches_all_records": candidate_count == claim.get("candidate_count") == inp.get("n_candidate_clusters"),
        "candidate_sufficiency_ready": sufficiency_audit.get("status") == "READY" and candidate_count >= MIN_CANDIDATES,
        "matched_random_counts": all(
            (cell.get("euler") or {}).get("added_dots") == (cell.get("euler") or {}).get("control_dots")
            for cell in cells
        ),
        "per_cell_derived_metrics_match_reported_arms": all(cell_metric_integrity),
        "far_field_truth_at_least_800m_from_visible_labels": min_farfield_match,
        "runner_and_protocol_code_match_claim": code_match,
        "every_cell_has_truth_and_finite_metrics": all(
            int(cell.get("n_truth", 0)) > 0
            and _finite((cell.get("losfo") or {}).get("dti"))
            and _finite((cell.get("euler") or {}).get("delta_dti_licence"))
            for cell in cells
        ),
    }
    support_ok = candidate_count >= MIN_CANDIDATES and added >= MIN_ADDITIONS
    c1 = (mean_delta > 0 and positive_cells >= 15 and positive_seed_means >= 4 and positive_fold_means >= 3)
    c2 = _finite(credit_per_dot) and credit_per_dot >= LIVE_BAR
    c3 = mean_vs_random > 0 and positive_vs_random_cells >= 15
    c4 = support_ok and all(integrity.values())
    c5 = mean_delta > benchmark_delta
    gates = {
        "C1_positive_and_spatially_repeatable": {
            "passed": bool(c1), "threshold": "mean > 0; >=15/20 positive cells; >=4/5 positive seed means; >=3/4 positive fold means",
            "mean_delta_dti": mean_delta, "positive_cells": positive_cells,
            "positive_seed_means": positive_seed_means, "per_seed_means": seed_means,
            "positive_fold_means": positive_fold_means, "per_fold_means": fold_means,
            "descriptive_95pct_t_interval": [mean_delta - ci_half, mean_delta + ci_half],
        },
        "C2_live_economic_bar": {
            "passed": bool(c2), "threshold_credit_per_dot": LIVE_BAR,
            "observed_credit_per_dot": credit_per_dot, "delta_credit_total": delta_tp,
            "added_dots_total": added, "farfield_break_even_bar_reported_by_runner": licence.get("tau_farfield_bar"),
        },
        "C3_candidate_beats_matched_random": {
            "passed": bool(c3), "threshold": "mean > 0 and >=15/20 positive paired cells",
            "mean_delta_dti_candidate_minus_random": mean_vs_random,
            "positive_cells": positive_vs_random_cells,
        },
        "C4_support_and_integrity": {
            "passed": bool(c4), "candidate_count": candidate_count,
            "minimum_candidate_count": MIN_CANDIDATES, "added_dots_total": added,
            "minimum_added_dots": MIN_ADDITIONS, "integrity_checks": integrity,
        },
        "C5_beats_previous_farfield_add_arm_best": {
            "passed": bool(c5), "previous_best_mean_delta_dti": benchmark_delta,
            "observed_mean_delta_dti": mean_delta,
            "margin": mean_delta - benchmark_delta,
            "comparison_limit": "different seed decades; point-estimate filter, not a paired superiority test",
        },
    }
    promotable = all(item["passed"] for item in gates.values())
    decision = (
        "ALL FROZEN GATES PASS. Eligible only for a separate fresh-seed confirmation and exact-file review; this holdout does not itself authorize a weekly slot."
        if promotable else
        "NOT PROMOTABLE under the frozen rule. No candidate TIFF, upload, or weekly slot; do not retune or rerun seeds 265–269."
    )
    return {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hypothesis": "H38-1 cross-field Euler/gravity/low-relief candidate addition",
        "status": "PASS" if promotable else "FAIL",
        "decision": decision,
        "scope": "internal LOSFO holdout on held-out mapped fault systems; neither organizer-authenticated labels nor a DrivenData score",
        "network_access": "none; no DrivenData access, leaderboard query, upload, or score was performed",
        "seeds": SEEDS,
        "folds": FOLDS,
        "protocol_freeze_commit": claim.get("protocol_commit"),
        "reservation_commit": claim.get("run_commit"),
        "preregistration": {"path": PREREG, "sha256": claim.get("preregistration_sha256")},
        "claim_fingerprint": claim_fingerprint(claim),
        "candidate": {
            "count": candidate_count,
            "csv": claim.get("candidate_csv"),
            "csv_sha256": claim.get("candidate_csv_sha256"),
            "sufficiency_audit_sha256": claim.get("sufficiency_audit_sha256"),
            "input_sha256": claim.get("input_sha256"),
        },
        "code_sha256": {**expected_code, "runner_recorded": code},
        "runtime_versions": claim.get("runtime_versions"),
        "benchmark": {
            "source": "evidence/losfo_h37_3_licence.json, seeds 260–264",
            "sha256": claim.get("baseline", {}).get("sha256"),
            "mean_delta_dti": benchmark_delta,
        },
        "summary": {
            "mean_delta_dti_licence_vs_base": mean_delta,
            "descriptive_95pct_t_interval": [mean_delta - ci_half, mean_delta + ci_half],
            "mean_delta_dti_licence_vs_random": mean_vs_random,
            "added_dots_total": added,
            "credit_per_added_dot": credit_per_dot,
            "positive_cells": positive_cells,
            "positive_cells_vs_random": positive_vs_random_cells,
            "positive_seed_means": positive_seed_means,
            "positive_fold_means": positive_fold_means,
            "per_seed_delta_dti": seed_means,
            "per_fold_delta_dti": fold_means,
        },
        "gates": gates,
        "promotable": promotable,
        "limitations": [
            "The LOSFO truth set consists of mapped catalogue systems, not newly discovered organizer labels.",
            "Twenty seed/fold cells are not fully independent; the t interval is descriptive, not a formal cross-fold population interval.",
            "The live break-even is fixed from the owner-reported 0.2600 anchor and does not authenticate that score or its raster association.",
            "Candidate source rasters are hash-pinned owner mirrors, not organizer-authenticated downloads.",
        ],
    }


def atomic_json(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(record, indent=2, sort_keys=True, default=_json_default) + "\n", encoding="utf-8")
    os.replace(temp, path)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, required=True)
    parser.add_argument("--claim", type=Path, required=True)
    parser.add_argument("--sufficiency-audit", type=Path, required=True)
    parser.add_argument("--benchmark", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raw = json.loads(args.raw.read_text(encoding="utf-8"))
    claim = json.loads(args.claim.read_text(encoding="utf-8"))
    audit_record = json.loads(args.sufficiency_audit.read_text(encoding="utf-8"))
    baseline_record = json.loads(args.benchmark.read_text(encoding="utf-8"))
    if claim.get("status") != "RUNNING":
        raise SystemExit("analyzer requires the one-use claim to be RUNNING")
    if claim.get("protocol_branch") != "arena/01a10412-gemsdoe28":
        raise SystemExit("claim does not belong to the session branch")
    def relative_path(path: Path) -> str:
        return path.resolve().relative_to(ROOT).as_posix() if path.resolve().is_relative_to(ROOT) else str(path)
    if relative_path(args.raw) != claim.get("result_paths", {}).get("raw"):
        raise SystemExit("raw result path differs from the reserved claim")
    if relative_path(args.out) != claim.get("result_paths", {}).get("summary"):
        raise SystemExit("summary result path differs from the reserved claim")
    if relative_path(args.sufficiency_audit) != claim.get("sufficiency_audit"):
        raise SystemExit("sufficiency audit path differs from the claim")
    if relative_path(args.benchmark) != claim.get("baseline", {}).get("path"):
        raise SystemExit("benchmark path differs from the claim")
    if claim.get("runtime_versions") != runtime_versions():
        raise SystemExit("analysis runtime differs from the reserved runtime versions")
    if claim.get("preregistration_sha256") != claim.get("code_sha256", {}).get(PREREG):
        raise SystemExit("claim preregistration hash does not match its frozen code hash")
    for rel, expected in claim.get("code_sha256", {}).items():
        path = ROOT / rel
        if not path.is_file() or sha256_file(path) != expected:
            raise SystemExit(f"frozen code hash mismatch during analysis: {rel}")
    for rel, expected in claim.get("input_sha256", {}).items():
        path = ROOT / rel
        if not path.is_file() or sha256_file(path) != expected:
            raise SystemExit(f"frozen input hash mismatch during analysis: {rel}")
    if sha256_file(args.sufficiency_audit) != claim.get("sufficiency_audit_sha256"):
        raise SystemExit("candidate sufficiency audit hash differs from the claim")
    if sha256_file(args.benchmark) != claim.get("baseline", {}).get("sha256"):
        raise SystemExit("H37-3 benchmark hash differs from the claim")
    candidate_path = ROOT / str(claim.get("candidate_csv", ""))
    if not candidate_path.is_file() or sha256_file(candidate_path) != claim.get("candidate_csv_sha256"):
        raise SystemExit("candidate CSV hash differs from the claim")
    result = evaluate(raw, claim, audit_record, baseline_record.get("euler_licence", {}))
    result["raw_result"] = {
        "path": str(args.raw.relative_to(ROOT)) if args.raw.is_relative_to(ROOT) else str(args.raw),
        "sha256": sha256_file(args.raw),
    }
    result["source_records"] = {
        "candidate_sufficiency": str(args.sufficiency_audit.relative_to(ROOT)) if args.sufficiency_audit.is_relative_to(ROOT) else str(args.sufficiency_audit),
        "baseline": str(args.benchmark.relative_to(ROOT)) if args.benchmark.is_relative_to(ROOT) else str(args.benchmark),
    }
    result["sha256"] = None
    result["sha256"] = hashlib.sha256(json.dumps(
        result, sort_keys=True, separators=(",", ":"), default=_json_default,
    ).encode()).hexdigest()
    atomic_json(args.out, result)
    print(json.dumps({
        "status": result["status"],
        "promotable": result["promotable"],
        "mean_delta_dti": result["summary"]["mean_delta_dti_licence_vs_base"],
        "credit_per_added_dot": result["summary"]["credit_per_added_dot"],
        "previous_best_mean_delta_dti": result["benchmark"]["mean_delta_dti"],
        "gates": {key: value["passed"] for key, value in result["gates"].items()},
        "out": str(args.out),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
