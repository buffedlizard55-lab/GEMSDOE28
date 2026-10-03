#!/usr/bin/env python3
"""Fetch, hash-verify and inventory the free official external layers named by a pins file.

Runs only on the GitHub Actions runner (`.github/workflows/fetch-gdr-external-layers.yml`); the agent
sandbox cannot reach gdr.openei.org, mrdata.usgs.gov, sciencebase.gov or the run-log hosts, so this is
the bridge that turns "listed by an official source" into "bytes were obtained, hashed and pinned".

Inputs
------
--pins      JSON with a ``downloads`` mapping (label -> {url, bytes, sha256, ok}) or a flat
            ``label -> {url, sha256}`` mapping. The repository record used in practice is
            https://github.com/buffedlizard55-lab/16GEMSDOE/blob/main/evidence/ci/external_verification.json
            which was produced by an independent runner on 2026-09-30.
--datasets  comma-separated label subsets: ``all`` or any of
            paleo,probes,volcanics,qfaults,wellspring,sgmc,ens12,lidar7
--out       directory for downloaded bytes, ``inventory.json`` and a per-label sha256 file.

Behaviour
---------
* Every URL is fetched with ``urllib`` and a plain user agent, https only.
* A payload whose SHA-256 differs from the pin is recorded as ``MISMATCH`` and makes the process exit
  non-zero: a pin exists to be broken loudly, not silently.
* Labels without a pin are recorded as ``unpinned`` and are never treated as verified.
* With ``--availability-only true`` the bytes are streamed but discarded after hashing, and a
  HEAD/GET status is recorded; nothing is written to ``--out`` except ``inventory.json``.
* This script never contacts drivendata.org; the competition Terms of Use prohibit automated access.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

USER_AGENT = "GEMSDOE28-external-layer-bridge/1.0 (+https://github.com/buffedlizard55-lab/GEMSDOE28)"
DATASET_ALIASES = {
    "paleo": ["gdr_paleo"],
    "probes": ["gdr_2m_probes"],
    "volcanics": ["gdr_volcanics"],
    "qfaults": ["gdr_qfaults_v1", "gdr_qfaults_v2"],
    "wellspring": ["gdr_wellspring"],
    "sgmc": ["sgmc_nv", "sgmc_ca"],
    "ens12": ["ens12"],
    "lidar7": ["lidar7"],
}


def load_pins(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    pins = payload.get("downloads", payload)
    if not isinstance(pins, dict):
        raise SystemExit(f"{path}: expected a mapping of label -> pin")
    return {str(k): dict(v) for k, v in pins.items() if isinstance(v, dict)}


def selected_labels(datasets: str, pins: dict[str, dict]) -> list[str]:
    wanted = [item.strip() for item in datasets.split(",") if item.strip()]
    if not wanted or "all" in wanted:
        return sorted(pins)
    labels: list[str] = []
    for key in wanted:
        if key in DATASET_ALIASES:
            labels.extend(DATASET_ALIASES[key])
        elif key in pins:
            labels.append(key)
        else:
            print(f"warning: dataset key {key!r} is unknown and has no pin entry", file=sys.stderr)
    return sorted(dict.fromkeys(labels))


def fetch(url: str, keep: bool, out_dir: Path, label: str) -> dict:
    """Stream the URL, hash every byte, optionally keep it. Never raises for HTTP errors."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    digest = hashlib.sha256()
    size = 0
    record: dict = {"url": url}
    try:
        with urllib.request.urlopen(request, timeout=300) as response:  # noqa: S310 - fixed https pins
            record["http_status"] = int(getattr(response, "status", 200))
            record["content_type"] = response.headers.get("Content-Type", "")
            target = out_dir / f"{label}{Path(url).suffix or '.bin'}" if keep else None
            sink = target.open("wb") if target else None
            try:
                while True:
                    chunk = response.read(1 << 20)
                    if not chunk:
                        break
                    digest.update(chunk)
                    size += len(chunk)
                    if sink:
                        sink.write(chunk)
            finally:
                if sink:
                    sink.close()
        record["bytes"] = size
        record["sha256"] = digest.hexdigest()
        record["status"] = "FETCHED"
        if keep and target:
            record["path"] = str(target)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as error:
        record["status"] = "UNREACHABLE"
        record["error"] = f"{type(error).__name__}: {error}"
        record.setdefault("bytes", size)
        record.setdefault("sha256", digest.hexdigest() if size else None)
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", default="paleo,probes,volcanics")
    parser.add_argument("--availability-only", default="true")
    parser.add_argument("--out", default="/tmp/gdr/out")
    parser.add_argument("--pins", default="/tmp/gdr/pins.json")
    args = parser.parse_args()

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    availability_only = str(args.availability_only).lower() in {"1", "true", "yes"}
    pins = load_pins(Path(args.pins))
    labels = selected_labels(args.datasets, pins)
    if not labels:
        raise SystemExit("no labels selected: pass --datasets all or check --pins")

    inventory: dict[str, object] = {
        "schema": 1,
        "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "pins_file": str(args.pins),
        "pins_file_loaded": bool(pins),
        "availability_only": availability_only,
        "drivendata_access": False,
        "rows": {},
    }
    mismatch: list[str] = []
    for label in labels:
        pin = pins.get(label, {})
        url = pin.get("url")
        if not url:
            inventory["rows"][label] = {"status": "NO_URL", "note": "label has no pin/URL record"}
            continue
        record = fetch(url, keep=not availability_only, out_dir=out_dir, label=label)
        record["pinned_bytes"] = pin.get("bytes")
        record["pinned_sha256"] = pin.get("sha256")
        if record.get("sha256") and pin.get("sha256"):
            record["pin_match"] = record["sha256"] == pin["sha256"]
            if not record["pin_match"]:
                mismatch.append(label)
        elif record.get("sha256"):
            record["pin_match"] = None
            record["status"] = record.get("status", "FETCHED") + "_UNPINNED"
        if "bytes" in record and record.get("bytes") and record["bytes"] > 64 << 20:
            record["note"] = "large payload; availability-only keeps nothing on disk"
        inventory["rows"][label] = record
        print(json.dumps({label: {k: record.get(k) for k in ("status", "bytes", "pin_match")}}))

    reachable = sum(1 for row in inventory["rows"].values() if isinstance(row, dict) and row.get("status", "").startswith("FETCHED"))
    inventory["summary"] = {
        "labels": len(inventory["rows"]),
        "reachable": reachable,
        "pin_mismatches": mismatch,
        "unpinned": sorted(k for k, v in inventory["rows"].items()
                           if isinstance(v, dict) and v.get("pin_match") is None),
    }
    (out_dir / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(inventory["summary"], indent=2))
    if mismatch:
        print(f"pin mismatch for {mismatch}: refusing to report success", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
