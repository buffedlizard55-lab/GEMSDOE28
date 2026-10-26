"""Object-level radiometric alteration lineaments (S19-RADLIN, knowledge/55).

Label-free transform of the GeoDAWN Th/K ratio grid into a lineament score.
Low Th/K marks potassic alteration; a *linear* low-Th/K ridge that stays
collinear over >= 1 km is the frozen signature.  Nothing here reads labels,
catalogue rasters or scores, so the surface cannot leak held-out fault
systems into a LOSFO cell.  Outside valid radiometry the score is exactly 0.

Frozen definitions (knowledge/55, written before any fit):
  f      = clip((p95 - ThK) / (p95 - p5), 0, 1) over valid (ThK > 0) pixels,
           nearest-valid fill used only so filters see no nodata holes
  fs     = gaussian_filter(f, sigma=1 px)
  ridge  = shared 1-px ridge of fs (oof_detector.ridge_nms, no extra smoothing)
  mx10   = max over 4 orientations of the +-10 px line mean of fs
  aniso  = (mx10 - mean10) / mx10 where mx10 > 0, else 0
  score  = ridge * clip(mx10, 0, 1) * (0.5 + 0.5 * aniso), in [0, 1]
  bonus  = 7x7 maximum of score (lineament influence within 300 m)

Named non-fault mimic: felsic lithologic boundaries, playa evaporite K
enrichment and GeoDAWN flight-line striping all make low-Th/K lineaments
with zero fault displacement.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import gaussian_filter, maximum_filter

from .oof_detector import ridge_nms

ORIENTATIONS = ((1, 0), (1, 1), (0, 1), (1, -1))  # row/col steps: N-S, NE, E-W, NW
LINE_HALF_PX = 10  # 1 km half-length on the 100 m grid
BONUS_BONUS_SIZE = 7  # 7x7 maximum == within 3 px (300 m)


def _shift(a: np.ndarray, dr: int, dc: int) -> np.ndarray:
    """Zero-filled translation by (dr, dc); deterministic, no wrap-around."""
    out = np.zeros_like(a)
    h, w = a.shape
    rs0, rs1 = max(0, dr), min(h, h + dr)
    cs0, cs1 = max(0, dc), min(w, w + dc)
    if rs0 >= rs1 or cs0 >= cs1:
        return out
    out[rs0:rs1, cs0:cs1] = a[rs0 - dr:rs1 - dr, cs0 - dc:cs1 - dc]
    return out


def oriented_line_means(img: np.ndarray, half_px: int = LINE_HALF_PX) -> tuple[np.ndarray, np.ndarray]:
    """(max, mean) over the 4 orientations of the +-half_px line mean at each pixel."""
    accs = []
    for dr, dc in ORIENTATIONS:
        acc = img.astype(np.float32).copy()
        for k in range(1, int(half_px) + 1):
            acc += _shift(img, dr * k, dc * k)
            acc += _shift(img, -dr * k, -dc * k)
        accs.append(acc / np.float32(2 * int(half_px) + 1))
    stack = np.stack(accs)
    return stack.max(axis=0), stack.mean(axis=0)


def radiometric_lineament_surface(
    thk: np.ndarray, valid: np.ndarray
) -> dict[str, np.ndarray | dict]:
    """Return {score, bonus, field} float32 in [0,1], zero outside `valid`, plus audit meta.

    `thk` is the u8 Th/K ratio grid (0 = nodata); `valid` is the footprint/validity mask.
    Raises on shape mismatch, non-2-D input, or no valid pixels (a silent all-zero
    surface would masquerade as "no lineaments").
    """
    thk = np.asarray(thk)
    valid = np.asarray(valid, bool)
    if thk.ndim != 2 or thk.shape != valid.shape:
        raise ValueError("thk and valid must be equal-shaped 2-D arrays")
    vmask = valid & (thk > 0)
    if not vmask.any():
        raise ValueError("no valid radiometric pixels")
    vals = thk[vmask].astype(np.float64)
    p5, p95 = np.percentile(vals, (5.0, 95.0))
    if not np.isfinite(p5) or not np.isfinite(p95) or p95 <= p5:
        raise ValueError("ThK valid distribution is degenerate")
    field = np.clip((p95 - thk.astype(np.float64)) / (p95 - p5), 0.0, 1.0).astype(np.float32)
    # Nearest-valid fill for filtering only (same convention as prepare_data/potential_edges).
    from scipy.ndimage import distance_transform_edt

    if not vmask.all():
        idx = distance_transform_edt(~vmask, return_distances=False, return_indices=True)
        field_filled = field[tuple(idx)]
    else:
        field_filled = field
    fs = gaussian_filter(field_filled, sigma=1.0).astype(np.float32)
    ridge = ridge_nms(fs, vmask, sigma=0.0)
    mx, mean = oriented_line_means(fs)
    aniso = np.where(mx > 0, (mx - mean) / np.maximum(mx, 1e-12), 0.0).astype(np.float32)
    score = np.where(ridge, np.clip(mx, 0.0, 1.0) * (0.5 + 0.5 * aniso), 0.0).astype(np.float32)
    score[~vmask] = 0.0
    bonus = maximum_filter(score, size=BONUS_BONUS_SIZE, mode="constant", cval=0.0)
    bonus[~vmask] = 0.0
    out_field = np.where(vmask, fs, 0.0).astype(np.float32)
    meta = {
        "thk_p5": float(p5), "thk_p95": float(p95),
        "valid_px": int(vmask.sum()), "ridge_px": int(ridge.sum()),
        "score_positive_px": int((score > 0).sum()),
        "bonus_positive_px": int((bonus > 0).sum()),
        "score_max": float(score.max()),
    }
    return {"score": score, "bonus": bonus.astype(np.float32), "field": out_field, "meta": meta}
