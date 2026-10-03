#!/usr/bin/env python3
"""Restore the hash-pinned competition inputs from *local clones* of the owner mirrors.

Why this exists
---------------
`scripts/restore_data.py` downloads the pinned mirror objects over HTTPS from
`raw.githubusercontent.com`. Some sandboxes and restricted runners cannot reach that host
(observed here: `curl` to raw.githubusercontent.com fails while `https://github.com` and
`git clone` both work). A `git clone` of the same public mirror repository yields the *same
bytes*, so this script performs the restore from a local checkout instead of over HTTP.

It never contacts DrivenData and never downloads anything itself.

Usage
-----
    # one-time, on any machine with git network access (public repos, no credentials):
    git clone --depth 1 --filter=blob:none --no-checkout https://github.com/buffedlizard55-lab/GEMSDOE.git   /tmp/gems-mirrors/GEMSDOE
    git clone --depth 1 --filter=blob:none --no-checkout https://github.com/buffedlizard55-lab/GEMSDOE24.git /tmp/gems-mirrors/GEMSDOE24
    # then materialise the needed paths inside each clone:
    (cd /tmp/gems-mirrors/GEMSDOE   && git sparse-checkout init --cone && git sparse-checkout set data/bridge && git checkout)
    (cd /tmp/gems-mirrors/GEMSDOE24 && git sparse-checkout init --cone && git sparse-checkout set data/bridge data/external inputs docs/downloads && git checkout)

    python scripts/restore_from_checkout.py --mirror-root /tmp/gems-mirrors --data-dir "$PWD/data"

Every restored object is verified against `registry/data_manifest.json` by byte count and
SHA-256; a mismatch is a hard failure and no partial file is left behind.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = REPO / "registry" / "data_manifest.json"
CHUNK = 1 << 20


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(CHUNK), b""):
            h.update(block)
    return h.hexdigest()


def assemble(parts: list[Path], dest: Path) -> None:
    tmp = dest.with_suffix(dest.suffix + ".part")
    with tmp.open("wb") as out:
        for part in parts:
            with part.open("rb") as fh:
                shutil.copyfileobj(fh, out, CHUNK)
    tmp.replace(dest)


def repo_dir_name(repo: str) -> str:
    return repo.split("/")[-1]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--mirror-root", required=True, type=Path,
                    help="directory containing checkouts named after the mirror repos")
    ap.add_argument("--data-dir", required=True, type=Path)
    ap.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    ap.add_argument("--out", type=Path, default=REPO / "evidence" / "restore_audit_checkout.json")
    args = ap.parse_args()

    manifest = json.loads(args.manifest.read_text())
    args.data_dir.mkdir(parents=True, exist_ok=True)

    report: dict[str, object] = {
        "schema": 1,
        "method": "local git checkout of the public owner mirror repositories",
        "manifest": str(args.manifest.relative_to(REPO)) if args.manifest.is_relative_to(REPO) else str(args.manifest),
        "mirror_root": str(args.mirror_root),
        "provenance_warning": (
            "Owner-supplied public GitHub mirrors, integrity-pinned here but NOT "
            "organizer-authenticated. A hash match proves equality to the registered mirror."
        ),
        "files": [],
    }
    failures: list[str] = []

    for entry in manifest["files"]:
        root = args.mirror_root / repo_dir_name(entry["repo"])
        ref = entry.get("ref")
        rec: dict[str, object] = {
            "id": entry["id"],
            "dest": entry["dest"],
            "repo": entry["repo"],
            "ref": ref,
            "expected_sha256": entry["sha256"],
            "expected_bytes": entry["bytes"],
        }
        if not root.exists():
            rec["status"] = "mirror-checkout-missing"
            failures.append(f"{entry['id']}: {root} not found")
            report["files"].append(rec)
            continue

        head = None
        git_head = root / ".git" / "HEAD"
        if git_head.exists():
            head = git_head.read_text().strip()
        rec["checkout_head"] = head
        if ref and head and ref not in head and not head.startswith("ref:"):
            rec["head_note"] = "checkout HEAD is not the pinned ref; hash check still decides"

        parts = entry.get("parts")
        dest = args.data_dir / entry["dest"]
        if parts:
            src_parts = [root / p for p in parts]
            missing = [str(p) for p in src_parts if not p.exists()]
            if missing:
                rec["status"] = "parts-missing"
                rec["missing"] = missing
                failures.append(f"{entry['id']}: {len(missing)} part(s) missing")
                report["files"].append(rec)
                continue
            assemble(src_parts, dest)
        else:
            src = root / entry["path"]
            if not src.exists():
                rec["status"] = "source-missing"
                rec["missing"] = str(src)
                failures.append(f"{entry['id']}: {src} not found")
                report["files"].append(rec)
                continue
            shutil.copyfile(src, dest)

        got_bytes = dest.stat().st_size
        got_sha = sha256_file(dest)
        rec["got_bytes"] = got_bytes
        rec["got_sha256"] = got_sha
        ok = got_bytes == entry["bytes"] and got_sha == entry["sha256"]
        rec["status"] = "verified" if ok else "HASH-MISMATCH"
        if not ok:
            failures.append(f"{entry['id']}: bytes/sha mismatch")
        report["files"].append(rec)

    report["n_files"] = len(report["files"])
    report["n_verified"] = sum(1 for f in report["files"] if f.get("status") == "verified")
    report["failures"] = failures
    report["ok"] = not failures
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=1) + "\n")

    print(f"restored {report['n_verified']}/{report['n_files']} objects into {args.data_dir}")
    for f in report["files"]:
        print(f"  {f['status']:>18}  {f['id']:<28} -> {f['dest']}")
    if failures:
        print("FAILURES:", *failures, sep="\n  ")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
