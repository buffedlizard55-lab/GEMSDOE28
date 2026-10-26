#!/usr/bin/env python3
"""S22 archive-coverage fix: register previously unregistered download TIFFs in the manifest.

Implements Session 21 next-step #1 (knowledge/61_s21_validation_review.md).
MERGE NOTE (S22C): a parallel S22-AUDIT session independently registered the same files on main
(keys s22_archive_*); at merge those entries were kept and this session's duplicate archive_*
entries were dropped. Re-running this script after the merge is therefore a no-op (it skips
already-registered filenames). Kept as the reproducible record of this session's registration. Every registered
value is either (a) recomputed from the bytes on disk here (SHA-256, bytes, emitted_px), or
(b) copied from an existing in-repo provenance file named in the entry (checks JSON / note txt /
run card). No score, verdict upgrade, or scientific claim is invented: each entry's status states
it is an archive registration only and carries no promotion. Adds entries ONLY for TIFFs that
evidence/s22_download_audit.json listed as unregistered; existing entries are untouched.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path

import numpy as np
import rasterio

ROOT = Path(__file__).resolve().parents[1]
DL = ROOT / "docs/downloads"


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def emitted_px(p: Path) -> int:
    with rasterio.open(p) as ds:
        a = ds.read(1)
    return int((np.isfinite(a) & (a == 1.0)).sum())


# (manifest_key, nan_name, allfinite_name, zip_name_or_None, provenance_files, note_file_or_None)
LEGACY = [
    ("archive_gems27_all_increments",
     "gems27-all-increments-d2-8-h27-4-r1-t-v2-20261002-23ad46a4d7ba-nan.tif",
     "gems27-all-increments-d2-8-h27-4-r1-t-v2-20261002-23ad46a4d7ba-allfinite.tif",
     "gems27-all-increments-d2-8-h27-4-r1-t-v2-20261002-23ad46a4d7ba-nan.zip",
     ["docs/downloads/checks-gems27-all-increments-d2-8-h27-4-r1-t-v2-20261002-23ad46a4d7ba-nan.json"],
     "note-gems27-all-increments-d2-8-h27-4-r1-t-v2-20261002-23ad46a4d7ba-nan.txt"),
    ("archive_gems27_h27_4_pruned",
     "gems27-h27-4-r1-pruned-d1-5-20261003-450eb6859636-nan.tif",
     "gems27-h27-4-r1-pruned-d1-5-20261003-450eb6859636-allfinite.tif",
     "gems27-h27-4-r1-pruned-d1-5-20261003-450eb6859636-nan.zip",
     ["docs/downloads/h28_1_candidate_manifest.json"],
     None),
    ("archive_gems27_h28_1_edge",
     "gems27-h28-1-edge-coherence-plus-t-v2-h27-4-20261002-1113fba5f6cb-nan.tif",
     "gems27-h28-1-edge-coherence-plus-t-v2-h27-4-20261002-1113fba5f6cb-allfinite.tif",
     "gems27-h28-1-edge-coherence-plus-t-v2-h27-4-20261002-1113fba5f6cb-nan.zip",
     ["docs/downloads/checks-gems27-h28-1-edge-coherence-plus-t-v2-h27-4-20261002-1113fba5f6cb-nan.json",
      "docs/downloads/h28_1_candidate_manifest.json"],
     "note-gems27-h28-1-edge-coherence-plus-t-v2-h27-4-20261002-1113fba5f6cb-nan.txt"),
    ("archive_gems28_h40_1_thermal_vent",
     "gems28-h40-1-thermal-vent-r35-20261025T204851Z-7935260dcfad-nan.tif",
     "gems28-h40-1-thermal-vent-r35-20261025T204851Z-7935260dcfad-allfinite.tif",
     "gems28-h40-1-thermal-vent-r35-20261025T204851Z-7935260dcfad-nan.zip",
     ["docs/downloads/checks-gems28-h40-1-thermal-vent-r35-20261025T204851Z-7935260dcfad-holdout.json",
      "docs/downloads/checks-gems28-h40-1-thermal-vent-r35-20261025T204851Z-7935260dcfad-nan.tif.json"],
     None),
    ("archive_gems28_h41_1_thermal_spring",
     "gems28-h41-1-thermal-spring-r30-20261025T205008Z-73e2b0bd94a8-nan.tif",
     "gems28-h41-1-thermal-spring-r30-20261025T205008Z-73e2b0bd94a8-allfinite.tif",
     "gems28-h41-1-thermal-spring-r30-20261025T205008Z-73e2b0bd94a8-nan.zip",
     ["docs/downloads/checks-gems28-h41-1-thermal-spring-r30-20261025T205008Z-73e2b0bd94a8-nan.tif.json"],
     None),
    ("archive_gems28_h43_1_tpb2gkc",
     "gems28-h43-1-tpb2gkc-20261026-76737f19814e-nan.tif",
     "gems28-h43-1-tpb2gkc-20261026-76737f19814e-allfinite.tif",
     None,  # only an -allfinite.zip exists; slot zip semantics require the NaN member, so omit
     ["docs/downloads/checks-gems28-h43-1-tpb2gkc-20261026-76737f19814e.json",
      "evidence/session20_h43_run_card.json"],
     "note-gems28-h43-1-tpb2gkc-20261026-76737f19814e.txt"),
    ("archive_gems28_s21_puhgb",
     "gems28-s21-puhgb-20261026-16bbf281ba9b-nan.tif",
     "gems28-s21-puhgb-20261026-16bbf281ba9b-allfinite.tif",
     "gems28-s21-puhgb-20261026-16bbf281ba9b-nan.zip",
     ["evidence/s21_puhgb_run_card.json",
      "docs/downloads/checks-gems28-s21-puhgb-20261026-16bbf281ba9b.json"],
     "note-gems28-s21-puhgb-20261026-16bbf281ba9b.txt"),
]


def main() -> int:
    manifest_path = DL / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    registered = {
        item[key] for item in manifest.values() if isinstance(item, dict)
        for key in ("nan", "allfinite", "filename") if isinstance(item.get(key), str)
    }
    added = []
    for key, nan_name, fin_name, zip_name, provenance, note_file in LEGACY:
        if key in manifest:
            continue
        if nan_name in registered:
            continue
        nan_p, fin_p = DL / nan_name, DL / fin_name
        assert nan_p.is_file() and fin_p.is_file(), (nan_name, fin_name)
        m = re.search(r"-([0-9a-f]{12})-nan\.tif$", nan_name)
        assert m, nan_name
        cid = m.group(1)
        for rel in provenance:
            assert (ROOT / rel).is_file(), rel
        note = None
        if note_file and (DL / note_file).is_file():
            note = (DL / note_file).read_text(encoding="utf-8").strip()
        if not note:
            note = f"ARCHIVE ONLY {cid} | registered 2026-10-26 for audit coverage | DO NOT SUBMIT"
        assert 0 < len(note) <= 200, (key, len(note))
        entry = {
            "slug": key.removeprefix("archive_").replace("_", "-"),
            "hypothesis": "Archive registration only (S22, 2026-10-26). Scientific provenance: "
                          + "; ".join(provenance),
            "content_id": cid,
            "nan": nan_name,
            "allfinite": fin_name,
            "sha256_nan": sha256_file(nan_p),
            "sha256_allfinite": sha256_file(fin_p),
            "bytes_nan": nan_p.stat().st_size,
            "bytes_allfinite": fin_p.stat().st_size,
            "emitted_px": emitted_px(fin_p),
            "format_verified": True,
            "status": "ARCHIVE-REGISTERED 2026-10-26 by S22 for audit coverage (hashes/bytes/counts recomputed "
                      "from disk; provenance files named in hypothesis). This registration records NO promotion, "
                      "NO score and NO verdict change; the artifact's own evidence governs. DO NOT SUBMIT on the "
                      "basis of this entry.",
            "note": note,
            "submission_name": f"ARCHIVE-{key.removeprefix('archive_')}-{cid}",
            "verdict": "archive-unpromoted",
            "submission_ready": False,
            "slot_selected": False,
        }
        if note_file and (DL / note_file).is_file():
            entry["note_file"] = note_file
        if zip_name:
            zp = DL / zip_name
            assert zp.is_file(), zip_name
            entry["zip"] = zip_name
            entry["sha256_zip"] = sha256_file(zp)
            entry["bytes_zip"] = zp.stat().st_size
        manifest[key] = entry
        added.append(key)
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps({"added": added, "total_manifest_keys": len(manifest)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
