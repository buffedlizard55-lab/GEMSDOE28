"""H33-1 kinematic reactivation favourability score.

Label-free per-dot favourability built from the USGS slip-/dilation-tendency release
(Siler 2022, *Slip and dilation tendency analysis of Quaternary faults, Great Basin*,
DOI 10.5066/P9YL58W6), clipped to the competition footprint by the runner bridge
(`docs/data/sb_slip_tendency_in_footprint.json`).

This module implements section 2 of `knowledge/19_preregistration_H33-1.md` exactly as frozen
there. Nothing in it is tuned after the fact: the search radii, the strike tolerance, the number
of borrowed neighbours and the neutral default are all constants taken from that document.

**Units.** The preregistration states every radius in grid pixels, but the clipped trace is stored
in EPSG:32611 *metres*. Mixing the two is the single easiest way to make this score silently find
nothing: at a 10 "pixel" radius interpreted as metres the search discards essentially every
segment, and `fav` coverage comes back 0.0. So the trace is converted to **fractional grid pixel
coordinates once, at load time**, via `grid.xy_to_rc`, and every distance in this module is
thereafter in pixels. There is no metre-valued quantity below this docstring.

Two conventions are established from the data rather than assumed:

* The source `Strike` attribute is a geographic azimuth (0 = north, clockwise, 0-360). Verified
  against the geometric azimuth of the clipped EPSG:32611 vertices on 4,000 segments: median
  absolute difference 4.27 deg, p90 6.35 deg. Strike is nevertheless computed geometrically here
  from the pixel-space chord, so the score does not depend on that attribute's convention at all.
* Strike is a *line* direction, folded into [0, 180) before comparison, and the angular difference
  is the circular difference on that half-circle (max 90 deg, not 180).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

from . import grid

# --- frozen constants (knowledge/19 section 2), all in grid pixels -----------------------------
STRIKE_SEARCH_PX = 5.0   # dot strike is taken from the nearest OOF ridge within 500 m
SEGMENT_MAX_PX = 10.0    # a dot borrows Ts/Td only from segments within 1 km
STRIKE_TOL_DEG = 20.0    # and only from segments oriented within 20 degrees of the dot
N_NEIGHBOURS = 3         # inverse-distance weighting over at most 3 such segments
TRACE_STEP_PX = 0.5      # sample each segment every half pixel so long segments are still found
NEUTRAL = float("nan")   # a dot with no qualifying neighbour is never pruned, never protected


def circular_strike_difference(a: np.ndarray | float, b: np.ndarray | float) -> np.ndarray:
    """Absolute difference between two line strikes, folded onto [0, 90] degrees.

    Strikes are undirected, so 179 and 1 are 2 degrees apart, not 178.
    """
    d = np.abs(np.asarray(a, float) - np.asarray(b, float)) % 180.0
    return np.minimum(d, 180.0 - d)


def geometric_strike(colrow: np.ndarray) -> float | None:
    """Strike in [0, 180) of the chord joining a part's endpoints, or None if degenerate.

    `colrow` is (col, row) in pixel space. Grid north is -row, so the geographic azimuth is
    measured from -row towards +col.
    """
    if len(colrow) < 2:
        return None
    dv = np.asarray(colrow[-1], float) - np.asarray(colrow[0], float)
    if not np.isfinite(dv).all() or np.hypot(dv[0], dv[1]) < 1e-9:
        return None
    return float(np.degrees(np.arctan2(dv[0], -dv[1])) % 180.0)


def densify(colrow: np.ndarray, step_px: float = TRACE_STEP_PX) -> np.ndarray:
    """Insert vertices every `step_px` pixels so a 6 km segment is not represented by two points."""
    p = np.asarray(colrow, float)
    if len(p) < 2:
        return p
    seg = np.diff(p, axis=0)
    lengths = np.hypot(seg[:, 0], seg[:, 1])
    out = [p[0]]
    for i, length in enumerate(lengths):
        n = max(1, int(np.ceil(length / step_px))) if length > 0 else 1
        t = np.arange(1, n + 1)[:, None] / n
        out.append(p[i][None, :] + t * seg[i][None, :])
    return np.vstack(out)


def _part_to_pixel(part: np.ndarray) -> np.ndarray:
    """EPSG:32611 metre vertices to (col, row) pixel coordinates."""
    p = np.asarray(part, float)
    rows, cols = grid.xy_to_rc(p[:, 0], p[:, 1])
    return np.column_stack([cols, rows])


def load_segments(clip_path: str | Path) -> dict[str, np.ndarray]:
    """Read the committed in-footprint clip into flat pixel-space arrays.

    Segments missing a finite `TS` or `TD` are dropped: a borrow needs both, and silently
    substituting 0.0 would make an absent measurement look like the least favourable value.
    """
    doc = json.loads(Path(clip_path).read_text())
    records = doc["records"]
    trace, owner, ts, td, strike = [], [], [], [], []
    dropped = 0
    for rec in records:
        s, t = rec.get("TS"), rec.get("TD")
        if s is None or t is None or not (np.isfinite(s) and np.isfinite(t)):
            dropped += 1
            continue
        for part in rec["parts"]:
            px = _part_to_pixel(np.asarray(part, float))
            if len(px) < 2:
                continue
            st = geometric_strike(px)
            if st is None:
                src = rec.get("Strike")
                st = float(src) % 180.0 if src is not None and np.isfinite(src) else NEUTRAL
            dense = densify(px)
            trace.append(dense)
            owner.append(np.full(len(dense), len(strike), dtype=np.int32))
            strike.append(st)
            ts.append(float(s))
            td.append(float(t))
    if not trace:
        raise ValueError(f"{clip_path} contains no usable slip/dilation-tendency segments")
    return {
        "trace_colrow": np.vstack(trace),
        "trace_owner": np.concatenate(owner),
        "strike": np.asarray(strike, float),
        "TS": np.asarray(ts, float),
        "TD": np.asarray(td, float),
        "n_segments": len(strike),
        "n_records": len(records),
        "n_records_dropped": dropped,
    }


def percentile_rank(values: np.ndarray, reference: np.ndarray) -> np.ndarray:
    """Rank of each value within `reference`, in [0, 1]. NaN in, NaN out."""
    ref = np.sort(reference[np.isfinite(reference)])
    out = np.full(len(values), np.nan)
    ok = np.isfinite(values)
    if ok.any() and len(ref):
        out[ok] = np.searchsorted(ref, values[ok], side="right") / len(ref)
    return out


def borrow_kinematics(
    dot_colrow: np.ndarray,
    dot_strike: np.ndarray,
    seg: dict[str, np.ndarray],
) -> tuple[np.ndarray, np.ndarray]:
    """Inverse-distance borrow of (TS, TD) from similarly oriented nearby segments.

    Both arguments are (col, row) in the *full-grid* pixel frame. Returns (TS, TD) with NaN where
    no segment qualified within `SEGMENT_MAX_PX` at a strike within `STRIKE_TOL_DEG`.
    """
    n = len(dot_colrow)
    ts_out = np.full(n, np.nan)
    td_out = np.full(n, np.nan)
    if n == 0:
        return ts_out, td_out
    tree = cKDTree(seg["trace_colrow"])
    query = np.asarray(dot_colrow, float)
    for i, hits in enumerate(tree.query_ball_point(query, r=SEGMENT_MAX_PX)):
        if not hits:
            continue
        hits = np.asarray(hits, dtype=int)
        seg_id = seg["trace_owner"][hits]
        dstrike = circular_strike_difference(dot_strike[i], seg["strike"][seg_id])
        keep = np.isfinite(dstrike) & (dstrike <= STRIKE_TOL_DEG)
        if not keep.any():
            continue
        seg_id = seg_id[keep]
        dist = np.hypot(*(query[i][None, :] - seg["trace_colrow"][hits][keep]).T)
        # one entry per segment: the closest qualifying trace point of each
        order = np.argsort(dist)
        seg_id, dist = seg_id[order], dist[order]
        _, first = np.unique(seg_id, return_index=True)
        seg_id, dist = seg_id[first][:N_NEIGHBOURS], dist[first][:N_NEIGHBOURS]
        w = 1.0 / np.maximum(dist, 0.01)  # 1 m floor so a coincident vertex cannot dominate
        w = w / w.sum()
        ts_out[i] = float((w * seg["TS"][seg_id]).sum())
        td_out[i] = float((w * seg["TD"][seg_id]).sum())
    return ts_out, td_out


def favourability(
    dot_colrow: np.ndarray,
    dot_strike: np.ndarray,
    seg: dict[str, np.ndarray],
    dot_geod: np.ndarray,
    geod_reference: np.ndarray,
) -> tuple[np.ndarray, float]:
    """Frozen `fav` score: mean percentile rank of (Ts, Td) times the strain percentile rank.

    All three percentile ranks use *fixed, seed-independent* footprint-wide reference
    distributions, so a dot's score does not move when the fold or the seed changes and the
    deciles stay comparable across cells. Returns (fav, coverage_fraction).
    """
    ts, td = borrow_kinematics(dot_colrow, dot_strike, seg)
    p_ts = percentile_rank(ts, seg["TS"])
    p_td = percentile_rank(td, seg["TD"])
    p_strain = percentile_rank(np.asarray(dot_geod, float), geod_reference)
    stacked = np.column_stack([p_ts, p_td])
    finite = np.isfinite(stacked)
    # Manual mean-of-available so an all-NaN row yields NaN (the neutral default this document
    # specifies: a dot with no qualifying neighbour is never pruned) without nanmean's warning.
    counts = finite.sum(axis=1)
    sums = np.where(finite, stacked, 0.0).sum(axis=1)
    kinematic = np.where(counts > 0, sums / np.maximum(counts, 1), np.nan)
    fav = kinematic * p_strain
    coverage = float(np.isfinite(fav).mean()) if len(fav) else 0.0
    return fav, coverage
