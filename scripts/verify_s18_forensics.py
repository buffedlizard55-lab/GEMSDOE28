#!/usr/bin/env python3
"""Educational byte forensics only. No prediction pixels are copied to a new artifact."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import rasterio
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid, paths, submission  # noqa: E402

# These figures are unverified task-statement claims, not measured scores or receipts.
CLAIMS = [(24, "989f59505db1", 0.2477), (25, "e56ea318af89", 0.2600),
          (27, "5512495c6bd1", 0.2449), (28, "b531dae0a36f", 0.2710),
          (30, "91eae1ca", 0.2600), (31, "h27-4-solo-d28", 0.2708),
          (32, "e5eb6e7e-zeros", 0.2778), (33, "cb490425926e", 0.2632),
          (36, "9b9ea4e6-zeros", 0.2750)]


def main():
    registry = json.loads((ROOT / "evidence/s18_registry_snapshot.json").read_text())
    foot = grid.load_footprint(paths.TEMPLATE)
    labels = grid.load_labels(paths.LABELS)
    dcat = distance_transform_edt(~labels)
    sites, dots = [], {}
    for site, token, claim in CLAIMS:
        matches = []
        for entry in registry["entries"]:
            if entry["status"] != "included":
                continue
            for alias in entry.get("aliases", []):
                if alias["repo"] == f"buffedlizard55-lab/GEMSDOE{site}" and token in alias["path"]:
                    matches.append((alias["path"], entry, alias))
        # Prefer finite variant by name; arrays must be compared inside official template footprint.
        matches.sort(key=lambda x: ("nan" in x[0], x[0]))
        if not matches:
            raise ValueError(f"Missing claimed artifact for site {site}")
        name, entry, alias = matches[0]
        path = ROOT / entry["local_path"]
        if submission.sha256_file(path) != entry["sha256"]:
            raise ValueError("registry file changed")
        with rasterio.open(path) as src:
            raw = src.read(1)
        dot = foot & np.isfinite(raw) & (raw > 0)
        dots[site] = dot
        sites.append({"site": f"GEMSDOE{site}", "artifact": name.split("/")[-1],
                      "owner_reported_claim": claim, "evidence_class": "UNVERIFIED OWNER-REPORTED CONTEXT ONLY",
                      "organizer_receipt": None, "sha256": entry["sha256"], "dot_count": int(dot.sum()),
                      "on_catalogue": int((dot & labels).sum()),
                      "review_url": f"https://github.com/{alias['repo']}/blob/{alias['ref']}/{name}"})
    champion = dots[32]
    solo_path = ROOT / "docs/downloads/gems28-h27-4-r1-solo-d2-8-20261003-8acb75e1f2cc-nan.tif"
    with rasterio.open(solo_path) as src:
        raw = src.read(1)
        solo = foot & np.isfinite(raw) & (raw > 0)
    with rasterio.open(paths.DOTTED_D2_8) as src:
        raw = src.read(1)
        d28 = foot & np.isfinite(raw) & (raw > 0)
    checks = {"champion_equals_solo_without_dcat_le2": bool(np.array_equal(champion, solo & (dcat > 2))),
              "solo_equals_d28_without_dcat_le1": bool(np.array_equal(solo, d28 & (dcat > 1))),
              "site31_solo_equals_local_solo": bool(np.array_equal(dots[31], solo)),
              "site30_equals_d28": bool(np.array_equal(dots[30], d28)),
              "site36_contains_champion": bool(not np.any(champion & ~dots[36]))}
    assert all(checks.values()), checks
    obj = {"session": "S18-MXTP", "purpose": "EDUCATION ONLY; score causation is not authenticated",
           "sites": sites, "checks": checks, "solo_sha256": submission.sha256_file(solo_path),
           "champion_sha256": next(x["sha256"] for x in sites if x["site"] == "GEMSDOE32"),
           "removed_from_solo": int((solo & ~champion).sum()),
           "added_to_solo": int((champion & ~solo).sum()),
           "symmetric_difference_reconstruction": int((champion ^ (solo & (dcat > 2))).sum()),
           "site36_added_to_champion": int((dots[36] & ~champion).sum()),
           "organizer_confirmed_scores": [], "note": "Reported performance ladder is consistent with pruning false positives; hidden truth and receipts are unavailable, so causal attribution remains conditional."}
    dest = ROOT / "evidence/s18_champion_forensic.json"
    dest.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")
    print(json.dumps({"checks": checks, "removed_from_solo": obj["removed_from_solo"],
                      "site36_added_to_champion": obj["site36_added_to_champion"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
