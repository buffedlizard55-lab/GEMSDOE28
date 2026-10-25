#!/usr/bin/env python3
"""Exercise shared-tool contracts on synthetic fixtures, not a geological experiment.

No private metric, evaluator or writer is created. This checks the hash-pinned
upstream implementation and records its limitations. No submission is emitted.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import metric  # noqa: E402
from gems27.shared_template import load_shared, verify_assets  # noqa: E402


def exercise(shared) -> dict:
    footprint = np.ones((240, 240), bool)
    labels = np.zeros(footprint.shape, bool)
    labels[40, 20:220] = True  # Crosses the northern quadrant boundary.
    labels[170, 20:75] = True
    labels[180, 165:220] = True
    context = shared.holdout.SegmentHoldout(footprint, labels, buffer_px=15)
    checks = {}
    for fold in context.folds:
        hidden_ids = fold["hidden_component_ids"]
        visible_ids = context.components[fold["visible"]]
        checks[fold["name"] + "_whole_components_hidden"] = not bool(np.isin(visible_ids, hidden_ids).any())
        checks[fold["name"] + "_train_validation_disjoint"] = not bool((fold["train"] & fold["valid"]).any())
        checks[fold["name"] + "_truth_not_visible"] = not bool((fold["truth"] & fold["visible"]).any())
    rng = np.random.default_rng(20261025)
    canary = context.canary({"random_control": rng.random(footprint.shape),
                             "deliberate_catalogue_leak": labels.astype(float),
                             "inverted_catalogue_leak": 1 - labels.astype(float)})
    checks["canary_rejects_deliberate_leak"] = canary["features"]["deliberate_catalogue_leak"]["leakage_suspected"]
    checks["canary_rejects_inverted_leak"] = canary["features"]["inverted_catalogue_leak"]["leakage_suspected"]
    checks["random_control_not_flagged"] = not canary["features"]["random_control"]["leakage_suspected"]
    errors = []
    for _ in range(12):
        truth = rng.random((17, 19)) < 0.05
        prediction = rng.random((17, 19)) < 0.09
        valid = rng.random((17, 19)) < 0.9
        known = rng.random((17, 19)) < 0.04
        local = metric.dti_binary(prediction, truth, valid, known)
        upstream = shared.metric.dti_score_fast(prediction, truth, valid, known)
        errors += [abs(local[a] - upstream[b]) for a, b in (("TPw", "TP_w"), ("FPw", "FP_w"), ("FNw", "FN_w"))]
    checks["legacy_metric_matches_pinned_metric_on_fixtures"] = max(errors) < 1e-9
    return {"label": "SOFTWARE CONTRACT TEST, not HOLDOUT-DTI or a competition result",
            "passed": all(checks.values()), "checks": checks,
            "random_metric_fixtures": 12, "max_component_disagreement": max(errors),
            "shared_evaluator_version": shared.holdout.MTR_EVALUATOR_VERSION,
            "limitations": ["Whole raster components are a conservative proxy, not authenticated fault segment IDs.",
                            "Each lane must rebuild catalogue-dependent features from fold.visible; this cannot be inferred from a stored final TIFF.",
                            "The shared evaluate_holdout.py entry point is a frozen MTR1-specific runner, not an assigned lane for this session.",
                            "Synthetic software checks do not validate any geological hypothesis or current holdout best."],
            "experiments_run": 0, "new_raster_generated": False}


def main() -> int:
    report = {"shared_assets": verify_assets(), **exercise(load_shared())}
    destination = ROOT / "evidence/shared_template_contract.json"
    destination.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps(report, indent=2, allow_nan=False))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
