"""H43-1 TPB2-GKC: tip-protected B2 eligibility + greedy kernel-cover placement.

Session 20 lane (see knowledge/56_s20_preregistration_H43-1.md). Two deterministic pieces:

1. ``eligibility`` — a pool pixel may host a dot iff it is off the *visible* catalogue and
   either farther than ``ring_px`` from it or within ``tip_radius_px`` of a visible-catalogue
   endpoint (8-neighbourhood degree <= 1, the endpoint geometry already used by
   ``scripts/run_h32_1_holdout.py:build_flank_mid_mask``). This keeps the champion's validated
   mid-segment flank-shadow deletion (ring widened to 2 px) while rescuing along-strike tip
   continuations, the one ring subclass with measured elevated holdout credit density (H32-1).

2. ``greedy_kernel_cover`` — deterministic lazy-greedy maximisation of covered pool mass under
   the official triangular kernel k(d) = max(1 - d/3, 0): every pick maximises the *increase*
   in sum_x max_dots k(d(dot, x)) over pool pixels x, subject to min inter-dot distance
   ``min_dist``. Unlike ``thinning.dot_thin`` (raster-order FIFO phase), placement here is by
   coverage value, and dots may land on pool pixels no previous raster emitted. The function is
   generative, not a subset operation on any earlier dot set.

No labels are read beyond the caller-supplied visible catalogue; no scores are read at all.
Tie-breaking is by flat raster index, so runs are byte-identical.
"""

from __future__ import annotations

import heapq

import numpy as np
from scipy.ndimage import convolve, distance_transform_edt

KERNEL_RADIUS_PX = 3.0


def _kernel_offsets(width: int) -> tuple[np.ndarray, np.ndarray]:
    """Flat offsets + triangular-kernel weights for every offset with k > 0."""
    offs, ks = [], []
    r = int(np.ceil(KERNEL_RADIUS_PX))
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d = float(np.hypot(dy, dx))
            k = 1.0 - d / KERNEL_RADIUS_PX
            if k > 0.0:
                offs.append(dy * width + dx)
                ks.append(k)
    return np.asarray(offs, dtype=np.int64), np.asarray(ks, dtype=np.float64)


def _spacing_offsets(min_dist: float, width: int) -> np.ndarray:
    """Flat offsets strictly closer than ``min_dist`` (blocked after a pick)."""
    offs = []
    r = int(np.ceil(min_dist))
    lim = min_dist * min_dist
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy * dy + dx * dx < lim:
                offs.append(dy * width + dx)
    return np.asarray(offs, dtype=np.int64)


def eligibility(
    pool: np.ndarray,
    visible: np.ndarray,
    *,
    ring_px: float = 2.0,
    tip_radius_px: float = 3.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Return (eligible, d_visible, d_endpoint) for a pool under a visible catalogue.

    Eligible = pool & ~visible & (d_visible > ring_px | d_endpoint <= tip_radius_px).
    Endpoints are visible-catalogue pixels with 8-neighbourhood catalogue degree <= 1.
    With an empty catalogue every pool pixel is eligible (distances are +inf).
    """
    pool = np.asarray(pool, bool)
    visible = np.asarray(visible, bool)
    if pool.shape != visible.shape or pool.ndim != 2:
        raise ValueError("pool/visible must be equal-shaped 2-D grids")
    if not visible.any():
        inf = np.full(pool.shape, np.inf)
        return pool.copy(), inf, inf.copy()
    d_visible = distance_transform_edt(~visible)
    degree = convolve(visible.astype(np.int32), np.ones((3, 3), np.int32), mode="constant") - 1
    endpoints = visible & (degree <= 1)
    d_endpoint = (
        distance_transform_edt(~endpoints)
        if endpoints.any()
        else np.full(pool.shape, np.inf)
    )
    elig = pool & ~visible & ((d_visible > ring_px) | (d_endpoint <= tip_radius_px))
    return elig, d_visible, d_endpoint


def cover_surface(pool: np.ndarray, elig: np.ndarray) -> np.ndarray:
    """Pre-placement surface: triangular-kernel density of the pool, masked to eligibles.

    This is the continuous surface whose rank correlation against every registry raster is
    reported before placement (parallel-run protocol duplicate check on the surface).
    """
    pool = np.asarray(pool, bool)
    elig = np.asarray(elig, bool)
    r = int(np.ceil(KERNEL_RADIUS_PX))
    yy, xx = np.mgrid[-r : r + 1, -r : r + 1]
    kern = np.maximum(1.0 - np.hypot(yy, xx) / KERNEL_RADIUS_PX, 0.0)
    dens = convolve(pool.astype(np.float64), kern, mode="constant")
    return np.where(elig, dens, 0.0)


def greedy_kernel_cover(
    pool: np.ndarray,
    elig: np.ndarray,
    budget: int,
    *,
    min_dist: float = 2.8,
) -> np.ndarray:
    """Place up to ``budget`` dots from ``elig`` maximising covered pool mass, greedily.

    Deterministic lazy greedy. Returns a boolean dot mask with min inter-dot distance
    >= ``min_dist`` (dots at distance exactly ``min_dist`` are allowed, matching
    ``thinning.dot_thin``'s strict-``<`` blocking convention).
    """
    pool = np.asarray(pool, bool)
    elig = np.asarray(elig, bool)
    if pool.shape != elig.shape or pool.ndim != 2:
        raise ValueError("pool/elig must be equal-shaped 2-D grids")
    if budget < 0:
        raise ValueError("budget must be >= 0")
    dots = np.zeros(pool.shape, bool)
    if budget == 0 or not elig.any() or not pool.any():
        return dots

    pad = int(np.ceil(KERNEL_RADIUS_PX)) + 1
    H, W = pool.shape
    Hp, Wp = H + 2 * pad, W + 2 * pad
    pool_p = np.zeros((Hp, Wp), bool)
    pool_p[pad : pad + H, pad : pad + W] = pool
    elig_p = np.zeros((Hp, Wp), bool)
    elig_p[pad : pad + H, pad : pad + W] = elig

    pool_f = pool_p.ravel()
    credit = np.zeros(Hp * Wp, dtype=np.float64)
    blocked = np.zeros(Hp * Wp, dtype=bool)
    offs, ks = _kernel_offsets(Wp)
    spacing = _spacing_offsets(min_dist, Wp)

    # Initial gains = kernel density of the pool at each eligible pixel (exact convolution).
    surface = cover_surface(pool, elig)
    surf_p = np.zeros((Hp, Wp))
    surf_p[pad : pad + H, pad : pad + W] = surface
    cand = np.flatnonzero(elig_p.ravel())
    gains0 = surf_p.ravel()[cand]
    heap = [(-float(g), int(i)) for g, i in zip(gains0, cand)]
    heapq.heapify(heap)

    def gain(idx: int) -> float:
        tgt = idx + offs
        on_pool = pool_f[tgt]
        if not on_pool.any():
            return 0.0
        return float(np.maximum(ks[on_pool] - credit[tgt[on_pool]], 0.0).sum())

    picked: list[int] = []
    eps = 1e-12
    while heap and len(picked) < budget:
        _neg_stored, idx = heapq.heappop(heap)
        if blocked[idx]:
            continue
        g = gain(idx)
        if heap and g < -heap[0][0] - eps:
            heapq.heappush(heap, (-g, idx))
            continue
        if g <= 0.0 and len(picked) > 0:
            # No uncovered pool mass left for any remaining (unblocked) candidate heading
            # the heap with a stale-but-maximal bound; keep scanning only if some other
            # candidate could still have gain > 0. The heap's next stored gain is an upper
            # bound (gains only decrease as credit grows), so if it is also ~0 we are done.
            if not heap or -heap[0][0] <= eps:
                break
            heapq.heappush(heap, (-g, idx))
            # Mark this candidate exhausted so the loop cannot spin on it forever.
            blocked[idx] = True
            continue
        # Pick idx.
        picked.append(idx)
        tgt = idx + offs
        on_pool = pool_f[tgt]
        t = tgt[on_pool]
        credit[t] = np.maximum(credit[t], ks[on_pool])
        blocked[idx + spacing] = True

    out_p = np.zeros(Hp * Wp, dtype=bool)
    if picked:
        out_p[np.asarray(picked, dtype=np.int64)] = True
    return out_p.reshape(Hp, Wp)[pad : pad + H, pad : pad + W]
