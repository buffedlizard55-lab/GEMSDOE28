import copy
import json

import numpy as np
from scripts.analyze_h38_1_holdout import BEST_FARFIELD_ADD_ARM, atomic_json, evaluate

SEEDS = list(range(265, 270))
FOLDS = ["NW", "NE_LidarGapHeavy", "SW", "SE"]
ARM = "H38-1 shallow Euler × gravity × low-relief licence"
PREREG = "knowledge/38_preregistration_H38-1.md"
CANDIDATE_SHA = "a" * 64
CODE = {
    "scripts/run_losfo_harness.py": "1" * 64,
    "src/gems27/losfo.py": "2" * 64,
    "src/gems27/oof_detector.py": "3" * 64,
    "src/gems27/metric.py": "4" * 64,
    "src/gems27/thinning.py": "5" * 64,
    "src/gems27/holdout.py": "6" * 64,
    "src/gems27/grid.py": "7" * 64,
    "src/gems27/paths.py": "8" * 64,
    "src/gems27/packing.py": "9" * 64,
}
RUNTIME = {"python": "3.12.0", "numpy": "2.0.0", "scipy": "1.14.0", "scikit_learn": "1.5.0", "rasterio": "1.4.0"}


def fixture():
    claim = {
        "status": "RUNNING",
        "arm_name": ARM,
        "seeds": SEEDS,
        "candidate_csv": "evidence/h38_1_candidate_clusters.csv",
        "candidate_csv_sha256": CANDIDATE_SHA,
        "candidate_count": 140,
        "code_sha256": CODE,
        "runtime_versions": copy.deepcopy(RUNTIME),
        "baseline": {"mean_delta_dti_licence_vs_base": BEST_FARFIELD_ADD_ARM, "sha256": "b" * 64},
        "run_commit": "deadbeef",
    }
    def dti(tp, fp, n_truth=10):
        return tp / (tp + 0.2 * fp + 0.8 * (n_truth - tp) + 1e-7)

    base_tp, base_fp = 1.0, 9.0
    base_dti = dti(base_tp, base_fp)
    candidate_tp = base_tp + 0.6
    random_tp = base_tp + 0.2
    candidate_dti = base_dti + 0.001
    random_dti = base_dti + 0.0002
    candidate_fp = (candidate_tp / candidate_dti - candidate_tp - 0.8 * (10 - candidate_tp) - 1e-7) / 0.2
    random_fp = (random_tp / random_dti - random_tp - 0.8 * (10 - random_tp) - 1e-7) / 0.2
    cells = []
    for seed in SEEDS:
        for fold in FOLDS:
            cells.append({
                "seed": seed,
                "fold": fold,
                "n_truth": 10,
                "min_dist_truth_to_known_px": 8.0,
                "losfo": {"dti": base_dti, "tp": base_tp, "fp": base_fp, "dots": 100, "n_truth": 10},
                "euler": {
                    "delta_dti_licence": candidate_dti - base_dti,
                    "delta_dti_random": random_dti - base_dti,
                    "delta_tp_licence": candidate_tp - base_tp,
                    "delta_tp_random": random_tp - base_tp,
                    "added_dots": 10,
                    "control_dots": 10,
                    "licence": {"dti": dti(candidate_tp, candidate_fp), "tp": candidate_tp,
                                "fp": candidate_fp, "dots": 110, "n_truth": 10},
                    "random_control": {"dti": dti(random_tp, random_fp), "tp": random_tp,
                                       "fp": random_fp, "dots": 110, "n_truth": 10},
                    "integrity": {
                        "licence_base_overlap_px": 0,
                        "licence_visible_catalogue_overlap_px": 0,
                        "random_base_overlap_px": 0,
                        "random_visible_catalogue_overlap_px": 0,
                    },
                },
            })
    raw = {
        "seeds": SEEDS,
        "cells": cells,
        "euler_licence": {
            "arm_name": ARM,
            "preregistration": PREREG,
            "input": {
                "name": ARM,
                "preregistration": PREREG,
                "csv": "evidence/h38_1_candidate_clusters.csv",
                "csv_sha256": CANDIDATE_SHA,
                "base_euler_rule": "depth_mad_m <= 60 and median_depth_m <= 400 and n_solutions >= 8",
                "n_candidate_clusters": 140,
                "thin_d_px": 2.8,
            },
            "n_cells": 20,
            "added_dots_total": 200,
            "control_dots_total": 200,
            "credit_per_added_dot": 0.06,
            "tau_live_bar": 0.0548,
            "mean_delta_dti_licence_vs_base": 0.001,
            "mean_delta_dti_random_vs_base": 0.0002,
            "mean_delta_dti_licence_vs_random": 0.0008,
        },
        "code_sha256": {
            "runner": CODE["scripts/run_losfo_harness.py"],
            "losfo": CODE["src/gems27/losfo.py"],
            "oof_detector": CODE["src/gems27/oof_detector.py"],
            "metric": CODE["src/gems27/metric.py"],
            "thinning": CODE["src/gems27/thinning.py"],
            "holdout": CODE["src/gems27/holdout.py"],
            "grid": CODE["src/gems27/grid.py"],
            "paths": CODE["src/gems27/paths.py"],
            "packing": CODE["src/gems27/packing.py"],
        },
        "runtime_versions": copy.deepcopy(RUNTIME),
        "meta": {"dilate_px": 3, "buffer_px": 6},
        "thin_d_px": 2.8,
        "far_field_check": {"min_dist_truth_to_known_px_over_cells": 8.0},
    }
    audit = {"status": "READY", "clusters": {"selected_clusters": 140}}
    benchmark = {"mean_delta_dti_licence_vs_base": BEST_FARFIELD_ADD_ARM}
    return raw, claim, audit, benchmark


def test_all_frozen_h38_1_gates_pass_only_when_every_rule_is_satisfied():
    raw, claim, audit, benchmark = fixture()
    result = evaluate(raw, claim, audit, benchmark)
    assert result["status"] == "PASS"
    assert result["promotable"] is True
    assert all(gate["passed"] for gate in result["gates"].values())
    assert result["summary"]["added_dots_total"] == 200
    assert abs(result["summary"]["credit_per_added_dot"] - 0.06) < 1e-12
    assert result["gates"]["C5_beats_previous_farfield_add_arm_best"]["passed"] is True


def test_live_bar_and_previous_best_are_independent_hard_gates():
    raw, claim, audit, benchmark = fixture()
    for cell in raw["cells"]:
        cell["euler"]["delta_tp_licence"] = 0.05  # 0.005 credit per dot
        cell["euler"]["delta_dti_licence"] = BEST_FARFIELD_ADD_ARM / 2
    result = evaluate(raw, claim, audit, benchmark)
    assert result["gates"]["C2_live_economic_bar"]["passed"] is False
    assert result["gates"]["C5_beats_previous_farfield_add_arm_best"]["passed"] is False
    assert result["promotable"] is False


def test_integrity_gate_checks_runner_aggregates_runtime_and_far_field_separation():
    raw, claim, audit, benchmark = fixture()
    raw["euler_licence"]["added_dots_total"] = 201
    raw["runtime_versions"]["numpy"] = "wrong-version"
    raw["far_field_check"]["min_dist_truth_to_known_px_over_cells"] = 7.0
    result = evaluate(raw, claim, audit, benchmark)
    checks = result["gates"]["C4_support_and_integrity"]["integrity_checks"]
    assert checks["runner_aggregate_matches_cell_metrics"] is False
    assert checks["runtime_versions_match_claim"] is False
    assert checks["far_field_truth_at_least_800m_from_visible_labels"] is False
    assert result["gates"]["C4_support_and_integrity"]["passed"] is False
    assert result["promotable"] is False


def test_integrity_gate_recomputes_cell_deltas_from_arm_metrics():
    raw, claim, audit, benchmark = fixture()
    raw["cells"][0]["euler"]["delta_dti_licence"] += 0.01
    result = evaluate(raw, claim, audit, benchmark)
    integrity = result["gates"]["C4_support_and_integrity"]["integrity_checks"]
    assert integrity["per_cell_derived_metrics_match_reported_arms"] is False
    assert result["gates"]["C4_support_and_integrity"]["passed"] is False


def test_integrity_gate_recomputes_dti_from_weighted_tp_fp_and_truth():
    raw, claim, audit, benchmark = fixture()
    raw["cells"][0]["euler"]["licence"]["dti"] += 0.01
    result = evaluate(raw, claim, audit, benchmark)
    checks = result["gates"]["C4_support_and_integrity"]["integrity_checks"]
    assert checks["per_cell_derived_metrics_match_reported_arms"] is False
    assert result["gates"]["C4_support_and_integrity"]["passed"] is False


def test_analyzer_json_writer_serializes_numpy_scalar_and_array_values(tmp_path):
    destination = tmp_path / "result.json"
    atomic_json(destination, {
        "count": np.int64(3),
        "score": np.float64(0.5),
        "ok": np.bool_(True),
        "values": np.array([1, 2], dtype=np.int64),
    })
    assert json.loads(destination.read_text()) == {
        "count": 3, "score": 0.5, "ok": True, "values": [1, 2],
    }


def test_analyzer_rejects_changed_seed_set_and_unmatched_control_counts():
    raw, claim, audit, benchmark = fixture()
    wrong = copy.deepcopy(raw)
    wrong["seeds"] = [260, 261, 262, 263, 264]
    try:
        evaluate(wrong, claim, audit, benchmark)
    except ValueError as error:
        assert "seeds differ" in str(error)
    else:
        raise AssertionError("wrong holdout decade was accepted")

    wrong = copy.deepcopy(raw)
    wrong["cells"][0]["euler"]["control_dots"] = 9
    try:
        evaluate(wrong, claim, audit, benchmark)
    except ValueError as error:
        assert "not exactly matched" in str(error)
    else:
        raise AssertionError("unmatched random control was accepted")
