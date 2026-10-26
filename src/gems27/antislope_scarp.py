"""Label-free antislope scarp curvature-pair surface for S19-ASCP.

The input bands are quantized terrain descriptors, not fault labels. This module
only computes the preregistered physical conjunction; placement and evaluation
remain in the shared pipeline.
"""
from __future__ import annotations

import numpy as np

EPS = np.float32(1e-6)


def decode_sqrt_rank(values: np.ndarray) -> np.ndarray:
    """Invert q=1+round(254*sqrt(clip(x/xmax,0,1))) to normalized x/xmax."""
    q = np.asarray(values, dtype=np.float32)
    t = np.clip((q - 1.0) / 254.0, 0.0, 1.0)
    return np.where(q > 0, t * t, 0.0).astype(np.float32)


def decode_linear_rank(values: np.ndarray) -> np.ndarray:
    q = np.asarray(values, dtype=np.float32)
    return np.where(q > 0, np.clip((q - 1.0) / 254.0, 0.0, 1.0), 0.0).astype(np.float32)


def build_surface(
    step_q: np.ndarray,
    lapneg_q: np.ndarray,
    lappos_q: np.ndarray,
    downface_q: np.ndarray,
    upface_q: np.ndarray,
    cross_q: np.ndarray,
    coherence_q: np.ndarray,
    valid_q: np.ndarray,
) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """Return fixed geometric-mean surface and its four preregistered legs."""
    arrays = [np.asarray(x) for x in (step_q, lapneg_q, lappos_q, downface_q,
                                      upface_q, cross_q, coherence_q, valid_q)]
    if any(x.shape != arrays[0].shape for x in arrays) or arrays[0].ndim != 2:
        raise ValueError("Eight aligned 2-D descriptor bands are required")
    step, neg, pos, down, up, cross = map(decode_sqrt_rank, arrays[:6])
    coherence = decode_linear_rank(arrays[6])
    valid = arrays[7] > 0
    curvature_pair = 2.0 * np.minimum(neg, pos) / (neg + pos + EPS)
    antislope = up / (up + down + cross + EPS)
    legs = {
        "step_strength": step,
        "curvature_pair": curvature_pair.astype(np.float32),
        "antislope_selectivity": antislope.astype(np.float32),
        "coherence": coherence,
    }
    product = np.ones(step.shape, dtype=np.float32)
    for value in legs.values():
        product *= np.clip(value, 0.0, 1.0)
    surface = np.where(valid, np.power(product, 0.25), 0.0).astype(np.float32)
    if not np.isfinite(surface).all() or np.any((surface < 0) | (surface > 1)):
        raise AssertionError("S19 surface must be finite in [0,1]")
    return surface, legs
