#!/usr/bin/env python3
"""Prepare (but do not execute) the frozen H38-1 single-use seed claim.

Run only after all protocol/code/tests/data-support artifacts are final. It refuses an existing claim
or result, and runs a repository-local collision scan; it does not start a model fit.
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
sys.path.insert(0, str(ROOT / "scripts"))
from audit_holdout_seed_range import audit  # noqa: E402

SEEDS = list(range(265, 270))
BRANCH = "arena/01a10412-gemsdoe28"
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
    PREREG,
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
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def runtime_versions() -> dict[str, str]:
    packages = {"numpy": "numpy", "scipy": "scipy", "scikit_learn": "scikit-learn", "rasterio": "rasterio"}
    return {"python": sys.version.split()[0], **{key: metadata.version(name) for key, name in packages.items()}}


def atomic_json(path: Path, record: dict) -> None:
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    os.replace(temp, path)


def prepare() -> dict:
    if git("branch", "--show-current") != BRANCH:
        raise RuntimeError(f"wrong branch; session branch must remain {BRANCH}")
    if git("status", "--porcelain"):
        raise RuntimeError("seed claim may be prepared only from the clean committed protocol freeze")
    if CLAIM.exists() or SEED_AUDIT.exists() or RAW.exists() or RESULT.exists():
        raise FileExistsError("H38-1 claim/audit/output already exists; refusing to reserve or run twice")
    if not SUFFICIENCY.is_file() or not CANDIDATE.is_file() or not BENCHMARK.is_file():
        raise FileNotFoundError("candidate support, candidate CSV, or H37-3 benchmark missing")
    suff = json.loads(SUFFICIENCY.read_text(encoding="utf-8"))
    if suff.get("status") != "READY" or suff.get("clusters", {}).get("selected_clusters") != 140:
        raise RuntimeError("frozen candidate support must be READY with exactly 140 rows")
    outputs = suff.get("outputs", {})
    csv_meta = outputs.get("candidate_csv", {})
    if sha256_file(CANDIDATE) != csv_meta.get("sha256") or csv_meta.get("row_count") != 140:
        raise RuntimeError("candidate CSV bytes/count differ from the sufficiency audit")
    if outputs.get("builder_sha256") != sha256_file(ROOT / "scripts" / "build_h38_1_candidate_clusters.py"):
        raise RuntimeError("sufficiency audit was not produced by the frozen candidate builder")
    if outputs.get("module_sha256") != sha256_file(ROOT / "src" / "gems27" / "h38_1.py"):
        raise RuntimeError("sufficiency audit was not produced by the frozen H38-1 module")
    expected_inputs = {
        "template": ROOT / "data" / "sample_submission.tif",
        "training_features": ROOT / "data" / "training_features.tif",
        "lidar_descriptors": ROOT / "data" / "lidar_scarp_features_u8.tif",
        "euler_clusters": ROOT / "evidence" / "h31_1_euler_clusters.csv",
    }
    recorded_inputs = suff.get("inputs", {})
    for key, path in expected_inputs.items():
        if recorded_inputs.get(key, {}).get("sha256") != sha256_file(path):
            raise RuntimeError(f"sufficiency audit input hash mismatch: {key}")
    baseline = json.loads(BENCHMARK.read_text(encoding="utf-8")).get("euler_licence", {})
    if abs(float(baseline.get("mean_delta_dti_licence_vs_base", -1)) - 0.0005763894914862378) > 1e-15:
        raise RuntimeError("H37-3 far-field benchmark differs from the predeclared C5 value")

    code_hashes = {}
    for rel in CODE_PATHS:
        path = ROOT / rel
        if not path.is_file():
            raise FileNotFoundError(f"frozen code file missing: {rel}")
        code_hashes[rel] = sha256_file(path)
    input_hashes = {}
    for rel in INPUT_PATHS:
        path = ROOT / rel
        if not path.is_file():
            raise FileNotFoundError(f"frozen input file missing: {rel}")
        input_hashes[rel] = sha256_file(path)

    prereg_hash = code_hashes[PREREG]
    claim = {
        "schema": 1,
        "status": "RESERVED",
        "arm_name": ARM_NAME,
        "preregistration": PREREG,
        "preregistration_sha256": prereg_hash,
        "seeds": SEEDS,
        "reserved_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "protocol_commit": git("rev-parse", "HEAD"),
        "protocol_branch": git("branch", "--show-current"),
        "scope": "repository-local single-use claim; external/unpublished seed use remains unknown",
        "runtime_versions": runtime_versions(),
        "candidate_csv": "evidence/h38_1_candidate_clusters.csv",
        "candidate_csv_sha256": sha256_file(CANDIDATE),
        "candidate_count": 140,
        "sufficiency_audit": "evidence/h38_1_sufficiency_audit.json",
        "sufficiency_audit_sha256": sha256_file(SUFFICIENCY),
        "pre_run_seed_audit": "evidence/h38_1_seed_audit_pre_run.json",
        "input_sha256": input_hashes,
        "code_sha256": code_hashes,
        "baseline": {
            "path": "evidence/losfo_h37_3_licence.json",
            "sha256": sha256_file(BENCHMARK),
            "mean_delta_dti_licence_vs_base": baseline["mean_delta_dti_licence_vs_base"],
            "live_bar": 0.0548,
        },
        "result_paths": {
            "raw": "evidence/losfo_h38_1_raw.json",
            "summary": "evidence/h38_1_holdout.json",
        },
        "holdout_started": False,
        "submission_slot_used": False,
    }
    atomic_json(CLAIM, claim)

    scan = audit(265, 269, CLAIM, SEED_AUDIT)
    SEED_AUDIT.parent.mkdir(parents=True, exist_ok=True)
    SEED_AUDIT.write_text(json.dumps(scan, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    claim["input_sha256"]["evidence/h38_1_seed_audit_pre_run.json"] = sha256_file(SEED_AUDIT)
    atomic_json(CLAIM, claim)
    if scan.get("status") != "PASS_LOCAL_SCAN":
        raise RuntimeError("local seed collision audit failed; the report and blocked reservation were preserved, but no holdout started")
    return claim


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    claim = prepare()
    print(json.dumps({
        "status": claim["status"],
        "seeds": claim["seeds"],
        "scope": claim["scope"],
        "candidate_count": claim["candidate_count"],
        "claim": str(CLAIM.relative_to(ROOT)),
        "seed_audit": str(SEED_AUDIT.relative_to(ROOT)),
        "holdout_started": False,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
