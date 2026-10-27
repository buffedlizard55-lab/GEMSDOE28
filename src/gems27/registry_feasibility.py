"""Exact geometry-only bounds for the literal any-registry-raster overlap rule.

These are counting arguments, not performance estimates. Never use this module to
move/filter predictions into registry holes: a duplicate lane must stop, not tune.
"""
from __future__ import annotations

import math

import numpy as np
from scipy.ndimage import distance_transform_edt


def _positive_integer(value, name):
    if isinstance(value, bool) or not isinstance(value, (int, np.integer)) or value < 1:
        raise ValueError(f"{name} must be a positive integer")
    return int(value)


def coverage_bounds(
    footprint,
    reference,
    *,
    budget: int,
    radius_px: float = 3.0,
    overlap_limit: float = 0.70,
    min_spacing_px: float | None = None,
):
    """Return necessary feasibility conditions and the exact covered-pixel mask.

    At most U distinct candidate dots can lie in U uncovered footprint cells.
    Therefore every B-dot candidate has overlap >= max(0, (B-U)/B).

    Optional spacing bound: partition the integer grid into squares whose diameter
    is STRICTLY less than the required dot spacing. Each occupied square can hold
    at most one admissible dot. The tightest of up to four grid-origin shifts is
    a valid upper bound on uncovered-dot capacity (not an exact packing solution).
    """
    fp_raw, ref_raw = np.asarray(footprint), np.asarray(reference)
    if (fp_raw.ndim != 2 or fp_raw.shape != ref_raw.shape or not fp_raw.any()
            or not np.isin(fp_raw, [0, 1]).all() or not np.isin(ref_raw, [0, 1]).all()):
        raise ValueError("Aligned, nonempty finite binary 2-D footprint and reference required")
    fp, ref = fp_raw.astype(bool), ref_raw.astype(bool)
    budget = _positive_integer(budget, "budget")
    if budget > int(fp.sum()):
        raise ValueError("budget cannot exceed the number of footprint cells")
    if isinstance(radius_px, bool) or not np.isfinite(radius_px) or radius_px < 0:
        raise ValueError("radius_px must be finite and nonnegative")
    if isinstance(overlap_limit, bool) or not np.isfinite(overlap_limit) or not 0 <= overlap_limit <= 1:
        raise ValueError("overlap_limit must be finite and in [0,1]")
    ref = ref & fp
    # EDT of an empty reference has an implicit off-array background; do not
    # mistake that numerical behavior for proximity to a real registry dot.
    covered = fp & (distance_transform_edt(~ref) <= radius_px) if ref.any() else np.zeros_like(fp)
    uncovered = fp & ~covered
    n, u = int(fp.sum()), int(uncovered.sum())
    pixel_lower = max(0.0, (budget - u) / budget)
    required_uncovered = int(math.ceil(budget * (1.0 - overlap_limit) - 1e-10))
    result = {
        "label": "GEOMETRY-AUDIT (not HOLDOUT-DTI or an organizer score)",
        "footprint_pixels": n,
        "reference_positive_pixels": int(ref.sum()),
        "radius_px": float(radius_px),
        "covered_pixels": int(covered.sum()),
        "covered_fraction": float(covered.sum() / n),
        "uncovered_pixels": u,
        "candidate_budget": budget,
        "overlap_limit": float(overlap_limit),
        "required_uncovered_dots_to_pass": required_uncovered,
        "unspaced_overlap_lower_bound": pixel_lower,
        "unspaced_target_budget_impossible": bool(pixel_lower > overlap_limit),
        "max_budget_not_ruled_out_by_pixel_count": (
            min(n, int(math.floor(u / (1.0 - overlap_limit) + 1e-10))) if overlap_limit < 1 else n
        ),
        "spacing": None,
        "target_budget_impossible": bool(pixel_lower > overlap_limit),
        "interpretation": "A necessary counting bound only. A non-blocked budget is not a novelty pass, a score estimate or permission to relocate dots.",
    }
    if min_spacing_px is not None:
        if isinstance(min_spacing_px, bool) or not np.isfinite(min_spacing_px) or min_spacing_px <= 0:
            raise ValueError("min_spacing_px must be finite and positive")
        # Integer cell coordinates in a side-L square have diameter sqrt(2)*(L-1).
        side = min(max(fp.shape), max(1, int(math.ceil(min_spacing_px / math.sqrt(2)))))
        while side > 1 and math.sqrt(2) * (side - 1) >= min_spacing_px:
            side -= 1
        coords = np.argwhere(uncovered)
        capacities = []
        shifts = sorted({0, min(1, side - 1)})
        for dy in shifts:
            for dx in shifts:
                if len(coords):
                    bins = (coords + (dy, dx)) // side
                    capacity = int(len(np.unique(bins, axis=0)))
                else:
                    capacity = 0
                capacities.append({"row_shift": dy, "col_shift": dx, "occupied_squares": capacity})
        upper = min(row["occupied_squares"] for row in capacities)
        lower = max(0.0, (budget - upper) / budget)
        result["spacing"] = {
            "min_spacing_px": float(min_spacing_px),
            "partition_side_pixels": side,
            "partition_diameter_px": math.sqrt(2) * (side - 1),
            "uncovered_dot_capacity_upper_bound": upper,
            "overlap_lower_bound": lower,
            "partitions": capacities,
            "target_budget_impossible": bool(lower > overlap_limit),
        }
        result["target_budget_impossible"] |= bool(lower > overlap_limit)
    return result, covered
