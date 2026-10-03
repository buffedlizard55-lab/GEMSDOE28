#!/usr/bin/env python3
"""Audit local evidence for H31-1 screen/confirmation seed reuse; no model is fit."""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"
OUTPUT = EVIDENCE / "h31_1_seed_reuse_audit.json"
PROTOCOL = ROOT / "knowledge" / "12_preregistration_H31-1_euler.md"
RANGES = {"screen": list(range(160, 170)), "confirmation": list(range(170, 180))}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def find_seeds(value) -> set[int]:
    found: set[int] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key in {"seed", "seeds", "holdout_seeds", "used_seeds"}:
                if isinstance(item, int) and not isinstance(item, bool):
                    found.add(item)
                elif isinstance(item, list):
                    found.update(x for x in item if isinstance(x, int) and not isinstance(x, bool))
            found.update(find_seeds(item))
    elif isinstance(value, list):
        for item in value:
            found.update(find_seeds(item))
    return found


def protocol_commit() -> str:
    relative = PROTOCOL.relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "log", "-1", "--format=%H", "--", relative],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    commit = result.stdout.strip()
    if not commit:
        return ""
    committed = subprocess.run(
        ["git", "show", f"{commit}:{relative}"], cwd=ROOT, check=True, capture_output=True
    ).stdout
    return commit if hashlib.sha256(committed).hexdigest() == sha256_file(PROTOCOL) else ""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="print audit status without writing JSON")
    args = parser.parse_args()
    screen_path = EVIDENCE / "h31_1_euler_screen.json"
    confirm_path = EVIDENCE / "h31_1_euler_confirm.json"
    used_by_file: dict[str, list[int]] = {}
    scanned: dict[str, str] = {}
    unreadable: list[str] = []
    for path in sorted(EVIDENCE.glob("*.json")):
        if path == OUTPUT:
            continue
        scanned[path.name] = sha256_file(path)
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            unreadable.append(path.name)
            continue
        seeds = sorted(find_seeds(record))
        relevant = sorted(set(seeds).intersection(range(100, 180)))
        if relevant:
            used_by_file[path.name] = relevant

    used = sorted({seed for values in used_by_file.values() for seed in values})
    stage_status = {}
    unexpected = {}
    invalid_stage_records = []
    for stage, stage_range in RANGES.items():
        final_path = screen_path if stage == "screen" else confirm_path
        claim_path = final_path.with_name(final_path.stem + ".started.json")
        expected = set(stage_range)
        final_observed = set(used_by_file.get(final_path.name, []))
        claim_observed = set(used_by_file.get(claim_path.name, []))
        for path, observed in ((final_path, final_observed), (claim_path, claim_observed)):
            if path.exists() and observed != expected:
                invalid_stage_records.append(path.name)
                unexpected[path.name] = sorted(observed)
        if final_path.exists() and final_observed == expected:
            stage_status[stage] = "CONSUMED"
        elif claim_path.exists() and claim_observed == expected:
            stage_status[stage] = "INCOMPLETE"
        elif not final_path.exists() and not claim_path.exists():
            stage_status[stage] = "UNUSED"
        else:
            stage_status[stage] = "INVALID"
        allowed_files = {final_path.name, claim_path.name}
        for file_name, values in used_by_file.items():
            overlap = set(values).intersection(expected)
            if overlap and file_name not in allowed_files:
                unexpected[file_name] = sorted(set(unexpected.get(file_name, [])) | overlap)
    protocol_revision = protocol_commit()
    status = "PASS" if not unexpected and not unreadable and not invalid_stage_records and protocol_revision else "FAIL"
    git_log = subprocess.run(
        ["git", "log", "--all", "-5", "--format=%H %s"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    report = {
        "schema": 1,
        "checked_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "status": status,
        "scope": "local repository evidence only; cannot rule out undocumented seed use in unsearched external/sibling workspaces",
        "network_access": "none",
        "audit_script_sha256": sha256_file(Path(__file__).resolve()),
        "protocol": {
            "path": str(PROTOCOL.relative_to(ROOT)),
            "sha256": sha256_file(PROTOCOL),
            "last_modifying_commit": protocol_revision,
            "matches_committed_bytes": bool(protocol_revision),
        },
        "git_history_review": {"shallow": subprocess.run(
            ["git", "rev-parse", "--is-shallow-repository"], cwd=ROOT, check=True,
            capture_output=True, text=True).stdout.strip() == "true", "recent_commits": git_log},
        "planned_ranges": RANGES,
        "range_status": stage_status,
        "previously_used_holdout_seeds": [seed for seed in used if 100 <= seed <= 159],
        "observed_by_evidence_file": used_by_file,
        "evidence_json_sha256_scanned": scanned,
        "unexpected_collisions": unexpected,
        "unreadable_evidence_json": unreadable,
        "invalid_stage_records": invalid_stage_records,
        "decision": "Seeds 160-169 are reserved for one frozen screen; 170-179 are confirmation-only after an unchanged passing screen.",
    }
    report["sha256"] = None
    report["sha256"] = hashlib.sha256(json.dumps(report, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    if not args.check:
        OUTPUT.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "screen": stage_status["screen"], "confirmation": stage_status["confirmation"],
                      "prior_seed_count": len(report["previously_used_holdout_seeds"]),
                      "unexpected_collisions": unexpected, "output": str(OUTPUT)}, indent=2))
    return 0 if status == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
