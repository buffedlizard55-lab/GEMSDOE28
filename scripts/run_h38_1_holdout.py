#!/usr/bin/env python3
"""Run the single-use, preregistered H38-1 LOSFO panel on seeds 265–269.

The wrapper refuses an uncommitted/dirty freeze, a changed input/code hash, an existing output, a
wrong seed claim, or a failed local seed-collision audit. Once it marks the claim RUNNING, all five
seeds are burned even if the harness or analyzer exits with an error.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BRANCH = "arena/01a10412-gemsdoe28"
SEEDS = list(range(265, 270))
ARM_NAME = "H38-1 shallow Euler × gravity × low-relief licence"
PREREG = "knowledge/38_preregistration_H38-1.md"
CLAIM = ROOT / "evidence" / "h38_1_holdout.started.json"
SEED_AUDIT = ROOT / "evidence" / "h38_1_seed_audit_pre_run.json"
SUFFICIENCY = ROOT / "evidence" / "h38_1_sufficiency_audit.json"
CANDIDATE = ROOT / "evidence" / "h38_1_candidate_clusters.csv"
BENCHMARK = ROOT / "evidence" / "losfo_h37_3_licence.json"
RAW = ROOT / "evidence" / "losfo_h38_1_raw.json"
RESULT = ROOT / "evidence" / "h38_1_holdout.json"

CODE_PATHS = (
    "knowledge/38_preregistration_H38-1.md",
    "src/gems27/h38_1.py",
    "scripts/build_h38_1_candidate_clusters.py",
    "scripts/run_losfo_harness.py",
    "src/gems27/losfo.py",
    "src/gems27/oof_detector.py",
    "src/gems27/metric.py",
    "src/gems27/thinning.py",
    "src/gems27/holdout.py",
    "src/gems27/grid.py",
    "src/gems27/paths.py",
    "src/gems27/packing.py",
    "scripts/audit_holdout_seed_range.py",
    "scripts/prepare_h38_1_seed_claim.py",
    "scripts/run_h38_1_holdout.py",
    "scripts/analyze_h38_1_holdout.py",
    "tests/test_h38_1.py",
    "tests/test_h38_1_holdout.py",
    "tests/test_seed_range_audit.py",
)
INPUT_PATHS = (
    "data/sample_submission.tif",
    "data/labels.tif",
    "data/training_features.tif",
    "data/lidar_scarp_features_u8.tif",
    "data/prepared/features.npy",
    "data/prepared/features.json",
    "evidence/h31_1_euler_clusters.csv",
    "evidence/h38_1_candidate_clusters.csv",
    "evidence/h38_1_sufficiency_audit.json",
    "evidence/losfo_h37_3_licence.json",
    "evidence/h38_1_seed_audit_pre_run.json",
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_json(path: Path, record: dict) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def runtime_versions() -> dict[str, str]:
    packages = {"numpy": "numpy", "scipy": "scipy", "scikit_learn": "scikit-learn", "rasterio": "rasterio"}
    return {"python": sys.version.split()[0], **{key: metadata.version(name) for key, name in packages.items()}}


def verify_preflight() -> dict:
    if git("branch", "--show-current") != BRANCH:
        raise RuntimeError(f"wrong branch; session branch must remain {BRANCH}")
    dirty = git("status", "--porcelain")
    if dirty:
        raise RuntimeError("working tree is not clean; commit the frozen protocol and all inputs first")
    if not CLAIM.is_file():
        raise FileNotFoundError(f"single-use claim is missing: {CLAIM}")
    claim = json.loads(CLAIM.read_text(encoding="utf-8"))
    if claim.get("status") != "RESERVED" or claim.get("seeds") != SEEDS:
        raise RuntimeError("claim is not a fresh reservation for exactly seeds 265–269")
    if claim.get("arm_name") != ARM_NAME or claim.get("preregistration") != PREREG:
        raise RuntimeError("claim points to a different arm or protocol")
    if claim.get("protocol_branch") != BRANCH or not claim.get("protocol_commit"):
        raise RuntimeError("claim lacks the correct committed protocol-freeze identity")
    ancestor = subprocess.run(
        ["git", "merge-base", "--is-ancestor", claim["protocol_commit"], "HEAD"],
        cwd=ROOT, check=False,
    )
    if ancestor.returncode != 0:
        raise RuntimeError("protocol freeze commit is not an ancestor of the reservation commit")
    if claim.get("runtime_versions") != runtime_versions():
        raise RuntimeError("Python or numerical-library versions differ from the committed claim")
    if any(path.exists() for path in (RAW, RESULT)):
        raise RuntimeError("holdout output already exists; refusing a second use of the seed range")

    for rel in CODE_PATHS:
        path = ROOT / rel
        if not path.is_file() or sha256_file(path) != claim.get("code_sha256", {}).get(rel):
            raise RuntimeError(f"frozen code hash mismatch: {rel}")
    for rel in INPUT_PATHS:
        path = ROOT / rel
        if not path.is_file() or sha256_file(path) != claim.get("input_sha256", {}).get(rel):
            raise RuntimeError(f"frozen input hash mismatch: {rel}")

    audit = json.loads(SEED_AUDIT.read_text(encoding="utf-8"))
    if audit.get("status") != "PASS_LOCAL_SCAN" or audit.get("target_range") != SEEDS:
        raise RuntimeError("local seed-collision audit is not a PASS for exactly 265–269")
    if audit.get("claim", {}).get("status") != "RESERVED" or not audit.get("claim", {}).get("valid_for_exact_range"):
        raise RuntimeError("pre-run seed audit does not validate the single-use reservation")
    suff = json.loads(SUFFICIENCY.read_text(encoding="utf-8"))
    if suff.get("status") != "READY" or suff.get("clusters", {}).get("selected_clusters") != 140:
        raise RuntimeError("candidate sufficiency is not the frozen 140-row READY list")
    if suff.get("outputs", {}).get("candidate_csv", {}).get("sha256") != claim.get("candidate_csv_sha256"):
        raise RuntimeError("candidate CSV hash differs from the sufficiency audit")
    if claim.get("candidate_count") != 140:
        raise RuntimeError("candidate count differs from the frozen preregistration")

    benchmark = json.loads(BENCHMARK.read_text(encoding="utf-8"))
    euler = benchmark.get("euler_licence", {})
    if not euler or euler.get("mean_delta_dti_licence_vs_base") != claim.get("baseline", {}).get("mean_delta_dti_licence_vs_base"):
        raise RuntimeError("H37-3 benchmark does not match the single-use claim")
    return claim


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--claim", type=Path, default=CLAIM)
    args = parser.parse_args()
    if args.claim.resolve() != CLAIM.resolve():
        raise SystemExit("only the preregistered single-use claim path is permitted")
    claim = verify_preflight()
    started = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    claim["status"] = "RUNNING"
    claim["holdout_started"] = True
    claim["started_utc"] = started
    claim["run_commit"] = git("rev-parse", "HEAD")
    claim["run_branch"] = git("branch", "--show-current")
    atomic_json(CLAIM, claim)

    runner = [
        sys.executable, str(ROOT / "scripts" / "run_losfo_harness.py"),
        "--seeds", "265-269",
        "--thin-d", "2.8",
        "--euler-licence", str(CANDIDATE.relative_to(ROOT)),
        "--licence-name", ARM_NAME,
        "--licence-preregistration", PREREG,
        "--out", str(RAW.relative_to(ROOT)),
    ]
    run = subprocess.run(runner, cwd=ROOT, check=False)
    if run.returncode != 0:
        claim.update({
            "status": "FAILED",
            "finished_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "runner_exit_code": run.returncode,
            "seed_range_burned": True,
        })
        atomic_json(CLAIM, claim)
        return run.returncode

    analyzer = [
        sys.executable, str(ROOT / "scripts" / "analyze_h38_1_holdout.py"),
        "--raw", str(RAW.relative_to(ROOT)),
        "--claim", str(CLAIM.relative_to(ROOT)),
        "--sufficiency-audit", str(SUFFICIENCY.relative_to(ROOT)),
        "--benchmark", str(BENCHMARK.relative_to(ROOT)),
        "--out", str(RESULT.relative_to(ROOT)),
    ]
    analysis = subprocess.run(analyzer, cwd=ROOT, check=False)
    if analysis.returncode != 0:
        claim.update({
            "status": "FAILED",
            "finished_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "analyzer_exit_code": analysis.returncode,
            "seed_range_burned": True,
            "raw_result_sha256": sha256_file(RAW) if RAW.exists() else None,
        })
        atomic_json(CLAIM, claim)
        return analysis.returncode

    result_record = json.loads(RESULT.read_text(encoding="utf-8"))
    claim.update({
        "status": "CONSUMED",
        "finished_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "seed_range_burned": True,
        "raw_result_path": str(RAW.relative_to(ROOT)),
        "raw_result_sha256": sha256_file(RAW),
        "summary_result_path": str(RESULT.relative_to(ROOT)),
        "summary_result_sha256": sha256_file(RESULT),
        "promotable": bool(result_record.get("promotable")),
    })
    atomic_json(CLAIM, claim)
    print(f"single-use seed claim consumed; promotable={claim['promotable']}; no submission slot was used")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
