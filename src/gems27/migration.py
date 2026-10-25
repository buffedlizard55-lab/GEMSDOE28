"""Continuation-height ridge migration bands (H40-1, Session 16; knowledge/49).

A dipping subsurface boundary (fault, contact, dike) does not project to the same
map position at every observation height: upward-continuing the field by h attenuates
short wavelengths as exp(-|k|h) (Blakely 1995), and the horizontal-gradient (HG)
ridge of a dipping edge shifts laterally, systematically, in the dip direction.
A vertical edge does not move; a shallow noise ridge vanishes instead of moving.
H39-1 (depthslice.py) encoded only HG *magnitudes* and a persistence ratio at each
pixel. This module encodes the ridge *geometry* depthslice never used:

  {tmi,grav}_signed_migration_px  signed distance the shallow HG ridge travels to
      reach the 2 km HG ridge, projected on the local field-gradient normal
      (px, clipped [-12, 12]), Gaussian-smoothed (sigma=2) along the shallow ridge
      and 0 away from any ridge corridor.
  {tmi,grav}_migration_coherence mean over the 0/1/2 km levels of exp(-d_l / 2),
      d_l = distance (px) to that level's HG ridge. In [0, 1]; 1 on a ridge that
      exists at every level.

Label-free: no function here reads labels or any catalogue-derived raster.
Named non-fault mimic: a dipping lithologic contact / mafic dike migrates
identically with zero Quaternary slip (knowledge/49).
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

from . import depthslice, oof_detector

BAND_NAMES = [
    "tmi_signed_migration_px",
    "tmi_migration_coherence",
    "grav_signed_migration_px",
    "grav_migration_coherence",
]
LEVELS_M = (0.0, 1000.0, 2000.0)
CLIP_PX = 12.0


def ridge_at(hg: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """1-px HG ridge mask via the repo's shared directional NMS (not a fork)."""
    return oof_detector.ridge_nms(np.asarray(hg, dtype=np.float32), np.asarray(valid, bool), sigma=1.0)


def migration_bands_from_hg_levels(
    hg_levels: list[np.ndarray], grad_normal: tuple[np.ndarray, np.ndarray], valid: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """(signed_migration_px, coherence) from HG magnitudes at increasing heights.

    `grad_normal` is (gy, gx) of the mid-level field (unit normal is derived here).
    Deterministic; pure function of its inputs (synthetic-tested in tests/test_migration.py).
    """
    if len(hg_levels) < 2:
        raise ValueError("need at least two continuation levels")
    valid = np.asarray(valid, bool)
    ridges = [ridge_at(h, valid) for h in hg_levels]
    dists = [distance_transform_edt(~r) for r in ridges]
    coherence = np.mean([np.exp(-d / 2.0) for d in dists], axis=0)

    shallow, deep = ridges[0], ridges[-1]
    # Nearest deep-ridge pixel for every shallow-ridge pixel (EDT indices on ~deep).
    inds = distance_transform_edt(~deep, return_distances=False, return_indices=True)
    ys, xs = np.nonzero(shallow & valid)
    vy = inds[0][ys, xs].astype(np.float64) - ys
    vx = inds[1][ys, xs].astype(np.float64) - xs
    gy, gx = (np.asarray(g, dtype=np.float64) for g in grad_normal)
    nrm = np.hypot(gx[ys, xs], gy[ys, xs])
    ok = nrm > 0
    signed_vals = np.zeros(len(ys))
    signed_vals[ok] = (vx[ok] * gx[ys[ok], xs[ok]] + vy[ok] * gy[ys[ok], xs[ok]]) / nrm[ok]

    sparse = np.zeros(valid.shape, dtype=np.float64)
    sparse[ys, xs] = np.clip(signed_vals, -CLIP_PX, CLIP_PX)
    weight = gaussian_filter((shallow & valid).astype(np.float64), 2.0)
    smooth = gaussian_filter(sparse, 2.0)
    signed = np.where(weight > 0.05, smooth / np.maximum(weight, 1e-12), 0.0)
    signed = np.clip(signed, -CLIP_PX, CLIP_PX)
    return signed.astype(np.float32), coherence.astype(np.float32)


def _field_bands(field_filled: np.ndarray, valid: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    ups = [gaussian_filter(field_filled, 1.0)]
    ups += [depthslice.upward_continue(field_filled, h) for h in LEVELS_M[1:]]
    hgs = [depthslice.hg_mag(u) for u in ups]
    gy, gx = np.gradient(ups[1], depthslice.grid.PIXEL_M)
    return migration_bands_from_hg_levels(hgs, (gy, gx), valid)


def build_migration_bands(training_path, foot: np.ndarray) -> dict:
    """Build the 4 frozen H40-1 bands from training bands 14 (tmi) and 13 (iso_grav_anom)."""
    foot = np.asarray(foot, bool)
    tmi, tmi_valid = depthslice._read_band(training_path, 14, "tmi", foot)
    grav, grav_valid = depthslice._read_band(training_path, 13, "iso_grav_anom", foot)
    tmi_s, tmi_c = _field_bands(tmi, foot)
    grav_s, grav_c = _field_bands(grav, foot)
    bands = {
        "tmi_signed_migration_px": tmi_s,
        "tmi_migration_coherence": tmi_c,
        "grav_signed_migration_px": grav_s,
        "grav_migration_coherence": grav_c,
    }
    return {
        "names": list(BAND_NAMES),
        "bands": {k: np.where(foot, v, 0.0).astype(np.float32) for k, v in bands.items()},
        "valid_frac": {"tmi": float(tmi_valid[foot].mean()), "iso_grav_anom": float(grav_valid[foot].mean())},
    }


def bands_to_footprint_matrix(built: dict, foot: np.ndarray) -> np.ndarray:
    """(n_footprint, 4) float32 matrix in row-major footprint order (oof_detector contract)."""
    foot = np.asarray(foot, bool)
    return np.column_stack([built["bands"][n][foot] for n in built["names"]]).astype(np.float32)


# ---------------------------------------------------------------------------
# H39-5 (Session 18, knowledge/52): migration-EXTRAPOLATED placement.
# H40-1 above encoded migration as detector *features* but still emitted on the
# detector ridge. The functions below turn the same label-free geometry into a
# *placement* surface: every shallow-ridge pixel is displaced one full
# migration step up-dip (shallow - v), the linear extrapolation of ridge
# position vs. continuation height to the -2 km equivalent. Label-free: no
# function here reads labels or any catalogue-derived raster. Named non-fault
# mimic: a dipping lithologic contact / mafic dike (migrates identically,
# zero Quaternary slip); GeoDAWN flight-line striping.
# ---------------------------------------------------------------------------

EXTRAP_BAND_NAMES = ["tmi_extrap_surface", "grav_extrap_surface", "extrap_surface_union"]
EXTRAP_MIN_DISP_PX = 2.0   # frozen in knowledge/52: pool needs |v| >= 2 px
EXTRAP_SWAP_FRAC = 0.35    # frozen in knowledge/52: weakest 35% of base dots are swapped


def ridge_displacement_from_hg_levels(
    hg_levels: list[np.ndarray], valid: np.ndarray
) -> dict:
    """Per-shallow-ridge-pixel displacement vector to the deepest level's ridge.

    Returns dict with float64 maps ``vy``/``vx`` (defined on shallow-ridge
    pixels, 0 elsewhere), the ``shallow`` ridge mask, the 3-level
    ``coherence`` (same formula as H40-1) and ``hg0`` (shallow HG magnitude).
    Deterministic; pure function of its inputs (synthetic-tested).
    """
    if len(hg_levels) < 2:
        raise ValueError("need at least two continuation levels")
    valid = np.asarray(valid, bool)
    ridges = [ridge_at(h, valid) for h in hg_levels]
    dists = [distance_transform_edt(~r) for r in ridges]
    coherence = np.mean([np.exp(-d / 2.0) for d in dists], axis=0)
    shallow, deep = ridges[0], ridges[-1]
    inds = distance_transform_edt(~deep, return_distances=False, return_indices=True)
    ys, xs = np.nonzero(shallow & valid)
    vy = np.zeros(valid.shape, dtype=np.float64)
    vx = np.zeros(valid.shape, dtype=np.float64)
    vy[ys, xs] = inds[0][ys, xs].astype(np.float64) - ys
    vx[ys, xs] = inds[1][ys, xs].astype(np.float64) - xs
    return {"vy": vy, "vx": vx, "shallow": shallow & valid,
            "coherence": coherence.astype(np.float32),
            "hg0": np.asarray(hg_levels[0], dtype=np.float64)}


def extrapolated_surface_from_hg_levels(
    hg_levels: list[np.ndarray], valid: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """(surface, disp_mag) at extrapolated positions shallow - v.

    Each extrapolated pixel inherits score = coherence * clip(hg0 / p99(hg0
    over valid), 0, 1) from its source shallow pixel; on collisions the
    larger score wins (and supplies ``disp_mag`` = |v| of the winning
    source). Pixels landing outside the grid or outside ``valid`` are
    dropped. Deterministic (stable raster order, ascending-score writes).
    """
    valid = np.asarray(valid, bool)
    d = ridge_displacement_from_hg_levels(hg_levels, valid)
    ys, xs = np.nonzero(d["shallow"])
    vy, vx = d["vy"][ys, xs], d["vx"][ys, xs]
    mag = np.hypot(vx, vy)
    ey = ys - np.rint(vy).astype(int)
    ex = xs - np.rint(vx).astype(int)
    h, w = valid.shape
    ok = (ey >= 0) & (ey < h) & (ex >= 0) & (ex < w)
    ey, ex, mag, ys_o, xs_o = ey[ok], ex[ok], mag[ok], ys[ok], xs[ok]
    okv = valid[ey, ex]
    ey, ex, mag, ys_o, xs_o = ey[okv], ex[okv], mag[okv], ys_o[okv], xs_o[okv]
    hg0 = d["hg0"]
    p99 = float(np.percentile(hg0[valid], 99.0)) if valid.any() else 0.0
    scale = p99 if p99 > 0 else 1.0
    score = (d["coherence"][ys_o, xs_o].astype(np.float64)
             * np.clip(hg0[ys_o, xs_o] / scale, 0.0, 1.0))
    order = np.argsort(score, kind="stable")  # ascending: largest written last
    surface = np.zeros(valid.shape, dtype=np.float32)
    disp = np.zeros(valid.shape, dtype=np.float32)
    surface[ey[order], ex[order]] = score[order].astype(np.float32)
    disp[ey[order], ex[order]] = mag[order].astype(np.float32)
    return surface, disp


def _field_extrap(field_filled: np.ndarray, valid: np.ndarray):
    ups = [gaussian_filter(field_filled, 1.0)]
    ups += [depthslice.upward_continue(field_filled, hh) for hh in LEVELS_M[1:]]
    hgs = [depthslice.hg_mag(u) for u in ups]
    surf, disp = extrapolated_surface_from_hg_levels(hgs, valid)
    d = ridge_displacement_from_hg_levels(hgs, valid)
    mags = np.hypot(d["vx"][d["shallow"]], d["vy"][d["shallow"]])
    stats = {
        "n_shallow_ridge_px": int(d["shallow"].sum()),
        "disp_mag_on_shallow_px": {
            "p50": float(np.percentile(mags, 50)) if mags.size else 0.0,
            "p90": float(np.percentile(mags, 90)) if mags.size else 0.0,
            "frac_ge_2px": float((mags >= EXTRAP_MIN_DISP_PX).mean()) if mags.size else 0.0,
        },
    }
    return surf, disp, stats


def build_extrapolated_surfaces(training_path, foot: np.ndarray) -> dict:
    """Build the frozen H39-5 surfaces from training bands 14 (tmi) and 13 (iso_grav_anom)."""
    foot = np.asarray(foot, bool)
    tmi, tmi_valid = depthslice._read_band(training_path, 14, "tmi", foot)
    grav, grav_valid = depthslice._read_band(training_path, 13, "iso_grav_anom", foot)
    tmi_s, tmi_d, tmi_stats = _field_extrap(tmi, foot)
    grav_s, grav_d, grav_stats = _field_extrap(grav, foot)
    union = np.maximum(tmi_s, grav_s)
    disp_union = np.where(tmi_s >= grav_s, tmi_d, grav_d)
    surfaces = {"tmi_extrap_surface": tmi_s, "grav_extrap_surface": grav_s,
                "extrap_surface_union": union}
    return {
        "names": list(EXTRAP_BAND_NAMES),
        "surfaces": {k: np.where(foot, v, 0.0).astype(np.float32) for k, v in surfaces.items()},
        "disp_mag_union": np.where(foot, disp_union, 0.0).astype(np.float32),
        "valid_frac": {"tmi": float(tmi_valid[foot].mean()),
                       "iso_grav_anom": float(grav_valid[foot].mean())},
        "field_stats": {"tmi": tmi_stats, "iso_grav_anom": grav_stats},
    }


class _SpacingHash:
    """Grid hash enforcing Euclidean min_dist (same rule as thinning.dot_thin:
    a candidate is rejected iff an accepted point is *closer* than min_dist)."""

    def __init__(self, min_dist: float):
        self.d = float(min_dist)
        self.cells: dict[tuple[int, int], list[tuple[int, int]]] = {}

    def _key(self, y: int, x: int) -> tuple[int, int]:
        return (int(y // self.d), int(x // self.d))

    def add(self, y: int, x: int) -> None:
        self.cells.setdefault(self._key(y, x), []).append((y, x))

    def clear(self, y: int, x: int) -> bool:
        ky, kx = self._key(y, x)
        lim = self.d * self.d
        for cy in (ky - 1, ky, ky + 1):
            for cx in (kx - 1, kx, kx + 1):
                for (py, px) in self.cells.get((cy, cx), ()):  # pragma: no branch
                    if (py - y) ** 2 + (px - x) ** 2 < lim:
                        return False
        return True


def extrap_swap(
    base: np.ndarray,
    base_score: np.ndarray,
    surface: np.ndarray,
    eligible: np.ndarray,
    swap_frac: float = EXTRAP_SWAP_FRAC,
    min_dist: float = 2.8,
) -> tuple[np.ndarray, dict]:
    """Frozen H39-5 placement swap (knowledge/52).

    Drops the weakest ``swap_frac`` of ``base`` dots (by ``base_score``) and
    replaces them 1-for-1 with top-scoring ``eligible`` extrapolated pixels
    (spacing >= min_dist vs. retained + accepted dots). If the pool is
    exhausted first, backfills from the dropped dots in score-descending
    order under the same spacing rule. Deterministic; reads no labels
    (``eligible`` is built by the caller from visible labels only).
    """
    base = np.asarray(base, bool)
    ys, xs = np.nonzero(base)
    n = len(ys)
    info = {"n_base": int(n), "swap_frac": float(swap_frac), "min_dist": float(min_dist)}
    if n == 0:
        return base.copy(), {**info, "n_keep": 0, "target_swap": 0, "pool_size": 0,
                             "n_swapped": 0, "n_backfilled": 0, "n_final": 0}
    target_swap = int(np.floor(swap_frac * n))
    n_keep = n - target_swap
    order_desc = np.argsort(-np.asarray(base_score, dtype=np.float64)[ys, xs], kind="stable")
    keep_idx, drop_idx = order_desc[:n_keep], order_desc[n_keep:]
    h = _SpacingHash(min_dist)
    for i in keep_idx:
        h.add(int(ys[i]), int(xs[i]))
    pool_mask = np.asarray(eligible, bool) & (np.asarray(surface) > 0) & ~base
    pys, pxs = np.nonzero(pool_mask)
    pool_order = np.argsort(-np.asarray(surface, dtype=np.float64)[pys, pxs], kind="stable")
    accepted: list[tuple[int, int]] = []
    for j in pool_order:
        if len(accepted) >= target_swap:
            break
        y, x = int(pys[j]), int(pxs[j])
        if h.clear(y, x):
            h.add(y, x)
            accepted.append((y, x))
    backfilled: list[tuple[int, int]] = []
    if len(accepted) < target_swap:
        for i in drop_idx:  # already score-descending
            if len(accepted) + len(backfilled) >= target_swap:
                break
            y, x = int(ys[i]), int(xs[i])
            if h.clear(y, x):
                h.add(y, x)
                backfilled.append((y, x))
    out = np.zeros_like(base)
    out[ys[keep_idx], xs[keep_idx]] = True
    for y, x in accepted + backfilled:
        out[y, x] = True
    return out, {**info, "n_keep": int(n_keep), "target_swap": int(target_swap),
                 "pool_size": int(len(pys)), "n_swapped": len(accepted),
                 "n_backfilled": len(backfilled), "n_final": int(out.sum())}



# -------------------------------------------------------------------------------------------------
# H42-1 (Session 18B parallel; knowledge/52 preregistration, knowledge/54 result): migration VECTOR field + dip-extrapolated dot relocation.
#
# The H40-1 bands above keep only the signed scalar migration along the field-gradient normal.
# Relocation needs the full 2-D displacement the shallow ridge travels to reach the 2 km ridge.
# A dipping boundary's ridge migrates down-dip with continuation height, so its zero-height
# (surface) trace is extrapolated up-dip: shift = -v * depth / 2000 m (see relocate_dots).
# Everything below is label-free: inputs are potential fields, depth-to-basement, and dot sets.
# -------------------------------------------------------------------------------------------------

DEPTH_BAND = 15
DEPTH_NAME = "depth_to_base_surf"
REF_DEPTH_M = 2000.0
CAP_PX = 3.0


def migration_vector_from_hg_levels(
    hg_levels: list[np.ndarray], valid: np.ndarray
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(vy, vx, coherence) in px per shallow->deep level span, from HG magnitudes.

    At shallow-ridge pixels the vector points to the nearest deep-ridge pixel (EDT indices),
    magnitude-clipped to CLIP_PX; components are Gaussian-smoothed (sigma=2) inside the
    shallow-ridge corridor (same weight gate as the signed band) and 0 outside it.
    Deterministic pure function (synthetic-tested in tests/test_migration.py).
    """
    if len(hg_levels) < 2:
        raise ValueError("need at least two continuation levels")
    valid = np.asarray(valid, bool)
    ridges = [ridge_at(h, valid) for h in hg_levels]
    coherence = np.mean([np.exp(-distance_transform_edt(~r) / 2.0) for r in ridges], axis=0)
    shallow, deep = ridges[0], ridges[-1]
    inds = distance_transform_edt(~deep, return_distances=False, return_indices=True)
    ys, xs = np.nonzero(shallow & valid)
    vy_raw = inds[0][ys, xs].astype(np.float64) - ys
    vx_raw = inds[1][ys, xs].astype(np.float64) - xs
    mag = np.hypot(vx_raw, vy_raw)
    over = mag > CLIP_PX
    if over.any():
        vy_raw[over] *= CLIP_PX / mag[over]
        vx_raw[over] *= CLIP_PX / mag[over]
    weight = gaussian_filter((shallow & valid).astype(np.float64), 2.0)
    out = []
    for raw in (vy_raw, vx_raw):
        sparse = np.zeros(valid.shape, dtype=np.float64)
        sparse[ys, xs] = raw
        smooth = gaussian_filter(sparse, 2.0)
        vec = np.where(weight > 0.05, smooth / np.maximum(weight, 1e-12), 0.0)
        out.append(vec)
    vy, vx = out
    mag2 = np.hypot(vx, vy)
    over2 = mag2 > CLIP_PX
    if over2.any():
        vy = np.where(over2, vy * CLIP_PX / np.maximum(mag2, 1e-12), vy)
        vx = np.where(over2, vx * CLIP_PX / np.maximum(mag2, 1e-12), vx)
    return vy.astype(np.float32), vx.astype(np.float32), coherence.astype(np.float32)


def _field_vector(field_filled: np.ndarray, valid: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    ups = [gaussian_filter(field_filled, 1.0)]
    ups += [depthslice.upward_continue(field_filled, h) for h in LEVELS_M[1:]]
    return migration_vector_from_hg_levels([depthslice.hg_mag(u) for u in ups], valid)


def build_migration_vectors(training_path, foot: np.ndarray) -> dict:
    """Combined TMI+gravity migration vector field (knowledge/52 lane).

    The combined vector at a pixel is the mean of the per-field vectors over the fields whose
    ridge corridor supports that pixel (nonzero vector); 0 where neither field has a corridor.
    """
    foot = np.asarray(foot, bool)
    tmi, tmi_valid = depthslice._read_band(training_path, 14, "tmi", foot)
    grav, grav_valid = depthslice._read_band(training_path, 13, "iso_grav_anom", foot)
    vy_t, vx_t, coh_t = _field_vector(tmi, foot)
    vy_g, vx_g, coh_g = _field_vector(grav, foot)
    sup_t = (np.hypot(vx_t, vy_t) > 0).astype(np.float64)
    sup_g = (np.hypot(vx_g, vy_g) > 0).astype(np.float64)
    n_sup = sup_t + sup_g
    vy = np.where(n_sup > 0, (vy_t + vy_g) / np.maximum(n_sup, 1.0), 0.0).astype(np.float32)
    vx = np.where(n_sup > 0, (vx_t + vx_g) / np.maximum(n_sup, 1.0), 0.0).astype(np.float32)
    return {
        "vy": vy, "vx": vx,
        "coherence_tmi": coh_t, "coherence_grav": coh_g,
        "valid_frac": {"tmi": float(tmi_valid[foot].mean()),
                       "iso_grav_anom": float(grav_valid[foot].mean())},
    }


def read_depth_to_base(training_path, foot: np.ndarray) -> np.ndarray:
    """Depth-to-basement (training band 15) in metres; invalid/outside-footprint -> 0 (no move).

    Unlike depthslice._read_band this does NOT nearest-fill: inventing a depth would invent a
    relocation distance. Verified label-free band statistics (metres) in knowledge/52 Exp 1.
    """
    import rasterio

    foot = np.asarray(foot, bool)
    with rasterio.open(training_path) as s:
        desc = (s.descriptions[DEPTH_BAND - 1] or "").split(" - ")[0].strip()
        if desc != DEPTH_NAME:
            raise ValueError(f"band {DEPTH_BAND} is {desc!r}, expected {DEPTH_NAME!r}")
        a = s.read(DEPTH_BAND).astype(np.float64)
        nd = s.nodata
    valid = foot & np.isfinite(a) & (np.abs(a) < 1e30)
    if nd is not None:
        valid &= a != float(nd)
    return np.where(valid, a, 0.0).astype(np.float32)


def shift_magnitude(vy: np.ndarray, vx: np.ndarray, depth_m: np.ndarray,
                    ref_m: float = REF_DEPTH_M, cap_px: float = CAP_PX) -> np.ndarray:
    """Per-pixel relocation distance |v| * clip(depth,0,ref)/ref, capped at cap_px (px)."""
    z = np.clip(np.where(np.isfinite(depth_m), depth_m, 0.0), 0.0, float(ref_m))
    return np.minimum(np.hypot(vx, vy) * (z / float(ref_m)), float(cap_px)).astype(np.float32)


def relocate_dots(
    dots: np.ndarray,
    vy: np.ndarray,
    vx: np.ndarray,
    depth_m: np.ndarray,
    blocked: np.ndarray,
    allowed: np.ndarray,
    *,
    mode: str = "phys",
    seed: int = 0,
    ref_m: float = REF_DEPTH_M,
    cap_px: float = CAP_PX,
) -> tuple[np.ndarray, dict]:
    """Relocate binary dots along the migration vector field (knowledge/52 lane).

    mode="phys": shift = -v * clip(depth,0,ref)/ref (up-dip extrapolation of the surface trace).
    mode="anti": the sign-flipped falsification control. mode="rand": each phys shift rotated by
    a seeded uniform angle (magnitudes preserved before rounding). Shift magnitudes are capped
    at cap_px, then rounded to whole pixels. Dots are placed in raster order; a dot whose target
    is outside `allowed`, inside `blocked`, or already claimed stays at its origin if that is
    still free and allowed, else is dropped (counted). Returns (relocated mask, stats dict).
    Spacing is NOT enforced here; callers apply the shared thinning.dot_thin afterwards.
    """
    if mode not in ("phys", "anti", "rand"):
        raise ValueError("mode must be 'phys', 'anti' or 'rand'")
    dots = np.asarray(dots, bool)
    blocked = np.asarray(blocked, bool)
    allowed = np.asarray(allowed, bool)
    if not (dots.shape == vy.shape == vx.shape == depth_m.shape == blocked.shape == allowed.shape):
        raise ValueError("all relocation inputs must share one shape")
    ys, xs = np.nonzero(dots)
    z = np.clip(np.where(np.isfinite(depth_m[ys, xs]), depth_m[ys, xs], 0.0), 0.0, float(ref_m))
    scale = z / float(ref_m)
    sy = -np.nan_to_num(vy[ys, xs].astype(np.float64)) * scale
    sx = -np.nan_to_num(vx[ys, xs].astype(np.float64)) * scale
    if mode == "anti":
        sy, sx = -sy, -sx
    elif mode == "rand":
        ang = np.random.default_rng(seed).uniform(0.0, 2.0 * np.pi, size=len(ys))
        ca, sa = np.cos(ang), np.sin(ang)
        sy, sx = sy * ca - sx * sa, sy * sa + sx * ca
    mag = np.hypot(sx, sy)
    over = mag > float(cap_px)
    if over.any():
        sy[over] *= float(cap_px) / mag[over]
        sx[over] *= float(cap_px) / mag[over]
    dy = np.rint(sy).astype(int)
    dx = np.rint(sx).astype(int)

    out = np.zeros(dots.shape, bool)
    H, W = dots.shape
    n_moved = n_stayed_blocked = n_dropped = 0
    for i in range(len(ys)):
        y, x = int(ys[i]), int(xs[i])
        ty, tx = y + int(dy[i]), x + int(dx[i])
        moved = (dy[i] != 0) or (dx[i] != 0)
        if moved and 0 <= ty < H and 0 <= tx < W and allowed[ty, tx] and not blocked[ty, tx] \
                and not out[ty, tx]:
            out[ty, tx] = True
            n_moved += 1
        elif allowed[y, x] and not out[y, x]:
            out[y, x] = True
            if moved:
                n_stayed_blocked += 1
        else:
            n_dropped += 1
    stats = {
        "mode": mode, "n_in": int(len(ys)), "n_out_pre_thin": int(out.sum()),
        "n_moved_ge1px": int(n_moved), "n_stayed_after_blocked_move": int(n_stayed_blocked),
        "n_dropped_collision_or_disallowed": int(n_dropped),
        "frac_moved_ge1px": float(n_moved / max(1, len(ys))),
        "mean_rounded_shift_px_of_moved": float(
            np.hypot(dy, dx)[np.hypot(dy, dx) > 0].mean()) if (np.hypot(dy, dx) > 0).any() else 0.0,
    }
    return out, stats
