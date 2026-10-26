#!/usr/bin/env python3
"""Pin and restore published TIFFs from the nine requested repositories (GitHub only).

Snapshot is a bounded comparison universe, not proof of global parallel-run completeness.
All published .tif files in docs/downloads, submissions, archive/legacy_candidates and
local pre-run docs/downloads are enumerated. Invalid submission grids are explicitly excluded.
No organizer score is inferred from filenames or GitHub availability.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import rasterio

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27 import grid  # noqa: E402

SITES = (24, 25, 27, 28, 30, 31, 32, 33, 36)
PREFIXES = ("docs/downloads/", "submissions/", "archive/legacy_candidates/")


def gh_json(endpoint):
    return json.loads(subprocess.check_output(["gh", "api", endpoint], text=True))


def restore(row, cache_dir):
    dest = cache_dir / f"{row['blob_sha']}.tif"
    try:
        if not dest.exists():
            tmp = dest.with_suffix(".partial")
            with tmp.open("wb") as out:
                subprocess.run(["gh", "api", f"repos/{row['repo']}/contents/{row['path']}?ref={row['ref']}",
                                "-H", "Accept: application/vnd.github.raw"], stdout=out, check=True)
            # Git blob identity authenticates bytes to the pinned tree, not to organizer data.
            raw = tmp.read_bytes()
            blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
            if blob != row["blob_sha"]:
                raise ValueError("Git blob mismatch")
            tmp.replace(dest)
        raw = dest.read_bytes()
        blob = hashlib.sha1(f"blob {len(raw)}\0".encode() + raw).hexdigest()
        if blob != row["blob_sha"]:
            raise ValueError("cached Git blob mismatch")
        row = {**row, "local_path": str(dest.relative_to(ROOT)),
               "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}
        with rasterio.open(dest) as src:
            good = (src.count == 1 and src.shape == grid.SHAPE and src.crs is not None
                    and src.crs.to_epsg() == grid.CRS_EPSG and tuple(src.transform)[:6] == grid.TRANSFORM)
            row["status"] = "included" if good else "excluded_non_submission_grid"
            row["grid"] = {"shape": list(src.shape), "count": src.count, "crs": str(src.crs)}
        return row
    except Exception as exc:
        return {**row, "status": "fetch_or_read_failed", "error": str(exc)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--session", default="S18-MXTP")
    parser.add_argument("--cache-dir", type=Path, default=ROOT / "data/registry_s18")
    parser.add_argument("--output", type=Path, default=ROOT / "evidence/s18_registry_snapshot.json")
    args = parser.parse_args(argv)
    cache_dir = args.cache_dir.resolve()
    if not cache_dir.is_relative_to((ROOT / "data").resolve()):
        raise SystemExit("Registry cache must remain inside the ignored data directory")
    cache_dir.mkdir(parents=True, exist_ok=True)
    repos, rows, failures = [], [], []
    for site in SITES:
        repo = f"buffedlizard55-lab/GEMSDOE{site}"
        try:
            ref = gh_json(f"repos/{repo}/commits/HEAD")["sha"]
            tree = gh_json(f"repos/{repo}/git/trees/{ref}?recursive=1")
            if tree.get("truncated"):
                raise ValueError("truncated recursive tree")
            paths = [r for r in tree["tree"] if r["path"].lower().endswith(".tif")
                     and r["path"].startswith(PREFIXES) and r["type"] == "blob"]
            repos.append({"repo": repo, "ref": ref, "published_tiffs": len(paths),
                          "review_url": f"https://github.com/{repo}/tree/{ref}"})
            rows.extend({"repo": repo, "ref": ref, "path": r["path"], "blob_sha": r["sha"]} for r in paths)
        except Exception as exc:
            failures.append({"repo": repo, "error": str(exc)})
    # Multiple paths can be the same Git blob. Download once to avoid partial-file races.
    groups = {}
    for row in rows:
        groups.setdefault(row["blob_sha"], []).append(row)
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        restored = list(pool.map(lambda row: restore(row, cache_dir),
                                 [group[0] for group in groups.values()]))
    entries = []
    for row in restored:
        row["aliases"] = [{k: x[k] for k in ("repo", "ref", "path")} for x in groups[row["blob_sha"]]]
        entries.append(row)
    # Include pre-existing uncommitted/checkout research artifacts too (not the new candidate).
    for path in sorted((ROOT / "docs/downloads").glob("*.tif")):
        raw = path.read_bytes()
        sha = hashlib.sha256(raw).hexdigest()
        if any(x.get("sha256") == sha for x in entries):
            continue
        with rasterio.open(path) as src:
            good = (src.count == 1 and src.shape == grid.SHAPE and src.crs is not None
                    and src.crs.to_epsg() == grid.CRS_EPSG and tuple(src.transform)[:6] == grid.TRANSFORM)
        entries.append({"repo": "local_pre_run_checkout", "path": str(path.relative_to(ROOT)),
                        "local_path": str(path.relative_to(ROOT)), "sha256": sha, "bytes": len(raw),
                        "status": "included" if good else "excluded_non_submission_grid", "aliases": []})
    obj = {"schema": 1, "session": args.session, "repos": repos, "failures": failures,
           "scope": "Nine pinned published-submission directories plus pre-run local TIFFs; not a global registry",
           "organizer_authenticated": False,
           "complete_within_declared_scope": not failures and all(x["status"] != "fetch_or_read_failed" for x in entries),
           "entries": entries}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n")
    try:
        display_output = str(args.output.relative_to(ROOT))
    except ValueError:
        display_output = str(args.output)
    print(json.dumps({"snapshot": display_output, "repos": len(repos), "entries": len(entries),
                      "included": sum(x["status"] == "included" for x in entries),
                      "complete_within_declared_scope": obj["complete_within_declared_scope"]}, indent=2))
    return 0 if obj["complete_within_declared_scope"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
