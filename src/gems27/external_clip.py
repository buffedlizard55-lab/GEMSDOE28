"""Clip an official external vector release to the competition footprint, losslessly but compactly.

Used by the GitHub-Actions runner bridge (`.github/workflows/fetch-gdr-external-layers.yml`) to turn a
byte-verified official release (e.g. the USGS slip-/dilation-tendency shapefile behind H33-1, DOI
10.5066/P9YL58W6) into a small derived table the repository can commit and every later session can
read without reaching the science host.

Rules this module enforces
--------------------------
* **The footprint is a bbox clip, not a dissolve.** Nothing is merged, snapped or re-typed; the
  caller gets the release's own attributes verbatim plus the geometry it shipped.
* **Coordinates are reprojected to the competition grid CRS (EPSG:32611)** so downstream code can
  compare them with `grid.TRANSFORM` directly.
* **Vertices are thinned to `vertex_step_m`** only along straight runs, and the *endpoints of every
  part are always kept*, so a clipped segment never loses its termination - which is what the
  structural analyses care about. Thinning is recorded in the schema file so a reader can tell a
  thinned trace from the original.
* **No attribute is invented.** Fields absent from the release are absent from the output; the schema
  file lists what was actually found, which is how a reviewer checks that the expected slip-tendency
  and dilation-tendency columns exist before any hypothesis uses them.

This module performs no network access.
"""

from __future__ import annotations

import json
from typing import Any, Iterable

import numpy as np

# Competition grid (src/gems27/grid.py): EPSG:32611, 100 m pixels, this exact envelope.
TARGET_CRS = "EPSG:32611"
BBOX_32611 = (243350.0, 4135550.0, 572550.0, 4508550.0)
PIXEL_M = 100.0


def thin_ring(coords: np.ndarray, step_m: float) -> np.ndarray:
    """Drop interior vertices closer than `step_m` to the last kept one; always keep both endpoints.

    `coords` is an (n, 2) float array. Returns an (m, 2) array with m <= n. Rings are not closed
    here; the caller handles polygons.
    """
    coords = np.asarray(coords, dtype=float)
    if coords.shape[0] <= 2 or step_m <= 0:
        return coords
    keep = [0]
    last = coords[0]
    for i in range(1, coords.shape[0] - 1):
        if float(np.hypot(*(coords[i] - last))) >= step_m:
            keep.append(i)
            last = coords[i]
    keep.append(coords.shape[0] - 1)
    out = coords[keep]
    # a thinned line can collapse to a duplicate pair; drop exact consecutive duplicates
    if out.shape[0] > 1:
        dup = np.all(np.isclose(out[1:], out[:-1], atol=1e-9), axis=1)
        if dup.any():
            out = np.vstack([out[0], out[1:][~dup]])
    return out


def iter_parts(geom: Any) -> Iterable[tuple[str, np.ndarray]]:
    """Yield (kind, (n,2) coords) for every part of a shapely geometry."""
    kind = geom.geom_type
    if kind == "LineString":
        yield "LineString", np.asarray(geom.coords, dtype=float)
    elif kind == "MultiLineString":
        for part in geom.geoms:
            yield "LineString", np.asarray(part.coords, dtype=float)
    elif kind == "Polygon":
        yield "Polygon", np.asarray(geom.exterior.coords, dtype=float)
    elif kind == "MultiPolygon":
        for part in geom.geoms:
            yield "Polygon", np.asarray(part.exterior.coords, dtype=float)
    elif kind == "Point":
        yield "Point", np.asarray([geom.coords[0]], dtype=float)
    elif kind == "MultiPoint":
        for part in geom.geoms:
            yield "Point", np.asarray([part.coords[0]], dtype=float)
    elif kind == "GeometryCollection":
        for part in geom.geoms:
            yield from iter_parts(part)
    # Unknown/empty geometries contribute nothing rather than raising.


def bbox_of_parts(parts: list[tuple[str, np.ndarray]]) -> tuple[float, float, float, float] | None:
    if not parts:
        return None
    xs = np.concatenate([p[1][:, 0] for p in parts])
    ys = np.concatenate([p[1][:, 1] for p in parts])
    return float(xs.min()), float(ys.min()), float(xs.max()), float(ys.max())


def intersects_bbox(bb: tuple[float, float, float, float] | None,
                    bbox: tuple[float, float, float, float]) -> bool:
    if bb is None:
        return False
    return not (bb[2] < bbox[0] or bb[0] > bbox[2] or bb[3] < bbox[1] or bb[1] > bbox[3])


def records_from_frame(
    frame: Any,
    *,
    bbox: tuple[float, float, float, float] = BBOX_32611,
    vertex_step_m: float = 2 * PIXEL_M,
    keep_fields: Iterable[str] | None = None,
) -> tuple[list[dict], dict]:
    """Convert a GeoDataFrame (already in TARGET_CRS) into compact JSON-serialisable records.

    Returns (records, schema). Each record has `fid`, `kinds`, `parts` (list of coordinate lists),
    `length_m`, `n_vertices_raw`, `n_vertices_kept`, and the release's own attribute fields.
    `keep_fields=None` keeps every non-geometry column.
    """
    records: list[dict] = []
    fields_seen: dict[str, str] = {}
    geom_col = frame.geometry.name
    n_features = int(len(frame))
    n_in = 0
    raw_vertices = kept_vertices = 0
    for fid, (_, row) in enumerate(frame.iterrows()):
        geom = row[geom_col]
        if geom is None or geom.is_empty:
            continue
        parts = list(iter_parts(geom))
        if not intersects_bbox(bbox_of_parts(parts), bbox):
            continue
        n_in += 1
        attrs: dict[str, Any] = {}
        for col in frame.columns:
            if col == geom_col:
                continue
            if keep_fields is not None and col not in keep_fields:
                continue
            value = row[col]
            if isinstance(value, np.integer):
                value = int(value)
            elif isinstance(value, np.bool_):
                value = bool(value)
            elif isinstance(value, (float, np.floating)):
                # NoData in an official release arrives as NaN. json.dump would emit the bare token
                # `NaN`, which is not valid JSON, so every non-finite float becomes null.
                value = None if not np.isfinite(float(value)) else float(value)
            elif isinstance(value, int):
                value = int(value)
            elif not isinstance(value, (str, bool, type(None))):
                value = str(value)
            attrs[col] = value
            fields_seen.setdefault(col, type(value).__name__)
        out_parts: list[list[list[float]]] = []
        kinds: list[str] = []
        for kind, coords in parts:
            thinned = thin_ring(coords, vertex_step_m)
            raw_vertices += int(coords.shape[0])
            kept_vertices += int(thinned.shape[0])
            kinds.append(kind)
            out_parts.append([[round(float(x), 2), round(float(y), 2)] for x, y in thinned])
        length_m = 0.0
        for _kind, coords in parts:
            if coords.shape[0] > 1:
                seg = np.diff(coords, axis=0)
                # np.hypot over the two coordinate columns is element-wise, so it must be summed
                length_m += float(np.hypot(seg[:, 0], seg[:, 1]).sum())
        records.append({
            "fid": fid, "kinds": sorted(set(kinds)), "parts": out_parts,
            "length_m": round(length_m, 1),
            "n_vertices_raw": int(sum(p[1].shape[0] for p in parts)),
            "n_vertices_kept": int(sum(len(p) for p in out_parts)),
            **attrs,
        })
    schema = {
        "target_crs": TARGET_CRS,
        "bbox_32611": list(bbox),
        "vertex_step_m": vertex_step_m,
        "n_features_in_source": n_features,
        "n_features_in_bbox": n_in,
        "raw_vertices": raw_vertices,
        "kept_vertices": kept_vertices,
        "vertex_retention": (kept_vertices / raw_vertices) if raw_vertices else None,
        "attribute_fields": fields_seen,
        "note": "Vertices thinned along straight runs only; every part endpoint is retained. "
                "Attributes are copied verbatim from the source release; none are derived.",
    }
    return records, schema


def clip_and_clip_report(
    source_path: str,
    *,
    bbox: tuple[float, float, float, float] = BBOX_32611,
    vertex_step_m: float = 2 * PIXEL_M,
    keep_fields: Iterable[str] | None = None,
) -> tuple[list[dict], dict]:
    """Read one vector file, reproject to TARGET_CRS, clip to `bbox`, return (records, schema).

    Requires pyogrio + shapely (the runner installs them). Kept separate from `records_from_frame`
    so the record/schema logic stays testable without a reader installed.
    """
    import pyogrio

    info = pyogrio.read_info(source_path)
    src_crs = str(info.get("crs") or TARGET_CRS)
    frame = pyogrio.read_dataframe(source_path)
    if frame.crs is not None and frame.crs.to_epsg() != 32611:
        frame = frame.to_crs(TARGET_CRS)
    records, schema = records_from_frame(
        frame, bbox=bbox, vertex_step_m=vertex_step_m, keep_fields=keep_fields
    )
    schema["source_path"] = source_path
    schema["source_crs"] = str(src_crs)
    schema["source_geometry_type"] = str(info.get("geometry_type"))
    schema["source_feature_count"] = int(info.get("features") or 0)
    return records, schema


def write_derived(records: list[dict], schema: dict, csv_path: str, json_path: str) -> dict:
    """Write the derived table as JSON + a flat CSV (one row per part, coordinates WKT-free)."""
    import csv

    Path_json = json_path
    with open(Path_json, "w", encoding="utf-8") as handle:
        json.dump({"schema": schema, "records": records}, handle)
    fields = sorted({k for r in records for k in r if k not in ("parts", "kinds")})
    with open(csv_path, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["fid", "kind", "part_index", "n_vertices", "length_m", *fields])
        for r in records:
            for i, part in enumerate(r["parts"]):
                writer.writerow([
                    r["fid"], r["kinds"][i] if i < len(r["kinds"]) else "", i, len(part),
                    r["length_m"], *[r.get(f, "") for f in fields],
                ])
    return {"csv_path": csv_path, "json_path": json_path, "n_records": len(records),
            "n_parts": int(sum(len(r["parts"]) for r in records))}
