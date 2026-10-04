#!/usr/bin/env python3
"""Audit local JSON evidence for references to a reserved fresh holdout seed range.

This is a repository-local collision check, not a claim about unpublished owner work or external
repositories. The target interval and claim file are supplied explicitly so the report cannot infer
that a range is globally unused from an old, narrower audit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
SEED_KEYS = {
    "seed", "seeds", "holdout_seeds", "used_seeds", "reserved_seeds",
    "seed_range", "seeds_range", "seed_start", "seed_end",
}
_RANGE = re.compile(r"^\s*(\d+)\s*(?:-|–|—|to)\s*(\d+)\s*$", re.IGNORECASE)


def _seed_items(value) -> list[int]:
    """Normalize supported numeric/list/range encodings used by local evidence records."""
    if isinstance(value, int) and not isinstance(value, bool):
        return [value]
    if isinstance(value, list):
        return [seed for item in value for seed in _seed_items(item)]
    if isinstance(value, str):
        if value.strip().isdigit():
            return [int(value.strip())]
        match = _RANGE.match(value)
        if match:
            lo, hi = map(int, match.groups())
            return list(range(lo, hi + 1)) if hi >= lo else [lo, hi]
    return []


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def seed_values(value, path: str = "") -> list[dict]:
    found = []
    if isinstance(value, dict):
        for key, child in value.items():
            key_path = f"{path}/{key}"
            if key in SEED_KEYS:
                found.extend({"path": key_path, "seed": item} for item in _seed_items(child))
            found.extend(seed_values(child, key_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            found.extend(seed_values(child, f"{path}/{index}"))
    return found


def git_text(*args: str) -> str:
    result = subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True)
    return result.stdout.strip()


def audit(start: int, end: int, claim_path: Path | None, output_path: Path) -> dict:
    if end < start:
        raise ValueError("seed interval end must be >= start")
    expected = set(range(start, end + 1))
    references: list[dict] = []
    unreadable = []
    scanned = {}
    for path in sorted(EVIDENCE.glob("*.json")):
        if path.resolve() == output_path.resolve() or (claim_path and path.resolve() == claim_path.resolve()):
            continue
        digest = sha256_file(path)
        scanned[path.name] = digest
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            unreadable.append(path.name)
            continue
        values = [entry for entry in seed_values(record) if entry["seed"] in expected]
        if values:
            references.append({"file": path.name, "sha256": digest, "seed_references": values})

    claim = None
    claim_valid = claim_path is None
    claim_name = None
    if claim_path is not None:
        claim_name = claim_path.name
        if claim_path.exists():
            claim_data = json.loads(claim_path.read_text(encoding="utf-8"))
            claimed = claim_data.get("seeds")
            claim_valid = (claimed == list(range(start, end + 1))
                           and claim_data.get("status") in {"RESERVED", "RUNNING", "CONSUMED", "FAILED"})
            claim = {
                "path": str(claim_path.relative_to(ROOT)) if claim_path.is_relative_to(ROOT) else str(claim_path),
                "status": claim_data.get("status"),
                "seeds": claimed,
                "valid_for_exact_range": claim_valid,
            }
        else:
            claim_valid = False
            claim = {"path": str(claim_path), "exists": False, "valid_for_exact_range": False}

    collisions = [row for row in references if row["file"] != claim_name]
    legacy_path = EVIDENCE / "h31_1_seed_reuse_audit.json"
    legacy_scope = None
    if legacy_path.exists():
        try:
            legacy = json.loads(legacy_path.read_text(encoding="utf-8"))
            legacy_scope = {
                "path": legacy_path.relative_to(ROOT).as_posix(),
                "checked_utc": legacy.get("checked_utc"),
                "preregistered_ranges": legacy.get("preregistered_ranges", {}),
                "covers_target_range": any(
                    start >= min(spec.get("range", [10**9])) and end <= max(spec.get("range", [-1]))
                    for spec in legacy.get("preregistered_ranges", {}).values()
                ),
                "limitation": "historical H31 audit only; not an authority for seeds outside its declared ranges",
            }
        except (OSError, json.JSONDecodeError):
            legacy_scope = {"path": legacy_path.name, "unreadable": True}

    record = {
        "schema": 1,
        "checked_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": "PASS_LOCAL_SCAN" if not collisions and not unreadable and claim_valid else "FAIL",
        "scope": "local evidence/*.json only; an empty scan cannot establish availability in owner workspaces, other repositories, or unpublished runs",
        "network_access": "none",
        "target_range": list(range(start, end + 1)),
        "claim": claim,
        "legacy_audit_scope": legacy_scope,
        "local_seed_references": references,
        "collisions_excluding_exact_claim": collisions,
        "unreadable_json": unreadable,
        "scanned_evidence_sha256": scanned,
        "repository": {
            "branch": git_text("branch", "--show-current"),
            "head": git_text("rev-parse", "HEAD"),
            "shallow": git_text("rev-parse", "--is-shallow-repository") == "true",
        },
        "interpretation": "The local range is collision-free in this scan. Reserve/use only with the limitation above; do not describe it as comprehensively free.",
    }
    record["sha256"] = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, required=True)
    parser.add_argument("--end", type=int, required=True)
    parser.add_argument("--claim", type=Path, default=None)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    report = audit(args.start, args.end, args.claim, args.out)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": report["status"],
        "target_range": report["target_range"],
        "references": len(report["local_seed_references"]),
        "collisions": len(report["collisions_excluding_exact_claim"]),
        "claim": report["claim"],
        "out": str(args.out),
    }, indent=2))
    return 0 if report["status"] == "PASS_LOCAL_SCAN" else 2


if __name__ == "__main__":
    raise SystemExit(main())
