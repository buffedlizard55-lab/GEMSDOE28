#!/usr/bin/env python3
"""Restore hash-pinned owner mirrors into a git-ignored data directory.

The mirrors are public GitHub files, not organizer-authenticated downloads. A SHA-256 match proves only
that fetched bytes match the registered mirror. This script does not contact DrivenData.

Examples:
  python scripts/restore_data.py --group core   # training raster, labels, grid template
  python scripts/restore_data.py --group model  # H19-5, derived terrain descriptors, comparison rasters
  python scripts/restore_data.py --group all
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "registry" / "data_manifest.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch_to(repo: str, ref: str, remote_path: str, destination: Path) -> None:
    """Fetch one public GitHub content object to disk without holding it in RAM."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_name(destination.name + ".partial")
    temporary.unlink(missing_ok=True)
    try:
        if shutil.which("gh"):
            with temporary.open("wb") as output:
                subprocess.run(
                    [
                        "gh", "api", f"repos/{repo}/contents/{remote_path}?ref={ref}",
                        "-H", "Accept: application/vnd.github.raw",
                    ],
                    stdout=output,
                    check=True,
                )
        else:
            request = urllib.request.Request(
                f"https://raw.githubusercontent.com/{repo}/{ref}/{remote_path}",
                headers={"User-Agent": "GEMSDOE28-research/1.0"},
            )
            with urllib.request.urlopen(request, timeout=180) as response, temporary.open("wb") as output:
                shutil.copyfileobj(response, output, length=1 << 20)
        if temporary.stat().st_size == 0:
            raise RuntimeError(f"GitHub returned an empty object for {repo}/{remote_path}")
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)


def restore(entry: dict, root: Path) -> dict:
    destination = root / entry["dest"]
    expected_hash = entry["sha256"]
    expected_bytes = int(entry["bytes"])
    if destination.is_file():
        actual_hash = sha256_file(destination)
        if actual_hash == expected_hash and destination.stat().st_size == expected_bytes:
            return {"id": entry["id"], "status": "already-verified", "bytes": expected_bytes,
                    "sha256": actual_hash}
        destination.unlink()

    partial = destination.with_name(destination.name + ".assembling")
    partial.unlink(missing_ok=True)
    try:
        if "parts" in entry:
            with partial.open("wb") as assembled:
                for index, remote_path in enumerate(entry["parts"]):
                    part = root / "raw" / f"{entry['id']}-{index:03d}.part"
                    fetch_to(entry["repo"], entry["ref"], remote_path, part)
                    with part.open("rb") as source:
                        shutil.copyfileobj(source, assembled, length=1 << 20)
                    part.unlink(missing_ok=True)
                    print(f"  assembled part {index + 1}/{len(entry['parts'])}: {remote_path}", flush=True)
        else:
            fetch_to(entry["repo"], entry["ref"], entry["path"], partial)
        actual_bytes = partial.stat().st_size
        actual_hash = sha256_file(partial)
        if actual_bytes != expected_bytes or actual_hash != expected_hash:
            raise ValueError(
                f"pin mismatch for {entry['id']}: bytes {actual_bytes}/{expected_bytes}; "
                f"sha256 {actual_hash}/{expected_hash}"
            )
        partial.replace(destination)
        return {"id": entry["id"], "status": "restored-and-verified", "bytes": actual_bytes,
                "sha256": actual_hash}
    except Exception:
        partial.unlink(missing_ok=True)
        destination.unlink(missing_ok=True)
        raise
    finally:
        shutil.rmtree(root / "raw", ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--group", choices=("core", "model", "all"), default="all")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--data-dir", type=Path, default=None,
                        help="defaults to GEMS_DATA_DIR or repository/data")
    args = parser.parse_args()
    root = (args.data_dir or Path(os.environ.get("GEMS_DATA_DIR", ROOT / "data"))).resolve()
    manifest = json.loads(args.manifest.read_text())
    root.mkdir(parents=True, exist_ok=True)
    results = []
    for entry in manifest["files"]:
        if args.group != "all" and entry["group"] != args.group:
            continue
        print(f"Fetching {entry['id']} → {root / entry['dest']}", flush=True)
        result = restore(entry, root)
        results.append(result)
        print(f"  {result['status']}: {result['bytes']:,} bytes; sha256={result['sha256']}", flush=True)
    receipt = {
        "schema_version": 1,
        "group": args.group,
        "data_root": str(root),
        "provenance_warning": manifest["provenance_warning"],
        "files": results,
    }
    (root / "restore_receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(f"Verified {len(results)} inputs in {root}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
