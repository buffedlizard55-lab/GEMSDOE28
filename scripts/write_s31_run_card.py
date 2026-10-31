#!/usr/bin/env python3
"""Assemble the S31 JSON run card from the session's evidence files (no hand-typed numbers)."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

HOLD = json.loads((ROOT / "evidence/s31_holdout.json").read_text())
CAL = json.loads((ROOT / "evidence/s31_calibration.json").read_text())
BUILD = json.loads((ROOT / "evidence/s31_build.json").read_text())
GATE = json.loads((ROOT / "evidence/s31_midband_gate.json").read_text())
SEEDS = json.loads((ROOT / "evidence/s31_seed_audit.json").read_text())

fill = BUILD["frozen_rule"]["selected"]
verdict_ok = GATE["verdict"]["ok_to_download"]
card = {
    "session": "S31",
    "date_utc": "2026-10-31",
    "branch": "arena/c4748811-gemsdoe28",
    "lane": ("hide-and-recover holdout lane (template cached feature stack; src/gems27/holdout.py + "
             "metric.py; withhold whole fault segments; catalogue-based features from visible faults "
             "only; visible faults masked pixel-exactly; pooled DTI alpha 0.2 beta 0.8, 300 m triangular kernel)"),
    "hypothesis": ("H-S31-A/B'/C/D: extend the leaderboard-verified catalogue-distance prune to the "
                   "(3,6] px band with a strain-rate edge condition, and refill the uniqueness-mandated "
                   "dots in the holdout-winning distance band (mid (3,6] vs far >=6 px) with the "
                   "holdout-winning prior; composition chosen by the family calibration."),
    "mechanism": ("Dots at 1-2 px of the catalogue are ~pure false positives under the DTI kernel "
                  "(verified: +0.0070 USER-REPORTED for removing 2,545 such dots vs +0.0288 theoretical "
                  "max). The (3,6] px band is where sub-parallel unmapped splays are most plausible; "
                  "uniqueness (<=70% of dots within 3 px of any registry raster) forces >=32% new dots, "
                  "so their band and prior decide the score."),
    "named_non_fault_process": ("Digitisation/rasterisation halo of the mapped catalogue itself and "
                                "lithologic/basin-margin geophysical edges (gravity/magnetic contacts, "
                                "strain-rate imagery seams) can mimic sub-parallel fault splays."),
    "holdout": {
        "label": "HOLDOUT-DTI",
        "evaluator_version": HOLD["evaluator_version"],
        "n_withheld_splits": HOLD["arms"]["base"]["n_splits"],
        "withheld_positives_total": HOLD["arms"]["base"]["FNw"] + int(round(HOLD["arms"]["base"]["TPw"])),
        "dti_base": HOLD["arms"]["base"]["dti_pooled"],
        "dti_selected_fill_arm": HOLD["arms"][fill.split(":", 1)[1]]["dti_pooled"],
        "ci95": HOLD["arms"][fill.split(":", 1)[1]]["dti_fold_ci95"],
        "note": "pooled DTI over hide-and-recover splits; catalogue-internal proxy, never a leaderboard score",
    },
    "leakage_canary": HOLD["leakage_canary"],
    "correlation_overlap_vs_registry": {
        "surface_prior_vs_registry_density_spearman": BUILD["surface_rank_corr_prior_vs_registry_density"],
        "final_max_overlap_within_3px": GATE["max_overlap"],
        "final_max_overlap_raster": GATE["max_overlap_raster"],
        "rasters_over_70pct": GATE["rasters_over_70pct"],
        "density_rank_corr_max_abs": GATE["density_rank_corr_max_abs"],
        "binary_spearman": "not applicable (tied ranks), as in S30",
    },
    "raster_sha256": GATE["sha256"],
    "validator": {
        "no_nan_inside_footprint": GATE["no_nan_inside_footprint"],
        "values_in_01": GATE["values_in_01"],
        "crs_shape_transform_match": GATE["validator_hard_checks_passed"],
        "hard_failures": GATE["validator_failures"],
    },
    "projection": {
        "label": "PROJECTION calibrated on 13 OWNER-REPORTED family scores (LOO R^2 = "
                 f"{round(CAL['primary']['loo_r2'], 3)}); NOT a score, NOT organizer-confirmed",
        **GATE["projection"],
    },
    "submission": {
        "name": BUILD["file"],
        "note": BUILD["note"],
        "note_chars": BUILD["note_chars"],
        "sha256": BUILD["sha256"],
    },
    "verdict": ("promote to the owner's selector step (file is format-valid, unique, lane-clean; "
                "score remains unestablished)" if verdict_ok else "negative: gate failed"),
    "experiments_used": 3,
    "experiment_cap": 3,
    "seed_freshness": {"range": "400-404", "collisions": len(SEEDS.get("collisions_excluding_exact_claim", []))},
}
(ROOT / "evidence/s31_midband_run_card.json").write_text(json.dumps(card, indent=1) + "\n")
# also expose under docs/data for the Pages site
(ROOT / "docs/data/s31_midband_run_card.json").write_text(json.dumps(card, indent=1) + "\n")
print(json.dumps({k: card[k] for k in ("session", "verdict", "raster_sha256", "experiments_used")}, indent=1))
