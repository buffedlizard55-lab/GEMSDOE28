"""Multi-scale Hessian tubularity (Frangi vesselness) for scarp-step centreline detection (S20-H2).

Preregistered in ``knowledge/56_s20_preregistration_and_hypotheses.md`` before any S20 holdout
number existed. The transform is **label-free**: no catalogue, prediction, or score raster is read,
so the surface cannot leak held-out fault systems into a LOSFO split.

Why a second-derivative detector when the repo already has gradient magnitudes
(``potential_edges``, ``structural_step``), directional line integrals (``newinfo``), upward
continuation (``depthslice``) and Euler deconvolution (``euler``)? Those measure *how much* a field
changes, or integrate evidence along assumed straight strikes. The Hessian eigenstructure measures
*shape*: at the centreline of a bright tubular ridge the second derivative across strike is large
and negative while the along-strike second derivative is near zero (|lambda2| >> |lambda1|,
lambda2 < 0). Isotropic blobs (volcanic cones, playa rims) have |lambda1| ~ |lambda2| and are
suppressed by the blobness term; plate-like steps are suppressed by the structureness term. No
Hessian/eigenvalue transform existed in ``src/gems27/`` before this module (verified by grep
2026-10-26).

Reference: Frangi et al. (1998), "Multiscale vessel enhancement filtering", MICCAI 1998,
LNCS 1496, 130-137. Eigenvalues ordered |lambda1| <= |lambda2|; for bright structures on a dark
background the ridge condition is lambda2 < 0. Scale-normalised derivatives (sigma^2 factor) follow
the standard Frangi formulation so responses are comparable across scales before the max.

Named non-fault mimic (knowledge/56): roads/levees, paleoshorelines, incised drainages and bedding
ridges are all tubular step anomalies with no fault slip. Vesselness high therefore never means
"fault" by itself; it is a candidate surface that must earn credit on the buffered holdout.

Determinism: no randomness, no fitted parameters. Invalid cells are nearest-filled for filtering
only (repo convention, cf. ``potential_edges._nearest_fill``) and are exactly 0.0 in the output.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import distance_transform_edt, gaussian_filter

SIGMAS_PX = (1.0, 2.0, 3.0)  # frozen in knowledge/56 (100 m px -> 100/200/300 m structure scales)
BETA = 0.5                   # Frangi blobness sensitivity (frozen)


def _nearest_fill(field: np.ndarray, valid: np.ndarray) -> np.ndarray:
    """Fill invalid cells from the nearest valid cell (filtering context only)."""
    if not valid.any():
        raise ValueError("vesselness input has no valid cells")
    if valid.all():
        return field.astype(np.float64, copy=True)
    inds = distance_transform_edt(~valid, return_distances=False, return_indices=True)
    return field[tuple(inds)].astype(np.float64, copy=False)


def _hessian_eigenvalues(filled: np.ndarray, sigma: float) -> tuple[np.ndarray, np.ndarray]:
    """Scale-normalised Hessian eigenvalues ordered |lambda1| <= |lambda2| (float64)."""
    s2 = float(sigma) ** 2
    dxx = gaussian_filter(filled, sigma, order=(0, 2), mode="nearest") * s2
    dyy = gaussian_filter(filled, sigma, order=(2, 0), mode="nearest") * s2
    dxy = gaussian_filter(filled, sigma, order=(1, 1), mode="nearest") * s2
    # Closed-form eigendecomposition of the symmetric 2x2 Hessian at every pixel.
    tmp = np.sqrt(np.maximum((dxx - dyy) ** 2 + 4.0 * dxy**2, 0.0))
    mu1 = 0.5 * (dxx + dyy + tmp)
    mu2 = 0.5 * (dxx + dyy - tmp)
    swap = np.abs(mu1) > np.abs(mu2)
    lam1 = np.where(swap, mu2, mu1)
    lam2 = np.where(swap, mu1, mu2)
    return lam1, lam2


def frangi_vesselness(
    field: np.ndarray,
    valid: np.ndarray,
    *,
    sigmas_px: tuple[float, ...] = SIGMAS_PX,
    beta: float = BETA,
) -> np.ndarray:
    """Frangi bright-ridge vesselness of ``field`` in [0, 1], exactly 0 outside ``valid``.

    Per scale: Rb = |lambda1|/|lambda2| (blobness), S = sqrt(lambda1^2 + lambda2^2)
    (structureness), c = 0.5 * max(S over valid cells) (Frangi's standard default), and
    V = exp(-Rb^2 / (2 beta^2)) * (1 - exp(-S^2 / (2 c^2))) where lambda2 < 0, else 0.
    The returned surface is the max over scales, float32, finite everywhere.
    """
    f = np.asarray(field, dtype=np.float64)
    mask = np.asarray(valid, dtype=bool) & np.isfinite(f)
    if f.ndim != 2 or f.shape != mask.shape:
        raise ValueError("field and valid must be same-shape 2-D arrays")
    if not sigmas_px or any((not np.isfinite(s)) or s <= 0 for s in sigmas_px):
        raise ValueError("sigmas_px must be non-empty finite positives")
    if not np.isfinite(beta) or beta <= 0:
        raise ValueError("beta must be finite and positive")
    filled = _nearest_fill(f, mask)

    out = np.zeros(f.shape, dtype=np.float64)
    # Degeneracy guard: c is defined relative to max(S), and scipy's truncated Gaussian
    # derivative kernels do not sum to exactly zero (measured |Dxx| ~ 5e-4 on a constant 7.0
    # field at sigma=1). On a heterogeneous field that residue is harmless (c is set by real
    # structure, so flat areas get V ~ S^2/2c^2 ~ 0), but on a globally constant valid field it
    # would be amplified to O(1). A constant field has no ridges by definition: return zeros.
    valid_vals = f[mask]
    if valid_vals.size and float(valid_vals.max()) == float(valid_vals.min()):
        return out.astype(np.float32)
    s_floor = 1e-12 * (float(np.abs(filled).max()) + 1.0)
    for sigma in sigmas_px:
        lam1, lam2 = _hessian_eigenvalues(filled, float(sigma))
        s_norm = np.sqrt(lam1**2 + lam2**2)
        c = 0.5 * float(s_norm[mask].max()) if mask.any() else 0.0
        if not np.isfinite(c) or c <= s_floor:
            continue
        rb = np.abs(lam1) / np.maximum(np.abs(lam2), np.finfo(np.float64).tiny)
        v = np.exp(-(rb**2) / (2.0 * beta * beta)) * (1.0 - np.exp(-(s_norm**2) / (2.0 * c * c)))
        v = np.where(lam2 < 0, v, 0.0)
        out = np.maximum(out, v)
    out = np.clip(out, 0.0, 1.0)
    out[~mask] = 0.0
    result = out.astype(np.float32)
    if not np.isfinite(result).all():
        raise ValueError("vesselness produced non-finite values")
    return result
