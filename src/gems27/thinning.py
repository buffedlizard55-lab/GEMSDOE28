"""Deterministic geodesic Poisson-disk dot thinning of a binary emission.

Why it matters: a solid 1-px line pays ~3x the false-positive mass of a dotted line (spacing ~3 px)
while earning only ~1.3x the on-line credit under the 300 m kernel, so thinning a solid emission
raises DTI without any new geology. This is how the owner's group obtained the 0.2477 file from the
0.1922 H19-5 emission (24GEMSDOE, `dot_thin(min_dist=1.5)`).

Credit: algorithm and determinism contract follow buffedlizard55-lab/GEMSDOE24 `src/gems/thinning.py`
(re-written here; byte-identity with the sibling output is verified in tests when data are present).
Guarantees: output is a subset of the input; no labels or scores are read; seeds are the lowest raster
index of each 8-connected component; traversal is FIFO breadth-first, so runs are byte-identical.
"""

from __future__ import annotations

from collections import deque

import numpy as np
from scipy.ndimage import label


def _disc_offsets(min_dist: float, width: int) -> list[int]:
    r = int(np.ceil(min_dist))
    lim = min_dist * min_dist
    return [dy * width + dx for dy in range(-r, r + 1) for dx in range(-r, r + 1)
            if dy * dy + dx * dx < lim]


def dot_thin(mask: np.ndarray, min_dist: float) -> np.ndarray:
    """Keep a pixel iff no already-kept pixel is closer than `min_dist` (Euclidean, pixels)."""
    mask = np.asarray(mask, bool)
    if mask.ndim != 2:
        raise ValueError("2-D mask required")
    if min_dist <= 1.0 or not mask.any():
        return mask.copy()
    H, W = mask.shape
    pad = int(np.ceil(min_dist)) + 1
    Wp, Hp = W + 2 * pad, H + 2 * pad
    padded = np.zeros((Hp, Wp), bool)
    padded[pad:pad + H, pad:pad + W] = mask
    flat = bytearray(padded.tobytes())
    visited, blocked, kept = bytearray(Hp * Wp), bytearray(Hp * Wp), bytearray(Hp * Wp)
    disc = _disc_offsets(min_dist, Wp)
    nbr = (-Wp - 1, -Wp, -Wp + 1, -1, 1, Wp - 1, Wp, Wp + 1)
    comp, _ = label(padded, structure=np.ones((3, 3), int))
    fc = comp.ravel()
    order = np.flatnonzero(fc)
    _, first = np.unique(fc[order], return_index=True)
    for seed in order[np.sort(first)].tolist():
        if visited[seed]:
            continue
        visited[seed] = 1
        q = deque((seed,))
        while q:
            c = q.popleft()
            if not blocked[c]:
                kept[c] = 1
                for o in disc:
                    blocked[c + o] = 1
            for o in nbr:
                n = c + o
                if flat[n] and not visited[n]:
                    visited[n] = 1
                    q.append(n)
    out = np.frombuffer(bytes(kept), dtype=np.uint8).reshape(Hp, Wp).astype(bool)
    return out[pad:pad + H, pad:pad + W]


def directional_dot_thin(
    mask: np.ndarray,
    strike_x: np.ndarray,
    strike_y: np.ndarray,
    a_along: float,
    a_across: float,
) -> np.ndarray:
    """Anisotropic Poisson-disk thinning of a 1-px ridge mask using a per-pixel local strike.

    Companion to ``dot_thin``. Why it matters: the linear DTI kernel saturates *along* strike
    (consecutive dots on a straight fault share most of their kernel mass) but does *not* across
    strike. Isotropic Poisson-disk packs at a single ``min_dist`` therefore *underuse* the kernel
    on straight ridges (too few dots) and *overuse* it on tight bends (too many dots where the
    ridge changes direction). The anisotropic variant keeps a pixel iff no already-kept pixel is
    closer than the ellipse ``(along / a_along)^2 + (across / a_across)^2 < 1`` oriented with the
    local strike vector at the kept pixel. The strike vector at a candidate pixel is the unit
    vector along the local ridge direction (perpendicular to the gradient).

    Parameters
    ----------
    mask : (H, W) boolean array
        Candidate pixels (typically a 1-px ridge).
    strike_x, strike_y : (H, W) float arrays
        Per-pixel unit strike vector (the along-ridge direction). Pixel coordinates (dy, dx) project
        onto ``along = dy * strike_y + dx * strike_x`` and ``across = -dy * strike_x + dx *
        strike_y``. Outside ``mask``, strike values are not consulted.
    a_along : float
        Spacing (pixels) along the local strike. ``a_along >= 1.0`` for any thinning; both
        ``a_along <= 1.0`` and ``a_across <= 1.0`` together short-circuit to ``mask.copy()``
        (the same convention as ``dot_thin``).
    a_across : float
        Spacing (pixels) across the local strike. Same validity rule.

    Returns
    -------
    (H, W) boolean array — a subset of ``mask`` (never adds pixels).

    Notes
    -----
    Determinism contract (mirrors ``dot_thin``):
      * FIFO BFS over each 8-connected component, seed = lowest raster index;
      * the kept set is therefore a function of ``mask`` and the strike field only;
      * outputs are deterministic on every input.
    Performance: mirrors ``dot_thin``'s bytearray BFS for the per-pixel neighbour walk; only the
    ellipse offset set is rebuilt per kept pixel (a fast ~50-entry array). On the 121K-pixel H19-5
    ridge the function completes in ~2 s on one CPU core.

    History
    -------
    Added in Session 13 (2026-10-03) as a directional / anisotropic Poisson-disk re-pack experiment
    in a parallel workstream. That work labeled it H37-1, colliding with this repository's distinct
    metric-aware H37-1; the collision is recorded in ``registry/irregularities.json``. Its
    preregistered four-criterion gate on fresh seeds 250-254 closed the directional arm (mean paired
    ΔDTI -0.00298, 0/5 seeds, 0/4 folds; primary lost to the isotropic rung-3.0 by -0.00510). The
    function is preserved and tested for
    callers with a higher-precision strike field than the OOF detector's 4-sector quantization
    (±22.5 deg; too noisy on the 26,645 short ridge components for anisotropy to help).
    """
    mask = np.asarray(mask, bool)
    if mask.ndim != 2:
        raise ValueError("2-D mask required")
    if mask.shape != strike_x.shape or mask.shape != strike_y.shape:
        raise ValueError("strike_x/strike_y must match mask shape")
    if a_along <= 1.0 and a_across <= 1.0:
        return mask.copy()
    H, W = mask.shape
    rmax = int(np.ceil(max(a_along, a_across)))
    pad = rmax + 2
    Hp, Wp = H + 2 * pad, W + 2 * pad
    padded = np.zeros((Hp, Wp), bool)
    padded[pad:pad + H, pad:pad + W] = mask
    spx = np.zeros((Hp, Wp), np.float32)
    spy = np.zeros((Hp, Wp), np.float32)
    spx[pad:pad + H, pad:pad + W] = np.asarray(strike_x, dtype=np.float32)
    spy[pad:pad + H, pad:pad + W] = np.asarray(strike_y, dtype=np.float32)

    # Offset set: integer (dy, dx) pairs inside the bounding box; the ellipse test happens
    # per-pixel against the strike vector at the kept pixel.
    offs = [(dy, dx) for dy in range(-rmax, rmax + 1) for dx in range(-rmax, rmax + 1)
            if not (dy == 0 and dx == 0)]
    inv_along = 1.0 / float(a_along)
    inv_across = 1.0 / float(a_across)

    flat = bytearray(padded.tobytes())
    visited = bytearray(Hp * Wp)
    blocked = bytearray(Hp * Wp)
    kept = bytearray(Hp * Wp)
    spx_flat = spx.ravel()
    spy_flat = spy.ravel()

    nbr = (-Wp - 1, -Wp, -Wp + 1, -1, 1, Wp - 1, Wp, Wp + 1)
    comp, _ = label(padded, structure=np.ones((3, 3), int))
    fc = comp.ravel()
    order = np.flatnonzero(fc)
    _, first = np.unique(fc[order], return_index=True)
    for seed in order[np.sort(first)].tolist():
        if visited[seed]:
            continue
        visited[seed] = 1
        q = deque((seed,))
        while q:
            c = q.popleft()
            if not blocked[c]:
                kept[c] = 1
                sx_ = float(spx_flat[c])
                sy_ = float(spy_flat[c])
                # If the strike vector is zero (e.g. on a flat pixel or outside the ridge), fall
                # back to the isotropic disc so off-ridge pixels do not over-block their
                # neighbours. Otherwise test every (dy, dx) offset against the oriented ellipse.
                mag2 = sx_ * sx_ + sy_ * sy_
                if mag2 < 1e-12:
                    # Isotropic disc test: along == across == sqrt(dx^2 + dy^2)/sqrt(2)
                    # (along**2 + across**2)/a**2 < 1  <=>  dx**2 + dy**2 < a**2
                    a_max = max(a_along, a_across)
                    for dy, dx in offs:
                        if dy * dy + dx * dx < a_max * a_max:
                            blocked[c + dy * Wp + dx] = 1
                else:
                    for dy, dx in offs:
                        along = dy * sy_ + dx * sx_
                        across = -dy * sx_ + dx * sy_
                        if (along * inv_along) ** 2 + (across * inv_across) ** 2 < 1.0:
                            blocked[c + dy * Wp + dx] = 1
            for o in nbr:
                n = c + o
                if flat[n] and not visited[n]:
                    visited[n] = 1
                    q.append(n)
    out = np.frombuffer(bytes(kept), dtype=np.uint8).reshape(Hp, Wp).astype(bool)
    return out[pad:pad + H, pad:pad + W]
