"""Leave-fault-system-out (LOSFO) far-field holdout: a protocol that can validate *addition* arms.

Why this module exists
----------------------
Every promotion gate in this repository so far has used `holdout.make_split`, which hides a random
20 % of the 8-connected catalogue components *inside* each spatial quadrant. `evidence/
arm_habitat_decomposition.json` measured the consequence exactly: 100 % of the hidden truth in that
protocol sits at distance 0 from the full published catalogue, so Habitat A (>= 300 m from the
catalogue, the only habitat a shippable file can occupy, because `scripts/verify_downloads.py`
requires zero pixels on catalogue cells) contains **no truth by construction**. A protocol with no
far-field truth can only ever reward dots placed next to the published catalogue.

That is survivable for *pruning* arms (they only decide which already-credible dots to drop) and it
is fatal for *addition* arms (they propose dots where nothing is catalogued). Session 10's
reachability frontier (`evidence/reachability_frontier.json`) shows the gap to the public leaderboard
#1 is a credit gap of ~1,150 px at the current budget, i.e. a detection gap that only an addition arm
can close. So the repository needed a protocol whose truth is genuinely off-catalogue.

Design
------
1. Group catalogue pixels into **fault systems**: 8-connected components of the catalogue dilated by
   `dilate_px`, so adjacent en-echelon segments of one structure are held out together rather than
   leaving a mapped stub next to a hidden one.
2. Assign whole systems to spatial folds (quadrant-blocked, so a fold is geographically contiguous).
3. **Erase a buffer around every held-out system from the training labels.** This is the step the
   interleaved protocol cannot do: if catalogue pixels within 600 m of a held-out system remained
   "known", a detector could score on the hidden system by learning "emit near mapped faults", which
   is exactly the behaviour a real submission cannot exploit off-catalogue.
4. Train the detector once on the masked labels, then evaluate on the held-out systems. Truth is now
   >= `buffer_px` from every pixel the detector was allowed to see as positive.

`inflation_of_interleaved_protocol` re-scores the *same* held-out systems under the interleaved
protocol (trained on the unmasked catalogue) and reports the ratio. That ratio is the quantitative
form of the standing caveat "catalogue-internal truth overstates real-world enrichment": it is how
much of a measured gain is catalogue interpolation rather than physics.

Known limits (stated wherever these numbers are quoted)
------------------------------------------------------
* Held-out systems are still *mapped* faults, so their geophysical expression is, by selection,
  detectable. The absolute DTI here is an upper bound on performance against genuinely unmapped
  faults, not an estimate of it.
* The feature rasters are not re-derived with the held-out systems removed; only the labels are
  masked. Any layer constructed *from* the catalogue (Qfaults distance fields, SGMC-derived bands)
  must therefore be excluded or explicitly audited before an arm's result is trusted.
* Catalogue truth is still ~12k px of a much larger real hidden set; the size calibration comes from
  the blind-lattice inversion, not from this protocol.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.ndimage import binary_dilation, distance_transform_edt
from scipy.ndimage import label as ndi_label

STRUCTURE_8 = np.ones((3, 3), int)


def dilate8(mask: np.ndarray, px: int) -> np.ndarray:
    """8-connected dilation by `px` pixels, with px <= 0 meaning "no dilation".

    scipy.ndimage.binary_dilation(iterations=0) does NOT return the input: it returns an all-True
    array, which would silently merge every fault in the footprint into a single system. The guard
    below is therefore load-bearing, not cosmetic.
    """
    mask = np.asarray(mask, bool)
    if px <= 0:
        return mask.copy()
    return binary_dilation(mask, structure=STRUCTURE_8, iterations=int(px))
DEFAULT_DILATE_PX = 3      # 300 m: merges en-echelon segments of one structure
DEFAULT_BUFFER_PX = 6      # 600 m: 2x the 300 m DTI kernel radius, matches oof_detector.BUFFER_PX
HOLDOUT_FRACTION = 0.25    # share of systems held out, matching the interleaved protocol's 20-25 %


def fault_systems(labels: np.ndarray, dilate_px: int = DEFAULT_DILATE_PX) -> tuple[np.ndarray, int]:
    """Label catalogue pixels into fault systems (8-connected components of the dilated catalogue).

    Returns (system_id_grid, n_systems). Pixels outside the catalogue get id 0. The returned grid is
    computed on the *dilated* mask then intersected with `labels`, so every catalogue pixel carries
    exactly one system id and dilation only decides which pixels are grouped together.
    """
    labels = np.asarray(labels, bool)
    if not labels.any():
        return np.zeros(labels.shape, np.int32), 0
    grown = dilate8(labels, int(dilate_px))
    comp, n = ndi_label(grown, structure=STRUCTURE_8)
    return (comp * labels).astype(np.int32), int(n)


def system_table(sys_grid: np.ndarray, n_systems: int, footprint: np.ndarray) -> np.ndarray:
    """Per-system (id, n_px, centroid_row, centroid_col) as a structured array, ids 1..n_systems."""
    ids = np.arange(1, n_systems + 1)
    ys, xs = np.nonzero(sys_grid)
    sids = sys_grid[ys, xs]
    n_px = np.bincount(sids, minlength=n_systems + 1)[1:].astype(float)
    sum_y = np.bincount(sids, weights=ys.astype(float), minlength=n_systems + 1)[1:]
    sum_x = np.bincount(sids, weights=xs.astype(float), minlength=n_systems + 1)[1:]
    safe = np.where(n_px > 0, n_px, 1.0)
    rec = np.zeros(
        n_systems,
        dtype=[("id", np.int32), ("n_px", np.int32), ("cy", np.float64), ("cx", np.float64),
               ("in_footprint", bool)],
    )
    rec["id"] = ids
    rec["n_px"] = n_px.astype(np.int32)
    rec["cy"] = sum_y / safe
    rec["cx"] = sum_x / safe
    fp_by_sys = np.bincount(sids[footprint[ys, xs]], minlength=n_systems + 1)[1:]
    rec["in_footprint"] = fp_by_sys > 0
    return rec


def assign_systems_to_folds(
    sys_table: np.ndarray, fold: np.ndarray, n_folds: int, seed: int
) -> np.ndarray:
    """Deterministically choose the held-out systems: quadrant-blocked, one share per fold.

    Returns an array `holdout_fold` of length n_systems where entry i is the fold id of system i+1 if
    that system is held out, else -1. Each fold's held-out systems are those whose centroid falls in
    that fold's quadrant, so a fold is a contiguous region rather than a scattered sample - which is
    what makes the result a test of spatial generalisation and not of interpolation between mapped
    neighbours.
    """
    n = len(sys_table)
    out = np.full(n, -1, dtype=np.int8)
    if n == 0:
        return out
    cy = np.clip(np.rint(sys_table["cy"]).astype(int), 0, fold.shape[0] - 1)
    cx = np.clip(np.rint(sys_table["cx"]).astype(int), 0, fold.shape[1] - 1)
    quad = fold[cy, cx]
    rng = np.random.default_rng(seed)
    for f in range(n_folds):
        members = np.flatnonzero((quad == f) & sys_table["in_footprint"])
        if members.size == 0:
            continue
        # Block by size-deciles so every fold holds out a comparable length of fault trace, then
        # draw the share within the fold. Deterministic given `seed`.
        sizes = sys_table["n_px"][members]
        order = members[np.argsort(sizes, kind="stable")]
        k = max(1, int(round(HOLDOUT_FRACTION * order.size)))
        pick = rng.choice(order.size, size=k, replace=False)
        out[order[pick]] = f
    return out


@dataclass
class LosfoSplit:
    """One LOSFO evaluation cell."""
    fold_id: int
    name: str
    seed: int
    fold_mask: np.ndarray   # full-grid bool: the quadrant
    hidden: np.ndarray      # full-grid bool: held-out systems inside this quadrant (the truth)
    known: np.ndarray       # full-grid bool: catalogue pixels the detector may treat as positive
    min_dist_hidden_to_known: float  # achieved separation in px; inf if no known pixel survives,
                                     # nan if this fold holds out nothing


def build_losfo_split(
    labels: np.ndarray,
    sys_grid: np.ndarray,
    holdout_fold: np.ndarray,
    fold: np.ndarray,
    fold_id: int,
    seed: int,
    fold_names: list[str],
    buffer_px: int = DEFAULT_BUFFER_PX,
) -> LosfoSplit:
    """Truth = this fold's held-out systems; known = catalogue minus a buffer around ALL held-out systems.

    The buffer is applied globally (over every fold's systems), not just this fold's, because the
    detector is trained once across all quadrants: leaving another fold's held-out systems visible
    would leak that structure into the shared model.
    """
    held = sys_grid > 0
    held_ids = np.flatnonzero(holdout_fold >= 0) + 1
    hidden_all = np.isin(sys_grid, held_ids) if held_ids.size else np.zeros(labels.shape, bool)
    buffered = dilate8(hidden_all, int(buffer_px))
    known = labels & ~buffered & held          # mapped, and not within buffer_px of a held-out system
    fm = fold == fold_id
    hidden = hidden_all & fm
    if not hidden.any():
        sep = float("nan")          # nothing held out in this fold
    elif not known.any():
        sep = float("inf")          # every known pixel was erased: separation is unbounded
    else:
        sep = float(distance_transform_edt(~known)[hidden].min())
    return LosfoSplit(fold_id, fold_names[fold_id], seed, fm, hidden, known, sep)


def masked_labels(labels: np.ndarray, sys_grid: np.ndarray, holdout_fold: np.ndarray,
                  buffer_px: int = DEFAULT_BUFFER_PX) -> np.ndarray:
    """The label set the detector is allowed to train on: catalogue minus buffer around held-out systems."""
    held_ids = np.flatnonzero(holdout_fold >= 0) + 1
    if held_ids.size == 0:
        return np.asarray(labels, bool).copy()
    hidden_all = np.isin(sys_grid, held_ids)
    return np.asarray(labels, bool) & ~dilate8(hidden_all, int(buffer_px))


def credit_on(pred: np.ndarray, truth: np.ndarray) -> float:
    """TPw of a binary prediction against a truth set: sum over truth of max_x k(d(x, truth))."""
    from . import metric
    if not truth.any() or not pred.any():
        return 0.0
    return float(metric.kernel_from_distance(distance_transform_edt(~pred)[truth]).sum())
