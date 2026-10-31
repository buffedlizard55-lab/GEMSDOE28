#!/usr/bin/env python3
"""Build data/registry_tifs/ (mirror + manifest) from local sparse git clones.

Local-only replacement for scripts/fetch_site_registry.py, which uses the GitHub
REST API. The REST quota for the shared token was exhausted (HTTP 403 rate limit,
2026-10-31), so this session mirrors the nine owner repositories from
data/site_repos/GEMSDOE{24,25,27,28,30,31,32,33,36} (git protocol, blob-filtered,
sparse docs/ checkout at the default-branch HEAD captured when cloned).

Selection, layout and manifest fields replicate fetch_site_registry.py exactly:
every docs/**/*.tif blob, disambiguated by parent folder when the file name
collides inside one repository, with site, repo, path, local, blob_sha (via
`git hash-object`, the same git blob SHA), bytes and sha256 recorded. Files are
owner-published mirrors, NOT organizer receipts.

Run:  python scripts/build_registry_from_clones.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPOS = ROOT / "data" / "site_repos"
OUT = ROOT / "data" / "registry_tifs"
SITES = ["24", "25", "27", "28", "30", "31", "32", "33", "36"]


def git_blob_sha(path: Path) -> str:
    return subprocess.run(
        ["git", "hash-object", str(path)], check=True, capture_output=True, text=True
    ).stdout.strip()


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []
    for site in SITES:
        repo_dir = REPOS / f"GEMSDOE{site}"
        if not (repo_dir / ".git").is_dir():
            raise SystemExit(f"Missing clone: {repo_dir}")
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"], cwd=repo_dir, check=True, capture_output=True, text=True
        ).stdout.strip()
        repo = f"buffedlizard55-lab/GEMSDOE{site}"
        site_dir = OUT / f"GEMSDOE{site}"
        site_dir.mkdir(parents=True, exist_ok=True)
        tifs = sorted(
            p for p in (repo_dir / "docs").rglob("*.tif") if p.is_file()
        )
        for src in tifs:
            rel = src.relative_to(repo_dir).as_posix()
            name = src.name
            # Same rule as fetch_site_registry.py: deeper than docs/<dir>/<file> gets a
            # parent-folder subdirectory so duplicate names never collide.
            destination = site_dir / name
            if rel.count("/") > 2:
                folder = site_dir / src.parent.name
                folder.mkdir(parents=True, exist_ok=True)
                destination = folder / name
            data = src.read_bytes()
            destination.write_bytes(data)
            manifest.append(
                {
                    "site": f"GEMSDOE{site}",
                    "repo": repo,
                    "repo_head": commit,
                    "path": rel,
                    "local": str(destination.relative_to(ROOT)),
                    "blob_sha": git_blob_sha(src),
                    "bytes": len(data),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }
            )
            print(f"{repo} {rel} {len(data)}", file=sys.stderr)
    (OUT / "manifest.json").write_text(
        json.dumps({"schema": 1, "sites": SITES, "files": manifest}, indent=1) + "\n"
    )
    print(f"wrote {len(manifest)} files", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
