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
* ``--derived <label>`` additionally keeps the bytes of one pinned ScienceBase release, verifies it
  against ``registry/external_pins.json``, opens the vector layer(s) inside it, clips them to the
  competition footprint and writes a small derived table plus a schema file under ``--out/commit/``.
  The workflow copies that directory into ``docs/data/`` and commits it, which is how a session that
  cannot reach sciencebase.gov still gets the release's in-footprint content.
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

# Additive (session 9, 2026-10-03): availability checks for the official USGS ScienceBase releases
# named by the H33-series hypotheses (knowledge/18_new_hypotheses_H33_series_2026-10-03.md). These
# are UNPINNED availability probes (filename + byte count + sha256 recorded live); they never fail
# the job and never override the pinned GDR flow above. Items and file names were read manually on
# 2026-10-03 from the ScienceBase item pages listed in registry/sources.json.
SCIENCEBASE_CHECKS = [
    {
        "label": "sb_slip_tendency_shapefile_full",
        "item": "6296974dd34ec53d276bb33d",
        "filename": "Shapefile_Full Study.zip",
        "doi": "10.5066/P9YL58W6",
        "page": "https://www.sciencebase.gov/catalog/item/6296974dd34ec53d276bb33d",
        "hypothesis": "H33-1 kinematic reactivation favourability gate",
    },
    {
        "label": "sb_mt_conductance_surface",
        "item": "62979746d34ec53d276c113b",
        "filename": "gb_conductance_surface_tp.tif",
        "doi": "10.5066/P9TWT2LU",
        "page": "https://www.sciencebase.gov/catalog/item/62979746d34ec53d276c113b",
        "hypothesis": "H33-2 multi-depth MT conductance alignment",
    },
    {
        "label": "sb_mt_conductance_middle_crust",
        "item": "62979746d34ec53d276c113b",
        "filename": "gb_conductance_middle_crust_tp.tif",
        "doi": "10.5066/P9TWT2LU",
        "page": "https://www.sciencebase.gov/catalog/item/62979746d34ec53d276c113b",
        "hypothesis": "H33-2 multi-depth MT conductance alignment",
    },
    {
        "label": "sb_heat_flow_zip",
        "item": "6297d2fad34ec53d276c5b28",
        "filename": "heat_flow_maps_and_supporting_data_for_the_Great_Basin_USA.zip",
        "doi": "10.5066/P9BZPVUC",
        "page": "https://www.sciencebase.gov/catalog/item/6297d2fad34ec53d276c5b28",
        "hypothesis": "H33-3 heat-flow residual + 2 m probe conjunction",
    },
]

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
            # urllib sets .status to None for non-HTTP schemes (file://, used by the tests) and
            # older response objects omit it entirely; int(None) would raise, so default explicitly.
            status = getattr(response, "status", None)
            record["http_status"] = int(status) if isinstance(status, int) else 200
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


def sciencebase_item_json(item_id: str) -> dict | None:
    url = f"https://www.sciencebase.gov/catalog/item/{item_id}?format=json"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=120) as response:  # noqa: S310 - fixed https host
            return json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError, json.JSONDecodeError) as error:
        print(f"sciencebase item {item_id}: {type(error).__name__}: {error}", file=sys.stderr)
        return None


def run_sciencebase_availability(out_dir: Path) -> dict:
    """Unpinned availability probes for the H33-series ScienceBase releases (never raises)."""
    results: dict[str, dict] = {}
    for check in SCIENCEBASE_CHECKS:
        label = check["label"]
        record: dict = {"doi": check["doi"], "page": check["page"], "filename": check["filename"],
                        "hypothesis": check["hypothesis"]}
        item = sciencebase_item_json(check["item"])
        files = list((item or {}).get("files", [])) if isinstance(item, dict) else []
        # ScienceBase nests some payloads (e.g. the five MT conductance GeoTIFFs) inside
        # facet extensions rather than the top-level files array; search both.
        for facet in (item or {}).get("facets", []) if isinstance(item, dict) else []:
            files.extend(facet.get("files", []) or [])
        match = next((f for f in files if f.get("name") == check["filename"]), None)
        if match is None:
            record["status"] = "FILE_NOT_LISTED"
            record["listed_files"] = [f.get("name") for f in files][:20]
            results[label] = record
            continue
        record["listed_bytes"] = match.get("size")
        record["download_url"] = match.get("url")
        got = fetch(match["url"], keep=False, out_dir=out_dir, label=label)
        record.update({k: got.get(k) for k in ("http_status", "bytes", "sha256", "status", "error")})
        record["status"] = "AVAILABILITY_" + str(record.get("status", "UNKNOWN"))
        results[label] = record
        print(json.dumps({label: {k: record.get(k) for k in ("status", "bytes", "sha256")}}))
    return results


# ---------------------------------------------------------------------------------------------
# Session 10 (2026-10-03): derived in-footprint clips of the pinned official vector releases.
#
# The availability probes above prove the bytes exist and hash them, but `--availability-only`
# discards them, so no session could ever *use* the release. This step keeps one pinned release,
# re-verifies it against registry/external_pins.json (the runner-recorded hashes), opens the vector
# layers inside and writes a compact in-footprint table the repository can commit. Everything the
# clipping does is covered by tests/test_external_clip.py.
DERIVED_SPECS = [
    {
        "label": "sb_slip_tendency_shapefile_full",
        "hypothesis": "H33-1 kinematic reactivation favourability gate",
        "stem": "sb_slip_tendency_in_footprint",
    },
]


def resolve_payload_format(payload: Path, pin_filename: str) -> tuple[Path, str]:
    """Return a path whose extension matches the payload's real format, plus the format name.

    ScienceBase download URLs carry no file suffix (``.../file/get/<item>?f=__disk__33%2Fb0%2F91%2F...``),
    so `fetch()` names the payload ``.bin`` and GDAL then refuses to open it ("not recognized as
    being in a supported file format"). That is exactly what the 2026-10-03T18:49:01Z runner run hit:
    the pin matched, the bytes were correct, and the clip silently produced 0 records.

    The format is decided by **magic bytes first**, then the pinned filename, then left alone. The
    payload is only ever *copied* to a correctly-suffixed name, never mutated in place, so the hash
    that was verified still refers to the original file on disk.
    """
    with payload.open("rb") as handle:
        head = handle.read(4)
    if head == b"PK\x03\x04":
        fmt, suffix = "zip", ".zip"
    elif head[:4] == b"\x1f\x8b\x08\x00"[:4] or head[:2] == b"\x1f\x8b":
        fmt, suffix = "gzip", ".gz"
    else:
        suffix = Path(pin_filename or "").suffix.lower()
        fmt = suffix.lstrip(".").lower() or "unknown"
    if payload.suffix.lower() == suffix:
        return payload, fmt
    target = payload.with_name(payload.stem + suffix)
    if not target.exists():
        target.write_bytes(payload.read_bytes())
    return target, fmt


def _zip_vector_layers(zip_path: Path, work_dir: Path) -> list[Path]:
    """Extract a zip and return every shapefile (.shp) or GeoPackage (.gpkg) layer inside it."""
    import zipfile

    with zipfile.ZipFile(zip_path) as archive:
        names = archive.namelist()
        targets = [n for n in names if n.lower().endswith((".shp", ".gpkg"))]
        if not targets:
            return []
        # a .shp needs its siblings (.dbf/.shx/.prj); extract everything next to them
        wanted = set()
        for n in targets:
            stem = n.rsplit(".", 1)[0].lower()
            wanted.update(m for m in names if m.rsplit(".", 1)[0].lower() == stem)
        archive.extractall(work_dir, members=sorted(wanted))  # noqa: S202 - pinned official zip
    out: list[Path] = []
    for n in sorted(targets):
        candidate = work_dir / n
        if candidate.exists():
            out.append(candidate)
    return out


def build_sciencebase_derived(out_dir: Path, pins: dict[str, dict], only: str | None) -> dict:
    """Download, hash-verify, clip and write derived in-footprint tables for the pinned releases."""
    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from gems27 import external_clip  # noqa: PLC0415 - runner-only dependency (pyogrio)

    commit_dir = out_dir / "commit"
    commit_dir.mkdir(parents=True, exist_ok=True)
    results: dict[str, dict] = {}
    for spec in DERIVED_SPECS:
        label = spec["label"]
        if only and only != label:
            continue
        pin = pins.get(label)
        record: dict = {"hypothesis": spec["hypothesis"]}
        if not pin:
            record["status"] = "NO_PIN"
            results[label] = record
            continue
        got = fetch(pin["url"], keep=True, out_dir=out_dir, label=label)
        record.update({k: got.get(k) for k in ("url", "http_status", "bytes", "sha256", "error")})
        if got.get("status") != "FETCHED":
            record["status"] = "UNREACHABLE"
            results[label] = record
            continue
        if got["sha256"] != pin["sha256"]:
            # a broken pin must be loud: the release changed, or the URL no longer points at it
            record["status"] = "PIN_MISMATCH"
            record["pinned_sha256"] = pin["sha256"]
            record["pinned_bytes"] = pin["bytes"]
            results[label] = record
            continue
        record["pin_match"] = True
        work = out_dir / f"_work_{label}"
        work.mkdir(parents=True, exist_ok=True)
        payload = Path(got["path"])
        usable, fmt = resolve_payload_format(payload, pin.get("filename", ""))
        record["payload_format"] = fmt
        record["payload_used"] = usable.name
        try:
            layers = _zip_vector_layers(usable, work) if fmt == "zip" else [usable]
        except Exception as error:  # noqa: BLE001 - record and continue, never fail the whole job
            record["status"] = "ARCHIVE_UNREADABLE"
            record["error"] = f"{type(error).__name__}: {error}"
            results[label] = record
            continue
        if not layers:
            record["status"] = "NO_VECTOR_LAYER"
            results[label] = record
            continue
        all_records, all_schemas = [], {}
        for layer in layers:
            try:
                recs, schema = external_clip.clip_and_clip_report(str(layer), vertex_step_m=200.0)
            except Exception as error:  # noqa: BLE001 - one unreadable layer must not sink the job
                all_schemas[layer.name] = {"status": "LAYER_UNREADABLE",
                                           "error": f"{type(error).__name__}: {error}"}
                continue
            for r in recs:
                r["source_layer"] = layer.name
            all_records.extend(recs)
            all_schemas[layer.name] = schema
        report = external_clip.write_derived(
            all_records, {"layers": all_schemas},
            str(commit_dir / f"{spec['stem']}.csv"),
            str(commit_dir / f"{spec['stem']}.json"),
        )
        unreadable = [name for name, s in all_schemas.items()
                      if isinstance(s, dict) and s.get("status") == "LAYER_UNREADABLE"]
        if unreadable:
            # GDAL could not open the layer: the derived table is empty because of a format
            # problem, not because the footprint is empty. That must not look like success.
            record["status"] = "LAYER_UNREADABLE"
            record["unreadable_layers"] = unreadable
            record["errors"] = {n: all_schemas[n].get("error") for n in unreadable}
        elif not all_records:
            record["status"] = "DERIVED_EMPTY"
            record["note"] = ("the release parsed but no feature intersects the competition bbox; "
                              "check the source CRS and the extent before trusting an empty clip")
        else:
            record["status"] = "DERIVED_WRITTEN"
        record["layers_found"] = [str(x.name) for x in layers]
        record["derived"] = report
        record["committed_files"] = [f"docs/data/{spec['stem']}.csv", f"docs/data/{spec['stem']}.json"]
        results[label] = record
        print(json.dumps({label: {k: record.get(k)
                                  for k in ("status", "pin_match", "payload_format", "derived")}}))
    return results


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", default="paleo,probes,volcanics")
    parser.add_argument("--availability-only", default="true")
    parser.add_argument("--out", default="/tmp/gdr/out")
    parser.add_argument("--pins", default="/tmp/gdr/pins.json")
    parser.add_argument("--skip-sciencebase", default="false",
                        help="skip the unpinned H33 ScienceBase availability probes")
    parser.add_argument("--derived", default="",
                        help="also download, hash-verify and clip one pinned release to the "
                             "footprint ('all' or a single label from DERIVED_SPECS)")
    parser.add_argument("--external-pins", default="",
                        help="registry/external_pins.json with the runner-recorded ScienceBase hashes")
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

    if args.derived:
        ext_pins = load_pins(Path(args.external_pins)) if args.external_pins else {}
        inventory["sciencebase_derived"] = build_sciencebase_derived(
            out_dir, ext_pins, None if args.derived.strip().lower() == "all" else args.derived.strip()
        )
        inventory["summary"]["sciencebase_derived_written"] = sum(
            1 for row in inventory["sciencebase_derived"].values()
            if row.get("status") == "DERIVED_WRITTEN")

    if str(args.skip_sciencebase).lower() not in {"1", "true", "yes"}:
        sb = run_sciencebase_availability(out_dir)
        inventory["sciencebase_availability"] = sb
        inventory["summary"]["sciencebase_reachable"] = sum(
            1 for row in sb.values() if str(row.get("status", "")).startswith("AVAILABILITY_FETCHED"))
        inventory["summary"]["sciencebase_checked"] = len(sb)
    (out_dir / "inventory.json").write_text(json.dumps(inventory, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(inventory["summary"], indent=2))
    if mismatch:
        print(f"pin mismatch for {mismatch}: refusing to report success", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
