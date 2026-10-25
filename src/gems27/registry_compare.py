"""Exact full-footprint Spearman and directed dot proximity for lane checks.

A different file hash is not geological uniqueness. No registry-dependent filtering
or relocation of predictions is performed here.
"""
from __future__ import annotations

import numpy as np
from scipy.spatial import cKDTree
from scipy.stats import rankdata


def ranked_centered(values):
    values = np.asarray(values)
    if values.ndim != 1 or values.size < 2 or not np.isfinite(values).all():
        raise ValueError("finite vector of at least two values required")
    ranks = rankdata(values, method="average")
    ranks -= ranks.mean()
    return ranks, float(np.sqrt(ranks @ ranks))


def spearman_against(ranks, norm, other):
    """Exact correlation; binary-reference fast path is algebraically identical.

    Constant reference/candidate: None, never a fabricated zero correlation.
    """
    other = np.asarray(other)
    if other.shape != ranks.shape or not np.isfinite(other).all():
        raise ValueError("comparison must be equal-shaped and finite")
    if norm == 0:
        return None
    positive = other > 0
    if np.all((other == 0) | (other == 1)):
        n, k = len(other), int(positive.sum())
        if k in (0, n):
            return None
        # Rank(0/1) is a positive affine transform of 0/1.
        return float(np.clip(ranks[positive].sum() / (norm * np.sqrt(k * (n - k) / n)), -1, 1))
    ref, refnorm = ranked_centered(other)
    return None if refnorm == 0 else float(np.clip((ranks @ ref) / (norm * refnorm), -1, 1))


def within_fraction(candidate, reference, radius=3.0):
    candidate = np.asarray(candidate, bool)
    reference = np.asarray(reference, bool)
    if candidate.ndim != 2 or candidate.shape != reference.shape:
        raise ValueError("equal-shaped 2-D masks required")
    a = np.argwhere(candidate)
    b = np.argwhere(reference)
    if len(a) == 0:
        return None
    if len(b) == 0:
        return 0.0
    if reference[candidate].all():
        return 1.0
    distances, _ = cKDTree(b).query(a, workers=1)
    return float(np.mean(distances <= radius))
