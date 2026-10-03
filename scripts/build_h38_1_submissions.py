#!/usr/bin/env python3
"""Build the H38-1 artifact bundle: the radiometric-augmented detector's emission.

Two files, both at the shipped rung-3.0 budget (41,333 px) with the unchanged H27-4 blind 1-px
catalogue-flank prune:

  h38-1-rad-cover-h19-5-r1   coverage packing of the **shipped H19-5 surface** ordered by the D1
                             (radiometric-augmented) full-fit detector probability. Byte-for-byte the
                             H37-1 construction (same pool, same budget, same prune) with the weight
                             field built from the new information - this is the minimal, most
                             lineage-consistent change against the current one-click primary.
  h38-1-rad-ridge-cover-r1   the same rule over the **D1 detector's own ridge field**, i.e. the
                             construction the H38-1 gate and the LOSFO far-field test measure directly.

Everything is written to ``docs/downloads/`` with the repository's content-addressed naming, the
``nan`` and ``allfinite`` outside-footprint conventions, a zip-of-one, a <= 200-character note and a
hard format verification. ``docs/downloads/manifest.json`` is re-slotted only if the operator passes
``--promote``; otherwise the new files are recorded in ``research_candidate``/``tertiary`` style slots.

Usage (the promote switch is a deliberate, separate act):

    GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/build_h38_1_submissions.py
    GEMS_DATA_DIR=$PWD/data .venv/bin/python scripts/build_h38_1_submissions.py --promote
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
from gems27 import grid, oof_detector, packing, paths, submission  # noqa: E402
from run_h38_1_holdout import RAD_EXTRA_BANDS, load_extras  # noqa: E402

RUNG30_PX = 41333
DATE = "20261003"
SLUG_H19 = "h38-1-rad-cover-h19-5-r1"
SLUG_RIDGE = "h38-1-rad-ridge-cover-r1"
EXPECTED_H19_PX = 121131


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--promote", action="store_true",
                    help="re-slot docs/downloads/manifest.json so the H19-5-pool file becomes primary")
    args = ap.parse_args()

    t0 = time.time()
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    catalogue = labels.astype(bool) & foot
    extras, extra_diag = load_extras(foot)
    print(f"extras {extra_diag['names']} finite {extra_diag['finite_fraction_inside_footprint']:.5f}",
          flush=True)

    prob0 = oof_detector.fit_predict_full_probabilities(foot, labels)
    ridge0 = oof_detector.ridge_nms(prob0, foot, sigma=1.0)
    prob1 = oof_detector.fit_predict_full_probabilities(foot, labels, extra=extras)
    ridge1 = oof_detector.ridge_nms(prob1, foot, sigma=1.0)
    print(f"full-fit ridges: D0 {int(ridge0.sum()):,}  D1 {int(ridge1.sum()):,}", flush=True)

    weight1 = np.where(foot & ~catalogue, prob1, 0.0).astype(np.float32)
    with rasterio.open(paths.H19_5) as src:
        raw = src.read(1)
    pool_h19 = foot & ~catalogue & np.isfinite(raw) & (raw > 0.5)
    if int(pool_h19.sum()) != EXPECTED_H19_PX:
        raise SystemExit(f"H19-5 surface {int(pool_h19.sum())} != {EXPECTED_H19_PX}")
    pool_ridge = ridge1 & foot & ~catalogue

    blind_r1 = distance_transform_edt(~catalogue) <= 1.0
    packed_h19 = packing.coverage_greedy(pool_h19, weight1, RUNG30_PX)
    packed_ridge = packing.coverage_greedy(pool_ridge, weight1, RUNG30_PX)
    for name, packed in ((SLUG_H19, packed_h19), (SLUG_RIDGE, packed_ridge)):
        if int(packed.sum()) != RUNG30_PX:
            raise SystemExit(f"{name}: packer emitted {int(packed.sum())} != {RUNG30_PX}")

    downloads_dir = paths.DOCS / "downloads"
    outputs: list[dict] = []
    for slug, packed, hypothesis, note_hyp, note_summary in (
        (SLUG_H19, packed_h19,
         ("H38-1: coverage packing of the shipped H19-5 surface ordered by the full-fit detector "
          "probability field of the 38-band (32 + GeoDAWN K, Th, U, Th/K, U/K, U/Th) matrix, at the "
          "rung-3.0 budget (41,333 px), with the unchanged H27-4 blind 1-px catalogue-flank prune"),
         "H38-1 rad-cover H19-5",
         "OOF dDTI +0.00287 vs same-rule D0 detector (9/10 seeds, 4/4 folds, seeds 280-289); added "
         "GeoDAWN radiometrics K,Th,U,ThK,UK,UTh; no T-v2"),
        (SLUG_RIDGE, packed_ridge,
         ("H38-1: coverage packing of the radiometric-augmented detector's own 1-px ridge field at the "
          "rung-3.0 budget (41,333 px) with the unchanged H27-4 blind 1-px catalogue-flank prune - the "
          "construction the frozen gate and the LOSFO transfer test measure"),
         "H38-1 rad-ridge-cover",
         "Same rule/detector as the gate primary (dDTI +0.00287, 9/10 seeds, 4/4 folds, 280-289); "
         "ridge-field emission, not the H19-5 lineage; no T-v2"),
    ):
        pred = np.where(packed & ~blind_r1, True, False)
        pred_clean = np.where(foot & ~catalogue & pred, np.float32(1.0), np.float32(0.0))
        cid = submission.scored_content_id(pred_clean, foot, catalogue)
        nan_name = submission.make_filename("gems28", slug, DATE, cid, "nan")
        all_name = submission.make_filename("gems28", slug, DATE, cid, "allfinite")
        nan_path, all_path = downloads_dir / nan_name, downloads_dir / all_name
        submission.write_geotiff(pred_clean, paths.TEMPLATE, nan_path, outside="nan")
        submission.write_geotiff(pred_clean, paths.TEMPLATE, all_path, outside="zero")
        zip_path = submission.zip_single(nan_path)
        v_nan = submission.verify_geotiff(nan_path, paths.TEMPLATE)
        v_all = submission.verify_geotiff(all_path, paths.TEMPLATE)
        if not (v_nan["hard_checks_passed"] and v_all["hard_checks_passed"]):
            raise RuntimeError(f"hard verification failed for {slug}: "
                               f"{v_nan['hard_failures']} / {v_all['hard_failures']}")
        note = submission.make_note(note_hyp, note_summary, cid, family="28GEMSDOE",
                                    status="UNSCORED, not slot-approved")
        if note_summary not in note:
            raise RuntimeError(f"note summary truncated by make_note: {note!r}")
        note_file = f"note-gemsdoe28-{slug}-{cid}.txt"
        (downloads_dir / note_file).write_text(note + "\n", encoding="utf-8")
        emitted = int(pred_clean[foot].sum())
        outputs.append({
            "slug": slug, "hypothesis": hypothesis, "content_id": cid,
            "nan": nan_name, "allfinite": all_name, "zip": zip_path.name,
            "sha256_nan": v_nan["sha256"], "sha256_allfinite": v_all["sha256"],
            "sha256_zip": submission.sha256_file(zip_path),
            "bytes_nan": v_nan["bytes"], "bytes_allfinite": v_all["bytes"],
            "bytes_zip": zip_path.stat().st_size, "emitted_px": emitted,
            "pre_prune_px": RUNG30_PX, "prune_px_removed": RUNG30_PX - emitted,
            "format_verified": True, "note": note, "note_file": note_file,
            "candidate_pool": ("H19-5 surface (121,131 px)" if slug == SLUG_H19
                               else f"D1 full-fit ridge field ({int(pool_ridge.sum()):,} px)"),
            "base_reference_id": "e56ea318af89",
            "base_reference_live_score": 0.26,
            "holdout_evidence": "evidence/h38_1_holdout.json",
            "holdout_preregistration": "knowledge/38_preregistration_H38-1.md",
            "holdout_seeds": "280-289",
            "holdout_mean_gain": 0.002869,
            "holdout_mean_gain_vs_incumbent": 0.002869,
            "holdout_seeds_improved": "9/10",
            "holdout_folds_improved": "4/4",
            "far_field_evidence": "evidence/losfo_rad_farfield.json",
            "far_field_preregistration": "knowledge/40_preregistration_H38-1_farfield.md",
        })
        print(f"wrote {nan_name}: {emitted:,} px, sha256 {v_nan['sha256'][:16]}…", flush=True)

    evidence = {
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "hypothesis": "H38-1 artifact build (radiometric-augmented detector)",
        "preregistration": "knowledge/38_preregistration_H38-1.md",
        "gate": "evidence/h38_1_holdout.json",
        "far_field": "evidence/losfo_rad_farfield.json",
        "extra_bands": RAD_EXTRA_BANDS,
        "extra_diag": extra_diag,
        "rung30_px": RUNG30_PX,
        "pool_h19_5_px": int(pool_h19.sum()),
        "pool_ridge_px": int(pool_ridge.sum()),
        "ridge_px_D0_fullfit": int(ridge0.sum()),
        "ridge_px_D1_fullfit": int(ridge1.sum()),
        "blind_r1_removed": {o["slug"]: o["prune_px_removed"] for o in outputs},
        "full_fit_seed": 2026,
        "code_sha256": {
            "packing": hashlib.sha256((REPO / "src" / "gems27" / "packing.py").read_bytes()).hexdigest(),
            "oof_detector": hashlib.sha256(
                (REPO / "src" / "gems27" / "oof_detector.py").read_bytes()).hexdigest(),
            "submission": hashlib.sha256(
                (REPO / "src" / "gems27" / "submission.py").read_bytes()).hexdigest(),
            "builder": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        },
        "outputs": outputs,
        "seconds": time.time() - t0,
        "honesty": (
            "The two files differ from each other ONLY in the candidate pool (H19-5 surface vs the "
            "detector's own ridges); pool, budget, prune, detector and weight field are identical. "
            "Neither file's exact global packing has been far-field measured: the LOSFO test measures "
            "the information at matched count on detector ridges, and knowledge/39 shows that "
            "pool-restricted coverage packing is far-field neutral. The interleaved +0.002869 is NOT a "
            "live projection (knowledge/39: no live range is quoted for packing arms)."
        ),
    }
    submission.dump_json(evidence, paths.EVIDENCE / "h38_1_artifact.json")
    print(f"wrote evidence/h38_1_artifact.json ({len(outputs)} files)")

    if args.promote:
        manifest_path = downloads_dir / "manifest.json"
        old = json.loads(manifest_path.read_text())
        primary, ridge_file = outputs[0], outputs[1]
        primary = dict(primary, status=(
            "UNSCORED one-click primary from 2026-10-03: won the frozen H38-1 gate on fresh seeds "
            "280-289 (G1-G5 all pass: +0.002869 mean ΔDTI vs the same-rule D0 detector, 9/10 seeds, "
            "4/4 folds, content control 0.054841 below it) and passed the frozen LOSFO transfer test "
            "(knowledge/40, seeds 220-224). Same pool, budget and prune as H37-1; only the weight field "
            "changed, and that field now carries the GeoDAWN radiometric channels the detector never "
            "saw before (the competition's band 6 'tc' is rank-identical to GeoDAWN radiometric total "
            "count and was excluded as mislabelled). Not slot-approved; no live score."))
        ridge_file = dict(ridge_file, status=(
            "UNSCORED research companion: the construction the H38-1 gate and the LOSFO transfer test "
            "measure directly (coverage packing of the radiometric-augmented detector's own ridge "
            "field). Kept because it is the only H38-1 file whose exact emission family has a "
            "far-field number; not slot-approved."))
        new_manifest = dict(old)
        new_manifest["generated_utc"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        new_manifest["status"] = (
            "Slot order revised 2026-10-03 by the frozen H38-1 gate (knowledge/38, seeds 280-289) and "
            "its LOSFO transfer test (knowledge/40, seeds 220-224): the primary is the H19-5-surface "
            "packing re-ordered by the radiometric-augmented detector. H36-1 and H37-1 stay audited and "
            "listed; every older slot keeps its status.")
        new_manifest["primary"] = primary
        new_manifest["secondary"] = dict(old["primary"], status=(
            "UNSCORED; previous one-click primary (H36-1, won its own frozen gate on seeds 240-249). "
            "Demoted by the H38-1 radiometric gate on a fresh decade. Still fully audited and the most "
            "conservative lineage (no detector weight in the packing at all)."))
        new_manifest["tertiary"] = dict(old["secondary"], status=(
            "UNSCORED; H37-1 - demoted under the H38-1 gate's predecessor comparison (its own far-field "
            "test failed, knowledge/33). Still the reference construction for the packing rule, and the "
            "file whose build the H38-1 primary clones except for the weight field."))
        new_manifest["quaternary"] = old["tertiary"]
        new_manifest["quinary_probe"] = old["quaternary"]
        new_manifest["conservative_alternative"] = old.get("conservative_alternative")
        new_manifest["research_candidate"] = ridge_file
        new_manifest["historical_reference"] = old.get("quinary_probe")
        new_manifest["promotion_rule"] = (
            "The one-click primary is the file that won a frozen fresh-seed gate whose criteria were "
            "written to knowledge/ before the seeds were spent AND (since knowledge/32-33) that did not "
            "fail the LASFO far-field transfer test. H38-1: knowledge/38_preregistration_H38-1.md, "
            "seeds 280-289; transfer: knowledge/40_preregistration_H38-1_farfield.md, seeds 220-224.")
        manifest_path.write_text(json.dumps(new_manifest, indent=2) + "\n", encoding="utf-8")
        print("re-slotted docs/downloads/manifest.json")
    else:
        print("manifest NOT re-slotted (pass --promote to re-slot)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
