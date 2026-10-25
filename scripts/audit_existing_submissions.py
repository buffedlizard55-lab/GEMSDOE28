#!/usr/bin/env python3
"""Re-audit historical downloads, comparison-only, using the pinned shared tools.

Does not place dots, train, modify a prediction, claim a score, or select a slot.
A final-dot audit of an old file is NOT a pre-placement surface experiment.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid  # noqa: E402
from gems27.shared_template import load_shared, verify_assets  # noqa: E402
from gems27.submission import sha256_file, verify_geotiff  # noqa: E402


def read_values(path: Path, footprint: np.ndarray, template: Path) -> np.ndarray:
    with rasterio.open(path) as source, rasterio.open(template) as reference:
        if (source.shape, source.crs, source.transform, source.count) != (
            reference.shape, reference.crs, reference.transform, 1
        ):
            raise ValueError(f"Misaligned comparison raster: {path}")
        values = source.read(1)
    if not np.isfinite(values[footprint]).all():
        raise ValueError(f"Nonfinite comparison inside footprint: {path}")
    return values


def canonical_hash(values: np.ndarray, footprint: np.ndarray) -> str:
    a = np.asarray(values[footprint], dtype="<f4").copy()
    a[a == 0] = 0
    return hashlib.sha256(a.tobytes()).hexdigest()


def main() -> int:
    template = ROOT / "data/sample_submission.tif"
    catalogue_path = ROOT / "data/labels.tif"
    foot = grid.load_footprint(template)
    catalogue = grid.load_labels(catalogue_path)
    shared = load_shared()
    manifest = json.loads((ROOT / "docs/downloads/manifest.json").read_text())
    item = manifest["primary"]
    primary = ROOT / "docs/downloads" / item["allfinite"]
    values = read_values(primary, foot, template)
    dots = foot & (values > 0)
    priority = json.loads((ROOT / "evidence/priority_repository_audit.json").read_text())
    references, seen = [], set()
    for repo in priority["repositories"]:
        for raster in repo["priority_rasters"]:
            path = ROOT / raster["local_path"]
            if sha256_file(path) != raster["sha256"]:
                raise ValueError("Priority registry bytes changed: " + str(path))
            # Exclude ONLY this archived prediction's own twins, not other duplicates.
            if repo["repository"].endswith("/GEMSDOE28") and item["content_id"] in raster["path"]:
                continue
            digest = raster["footprint_values_sha256"]
            if digest in seen:
                continue
            seen.add(digest)
            references.append({"id": repo["repository"] + ":" + raster["path"],
                               "file": raster["path"], "cache_path": raster["local_path"],
                               "sha256": raster["sha256"], "footprint_sha256": digest})
    for path in sorted((ROOT / "docs/downloads").glob("*-nan.tif")):
        if item["content_id"] in path.name:
            continue
        a = read_values(path, foot, template)
        digest = canonical_hash(a, foot)
        if digest in seen:
            continue
        seen.add(digest)
        references.append({"id": "local:" + path.name, "file": path.name,
                           "cache_path": str(path.relative_to(ROOT)),
                           "sha256": sha256_file(path), "footprint_sha256": digest})
    # Strict shared comparator; no perturbation or registry-driven reranking.
    similarity = shared.novelty.compare_registry(values, foot, references, ROOT, dots=dots)
    by_id = {row["id"]: row for row in references}
    for row in similarity["rows"]:
        row["raster_sha256"] = by_id[row["registry_id"]]["sha256"]
    validation = verify_geotiff(primary, template)
    shared_validation = shared.submission.check_variants(primary, template)
    # Educational reconstruction in memory only; never written as a submission.
    def priority_dots(name, token):
        candidates = [r for repo in priority["repositories"]
                      if repo["repository"].endswith("/" + name)
                      for r in repo["priority_rasters"] if token in r["path"]]
        if not candidates:
            raise ValueError(f"Missing priority artifact: {name}/{token}")
        return foot & (read_values(ROOT / candidates[0]["local_path"], foot, template) > 0)

    d28 = priority_dots("GEMSDOE25", "e56ea318af89")
    solo = priority_dots("GEMSDOE28", "8acb75e1f2cc")
    champion = priority_dots("GEMSDOE32", "e5eb6e7e")
    g36 = priority_dots("GEMSDOE36", "9b9ea4e6")
    dcat = distance_transform_edt(~catalogue)
    forensic = {
        "purpose": "Educational pixel-set comparisons only; no raster generated",
        "champion_equals_solo_minus_catalogue_distance_le_2px": bool(np.array_equal(champion, solo & (dcat > 2))),
        "champion_equals_d28_minus_catalogue_distance_le_2px": bool(np.array_equal(champion, d28 & (dcat > 2))),
        "champion_pixels": int(champion.sum()), "d28_pixels": int(d28.sum()),
        "solo_pixels": int(solo.sum()), "g36_pixels": int(g36.sum()),
        "removed_solo_to_champion": int((solo & ~champion).sum()),
        "added_solo_to_champion": int((champion & ~solo).sum()),
        "g36_contains_all_champion_pixels": bool(not (champion & ~g36).any()),
        "g36_additional_pixels": int((g36 & ~champion).sum()),
        "GEMSDOE25_equals_GEMSDOE30_inside_footprint": bool(np.array_equal(d28, priority_dots("GEMSDOE30", "91eae1ca"))),
        "GEMSDOE28_solo_equals_GEMSDOE31_solo_inside_footprint": bool(np.array_equal(solo, priority_dots("GEMSDOE31", "h27-4-solo"))),
    }
    report = {
        "schema_version": 1, "observed_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "Historical primary audit, not a new scientific experiment or submission",
        "archived_file": str(primary.relative_to(ROOT)), "raster_sha256": sha256_file(primary),
        "template_sha256": sha256_file(template), "catalogue_sha256": sha256_file(catalogue_path),
        "shared_template": verify_assets(), "format_validator": validation,
        "shared_format_validator": shared_validation,
        "surface_before_placement": {"status": "unavailable", "reason": "No original continuous primary surface supplied; not reconstructed from final dots."},
        "final_dots": similarity,
        "registry": {"complete": False, "scope": "Requested high-score artifacts plus local historical downloads; not the unsupplied parallel-run registry",
                     "members": references, "source_audit_sha256": sha256_file(ROOT / "evidence/priority_repository_audit.json")},
        "forensic": forensic, "organizer_confirmed_scores": [],
        "experiments_run": 0, "new_raster_generated": False, "slot_selected": False,
        "submission_ready": False, "verdict": "negative",
        "failures": ["Archived primary is duplicate under final-dot lane threshold",
                     "Assigned method paragraph absent", "No complete external parallel-run registry",
                     "No compliant paired improvement evidence for a new candidate"],
    }
    destination = ROOT / "evidence/current_submission_audit.json"
    destination.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"report": str(destination.relative_to(ROOT)), "format_valid": validation["hard_checks_passed"],
                      "final_dot_uniqueness_passed": similarity["passed"],
                      "max_overlap": similarity["max_dot_overlap"], "max_abs_spearman": similarity["max_abs_rank_correlation"],
                      "submission_ready": False, "verdict": "negative"}, indent=2))
    return 0  # An honestly measured negative audit is a successfully completed audit.


if __name__ == "__main__":
    raise SystemExit(main())
