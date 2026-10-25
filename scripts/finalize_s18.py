#!/usr/bin/env python3
"""Bind the frozen S18 results to the exact download, fail-closed verdict and site card."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, paths, promotion, submission  # noqa: E402


def main():
    stage = json.loads((ROOT / "evidence/s18_stage_result.json").read_text())
    evaluation = json.loads((ROOT / "evidence/s18_holdout.json").read_text())
    registry = json.loads((ROOT / "evidence/s18_registry_snapshot.json").read_text())
    artifact = stage["raster"]
    path = ROOT / artifact["path"]
    exact = submission.verify_geotiff(path, paths.TEMPLATE)
    if not (exact["sha256"] == artifact["sha256"] == evaluation["raster_sha256"]):
        raise ValueError("Evidence is not bound to the downloaded file")
    foot = grid.load_footprint(paths.TEMPLATE)
    with rasterio.open(path) as src, rasterio.open(paths.TEMPLATE) as template:
        vals = src.read(1)
        validator = {"raster_sha256": exact["sha256"], "no_nan_inside": bool(np.isfinite(vals[foot]).all()),
                     "range_0_1": bool(np.isfinite(vals).all() and ((vals >= 0) & (vals <= 1)).all()),
                     "crs_match": src.crs == template.crs, "shape_match": src.shape == template.shape,
                     "transform_match": src.transform == template.transform, "single_band": src.count == 1,
                     "single_band_float32": src.count == 1 and src.dtypes[0] == "float32",
                     "no_nan_anywhere": bool(np.isfinite(vals).all()),
                     "values": np.unique(vals).tolist(), "shape": list(src.shape),
                     "crs": str(src.crs), "transform": list(src.transform)[:6],
                     "on_catalogue": int(np.count_nonzero(vals[grid.load_labels(paths.LABELS)]))}
    note = "S18 MXTP: extrapolated TMI/gravity ridges; 11082 dots; holdout rejected; research only; DO NOT SUBMIT."
    h = {key: evaluation[key] for key in ("label", "raster_sha256", "baseline_sha256", "evaluator_version",
         "evaluator_hashes", "withheld_positives", "unique_withheld_positive_pixels", "whole_segments",
         "buffered", "visible_only_features", "pixel_exact_visible_mask", "pooled", "alpha", "beta", "kernel_m", "kernel")}
    h.update(dti=evaluation["candidate_pooled"]["dti"], ci95=evaluation["ci"]["candidate_ci95"],
             baseline_dti=evaluation["baseline_pooled"]["dti"], baseline_ci95=evaluation["ci"]["baseline_ci95"],
             paired_gain=evaluation["pooled_gain"], paired_gain_ci95=evaluation["ci"]["paired_gain_ci95"],
             uncertainty_method=evaluation["ci"]["method"], limitation=evaluation["limitations"])
    reg = {"complete": registry["complete_within_declared_scope"], "scope": registry["scope"],
           "global_parallel_registry_verified": False, "manifest_sha256": stage["registry_sha256"],
           "members": [r["sha256"] for r in registry["entries"] if r["status"] == "included"],
           "surface": stage["surface"], "dots": stage["dots"]}
    for phase in ("surface", "dots"):
        reg[f"{phase}_max_spearman"] = max(r["spearman"] for r in stage[phase])
        reg[f"{phase}_max_within_3px_fraction"] = max(r["within_3px_fraction"] for r in stage[phase])
    card = {"session": "S18-MXTP", "date_utc": "2026-10-25", "lane": "migration-extrapolated placement",
            "lane_authorization": "Autonomous adoption of repository next step; prompt omitted explicit method paragraph",
            "hypothesis": "Linear-in-height TMI/gravity HG-ridge loci extrapolate to concealed contact traces off the standard detector network.",
            "mechanism": "1/2/3 km continuation; q0=2q1-q2; three-height consistency; independent probability-order dot packing.",
            "non_fault_mimic": "Dipping lithologic contact, mafic dike, or superposed potential-field sources without fault displacement.",
            "holdout": h, "feature_canaries": {n: v["max_auc_1mauc"] for n, v in stage["canaries"]["features"].items()},
            "registry": reg, "raster_sha256": exact["sha256"], "validator": validator,
            "validator_full": exact, "submission_name": "GEMSDOE28-S18-MXTP-3e95505c011a", "note": note,
            "download": artifact["path"].removeprefix("docs/"), "dot_count": exact["nonzero_inside_px"],
            "experiments_used": 3, "experiment_budget": 3, "verdict": "negative",
            "submission_ready": False, "slot_selected": False, "organizer_receipt": None,
            "disposition": "Unique and format-valid RESEARCH TIFF; failed frozen holdout superiority gate. DO NOT SUBMIT.",
            "evidence": "evidence/s18_holdout.json"}
    card["strict_protocol_limitations"] = {
        "upstream_template_api_equivalence_established": False,
        "exclusive_external_lane_assignment_confirmed": False,
        "global_parallel_registry_complete": False,
        "certified_global_best_baseline": False,
        "scope": "Repository-existing shared harness/writer; later upstream API pins were not executed by this experiment."
    }
    gate = promotion.promotion_gate(card)
    card["evidence_schema_gate"] = gate
    # A schema pass cannot override a frozen scientific rejection or unknown lane/global registry.
    assert not evaluation["gate_passed"] and gate["verdict"] == "negative"
    assert len(note) <= 140 and exact["hard_checks_passed"]
    for dest in (ROOT / "evidence/s18_mxtp_run_card.json", ROOT / "docs/data/run_card_s18.json",
                 ROOT / "docs/data/run_card_2026-10-25.json"):
        dest.write_text(json.dumps(card, indent=2, allow_nan=False) + "\n")
    (ROOT / "docs/downloads/note-s18-mxtp.txt").write_text(note + "\n")
    manifest_path = ROOT / "docs/downloads/manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["s18_candidate"] = {"filename": path.name, "submission_name": card["submission_name"],
                                  "sha256": exact["sha256"], "note": note,
                                  "format_verified": True, "unique_within_snapshot": True,
                                  "submission_ready": False, "verdict": "negative",
                                  "status": card["disposition"], "run_card": "data/run_card_s18.json"}
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"submission_name": card["submission_name"], "validator_pass": exact["hard_checks_passed"],
                      "schema_gate": gate, "disposition": card["disposition"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
