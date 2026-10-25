#!/usr/bin/env python3
"""Pin and inspect the nine requested owner repositories through the GitHub API.

Educational comparison only: no model, placement, competition score or slot selection.
Owner mirrors are not official competition receipts. Downloads stay in ignored data/.
Every downloaded raster is checked against the pinned Git tree's blob identity.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid  # noqa: E402
from gems27.submission import sha256_file, verify_geotiff  # noqa: E402

PRIORITY = {
    "GEMSDOE24": ["989f59505db1"],
    "GEMSDOE25": ["e56ea318af89"],
    "GEMSDOE27": ["5512495c6bd1"],
    "GEMSDOE28": ["8acb75e1f2cc", "31e35eee884e", "b531dae0a36f", "56a9f473edc7"],
    "GEMSDOE30": ["91eae1ca"],
    "GEMSDOE31": ["8acb75e1"],
    "GEMSDOE32": ["e5eb6e7e"],
    "GEMSDOE33": ["cb490425926e"],
    "GEMSDOE36": ["9b9ea4e6"],
}


def api(path: str, *, raw: bool = False) -> bytes:
    command = ["gh", "api", path]
    if raw:
        command += ["-H", "Accept: application/vnd.github.raw"]
    return subprocess.run(command, check=True, capture_output=True, timeout=120).stdout


def blob_oid(data: bytes) -> str:
    return hashlib.sha1(f"blob {len(data)}\0".encode() + data).hexdigest()


def fetch_blob(repo: str, ref: str, entry: dict, destination: Path) -> bytes:
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = destination.read_bytes() if destination.exists() else b""
    if blob_oid(data) != entry["sha"]:
        data = api(f"repos/{repo}/contents/{entry['path']}?ref={ref}", raw=True)
    if len(data) != entry["size"] or blob_oid(data) != entry["sha"]:
        raise ValueError(f"Git blob mismatch: {repo}@{ref}:{entry['path']}")
    destination.write_bytes(data)
    return data


def inspect_repository(name: str, directory: Path, template: Path) -> dict:
    import numpy as np
    import rasterio

    repo = f"buffedlizard55-lab/{name}"
    commit = json.loads(api(f"repos/{repo}/commits/main"))["sha"]
    tree = json.loads(api(f"repos/{repo}/git/trees/{commit}?recursive=1"))
    if tree.get("truncated"):
        raise ValueError(f"Truncated registry tree: {repo}")
    entries = {e["path"]: e for e in tree["tree"] if e["type"] == "blob"}
    raster_paths = [p for p in entries if p.lower().endswith((".tif", ".tiff"))]
    selected = sorted(p for p in raster_paths if any(token in p for token in PRIORITY[name]))
    pages = []
    for path in ("README.md", "docs/index.html", "index.html"):
        if path not in entries:
            continue
        data = fetch_blob(repo, commit, entries[path], directory / name / path)
        lines = data.decode("utf-8").splitlines()
        excerpts = [{"line": i, "text": line[:1500]} for i, line in enumerate(lines, 1)
                    if any(token in line for token in PRIORITY[name])][:12]
        pages.append({"path": path, "sha256": hashlib.sha256(data).hexdigest(),
                      "source": f"https://github.com/{repo}/blob/{commit}/{path}",
                      "matching_excerpts": excerpts})
    foot = grid.load_footprint(template)
    rasters = []
    for path in selected:
        destination = directory / name / path
        data = fetch_blob(repo, commit, entries[path], destination)
        result = verify_geotiff(destination, template)
        with rasterio.open(destination) as dataset:
            values = dataset.read(1)[foot].astype("<f4")
        values[values == 0] = 0
        result.update({"path": path, "local_path": str(destination.relative_to(ROOT)),
                       "git_blob": entries[path]["sha"], "blob_verified": True,
                       "footprint_values_sha256": hashlib.sha256(values.tobytes()).hexdigest(),
                       "binary_inside": bool(np.isin(values, [0, 1]).all()),
                       "source": f"https://github.com/{repo}/blob/{commit}/{path}"})
        rasters.append(result)
    missing = [token for token in PRIORITY[name] if not any(token in p for p in selected)]
    return {"repository": repo, "commit": commit, "tree": tree["sha"], "pages": pages,
            "all_raster_paths": sorted(raster_paths), "priority_rasters": rasters,
            "missing_requested_identities": missing,
            "evidence_class": "Owner repository bytes, not organizer receipts or confirmed scores"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--template", type=Path, default=ROOT / "data/sample_submission.tif")
    parser.add_argument("--cache", type=Path, default=ROOT / "data/priority_repositories")
    parser.add_argument("--out", type=Path, default=ROOT / "evidence/priority_repository_audit.json")
    args = parser.parse_args(argv)
    records, errors = [], []
    for name in PRIORITY:
        try:
            record = inspect_repository(name, args.cache, args.template)
            records.append(record)
            if record["missing_requested_identities"]:
                errors.append({"repository": name, "error": "Requested artifact identities were not found",
                               "missing": record["missing_requested_identities"]})
            print(f"{name}: {record['commit'][:12]}, {len(record['priority_rasters'])} rasters", flush=True)
        except (OSError, ValueError, subprocess.SubprocessError) as exc:
            errors.append({"repository": name, "error": str(exc)})
            print(f"{name}: FAILED {exc}", flush=True)
    report = {"schema_version": 1, "observed_utc": datetime.now(timezone.utc).isoformat(),
              "purpose": "Educational audit only; no predictions generated or scores inferred",
              "template_sha256": sha256_file(args.template), "repositories": records,
              "errors": errors, "priority_inventory_retrieved": len(records) == len(PRIORITY) and not errors,
              "external_parallel_registry_complete": False,
              "registry_limitation": "Priority artifact subset only; no shared parallel-run registry or pre-placement surfaces supplied.",
              "organizer_confirmed_scores": [], "experiments_run": 0, "slot_selected": False}
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
