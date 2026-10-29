#!/usr/bin/env python3
"""Fetch every unique registry raster pinned in data/research/shared_priority_registry.json.

Why this exists: the duplicate/lane gates must compare a candidate against the *complete* registry
the project has pinned (46 unique rasters, including the GEMSDOE13 spacing-five lattice registered as
registry-039), not only the handful of TIFFs that happen to sit in docs/downloads/.

Each file is fetched from its owner GitHub repo at its pinned ref (or, for the "local historic
references" rows, from the GEMSDOE24 repo at the pinned ref where those inputs are published) and is
accepted only if its byte size and SHA-256 match the registry pin. Output is git-ignored under
data/research/registry_rasters/. A receipt is written to evidence/s29_registry_fetch.json.

This script never contacts DrivenData and never contacts any host other than GitHub.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "data" / "research" / "shared_priority_registry.json"
OUT_DIR = ROOT / "data" / "research" / "registry_rasters"
RECEIPT = ROOT / "evidence" / "s29_registry_fetch.json"
LOCAL_REFERENCE_REPO = "buffedlizard55-lab/GEMSDOE24"
LOCAL_REFERENCE_REF = "07345ea0604953d7efb858d9cfbc21e20c7aca0b"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def gh_fetch(repo: str, ref: str, remote_path: str, destination: Path) -> None:
    if not shutil.which("gh"):
        raise RuntimeError("gh CLI is required to fetch registry rasters")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".partial")
    temporary.unlink(missing_ok=True)
    with temporary.open("wb") as output:
        subprocess.run(
            ["gh", "api", f"repos/{repo}/contents/{remote_path}?ref={ref}",
             "-H", "Accept: application/vnd.github.raw"],
            stdout=output, check=True,
        )
    if temporary.stat().st_size == 0:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(f"empty object {repo}/{remote_path}@{ref}")
    temporary.replace(destination)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--only", nargs="*", default=None, help="registry ids to fetch (default: all)")
    args = parser.parse_args()
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    rows = []
    failures = []
    for entry in registry["unique_rasters"]:
        rid = entry.get("id") or entry["file"]
        if args.only and rid not in args.only:
            continue
        if entry["repo"] == "local historic references":
            repo, ref = LOCAL_REFERENCE_REPO, LOCAL_REFERENCE_REF
        else:
            repo, ref = entry["repo"], entry["ref"]
        remote_path = entry["file"]
        destination = OUT_DIR / f"{rid}.tif"
        expected = entry["sha256"]
        status = "already-verified"
        if not (destination.is_file() and sha256_file(destination) == expected):
            status = "fetched"
            try:
                gh_fetch(repo, ref, remote_path, destination)
            except Exception as exc:  # noqa: BLE001 - recorded as a failure, not hidden
                failures.append({"id": rid, "error": str(exc)[:300]})
                rows.append({"id": rid, "status": "fetch-failed", "repo": repo, "file": remote_path})
                continue
        actual = sha256_file(destination)
        ok = actual == expected
        if not ok:
            failures.append({"id": rid, "error": f"sha256 {actual} != pin {expected}"})
            destination.unlink(missing_ok=True)
        rows.append({"id": rid, "status": status if ok else "sha-mismatch", "repo": repo, "ref": ref,
                     "file": remote_path, "sha256": actual, "expected_sha256": expected,
                     "bytes": destination.stat().st_size if destination.exists() else None,
                     "sha_match": ok})
        print(f"{rid}: {'OK' if ok else 'MISMATCH'} {remote_path.split('/')[-1]}", flush=True)
    receipt = {
        "schema": "s29-registry-fetch-v1",
        "registry": "data/research/shared_priority_registry.json",
        "registry_sha256": sha256_file(REGISTRY),
        "requested": len(rows),
        "verified": sum(1 for r in rows if r.get("sha_match")),
        "failures": failures,
        "rows": rows,
        "provenance": "Owner GitHub repositories at pinned refs; SHA-256 pins from the project registry. "
                      "Not organizer-authenticated; a pin match proves byte identity with the registered file only.",
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"verified {receipt['verified']}/{receipt['requested']}; failures={len(failures)}")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
