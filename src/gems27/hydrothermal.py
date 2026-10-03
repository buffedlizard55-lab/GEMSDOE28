"""Hydrothermal upflow conjunction for the H35-1 ADD arm (Session 11).

Pure, deterministic, label-free transforms: hot well/spring cells, thermal proximity, radiometric
alteration halos, Euler-depth bonus, and budgeted top-K addition selection with dot-thinning.
No function here reads labels, truth, or the wellspring CSV's full-catalogue distance column
(`dist_known_fault_px` would leak held-out systems into a LOSFO cell - it is excluded by
`usecols`, and a test feeds a CSV without that column).

Frozen constants live in `knowledge/24_preregistration_H35-1.md`; this module takes them as
explicit arguments with the frozen values as defaults so the runner passes them verbatim.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
from scipy.ndimage import distance_transform_edt

from . import thinning

# Frozen by knowledge/24 (H35-1 preregistration).
TEMP_C_CUT = 60.0
QTZ_C_CUT = 130.0
DEDUP_PX = 2          # 200 m dedup grid for hot rows
THERMAL_PX = 10.0     # 1 km upflow-halo radius
THK_Q = 25.0          # Th/K at/below p25 (K-metasomatic depletion)
UTH_Q = 75.0          # U/Th at/above p75
EULER_PX = 3.0        # 300 m Euler-depth bonus radius
FAR_PX = 3.0          # 300 m far-field floor for added dots
BUDGET_FRAC = 0.02    # additions = 2% of base dots
THIN_D = 2.8          # emission spacing, same as the d=2.8 base
BONUS = 0.5           # each corroborating leg multiplies the score by (1 + BONUS)


def load_hot_cells(path: str | Path, shape: tuple[int, int], *,
                   temp_cut: float = TEMP_C_CUT, qtz_cut: float = QTZ_C_CUT,
                   dedup_px: int = DEDUP_PX) -> dict:
    """Return the deduped hot-cell grid plus descriptive counts.

    A row is hot iff temp_c >= temp_cut OR geothermquartz_c >= qtz_cut (NaN-safe: a missing
    value votes no on its leg). Only the two temperature columns and the grid coordinates are
    read - never the distance column.
    """
    df = pd.read_csv(path, usecols=["temp_c", "geothermquartz_c", "row", "col"])
    temp = pd.to_numeric(df["temp_c"], errors="coerce").to_numpy(dtype=np.float64)
    qtz = pd.to_numeric(df["geothermquartz_c"], errors="coerce").to_numpy(dtype=np.float64)
    hot_row = (np.nan_to_num(temp, nan=-np.inf) >= temp_cut) | (
        np.nan_to_num(qtz, nan=-np.inf) >= qtz_cut)
    rows = np.clip(df["row"].to_numpy(dtype=np.int64), 0, shape[0] - 1)
    cols = np.clip(df["col"].to_numpy(dtype=np.int64), 0, shape[1] - 1)
    cells = np.zeros(shape, bool)
    hr, hc = rows[hot_row] // dedup_px, cols[hot_row] // dedup_px
    # one hot cell per occupied dedup cell (representative = lowest raster index, deterministic)
    seen = set()
    for r, c, gr, gc in zip(hr, hc, rows[hot_row], cols[hot_row]):
        key = (int(r), int(c))
        if key in seen:
            continue
        seen.add(key)
        cells[int(gr), int(gc)] = True
    return {"hot": cells, "n_rows_hot": int(hot_row.sum()), "n_rows": len(df),
            "n_cells": int(cells.sum())}


def thermal_proximity(hot: np.ndarray, radius_px: float = THERMAL_PX) -> np.ndarray:
    """Pixels within `radius_px` of a hot cell (empty hot grid -> all False)."""
    hot = np.asarray(hot, bool)
    if not hot.any():
        return np.zeros_like(hot, bool)
    return distance_transform_edt(~hot) <= radius_px


def alteration_halo(thk: np.ndarray, uth: np.ndarray, *,
                    thk_q: float = THK_Q, uth_q: float = UTH_Q) -> dict:
    """K-metasomatic halo: Th/K <= p25 AND U/Th >= p75 over valid (nonzero-ThK) pixels.

    Zeros are nodata (the `channel_auc.py` convention for uint8 layers); quantiles are computed
    over valid pixels only and pixels outside valid coverage are never halo (neutral, not excluded).
    """
    thk = np.asarray(thk)
    uth = np.asarray(uth)
    valid = thk > 0
    if not valid.any():
        return {"halo": np.zeros(thk.shape, bool), "valid": valid,
                "thk_cut": None, "uth_cut": None, "valid_frac": 0.0}
    thk_cut = float(np.quantile(thk[valid].astype(np.float64), thk_q / 100.0))
    uth_cut = float(np.quantile(uth[valid].astype(np.float64), uth_q / 100.0))
    halo = valid & (thk <= thk_cut) & (uth >= uth_cut)
    return {"halo": halo, "valid": valid, "thk_cut": thk_cut, "uth_cut": uth_cut,
            "valid_frac": float(valid.mean())}


def euler_halo(rows: np.ndarray, cols: np.ndarray, shape: tuple[int, int],
               radius_px: float = EULER_PX) -> np.ndarray:
    """Pixels within `radius_px` of a rounded SI=0 Euler cluster centroid."""
    mask = np.zeros(shape, bool)
    rr = np.clip(np.round(np.asarray(rows, dtype=float)).astype(int), 0, shape[0] - 1)
    cc = np.clip(np.round(np.asarray(cols, dtype=float)).astype(int), 0, shape[1] - 1)
    mask[rr, cc] = True
    if not mask.any():
        return mask
    return distance_transform_edt(~mask) <= radius_px


def subthreshold_ridge(prob: np.ndarray, ridge: np.ndarray, fold_mask: np.ndarray,
                       known: np.ndarray, budget_frac: float) -> dict:
    """Split the cell's candidate ridge into emitted-top-k and sub-threshold pools.

    Replicates `oof_detector.build_oof_dotted_base`'s top-k cut exactly (same k formula, same
    argpartition selection) so `selected | subthreshold` partitions `ridge & active` and the
    shipped base is always a subset of `selected` (thinning only drops).
    """
    active = np.asarray(fold_mask, bool) & ~np.asarray(known, bool)
    cand = np.asarray(ridge, bool) & active
    k = int(round(float(budget_frac) * int(np.asarray(fold_mask, bool).sum())))
    ys, xs = np.nonzero(cand)
    selected = np.zeros_like(cand, bool)
    if ys.size and k > 0:
        if ys.size > k:
            sc = np.asarray(prob)[ys, xs]
            top = np.argpartition(-sc, k - 1)[:k]
            ys, xs = ys[top], xs[top]
        selected[ys, xs] = True
    return {"selected": selected, "subthreshold": cand & ~selected, "k": k,
            "n_cand": int(cand.sum())}


def _rank_topk_flat(score_flat: np.ndarray, k: int) -> np.ndarray:
    """Indices of the top-k scores; ties broken by raster order (stable, deterministic)."""
    order = np.argsort(-score_flat, kind="stable")
    return order[:k]


def select_additions(*, prob: np.ndarray, subthreshold: np.ndarray, base: np.ndarray,
                     known: np.ndarray, thermal: np.ndarray, halo: np.ndarray,
                     euler: np.ndarray, budget_dots: int,
                     far_px: float = FAR_PX, thin_d: float = THIN_D,
                     bonus: float = BONUS, require_thermal: bool = True) -> dict:
    """Select up to `budget_dots` addition dots from the sub-threshold ridge.

    Eligibility: sub-threshold & >= far_px from known & (>= thin_d from every base dot) &
    (thermal if `require_thermal`, else non-thermal for the direction control). Score =
    prob * (1 + bonus*halo + bonus*euler). Top-K by score with raster-order tie-break, then
    `dot_thin(thin_d)` for mutual spacing. Returns the thinned set plus an audit trail.
    """
    sub = np.asarray(subthreshold, bool)
    base = np.asarray(base, bool)
    known = np.asarray(known, bool)
    d_known = distance_transform_edt(~known) if known.any() else np.full(sub.shape, np.inf)
    d_base = distance_transform_edt(~base) if base.any() else np.full(sub.shape, np.inf)
    eligible = sub & (d_known >= far_px) & (d_base >= thin_d)
    thermal = np.asarray(thermal, bool)
    eligible = eligible & (thermal if require_thermal else ~thermal)
    ys, xs = np.nonzero(eligible)
    info: dict = {"n_eligible": int(eligible.sum()), "budget": int(budget_dots)}
    if ys.size == 0 or budget_dots <= 0:
        info.update({"n_selected": 0, "n_added": 0})
        return {"added": np.zeros_like(sub, bool), "info": info}
    p = np.asarray(prob, dtype=np.float64)[ys, xs]
    h = np.asarray(halo, bool)[ys, xs].astype(np.float64)
    e = np.asarray(euler, bool)[ys, xs].astype(np.float64)
    score = p * (1.0 + bonus * h + bonus * e)
    take = _rank_topk_flat(score, min(int(budget_dots), ys.size))
    raw = np.zeros_like(sub, bool)
    raw[ys[take], xs[take]] = True
    added = thinning.dot_thin(raw, thin_d)
    info.update({"n_selected": int(raw.sum()), "n_added": int(added.sum()),
                 "mean_score_selected": float(score[take].mean())})
    return {"added": added, "info": info}
