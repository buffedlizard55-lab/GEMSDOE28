#!/usr/bin/env python3
"""Fetch every GeoTIFF under docs/ of the nine GEMSDOE owner repositories into data/registry_tifs/.

Source: public GitHub repositories buffedlizard55-lab/GEMSDOE{24,25,27,28,30,31,32,33,36} at their
default-branch HEAD, read through the GitHub REST API (api.github.com). Bytes are identified by git blob
SHA and recorded with SHA-256. These are owner-published submission files, not organizer receipts.

Output (git-ignored, under data/): data/registry_tifs/<site>/<filename>.tif and
data/registry_tifs/manifest.json (site, path, blob sha, bytes, sha256).
"""
from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "registry_tifs"
SITES = ["24", "25", "27", "28", "30", "31", "32", "33", "36"]
OWNER = "buffedlizard55-lab"


def gh_json(endpoint: str) -> dict:
    result = subprocess.run(["gh", "api", endpoint], check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def gh_blob(sha_endpoint: str) -> bytes:
    result = subprocess.run(["gh", "api", sha_endpoint, "--jq", ".content"], check=True,
                            capture_output=True, text=True)
    return base64.b64decode("".join(result.stdout.split()))


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    for site in SITES:
        repo = f"{OWNER}/GEMSDOE{site}"
        tree = gh_json(f"repos/{repo}/git/trees/HEAD?recursive=1")["tree"]
        tifs = [t for t in tree if t["type"] == "blob" and t["path"].startswith("docs/")
                and t["path"].lower().endswith(".tif")]
        site_dir = OUT / f"GEMSDOE{site}"
        site_dir.mkdir(parents=True, exist_ok=True)
        for item in sorted(tifs, key=lambda t: t["path"]):
            name = Path(item["path"]).name
            # Disambiguate identical file names inside one repo (e.g. docs/downloads/blocked/).
            folder = site_dir
            if item["path"].count("/") > 2:
                folder = site_dir / Path(item["path"]).parent.name
                folder.mkdir(parents=True, exist_ok=True)
            destination = folder / name
            data = gh_blob(f"repos/{repo}/git/blobs/{item['sha']}")
            destination.write_bytes(data)
            manifest.append({
                "site": f"GEMSDOE{site}", "repo": repo, "path": item["path"],
                "local": str(destination.relative_to(ROOT)), "blob_sha": item["sha"],
                "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest(),
            })
            print(f"{repo} {item['path']} {len(data)}", file=sys.stderr)
    (OUT / "manifest.json").write_text(json.dumps({"schema": 1, "sites": SITES, "files": manifest},
                                                  indent=1) + "\n")
    print(f"wrote {len(manifest)} files", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
