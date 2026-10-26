#!/usr/bin/env python3
"""Compare the nine *historical* focus-site TIFFs; never place new dots.

The input inventory comes from audit_priority_repositories.py: owner GitHub bytes,
not organizer receipts. Rank correlations are exact over the template footprint
(binary Spearman equals binary Pearson). Overlaps are directional and include
all candidate dots at Euclidean distance <=3 pixels. Neither a pass within these
nine files nor a different file hash proves uniqueness versus other submissions.
"""
from __future__ import annotations

import argparse
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
from gems27.grid import load_footprint  # noqa: E402

# The filenames are the specific historical best *claims* in the user's prompt.
FOCUS = {
    "GEMSDOE24": "gems24-h25-1-dotted-h19-5-d1-5-20261002-989f59505db1-allfinite.tif",
    "GEMSDOE25": "gems25-dotted-h19-5-d2-8-20261002-e56ea318af89-zeros.tif",
    "GEMSDOE27": "gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-allfinite.tif",
    "GEMSDOE28": "gems28-h36-1-rung30-blind-r1-20261003-b531dae0a36f-allfinite.tif",
    "GEMSDOE30": "gemsdoe30-d28-poisson300m-offcat-44090-20261003T233156Z-91eae1ca.tif",
    "GEMSDOE31": "gemsdoe31-h27-4-solo-d28-20261004-8acb75e1-allfinite.tif",
    "GEMSDOE32": "gemsdoe32-h33-h33-2-b2-20261004T220000Z-e5eb6e7e-zeros.tif",
    "GEMSDOE33": "GEMSDOE33-h33d-analog-tip-stepover-r30-20261004-cb490425926e.tif",
    "GEMSDOE36": "gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
}


def binary_spearman(a: np.ndarray, b: np.ndarray, footprint: np.ndarray) -> float | None:
    """Exact average-tie Spearman for aligned binary grids on the footprint."""
    av, bv = np.asarray(a, bool)[footprint], np.asarray(b, bool)[footprint]
    n, na, nb = av.size, int(av.sum()), int(bv.sum())
    if not n or na in (0, n) or nb in (0, n):
        return None
    both = int(np.count_nonzero(av & bv))
    rho = (both - na * nb / n) / np.sqrt(na * (1 - na / n) * nb * (1 - nb / n))
    # Suppress harmless floating-roundoff excursions such as 1.0000000000000002.
    return float(np.clip(rho, -1.0, 1.0))


def compare(a: np.ndarray, b: np.ndarray, footprint: np.ndarray, *, radius_px: float = 3) -> dict:
    a, b, footprint = np.asarray(a, bool), np.asarray(b, bool), np.asarray(footprint, bool)
    if a.ndim != 2 or a.shape != b.shape or a.shape != footprint.shape or not footprint.any():
        raise ValueError("aligned nonempty 2-D footprint required")
    if not np.isfinite(radius_px) or radius_px < 0:
        raise ValueError("finite nonnegative radius required")
    a, b = a & footprint, b & footprint
    n = int(a.sum())
    # An empty candidate has undefined directional coverage, and a constant
    # reference has undefined rank correlation: neither is evidence of novelty.
    fraction = float(np.mean(distance_transform_edt(~b)[a] <= radius_px)) if n and b.any() else None
    rho = binary_spearman(a, b, footprint)
    duplicate = bool((rho is not None and abs(rho) > 0.90) or (fraction is not None and fraction > 0.70))
    return {"spearman_exact": rho, "candidate_within_3px_fraction": fraction,
            "candidate_dots": n, "reference_dots": int(b.sum()), "duplicate": duplicate,
            "complete": rho is not None and fraction is not None}


def load_focus(audit: dict, template: Path) -> tuple[np.ndarray, dict]:
    fp = load_footprint(template)
    with rasterio.open(template) as ds:
        signature = (ds.crs, ds.shape, ds.transform)
    if audit.get("priority_inventory_retrieved") is not True:
        raise ValueError("priority inventory incomplete")
    records = {r["repository"].split("/")[-1]: r for r in audit["repositories"]}
    if len(records) != len(audit["repositories"]):
        raise ValueError("duplicate repository records in priority inventory")
    result = {}
    for site, filename in FOCUS.items():
        if site not in records:
            raise ValueError(f"missing priority repository: {site}")
        repo = records[site]
        rows = [r for r in repo["priority_rasters"] if r["file"] == filename]
        if len(rows) != 1 or rows[0].get("blob_verified") is not True:
            raise ValueError(f"missing or ambiguous verified raster: {site} {filename}")
        row = rows[0]
        path = (ROOT / row["local_path"]).resolve()
        if not path.is_relative_to(ROOT) or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            raise ValueError(f"cache path or SHA-256 mismatch: {site}")
        with rasterio.open(path) as ds:
            if (ds.crs, ds.shape, ds.transform) != signature or ds.count != 1:
                raise ValueError(f"grid mismatch: {site}")
            values = ds.read(1)
        if not np.isfinite(values[fp]).all() or not np.isin(values[fp], [0, 1]).all():
            raise ValueError(f"non-binary or nonfinite footprint: {site}")
        result[site] = {"dots": fp & (values == 1), "file": filename, "sha256": row["sha256"],
                        "source": row["source"], "commit": repo["commit"],
                        "hard_checks_passed": row.get("hard_checks_passed") is True,
                        "hard_failures": row.get("hard_failures", ["validator status missing"])}
    return fp, result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit", type=Path, default=ROOT / "evidence/s22_priority_audit.json")
    parser.add_argument("--template", type=Path, default=ROOT / "data/sample_submission.tif")
    parser.add_argument("--labels", type=Path, default=ROOT / "data/labels.tif")
    parser.add_argument("--out", type=Path, default=ROOT / "evidence/s22_focus_novelty.json")
    args = parser.parse_args()
    fp, rasters = load_focus(json.loads(args.audit.read_text()), args.template)
    rows = []
    # Distance-to-reference is reused for all candidates, avoiding nine EDTs per candidate.
    for ref_site, ref in rasters.items():
        distance = distance_transform_edt(~ref["dots"])
        for site, item in rasters.items():
            if site == ref_site:
                continue
            candidate, reference = item["dots"], ref["dots"]
            rho = binary_spearman(candidate, reference, fp)
            fraction = float(np.mean(distance[candidate] <= 3)) if candidate.any() and reference.any() else None
            rows.append({"candidate_site": site, "reference_site": ref_site,
                         "spearman_exact": rho, "candidate_within_3px_fraction": fraction,
                         "duplicate": bool((rho is not None and abs(rho) > .90) or
                                           (fraction is not None and fraction > .70)),
                         "complete": rho is not None and fraction is not None})
    summary = []
    for site, item in rasters.items():
        comparisons = [r for r in rows if r["candidate_site"] == site]
        valid = [r for r in comparisons if r["complete"]]
        worst = max(valid, key=lambda r: r["candidate_within_3px_fraction"]) if valid else None
        summary.append({"site": site, "filename": item["file"], "sha256": item["sha256"],
                        "source": item["source"], "commit": item["commit"],
                        "hard_checks_passed": item["hard_checks_passed"], "hard_failures": item["hard_failures"],
                        "positive_pixels": int(item["dots"].sum()),
                        "max_overlap": worst, "duplicate_vs_other_eight": any(r["duplicate"] for r in comparisons),
                        "comparisons_complete": len(valid) == 8})
    # Reproduce the champion construction from the two independently fetched
    # historical artifacts and the hash-pinned owner-mirror catalogue. This is
    # pixel forensics, not proof of why an organizer score changed.
    inputs = json.loads((ROOT / "registry/data_manifest.json").read_text())["files"]
    expected_labels = next(row["sha256"] for row in inputs if row["id"] == "labels")
    if hashlib.sha256(args.labels.read_bytes()).hexdigest() != expected_labels:
        raise ValueError("catalogue hash does not match its owner-mirror pin")
    with rasterio.open(args.template) as template, rasterio.open(args.labels) as label_ds:
        if (label_ds.crs, label_ds.shape, label_ds.transform) != (template.crs, template.shape, template.transform):
            raise ValueError("catalogue grid mismatch")
        labels = label_ds.read(1) == 1
    solo = rasters["GEMSDOE31"]["dots"]
    champion = rasters["GEMSDOE32"]["dots"]
    g36 = rasters["GEMSDOE36"]["dots"]
    rebuilt = solo & (distance_transform_edt(~labels) > 2)
    forensics = {"solo_pixels": int(solo.sum()), "champion_pixels": int(champion.sum()),
                 "solo_removed_within_2px": int((solo & ~rebuilt).sum()),
                 "champion_reconstruction_symmetric_difference": int((rebuilt ^ champion).sum()),
                 "gem25_equals_gem30_inside_footprint": bool(np.array_equal(rasters["GEMSDOE25"]["dots"], rasters["GEMSDOE30"]["dots"])),
                 "gem36_champion_dots_missing": int((champion & ~g36).sum()),
                 "gem36_additional_dots": int((g36 & ~champion).sum()),
                 "catalogue_sha256": expected_labels,
                 "limitation": "Pixel reconstruction does not identify the hidden truth or prove score causation."}
    output = {"observed_utc": datetime.now(timezone.utc).isoformat(),
              "scope": "Nine explicitly named historical artifacts only; not the complete parallel registry",
              "method": "Exact binary Spearman across the footprint; directional Euclidean <=3-px overlap across every candidate dot",
              "registry_limitations": "No pre-placement surfaces or private/unpublished outputs; no organizer score receipts.",
              "summary": summary, "comparisons": rows, "forensics": forensics,
              "experiments_run": 0, "slot_selected": False}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(output, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"rows": len(rows), "pairs_with_duplicate": sum(r["duplicate"] for r in rows),
                      "all_complete": all(r["complete"] for r in rows), "out": str(args.out)}))
    return 0 if all(r["complete"] for r in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
