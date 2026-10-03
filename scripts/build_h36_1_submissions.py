#!/usr/bin/env python3
"""Build the H36-1 submission bundle: rung-3.0 re-pack of the 0.2600 surface + the H27-4 blind prune.

Protocol: ``knowledge/26_preregistration_H36-1.md``. Gate result: ``evidence/h36_1_holdout.json``
(fresh seeds 240-249; winner ``rung30_blind_r1``, +0.002599 mean OOF delta DTI, 10/10 seeds, 4/4
folds, promotion margin +0.000884 over the incumbent, anti-budget control at -0.001657, anti-selective
control at +0.001352).

The emission is built from the **real** H19-5 surface exactly as the gate's proxy was: the holdout
measures the *rule* on the OOF detector, the artifact applies the *rule* to the scored surface. Both
prongs are asserted against the counts measured on the full footprint before this file was written:

    dot_thin(h19_5_surface, 3.0)                    -> 41,333 px   (rung 3.0; H34's predicted optimum)
    dot_thin(h19_5_surface, 3.0) & ~(d_cat <= 1.0)  -> 37,660 px   (H36-1 winner)

Writes the GeoTIFF pair, the zip, the note, and re-slots ``docs/downloads/manifest.json``.
Reads no hidden truth. Never contacts drivendata.org.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from gems27 import paths, submission  # noqa: E402
from gems27.thinning import dot_thin  # noqa: E402

RUNG30_PX = 41333
H36_1_PX = 37660
# The gate measured the blind prune at 0.0098447 credit per unit of FP removed (seeds 240-249).
MEASURED_PRUNE_EFFICIENCY = 0.009844673368221007
N_REMOVED_FULL_FOOTPRINT = RUNG30_PX - H36_1_PX


def main() -> int:
    downloads_dir = ROOT / "docs" / "downloads"
    template_path = paths.DATA / "sample_submission.tif"
    labels_path = paths.DATA / "labels.tif"
    d28_path = paths.DATA / "dotted_h19_5_d2_8_nan.tif"

    with rasterio.open(template_path) as ds:
        footprint = np.isfinite(ds.read(1))
    with rasterio.open(labels_path) as ds:
        lbl = ds.read(1)
        catalogue = footprint & np.isfinite(lbl) & (lbl > 0.5)
    with rasterio.open(paths.H19_5) as ds:
        raw = ds.read(1)
    h19_5 = footprint & ~catalogue & np.isfinite(raw) & (raw > 0.5)
    with rasterio.open(d28_path) as ds:
        d28 = footprint & ~catalogue & (np.nan_to_num(ds.read(1), nan=0.0) > 0.5)

    assert int(h19_5.sum()) == 121131, f"h19_5 surface {int(h19_5.sum())} != 121,131"
    assert int(d28.sum()) == 44090, f"published d2.8 {int(d28.sum())} != 44,090"
    # Independent re-verification of the anchor: the shipped file is exactly dot_thin(surface, 2.8).
    assert np.array_equal(d28, dot_thin(h19_5, 2.8)), "published d2.8 is not dot_thin(surface, 2.8)"

    rung30 = dot_thin(h19_5, 3.0)
    assert int(rung30.sum()) == RUNG30_PX, f"rung 3.0 {int(rung30.sum())} != {RUNG30_PX}"
    blind_r1 = distance_transform_edt(~catalogue) <= 1.0
    pred = rung30 & ~blind_r1
    assert int(pred.sum()) == H36_1_PX, f"H36-1 emission {int(pred.sum())} != {H36_1_PX}"

    pred_clean = np.where(footprint & ~catalogue & pred, np.float32(1.0), np.float32(0.0))
    cid = submission.scored_content_id(pred_clean, footprint, catalogue)
    nan_name = submission.make_filename("gems28", "h36-1-rung30-blind-r1", "20261003", cid, "nan")
    all_name = submission.make_filename("gems28", "h36-1-rung30-blind-r1", "20261003", cid, "allfinite")
    nan_path = downloads_dir / nan_name
    all_path = downloads_dir / all_name
    submission.write_geotiff(pred_clean, template_path, nan_path, outside="nan")
    submission.write_geotiff(pred_clean, template_path, all_path, outside="zero")
    zip_path = submission.zip_single(nan_path)

    v_nan = submission.verify_geotiff(nan_path, template_path)
    v_all = submission.verify_geotiff(all_path, template_path)
    if not (v_nan["hard_checks_passed"] and v_all["hard_checks_passed"]):
        raise RuntimeError(f"hard verification failed: {v_nan['hard_failures']} / {v_all['hard_failures']}")

    # `make_note` prepends the family itself, so the hypothesis label must NOT repeat it (the first
    # H36-1 build shipped "28GEMSDOE 28GEMSDOE ..."). It also truncates the summary silently to fit
    # 200 characters, which cut the first build's note off mid-word ("...random d |"). Both are
    # guarded here: the summary below was measured to fit, and the assertion fails the build rather
    # than shipping a note whose text cannot be read.
    note_summary = (
        "OOF dDTI +0.00260, 10/10 seeds, 4/4 folds (seeds 240-249); "
        "re-pack beats matched-N random drop by +0.00261; no T-v2"
    )
    note = submission.make_note(
        "H36-1 rung3.0+r1",
        note_summary,
        cid,
        family="28GEMSDOE",
        status="UNSCORED, not slot-approved",
    )
    if note_summary not in note:
        raise RuntimeError(
            f"note summary was truncated by make_note ({len(note_summary)} chars do not fit in "
            f"200); shorten it rather than shipping a partial sentence: {note!r}"
        )
    note_file = f"note-gemsdoe28-h36-1-rung30-blind-r1-{cid}.txt"
    (downloads_dir / note_file).write_text(note + "\n", encoding="utf-8")

    primary_entry = {
        "slug": "h36-1-rung30-blind-r1",
        "hypothesis": (
            "H36-1: re-pack the H19-5 surface from packing rung 2.828 to rung 3.0 (a 41,333-px "
            "re-layout, not a thinning) and apply the H27-4 blind 1-px catalogue-flank prune"
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
        "emitted_px": int(pred_clean[footprint].sum()),
        "format_verified": True,
        "status": (
            "UNSCORED; won the frozen H36-1 gate on fresh seeds 240-249: +0.002599 mean OOF delta DTI, "
            "10/10 seeds, 4/4 folds, promotion margin +0.000884 over the incumbent, removal efficiency "
            "0.00984 < tau_live 0.054852. Anti-budget control (random drop to the same N) scored "
            "-0.001657; anti-selective control +0.001352."
        ),
        "note": note,
        "note_file": note_file,
        "holdout_mean_gain": 0.0025992913017957354,
        "holdout_folds_improved": "4/4",
        "holdout_seeds_improved": "10/10",
        "holdout_evidence": "evidence/h36_1_holdout.json",
        "holdout_preregistration": "knowledge/26_preregistration_H36-1.md",
        "holdout_seeds": "240-249",
        "base_reference_id": "e56ea318af89",
        "base_reference_live_score": 0.26,
        "rung30_px_before_prune": RUNG30_PX,
        "prune_px_removed": N_REMOVED_FULL_FOOTPRINT,
        "measured_prune_efficiency": MEASURED_PRUNE_EFFICIENCY,
        "projection_note": (
            "Live-anchored hybrid projection 0.2717-0.2727 (H34 ladder for the re-pack, +0.00283; the "
            "gate's measured prune efficiency for the flank prune, +0.0089-0.0098). A MODEL, not a "
            "score; the 0.2600 anchor is owner-reported."
        ),
    }

    manifest_path = downloads_dir / "manifest.json"
    old = json.loads(manifest_path.read_text())

    if old.get("primary", {}).get("content_id") == cid:
        # Idempotent re-run. Without this guard the builder would demote its OWN output into the
        # secondary slot (it re-slots by reading the manifest it just wrote), duplicating the
        # primary under a second rank. Refresh only the primary's record and leave the rest alone.
        refreshed = dict(old)
        refreshed["primary"] = primary_entry
        refreshed["generated_utc"] = "2026-10-03"
        old_primary_before = old["primary"]
        if old_primary_before.get("note") != note:
            refreshed["primary_note_revision"] = {
                "previous_note": old_primary_before.get("note"),
                "reason": ("first build shipped a duplicated family prefix and a mid-word truncation; "
                           "make_note silently truncates, so the builder now asserts the summary fits"),
                "previous_sha256_nan": old_primary_before.get("sha256_nan"),
            }
        manifest_path.write_text(json.dumps(refreshed, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({
            "primary": nan_name, "content_id": cid, "emitted_px": primary_entry["emitted_px"],
            "sha256_nan": v_nan["sha256"], "bytes_nan": v_nan["bytes"], "rerun": "idempotent",
            "note_chars": len(note),
        }, indent=2))
        return 0

    # Re-slot. The previous primary is a superseded, still-validated artifact; nothing is deleted.
    secondary = old["primary"]
    secondary["status"] = (
        "UNSCORED; previous one-click primary (won the H35-6 fresh-seed adjudication, seeds 235-239). "
        "Demoted by H36-1 on a fresh decade: +0.001715 vs +0.002599 on seeds 240-249. Still a validated, "
        "fully audited file and the conservative choice if the re-pack is judged too aggressive."
    )
    tertiary = old["secondary"]
    quaternary = old["tertiary"]
    quaternary["status"] = (
        "UNSCORED; the original preregistered H32-1 file. Dominated on every published statistic by the "
        "files above; retained because it is the only variant that protects fault tips and shallow Euler "
        "depth clusters."
    )

    new_manifest = {
        "schema": 1,
        "generated_utc": "2026-10-03",
        "status": "UNSCORED GEMSDOE28 research/reference artifacts; no GEMSDOE28 upload or organizer score is recorded",
        "provenance_warning": (
            "All inputs and historical model artifacts are owner-repository mirrors; local SHA-256 "
            "integrity does not prove organizer authenticity or score association."
        ),
        "manual_policy": (
            "No upload, portal call, scheduled check, scraping, API monitoring or other automated "
            "DrivenData access. All site links are downloads/manual-review links only."
        ),
        "primary": primary_entry,
        "secondary": secondary,
        "tertiary": tertiary,
        "quaternary": quaternary,
        "quinary_probe": old["quinary_probe"],
        "research_candidate": old["research_candidate"],
        "promotion_rule": (
            "The one-click primary is the file that won a frozen fresh-seed gate whose criteria were "
            "written to knowledge/ before the seeds were spent. H36-1: knowledge/26_preregistration_H36-1.md, "
            "seeds 240-249. H35-6 (the previous promotion) remains the record for the superseded slot."
        ),
    }
    manifest_path.write_text(json.dumps(new_manifest, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "primary": nan_name, "content_id": cid, "emitted_px": primary_entry["emitted_px"],
        "sha256_nan": v_nan["sha256"], "bytes_nan": v_nan["bytes"],
        "checks_nan": len(v_nan.get("checks", [])),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
