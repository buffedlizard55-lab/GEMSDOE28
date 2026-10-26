"""H44-1: potential-field marker-offset / piercing-point realignment (Session 22, S22-MOFR).

Physical hypothesis
--------------------
A continuous basement contact (an intrusive margin, a stratigraphic marker, a dyke edge) produces a
near-linear ridge in the horizontal-gradient magnitude of a potential field. The organizer-supplied
``tmi_hg`` (total-magnetic-intensity horizontal gradient) and ``iso_grav_anom_hg`` (isostatic-gravity
horizontal-gradient) bands are exactly this: the Cordell & Grauch (1985) horizontal-gradient-maximum
edge detector used throughout potential-field geophysics to locate steeply-dipping basement contacts.

A blind, concealed fault -- one the DOE/INGENIOUS Quaternary-fault catalogue has not yet mapped --
still truncates and laterally displaces ("piercing-point" offsets) that ridge, exactly the way a
seismic or outcrop geologist restores a marker horizon across a fault to recover its throw. This
module looks for exactly that geometric signature: a ridge that terminates, and a second, strike-
compatible ridge segment that resumes a short, consistent perpendicular offset away. That is a
DISCONTINUITY-AND-REALIGNMENT test, not a contact-gradient AMPLITUDE feature (H28-1's
``potential_mag_edge_*`` / ``potential_grav_edge_*``, `potential_edges.py`), not a depth/Euler
source-geometry inversion (H31/H32/H36/H38, `euler.py`, `heatflow_euler.py`), not a vertical ridge-
migration-with-continuation-height dip estimator (`migration.ridge_displacement_from_hg_levels`), and
not a relay/step-over rule applied to already-detected or catalogue-derived fault STRANDS
(`newinfo.steppover_links`, which needs a `FaultGraph` built from candidate traces). This module reads
only the two raw potential-field rasters; it is structurally incapable of reproducing a catalogue
trace it has never seen, because it never reads the catalogue.

Known non-fault mimics this test must rule out (and can be fooled by): a change in regional strike at
an intrusive contact corner, interference from a crossing, unrelated contact, a magnetic/gravity
survey flight-line or levelling seam (a straight, grid-aligned artifact), or two unrelated nearby
contacts that happen to satisfy the strike/offset geometry by chance. The strike and perpendicular-
offset-consistency gates below reduce but do not eliminate this risk; see
``knowledge/62_s22_mofr_preregistration.md`` for the full discussion.

Zero catalogue information is read by this module. ``exclude`` is supplied by the caller (e.g. a
``SegmentHoldout`` fold's ``B=2`` off-catalogue collar) purely to blank candidate placement; no
distance-to-catalogue, density, or label feature is computed anywhere below.
"""
from __future__ import annotations

import numpy as np
from scipy.ndimage import convolve, gaussian_filter
from scipy.ndimage import label as ndi_label
from scipy.spatial import cKDTree
from skimage.morphology import skeletonize

from .gravity_bench import GRAV_BAND, SENTINEL, TMI_BAND
from .oof_detector import ridge_nms, ridge_strike_degrees

__all__ = [
    "GRAV_BAND",
    "TMI_BAND",
    "SENTINEL",
    "clean_field",
    "skeleton_and_strike",
    "find_endpoints",
    "match_marker_offsets",
    "marker_offset_detector",
]

# Frozen constants (100 m grid). Gap/offset bounds and the 20 deg strike tolerance mirror the scale
# already used elsewhere in this repo (`oof_detector`'s disclosed 4-direction +/-22.5 deg ridge-strike
# resolution; `newinfo.steppover_links`'s 20 deg parallel-strand tolerance), so this hypothesis is
# judged at the SAME geometric tolerance the repo already treats as defensible, not a newly tuned one.
SIGMA_PX = 3.0            # 300 m smoothing, matching the competition's 300 m DTI kernel
MIN_GAP_PX = 2.0          # >=200 m: excludes a single-pixel ridge notch
MAX_GAP_PX = 15.0         # <=1500 m: within plausible along-strike coherence of one contact
MIN_OFFSET_PX = 1.0       # >=100 m: the grid's own resolution floor
MAX_OFFSET_PX = 8.0       # <=800 m: conservative small-to-moderate normal/strike-slip separation
STRIKE_TOL_DEG = 20.0     # matches `newinfo.steppover_links`
DIRECTION_TOL_DEG = 35.0  # the ridge's own outward heading must roughly aim at its partner


def clean_field(raw: np.ndarray, footprint: np.ndarray) -> np.ndarray:
    """Return a float32 field that is 0 outside the frozen |v|<1e30 validity rule, else the value."""
    arr = np.asarray(raw, dtype=np.float32)
    valid = np.asarray(footprint, dtype=bool) & np.isfinite(arr) & (np.abs(arr) < SENTINEL)
    out = np.where(valid, arr, 0.0).astype(np.float32)
    return out, valid


def skeleton_and_strike(field_abs: np.ndarray, valid: np.ndarray, sigma_px: float = SIGMA_PX):
    """1-px skeletonised ridge of a nonnegative horizontal-gradient field, with per-pixel strike."""
    ridge = ridge_nms(field_abs, valid, sigma=sigma_px)
    skel = skeletonize(ridge)
    strike = ridge_strike_degrees(field_abs, valid, sigma=sigma_px)
    strike = np.where(skel, strike, np.float32("nan"))
    return skel, strike


def find_endpoints(skeleton: np.ndarray) -> np.ndarray:
    """Skeleton pixels with exactly one 8-connected skeleton neighbour (open ridge tips)."""
    kernel = np.ones((3, 3), dtype=np.uint8)
    kernel[1, 1] = 0
    neighbour_count = convolve(skeleton.astype(np.uint8), kernel, mode="constant", cval=0)
    return skeleton & (neighbour_count == 1)


def _outward_direction(skeleton: np.ndarray, endpoints_rc: np.ndarray, reach_px: int = 5) -> np.ndarray:
    """Unit vector at each endpoint pointing away from its own segment (local trend extrapolation)."""
    comp, _ = ndi_label(skeleton, structure=np.ones((3, 3), int))
    directions = np.zeros((len(endpoints_rc), 2), dtype=np.float64)
    for i, (r, c) in enumerate(endpoints_rc):
        cid = comp[r, c]
        r0, r1 = max(0, r - reach_px), min(skeleton.shape[0], r + reach_px + 1)
        c0, c1 = max(0, c - reach_px), min(skeleton.shape[1], c + reach_px + 1)
        rows, cols = np.nonzero(comp[r0:r1, c0:c1] == cid)
        rows, cols = rows + r0, cols + c0
        if len(rows) < 2:
            directions[i] = (0.0, 0.0)
            continue
        vec = np.array([float(r) - rows.mean(), float(c) - cols.mean()])
        norm = np.hypot(*vec)
        directions[i] = vec / norm if norm > 1e-9 else (0.0, 0.0)
    return directions


def _circular_strike_diff(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    d = np.abs(a - b) % 180.0
    return np.minimum(d, 180.0 - d)


def match_marker_offsets(
    skeleton: np.ndarray,
    strike: np.ndarray,
    valid: np.ndarray,
    *,
    min_gap_px: float = MIN_GAP_PX,
    max_gap_px: float = MAX_GAP_PX,
    min_offset_px: float = MIN_OFFSET_PX,
    max_offset_px: float = MAX_OFFSET_PX,
    strike_tol_deg: float = STRIKE_TOL_DEG,
    direction_tol_deg: float = DIRECTION_TOL_DEG,
) -> dict:
    """Pair ridge endpoints whose gap/offset/strike geometry matches a displaced marker.

    Returns a dict with ``bridge_mask`` (bool, the straight connector between every matched pair,
    the modelled fault trace -- the same "shortest breaching segment" convention `newinfo.py` uses
    for catalogue step-overs) and per-pair diagnostics. Pure geometry; reads no catalogue.
    """
    endpoints = find_endpoints(skeleton)
    comp, _ = ndi_label(skeleton, structure=np.ones((3, 3), int))
    rc = np.argwhere(endpoints)
    if len(rc) < 2:
        return {"bridge_mask": np.zeros(skeleton.shape, bool), "n_endpoints": int(len(rc)), "pairs": []}
    directions = _outward_direction(skeleton, rc)
    ids = comp[rc[:, 0], rc[:, 1]]
    strikes = strike[rc[:, 0], rc[:, 1]]
    tree = cKDTree(rc.astype(np.float64))
    search_radius = max_gap_px + max_offset_px
    bridge = np.zeros(skeleton.shape, bool)
    pairs = []
    used = set()
    pair_candidates = tree.query_pairs(r=search_radius, output_type="ndarray")
    for i, j in pair_candidates:
        if ids[i] == ids[j]:
            continue  # same connected ridge strand: not a gap, just internal spacing
        key = (min(i, j), max(i, j))
        if key in used:
            continue
        if not np.isfinite(strikes[i]) or not np.isfinite(strikes[j]):
            continue
        if _circular_strike_diff(np.array([strikes[i]]), np.array([strikes[j]]))[0] > strike_tol_deg:
            continue
        delta = rc[j].astype(np.float64) - rc[i].astype(np.float64)
        dist = float(np.hypot(*delta))
        if dist < 1e-6:
            continue
        theta = np.deg2rad(float((strikes[i] + strikes[j]) / 2.0))
        strike_unit = np.array([np.sin(theta), np.cos(theta)])  # (row, col) unit vector along strike
        normal_unit = np.array([-strike_unit[1], strike_unit[0]])
        along = float(abs(np.dot(delta, strike_unit)))
        perp = float(abs(np.dot(delta, normal_unit)))
        if not (min_gap_px <= along <= max_gap_px):
            continue
        if not (min_offset_px <= perp <= max_offset_px):
            continue
        unit_delta = delta / dist
        cos_i = float(np.dot(directions[i], unit_delta))
        cos_j = float(np.dot(directions[j], -unit_delta))
        angle_tol = np.cos(np.deg2rad(direction_tol_deg))
        if cos_i < angle_tol or cos_j < angle_tol:
            continue
        r0, c0 = rc[i]
        r1, c1 = rc[j]
        n_steps = max(int(round(dist)), 1)
        rr = np.linspace(r0, r1, n_steps + 1).round().astype(int)
        cc = np.linspace(c0, c1, n_steps + 1).round().astype(int)
        inb = (rr >= 0) & (rr < skeleton.shape[0]) & (cc >= 0) & (cc < skeleton.shape[1])
        rr, cc = rr[inb], cc[inb]
        if not (valid[rr, cc].all()):
            continue
        bridge[rr, cc] = True
        used.add(key)
        pairs.append({
            "row0": int(r0), "col0": int(c0), "row1": int(r1), "col1": int(c1),
            "gap_px": along, "offset_px": perp,
            "strike_diff_deg": float(_circular_strike_diff(np.array([strikes[i]]), np.array([strikes[j]]))[0]),
        })
    return {"bridge_mask": bridge, "n_endpoints": int(len(rc)), "pairs": pairs}


def marker_offset_detector(
    tmi_hg: np.ndarray,
    grav_hg: np.ndarray,
    footprint: np.ndarray,
    exclude: np.ndarray,
    *,
    require_both_fields: bool = False,
    sigma_px: float = SIGMA_PX,
) -> dict:
    """Run the marker-offset test on both fields independently (and optionally require both).

    ``exclude`` masks out any pixel a fold must not place a candidate in (e.g. the SegmentHoldout
    B=2 off-catalogue collar); it is applied to candidate placement only, never used to compute the
    ridge/strike geometry itself (so the geometry genuinely never reads the catalogue).
    """
    foot = np.asarray(footprint, bool)
    place_ok = foot & ~np.asarray(exclude, bool)
    mag_clean, mag_valid = clean_field(tmi_hg, foot)
    grav_clean, grav_valid = clean_field(grav_hg, foot)
    mag_abs = np.abs(mag_clean)
    grav_abs = np.abs(grav_clean)

    mag_skel, mag_strike = skeleton_and_strike(mag_abs, mag_valid, sigma_px=sigma_px)
    grav_skel, grav_strike = skeleton_and_strike(grav_abs, grav_valid, sigma_px=sigma_px)
    mag_match = match_marker_offsets(mag_skel, mag_strike, mag_valid & place_ok)
    grav_match = match_marker_offsets(grav_skel, grav_strike, grav_valid & place_ok)

    mag_bridge = mag_match["bridge_mask"] & place_ok
    grav_bridge = grav_match["bridge_mask"] & place_ok
    if require_both_fields:
        # Corroborated variant: keep a magnetic bridge pixel only within 2 px of a gravity bridge
        # pixel and vice versa (independent-instrument agreement), the same corroboration logic
        # already used by `heatflow_euler.select_corroborated_ridge_dots` for a different pair of
        # layers, reused here for consistency rather than inventing a new corroboration rule.
        from scipy.ndimage import distance_transform_edt
        near_grav = distance_transform_edt(~grav_bridge) <= 2.0
        near_mag = distance_transform_edt(~mag_bridge) <= 2.0
        bridge = (mag_bridge & near_grav) | (grav_bridge & near_mag)
    else:
        bridge = mag_bridge | grav_bridge

    support = gaussian_filter(bridge.astype(np.float32), sigma=1.5)
    if support.max() > 0:
        support = support / support.max()
    support = np.where(place_ok, support, 0.0).astype(np.float32)

    return {
        "bridge_mask": bridge,
        "support": support,
        "mag_abs": mag_abs,
        "grav_abs": grav_abs,
        "mag_valid": mag_valid,
        "grav_valid": grav_valid,
        "mag_n_pairs": len(mag_match["pairs"]),
        "grav_n_pairs": len(grav_match["pairs"]),
        "mag_n_endpoints": mag_match["n_endpoints"],
        "grav_n_endpoints": grav_match["n_endpoints"],
        "n_bridge_px": int(bridge.sum()),
    }
