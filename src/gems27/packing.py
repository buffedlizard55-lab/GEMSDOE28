"""Metric-aware dot packing: lazy-greedy maximum expected coverage.

Motivation (measured, not assumed)
----------------------------------
`gems27.thinning.dot_thin` keeps a pixel iff no already-kept pixel is closer than `min_dist`, walking
candidates in ascending raster index. The rule never reads the evidence: a candidate's detector
probability cannot influence whether it survives. Two independent measurements say that is a loss:

* H36-1 (seeds 240-249, `evidence/h36_1_holdout.json`) showed that changing the *layout* at the same
  count is worth `+0.002599` OOF DTI (10/10 seeds, 4/4 folds) while a matched-count random deletion
  loses `0.001657` (0/10, 0/4).
* H37-1's exploratory passes (`evidence/_scratch/packing_h37_explore*.json`, spent seeds 181/185)
  measured that raster-order packing of the *full* ridge pool is catastrophic (`-0.0473`) because the
  rule is spatially biased once the top-k pre-filter is removed, and that covering the detector
  probability field - rather than the binary ridge set (`-0.0356`) or a smoothed ridge set
  (`-0.0210`) - is what buys the gain.

Objective
---------
Let `w(q) >= 0` be a non-negative field on the grid (here the detector's probability, i.e. the
expected fault-truth mass), `k(d) = max(1 - d/R, 0)` the official competition kernel (`R = 3 px =
300 m`, `src/gems27/metric.py`), and `C(q) = max_{x in S} k(|x - q|)` the coverage already achieved by
a selected set `S`. Selecting a dot at `x` earns

    gain(x | S) = sum_q w(q) * max(0, k(|x - q|) - C(q))      (q within the 7x7 kernel footprint)

which is exactly the expected distance-weighted true-positive mass of the competition metric
(`TPw = sum_g max_x p(x) k(d(x, g))`) under the detector's own field. `gain` is monotone and
submodular, so the greedy order is the classical maximum-coverage order (Nemhauser, Wolsey & Fisher,
1978, DOI 10.1007/BF01588971) with a `1 - 1/e` guarantee, and the lazy evaluation of Minoux (1978,
DOI 10.1007/BF01588962) makes it cheap without changing the selected set.

This module is deterministic: candidates are enumerated in row-major order and ties are broken by that
order, so two runs are byte-identical.
"""

from __future__ import annotations

import heapq

import numpy as np

from . import metric

RADIUS_PX = metric.RADIUS_PX  # 3.0 px = 300 m, the official kernel


def disc_rel(min_dist: float) -> tuple[int, np.ndarray]:
    """Integer radius and boolean disc mask for a hard spacing rule of `min_dist` pixels."""
    r = int(np.ceil(min_dist))
    dy, dx = np.mgrid[-r:r + 1, -r:r + 1]
    return r, (dy * dy + dx * dx) < min_dist * min_dist


def prob_order_pack(score: np.ndarray, candidates: np.ndarray, *, n_target: int | None = None,
                    min_dist: float = 2.8) -> np.ndarray:
    """Maximal independent set under `min_dist`, visiting candidates by descending `score`.

    The same spacing rule as :func:`gems27.thinning.dot_thin`, but the visiting order is the evidence
    field instead of the raster index. `score` is read only at candidate pixels; `n_target` truncates
    the accepted set so two arms can be compared at a matched dot count. Deterministic: ties break on
    flat index, and the scan is a pure Python loop over a sorted candidate list.
    """
    score = np.asarray(score, np.float32)
    candidates = np.asarray(candidates, bool)
    if score.shape != candidates.shape or candidates.ndim != 2:
        raise ValueError("score and candidates must be equal-shaped 2-D arrays")
    out = np.zeros_like(candidates)
    if n_target is not None and n_target <= 0:
        return out
    r, disc = disc_rel(min_dist)
    ys, xs = np.nonzero(candidates)
    if ys.size == 0:
        return out
    flat = ys.astype(np.int64) * candidates.shape[1] + xs
    order = np.lexsort((flat, -score[ys, xs]))
    H, W = candidates.shape
    blocked = np.zeros((H + 2 * r, W + 2 * r), bool)
    n_kept = 0
    for i in order:
        y, x = int(ys[i]), int(xs[i])
        if blocked[y + r, x + r]:
            continue
        out[y, x] = True
        blocked[y:y + disc.shape[0], x:x + disc.shape[1]] |= disc
        n_kept += 1
        if n_target is not None and n_kept >= n_target:
            break
    return out


def random_order_pack(candidates: np.ndarray, *, n_target: int | None = None,
                      min_dist: float = 2.8, seed: int = 0) -> np.ndarray:
    """The content-blind control: `prob_order_pack`'s rule with a seeded random visiting order."""
    candidates = np.asarray(candidates, bool)
    out = np.zeros_like(candidates)
    if n_target is not None and n_target <= 0:
        return out
    r, disc = disc_rel(min_dist)
    ys, xs = np.nonzero(candidates)
    if ys.size == 0:
        return out
    order = np.random.default_rng(seed).permutation(ys.size)
    H, W = candidates.shape
    blocked = np.zeros((H + 2 * r, W + 2 * r), bool)
    n_kept = 0
    for i in order:
        y, x = int(ys[i]), int(xs[i])
        if blocked[y + r, x + r]:
            continue
        out[y, x] = True
        blocked[y:y + disc.shape[0], x:x + disc.shape[1]] |= disc
        n_kept += 1
        if n_target is not None and n_kept >= n_target:
            break
    return out


def kernel_patch(radius_px: float = RADIUS_PX) -> np.ndarray:
    """The official triangular kernel evaluated on the (2r+1)^2 integer offsets."""
    r = int(radius_px)
    dy, dx = np.mgrid[-r:r + 1, -r:r + 1]
    return np.maximum(1.0 - np.hypot(dy, dx) / radius_px, 0.0).astype(np.float32)


def coverage_greedy(candidates: np.ndarray, weight: np.ndarray, n_target: int,
                    radius_px: float = RADIUS_PX) -> np.ndarray:
    """Select at most `n_target` pixels of `candidates` maximising expected kernel coverage of `weight`.

    Returns a boolean mask that is always a subset of `candidates`. Selection stops early when no
    remaining candidate has a positive marginal gain, so the result can contain fewer than
    `n_target` pixels; callers that need an exact count must check `out.sum()`.
    """
    candidates = np.asarray(candidates, bool)
    weight = np.asarray(weight, np.float32)
    if candidates.shape != weight.shape or candidates.ndim != 2:
        raise ValueError("candidates and weight must be equal-shaped 2-D arrays")
    if n_target <= 0 or not candidates.any():
        return np.zeros_like(candidates, bool)

    r = int(radius_px)
    patch = kernel_patch(radius_px)
    H, W = weight.shape
    padded = np.zeros((H + 2 * r, W + 2 * r), np.float32)
    padded[r:r + H, r:r + W] = np.where(np.isfinite(weight), weight, 0.0)
    coverage = np.zeros_like(padded)
    keep = np.zeros_like(candidates, bool)

    def exact_gain(py: int, px: int) -> float:
        window = padded[py - r:py + r + 1, px - r:px + r + 1] * patch
        window = window - coverage[py - r:py + r + 1, px - r:px + r + 1]
        np.maximum(window, 0.0, out=window)
        return float(window.sum())

    # Initial upper bounds: the exact C = 0 gain, computed for every pixel at once by correlation.
    from scipy.ndimage import correlate

    initial = correlate(padded, patch, mode="constant", cval=0.0)
    ys, xs = np.nonzero(candidates)
    heap = [(-float(initial[y + r, x + r]), int(y), int(x))
            for y, x in zip(ys.tolist(), xs.tolist()) if initial[y + r, x + r] > 0.0]
    heapq.heapify(heap)

    n_kept = 0
    while heap and n_kept < n_target:
        neg_ub, y0, x0 = heapq.heappop(heap)
        py, px = y0 + r, x0 + r
        gain = exact_gain(py, px)
        if heap and -gain > heap[0][0] + 1e-12:
            heapq.heappush(heap, (-gain, y0, x0))  # tighter bound; may still win later
            continue
        if gain <= 0.0:
            break
        keep[y0, x0] = True
        n_kept += 1
        window = coverage[py - r:py + r + 1, px - r:px + r + 1]
        np.maximum(window, patch, out=window)
    return keep


def coverage_of(selected: np.ndarray, weight: np.ndarray, radius_px: float = RADIUS_PX) -> float:
    """Total kernel coverage of `weight` achieved by `selected` (the greedy objective's value).

    `max_x k(d(x, q))` equals `k(min_x d(x, q))` because the kernel is monotone decreasing, so a single
    Euclidean distance transform to the nearest selected pixel reproduces the metric's own term.
    """
    from scipy.ndimage import distance_transform_edt

    selected = np.asarray(selected, bool)
    if not selected.any():
        return 0.0
    d = distance_transform_edt(~selected)
    k = np.maximum(1.0 - d / radius_px, 0.0).astype(np.float32)
    return float((np.asarray(weight, np.float32) * k).sum())
