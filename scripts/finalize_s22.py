#!/usr/bin/env python3
"""S22 finalize — downloads-manifest registration, note file, protocol run card.

Reads evidence/s22_{forensic,holdout,candidate_build}.json. Writes:
  docs/downloads/manifest.json (adds s22_candidate), note file, evidence/s22_run_card.json.
Verdict semantics: verdict='promote' means the frozen S22 gate in knowledge/62 passed.
submission_ready stays False: slot selection is a separate selector step (protocol section 6).
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, paths  # noqa: E402

DL = ROOT / "docs/downloads"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main() -> int:
    hold = json.loads((ROOT / "evidence/s22_holdout.json").read_text())
    build = json.loads((ROOT / "evidence/s22_candidate_build.json").read_text())
    fore = json.loads((ROOT / "evidence/s22_forensic.json").read_text())
    cid = build["content_id"]
    stem = f"gems28-s22-ctxhgb-20261026-{cid}"
    fin = DL / f"{stem}-allfinite.tif"
    nan = DL / f"{stem}-nan.tif"
    zp = DL / f"{stem}-nan.zip"
    fin_sha = sha256_file(fin)

    # Independent validator booleans by fresh re-read of the shipped primary bytes.
    foot = grid.load_footprint(paths.TEMPLATE)
    with rasterio.open(paths.TEMPLATE) as t:
        t_sig = (t.crs, t.shape, tuple(t.transform)[:6])
    with rasterio.open(fin) as s:
        arr = s.read(1)
        validator = {
            "raster_sha256": fin_sha,
            "no_nan_inside": bool(np.isfinite(arr[foot]).all()),
            "no_nan_whole_array": bool(np.isfinite(arr).all()),
            "range_0_1": bool(arr.min() >= 0 and arr.max() <= 1),
            "value_set_inside": sorted({float(v) for v in np.unique(arr[foot])}),
            "crs_match": bool(s.crs == t_sig[0]),
            "shape_match": bool(s.shape == t_sig[1]),
            "transform_match": bool(tuple(s.transform)[:6] == t_sig[2]),
            "single_band": bool(s.count == 1 and s.dtypes[0] == "float32"),
        }

    note = (f"S22 ctxHGB multiscale-context 37654d | HOLDOUT-DTI 0.1202 vs dotted 0.1052 "
            f"(+0.0150) seeds360-362 | {cid}")
    assert 0 < len(note) <= 140, len(note)
    note_name = f"note-gems28-s22-{cid}.txt"
    (DL / note_name).write_text(note + "\n", encoding="utf-8")

    pooled = hold["pooled_dti"]
    ratio = pooled["lane"] / pooled["dotted_b2"]
    projection = {
        "label": "MODEL PROJECTION (not a score, not an organizer receipt)",
        "method": "USER-REPORTED champion anchor 0.2778 x pooled HOLDOUT-DTI ratio lane/dotted_b2 "
                  "(same ratio method as S21); bootstrap ratio CI from the 12 cells",
        "ratio": ratio,
        "ratio_ci95": [1.1033, 1.1801],
        "projected_live_dti": 0.2778 * ratio,
        "projected_ci95": [0.2778 * 1.1033, 0.2778 * 1.1801],
        "caveats": [
            "Anchor 0.2778 is USER-REPORTED; no organizer receipt exists in this repository.",
            "Holdout truth is catalogue-internal hidden components; live truth is expert-mapped NEW faults. Transfer is unproven.",
            "S22 dots sit closer to the catalogue than the champion's (median 8px vs 19.6px; ring (2,3] 17.8% vs 5.8%); live inversion proved ring <=2px earns ~0 and ring (2,3] live credit is unmeasured, so live transfer may be worse than this ratio.",
            "Public leaderboard is a public/private split; a single GeoTIFF is also re-scored in the Final round on expanded labels.",
        ],
    }

    canaries = {k: v for k, v in hold["canary_single_feature_auc_cell_360_NW"].items() if v is not None}
    comps = build["uniqueness"]["comparisons"]
    card = {
        "session_id": "G28-S22-20261026",
        "date_utc": "2026-10-26",
        "branch": "arena/f2afeb88-gemsdoe28",
        "lane": "S22-H1 multi-scale spatial-context gradient boosting: shared 32-band stack + Gaussian-pyramid "
                "(sigma2/5 means, |grad sigma2|) context of 10 physical bands + structure-tensor coherence of "
                "lidar_step_max/tmi_hg; ridge-restricted 2.8px dot emission outside the <=2px catalogue ring. "
                "Self-assigned and frozen in knowledge/62 before any S22 canary/DTI (prompt's method paragraph absent).",
        "hypothesis": "Explicit multi-scale spatial context closes the gap between a fresh per-pixel tabular "
                      "detector (S21 PU-HGB, HOLDOUT-DTI 0.0839 vs 0.1062 baseline) and the H19-5 ensemble "
                      "geography, because catalogue-missing faults are separated from unfaulted contacts by "
                      "along-strike-coherent pattern at 200-500 m scales, not by per-pixel habitat values.",
        "mechanism": "Young/buried normal faults sustain a scarp-step / potential-field gradient coherently along "
                     "strike at a consistent piedmont position; pyramid means encode position, smoothed gradient "
                     "magnitudes encode sustained edges, tensor coherence encodes linearity. The HGB learns their "
                     "joint habitat from visible catalogue pixels only.",
        "non_fault_mimic": "Roads, canals, paleo-shorelines, terrace risers, incised drainages and unfaulted "
                           "lithologic contacts sustained along strike (linear context without slip).",
        "holdout": {
            "label": "HOLDOUT-DTI",
            "evaluator_version": "gems27.metric.dti_binary + gems27.holdout quadrant component-hide 20% "
                                 "(gems-segment-pooled-v1 semantics, as S21)",
            "raster_sha256": fin_sha,
            "baseline_sha256": "91eae1ca42ec845eaa8c2ba32da49806e24751743459b8a10017c479bbe639b8",
            "baseline": "dotted H19-5 d2.8 file dots, pruned vs VISIBLE catalogue only (d>2), S21 construction",
            "withheld_positives": int(hold["withheld_positives_pooled_across_cells"]),
            "seeds": hold["seeds"],
            "n_cells": hold["n_cells"],
            "dti": pooled["lane"],
            "ci95": hold["pooled_ci95"]["lane"],
            "baseline_dti": pooled["dotted_b2"],
            "baseline_ci95": hold["pooled_ci95"]["dotted_b2"],
            "control_dti": pooled["control"],
            "paired_gain": hold["delta_lane_minus_base"],
            "paired_gain_ci95": hold["delta_lane_minus_base_ci95"],
            "paired_gain_vs_control": hold["delta_lane_minus_control"],
            "paired_gain_vs_control_ci95": hold["delta_lane_minus_control_ci95"],
            "cells_lane_wins_vs_base": "12/12",
            "whole_segments": True,
            "buffered": False,
            "buffer_note": "Quadrant component-hide: training labels come only from the other three quadrants and "
                           "all features are label-free, so no label leakage path exists; there is no 600 m LOSFO "
                           "buffer around hidden components. Buffered LOSFO confirmation is a named selector-level "
                           "follow-up, not run here (3-experiment budget).",
            "visible_only_features": True,
            "pixel_exact_visible_mask": True,
            "pooled": True,
            "alpha": 0.2, "beta": 0.8, "kernel_m": 300, "kernel": "triangular",
        },
        "feature_canaries": canaries,
        "canary_note": "AUC of each feature alone, hidden truth vs 20k allowed negatives, cell 360-NW. "
                       "Worst 0.7200 (ctx_lidar_relief_g5) <= 0.90: physiographic habitat, label-free by "
                       "construction; no leakage signature.",
        "registry": {
            "complete": False,
            "completeness_note": "Snapshot registry of 30 distinct dot-sets (local docs/downloads allfinite files + "
                                 "byte-fetched GEMSDOE30/31/32/33/36 best files + H19-5 lineage), 2026-10-26. Not a "
                                 "synchronized global parallel registry; unmerged concurrent work is unknowable here.",
            "manifest_sha256": sha256_file(DL / "manifest.json"),
            "members": [c["dotset_sha256"] for c in comps],
            "member_identity": "dot-set SHA-256 (row/col int32 bytes), not file SHA-256",
            "surface": [{"raster_sha256": c["dotset_sha256"],
                         "spearman": c["spearman_surface_vs_registry_sample200k"]} for c in comps],
            "dots": [{"raster_sha256": c["dotset_sha256"],
                      "spearman": c["spearman_surface_vs_registry_sample200k"],
                      "within_3px_fraction": c["frac_our_dots_within3px"]} for c in comps],
            "worst_overlap3px": build["uniqueness"]["worst_overlap3px"],
            "vs_GEMSDOE32_champion": build["uniqueness"]["vs_GEMSDOE32_champion"],
            "thresholds": {"abs_spearman_max": 0.90, "within_3px_max": 0.70},
            "pass_snapshot": True,
            "margin_warning": "Worst 3px overlap is 0.6992 vs the unscored dense H37-1 probe-union-pool raster "
                              "(a union of many detectors' pools) - a pass by 0.0008. Against every SCORED raster "
                              "the overlap is <=0.4845 (H19-5 parent) and 0.4205 vs the GEMSDOE32 champion.",
        },
        "raster_sha256": fin_sha,
        "dotset_sha256": build["dotset_sha256"],
        "validator": validator,
        "submission_name": f"GEMSDOE28-S22-ctxhgb-{cid}",
        "note": note,
        "note_chars": len(note),
        "files": {
            "primary_allfinite": fin.name,
            "nan_twin": nan.name,
            "zip_single_nan": zp.name,
            **{k: v for k, v in build["files"].items()},
        },
        "n_dots": build["n_dots"],
        "catalogue_distance_profile_px": {
            "S22": {"(2,3]": 6688, "(3,5]": 5989, "(5,10]": 9923, ">10": 15054, "median": 8.0},
            "GEMSDOE32_champion": {"(2,3]": 2171, "(3,5]": 3466, "(5,10]": 5723, ">10": 26294, "median": 19.65},
        },
        "live_projection": projection,
        "forensic_anchor": {
            "champion_file_sha256": fore["files"]["GEMSDOE32_champion_h33_2_b2_reported_0.2778"]["file_sha256"],
            "lineage_symdiffs_zero": True,
            "all_nine_focus_bests_one_nested_family": True,
            "detail": "evidence/s22_forensic.json",
        },
        "experiments_run": 3,
        "experiment_cap": 3,
        "verdict": "promote",
        "verdict_scope": "Frozen S22 gate (knowledge/62) passed in full: canary, pooled HOLDOUT-DTI > baseline with "
                         "CI>0, > control, snapshot uniqueness, validator. Shared promotion_gate still blocks on "
                         "registry completeness + LOSFO buffer (see promotion_gate_output when run).",
        "submission_ready": False,
        "slot_selected": False,
        "selector_checklist": [
            "Confirm remaining weekly allowance on the authenticated DrivenData submission page (rules state 3/week; account state unknown here).",
            "Decide whether to require the buffered LOSFO confirmation run first (recommended; next session, fresh seeds).",
            "Upload ONLY docs/downloads/" + fin.name + " (or the single-member ZIP of the NaN twin), paste the registered note, preserve the organizer receipt + this file's SHA-256.",
            "Remember the single chosen GeoTIFF is re-scored in the Final Prize Round on expanded expert labels.",
        ],
        "limitations": [
            "Owner-mirrored inputs are hash-pinned but not organizer-authenticated.",
            "Holdout truth is catalogue-internal; live expert-new-fault transfer unproven (near-catalogue dot concentration is the main risk).",
            "12 cells / 4 geographic blocks: CIs are wide; seeds 360-362 claimed here for the first time.",
            "Registry is snapshot-bounded; worst overlap margin vs an unscored union-pool raster is 0.0008.",
            "No DrivenData account, receipt, or weekly-cap access in this sandbox; portal acceptance of any file is not guaranteed.",
        ],
    }
    (ROOT / "evidence/s22_run_card.json").write_text(json.dumps(card, indent=2) + "\n")

    # Register in downloads manifest (same shape as s20v_candidate).
    manifest_path = DL / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["s22_candidate"] = {
        "slug": "s22-ctxhgb",
        "hypothesis": "S22-H1 multi-scale spatial-context HGB (32 base + Gaussian-pyramid/tensor context), "
                      "ridge-restricted 2.8px emission, d_cat>2px, N=37,654",
        "content_id": cid,
        "nan": nan.name,
        "allfinite": fin.name,
        "zip": zp.name,
        "sha256_nan": build["files"]["nan_twin"]["sha256"],
        "sha256_allfinite": fin_sha,
        "sha256_zip": build["files"]["zip"]["sha256"],
        "bytes_nan": build["files"]["nan_twin"]["bytes"],
        "bytes_allfinite": build["files"]["allfinite_primary"]["bytes"],
        "bytes_zip": build["files"]["zip"]["bytes"],
        "emitted_px": build["n_dots"],
        "format_verified": True,
        "status": "PASSES FROZEN S22 GATE — SELECTOR DECISION REQUIRED, NO SLOT SPENT BY THIS SESSION; "
                  "HOLDOUT-DTI quadrant component-hide seeds 360-362 pooled lane 0.12018 vs dotted_b2 0.10519 "
                  "(paired +0.01498, 95% CI [+0.01067,+0.01932], 12/12 cells) vs per-pixel control 0.09505; "
                  "canary max AUC 0.7200 PASS; uniqueness vs champion 42.1% within3px / |Spearman| 0.067 PASS, "
                  "worst 69.92% vs unscored H37-1 union-pool (margin 0.0008, disclosed); validator PASS "
                  "(all-finite {0,1}); MODEL projection ~0.317 vs USER-REPORTED 0.2778 anchor (not a score); "
                  "verdict promote (frozen gate), submission_ready=false, slot_selected=false.",
        "note": note,
        "note_file": note_name,
        "submission_name": f"GEMSDOE28-S22-ctxhgb-{cid}",
        "run_card": "evidence/s22_run_card.json",
        "holdout_evidence": "evidence/s22_holdout.json",
        "holdout_preregistration": "knowledge/62_s22_preregistration.md",
        "holdout_seeds": "360-362",
        "verdict": "promote",
        "submission_ready": False,
        "slot_selected": False,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"run_card": "evidence/s22_run_card.json", "note": note, "note_chars": len(note),
                      "manifest_registered": stem}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
