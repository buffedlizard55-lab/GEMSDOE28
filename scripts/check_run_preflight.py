#!/usr/bin/env python3
"""Fail closed before a new geological experiment; never choose a lane or slot.

Exit 0 means prerequisites are configured, not that a candidate is promoted.
Exit 1 means blocked. Exit 2 means invalid/unreadable configuration.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gems27.evidence_json import loads  # noqa: E402
from gems27.grid import FOOTPRINT_PX  # noqa: E402
from gems27.promotion import finite_number  # noqa: E402
from gems27.shared_template import verify_assets  # noqa: E402


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def preflight(config: dict, *, root: Path = ROOT) -> dict:
    failures = []
    lane, assignment = config.get("lane"), config.get("lane_assignment_source")
    if (not isinstance(lane, str) or not lane.strip()
            or not isinstance(assignment, str) or not assignment.strip()):
        failures.append("Missing explicit assigned method lane and assignment source")
    def evidence(spec, reason):
        if not isinstance(spec, dict):
            failures.append(reason)
            return None
        try:
            path = (root / spec["path"]).resolve()
            if not path.is_relative_to(root.resolve()) or file_hash(path) != spec["sha256"]:
                raise ValueError("path or evidence checksum mismatch")
            value = loads(path.read_text())
            if not isinstance(value, dict):
                raise ValueError("evidence must be an object")
            return value
        except (OSError, KeyError, TypeError, ValueError) as exc:
            failures.append(f"{reason}: {exc}")
            return None

    registry = evidence(config.get("required_parallel_registry"),
                        "Missing complete shared parallel-run registry")
    if registry is not None:
        members = registry.get("members")
        if registry.get("complete") is not True or not isinstance(members, list) or not members:
            failures.append("Registry is not declared complete with a nonempty member list")
        else:
            identities = set()
            for member in members:
                if not isinstance(member, dict):
                    failures.append("Malformed registry member")
                    continue
                try:
                    path = (root / member["path"]).resolve()
                    if not path.is_relative_to(root.resolve()):
                        raise ValueError("registry member escapes repository")
                    digest = file_hash(path)
                    if (digest != member["sha256"] or digest in identities):
                        raise ValueError("missing, repeated or mismatched registry member")
                    identities.add(digest)
                except (OSError, KeyError, TypeError, ValueError) as exc:
                    failures.append(f"Invalid registry member: {exc}")
    baseline = evidence(config.get("frozen_protocol_comparable_best"),
                        "Missing frozen current-best result under the same strict protocol")
    if baseline is not None:
        if (baseline.get("label") != "HOLDOUT-DTI"
                or baseline.get("evaluator_version") != "gems-segment-pooled-v1"
                or baseline.get("retrained_per_fold") is not True
                or baseline.get("visible_only_catalogue_features") is not True
                or baseline.get("pooled") is not True
                or baseline.get("whole_segments_buffered") is not True):
            failures.append("Frozen baseline does not certify the same strict retrained protocol")
        score, ci, positives = baseline.get("dti"), baseline.get("ci95"), baseline.get("withheld_positives")
        if (not finite_number(score) or not 0 <= score <= 1 or not isinstance(ci, list)
                or len(ci) != 2 or not all(finite_number(x) for x in ci)
                or not 0 <= ci[0] <= score <= ci[1] <= 1
                or not isinstance(positives, int) or isinstance(positives, bool) or positives < 1):
            failures.append("Frozen baseline lacks a valid DTI, interval or withheld-positive count")
    seconds = config.get("time_cap_seconds")
    if not isinstance(seconds, int) or isinstance(seconds, bool) or not 0 < seconds <= 7200:
        failures.append("Time budget must be a positive integer no greater than two hours")
    count = config.get("experiments_run")
    cap = config.get("experiment_cap")
    if (not isinstance(count, int) or isinstance(count, bool) or not isinstance(cap, int)
            or isinstance(cap, bool) or not 0 <= count < cap <= 3):
        failures.append("Experiment budget exhausted or invalid")
    elapsed = None
    checked_at = datetime.now(timezone.utc)
    try:
        start = config["started_at_utc"]
        if not isinstance(start, str) or not start.endswith("Z"):
            raise ValueError("explicit UTC Z timestamp required")
        elapsed = (checked_at - datetime.fromisoformat(start[:-1] + "+00:00")).total_seconds()
        if elapsed < 0 or (isinstance(seconds, int) and elapsed >= seconds):
            failures.append("Wall-clock budget exhausted or start timestamp is in the future")
    except (KeyError, TypeError, ValueError) as exc:
        failures.append(f"Missing or invalid experiment budget start: {exc}")
    if config.get("slot_selected", False) is not False:
        failures.append("A slot must not be selected by an experiment preflight")
    cache = {}
    try:
        import numpy as np

        array_path = (root / config["cached_features"]).resolve()
        metadata_path = (root / config["cached_features_metadata"]).resolve()
        if not all(p.is_relative_to(root.resolve()) for p in (array_path, metadata_path)):
            raise ValueError("cache path escapes repository")
        meta = loads(metadata_path.read_text())
        if not isinstance(meta, dict):
            raise ValueError("Cached feature metadata must be an object")
        array = np.load(array_path, mmap_mode="r", allow_pickle=False)
        if not isinstance(array, np.ndarray):
            array.close()
            raise ValueError("Cached features must be a single .npy array")
        cache = {"path": str(array_path.relative_to(root)), "sha256": file_hash(array_path)}
        names = meta.get("names")
        if (cache["sha256"] != meta.get("sha256") or array.dtype != np.dtype("float32")
                or array.ndim != 2 or array.shape[0] != FOOTPRINT_PX or array.shape[1] != 32
                or list(array.shape) != meta.get("shape") or not isinstance(names, list)
                or len(names) != 32 or not all(isinstance(x, str) for x in names)
                or len(set(names)) != 32):
            failures.append("Cached feature checksum, shape, dtype or band contract mismatch")
        # Bound temporary memory while checking every value, not a random sample.
        for start in range(0, array.shape[0], 65536):
            if not np.isfinite(array[start:start + 65536]).all():
                failures.append("Cached feature stack contains NaN or infinity")
                break
    except (OSError, EOFError, KeyError, TypeError, ValueError) as exc:
        failures.append(f"Cached feature stack unavailable: {exc}")
    try:
        shared = verify_assets(root)
        failures.extend(shared["failures"])
    except (OSError, KeyError, TypeError, ValueError) as exc:
        shared = {"passed": False}
        failures.append(f"Shared tools unavailable: {exc}")
    # This is deliberately a prerequisites check, not validation of a prediction.
    return {"status": "BLOCKED" if failures else "PREREQUISITES_PRESENT",
            "checked_at_utc": checked_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "elapsed_seconds": elapsed,
            "time_cap_seconds": seconds if isinstance(seconds, int) and not isinstance(seconds, bool) else None,
            "experiment_allowed": not failures, "failures": failures,
            "cached_features": cache, "shared_template": shared,
            "submission_ready": False, "slot_selected": False,
            "scope": "No model, no scientific evaluation, no raster emission, no weekly cap or slot decision"}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "registry/current_session.json")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args(argv)
    try:
        config = loads(args.config.read_text())
        if not isinstance(config, dict):
            raise ValueError("Session configuration must be an object")
        result = preflight(config)
    except (OSError, TypeError, ValueError) as exc:
        print(json.dumps({"status": "BLOCKED", "experiment_allowed": False,
                          "submission_ready": False, "failures": [str(exc)]}, allow_nan=False))
        return 2
    output = json.dumps(result, indent=2, allow_nan=False) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(output)
    print(output, end="")
    return 0 if result["experiment_allowed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
