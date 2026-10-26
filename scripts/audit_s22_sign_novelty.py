#!/usr/bin/env python3
"""Read-only final-dot forensics for the concurrently merged S22-SIGN raster.

This is not a pre-placement surface check, full registry, experiment, score,
certificate, or slot selector. Excludes only the named candidate twins; a third
identical raster remains in the audit and will fail the duplicate stop.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio

from audit_focus_novelty import compare, load_focus

ROOT = Path(__file__).resolve().parents[1]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_dots(path: Path, signature: tuple, footprint: np.ndarray) -> np.ndarray:
    with rasterio.open(path) as src:
        if (src.crs, src.shape, src.transform) != signature or src.count != 1:
            raise ValueError(f"grid/band mismatch: {path}")
        arr = src.read(1)
    if not np.isfinite(arr[footprint]).all() or not np.isin(arr[footprint], [0, 1]).all():
        raise ValueError(f"invalid footprint values: {path}")
    return (arr == 1) & footprint


def audit() -> int:
    card = json.loads((ROOT / "evidence/s22_run_card.json").read_text())
    manifest = json.loads((ROOT / "docs/downloads/manifest.json").read_text())
    template = ROOT / "data/sample_submission.tif"
    pins = json.loads((ROOT / "registry/data_manifest.json").read_text())["files"]
    if sha(template) != next(x["sha256"] for x in pins if x["id"] == "sample_submission"):
        raise ValueError("template hash differs from owner-mirror pin")
    with rasterio.open(template) as src:
        signature = (src.crs, src.shape, src.transform)
        footprint = np.isfinite(src.read(1))
    candidate = (ROOT / card["submission_file"]).resolve()
    if not candidate.is_relative_to((ROOT / "docs/downloads").resolve()):
        raise ValueError("candidate must be in the registered downloads directory")
    if sha(candidate) != card["raster_sha256"]:
        raise ValueError("S22-SIGN candidate hash mismatch")
    dots = read_dots(candidate, signature, footprint)
    if not dots.any():
        raise ValueError("empty S22-SIGN candidate")

    refs = {}
    for item in manifest.values():
        if not isinstance(item, dict):
            continue
        for key, hash_key in (("nan", "sha256_nan"), ("allfinite", "sha256_allfinite"), ("filename", "sha256")):
            name, expected = item.get(key), item.get(hash_key)
            if isinstance(name, str):
                if Path(name).name != name or not isinstance(expected, str):
                    raise ValueError(f"unsafe or unpinned manifest raster: {name}")
                if name in refs and refs[name] != expected:
                    raise ValueError(f"conflicting hashes for {name}")
                refs[name] = expected
    downloads = ROOT / "docs/downloads"
    files = {p.name for p in downloads.glob("*.tif")}
    if files != set(refs):
        raise ValueError(f"local registry coverage mismatch: {sorted(files ^ set(refs))}")
    twins = {Path(card["submission_file"]).name, Path(card["submission_nan_file"]).name}
    if len(twins) != 2 or not twins.issubset(files):
        raise ValueError("candidate twins missing or ambiguous")
    for name in twins:
        path = downloads / name
        if sha(path) != refs[name] or not np.array_equal(read_dots(path, signature, footprint), dots):
            raise ValueError(f"excluded self-twin differs from the registered candidate: {name}")
    records, cache = [], {}

    def add(scope: str, name: str, digest: str, ref_dots: np.ndarray) -> None:
        key = hashlib.sha256(np.packbits(ref_dots).tobytes()).hexdigest()
        if key not in cache:
            cache[key] = compare(dots, ref_dots, footprint)
        result = dict(cache[key])
        if not result["complete"]:
            raise ValueError(f"undefined novelty comparison: {name}")
        records.append({"scope": scope, "name": name, "sha256": digest, **result})

    for name in sorted(files - twins):
        path = downloads / name
        if sha(path) != refs[name]:
            raise ValueError(f"manifest hash mismatch: {name}")
        add("local_archive", name, refs[name], read_dots(path, signature, footprint))
    priority = json.loads((ROOT / "evidence/s22_priority_audit.json").read_text())
    other_fp, focus = load_focus(priority, template)
    if not np.array_equal(footprint, other_fp):
        raise ValueError("priority audit footprint mismatch")
    for site, item in sorted(focus.items()):
        add("nine_site_historical", site + "/" + item["file"], item["sha256"], item["dots"])
    if not records:
        raise ValueError("no references")
    output = {
        "status": "COMPLETE_SCOPED",
        "observed_utc": datetime.now(timezone.utc).isoformat(),
        "scope": "final dots versus every registered local non-self TIFF and the nine named historical files only",
        "candidate_sha256": card["raster_sha256"],
        "candidate_dots": int(dots.sum()),
        "excluded_self_twins": sorted(twins),
        "local_reference_files": len(files - twins),
        "priority_reference_files": len(focus),
        "duplicate_comparisons": sum(row["duplicate"] for row in records),
        "maximum_overlap": max(records, key=lambda row: row["candidate_within_3px_fraction"]),
        "maximum_absolute_spearman": max(records, key=lambda row: abs(row["spearman_exact"])),
        "comparisons": records,
        "limitations": "No complete current parallel registry, private rasters or pre-placement surfaces; "
                       "this is not a uniqueness certificate or submission approval.",
        "experiments_run": 0,
        "slot_selected": False,
    }
    out = ROOT / "evidence/s22_sign_final_dot_audit.json"
    out.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    print(json.dumps({k: output[k] for k in ("local_reference_files", "priority_reference_files",
                                            "duplicate_comparisons", "maximum_overlap", "maximum_absolute_spearman")}))
    return 1 if output["duplicate_comparisons"] else 0


def main() -> int:
    try:
        return audit()
    except (OSError, ValueError, KeyError, IndexError, rasterio.errors.RasterioError) as exc:
        # Never leave an earlier successful scan behind after an invalid input.
        out = ROOT / "evidence/s22_sign_final_dot_audit.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps({"status": "FAIL", "observed_utc": datetime.now(timezone.utc).isoformat(),
                                   "failure": str(exc), "submission_ready": False}, indent=2) + "\n")
        print(f"FAIL: {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
