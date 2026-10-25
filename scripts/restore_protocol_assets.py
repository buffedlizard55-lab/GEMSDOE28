#!/usr/bin/env python3
"""Restore the read-only shared template with SHA-256 pins; no scientific run.

Uses the repository's existing GitHub fetch helper. Imports never download code.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27.shared_template import verify_assets  # noqa: E402

try:
    from scripts.restore_data import fetch_to
except ModuleNotFoundError:
    from restore_data import fetch_to


def restore(root: Path, pin: Path) -> dict:
    manifest = json.loads(pin.read_text())
    for entry in manifest["files"]:
        relative = Path(entry["dest"])
        if relative.is_absolute() or ".." in relative.parts:
            raise ValueError("Asset path escapes data directory")
        target = root / "data" / relative
        if not target.resolve().is_relative_to((root / "data").resolve()):
            raise ValueError("Asset symlink escapes data directory")
        if target.is_file() and hashlib.sha256(target.read_bytes()).hexdigest() == entry["sha256"]:
            continue
        partial = target.with_name(target.name + ".restore")
        try:
            fetch_to(entry["repo"], entry["ref"], entry["path"], partial)
            if (partial.stat().st_size != entry["bytes"]
                    or hashlib.sha256(partial.read_bytes()).hexdigest() != entry["sha256"]):
                raise ValueError(f"Shared source pin mismatch: {entry['id']}")
            partial.replace(target)
        finally:
            partial.unlink(missing_ok=True)
    return verify_assets(root, pin)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    args = parser.parse_args(argv)
    pin = ROOT / "registry/protocol_assets.json"
    result = verify_assets(ROOT, pin) if args.verify_only else restore(ROOT, pin)
    print(json.dumps(result, indent=2, allow_nan=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
