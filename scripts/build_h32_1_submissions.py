#!/usr/bin/env python3
"""Deterministically build and verify GEMSDOE28 H32-1 submission GeoTIFFs on the d=2.8 (0.2600) base.

Builds three T-v2-free d=2.8 candidates:
1. primary (h32-1-tip-euler-dejitter-d2-8): post-thinning H32-1 mid-segment flank-shadow de-jittering
   on d=2.8 (e56ea318af89, 0.2600 live), protecting tip-continuation (d_end <= 3.0 px) and shallow
   Euler N=0 depth-coherent clusters (d_euler <= 3.0 px). Emits 41,656 px.
2. secondary (h32-1-prethin-tip-euler-d2-8): pre-thinning H32-1 mid-segment flank-shadow de-jittering
   before dot_thin(..., min_dist=2.8), allowing blocked interior ridges to re-emit. Emits 42,294 px.
3. tertiary (h27-4-r1-solo-d2-8): pure d_cat <= 1.0 px flank-shadow prune on d=2.8 (0.2600 base)
   without the live-refuted T-v2 gap-closure dots. Emits 40,199 px.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import convolve, distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems27 import paths, submission  # noqa: E402
from gems27.thinning import dot_thin  # noqa: E402


def load_euler_halo(shape: tuple[int, int], radius_px: float = 3.0) -> np.ndarray:
    mask = np.zeros(shape, dtype=bool)
    csv_path = ROOT / "evidence" / "h31_1_euler_clusters.csv"
    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            r = int(round(float(row["row"])))
            c = int(round(float(row["col"])))
            if 0 <= r < shape[0] and 0 <= c < shape[1]:
                mask[r, c] = True
    return distance_transform_edt(~mask) <= radius_px


def build_flank_mid_mask(known: np.ndarray, eu_halo: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Return (flank_mid, tip_or_euler) partition of the d_known <= 1.0 (100 m) ring."""
    d_kn = distance_transform_edt(~known)
    kn_deg = convolve(known.astype(int), np.ones((3, 3), int), mode="constant") - 1
    end_mask = known & (kn_deg <= 1)
    d_end = distance_transform_edt(~end_mask)
    kn_nbrs = convolve(known.astype(int), np.ones((3, 3), int), mode="constant")
    r1 = (d_kn > 0.0) & (d_kn <= 1.0)
    flank_mid = r1 & (d_end > 3.0) & (kn_nbrs >= 2) & ~eu_halo
    tip_or_euler = r1 & ~flank_mid
    return flank_mid, tip_or_euler


def write_candidate_bundle(
    pred: np.ndarray,
    footprint: np.ndarray,
    catalogue: np.ndarray,
    template: Path,
    out_dir: Path,
    slug: str,
    hypothesis_label: str,
    note_summary: str,
    note_prefix: str,
    status_str: str,
    extra_fields: dict,
) -> dict:
    pred_clean = np.where(footprint & ~catalogue & (pred > 0), np.float32(1.0), np.float32(0.0))
    cid = submission.scored_content_id(pred_clean, footprint, catalogue)
    nan_name = submission.make_filename("gems28", slug, "20261003", cid, "nan")
    allfinite_name = submission.make_filename("gems28", slug, "20261003", cid, "allfinite")
    nan_path = out_dir / nan_name
    allfinite_path = out_dir / allfinite_name
    submission.write_geotiff(pred_clean, template, nan_path, outside="nan")
    submission.write_geotiff(pred_clean, template, allfinite_path, outside="zero")
    zip_path = submission.zip_single(nan_path)

    v_nan = submission.verify_geotiff(nan_path, template)
    v_all = submission.verify_geotiff(allfinite_path, template)
    if not (v_nan["hard_checks_passed"] and v_all["hard_checks_passed"]):
        raise RuntimeError(f"Hard verification failed for {slug}: {v_nan['hard_failures']} / {v_all['hard_failures']}")

    note = submission.make_note(
        note_prefix,
        note_summary,
        cid,
        family="28GEMSDOE",
        status="UNSCORED, not slot-approved",
    )
    note_file = f"note-gemsdoe28-{slug}-{cid}.txt"
    (out_dir / note_file).write_text(note + "\n", encoding="utf-8")

    return {
        "slug": slug,
        "hypothesis": hypothesis_label,
        "content_id": cid,
        "nan": nan_name,
        "allfinite": allfinite_name,
        "zip": zip_path.name,
        "sha256_nan": v_nan["sha256"],
        "sha256_allfinite": v_all["sha256"],
        "sha256_zip": submission.sha256_file(zip_path),
        "bytes_nan": v_nan["bytes"],
        "bytes_allfinite": v_all["bytes"],
        "bytes_zip": zip_path.stat().st_size,
        "emitted_px": int((pred_clean[footprint] == 1.0).sum()),
        "format_verified": True,
        "status": status_str,
        "note": note,
        "note_file": note_file,
        **extra_fields,
    }


def main() -> int:
    data_dir = paths.DATA
    downloads_dir = ROOT / "docs" / "downloads"
    template_path = data_dir / "sample_submission.tif"
    labels_path = data_dir / "labels.tif"
    h19_5_path = paths.H19_5
    d28_path = data_dir / "dotted_h19_5_d2_8_nan.tif"

    with rasterio.open(template_path) as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(labels_path) as ds:
        lbl = ds.read(1)
        catalogue = footprint & np.isfinite(lbl) & (lbl > 0.5)
    with rasterio.open(h19_5_path) as ds:
        h19_5 = footprint & ~catalogue & (np.nan_to_num(ds.read(1), nan=0.0) > 0.5)
    with rasterio.open(d28_path) as ds:
        d28 = footprint & ~catalogue & (np.nan_to_num(ds.read(1), nan=0.0) > 0.5)

    assert int(d28.sum()) == 44090, f"Expected 44,090 px in d28, got {int(d28.sum())}"

    eu_halo = load_euler_halo(catalogue.shape, radius_px=3.0)
    mid_flank_shadow, _ = build_flank_mid_mask(catalogue, eu_halo)
    blind_r1 = distance_transform_edt(~catalogue) <= 1.0

    # 1. Primary: post-thinning H32-1 on d=2.8 (41,656 px)
    pred_h32_1_post = d28 & ~mid_flank_shadow
    assert int(pred_h32_1_post.sum()) == 41656

    # 2. Secondary: pre-thinning H32-1 on h19_5 before dot_thin(2.8) (42,294 px)
    pred_h32_1_pre = dot_thin((h19_5 & ~mid_flank_shadow).astype(np.float32), min_dist=2.8) > 0.5
    assert int(pred_h32_1_pre.sum()) == 42294

    # 3. Tertiary: solo H27-4 r=1 prune on d=2.8 without T-v2 (40,199 px)
    pred_h27_4_d28 = d28 & ~blind_r1
    assert int(pred_h27_4_d28.sum()) == 40199

    primary_entry = write_candidate_bundle(
        pred=pred_h32_1_post,
        footprint=footprint,
        catalogue=catalogue,
        template=template_path,
        out_dir=downloads_dir,
        slug="h32-1-tip-euler-dejitter-d2-8",
        hypothesis_label="H32-1 tip- & Euler-depth-cluster-protected mid-segment flank-shadow de-jittering on d=2.8",
        note_prefix="H32-1 d2.8 post",
        note_summary="OOF ΔDTI +0.00127 (10/10 seeds, 4/4 folds, seeds 180-189) on 0.2600 d2.8 base; no T-v2",
        status_str="UNSCORED; 4-fold spatially blocked holdout PASS (+0.001272 mean ΔDTI, 10/10 seeds, 4/4 folds on seeds 180-189); built on 0.2600 d=2.8 base without T-v2 drag",
        extra_fields={
            "holdout_mean_gain": 0.0012715910909455819,
            "holdout_folds_improved": "4/4",
            "holdout_seeds_improved": "10/10",
            "holdout_evidence": "evidence/h32_1_holdout.json",
            "base_reference_id": "e56ea318af89",
            "base_reference_live_score": 0.2600,
            "model_score_hybrid": 0.2663,
        },
    )

    secondary_entry = write_candidate_bundle(
        pred=pred_h32_1_pre,
        footprint=footprint,
        catalogue=catalogue,
        template=template_path,
        out_dir=downloads_dir,
        slug="h32-1-prethin-tip-euler-d2-8",
        hypothesis_label="H32-1 pre-thinning tip- & Euler-protected mid-segment de-jittering before dot_thin(2.8)",
        note_prefix="H32-1 d2.8 pre",
        note_summary="OOF ΔDTI +0.00140 (10/10 seeds, 4/4 folds, seeds 180-189) pre-thinning d2.8; no T-v2",
        status_str="UNSCORED; 4-fold spatially blocked holdout PASS (+0.001399 mean ΔDTI, 10/10 seeds, 4/4 folds on seeds 180-189); re-emits 638 interior ridge dots blocked by flank shadow",
        extra_fields={
            "holdout_mean_gain": 0.0013989919559766317,
            "holdout_folds_improved": "4/4",
            "holdout_seeds_improved": "10/10",
            "holdout_evidence": "evidence/h32_1_holdout.json",
            "base_reference_id": "e56ea318af89",
            "base_reference_live_score": 0.2600,
            "model_score_hybrid": 0.2669,
        },
    )

    tertiary_entry = write_candidate_bundle(
        pred=pred_h27_4_d28,
        footprint=footprint,
        catalogue=catalogue,
        template=template_path,
        out_dir=downloads_dir,
        slug="h27-4-r1-solo-d2-8",
        hypothesis_label="H27-4 solo 1-pixel (100 m) catalogue-flank prune on d=2.8 (0.2600 base, no T-v2)",
        note_prefix="H27-4 d2.8 solo",
        note_summary="OOF ΔDTI +0.00177 (10/10 seeds, 4/4 folds) 1px flank prune on 0.2600 d2.8; no T-v2",
        status_str="UNSCORED; solo H27-4 r=1 flank prune on d=2.8 (e56ea318af89, 0.2600) with live-refuted T-v2 gap closure removed",
        extra_fields={
            "holdout_mean_gain": 0.0017660520700670697,
            "holdout_folds_improved": "4/4",
            "holdout_seeds_improved": "10/10",
            "holdout_evidence": "evidence/h32_1_holdout.json",
            "base_reference_id": "e56ea318af89",
            "base_reference_live_score": 0.2600,
            "model_score_hybrid": 0.2686,
        },
    )

    manifest_path = downloads_dir / "manifest.json"
    old_manifest = json.loads(manifest_path.read_text())

    # Preserve historical references in quaternary, quinary_probe, research_candidate
    quaternary_entry = old_manifest["quaternary"]
    quinary_entry = old_manifest["tertiary"]
    quinary_entry["status"] = (
        "HISTORICAL LIVE-SCORED IN GEMSDOE27 (owner-reported 0.2449 vs 0.2477 d=1.5 base, -0.0028 DTI); "
        "retained as negative-control reference proving T-v2 gap closure is false-positive drag"
    )
    research_entry = old_manifest["primary"]
    research_entry["status"] = (
        "UNSCORED historical H28-1 + T-v2 + H27-4 reference on d=1.5; superseded as primary by H32-1 on d=2.8 "
        "after d=2.8 scored 0.2600 and T-v2 scored 0.2449 (-0.0028); not one of the four weekly slots"
    )

    new_manifest = {
        "schema": 1,
        "generated_utc": "2026-10-03",
        "status": "UNSCORED GEMSDOE28 research/reference artifacts; no GEMSDOE28 upload or organizer score is recorded",
        "provenance_warning": "All inputs and historical model artifacts are owner-repository mirrors; local SHA-256 integrity does not prove organizer authenticity or score association.",
        "manual_policy": "No upload, portal call, scheduled check, scraping, API monitoring or other automated DrivenData access. All site links are downloads/manual-review links only.",
        "primary": primary_entry,
        "secondary": secondary_entry,
        "tertiary": tertiary_entry,
        "quaternary": quaternary_entry,
        "quinary_probe": quinary_entry,
        "research_candidate": research_entry,
    }
    manifest_path.write_text(json.dumps(new_manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "primary": primary_entry["nan"],
        "secondary": secondary_entry["nan"],
        "tertiary": tertiary_entry["nan"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
