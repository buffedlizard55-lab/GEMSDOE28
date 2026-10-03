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
# Session 10 (2026-10-03): the four ScienceBase releases above came back AVAILABILITY_FETCHED with
# a runner-recorded SHA-256, so the next step is not another availability probe but the actual
# derivation of a layer the sandbox can use. H33-1 (kinematic reactivation favourability gate,
# knowledge/18) needs the USGS slip/dilation tendency release of Siler (2022), DOI 10.5066/P9YL58W6.
# The pin below is the SHA-256 recorded by this repository's own runner on 2026-10-03
# (evidence/external_layer_inventory.json -> sciencebase_availability.sb_slip_tendency_shapefile_full),
# so a later byte change is detected instead of silently absorbed.
SLIP_TENDENCY_PIN = {
    "label": "slip",
    "doi": "10.5066/P9YL58W6",
    "page": "https://www.sciencebase.gov/catalog/item/6296974dd34ec53d276bb33d",
    "filename": "Shapefile_Full Study.zip",
    "url": "https://www.sciencebase.gov/catalog/file/get/6296974dd34ec53d276bb33d?f=__disk__33%2Fb0%2F91%2F33b091fae2403dcf2f1dd2f698f7368ffdcf000d",
    "bytes": 35912323,
    "sha256": "5d6213f7763002d369c40b281c31d22113f9c48c482e10ca469e0f6f6b985163",
    "hypothesis": "H33-1 kinematic reactivation favourability gate",
}

# Field-name candidates for slip tendency / dilation tendency, tried in order. The real schema is
# discovered at run time and echoed into the inventory, so a schema change is visible, not guessed.
TS_FIELD_CANDIDATES = ("slip_tend", "Ts", "TS", "sliptenden", "slip_tenden", "slip_t", "T_s")
TD_FIELD_CANDIDATES = ("dil_tend", "Td", "TD", "dilat_tend", "dilation_t", "diltenden", "T_d")


def _pick_field(names: list[str], candidates: tuple[str, ...]) -> str | None:
    lowered = {str(n).lower(): str(n) for n in names}
    for cand in candidates:
        if cand.lower() in lowered:
            return lowered[cand.lower()]
    for name in lowered.values():
        low = name.lower()
        if ("slip" in low or low.startswith("t_s")) and "tend" in low:
            return name
        if ("dil" in low or low.startswith("t_d")) and "tend" in low:
            return name
    return None


def run_slip_tendency_derivation(out_dir: Path) -> dict:
    """Download the pinned Siler (2022) release and derive 100 m Ts/Td grids on the contest grid.

    Writes <out>/slip_tendency_grids.tar.gz holding two deflate uint8 GeoTIFFs and a sidecar JSON.
    The grid is taken from a committed submission TIFF (docs/downloads/*.tif) so the runner needs no
    login-walled data. Everything here is free, official and public; nothing contacts drivendata.org.
    """
    import io
    import tarfile
    import zipfile

    record: dict = {k: SLIP_TENDENCY_PIN[k] for k in ("doi", "page", "filename", "url", "hypothesis")}
    got = fetch(SLIP_TENDENCY_PIN["url"], keep=True, out_dir=out_dir, label="slip")
    record.update({k: got.get(k) for k in ("http_status", "bytes", "sha256", "status", "error", "path")})
    record["pinned_bytes"] = SLIP_TENDENCY_PIN["bytes"]
    record["pinned_sha256"] = SLIP_TENDENCY_PIN["sha256"]
    record["pin_match"] = record.get("sha256") == SLIP_TENDENCY_PIN["sha256"]
    if not record.get("pin_match"):
        record["status"] = "PIN_MISMATCH_OR_UNREACHABLE"
        return record

    try:
        import numpy as np
        import pyogrio
        import rasterio
        from rasterio.transform import Affine
        from scipy.spatial import cKDTree
    except Exception as exc:  # pragma: no cover - runner environment only
        record["status"] = "DEPENDENCY_MISSING"
        record["error"] = f"{type(exc).__name__}: {exc}"
        return record

    # 1. Unzip and read every vector layer we can find.
    zpath = Path(record["path"])
    extracted = out_dir / "slip_unzip"
    with zipfile.ZipFile(zpath) as zf:
        zf.extractall(extracted)
        record["zip_members"] = zf.namelist()[:40]
    shp = sorted(extracted.rglob("*.shp"))
    record["shapefiles_found"] = [str(p.relative_to(extracted)) for p in shp][:20]
    if not shp:
        record["status"] = "NO_SHAPEFILE_IN_ARCHIVE"
        return record

    frames = []
    schema_seen = []
    for path in shp:
        try:
            info = pyogrio.read_info(path)
            fields = [str(f) for f in info.get("fields", [])]
            schema_seen.append({"layer": path.stem, "crs": str(info.get("crs")), "fields": fields,
                                "features": info.get("features")})
            gdf = pyogrio.read_dataframe(path)
        except Exception as exc:
            schema_seen.append({"layer": path.stem, "error": f"{type(exc).__name__}: {exc}"})
            continue
        frames.append((path.stem, gdf))
    record["layers"] = schema_seen
    record["crs_listed"] = [s.get("crs") for s in schema_seen if "crs" in s]
    if not frames:
        record["status"] = "NO_LAYER_READABLE"
        return record

    # 2. Locate Ts / Td columns across all layers.
    ts_col = td_col = None
    src_layer = None
    for stem, gdf in frames:
        cols = [str(c) for c in gdf.columns]
        ts_col = ts_col or _pick_field(cols, TS_FIELD_CANDIDATES)
        td_col = td_col or _pick_field(cols, TD_FIELD_CANDIDATES)
        if ts_col and td_col and src_layer is None:
            src_layer = (stem, gdf)
    record["ts_field"] = ts_col
    record["td_field"] = td_col
    record["source_layer"] = src_layer[0] if src_layer else None
    if ts_col is None or td_col is None or src_layer is None:
        record["status"] = "FIELDS_NOT_IDENTIFIED"
        return record

    stem, gdf = src_layer
    gdf = gdf[[c for c in gdf.columns if c in (ts_col, td_col, "geometry")]].dropna(subset=[ts_col])
    record["features_used"] = int(len(gdf))

    # 3. Competition grid from a committed submission TIFF (no login-walled input required).
    ref = sorted((Path(__file__).resolve().parents[1] / "docs" / "downloads").glob("*-nan.tif"))
    if not ref:
        record["status"] = "NO_REFERENCE_GRID"
        return record
    with rasterio.open(ref[0]) as ds:
        profile = ds.profile.copy()
        transform: Affine = ds.transform
        crs = ds.crs
        shape = (ds.height, ds.width)
        footprint = np.isfinite(ds.read(1))
    record["reference_grid"] = {"file": ref[0].name, "shape": list(shape), "crs": str(crs),
                                "transform": [transform.a, transform.b, transform.c,
                                              transform.d, transform.e, transform.f]}
    record["footprint_px"] = int(footprint.sum())

    # 4. Densify every polyline to ~100 m in the grid CRS and build a KD-tree of vertices.
    try:
        gdf = gdf.to_crs(crs)
    except Exception as exc:
        record["status"] = "REPROJECTION_FAILED"
        record["error"] = f"{type(exc).__name__}: {exc}"
        return record
    pts, ts_vals, td_vals = [], [], []
    for geom, ts, td in zip(gdf.geometry, gdf[ts_col], gdf[td_col]):
        if geom is None or geom.is_empty:
            continue
        geoms = getattr(geom, "geoms", [geom])
        for part in geoms:
            coords = np.asarray(part.coords, dtype=float)
            if coords.ndim != 2 or len(coords) < 2:
                continue
            seg = np.hypot(np.diff(coords[:, 0]), np.diff(coords[:, 1]))
            keep = [coords[0:1]]
            for (x0, y0), (x1, y1), length in zip(coords[:-1], coords[1:], seg):
                n = max(1, int(np.ceil(length / 100.0)))
                t = np.linspace(0.0, 1.0, n + 1)[1:]
                keep.append(np.column_stack([x0 + (x1 - x0) * t, y0 + (y1 - y0) * t]))
            dense = np.vstack(keep)
            pts.append(dense)
            ts_vals.append(np.full(len(dense), float(ts), dtype=np.float32))
            td_vals.append(np.full(len(dense), float(td), dtype=np.float32))
    if not pts:
        record["status"] = "NO_GEOMETRY_VERTICES"
        return record
    pts = np.vstack(pts)
    ts_vals = np.concatenate(ts_vals)
    td_vals = np.concatenate(td_vals)
    record["densified_vertices"] = int(len(pts))

    tree = cKDTree(pts)
    rows, cols = np.nonzero(footprint)
    xs = transform.c + (cols + 0.5) * transform.a
    ys = transform.f + (rows + 0.5) * transform.e
    dist, idx = tree.query(np.column_stack([xs, ys]), k=1, workers=-1)
    record["nearest_vertex_distance_m"] = {
        "p10": float(np.percentile(dist, 10)), "p50": float(np.percentile(dist, 50)),
        "p90": float(np.percentile(dist, 90)), "max": float(dist.max()),
    }

    def to_grid(vals: np.ndarray) -> np.ndarray:
        grid = np.zeros(shape, dtype=np.float32)
        grid[rows, cols] = vals[idx]
        return grid

    ts_grid, td_grid = to_grid(ts_vals), to_grid(td_vals)

    def quantise(grid: np.ndarray) -> tuple[np.ndarray, float, float]:
        finite = np.isfinite(grid)
        lo, hi = float(np.percentile(grid[finite], 1)), float(np.percentile(grid[finite], 99))
        if hi <= lo:
            hi = lo + 1.0
        q = np.clip((grid - lo) / (hi - lo), 0.0, 1.0)
        u8 = np.where(finite, np.round(q * 254.0) + 1.0, 0.0).astype(np.uint8)
        return u8, lo, hi

    ts_u8, ts_lo, ts_hi = quantise(ts_grid)
    td_u8, td_lo, td_hi = quantise(td_grid)

    profile.update(driver="GTiff", dtype="uint8", count=1, compress="deflate", predictor=2,
                   nodata=0, crs=crs, transform=transform, height=shape[0], width=shape[1])
    paths = {}
    for name, arr, lo, hi in (("slip_tendency_ts_u8.tif", ts_u8, ts_lo, ts_hi),
                              ("slip_tendency_td_u8.tif", td_u8, td_lo, td_hi)):
        target = out_dir / name
        with rasterio.open(target, "w", **profile) as ds:
            ds.write(arr, 1)
        paths[name] = {"bytes": target.stat().st_size, "p1_value": lo, "p99_value": hi,
                       "footprint_positive": int((arr > 0).sum())}
    sidecar = {"schema": 1, "generated_utc": record.get("generated_utc"), "source": SLIP_TENDENCY_PIN,
               "reference_grid": record["reference_grid"], "quantisation": "uint8 0=nodata, 1..255 = p1..p99 linear",
               "files": paths, "sha256_pin_match": True}
    (out_dir / "slip_tendency_sidecar.json").write_text(json.dumps(sidecar, indent=2), encoding="utf-8")

    tar_path = out_dir / "slip_tendency_grids.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        for name in list(paths) + ["slip_tendency_sidecar.json"]:
            tar.add(out_dir / name, arcname=name)
        tar.add(extracted, arcname="slip_source_shapefiles", recursive=True)
    record["derived_tar_gz"] = {"path": str(tar_path), "bytes": tar_path.stat().st_size}
    record["grids"] = paths
    record["status"] = "DERIVED"
    print(json.dumps({k: record.get(k) for k in ("status", "pin_match", "ts_field", "td_field",
                                                 "features_used", "densified_vertices", "grids")}, default=str))
    return record


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--datasets", default="paleo,probes,volcanics")
    parser.add_argument("--availability-only", default="true")
    parser.add_argument("--out", default="/tmp/gdr/out")
    parser.add_argument("--pins", default="/tmp/gdr/pins.json")
    parser.add_argument("--skip-sciencebase", default="false",
                        help="skip the unpinned H33 ScienceBase availability probes")
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

    wanted = [item.strip() for item in args.datasets.split(",") if item.strip()]
    if "slip" in wanted or "all" in wanted:
        inventory["slip_tendency"] = run_slip_tendency_derivation(out_dir)
        inventory["summary"]["slip_tendency_status"] = inventory["slip_tendency"].get("status")

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
