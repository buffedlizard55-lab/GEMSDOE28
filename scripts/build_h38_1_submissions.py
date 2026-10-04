#!/usr/bin/env python3
"""Build the H38-1 multi-physics corroborated submission package and update docs/downloads/manifest.json.

Protocol: ``knowledge/38_preregistration_H36_1_and_H38_farfield.md``.
Evidence:
  * LOSFO far-field (seeds 265-269, 20 cells): ``evidence/losfo_session14_h36_1_and_h38.json``
    - H36-1 (rung30_blind_r1) passes F1-F4 (+0.001713 mean LOSFO dDTI vs d=2.8, 16/20 cells, 5/5
      seeds, e_far = 0.01359 < tau_live = 0.054852; F1 +0.002073 vs matched-N random drop; F4 0.00
      TP loss across 20/20 cells).
    - H38-1 (h38_1_joint & h38_1_joint_on_r30_r1) passes C1-C4 (ALL_PASS = True: +0.000792 on base
      at 0.07724 credit/dot, 17/20 cells, 4/5 seeds; +0.000747 on rung30_blind_r1 at 0.06993
      credit/dot, 16/20 cells, 4/5 seeds, +0.002460 over d=2.8).
  * Interleaved 4-fold spatial-CV holdout (seeds 270-279, 40 cells):
    ``evidence/h38_1_interleaved_holdout.json``
    - h38_1_joint: +0.000656 mean dDTI (27/40 cells, 9/10 seeds, 4/4 folds, 0.06440 credit/dot).
    - h38_1_joint_on_r30_r1: +0.000543 mean dDTI over H36-1 (27/40 cells, 8/10 seeds, 4/4 folds).
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems27 import heatflow_euler, holdout, oof_detector, paths, submission  # noqa: E402
from gems27.thinning import dot_thin  # noqa: E402

RUNG30_PX = 41333
H36_1_PX = 37660


def main() -> int:
    downloads_dir = ROOT / "docs" / "downloads"
    template_path = paths.TEMPLATE
    labels_path = paths.LABELS

    with rasterio.open(template_path) as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(labels_path) as ds:
        lbl = ds.read(1)
        catalogue = footprint & np.isfinite(lbl) & (lbl > 0.5)
    with rasterio.open(paths.H19_5) as ds:
        raw = ds.read(1)
    h19_5 = footprint & ~catalogue & np.isfinite(raw) & (raw > 0.5)

    rung30 = dot_thin(h19_5, 3.0)
    assert int(rung30.sum()) == RUNG30_PX, f"rung 3.0 {int(rung30.sum())} != {RUNG30_PX}"
    blind_r1 = distance_transform_edt(~catalogue) <= 1.0
    h36_1 = rung30 & ~blind_r1
    assert int(h36_1.sum()) == H36_1_PX, f"H36-1 emission {int(h36_1.sum())} != {H36_1_PX}"

    fields = heatflow_euler.build_corroboration_fields(
        footprint,
        hf_json_path=paths.SB_HEAT_FLOW_JSON,
        euler_csv_path=paths.EULER_CLUSTERS_CSV,
        lidar_path=paths.LIDAR,
    )
    prob_full = oof_detector.fit_predict_full_probabilities(footprint, catalogue)
    ridge_full = (oof_detector.ridge_nms(prob_full, footprint, sigma=1.0) | h19_5) & footprint
    fold = holdout.make_quadrant_folds(footprint)

    added_full = np.zeros_like(footprint, dtype=bool)
    per_quad_added = {}
    for f in range(4):
        fm = fold == f
        sl = holdout.crop(None, fm)
        active = fm[sl] & ~catalogue[sl]
        sel = heatflow_euler.select_corroborated_ridge_dots(
            prob_full[sl],
            ridge_full[sl],
            active,
            h36_1[sl],
            catalogue[sl],
            fields["joint_mask"][sl],
            score_mult=fields["score_mult"][sl],
            k_cap=heatflow_euler.K_CAP_PER_CELL,
            min_dist_base=heatflow_euler.MIN_DIST_BASE_PX,
            min_dist_known=heatflow_euler.MIN_DIST_KNOWN_PX,
            thin_d=heatflow_euler.THIN_D_PX,
            rng_seed=50_000 + f,
        )
        added_full[sl] |= sel["added"]
        per_quad_added[holdout.FOLD_NAMES[f]] = int(sel["n_added"])

    # Enforce global 2.8 px spacing across quadrant boundaries as well
    added_global = dot_thin(added_full, heatflow_euler.THIN_D_PX) & footprint & ~catalogue & ~h36_1
    d_h36 = distance_transform_edt(~h36_1)
    d_cat = distance_transform_edt(~catalogue)
    added_global = added_global & (d_h36 >= 2.8) & (d_cat >= 3.0)

    pred_h38_1 = h36_1 | added_global
    n_added = int(added_global.sum())
    n_total = int(pred_h38_1.sum())
    assert n_total == H36_1_PX + n_added

    pred_clean = np.where(footprint & ~catalogue & pred_h38_1, np.float32(1.0), np.float32(0.0))
    cid = submission.scored_content_id(pred_clean, footprint, catalogue)
    nan_name = submission.make_filename("gems28", "h38-1-hf-euler-r30-r1", "20261003", cid, "nan")
    all_name = submission.make_filename(
        "gems28", "h38-1-hf-euler-r30-r1", "20261003", cid, "allfinite"
    )
    nan_path = downloads_dir / nan_name
    all_path = downloads_dir / all_name
    submission.write_geotiff(pred_clean, template_path, nan_path, outside="nan")
    submission.write_geotiff(pred_clean, template_path, all_path, outside="zero")
    zip_path = submission.zip_single(nan_path)

    v_nan = submission.verify_geotiff(nan_path, template_path)
    v_all = submission.verify_geotiff(all_path, template_path)
    if not (v_nan["hard_checks_passed"] and v_all["hard_checks_passed"]):
        raise RuntimeError(
            f"hard verification failed: {v_nan['hard_failures']} / {v_all['hard_failures']}"
        )

    note_summary = (
        "H36-1+H38-1 hf_resid+SI0 Euler ridge: LOSFO +0.00075 (16/20, c/d 0.0699, 265-269), "
        "OOF +0.00054 (8/10, 4/4, 270-279)"
    )
    note = submission.make_note(
        "H38-1 hf+euler+r3.0",
        note_summary,
        cid,
        family="28GEMSDOE",
        status="UNSCORED, not slot-approved",
    )
    if note_summary not in note:
        raise RuntimeError(f"note summary truncated: {note!r}")
    note_file = f"note-gemsdoe28-h38-1-hf-euler-r30-r1-{cid}.txt"
    (downloads_dir / note_file).write_text(note + "\n", encoding="utf-8")

    manifest_path = downloads_dir / "manifest.json"
    man = json.loads(manifest_path.read_text(encoding="utf-8"))

    # Update primary (H36-1) with its now-completed LOSFO far-field verification (seeds 265-269)
    primary = dict(man["primary"])
    primary["far_field"] = {
        "evidence": "evidence/losfo_session14_h36_1_and_h38.json",
        "preregistration": "knowledge/38_preregistration_H36_1_and_H38_farfield.md",
        "seeds": [265, 266, 267, 268, 269],
        "F1_rung30_vs_matched_random_dti": 0.002072843520463665,
        "F1_cells_improved": "17/20",
        "F1_seeds_improved": "5/5",
        "F2_e_far_rung30": 0.025293452114204116,
        "F2_passes_tau_live": True,
        "F3_rung30_blind_r1_vs_base_dti": 0.001712582065785942,
        "F3_cells_improved": "16/20",
        "F3_seeds_improved": "5/5",
        "F3_e_far_rung30_blind_r1": 0.013587074587158542,
        "F4_h27_4_blind_r1_vs_base_dti": 0.0022486716567998973,
        "F4_tp_removed": 0.0,
        "verdict": "F1-F4 ALL PASS - H36-1 spacing re-pack and blind_r1 flank prune both transfer to far-field truth on seeds 265-269",
    }
    primary["note_far_field"] = (
        "FAR-FIELD VERIFIED 2026-10-03 (LOSFO seeds 265-269, knowledge/38 & knowledge/39): "
        "passes all four frozen criteria (F1 rung30 vs matched-N random drop +0.002073, 17/20 cells, 5/5 seeds; "
        "F2 e_far = 0.02529 < tau_live 0.054852; F3 rung30_blind_r1 vs d=2.8 base +0.001713, 16/20 cells, "
        "5/5 seeds, e_far = 0.01359; F4 blind_r1 loses 0.00 TP across 20/20 cells)."
    )

    h38_entry = {
        "slug": "h38-1-hf-euler-r30-r1",
        "hypothesis": (
            "H38-1: H36-1 rung-3.0 + blind-r1 base augmented with multi-physics sub-threshold 1-px "
            "ridge lineaments corroborated within 1 km by DeAngelo et al. (2022) conductive heat-flow "
            "residuals (hf_resid >= 50 mW/m^2) and/or within 300 m by Reid et al. (1990) shallow "
            "depth-coherent SI=0 Euler contact clusters"
        ),
        "content_id": cid,
        "nan": nan_name,
        "allfinite": all_name,
        "zip": zip_path.name,
        "sha256_nan": v_nan["sha256"],
        "sha256_allfinite": v_all["sha256"],
        "sha256_zip": submission.sha256_file(zip_path),
        "bytes_nan": v_nan["bytes"],
        "bytes_allfinite": v_all["bytes"],
        "bytes_zip": zip_path.stat().st_size,
        "emitted_px": n_total,
        "added_px_over_h36_1": n_added,
        "per_quadrant_added_px": per_quad_added,
        "format_verified": True,
        "status": (
            "UNSCORED; passed ALL FOUR frozen LOSFO far-field criteria (C1-C4) on fresh seeds 265-269 "
            "(+0.000792 on d=2.8 base at 0.07724 credit/dot, 17/20 cells, 4/5 seeds; +0.000747 on "
            "H36-1 rung30_blind_r1 at 0.06993 credit/dot > tau_live 0.054852, 16/20 cells, 4/5 seeds, "
            "4/4 folds, +0.002460 over d=2.8 base) AND passed the 10-seed interleaved spatial-CV "
            "holdout on fresh seeds 270-279 (+0.000656 on d=2.8 base, 27/40 cells, 9/10 seeds, 4/4 "
            f"folds; +0.000543 over H36-1, 27/40 cells, 8/10 seeds, 4/4 folds). Retained at secondary "
            f"beside H36-1 because the {n_added} added dots come from the 32-band detector ridge rather than "
            "the pure H19-5 surface."
        ),
        "note": note,
        "note_file": note_file,
        "holdout_mean_gain": 0.0031422494118066428,
        "holdout_mean_gain_vs_h36_1": 0.0005429581100109074,
        "holdout_folds_improved": "4/4",
        "holdout_seeds_improved": "8/10",
        "holdout_evidence": "evidence/h38_1_interleaved_holdout.json",
        "holdout_preregistration": "knowledge/38_preregistration_H36_1_and_H38_farfield.md",
        "holdout_seeds": "270-279",
        "far_field": {
            "evidence": "evidence/losfo_session14_h36_1_and_h38.json",
            "seeds": [265, 266, 267, 268, 269],
            "mean_delta_dti_on_base": 0.000791809196456296,
            "mean_delta_dti_on_r30_r1": 0.0007474376185384414,
            "mean_delta_dti_total_vs_d28": 0.0024600196843243834,
            "credit_per_added_dot_on_base": 0.07724129932637987,
            "credit_per_added_dot_on_r30_r1": 0.06992977854336586,
            "cells_improved_on_base": "17/20",
            "cells_improved_on_r30_r1": "16/20",
            "seeds_improved": "4/5",
            "verdict": "C1-C4 ALL PASS - first addition arm to clear tau_live (0.054852) and both sub-ridge and random controls on LOSFO far-field truth",
        },
        "base_reference_id": "b531dae0a36f",
        "base_reference_live_score": 0.26,
    }

    # Preserve H37-1 if it was in secondary so verify_downloads.py continues auditing it
    old_secondary = man.get("secondary", {})
    if old_secondary.get("slug") == "h37-1-coverprob-h19-5-r1":
        man["h37_1_falsified"] = old_secondary

    man["primary"] = primary
    man["secondary"] = h38_entry
    man["generated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    man["status"] = (
        "Session 14 (2026-10-03): H36-1 (primary, b531dae0a36f, 37,660 px) is now verified on BOTH "
        "interleaved spatial CV (seeds 240-249, +0.002599) and LOSFO far-field truth (seeds 265-269, "
        "+0.001713, F1-F4 ALL PASS, e_far = 0.01359 < tau_live 0.054852). H38-1 (secondary, "
        f"{cid}, {n_total:,} px) adds {n_added} multi-physics corroborated lineament dots "
        "(DeAngelo et al. 2022 conductive heat-flow residual hf_resid >= 50 mW/m^2 + Reid et al. 1990 "
        "shallow SI=0 Euler contact cluster) and passed both LOSFO far-field C1-C4 (+0.000747 over "
        "H36-1, 0.06993 credit/dot) and interleaved spatial CV (seeds 270-279, +0.000543 over H36-1). "
        "All files UNSCORED / not slot-approved."
    )
    manifest_path.write_text(json.dumps(man, indent=2) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "secondary_h38_1": nan_name,
                "content_id": cid,
                "emitted_px": n_total,
                "added_px": n_added,
                "sha256_nan": v_nan["sha256"],
                "note_chars": len(note),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
